import cv2
import numpy as np
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.dijkstra import DijkstraFinder
from ras_constants import *

# http://theory.stanford.edu/~amitp/GameProgramming/AStarComparison.html
# https://pypi.org/project/pathfinding/
# Map built based on gps values of the vehicle (scaled-down by given factor)
class MiniMap:
    def __init__(self, size, map_scale_factor=15, base_color=(255, 255, 255)):
        self.size = size
        self.map_scale_factor = map_scale_factor
        self.origin_offset = (0, 0)
        self.current_position = (0, 0)
        self.previous_position = (0, 0)

        self.map = np.full((size, size, 3), base_color, dtype=np.uint8)
        self.charging_points = []
        self.path = []

        self.previous_position_set = set()

    def set_origin_offset(self, offset):
        self.origin_offset = offset  #

    def set_charging_point(self):
        self.charging_points.append(self.current_position)
        print(f'Charging points: {self.charging_points}')
        self.map[self.current_position[0], self.current_position[1]] = C_BLUE

    # Encoding the gps values to the map array indices
    def encode_gps(self, gps_value):
        g1 = gps_value[0] - self.origin_offset[0]  # x-axis
        g2 = gps_value[1] - self.origin_offset[1]  # y-axis
        # Get scaled-down values
        g1 = g1 // self.map_scale_factor
        g2 = g2 // self.map_scale_factor
        # Convert to Array indices with initial position at center of array
        x = int((self.map.shape[0] // 2) + g1)
        y = int((self.map.shape[1] // 2) + g2)
        return x, y

    def decode_gps(self, x, y):
        g1 = x - (self.map.shape[0] // 2)
        g2 = y - (self.map.shape[1] // 2)

        g1 = g1 * self.map_scale_factor
        g2 = g2 * self.map_scale_factor

        g1 = g1 + self.origin_offset[0]
        g2 = g2 + self.origin_offset[1]

        return g1, g2

    # Setting previous position
    def update_previous_position(self):
        self.previous_position_set.add(self.current_position)

        if len(self.previous_position_set) < 2:
            return

        self.previous_position = self.previous_position_set.pop()

    # Update map as per the gps values
    def update(self, gps_value, vehicle_state, is_charging):
        # Apply offset
        x, y = self.encode_gps(gps_value)

        # Update the value at the index as road
        self.current_position = (x, y)

        self.update_previous_position()

        if is_charging:
            self.map[x, y] = (0, 0, 0)

            self.map[x + 1, y] = C_GREEN
            self.map[x - 1, y] = C_GREEN
        else:
            self.map[x, y] = (0, 0, 0)

    def get_map(self):
        return self.map

    def show(self):
        cv2.namedWindow('MiniMap', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('MiniMap', 256 * 2, 256 * 2)

        tmp = self.map.copy()

        if len(self.path) > 0:
            path_map = tmp.copy()
            path = self.path.copy()

            # Draw the path on the image
            for i in range(len(path) - 1):
                path_map[path[i][1], path[i][0]] = C_BLUE

            tmp = cv2.addWeighted(tmp, 1, path_map, 0.8, 0)

        if len(self.charging_points) > 0:
            for charging_point in self.charging_points:
                tmp[charging_point[0], charging_point[1]] = C_BLUE

        tmp[self.current_position[0], self.current_position[1]] = C_RED
        cv2.imshow('MiniMap', tmp)

    # Find the path to the charging points
    def path_to_charging_points(self):

        if len(self.charging_points) == 0:
            print('Keep exploring, No charging points found yet !!!')
            return

        paths = []

        for charging_point in self.charging_points:
            _, threshold_image = cv2.threshold(cv2.cvtColor(self.map, cv2.COLOR_BGR2GRAY), 250, 255,
                                               cv2.THRESH_BINARY_INV)

            # Convert the threshold image to a binary grid
            binary_grid = (threshold_image > 0).astype(np.uint8)

            start_position = (self.current_position[1], self.current_position[0])
            end_position = (charging_point[1], charging_point[0])

            grid = Grid(matrix=binary_grid)

            # Get the start and end nodes
            start_node = grid.node(*start_position)
            end_node = grid.node(*end_position)

            # Using Dijkstra Finder and find the path from current position to the charging point
            finder = DijkstraFinder(diagonal_movement=DiagonalMovement.always)
            path, _ = finder.find_path(start_node, end_node, grid)

            # print('Detected Path : ', path)
            paths.append(path)

        if len(paths) > 0:
            self.path = min(paths, key=len)
            print('Length of shortest path: ', len(self.path))
