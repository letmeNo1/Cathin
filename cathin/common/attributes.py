class Attribute:
    def __init__(self, platform, result_data):
        self.platform = platform
        self.result_data = result_data
        self.img = result_data.get("img")
        self.all_bounds = result_data.get("all_bounds")
        self.index = result_data.get("found_element_data")[0]
        self.bounds = result_data.get("found_element_data")[1]

    def left(self, offset=1):
        # Import the appropriate Element class based on the platform
        if self.platform == "Windows":
            from cathin.Windows.windows_element import Element
        elif self.platform == "Android":
            from cathin.Android.android_element import Element

        # Calculate the left and right indices
        left_index = self.index - offset
        right_index = self.index + offset

        # Check if the left index is out of range
        if left_index < 0:
            raise IndexError("Left index out of range")

        # Get the current, left, and right bounds and text
        current_bounds = list(self.all_bounds[self.index].keys())[0]
        left_bounds, left_text = list(self.all_bounds[left_index].items())[0]
        right_bounds, right_text = list(self.all_bounds[right_index].items())[0]

        # Select which side to update the result data based on bounds position
        if left_bounds[0] < current_bounds[0]:
            selected_index, selected_bounds, selected_text = right_index, right_bounds, right_text
        else:
            selected_index, selected_bounds, selected_text = left_index, left_bounds, left_text

        # Update the result data
        self.result_data["found_element_data"] = [selected_index, selected_bounds, selected_text]

        # Return a new Element object
        return Element(self.result_data)

    def right(self, offset=1):
        # Import the appropriate Element class based on the platform
        if self.platform == "Windows":
            from cathin.Windows.windows_element import Element
        elif self.platform == "Android":
            from cathin.Android.android_element import Element

        # Calculate the left and right indices
        left_index = self.index - offset
        right_index = self.index + offset

        # Check if the right index is out of range
        if right_index >= len(self.all_bounds):
            raise IndexError("Right index out of range")

        # Get the left, right, and current bounds and text
        left_bounds, left_text = list(self.all_bounds[left_index].items())[0]
        right_bounds, right_text = list(self.all_bounds[right_index].items())[0]
        current_bounds, _ = list(self.all_bounds[self.index].items())[0]

        # Select which side to update the result data based on bounds position
        if right_bounds[0] < current_bounds[0]:
            selected_index, selected_bounds, selected_text = left_index, left_bounds, left_text
        else:
            selected_index, selected_bounds, selected_text = right_index, right_bounds, right_text

        # Update the result data
        self.result_data["found_element_data"] = [selected_index, selected_bounds, selected_text]

        # Return a new Element object
        return Element(self.result_data)

    def up(self, offset=1):
        if self.platform == "Windows":
            from cathin.Windows.windows_element import Element
        elif self.platform == "Android":
            from cathin.Android.android_element import Element
        current_top_y = self.bounds[1]
        current_center_x = self.bounds[0] + self.bounds[2] // 2
        closest_elements = []

        for up_index in range(self.index - 1, -1, -1):
            up_bounds, up_bounds = list(self.all_bounds[up_index].items())[0]

            element_bottom_y = up_bounds[1] + up_bounds[3]
            element_center_x = up_bounds[0] + up_bounds[2] // 2

            if element_bottom_y <= current_top_y:
                distance = current_top_y - element_bottom_y + abs(current_center_x - element_center_x)
                self.result_data["found_element_data"][0] = up_index
                self.result_data["found_element_data"][1] = up_bounds
                self.result_data["found_element_data"][2] = up_bounds
                closest_elements.append(
                    (distance, Element(self.result_data)))

        closest_elements.sort(key=lambda x: x[0])
        if len(closest_elements) < offset:
            raise IndexError("No element found above the current element with the given offset")
        return closest_elements[offset - 1][1]

    def down(self, offset=1):
        if self.platform == "Windows":
            from cathin.Windows.windows_element import Element
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
                self.result_data["found_element_data"][0] = down_index
                self.result_data["found_element_data"][1] = down_bounds
                self.result_data["found_element_data"][2] = down_text
                closest_elements.append(
                    (distance, Element(self.result_data)))

        closest_elements.sort(key=lambda x: x[0])
        if len(closest_elements) < offset:
            raise IndexError("No element found below the current element with the given offset")
        return closest_elements[offset - 1][1]
