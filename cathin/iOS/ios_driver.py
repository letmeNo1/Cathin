import random
import subprocess
import time

import cv2
from loguru import logger
from cathin.common.lazy_element import LazyElement
from cathin.common.find_method import find_by_method
from cathin.common.get_all_bounds_and_labels import get_all_bounds_and_labels
from cathin.common.request_api import _check_service_health

from cathin.common.runtime_cache import RunningCache
from cathin.common.send_request import send_tcp_request
from cathin.iOS.idb_utils import IdbUtils
from ApolloModule.ApolloNico.apollo_nico.common.error import IDBServerError


class IDBServerError(Exception):
    pass


class IOSDriver:
    def __init__(self, udid, package_name=None, port="random"):
        self.udid = udid
        self.idb_utils = IdbUtils(udid)
        self.package_name = package_name

        logger.debug(f"{self.udid}'s test server is being initialized, plaese wait")
        self.__check_idb_server(udid)
        self.runtime_cache = RunningCache(udid)
        self.__set_running_port(port)
        rst = "200 OK" in send_tcp_request(RunningCache(udid).get_current_running_port(), "print")
        if rst:
            logger.debug(f"{self.udid}'s test server is ready")
        else:
            logger.debug(f"{self.udid} test server disconnect, restart ")
            self.__init_idb_auto()
        if self.package_name is None:
            self.package_name = self.__get_current_bundleIdentifier(RunningCache(udid).get_current_running_port())
        self.runtime_cache.set_action_was_taken(True)

    def _capture_screenshot(self):
        self.idb_utils.get_image_object()
        return self.idb_utils.get_image_object()

    def __find_element(self, timeout=10, **query):
        start_time = time.time()
        while True:
            img = self._capture_screenshot()
            height, width, _ = img.shape
            new_height = int(height / 3)
            new_width = int(width / 3)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            height, width, _ = img.shape
            all_bounds = get_all_bounds_and_labels(img, query.get('id'))
            find_result = find_by_method(all_bounds, **query)
            if find_result:
                return {"img": img, "all_bounds": all_bounds, "udid": self.udid, "found_element_data": find_result,
                        "package_name": self.package_name}

            if time.time() - start_time > timeout:
                raise TimeoutError(f"Operation timed out after {timeout} seconds")
            time.sleep(0.1)  # Optional: sleep for a short period to avoid busy-waiting

    def print_all_bounds(self):
        img = self._capture_screenshot()
        all_bounds = get_all_bounds_and_labels(img)
        print(all_bounds)

    def __check_idb_server(self, udid):
        result = subprocess.run("tidevice list", shell=True, stdout=subprocess.PIPE).stdout
        decoded_result = result.decode('utf-8', errors='ignore')
        if udid in decoded_result:
            pass
        else:
            raise IDBServerError("no devices connect")

    def __init_idb_auto(self):
        self.__set_tcp_forward_port()
        self.__start_test_server()

    def __set_running_port(self, port):
        exists_port, pid = self.idb_utils.get_tcp_forward_port()
        if exists_port is None:
            logger.debug(f"{self.udid} no exists port")
            if port != "random":
                running_port = port
            else:
                random_number = random.randint(9000, 9999)
                running_port = random_number
        else:
            running_port = int(exists_port)
        RunningCache(self.udid).set_current_running_port(running_port)

    def __get_current_bundleIdentifier(self, port):
        bundle_list = self.idb_utils.get_app_list()
        command = "get_current_bundleIdentifier"
        for item in bundle_list:
            if item:
                item = item.split(" ")[0]
                command = command + f":{item}"
        package_name = send_tcp_request(port, command)
        return package_name

    def __set_tcp_forward_port(self):
        current_port = RunningCache(self.udid).get_current_running_port()
        logger.debug(
            f"""tidevice --udid {self.udid} relay {current_port} {current_port}""")
        commands = f"""tidevice --udid {self.udid} relay {current_port} {current_port}"""
        try:

            subprocess.Popen(commands, shell=True)
        except OSError:
            print("start fail")
            subprocess.Popen(commands, shell=True)

    def __start_test_server(self):
        current_port = RunningCache(self.udid).get_current_running_port()
        test_server_package_dict = self.idb_utils.get_test_server_package()
        logger.debug(
            f"""tidevice  --udid {self.udid} xcuitest --bundle-id {test_server_package_dict.get("test_server_package")} --target-bundle-id {test_server_package_dict.get("main_package")} -e USE_PORT:{current_port}""")

        commands = f"""tidevice  --udid {self.udid} xcuitest --bundle-id {test_server_package_dict.get("test_server_package")} --target-bundle-id {test_server_package_dict.get("main_package")} -e USE_PORT:{current_port}"""
        subprocess.Popen(commands, shell=True)
        for _ in range(10):
            response = send_tcp_request(current_port, "print")
            if "200 OK" in response:
                logger.debug(f"{self.udid}'s test server is ready")
                break
            time.sleep(1)
        logger.debug(f"{self.udid}'s uiautomator was initialized successfully")

    def __call__(self, **query) -> LazyElement:
        _check_service_health()
        return LazyElement("ios", self.__find_element, **query)