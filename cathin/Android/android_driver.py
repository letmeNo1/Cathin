import subprocess
import time

import numpy as np

import cv2

from cathin.common.lazy_element import LazyElement
from cathin.common.find_method import find_by_method
from cathin.common.get_all_bounds_and_labels import get_all_bounds_and_labels
from cathin.common.request_api import _check_service_health



class AndroidDriver:
    def __init__(self, udid, lang="en"):
        self.udid = udid
        self.lang = lang

    def _capture_screenshot(self):
        result = subprocess.run(['adb', '-s', self.udid, 'exec-out', 'screencap', '-p'], stdout=subprocess.PIPE)
        screenshot_data = result.stdout
        nparr = np.frombuffer(screenshot_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    def __find_element(self, timeout=10, **query):
        start_time = time.time()
        while True:
            img = self._capture_screenshot()
            all_bounds = get_all_bounds_and_labels(img, query.get('id'))
            find_result = find_by_method(all_bounds, **query)
            if find_result:
                return {"img": img, "all_bounds": all_bounds, "udid": self.udid, "found_element_data": find_result}

            if time.time() - start_time > timeout:
                raise TimeoutError(f"Operation timed out after {timeout} seconds")
            time.sleep(0.1)  # Optional: sleep for a short period to avoid busy-waiting

    def print_all_bounds(self):
        img = self._capture_screenshot()
        all_bounds = get_all_bounds_and_labels(img)
        print(all_bounds)


    def __call__(self, **query) -> LazyElement:
        _check_service_health()
        return LazyElement("android",self.__find_element, **query)