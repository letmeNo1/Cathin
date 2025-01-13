import time

import cv2
import numpy as np
from loguru import logger


def show_resized_image(window_name, image, scale_percent=40, debug=True):
    if debug:
        # 计算缩放后的尺寸
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)

        # 调整图像大小
        resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

        # 显示缩放后的图像
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
                  erode_iterations=1, aspect_ratio_threshold=0.1, overlap_thresh=1):
    # 增强对比度
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    enhanced_image = cv2.cvtColor(limg, cv2.COLOR_Lab2BGR)

    # 转换为灰度图像
    gray = cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2GRAY)

    # 使用高斯模糊来减少噪声
    blurred = cv2.GaussianBlur(gray, blur_kernel_size, 0)

    # 使用Canny边缘检测，增强边缘检测效果
    edges = cv2.Canny(blurred, canny_threshold1, canny_threshold2)
    show_resized_image('Edges', edges, debug=debug)

    # 使用形态学操作来增强边缘
    kernel = np.ones(morph_kernel_size, np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=dilate_iterations)
    edges = cv2.erode(edges, kernel, iterations=erode_iterations)

    # 进行二值化处理
    ret, binary = cv2.threshold(edges, 127, 255, cv2.THRESH_BINARY)
    show_resized_image('Binary', binary, debug=debug)

    # 查找轮廓
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    # 创建一个掩码
    h, w = binary.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)

    # 填充每个封闭区域
    for i, contour in enumerate(contours):
        contour_area = cv2.contourArea(contour)
        parent_idx = hierarchy[0][i][3]
        if parent_idx != -1:
            parent_area = cv2.contourArea(contours[parent_idx])
            if contour_area < 0.5 * parent_area:
                cv2.drawContours(binary, [contour], 0, 255, -1)
                cv2.floodFill(binary, mask, (contour[0][0][0], contour[0][0][1]), 255)

    show_resized_image('Filled Image', binary, debug=debug)

    # 查找所有层次的轮廓
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # 删除长宽比相似的父轮廓
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

    # 获取所有边界框
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        boxes.append([x, y, x + w, y + h])

    boxes = np.array(boxes)
    boxes = non_max_suppression(boxes, overlap_thresh)

    # 绘制初始的矩形框
    initial_boxes_image = image.copy()
    for (x1, y1, x2, y2) in boxes:
        cv2.rectangle(initial_boxes_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

    show_resized_image('Initial Boxes', initial_boxes_image, debug=debug)

    if len(boxes) == 0:
        logger.debug("No contours found")
        return []

    # 获取所有边界框
    boxes_and_labels = [{(x1, y1, x2 - x1, y2 - y1): "icon"} for (x1, y1, x2, y2) in boxes]

    # 绘制合并后的矩形框
    merged_boxes_image = image.copy()
    for item in boxes_and_labels:
        for box, label in item.items():
            x, y, w, h = box
            cv2.rectangle(merged_boxes_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

    show_resized_image('Merged Boxes', merged_boxes_image, debug=debug)

    return boxes_and_labels

image_path = r"C:\Users\Administrator\Documents\GitHub\vision-ui\capture\local_imagess\34.jpg"

img = cv2.imread(image_path)


start_time = time.time()
process_image(img,debug=False)
end_time = time.time()

elapsed_time = end_time - start_time
print(f"处理图像耗时: {elapsed_time} 秒")