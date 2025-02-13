import cv2
import numpy as np
from loguru import logger


def show_resized_image(window_name, image, scale_percent=50, debug=True):
    if debug:
        # Calculate the dimensions after scaling
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)

        # Resize the image
        resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

        # Display the resized image
        cv2.imshow(window_name, resized_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def non_max_suppression(boxes, overlap_thresh):
    if len(boxes) == 0:
        return []

    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    pick = []

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(y2)

    while len(idxs) > 0:
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        overlap = (w * h) / area[idxs[:last]]

        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlap_thresh)[0])))

    return boxes[pick].astype("int")


def process_image(image, debug=True, clip_limit=3.0, tile_grid_size=(16, 16), blur_kernel_size=(5, 5),
                  canny_threshold1=30, canny_threshold2=200, morph_kernel_size=(3, 3), dilate_iterations=3,
                  erode_iterations=1, aspect_ratio_threshold=0.1, overlap_thresh=0.3):
    # Enhance contrast
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    enhanced_image = cv2.cvtColor(limg, cv2.COLOR_Lab2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2GRAY)

    # Use Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, blur_kernel_size, 0)

    # Use Canny edge detection to enhance edge detection
    edges = cv2.Canny(blurred, canny_threshold1, canny_threshold2)
    show_resized_image('Edges', edges, debug=debug)

    # Use morphological operations to enhance edges
    kernel = np.ones(morph_kernel_size, np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=dilate_iterations)
    edges = cv2.erode(edges, kernel, iterations=erode_iterations)

    # Perform binarization
    ret, binary = cv2.threshold(edges, 127, 255, cv2.THRESH_BINARY)
    show_resized_image('Binary', binary, debug=debug)

    # Find contours
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    # Create a mask
    h, w = binary.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)

    # Fill each closed region
    for i, contour in enumerate(contours):
        contour_area = cv2.contourArea(contour)
        parent_idx = hierarchy[0][i][3]
        if parent_idx != -1:
            parent_area = cv2.contourArea(contours[parent_idx])
            if contour_area < 0.5 * parent_area:
                cv2.drawContours(binary, [contour], 0, 255, -1)
                cv2.floodFill(binary, mask, (contour[0][0][0], contour[0][0][1]), 255)

    show_resized_image('Filled Image', binary, debug=debug)

    # Find contours of all levels
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Remove parent contours with similar aspect ratios
    to_remove = set()
    for i, contour in enumerate(contours):
        parent_idx = hierarchy[0][i][3]
        if parent_idx != -1:
            x, y, w, h = cv2.boundingRect(contour)
            child_aspect_ratio = w / h
            px, py, pw, ph = cv2.boundingRect(contours[parent_idx])
            parent_aspect_ratio = pw / ph
            if abs(child_aspect_ratio - parent_aspect_ratio) < aspect_ratio_threshold:
                to_remove.add(parent_idx)

    contours = [contour for i, contour in enumerate(contours) if i not in to_remove]

    # Get all bounding boxes
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        boxes.append([x, y, x + w, y + h])

    boxes = np.array(boxes)
    boxes = non_max_suppression(boxes, overlap_thresh)

    # Draw initial bounding boxes
    initial_boxes_image = image.copy()
    for (x1, y1, x2, y2) in boxes:
        cv2.rectangle(initial_boxes_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

    show_resized_image('Initial Boxes', initial_boxes_image, debug=debug)

    if len(boxes) == 0:
        logger.debug("No contours found")
        return []

    # Get all bounding boxes with labels
    boxes_and_labels = [{(x1, y1, x2 - x1, y2 - y1): "icon"} for (x1, y1, x2, y2) in boxes]

    # Draw merged bounding boxes
    merged_boxes_image = image.copy()
    for item in boxes_and_labels:
        for box, label in item.items():
            x, y, w, h = box
            cv2.rectangle(merged_boxes_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

    show_resized_image('Merged Boxes', merged_boxes_image, debug=debug)

    return boxes_and_labels