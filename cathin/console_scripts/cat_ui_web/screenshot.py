import cv2
from PIL import Image
import subprocess

from cathin.Android.android_driver import AndroidDriver
from cathin.Windows.windows_driver import WindowsDriver

from cathin.common.get_all_bounds_and_labels import get_all_bounds_and_labels

from cathin.console_scripts.cat_ui_web.get_windows import getWindowsWithHandle

loading_window_ref = None


def process_screenshot(img):
    all_text_bounds_and_des = get_all_bounds_and_labels(img, get_icon_des=True)
    all_values = []
    all_bounds = []
    for index, box_dict in enumerate(all_text_bounds_and_des):
        box = list(box_dict.keys())[0]
        des = f"{index}"
        x, y, w, h = box
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), 2)
        cv2.putText(img, des, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 4)
        cv2.putText(img, des, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 1)
        for key, value in box_dict.items():
            if isinstance(value, list):
                all_values.append({f"{index}.id:{value[1]}": list(box)})
                all_bounds.append(list(box))
            else:
                all_values.append({f"{index}.text:{value}": list(box)})

    screenshot = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return screenshot, all_values


def take_screenshot(platform, device_udid, language):
    if platform == "Android":
        android_driver = AndroidDriver(device_udid, language)
        img = android_driver._capture_screenshot()
        return img

    elif platform == "iOS":
        device_command = ["idevicescreenshot", "-u", device_udid, "screenshot.png"]
        subprocess.run(device_command)
        return Image.open("screenshot.png")

    elif platform == "PC":
        window_obj = getWindowsWithHandle(str(device_udid).split(",")[-1])
        window_ins = WindowsDriver(language, window_obj)
        img = window_ins._capture_screenshot()
        return img
