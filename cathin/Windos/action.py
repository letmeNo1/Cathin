import os

import pyautogui
from loguru import logger


class Action:
    def __init__(self, bounds, text):
        self.bounds = bounds
        self.text = text

    def center_coordinate(self):
        x, y, w, h = self.bounds
        center_x = x + w // 2
        center_y = y + h // 2
        return center_x, center_y

    def click(self):
        x, y = self.center_coordinate()
        pyautogui.click(x, y)