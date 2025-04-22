import time

import pygetwindow
from cathin.common.find_method import find_by_method
from cathin.common.get_all_bounds_and_labels import get_all_bounds_and_labels
from cathin.common.lazy_element import LazyElement
from cathin.common.request_api import _check_service_health
from ctypes import windll
import win32gui
import win32ui
import cv2
import numpy as np
from PIL import Image
from screeninfo import get_monitors


class WindowsDriver:
    def __init__(self, window):
        self.window = window
        try:
            self.window.activate()
            self.window.show()
        except pygetwindow.PyGetWindowException:
            pass
        self.hwnd = self.window._hWnd
        rect = self.window._rect
        screen_width, screen_height = get_monitors()[0].width, get_monitors()[0].height
        self.left, self.top, self.right, self.bottom = rect.left + screen_width * 0.005, rect.top + screen_height * 0.001, rect.right - screen_width * 0.005, rect.bottom - screen_height * 0.008

    def _capture_screenshot(self):
        # Capture a screenshot of the specified region of the screen
        windll.user32.SetProcessDPIAware()

        # Get the window handle (for demonstration, we'll use the desktop window)
        left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
        w = right - left
        h = bot - top

        hwndDC = win32gui.GetWindowDC(self.hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

        saveDC.SelectObject(saveBitMap)

        # Use the PrintWindow function to copy the window content to the bitmap object
        result = windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 3)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwndDC)

        if result != 1:
            raise Exception("PrintWindow operation failed")

        img_np = np.array(img)
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        return img_cv

    def __find_element(self, timeout=10, **query):
        start_time = time.time()
        while True:
            img = self._capture_screenshot()
            all_bounds = get_all_bounds_and_labels(img, query.get('id'))
            find_result = find_by_method(all_bounds, **query)
            if find_result:
                return {"img": img, "all_bounds": all_bounds, "left": self.left, "top": self.top,
                        "found_element_data": find_result}

            if time.time() - start_time > timeout:
                raise TimeoutError(f"Operation timed out after {timeout} seconds")
            time.sleep(0.1)  # Optional: sleep for a short period to avoid busy-waiting

    def __call__(self,  **query) -> LazyElement:
        _check_service_health()
        return LazyElement("windows", self.__find_element, **query)
