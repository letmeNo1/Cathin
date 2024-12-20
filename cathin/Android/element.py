from cathin.common.request_api import _call_generate_image_caption_api
from cathin.common.utils import _crop_and_encode_image

from cathin.Android.action import Action
from loguru import logger

from cathin.common.find_method import MultipleValuesFoundError


class LazyElement:
    def __init__(self, find_element_func, **query):
        self.find_element_func = find_element_func
        self.query = query
        self._element = None

    def _find_element(self):
        if self._element is None:
            self._element = self.find_element_func(**self.query)
        return self._element

    def __getattr__(self, item):
        element = self._find_element()
        data = element.get("data")
        udid = element.get("udid")
        all_bounds = element.get("all_bounds")
        img = element.get("img")

        if len(data) > 1:
            raise MultipleValuesFoundError(f"Finding multiple elements", data)
        else:
            logger.debug(f"Found element: {data}")
            return getattr(Element(img, all_bounds, data[0],udid), item)

    def __getitem__(self, index):
        element = self._find_element()
        data = element.get("data")
        udid = element.get("udid")
        all_bounds = element.get("all_bounds")
        img = element.get("img")
        return Element(img,all_bounds,data[index], udid)


class Element(Action):
    def __init__(self, img, all_bounds, data, udid):
        self.index = data[0]
        self.all_bounds = all_bounds
        self.img = img
        self.udid = udid
        bounds = data[1]
        text = data[2]
        super().__init__(udid, bounds, text)

    def left(self, offset=1):
        left_index = self.index - offset
        if left_index < 0:
            raise IndexError("Left index out of range")
        left_bounds, left_text = list(self.all_bounds[left_index].items())[0]
        return Element(self.img, self.all_bounds, [left_index, left_bounds, left_text], self.udid)

    def right(self, offset=1):
        right_index = self.index + offset
        if right_index >= len(self.all_bounds):
            raise IndexError("Right index out of range")
        right_bounds, right_text = list(self.all_bounds[right_index].items())[0]
        return Element(self.img, self.all_bounds, [right_index, right_text, right_text], self.udid)

    def up(self, offset=1):
        current_top_y = self.bounds[1]
        current_center_x = self.bounds[0] + self.bounds[2] // 2
        closest_elements = []

        for up_index in range(self.index - 1, -1, -1):
            up_bounds, up_text = list(self.all_bounds[i].items())[0]

            element_bottom_y = up_bounds[1] + up_bounds[3]
            element_center_x = up_bounds[0] + up_bounds[2] // 2

            if element_bottom_y <= current_top_y:
                distance = current_top_y - element_bottom_y + abs(current_center_x - element_center_x)
                closest_elements.append(
                    (distance, Element(self.img, self.all_bounds, [up_index, up_bounds, up_text], self.udid)))

        closest_elements.sort(key=lambda x: x[0])
        if len(closest_elements) < offset:
            raise IndexError("No element found above the current element with the given offset")
        return closest_elements[offset - 1][1]

    def down(self, offset=1):
        current_bottom_y = self.bounds[1] + self.bounds[3]
        current_center_x = self.bounds[0] + self.bounds[2] // 2
        closest_elements = []

        for down_index in range(self.index + 1, len(self.all_bounds)):
            down_bounds, down_text = list(self.all_bounds[down_index].items())[0]
            element_top_y = down_bounds[1]
            element_center_x = down_bounds[0] + down_bounds[2] // 2
            if element_top_y >= current_bottom_y:
                distance = element_top_y - current_bottom_y + abs(current_center_x - element_center_x)
                closest_elements.append(
                    (distance, Element(self.img, self.all_bounds, [i, down_bounds, down_text], self.udid)))

        closest_elements.sort(key=lambda x: x[0])
        if len(closest_elements) < offset:
            raise IndexError("No element found below the current element with the given offset")
        return closest_elements[offset - 1][1]

    @property
    def description(self):
        logger.debug("Description being generated")
        a = _crop_and_encode_image(self.img, [self.bounds])
        text = _call_generate_image_caption_api(a).get("descriptions")[0]
        logger.debug("Description generated successfully")
        return text
