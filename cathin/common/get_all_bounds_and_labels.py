from loguru import logger

from cathin.common.find_and_draw_con import process_image
from cathin.common.utils import _encode_image, _convert_keys_to_tuples, \
    _remove_overlapping, _sort_boxes_by_rows, _crop_and_encode_image

from cathin.common.request_api import _call_ocr_api,_call_classify_image_api



def get_all_bounds_and_labels(img, get_icon_des=False):
    all_bounds_and_labels = process_image(img, debug=False)
    logger.debug("Processed image")
    all_text_bounds_and_descriptions = _convert_keys_to_tuples(_call_ocr_api(_encode_image(img)).get("ocr_result"))
    logger.debug("OCR result received")
    non_text_bounds_and_labels = _remove_overlapping(all_bounds_and_labels, all_text_bounds_and_descriptions)
    non_text_bounds_and_labels = _sort_boxes_by_rows(non_text_bounds_and_labels)

    # Dictionary to keep track of counts for each class
    class_count_list = []
    classes_count_list = []

    class_count_dict = {}
    if get_icon_des:

        for index, bound_label in enumerate(non_text_bounds_and_labels):
            cropped_image = _crop_and_encode_image(img, [list(bound_label.keys())[0]])[0]
            classification_result = _call_classify_image_api(cropped_image)
            predicted_class = classification_result.get("top_predictions")[0][0]
            predicted_classes = f'{classification_result.get("top_predictions")[0][0]}_{classification_result.get("top_predictions")[1][0]}_{classification_result.get("top_predictions")[2][0]}'

            # Handle predicted_class and predicted_classes
            original_class = predicted_class
            original_classes = predicted_classes
            if class_count_list.count(original_class) > 0 and class_count_dict.get(original_class) != predicted_classes:
                original_class = predicted_classes
            predicted_class = f"{original_class}_{classes_count_list.count(original_classes) + 1}" if classes_count_list.count(
                original_classes) > 0 else original_class
            classes_count_list.append(original_classes)
            class_count_list.append(original_class)
            class_count_dict[predicted_class] = predicted_classes

            non_text_bounds_and_labels[index] = {list(bound_label.keys())[0]: ["icon", predicted_class]}

    # Update class names with suffixes and prefixes
    all_bounds = non_text_bounds_and_labels + all_text_bounds_and_descriptions
    all_bounds = _sort_boxes_by_rows(all_bounds)
    return all_bounds
