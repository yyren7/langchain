from __future__ import print_function
import cv2
import numpy as np
import time
from picamera import PiCamera, mmal, mmalobj, exc
from picamera.array import PiRGBArray  # PiYUVArray
from picamera.mmalobj import to_rational

from typing import Optional

try:
    from .abc_camera import Camera
except Exception:
    from abc_camera import Camera

try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


MMAL_PARAMETER_ANALOG_GAIN = mmal.MMAL_PARAMETER_GROUP_CAMERA + 0x59
MMAL_PARAMETER_DIGITAL_GAIN = mmal.MMAL_PARAMETER_GROUP_CAMERA + 0x5A


def set_gain(camera, gain, value):
    """Set the analog gain of a PiCamera.

    camera: the picamera.PiCamera() instance you are configuring
    gain: either MMAL_PARAMETER_ANALOG_GAIN or MMAL_PARAMETER_DIGITAL_GAIN
    value: a numeric value that can be converted to a rational number.
    """
    if gain not in [MMAL_PARAMETER_ANALOG_GAIN, MMAL_PARAMETER_DIGITAL_GAIN]:
        raise ValueError("The gain parameter was not valid")
    ret = mmal.mmal_port_parameter_set_rational(camera._camera.control._port,
                                                gain,
                                                to_rational(value))
    if ret == 4:
        raise exc.PiCameraMMALError(ret, "Are you running the latest version of the userland libraries? Gain setting was introduced in late 2017.")
    elif ret != 0:
        raise exc.PiCameraMMALError(ret)


def set_analog_gain(camera, value):
    """Set the gain of a PiCamera object to a given value."""
    set_gain(camera, MMAL_PARAMETER_ANALOG_GAIN, value)


def set_digital_gain(camera, value):
    """Set the digital gain of a PiCamera object to a given value."""
    set_gain(camera, MMAL_PARAMETER_DIGITAL_GAIN, value)


class RaspiCamera(Camera):
    def __init__(self):
        super().__init__()
        self.camera = PiCamera()

    def __del__(self):
        logger.info("call destructor")
        self.cleanup()

    def _get_nearest_value(self, candidate_: list, val: float):
        idx = np.abs(np.asarray(candidate_) - val).argmin()
        return candidate_[idx]

    def calculate_fps(self, exposure_time: float):
        candidate_ = [10, 15, 20, 25, 30, 45, 50, 60]
        fps = 1 / (exposure_time * 2.0)
        return self._get_nearest_value(candidate_, fps)

    def set_resolution(self):
        self.camera.sensor_mode = self.sensor_mode
        time.sleep(0.2)
        self.camera.resolution = self.resolution

    def set_exposure_time(self):
        if self.auto_exposure:
            exposure_mode = "auto"
            self.camera.exposure_mode = exposure_mode
        else:
            exposure_mode = "off"
            self.camera.exposure_mode = exposure_mode
            exposure_time = int(self.exposure_time * 1000)
            # fps value calculated from the shutter speed.
            self.camera.framerate = self.calculate_fps(exposure_time)
            time.sleep(0.2)
            self.camera.shutter_speed = exposure_time
            time.sleep(0.2)  # warming time

    def set_camera_gain(self):
        if not self.auto_exposure:
            set_analog_gain(self.camera, self.analog_gain)
            set_digital_gain(self.camera, self.digital_gain)

    def set_white_balance(self):
        if self.auto_wb:
            awb_mode = 'auto'
            self.camera.awb_mode = awb_mode
        else:
            awb_mode = 'off'
            self.camera.awb_mode = awb_mode
            self.camera.awb_gains = (self.color_gain[0],
                                     self.color_gain[1])

    def capture(self, counter: int = 2) -> Optional[np.ndarray]:
        try:
            with PiRGBArray(self.camera) as np_array:
                self.camera.capture(np_array, 'rgb', use_video_port=True)
                img = cv2.cvtColor(np_array.array, cv2.COLOR_BGR2RGB)
                return img
        except Exception as e:
            logger.error(e)
            if counter < 0:
                return None
            counter -= 1
            return self.capture(counter=counter)

    def reset_gain_level(self):
        set_analog_gain(self.camera, 1.0)
        set_digital_gain(self.camera, 1.0)

    def check_camera_connection(self) -> bool:
        check1 = (self.camera.analog_gain == 0)
        check2 = (self.camera.digital_gain == 0)
        if (check1 or check2):
            return False
        return True

    def cleanup(self):
        if self.camera:
            self.camera.close()

    def disp_param(self):
        logger.info("< Picamera Parameter >")
        logger.info(f"Resolution : {self.camera.resolution}")
        logger.info(f"FrameRate  : {self.camera.framerate}")
        logger.info(f"SensorMode : {self.camera.sensor_mode}")
        logger.info(f"ExposeMode : {self.camera.exposure_mode}")
        logger.info(f"Exposure   : {self.camera.shutter_speed}[us]")
        logger.info(f"AWB Mode   : {self.camera.awb_mode}")
        logger.info(f"AWB Gains  : {self.camera.awb_gains}")
        logger.info(f"AnalogGain : {self.camera.analog_gain}")
        logger.info(f"DigitalGain: {self.camera.digital_gain}")


def _main():
    rasp_cam = RaspiCamera()
    data = dict(sensor_mode=1,
                width=2592,
                height=1944,
                framerate=30.0,
                auto_exposure=False,
                exposure_time=15.0,
                analog_gain=1.0,
                digital_gain=1.0,
                auto_wb=False,
                color_temperature=5000,
                color_gain=[1.0, 1.0],
                focus=1000,
                buffer_size=1
                )

    rasp_cam.set_parameter(data)
    while True:
        hoge = rasp_cam.capture()
        cv2.imshow("jg", hoge)
        cv2.waitKey(10)


if __name__ == '__main__':
    _main()
