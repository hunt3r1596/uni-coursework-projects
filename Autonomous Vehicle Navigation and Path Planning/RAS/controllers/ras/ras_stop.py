import time
import cv2
import numpy as np
from ras_constants import *


# To get mask for detecting stop sign boards
def get_sign_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Define the lower and upper bounds for the red color
    lower_red_1 = np.array([0, 50, 50])
    upper_red_1 = np.array([10, 255, 255])
    lower_red_2 = np.array([160, 30, 30])
    upper_red_2 = np.array([180, 255, 255])

    # Create masks
    kernel_size = (1, 1)
    mask1 = cv2.GaussianBlur(cv2.inRange(hsv, lower_red_1, upper_red_1), kernel_size, 0)
    mask2 = cv2.GaussianBlur(cv2.inRange(hsv, lower_red_2, upper_red_2), kernel_size, 0)
    mask = cv2.bitwise_or(mask1, mask2)

    # Apply morphological operations to the mask
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


# Get the stop sign templates
def get_stop_templates():
    templates = []
    for i in range(0, 4):
        template = cv2.imread(f'../../res/stopPrototype_{i}.png')
        template = cv2.resize(template, (24, 24), interpolation=cv2.INTER_LINEAR)
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        templates.append(gray_template)
    return templates


# Perform template matching
def match_templates(stop_roi, stop_templates, threshold=0.5):
    for i in range(0, 4):
        res = cv2.matchTemplate(stop_roi, stop_templates[i], cv2.TM_CCOEFF_NORMED)
        loc = cv2.minMaxLoc(res)

        # If the match value is above the threshold, a stop sign is detected
        if loc[1] > threshold:
            return True, loc[1]
    return False, 0


# Scan for stop sign in the image
def scan_for_template(img, stop_templates):
    stop_sign_detected = False

    sign_mask = get_sign_mask(img)

    # Find contours in the mask
    contours, hierarchy = cv2.findContours(sign_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Iterate through each contour and perform template matching
    for contour in contours:

        is_in_roi = cv2.pointPolygonTest(SIGNS_ROI, tuple(contour.tolist()[0][0]), False)
        if is_in_roi < 0:
            continue

        # Get the bounding box of the contour
        x, y, w, h = cv2.boundingRect(contour)

        # Crop the image to the bounding box
        roi = img[y:y + h, x:x + w]

        # Resize the image to the size of the template
        roi = cv2.resize(roi, (24, 24), interpolation=cv2.INTER_AREA)

        # Convert the cropped image to grayscale
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Perform template matching
        is_match, match_value = match_templates(gray_roi, stop_templates, 0.5)

        # cv2.drawContours(img, contour, -1, (0, 255, 0), 1)

        if match_value > 0:
            cv2.putText(img, f'{match_value:.2f}', (x, y-5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

        # cv2.drawContours(img, [contour], 0, (0, 0, 255), 1)
        if is_match:
            img_tmp = img.copy()
            cv2.rectangle(img_tmp, (x, y), (x + w, y + h), (0, 255, 0), cv2.FILLED)
            img = cv2.addWeighted(img, 1, img_tmp, 0.25, 0)

            # print('Stop sign detected at ({}, {}) with threshold: {}'.format(x + w / 2, y + h / 2, loc[1]))
            stop_sign_detected = True
            break

    cv2.polylines(img, SIGNS_ROI, True, (0, 255, 0), 2)
    return img, stop_sign_detected


def is_stop_detection_active(last_stop_time):
    return last_stop_time is None or time.time() - last_stop_time > 10
