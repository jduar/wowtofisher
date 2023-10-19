import cv2
import numpy as np
from mss import mss

# from PIL import Image


sct = mss()


def get_screen_dimensions() -> (int, int):
    dimensions = sct.monitors[1]
    return dimensions["width"], dimensions["height"]


while True:
    width, height = get_screen_dimensions()
    bounding_box = {"top": height // 2, "left": width // 4, "width": width // 2, "height": height // 2}
    sct_img = sct.grab(bounding_box)
    cv2.imshow("screen", np.array(sct_img))

    if (cv2.waitKey(1) & 0xFF) == ord("q"):
        cv2.destroyAllWindows()
        break
