import os

from cathin.common.attributes import Attribute
from cathin.common.request_api import _call_generate_image_caption_api
from cathin.common.utils import _crop_and_encode_image
from cathin.Windows.action import Action
from loguru import logger


class Element(Action):
    def __init__(self, result_data):
        found_element_data = result_data.get("found_element_data")
        self.all_bounds = result_data.get("all_bounds")
        self.img = result_data.get("img")
        self.left = result_data.get("left")
        self.top = result_data.get("top")
        self.index = found_element_data[0]
        self.bounds = found_element_data[1]
        self.text = found_element_data[2]
        self.attribute = Attribute("Windows", result_data)
        self.bounds = (
            self.bounds[0] + self.left,  # left
            self.bounds[1] + self.top,  # top
            self.bounds[2],  # w
            self.bounds[3],  # h
        )
        super().__init__(self.bounds, self.text)

    def left(self, offset=1):
        return self.attribute.left(offset)

    def right(self, offset=1):
        return self.attribute.right(offset)

    def up(self, offset=1):
        return self.attribute.up(offset)

    def down(self, offset=1):
        return self.attribute.down(offset)

    @property
    def description(self):
        logger.debug("Description being generated")
        a = _crop_and_encode_image(self.img, [self.bounds])
        text = _call_generate_image_caption_api(a).get("descriptions")[0]
        logger.debug("Description generated successfully")
        return text
