#!/usr/bin/env python3

import math
import random
import time
from copy import deepcopy

import cv2
import numpy as np
import pyautogui
import pywinctl as pwc
from mss import mss

DEBUG = True

SENSITIVITY = 15
BOBBING_PASSES = 20  # Number of iterations of bobber detection to ensure it found a bobber

RECAST_TIME_LOWER = 30
RECAST_TIME_UPPER = 35
CLICK_TIME_LOWER = 0.5
CLICK_TIME_UPPER = 2
NO_BOBBER_TIME = 5
FISHING_KEY = "8"

# (0–180, 0–255, 0–255)
RED_LOWER_VALUES = [0, 80 - SENSITIVITY, 0]
RED_UPPER_VALUES = [14, 255, 130 + SENSITIVITY]

BLUE_LOWER_VALUES = [95 - SENSITIVITY, 80 - SENSITIVITY, 70]
BLUE_UPPER_VALUES = [110 + SENSITIVITY, 255, 130 + SENSITIVITY]


def window_active(func):
    # Must be used with Bot methods.
    def wrapper(*args, **kwargs):
        if args[0].window.isActive:
            return func(*args, **kwargs)
        print(" * Attempted action outside of the World of Warcraft window!")

    return wrapper


# TODO: Fix it.
def within_window(func):
    def wrapper(*args, **kwargs):
        if inside_window(args[0].window, kwargs["x"], kwargs["y"]):
            return func(*args, **kwargs)
        print(" * Attempted action outside of the World of Warcraft window!")

    return wrapper


class BotState:
    STOPPED = "stopped"
    FISHING = "fishing"
    HOOKING = "hooking"


