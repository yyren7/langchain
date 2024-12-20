from vast_base_objects import BaseInputs, BaseOutputs
import numpy as np
import cv2
import math


class Det_LineDistanceInputs(BaseInputs, enable=True):
    img: np.ndarray
    px:  float
    py:  float
    y1:  float

    def run(self):
        super().run()
        return line_distance(self)

class Det_LineDistanceOutputs(BaseOutputs, enable=True):
    dst: np.ndarray
    rsme: int


def line_distance(param: Det_LineDistanceInputs):
    distance = abs(int(param.py) - int(param.y1))

    # 基準点を描画
    out_img = cv2.circle(param.img, (int(param.px), int(param.py)), 5, (0, 0, 255), thickness=-1)
    out_img = cv2.circle(out_img, (int(param.px), int(param.y1)), 5, (0, 0, 255), thickness=-1)

    # 線を描画
    out_img = cv2.line(out_img, (int(param.px - 100), int(param.y1)), (int(param.px + 100), int(param.y1)), (0, 255, 0), thickness=2)
    out_img = cv2.line(out_img, (int(param.px), int(param.py)), (int(param.px), int(param.y1)), (0, 255, 0), thickness=2)

    out_img = cv2.line(out_img, (int(param.px - 100), 845), (int(param.px + 100), 845), (0, 255, 0), thickness=2)

    # 距離を書き込み
    out_img = cv2.putText(out_img, text=str(distance), org=(int(param.px - 200), int((param.py + param.y1) / 2)),
                      fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=4,
                      color=(0, 0, 255), thickness=2, lineType=cv2.LINE_AA)


    return Det_LineDistanceOutputs(dst=out_img,rsme=distance)