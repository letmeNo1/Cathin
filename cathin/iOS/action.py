import os

from loguru import logger

from cathin.common.runtime_cache import RunningCache
from cathin.common.send_request import send_tcp_request


class Action:
    def __init__(self, udid, bounds, text, package_name):
        self.udid = udid
        self.bounds = bounds
        self.text = text
        self.package_name = package_name

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

    def click(self, x=None, y=None, x_offset=None, y_offset=None):
        RunningCache(self.udid).get_current_running_port()

        if x is None and y is None:
            x = self.center_coordinate()[0]
            y = self.center_coordinate()[1]
        if x_offset is not None:
            x = x + x_offset
        if y_offset is not None:
            y = y + y_offset
        send_tcp_request(RunningCache(self.udid).get_current_running_port(), f"coordinate_action:{self.package_name}:click:{x}:{y}:none")
        RunningCache(self.udid).clear_current_cache_ui_tree()
        logger.debug(f"click {x} {y}")

    def long_click(self, duration, x_offset=None, y_offset=None):
        x = self.center_coordinate()[0]
        y = self.center_coordinate()[1]
        if x_offset is not None:
            x = x + x_offset
        if y_offset is not None:
            y = y + y_offset
        send_tcp_request(RunningCache(self.udid).get_current_running_port(), f"coordinate_action:{self.package_name}:press:{x}:{y}:{float(duration)}")
        RunningCache(self.udid).clear_current_cache_ui_tree()
        logger.debug(f"click {x} {y}")

    def set_text(self, text):
        send_tcp_request(RunningCache(self.udid).get_current_running_port(), f"coordinate_action:{self.package_name}:enter_text:none:none:{text}")
        RunningCache(self.udid).clear_current_cache_ui_tree()

    def set_seek_bar(self, percentage):
        x = self.bounds()[0] + self.bounds()[2] * percentage
        y = self.center_coordinate()[1]
        logger.debug(f"set seek bar to {percentage}")
        self.click(x, y)
        logger.debug(f"set seek bar to {percentage}")