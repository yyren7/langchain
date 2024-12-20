# ===============================================================================
# Name      : picam_imx477.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-08-16 10:23
# Copyirght 2022 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================
import cv2
import numpy as np
import time
from pydantic import BaseModel
from typing import Union, Tuple, Optional
from picamera2 import Picamera2  # type: ignore

try:
    from .abc_camera import Camera, CameraParam
except Exception:
    from abc_camera import Camera, CameraParam  # type: ignore

try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


RES_HQ = [(1332, 990), (2028, 1080), (2028, 1520), (4056, 3040), (640, 480)]
RES_16MP = [(1280, 720), (1920, 1080), (2328, 1748),
            (3840, 2160), (4656, 3496)]
RES_64MP = [(1280, 720), (1920, 1080), (2328, 1748),
            (3840, 2160), (4656, 3496)]


class MetaData(BaseModel):
    """Picamera2から取得できるメタデータクラス"""
    SensorTimestamp: int = -1
    ExposureTime: int = -1
    FocusFoM: int = -1
    SensorTemperature: float = -1.0
    ColourCorrectionMatrix: tuple
    FrameDuration: int = -1
    AeLocked: bool
    AnalogueGain: float = -1.0
    ColourGains: Tuple[float, float]
    DigitalGain: float = -1.0
    ColourTemperature: int = -1
    Lux: float = -1.0
    SensorBlackLevels: Tuple[int, int, int, int]
    ScalerCrop: Tuple[int, int, int, int]


class HQCamera(Camera):
    """HQCameraの制御クラス

    Args:
        Camera (_type_): _description_
    """

    def __init__(self):
        super().__init__()
        self.cam = Picamera2()

    def __del__(self):
        logger.info("call destructor")
        # NOTE: 念のため例外処理
        try:
            self.cleanup()
        except Exception as e:
            print(e)

    @property
    def focus_value(self) -> float:
        return -1.0

    @focus_value.setter
    def focus_value(self, value: float) -> None:
        pass

    def _get_nearest_value(self, candidate_: list, val: float) -> int:
        idx = np.abs(np.asarray(candidate_) - val).argmin()
        return candidate_[idx]

    def _calculate_fps(self, exposure_time: float) -> int:
        candidate_ = [10, 15, 20, 25, 30, 45, 50, 60]
        fps = 1 / (exposure_time * 2.0)
        return self._get_nearest_value(candidate_, fps)

    def cleanup(self) -> None:
        if self.cam:
            self.cam.close()

    def reset_focus_value(self) -> None:
        pass

    def set_resolution(self) -> None:
        # NOTE: CROP解像度
        self.cam.still_configuration.size = self.resolution
        self.cam.still_configuration.enable_lores()
        # NOTE: RAW解像度
        self.cam.still_configuration.enable_raw()
        self.cam.still_configuration.raw.size = self.raw_resolution
        self.cam.still_configuration.buffer_count = 1
        # NOTE: stillモードで開始
        self.cam.start('still')

    def set_controls(self) -> None:
        with self.cam.controls as controls:
            if not self.auto_exposure:
                controls.ExposureTime = int(self.exposure_time * 1000)
                controls.AnalogueGain = self.analog_gain
            if not self.auto_wb:
                controls.ColourGains = self.color_gain

    def set_exposure_time(self) -> None:
        pass

    def set_camera_gain(self) -> None:
        pass

    def set_white_balance(self) -> None:
        pass

    def initialize_camera(self, data: Union[dict, CameraParam]):
        # NOTE: 解像度を変更する際、カメラを再定義する必要有
        self.cleanup()
        self.cam = Picamera2()
        self.set_parameter(data)

    def capture(self, counter: int = 2) -> Optional[np.ndarray]:
        try:
            array = self.cam.capture_array('main')
            img = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
            if self.flip == 1:
                img = cv2.rotate(img, cv2.ROTATE_180)
            return img
        except Exception as e:
            logger.error(str(e))
            self._error_message = str(e)
            if counter < 0:
                return None
            counter -= 1
            return self.capture(counter=counter)

    def get_metadata(self) -> MetaData:
        metadata = self.cam.capture_metadata()
        data = MetaData(**metadata)
        return data


if __name__ == '__main__':

    RSL = [(1332, 990), (2028, 1080), (2028, 1520), (4056, 3040), (640, 480)]
    # RSL = [(1280, 720), (1920, 1080), (2328, 1748), (3840, 2160), (4656, 3496)]
    afcam = HQCamera()
    data = {
        "sensor_mode": 1,
        "width": 640,
        "height": 480,
        "raw_width": 1280,
        "raw_height": 720,
        "framerate": 30.0,
        "auto_exposure": False,
        "exposure_time": 15,
        "analog_gain": 1,
        "digital_gain": 1,
        "auto_wb": True,
        "color_temperature": 5000,
        "color_gain": [1.0, 1.0],
        "focus": 1000,
        "buffer_size": 1,
        "flip": 0
    }
    afcam.set_parameter(data)
    val = afcam.get_metadata()

    while True:
        t1 = time.time()
        array = afcam.capture()
        t2 = time.time()
        print(round(t2 - t1, 4))
        # print(array.shape[:2])
        cv2.imshow('frame', array)
        cv2.waitKey(10)
