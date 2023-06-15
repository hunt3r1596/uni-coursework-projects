import math
import random

import numpy as np
import cv2
from ras_constants import *

# Display Image
def display_image(image, name, size=(256 * 2, 128 * 2)):
    cv2.namedWindow(name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(name, size[0], size[1])
    cv2.imshow(name, image)


# To get Region of Interest Mask
def get_roi(image, roi_type='lane'):
    if type == 'lane':
        viewport = LANE_ROI
    elif roi_type == 'sign':
        viewport = SIGNS_ROI
    else:
        viewport = LANE_ROI

    view_mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
    cv2.fillPoly(view_mask, viewport, (255, 255, 255))

    return view_mask


# To Apply Mask to image
def apply_mask(image, roi_mask, color=(0, 255, 0), thickness = cv2.FILLED):
    roi_contours, _ = cv2.findContours(roi_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    alpha = 0.25
    filled_contours = np.zeros_like(image)
    cv2.drawContours(filled_contours, roi_contours, -1, color, thickness)

    image = cv2.addWeighted(image, 1, filled_contours, alpha, 0)
    return image


# Morphological Operations to clean the mask
def clean(mask):
    # Apply the erode operation
    mask = cv2.erode(mask, (1, 1), iterations=1)

    # Apply the dilation operation
    mask = cv2.dilate(mask, (3, 3), iterations=2)

    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, (5, 5), iterations=5)

    # Apply a Gaussian blur to reduce noise
    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    return mask


# Getting the color mask based on HSV thresholds
def get_color_mask(hsv, low, high):
    mask = cv2.inRange(hsv, low, high)
    mask = clean(mask)
    return mask


# Preprocessing the image
def pre_process_image(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    crossing_mask = get_color_mask(hsv, CROSSING_LOW, CROSSING_HIGH)
    lane_mask = get_color_mask(hsv, LANE_LOW, LANE_HIGH)

    # display_image(crossing_mask, 'Crossing Mask')

    tmp_mask = cv2.bitwise_and(lane_mask, crossing_mask)
    mask = cv2.bitwise_or(lane_mask, tmp_mask)

    return mask


# To detect the bumpy crossings
def cross_ahead(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    crossing_mask = get_color_mask(hsv, CROSSING_LOW, CROSSING_HIGH)
    x = find_counters(crossing_mask, min_area=150)
    if len(x) > 0:
        largest_contour = np.vstack(x)
        if cv2.contourArea(largest_contour) > 500:
            return True

    return False


# Finding the contours for the mask
def find_counters(mask, min_area=0):
    # Find the contours in the binary image
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Filter the contours based on the area
    if min_area > 0:
        filtered_contours = []
        for contour in contours:
            if cv2.contourArea(contour) > min_area:
                filtered_contours.append(contour)
        return filtered_contours
    return contours


# Picking Random Turn
def pick_random_turn():
    choice = random.choice([Direction.LEFT, Direction.RIGHT])
    if choice == Direction.LEFT:
        steering_angle = -TURN_RATE
    elif choice == Direction.RIGHT:
        steering_angle = TURN_RATE
    return steering_angle


# To find angle between two points
def angle_between_points(point1, point2):
    delta_x, delta_y = point2[0] - point1[0], point2[1] - point1[1]
    return math.atan2(delta_y, delta_x)


# To find the turn based on previous location, current and next nav location
def find_turn_angle(prev, curr, next):
    angle1 = angle_between_points(prev, curr)
    angle2 = angle_between_points(curr, next)
    turn_angle = (angle2 - angle1 + 2 * math.pi) % (2 * math.pi)

    # print(prev, curr, next)
    # print(f'Turn angle: {math.degrees(turn_angle)}')

    if turn_angle == 0:
        return Direction.STRAIGHT
    elif turn_angle == math.pi:
        return Direction.BACK
    elif turn_angle == math.pi / 2 or 0 < turn_angle < math.pi:
        return Direction.RIGHT
    elif turn_angle == 3 * math.pi / 2 or math.pi < turn_angle < 2 * math.pi:
        return Direction.LEFT


# To find the turn rate for the vehicle
def turn_rate_from_path(image, road_mask, prev_steering_angle, vehicle_state, is_low_charge, mini_map):
    steering_angle = 0
    cy = 105

    # Find the contours in the binary image
    contours = find_counters(road_mask, min_area=100)

    # If any contours are found, select the one with the largest area
    if len(contours) > 0:
        vehicle_state = 'lane'
        largest_contour = max(contours, key=cv2.contourArea)

        # Find the centroid of the largest contour
        M = cv2.moments(largest_contour)

        if M['m00'] == 0 or M['m01'] == 0:
            return steering_angle

        cx = int(M['m10'] / M['m00'])

        steering_angle = cx - len(image[0]) // 2

        cv2.circle(image, (cx - steering_angle, cy), 2, (0, 255, 0), -1)  # Center of Path

    elif vehicle_state != 'intersection' and not cross_ahead(image):
        vehicle_state = 'intersection'

        # Default (Random) Turn
        steering_angle = pick_random_turn()

        # If low charge, find the path to the charging points
        if is_low_charge:
            mini_map.path_to_charging_points()

            # If path is found, find the turn angle
            if len(mini_map.path) > 0:
                pp = (mini_map.previous_position[1], mini_map.previous_position[0])
                cp = (mini_map.current_position[1], mini_map.current_position[0])
                n1 = mini_map.path[1]

                turn = find_turn_angle(pp, cp, n1)
                print('Select n1: ', turn)

                if turn == Direction.LEFT:
                    steering_angle = -TURN_RATE
                elif turn == Direction.RIGHT:
                    steering_angle = TURN_RATE
                elif turn == Direction.STRAIGHT:
                    steering_angle = prev_steering_angle
                else:
                    steering_angle = pick_random_turn()

    else:
        steering_angle = prev_steering_angle

    x_center = (len(image[0]) // 2)

    if steering_angle > 0:
        cv2.putText(image, f'{steering_angle:.2f}', ((x_center * 2) - 50, 20), cv2.FONT_HERSHEY_COMPLEX, 0.5, C_BLUE, 1)
    elif steering_angle < 0:
        cv2.putText(image, f'{abs(steering_angle):.2f}', (2, 20), cv2.FONT_HERSHEY_COMPLEX, 0.5, C_RED, 1)

    steering_angle = np.clip(steering_angle, -TURN_RATE, TURN_RATE)

    return steering_angle, vehicle_state
