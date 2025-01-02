import ctypes
import re
import time
from ctypes import *
from ctypes import wintypes
from ctypes.wintypes import HWND, CHAR, LPSTR, RECT
import pygetwindow as gw

import _ctypes
import comtypes
from apollo_makima.windows.utils.keyboard import WinKeyboard
from apollo_makima.windows.utils.hwnd import HWND_OBJ
from loguru import logger


def __get_ui_automation_objec_class_name(hwnd):
    def get_uiautomation():
        try:
            _IUIAutomation = comtypes.CoCreateInstance(comtypes.gen.UIAutomationClient.CUIAutomation._reg_clsid_,
                                                       interface=comtypes.gen.UIAutomationClient.IUIAutomation,
                                                       clsctx=comtypes.CLSCTX_INPROC_SERVER)
        except _ctypes.COMError as E:
            print("UIAutomationClient is not installed")
            return None
        except WindowsError as E:
            print("UIAutomationClient is not installed")
            return None
        except Exception as E:
            print("UIAutomationClient is not installed")
            return None
        return _IUIAutomation
    return getattr(get_uiautomation().ElementFromHandle(hwnd), "CurrentClassName")


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
            attribute = query_method.replace("_contains","").replace("_matches","")
            element_attr = self.__get_window_attribute(hwnd, attribute)
            if "contains" in query_method:
                rst.append(str(element_attr).find(query_string) != -1)
            elif "matches" in query_method:
                rst.append(re.search(query_string, str(element_attr)) is not None)
            elif "min" in query_method or "max" in query_method:
                if "min" in query_method:
                    rst.append(element_attr >= float(query_string))
                if "max" in query_method:
                    rst.append(element_attr <= float(query_string))
            else:
                rst.append(element_attr == query_string)
        return all(rst)

    def print_windows(self):
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def EnumWindowsProc(hwnd, lParam):
            length = self.user32.GetWindowTextLengthW(hwnd) + 1
            buffer = ctypes.create_unicode_buffer(length)
            self.user32.GetWindowTextW(hwnd, buffer, length)
            if self.user32.IsWindowVisible(hwnd):
                class_name = self.__get_window_class_name(hwnd)
                width, height = self.__get_window_size(hwnd)

                # Get screen resolution
                screen_width = self.user32.GetSystemMetrics(0)
                screen_height = self.user32.GetSystemMetrics(1)
                screen_area = screen_width * screen_height

                # Calculate the ratio of window size to screen size
                window_area = width * height
                area_ratio = window_area / screen_area

                print(
                    f"Window Handle: {hwnd}, Title: {buffer.value}, Class Name: {class_name}, Size: {width}x{height}, Area: {window_area}, Area Ratio: {area_ratio:.2f}")
            return True

        self.user32.EnumWindows(WNDENUMPROC(EnumWindowsProc), 0)

    def find_window_by_wait(self, timeout=5, **kwargs):
        time_started_sec = time.time()
        while time.time() < time_started_sec + timeout:
            result = self.find_windows(**kwargs)
            if len(result) > 0:
                return result
        error = "Can't find window"
        raise TimeoutError(error)

    def open_app_by_name(self, app_name):
        win_keyboard = WinKeyboard()
        win_keyboard.send_keys(win_keyboard.codes.LEFT_WIN)
        win_keyboard.copy_text(app_name)
        time.sleep(1)
        win_keyboard.send_keys(win_keyboard.codes.CONTROL, win_keyboard.codes.KEY_V, delay=1)
        time.sleep(1)
        win_keyboard.send_keys(win_keyboard.codes.RETURN)
        time.sleep(2)

    def find_windows(self, **query):
        windows = gw.getAllWindows()
        hwnd_list = []
        for window in windows:
            hwnd = window._hWnd
            if self.__assert_ui_element(hwnd, **query):
                hwnd_list.append(HWND_OBJ(hwnd))
        for i in hwnd_list:
            logger.debug(i.window_name)
        return hwnd_list

    def get_foreground_window(self):
        hWnd = self.user32.GetForegroundWindow()
        length = self.user32.GetWindowTextLengthW(hWnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(hWnd, buff, length + 1)
        return HWND_OBJ(hWnd)


# windows = win_common.find_windows(name_contains="Teams", max_area=120000)
# for window in windows:
#     print(window.window_name)