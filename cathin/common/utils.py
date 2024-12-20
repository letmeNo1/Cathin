import base64
import cv2

def __is_overlapping(rect1, rect2):
    """
    Check if two rectangles are overlapping.
    rect1 and rect2 are in the format (x1, y1, width1, height1).
    """
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2

    # Calculate the bottom-right coordinates of the rectangles
    x1_br, y1_br = x1 + w1, y1 + h1
    x2_br, y2_br = x2 + w2, y2 + h2

    # Check for overlap
    if x1 < x2_br and x1_br > x2 and y1 < y2_br and y1_br > y2:
        return True
    return False

def _remove_overlapping(A, B):
    """
    Remove parts of dictionary array A that are overlapped by dictionary array B.
    """
    result = []
    for dict_a in A:
        rect_a = list(dict_a.keys())[0]
        overlap = False
        for dict_b in B:
            rect_b = list(dict_b.keys())[0]
            if __is_overlapping(rect_a, rect_b):
                overlap = True
                break
        if not overlap:
            result.append(dict_a)
    return result

def _encode_image(image):
    """
    Encode a single image to Base64 format.

    :param image: The image to be encoded.
    :return: Base64 encoded string of the image.
    """
    _, buffer = cv2.imencode('.png', image)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    return img_base64

def _crop_and_encode_image(image, rectangles):
    """
    Crop and encode multiple images to Base64 format.

    :param image: The original image.
    :param rectangles: List of rectangles to crop from the image.
    :return: List of Base64 encoded strings of the cropped images.
    """
    cropped_images_base64 = []
    for rect in rectangles:
        x, y, w, h = rect
        cropped_img = image[y:y + h, x:x + w]
        _, buffer = cv2.imencode('.png', cropped_img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        cropped_images_base64.append(img_base64)
    return cropped_images_base64

def _convert_keys_to_tuples(data):
    """
    Convert string-form tuple keys in a list of dictionaries back to actual tuple keys.

    :param data: List[Dict[str, str]] - List of dictionaries with string-form tuple keys.
    :return: List[Dict[Tuple[int, int, int, int], str]] - List of dictionaries with actual tuple keys.
    """
    converted_data = []
    for item in data:
        converted_item = {}
        for key, value in item.items():
            # Convert string-form tuple back to actual tuple
            bounds = tuple(map(int, key.strip('()').split(',')))
            converted_item[bounds] = value
        converted_data.append(converted_item)
    return converted_data

def __add_overlapping_descriptions(A, B):
    """
    Detect parts of A that are covered by B and add B's descriptions to all_bounds_and_des dictionary.
    A and B are in the format [(x1, y1, width1, height1), ...]
    all_text_bounds_and_des is a dictionary where keys are rectangle bounds and values are descriptions.
    """
    all_bounds_and_des = {}
    covered_by_b = set()

    for rect_b, description in B.items():
        for rect_a in A:
            if __is_overlapping(rect_a, rect_b):
                covered_by_b.add(rect_a)
                all_bounds_and_des[rect_b] = description

    for rect_a in A:
        if rect_a not in covered_by_b:
            all_bounds_and_des[rect_a] = "no des"

    return all_bounds_and_des

def _sort_boxes_by_rows(boxes, row_threshold=10):
    """
    Sort rectangles in a dictionary array by rows, first by the center y-coordinate, then by the center x-coordinate.
    """
    # Extract rectangles and sort by the center y-coordinate
    boxes = sorted(boxes, key=lambda box: (list(box.keys())[0][1] + list(box.keys())[0][3] / 2))

    rows = []
    current_row = []
    current_y = None

    for box_dict in boxes:
        rect = list(box_dict.keys())[0]
        x, y, w, h = rect
        center_y = y + h / 2

        if current_y is None or abs(center_y - current_y) <= row_threshold:
            current_row.append(box_dict)
            current_y = center_y
        else:
            rows.append(current_row)
            current_row = [box_dict]
            current_y = center_y

    if current_row:
        rows.append(current_row)

    # Sort each row by the center x-coordinate
    sorted_boxes = []
    for row in rows:
        sorted_boxes.extend(sorted(row, key=lambda box: list(box.keys())[0][0] + list(box.keys())[0][2] / 2))

    return sorted_boxes