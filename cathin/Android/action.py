import os

from loguru import logger


class Action:
    def __init__(self, udid, bounds, text):
        self.udid = udid
        self.bounds = bounds
        self.text = text

    def center_coordinate(self):
        x, y, w, h = self.bounds
        center_x = x + w // 2
        center_y = y + h // 2
        return center_x, center_y

    def scroll(self, duration=200, direction='vertical_up'):
        if direction not in ('vertical_up', "vertical_down", 'horizontal_left', "horizontal_right"):
            raise ValueError(
                'Argument `direction` should be one of "vertical_up" or "vertical_down" or "horizontal_left"'
                'or "horizontal_right". Got {}'.format(repr(direction)))
        to_x = 0
        to_y = 0
        from_x = self.center_coordinate()[0]
        from_y = self.center_coordinate()[1]
        if direction == "vertical_up":
            to_x = from_x
            to_y = from_y - from_y / 2
        elif direction == "vertical_down":
            to_x = from_x
            to_y = from_y + from_y / 2
        elif direction == "horizontal_left":
            to_x = from_x - from_x / 2
            to_y = from_y
        elif direction == "horizontal_right":
            to_x = from_x + from_x / 2
            to_y = from_y
        command = f'adb -s {self.udid} shell input swipe {from_x} {from_y} {to_x} {to_y} {duration}'
        os.system(command)
        logger.debug(f"scroll {direction}")

    def swipe(self, to_x, to_y, duration=0):
        from_x = self.center_coordinate()[0]
        from_y = self.center_coordinate()[1]
        duration = duration * 1000 + 200
        command = f'adb -s {self.udid} shell input swipe {from_x} {from_y} {to_x} {to_y} {duration}'
        os.environ[f"{self.udid}_ui_tree"] = ""
        os.system(command)
        logger.debug(f"swipe from {from_x} {from_y} to {to_x} {to_y}")

    def drag(self, to_x, to_y, duration=0):
        from_x = self.center_coordinate()[0]
        from_y = self.center_coordinate()[1]
        duration = duration * 1000 + 2000
        command = f'adb -s {self.udid} shell input swipe {from_x} {from_y} {to_x} {to_y} {duration}'
        os.environ[f"{self.udid}_ui_tree"] = ""
        os.system(command)
        logger.debug(f"drag from {from_x} {from_y} to {to_x} {to_y}")

    def click(self, x=None, y=None, x_offset=None, y_offset=None):
        if x is None and y is None:
            x = self.center_coordinate()[0]
            y = self.center_coordinate()[1]
        if x_offset is not None:
            x = x + x_offset
        if y_offset is not None:
            y = y + y_offset
        command = f'adb -s {self.udid} shell input tap {x} {y}'
        os.system(command)
        logger.debug(f"click {x} {y}")

    def long_click(self, duration, x_offset=None, y_offset=None):
        x = self.center_coordinate()[0]
        y = self.center_coordinate()[1]
        if x_offset is not None:
            x = x + x_offset
        if y_offset is not None:
            y = y + y_offset
        command = f'adb -s {self.udid} shell input swipe {x} {y} {x} {y} {int(duration * 1000)}'
        os.system(command)
        logger.debug(f"long click {x} {y}")

    def set_text(self, text, append=False, x_offset=None, y_offset=None):
        len_of_text = 0 if self.text is None else len(self.text)
        self.click(x_offset=x_offset, y_offset=y_offset)
        os.system(f'adb -s {self.udid} shell input keyevent KEYCODE_MOVE_END')
        del_cmd = f'adb -s {self.udid} shell input keyevent'
        if not append:
            for _ in range(len_of_text + 8):
                del_cmd = del_cmd + " KEYCODE_DEL"
            os.system(del_cmd)
        text = text.replace("&", "\&").replace("\"", "")
        os.system(f'''adb -s {self.udid} shell input text "{text}"''')
        os.system(f'adb -s {self.udid} shell settings put global policy_control immersive.full=*')
        logger.debug(f"set text {text}")

    def set_seek_bar(self, percentage):
        x = self.bounds()[0] + self.bounds()[2] * percentage
        y = self.center_coordinate()[1]
        logger.debug(f"set seek bar to {percentage}")
        self.click(x, y)
        logger.debug(f"set seek bar to {percentage}")