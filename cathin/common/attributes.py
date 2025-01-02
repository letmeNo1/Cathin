

class Attribute:
    def __init__(self, platform, img, all_bounds, data, udid=None):
        self.img = img
        self.all_bounds = all_bounds
        self.index, self.bounds, self.text = data
        self.udid = udid
        self.platform = platform

    def left(self, offset=1):
        if self.platform == "Windows":
            from cathin.Windos.windows_element import Element
        elif self.platform == "Android":
            from cathin.Android.android_element import Element

        left_index = self.index - offset
        if left_index < 0:
            raise IndexError("Left index out of range")
        left_bounds, left_text = list(self.all_bounds[left_index].items())[0]
        return Element(self.img, self.all_bounds, [left_index, left_bounds, left_text], self.udid)

    def right(self, offset=1):
        if self.platform == "Windows":
            from cathin.Windos.windows_element import Element
        elif self.platform == "Android":
            from cathin.Android.android_element import Element
        right_index = self.index + offset
        if right_index >= len(self.all_bounds):
            raise IndexError("Right index out of range")
        right_bounds, right_text = list(self.all_bounds[right_index].items())[0]
        return Element(self.img, self.all_bounds, [right_index, right_text, right_text], self.udid)

    def up(self, offset=1):
        if self.platform == "Windows":
            from cathin.Windos.windows_element import Element
        elif self.platform == "Android":
            from cathin.Android.android_element import Element
        current_top_y = self.bounds[1]
        current_center_x = self.bounds[0] + self.bounds[2] // 2
        closest_elements = []

        for up_index in range(self.index - 1, -1, -1):
            up_bounds, up_text = list(self.all_bounds[up_index].items())[0]

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
        if self.platform == "Windows":
            from cathin.Windos.windows_element import Element
        elif self.platform == "Android":
            from cathin.Android.android_element import Element
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
                    (distance, Element(self.img, self.all_bounds, [down_index, down_bounds, down_text], self.udid)))

        closest_elements.sort(key=lambda x: x[0])
        if len(closest_elements) < offset:
            raise IndexError("No element found below the current element with the given offset")
        return closest_elements[offset - 1][1]
