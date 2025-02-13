from loguru import logger
from cathin.common.find_method import MultipleValuesFoundError


class LazyElement:
    def __init__(self, platform, find_element_func, **query):
        self.find_element_func = find_element_func
        self.query = query
        self.platform = platform
        self.element = None

    def _find_element(self):
        if self.element is None:
            self.element = self.find_element_func(**self.query)
        return self.element

    def _create_element(self, element_data):
        if self.platform == "windows":
            from cathin.Windows.windows_element import Element
        elif self.platform == "android":
            from cathin.Android.android_element import Element
        elif self.platform == "ios":
            from cathin.iOS.ios_element import Element
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")
        return Element(element_data)

    def __getattr__(self, item):
        element_data = self._find_element()
        data = element_data.get("found_element_data")
        if len(data) > 1:
            raise MultipleValuesFoundError(f"Multiple elements found: ", data)
        else:
            logger.debug(f"Found element: {data[0]}")
            element_data["found_element_data"] = data[0]
            return getattr(self._create_element(element_data), item)

    def __getitem__(self, index):
        element_data = self._find_element()
        data = element_data.get("found_element_data")
        if index >= len(data):
            raise IndexError(f"Index {index} out of range for elements: {data}")
        element_data["found_element_data"] = data[index]

        return self._create_element(element_data)
