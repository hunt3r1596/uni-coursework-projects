from enum import Enum

import numpy as np

'''
    Constants for the RAS project
'''


LANE_LOW = np.array([20, 100, 100])
# LANE_HIGH = np.array([40, 140, 250])
LANE_HIGH = np.array([40, 150, 255])

# Crossing Markings
CROSSING_LOW = np.array([26, 135, 100])
CROSSING_HIGH = np.array([45, 255, 250])

TURN_RATE = 25
TURN_SPEED = 22

SIGNS_ROI = np.array([
    [(200, 100), (255, 100), (255, 40), (200, 40)]
])

LANE_ROI = np.array([
    [(40, 120), (216, 120), (196, 90), (50, 90)]
])

LANE_ROI = np.array([
    [(40, 120), (216, 120), (196, 90), (50, 90)]
])

C_BLUE = (255, 0, 0)
C_RED = (0, 0, 255)
C_GREEN = (0, 255, 0)

# Enums for defining turning directions
class Direction(Enum):
    STRAIGHT = 1
    RIGHT = 2
    LEFT = 3
    BACK = 4

    def get(self):
        return self.value
