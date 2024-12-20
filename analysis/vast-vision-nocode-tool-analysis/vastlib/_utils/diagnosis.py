# ===============================================================================
# Name      : self.diagnosis.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2024-01-10 09:02
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================
import numpy as np
import cv2
import statistics
from typing import Tuple, Any
from utils.observer.status_monitor import get_raspberrypi_status

try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


def imshow(src):
    import matplotlib.pyplot as plt
    plt.imshow(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))
    plt.show()


def calc_hist(img):
    hist = cv2.calcHist([img], channels=[0], mask=None, histSize=[256], ranges=[0, 256])
    hist = cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
    hist = hist.squeeze(axis=-1)
    return hist


def calc_rgb_hist(img, color: str = 'red'):
    b, g, r = cv2.split(img)

    if color == 'blue':
        component = b
    elif color == 'green':
        component = g
    else:
        component = r

    hist = calc_hist(component)
    return hist


def calc_hsv_hist(img, element: str = 'hue'):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    if element == 'hue':
        component = h
    elif element == 'saturation':
        component = s
    else:
        component = v

    hist = calc_hist(component)
    return hist


def hotelling_model(value: float,
                    value_list: list,
                    data_size: int,
                    thresh: float = 8.5) -> bool:

    # NOTE: 100% format or 1.0 format
    # if thresh_percent > 1:
    #     thresh_percent = thresh_percent / 100

    # NOTE: 指定のデータサイズより多くなれば削除
    value_list.append(valur)

    if len(value_list) > data_size:
        del value_list[0]
    else:
        logger.debug('There is not enough data.')
        return True

    # NOTE: 平均-分散
    mean_v = statistics.mean(val_list[:-1])
    variance = statistics.variance(val_list[:-1])

    # NOTE: 異常スコア計算
    try:
        anomaly_score = (value - mean_v)**2 / variance
    except ZeroDivisionError:
        anomaly_score = (value - mean_v)**2 / 1
    except Exception as e:
        logger.error(f'{e}')
        anomaly_score = (value - mean_v)**2 / 1

    # threshold = stats.chi2.interval(alpha=per, df=1)[1]
    threshold = 8.5

    # NOTE: 異常判定
    if anomaly_score > thresh:
        logger.info('abnormal detected')
        return False

    return True


class VASTDiagnosis:
    # NOTE: 異常検知システム with ホテリング理論
    def __init__(self):
        # ヒストグラム診断
        self.similarity_th = 0.85
        self.reference_hist = None
        self.score_list = []
        self.data_size = 100

    def histgram_checker(self, frame: np.ndarray) -> Tuple[bool, float]:
        # NOTE: 画像のヒストグラムで異常をチェック
        img = frame.copy()

        # NOTE: 計算量軽減のためリサイズ
        img = cv2.resize(src=img, dsize=(640, 480))

        # NOTE: ヒストグラム計算
        hist = calc_hsv_hist(img, element='value')

        # NOTE: 参照とするヒストグラムがなければreturn
        if self.reference_hist is None:
            self.reference_hist = hist
            return True, 0.0

        # NOTE: ヒストグラム類似度を使って異常度検知
        score = cv2.compareHist(hist, self.reference_hist, cv2.HISTCMP_CORREL)
        normal = hotelling_model(value=score,
                                 value_list=self.score_list,
                                 data_size=self.data_size)

        if not normal:
            return False, score

        return True, score


if __name__ == '__main__':
    # hoge = np.zeros((300, 300, 3), dtype=np.uint8)
    dia = SelfDiagnosis()
    cap = cv2.VideoCapture(0)

    _, frame = cap.read()
    dia.set_reference_hist(frame)

    while True:
        _, frame = cap.read()
        # dia.focus_checker(frame)
        dia.hist_checker(frame)
        cv2.imshow("jg", frame)
        cv2.waitKey(10)
