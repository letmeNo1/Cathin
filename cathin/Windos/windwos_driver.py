import io
import os
import time

import cv2
import numpy as np
import pyautogui
from cathin.common.find_method import find_by_method
from cathin.common.get_all_bounds_and_labels import get_all_bounds_and_labels
from cathin.common.lazy_element import LazyElement
from cathin.common.request_api import _start_server
from screeninfo import get_monitors

from cathin.Windos.common import WinCommon


class WindowsDriver:
    def __init__(self, timeout=10, index=0, lang="en", **query):
        os.environ["cathin_platform"] = "Windows"
        win_common = WinCommon()
        self.window = win_common.find_window_by_wait(timeout=timeout, index=index, **query)
        self.window.show()
        self.window.activate()
        self.udid = self.window._hWnd
        _start_server(lang)
        rect = self.window._rect
        screen_width, screen_height = get_monitors()[0].width, get_monitors()[0].height

        self.left, self.top, self.right, self.bottom = rect.left + screen_width * 0.005, rect.top + screen_height * 0.001, rect.right - screen_width * 0.005, rect.bottom - screen_height * 0.008

    def __capture_screenshot(self):
        # Capture a screenshot of the specified region of the screen
        screenshot = pyautogui.screenshot(region=(self.left, self.top, self.right - self.left, self.bottom - self.top))

        # Convert the screenshot to byte data
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # Convert the byte data to a numpy array
        nparr = np.frombuffer(img_byte_arr, np.uint8)

        # Decode the numpy array to an OpenCV image object
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        cv2.imwrite("processed_image.png", img)
        return img

    def __find_element(self, timeout=10, **query):
        start_time = time.time()
        while True:
            img = self.__capture_screenshot()
            all_bounds = get_all_bounds_and_labels(img, query.get('id'))
            find_result = find_by_method(all_bounds, **query)
            if find_result:
                return {"img": img, "all_bounds": all_bounds, "left": self.left, "top": self.top,
                        "found_element_data": find_result}

            if time.time() - start_time > timeout:
                raise TimeoutError(f"Operation timed out after {timeout} seconds")
            time.sleep(0.1)  # Optional: sleep for a short period to avoid busy-waiting

    def __call__(self, **query) -> LazyElement:
        return LazyElement("windows", self.__find_element, **query)