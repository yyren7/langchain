# ===============================================================================
# Name      : abc_camera.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-05-20 09:45
# Copyirght 2022 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================
from abc import ABCMeta, abstractmethod
from pydantic import BaseModel
from typing import List, Union, Tuple


class CameraConfiguration(BaseModel):
    sensor_mode: int = 0
    width: int = 640
    height: int = 480
    raw_width: int = 2028
    raw_height: int = 1520
    framerate: float = 30.0
    auto_exposure: bool = False
    exposure_time: float = 15.0
    analog_gain: float = 1.0
    digital_gain: float = 1.0
    auto_wb: bool = True
    color_temperature: int = 5000
    color_gain: List[float] = [1.0, 1.0]
    focus: float = 1000
    buffer_size: int = 1
    flip: int = 0


class BaseCameraCls(metaclass=ABCMeta):
    """基底カメラクラス

    Args:
        metaclass (_type_, optional): _description_. Defaults to ABCMeta.

    Returns:
        _type_: _description_
    """

    __version__ = '1.0.3'

    def __init__(self):
        self._alive: bool = False
        self._error_message: str = 'camera error'
        self.param = CameraConfiguration()

    def isOpened(self) -> bool:
        return self._alive

    def loadCameraConfiguration(self, data: Union[dict, CameraConfiguration]) -> None:
        if isinstance(data, dict):
            self.param = CameraConfiguration(**data)
        else:
            self.param = data

    def getCameraConfiguration(self, *, format: str = 'class'):
        """パラメータクラスから情報を取得(生データではない)"""
        if format == 'class':
            return self.param
        else:
            return self.param.dict()

    @abstractmethod
    def setCameraResolution(self):
        """解像度の設定"""
        pass

    @abstractmethod
    def setWhiteBalance(self):
        """ホワイトバランスの設定"""
        pass

    @abstractmethod
    def setExposureTime(self):
        """露光時間の設定"""
        pass

    @abstractmethod
    def setCameraGain(self):
        """ゲインの設定"""
        pass

    def setCameraControls(self):
        """WB,SS,Gainの設定(一括で行いたい場合の関数)"""
        # NOTE: 一括で設定が必要な場合に下三つの関数を無視して継承。
        # そうでない場合は下三つの関数をそれぞれ継承しこの関数を無視する。
        # set_controls
        # = set_white_balance and set_exposure_time and set_camera_gain
        pass

    def updateCameraConfiguration(self, data: Union[dict, CameraConfiguration]):
        self.loadCameraConfiguration(data)
        self.setCameraResolution()
        self.setCameraControls()
        self.setExposureTime()
        self.setCameraGain()
        self.setWhiteBalance()

    @abstractmethod
    def capture(self):
        """撮影"""
        pass

    def getMetaDataFromCamera(self):
        """カメラから生データを取得"""
        pass

    # NOTE: Define the getter
    @property
    def sensor_mode(self) -> int:
        return self.param.sensor_mode

    @sensor_mode.setter
    def sensor_mode(self, value: int):
        self.param.sensor_mode = value

    @property
    def resolution(self) -> Tuple[int, int]:
        return (self.param.width, self.param.height)

    @resolution.setter
    def resolution(self, value: Tuple[int, int]):
        self.param.width, self.param.height = value

    @property
    def raw_resolution(self) -> Tuple[int, int]:
        return (self.param.raw_width, self.param.raw_height)

    @raw_resolution.setter
    def raw_resolution(self, value: Tuple[int, int]):
        self.param.raw_width, self.param.raw_height = value

    @property
    def framerate(self) -> float:
        return self.param.framerate

    @framerate.setter
    def framerate(self, value: float):
        self.param.framerate = value

    @property
    def auto_exposure(self) -> bool:
        return self.param.auto_exposure

    @auto_exposure.setter
    def auto_exposure(self, value: bool):
        self.param.auto_exposure = value

    @property
    def exposure_time(self) -> float:
        return self.param.exposure_time

    @exposure_time.setter
    def exposure_time(self, value: float):
        self.param.exposure_time = value

    @property
    def analog_gain(self) -> float:
        return self.param.analog_gain

    @analog_gain.setter
    def analog_gain(self, value: float):
        self.param.analog_gain = value

    @property
    def digital_gain(self) -> float:
        return self.param.digital_gain

    @digital_gain.setter
    def digital_gain(self, value: float):
        self.param.digital_gain = value

    @property
    def auto_wb(self) -> bool:
        return self.param.auto_wb

    @auto_wb.setter
    def auto_wb(self, value: bool):
        self.param.auto_wb = value

    @property
    def color_temperature(self) -> int:
        return self.param.color_temperature

    @color_temperature.setter
    def color_temperature(self, value: int):
        self.param.color_temperature = value

    @property
    def color_gain(self) -> List[float]:
        return self.param.color_gain

    @color_gain.setter
    def color_gain(self, value: List[float]):
        self.param.color_gain = value

    @property
    def focus(self) -> float:
        return self.param.focus

    @focus.setter
    def focus(self, value: float):
        self.param.focus = value

    @property
    def buffer_size(self) -> int:
        return self.param.buffer_size

    @buffer_size.setter
    def buffer_size(self, value: int):
        self.param.buffer_size = value

    @property
    def flip(self) -> int:
        return self.param.flip

    @flip.setter
    def flip(self, value: int):
        self.param.flip = value

    @property
    def error_message(self) -> str:
        return self._error_message
