import numpy as np

from rasrobot import RASRobot

from ras_move import *
from ras_mini_map import MiniMap
from ras_stop import *

import cv2

from collections import deque


class MyRobot(RASRobot):
    def __init__(self):
        """
        The constructor has no parameters.
        """
        super(MyRobot, self).__init__()

        # Initialise and resize a new window
        cv2.namedWindow("output", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("output", 256 * 2, 128 * 2)
        cv2.namedWindow("output", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("output", 256 * 2, 128 * 2)

        self.queue = deque(maxlen=15)

        self.vehicle_state = None

        self.start_point = None

        # Minimap for mapping path and Navigation
        self.mini_map = MiniMap(size=40, map_scale_factor=30)
        self.stop_timer = None
        self.previous_charge = 500

        self.stop_templates = get_stop_templates()
        self.last_stop_time = None

    def is_charging(self):
        return self.previous_charge <= self.time_to_live

    def is_low_charge(self):
        return self.time_to_live <= 100
        # return self.time_to_live <= 230

    def is_charged(self):
        return self.time_to_live >= 0.9 * 240

    def get_road(self):
        """
        This method relies on the `get_camera_image` method from RASRobot. It takes the image, converts
        it into HSV (Hue, Saturation, Value) and filters pixels that belong to the three following
        ranges:
        - Hue: 0-200 (you may want to tweak this)
        - Saturation: 0-50    (you may want to tweak this)
        - Value: 0-100    (you may want to tweak this)
        """
        image = self.get_camera_image()

        # Pre-process the image
        processed_mask = pre_process_image(image)

        # Lane Region of Interest Mask
        roi_mask = get_roi(image, roi_type='lane')

        processed_mask = cv2.bitwise_and(processed_mask, roi_mask)

        # Apply the mask to the image
        image_view = apply_mask(image, roi_mask)

        image, stop_sign = scan_for_template(image, self.stop_templates)

        return image, cv2.morphologyEx(image_view, cv2.MORPH_OPEN, (3, 3)), processed_mask, stop_sign

    def run(self):
        """
        This function implements the main loop of the robot.
        """
        prev_turn_rate = 0
        prev_charging_state = False

        while self.tick():

            # Setting initial offset to the origin
            if self.start_point is None:
                self.start_point = self.get_gps_values()
                self.mini_map.set_origin_offset(self.start_point)

            speed = 50

            raw_image, image, road_mask, stop_sign = self.get_road()

            # Check if the stop sign detection is active (not on cooldown)
            if is_stop_detection_active(self.last_stop_time):
                if stop_sign is True:
                    self.stop_timer = time.time()
                    self.last_stop_time = time.time()
                    print('Setting speed to 0')

            if self.stop_timer is not None and time.time() - self.stop_timer < 7:
                print('waiting, ', round(time.time() - self.stop_timer, 2))
                speed = 0
            else:
                speed = 40
                self.stop_timer = None

            turn_rate, v_state = turn_rate_from_path(image, road_mask, prev_turn_rate, self.vehicle_state, self.is_low_charge(), self.mini_map)
            self.vehicle_state = v_state

            if self.is_low_charge() and not self.is_charging() and int(self.time_to_live) % 20 == 0:
                print(f'Low charge: {self.time_to_live}')

            # Clear path once reached to charging points
            if self.is_charging():
                self.mini_map.path.clear()

            if abs(turn_rate) >= 20:
                speed = TURN_SPEED

            # Wait until 90% charged
            if self.is_charging() and not self.is_charged():
                speed = 0
                print('Waiting to charge... (90%) : ', round(self.time_to_live * 100 /240, 2))

            self.set_speed(speed)
            self.set_steering_angle(turn_rate / 100)

            prev_turn_rate = turn_rate

            # Update the minimap based on gps
            self.mini_map.update(self.get_gps_values(), self.vehicle_state, self.is_charging())

            # Set charging point once identified (start point)
            if self.is_charging() and len(self.mini_map.charging_points) == 0:
                    self.mini_map.set_charging_point()

            # Set charging point once identified (end point)
            if not self.is_charging():
                if prev_charging_state and len(self.mini_map.charging_points) == 1:
                    self.mini_map.set_charging_point()

            # Show the minimap
            self.mini_map.show()

            self.previous_charge = self.time_to_live
            prev_charging_state = self.is_charging()

            cv2.imshow('output', image)
            cv2.waitKey(1)


# The API of the MyRobot class, is extremely simple, not much to explain.
# We just create an instance and let it do its job.
robot = MyRobot()
robot.run()
