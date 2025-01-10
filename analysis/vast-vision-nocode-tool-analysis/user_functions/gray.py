from vast_base_objects import BaseInputs, BaseOutputs
import cv2
import numpy as np

class TEST_GrayScaleInputs(BaseInputs, enable=True):
    img: np.ndarray = None
    def run(self):
        return grayscaling(self)

class TEST_GrayScaleOutputs(BaseOutputs, enable=True):
    dst: np.ndarray = None


def grayscaling(param:TEST_GrayScaleInputs):
    dst = cv2.cvtColor(param.img, cv2.COLOR_BGR2GRAY)
    return TEST_GrayScaleOutputs(
        dst=dst
    )