import ctypes
import re
import time
from ctypes import *
from ctypes import wintypes
from ctypes.wintypes import HWND, CHAR, LPSTR, RECT
import pygetwindow as gw
from cathin.common.find_method import MultipleValuesFoundError
from pygetwindow import Win32Window
from loguru import logger


class WinCommon:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def __get_window_name(self, hwnd):
        length = self.user32.GetWindowTextLengthW(hwnd)
        title = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(hwnd, title, length + 1)
        return title.value

    def __get_window_class_name(self, hwnd):
        _GetClassNameA = self.user32.GetClassNameA
        _GetClassNameA.argtypes = [HWND, LPSTR, ctypes.c_int]
        _GetClassNameA.restype = ctypes.c_int

        nMaxCount = 0x1000
        dwCharSize = sizeof(CHAR)
        while 1:
            lpClassName = ctypes.create_string_buffer(nMaxCount)
            nCount = _GetClassNameA(hwnd, lpClassName, nMaxCount)
            if nCount == 0:
                raise ctypes.WinError()
            if nCount < nMaxCount - dwCharSize:
                break
            nMaxCount += 0x1000
        return str(lpClassName.value.decode())

    def __get_window_size(self, hwnd):
        rect = wintypes.RECT()
        if not self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            raise ctypes.WinError()
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        return width, height

    def __get_window_attribute(self, hwnd, attribute):
        if attribute == "name":
            return self.__get_window_name(hwnd)
        elif attribute == "class_name":
            return self.__get_window_class_name(hwnd)
        elif attribute == "area_ratio":
            screen_width = self.user32.GetSystemMetrics(0)
            screen_height = self.user32.GetSystemMetrics(1)
            screen_area = screen_width * screen_height
            width, height = self.__get_window_size(hwnd)
            window_area = width * height
            return window_area / screen_area
        else:
            raise ValueError(f"Unsupported attribute: {attribute}")

    def __assert_ui_element(self, hwnd, **query):
        rst = []
        for query_method, query_string in query.items():
            attribute = query_method.replace("_contains", "").replace("_matches", "")
            if "contains" in query_method:
                element_attr = self.__get_window_attribute(hwnd, attribute)
                rst.append(str(element_attr).find(query_string) != -1)
            elif "matches" in query_method:
                element_attr = self.__get_window_attribute(hwnd, attribute)
                rst.append(re.search(query_string, str(element_attr)) is not None)
            elif "min" in query_method or "max" in query_method:
                element_attr = self.__get_window_attribute(hwnd, "area_ratio")
                if "min" in query_method:
                    rst.append(element_attr >= float(query_string))
                if "max" in query_method:
                    rst.append(element_attr <= float(query_string))
            else:
                element_attr = self.__get_window_attribute(hwnd, attribute)
                rst.append(element_attr == query_string)
        return all(rst)

    def print_windows(self):
        windows = gw.getAllWindows()
        for window in windows:
            hwnd = window._hWnd
            buffer = ctypes.create_unicode_buffer(255)
            self.user32.GetWindowTextW(hwnd, buffer, 255)
            class_name = self.__get_window_class_name(hwnd)
            logger.debug(f"Window Handle: {hwnd}, Title: {buffer.value}, Class Name: {class_name}")

    def find_window_by_wait(self, timeout=5, index=0, **kwargs) ->Win32Window:
        time_started_sec = time.time()
        while time.time() < time_started_sec + timeout:
            result = self.find_windows(**kwargs)
            if result:
                if len(result) == 1 or index == 0:
                    logger.debug(f"Found window!: {result[0]}")
                    return result[0]
                elif len(result) > 1:
                    raise MultipleValuesFoundError(f"Finding multiple windows", result)
        raise TimeoutError(f"No window found within {timeout} seconds")

    def find_windows(self, **query):
        windows = gw.getAllWindows()
        match_window_list = []
        for window in windows:
            hwnd = window._hWnd
            if self.__assert_ui_element(hwnd, **query):
                match_window_list.append(window)
        return match_window_list

    def get_foreground_window(self):
        hWnd = self.user32.GetForegroundWindow()
        length = self.user32.GetWindowTextLengthW(hWnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(hWnd, buff, length + 1)
        return hWnd

# windows = win_common.find_windows(name_contains="Teams", max_area=120000)
# for window in windows:
