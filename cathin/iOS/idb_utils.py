import os
import platform
import re
import time
import subprocess

import cv2
import numpy as np
import psutil

from cathin.common.runtime_cache import RunningCache
from cathin.common.send_request import send_http_request


class IdbUtils:
    def __init__(self, udid):
        self.udid = udid
        self.runtime_cache = RunningCache(udid)

    def get_tcp_forward_port(self):
        if platform.system() == "Windows":
            result = subprocess.run(f'netstat -ano | findstr "LISTENING"', capture_output=True, text=True, shell=True)
            output = result.stdout
            lines = output.split('\n')
            pids = [line.split()[4] for line in lines if line.strip()]

        elif platform.system() == "Darwin" or platform.system() == "Linux":
            result = subprocess.run(f'lsof -i | grep LISTEN', capture_output=True, text=True, shell=True)
            output = result.stdout
            lines = output.split('\n')
            pids = [line.split()[1] for line in lines if line.strip()]
        else:
            raise Exception("Unsupported platform")
        for index, pid in enumerate(pids):
            try:
                if "tidevice" in psutil.Process(int(pid)).cmdline()[1]:
                    if platform.system() == "Windows":
                        return lines[index].split()[1].split("->")[0].split(":")[-1], pid
                    else:
                        result = subprocess.run(f"lsof -Pan -p {pid} -i", capture_output=True, text=True, shell=True)
                        output = result.stdout
                        ports = re.findall(r':(\d+)', output)
                        return ports[0], pid
            except:
                continue
        return None, None


    def device_list(self):
        command = f'tidevice list'
        return os.popen(command).read()

    def set_port_forward(self, port):
        commands = f"""tidevice --udid {self.udid} relay {port} {port}"""
        subprocess.Popen(commands, shell=True)

    def get_app_list(self):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        result = subprocess.run(f"tidevice --udid {self.udid} applist", capture_output=True, text=True,
                                encoding='utf-8')
        result_list = result.stdout.splitlines()
        return result_list

    def get_test_server_package(self):
        app_list = self.get_app_list()
        test_server_package_list = [s for s in app_list if s.startswith('nico.')]
        test_server_package = test_server_package_list[0] if "xctrunner" in test_server_package_list[0] else \
            test_server_package_list[1]
        main_package = test_server_package_list[0] if "xctrunner" not in test_server_package_list[0] else \
            test_server_package_list[1]
        return {"test_server_package": test_server_package.split(" ")[0], "main_package": main_package.split(" ")[0]}

    def start_app(self, package_name):
        command = f'launch {package_name}'
        self.cmd(command)
        self.runtime_cache.set_current_running_package_name(package_name)

    def activate_app(self, package_name):
        exists_port = self.runtime_cache.get_current_running_port()
        send_http_request(exists_port, f"activate_app",{"bundle_id":package_name})

    def terminate_app(self, package_name):
        exists_port = self.runtime_cache.get_current_running_port()
        send_http_request(exists_port, f"terminate_app", {"bundle_id":package_name})

    def get_output_device_name(self):
        exists_port = self.runtime_cache.get_current_running_port()
        respo = send_http_request(exists_port, "device_info",{"value":"get_output_device_name"})
        return respo

    def stop_app(self, package_name):
        command = f'kill {package_name}'
        self.cmd(command)

    def cmd(self, cmd):
        udid = self.udid
        """@Brief: Execute the CMD and return value
        @return: bool
        """
        try:
            result = subprocess.run(f'''tidevice --udid {udid} {cmd}''', shell=True, capture_output=True, text=True,
                                    check=True, timeout=10).stdout
        except subprocess.CalledProcessError as e:
            return e.stderr
        return result

    def restart_app(self, package_name):
        self.stop_app(package_name)
        time.sleep(1)
        self.start_app(package_name)

    def unlock(self):
        pass

    def home(self):
        exists_port = self.runtime_cache.get_current_running_port()
        send_http_request(exists_port, "device_action", {"action": "home"})

    def get_volume(self):
        exists_port = self.runtime_cache.get_current_running_port()
        send_http_request(exists_port, "device_info", {"value": "get_output_volume"})

    def turn_volume_up(self):
        exists_port = self.runtime_cache.get_current_running_port()
        send_http_request(exists_port, "device_action", {"action": "volume_up"})

    def turn_volume_down(self):
        exists_port = self.runtime_cache.get_current_running_port()
        send_http_request(exists_port, "device_action", {"action": "volume_down"})

    def snapshot(self, name, path):
        self.cmd(f'screenshot {path}/{name}.jpg')

    def get_pic(self, quality=1.0):
        exists_port = self.runtime_cache.get_current_running_port()
        send_http_request(exists_port, "get_jpg_pic", {"compression_quality": quality})
    def get_image_object(self, quality=100):
        exists_port = self.runtime_cache.get_current_running_port()
        a = send_http_request(exists_port, "get_jpg_pic", {"compression_quality": quality})
        nparr = np.frombuffer(a, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image

    def click(self, x, y):
        current_bundleIdentifier = self.runtime_cache.get_current_running_package()
        if current_bundleIdentifier is None:
            current_bundleIdentifier = self.get_current_bundleIdentifier(
                self.runtime_cache.get_current_running_port())

        send_http_request(RunningCache(self.udid).get_current_running_port(),
                          f"coordinate_action",
                          {"bundle_id": current_bundleIdentifier, "action": "click", "xPixel": x, "yPixel": y,
                           "action_parms": "none"})
        self.runtime_cache.clear_current_cache_ui_tree()

    def get_current_bundleIdentifier(self, port):
        bundle_list = self.get_app_list()
        command = "get_current_bundleIdentifier"
        for item in bundle_list:
            if item:
                item = item.split(" ")[0]
                command = command + f":{item}"
        package_name = send_http_request(port, command)
        return package_name
