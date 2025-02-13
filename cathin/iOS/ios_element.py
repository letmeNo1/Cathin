from cathin.common.request_api import _call_generate_image_caption_api
from cathin.common.utils import _crop_and_encode_image


from cathin.Android.action import Action


from loguru import logger

from cathin.common.attributes import Attribute


class Element(Action):
    def __init__(self, result_data):

        found_element_data = result_data.get("found_element_data")
        self.all_bounds = result_data.get("all_bounds")
        self.img = result_data.get("img")
        self.udid = result_data.get("udid")
        self.package_name = result_data.get("package_name")
        self.index = found_element_data[0]
        self.bounds = found_element_data[1]
        self.text = found_element_data[2]
        self.attribute = Attribute("Android", result_data)

        super().__init__(self.udid, self.bounds, self.text, self.package_name)

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
        cropped_image = _crop_and_encode_image(self.img, [self.bounds])
        text = _call_generate_image_caption_api(cropped_image[0]).get("descriptions")
        logger.debug("Description generated successfully")
        return text