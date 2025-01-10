# ===============================================================================
# Name      : camera.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2022-06-21 11:03
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================

import cv2
import numpy as np
import time
# import sys
import subprocess

try:
    from utils.camera.abc_camera import Camera
except Exception:
    from abc_camera import Camera

from typing import Optional, Any, Tuple, Union


class USBCamera(Camera):

    __version__ = '0.0.1'

    def __init__(self, device_port: int = 0):
        super().__init__()
        self.cap = cv2.VideoCapture(device_port)

    def __del__(self):
        pass

    def set_resolution(self):
        width, height = self.resolution
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, width)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, height)

    def set_exposure_time(self):
        return super().set_exposure_time()

    def set_white_balance(self):
        return super().set_white_balance()

    def set_camera_gain(self):
        return super().set_camera_gain()

    def capture(self) -> Optional[np.ndarray]:
        try:
            ret, frame = self.cap.read()
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                print("[ERROR] Could not grab image...")
                return None
        except Exception as e:
            print(str(e))
            return None


class CameraV4L(Camera):
    __version__ = '0.0.1'

    def __init__(self, device: Union[int, str]):
        super().__init__()

        if isinstance(device, int):
            self.device = f'/dev/video{id}'
        elif isinstance(device, str):
            self.device = device

        self.cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)

        if self.cap.isOpened() is False:
            raise IOError

    def __del__(self):
        print("call destructor")
        self.cap.release()

    def set_resolution(self):
        width, height = self.resolution
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        # self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('Y', 'U', 'Y', 'V'))
        if self.auto_wb:
            self.cap.set(cv2.CAP_PROP_AUTO_WB, 1)
        else:
            self.cap.set(cv2.CAP_PROP_AUTO_WB, 0)
            self.cap.set(cv2.CAP_PROP_WB_TEMPERATURE, self.color_temperature)

        self.cap.set(cv2.CAP_PROP_FPS, self.framerate)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)

    def set_white_balance(self):
        if self.auto_wb:
            subprocess.run(['v4l2-ctl',
                            '--device',
                            self.device,
                            '-c',
                            'white_balance_temperature_auto=1'])
        else:
            subprocess.run(['v4l2-ctl',
                            '--device',
                            self.device,
                            '-c',
                            'white_balance_temperature_auto=0'])
            time.sleep(0.5)  # warming time

            subprocess.run(['v4l2-ctl',
                            '--device',
                            self.device,
                            '-c',
                            f'white_balance_temperature={self.color_temperature}'])

    def set_exposure_time(self):
        if self.auto_exposure:
            subprocess.run(['v4l2-ctl',
                            '--device',
                            self.device,
                            '-c',
                            'exposure_auto=1'])
        else:
            subprocess.run(['v4l2-ctl',
                            '--device',
                            self.device,
                            '-c',
                            'exposure_auto=0'])
            time.sleep(0.5)  # warming time

            subprocess.run(['v4l2-ctl',
                            '--device',
                            self.device,
                            '-c',
                            f'exposure_absolute={self.exposure_time*10}'])
            time.sleep(0.5)  # warming time

    def set_camera_gain(self):
        if self.auto_exposure:
            subprocess.run(['v4l2-ctl',
                            '--device',
                            self.device,
                            '-c',
                            f'gain={self.analog_gain}'])
            time.sleep(0.5)  # warming time

    def capture(self) -> Optional[np.ndarray]:
        try:
            ret, frame = self.cap.read()
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                print("[ERROR] Could not grab image...")
                return None
        except Exception as e:
            print(str(e))
            return None


if __name__ == "__main__":
    cam = USBCamera()
    print(cam.__version__)
    data = dict(sensor_mode=1, height=720, width=1280)
    cam.set_parameter(data)

    print(cam.get_metadata())

    frame = cam.capture()

    cv2.imshow('www', frame)
    cv2.waitKey(0)