class Bot:
    kernel = np.ones((5, 5), "uint8")

    def __init__(self):
        self.state = BotState.STOPPED
        self.fish_spotted = False

        self.cast_time = time.time()
        self.click_time = time.time()
        self.recast_time = 0
        self.max_click_time = 0

        self.bobbing_passes = 0
        self.bobber_x = 0
        self.bobber_y = 0

        self.sct = mss()
        self.initial_recording_box = self.start_fisher()
        self.recording_box = deepcopy(self.initial_recording_box)

        self.run_bot(self.recording_box)

    def start_fisher(self):
        print(" *** Starting WoWtofisherw*** ")
        time.sleep(1)
        try:
            self.window = pwc.getWindowsWithTitle("World of Warcraft")[0]
        except IndexError as no_window_error:
            raise Exception(" # No World of Warcraft window is running! # ") from no_window_error
        self.window.activate()
        return {
            "top": int(self.window.top + (self.window.height / 4)),
            "left": int(self.window.left + (self.window.width / 4)),
            "width": int(self.window.width * 0.5),
            "height": int(self.window.height * 0.5),
        }

    def run_bot(self, recording_box):
        self.bobbing_passes = 0
        self.recast_time = random.randint(RECAST_TIME_LOWER, RECAST_TIME_UPPER)  # noqa: S311
        self.max_click_time = random.uniform(CLICK_TIME_LOWER, CLICK_TIME_UPPER)  # noqa: S311

        self.cast_time = time.time()

        while True:
            frame = self.sct.grab(self.recording_box)
            frame_np = np.array(frame)
            hsv_frame = cv2.cvtColor(frame_np, cv2.COLOR_BGR2HSV)

            if self.state != BotState.STOPPED and time.time() - self.cast_time > self.recast_time:
                print(" * Too long, gave up!")
                self.reset()

            if self.state == BotState.FISHING:
                self.find_bobber(frame_np, hsv_frame)

            elif self.state == BotState.HOOKING:
                self.hook_fish(frame_np, hsv_frame)

            elif self.state == BotState.STOPPED:
                self.cast()

            if DEBUG:
                cv2.namedWindow("output", cv2.WINDOW_NORMAL)
                cv2.imshow("output", frame_np)
                if (cv2.waitKey(1) & 0xFF) == ord("q"):
                    cv2.destroyAllWindows()
                    break

    def cast(self):
        time.sleep(2)
        print("\n * Let's fish!")
        self.press(FISHING_KEY, **{"window": self.window})
        self.state = BotState.FISHING
        self.cast_time = time.time()
        self.bobbing_passes = 0

    def find_bobber(self, frame, hsv_frame):
        # if time.time() - cast_time > NO_BOBBER_TIME:
        #     currently_fishing = False

        red_mask = self.generate_range_mask(RED_LOWER_VALUES, RED_UPPER_VALUES, hsv_frame)
        blue_mask = self.generate_range_mask(BLUE_LOWER_VALUES, BLUE_UPPER_VALUES, hsv_frame)

        cv2.bitwise_and(frame, frame, mask=red_mask)
        cv2.bitwise_and(frame, frame, mask=blue_mask)

        contours_red, _ = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours_blue, _ = cv2.findContours(blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        red_contour_coords = draw_mask_contours(frame, contours_red, (0, 0, 255))
        blue_contour_coords = draw_mask_contours(frame, contours_blue, (255, 0, 0))

        bobber_coords = find_bobber_area(red_contour_coords, blue_contour_coords)
        if bobber_coords:
            self.bobbing_passes += 1
            bobber_x, bobber_y, length = bobber_coords[0], bobber_coords[1], bobber_coords[2]
            cv2.rectangle(
                frame,
                (bobber_x - 2 * length, bobber_y - 2 * length),
                (bobber_x + 2 * length, bobber_y + 2 * length),
                (0, 0, 0),
                2,
            )
        if self.bobbing_passes > BOBBING_PASSES:
            self.bobber_x = bobber_x
            self.bobber_y = bobber_y
            self.state = BotState.HOOKING
            pyautogui.moveTo(
                bobber_x + self.recording_box["left"],
                bobber_y + self.recording_box["top"],
                0.3,
            )
            self.recording_box["top"] = int(self.initial_recording_box["top"] + (bobber_y - 2.5 * length))
            self.recording_box["left"] = int(self.initial_recording_box["left"] + (bobber_x - 2.5 * length))
            self.recording_box["width"] = int(5 * length)
            self.recording_box["height"] = int(5 * length)
            print(" * Found the bobber!")

    def hook_fish(self, frame, hsv_frame):
        if self.fish_spotted and time.time() - self.click_time > self.max_click_time:
            print(" * Fish!")
            click_params = {"window": self.window, "x": self.bobber_x, "y": self.bobber_y}
            self.shift_click(**click_params)
            self.reset()

        white_mask = self.generate_range_mask([0, 0, 255 - 2 * SENSITIVITY], [255, 2 * SENSITIVITY, 255], hsv_frame)
        cv2.bitwise_and(frame, frame, mask=white_mask)
        contours_white, _ = cv2.findContours(white_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        white_contour_coords = draw_mask_contours(frame, contours_white, (255, 255, 255))
        if white_contour_coords and not self.fish_spotted:
            self.click_time = time.time()
            self.fish_spotted = True

        if time.time() - self.cast_time > self.recast_time:
            self.reset()

    def reset(self):
        self.fish_spotted = False
        self.recording_box = self.initial_recording_box
        self.state = BotState.STOPPED

    def generate_range_mask(self, lower_limits, upper_limits, hsv_frame):
        lower_limit = np.array(lower_limits, np.uint8)
        upper_limit = np.array(upper_limits, np.uint8)
        mask = cv2.inRange(hsv_frame, lower_limit, upper_limit)
        return cv2.dilate(mask, self.kernel)

    @window_active
    def shift_click(self, **kwargs):
        pyautogui.keyDown("shift")
        pyautogui.rightClick()
        pyautogui.keyUp("shift")

    @window_active
    def press(self, key, **kwargs):
        pyautogui.press(key)


def draw_mask_contours(frame: np.ndarray, contours, color: tuple[int, int, int]):
    bounds = []
    for _, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area > 300:
            x, y, w, h = cv2.boundingRect(contour)
            frame = cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            bounds.append((x, y, w, h))
    return bounds


def find_bobber_area(list_a, list_b):
    """
    Go through list of contour coordinates and find intersection to determine bobber position.
    Return intersection coordinates and length of bobber area.
    """
    for point_a in list_a:
        for point_b in list_b:
            distance = math.sqrt(
                (point_b[0] - point_a[0]) * (point_b[0] - point_a[0])
                + (point_b[1] - point_a[1]) * (point_b[1] - point_a[1])
            )
            if distance < 50:
                return (point_a[0] + point_a[2], point_a[1] + point_a[3], point_a[2])
    return None


def inside_window(window, x, y):
    return x > window.left and x < window.left + window.width and y < window.top and y > window.top - window.height


if __name__ == "__main__":
    bot = Bot()
