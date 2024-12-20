# ===============================================================================
# Name      : edge_lib.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-12-25 15:04
# Copyirght 2022 Hiroya Aoyama
# ===============================================================================

import numpy as np
import cv2
from scipy.signal import find_peaks
from typing import Tuple, List, Any, Union


def crop_roi(src: np.ndarray, box: list) -> np.ndarray:
    return src[box[0]:box[2], box[1]:box[3]]


def calculate_subpixel(val1: float,
                       val2: float,
                       *,
                       interval: int = 1) -> float:
    """小数点のシフト量を計算"""
    if np.sign(val1) != np.sign(val2):
        subpixel = abs(val1) / (abs(val1) + abs(val2))
        subpixel = subpixel / interval
        return subpixel
    else:
        return -1.0


def fine_search(roi_1d: Union[Any, np.ndarray],
                base_idx: int,
                *,
                search_len: int = 4) -> Tuple[bool, float]:
    """サブピクセルの計算 \n
        2重微分のゼロ交点(極)を見つける
    """
    search_area: np.ndarray = np.array(roi_1d)
    # NOTE: 配列が一次元でない場合
    if search_area.ndim != 1:
        return False, 0.0

    # NOTE: エッジ位置が探索領域の端の場合
    # サブピクセルを計算する領域を確保できないのでそのまま値を返す
    if base_idx - search_len < 0:
        return True, base_idx

    # NOTE: 2重微分のゼロ交点（極）を見つける
    search_area = search_area[base_idx - search_len:base_idx + search_len]
    dy = np.gradient(search_area)
    ddy = np.gradient(dy)

    # NOTE: 端でサブピクセルを誤検出しないように符号を統一
    ddy[0] = ddy[1]
    ddy[-1] = ddy[-2]

    # NOTE: 符号が変わる場所を探索
    signs = np.sign(ddy)
    indices = np.where(signs[:-1] != signs[1:])[0]

    # NOTE: 符号が変わらない場合
    if indices.size == 0:
        return True, base_idx

    if len(indices) == 1:
        # NOTE: 符号が変わる箇所が1個の場合
        peak_idx = indices[0]
    else:
        # NOTE: 符号が変わる箇所が複数個の場合
        # ギャップが最大の箇所を選択する
        max_val = 0
        for ix in indices:
            gap = abs(ddy[ix] - ddy[ix + 1])
            if gap > max_val:
                max_val = gap
                peak_idx = ix

    subpixel = calculate_subpixel(val1=ddy[peak_idx],
                                  val2=ddy[peak_idx + 1])

    # NOTE: シフト量が計算できない場合そのまま返す
    if subpixel == -1:
        return True, base_idx

    edge_position = base_idx + peak_idx - search_len + subpixel

    return True, edge_position


def find_side_peak(input_array: np.ndarray,
                   edge_type: str,
                   peak_position: str,
                   sigma_gain: float) -> Tuple[int, float]:
    """最初・最後のピークを検出"""
    threshold = 0
    mu = np.average(input_array)
    sigma = np.std(input_array)
    sigma_min = 1.0

    # NOTE: 閾値以上のピークの中から最初・最後のピークを探索
    while sigma_gain > sigma_min:
        if edge_type == 'positive':
            threshold = mu + (sigma_gain * sigma)
            # peak_list = np.where(input_array > threshold)
            peak_idx_list, _ = find_peaks(input_array, height=threshold)
        elif edge_type == 'negative':  # peak == 'low':
            # threshold = mu - (sigma_gain * sigma)
            # peak_list = np.where(input_array < threshold)
            threshold = mu - (sigma_gain * sigma)
            peak_idx_list, _ = find_peaks(-input_array, height=-threshold)
        else:
            return -1, 0

        # NOTE: ピークが見つかればループから抜け出す
        if peak_idx_list.size > 0:
            break

        # NOTE: 閾値を下げてもう一度検出
        sigma_gain -= 0.5

    if peak_idx_list.size == 0:
        return -1, 0

    # NOTE: ピークのINDEXを返す
    if peak_position == 'first':
        peak_idx = peak_idx_list[0]
    elif peak_position == 'last':
        peak_idx = peak_idx_list[-1]
    else:
        return -1, 0

    return peak_idx, threshold


def format_roi_data(roi_data: list, w: int, h: int) -> list:
    # NOTE: 検査領域の一部が枠外に設定された際にリサイズを行う
    if roi_data[0] < 0:
        roi_data[0] = 1
    if roi_data[1] < 0:
        roi_data[1] = 1
    if roi_data[2] > h:
        roi_data[2] = int(h - 1)
    if roi_data[3] > w:
        roi_data[3] = int(w - 1)

    return roi_data


def edge_detection(src: np.ndarray,
                   roi_data: List[int],
                   *,
                   direction_axis: str = 'horizontal',
                   edge_type: str = 'positive',
                   inverse: bool = False,
                   peak_position: str = 'maximum',
                   kernel: np.ndarray = np.array([0.25, 0.5, 0.25]),
                   subpixel: bool = False,
                   sigma_gain: float = 3.0,
                   ) -> Tuple[bool, list]:
    """エッジ検出

    Args:
        src (np.ndarray): _description_
        roi_data (List[int]): _description_
        direction (str, optional): 検出方向(水平or垂直).
        edge_type (str, optional): 黒->白(positive), 白->黒(negative).
        inverse (bool, optional): 検出方向を画像軸と逆転させる.
        peak_position (str, optional): 検出するピーク位置(maximum, first, last)
        kernel (np.ndarray, optional): ノイズ対策用カーネル
        subpixel (bool, optional): サブピクセル使うかどうか
        sigma_gain (float, optional): 検出するピーク位置の閾値パラメータ(first, lastの時使用)

    Returns:
        Tuple[bool, float, float]: _description_
    """

    search_area = src.copy()

    # NOTE: 探索エリア
    search_area = crop_roi(search_area, roi_data)
    x = round(((roi_data[1] + roi_data[3]) / 2), 2)
    y = round(((roi_data[0] + roi_data[2]) / 2), 2)
    x_bias = roi_data[1]
    y_bias = roi_data[0]

    # NOTE: サーチ方向
    if direction_axis == 'horizontal':  # >>
        axis = 0
    elif direction_axis == 'vertical':  # vv
        axis = 1

    # NOTE: 領域を一次元に畳み込み
    # NOTE: axis=0, 垂直方向にsum
    # NOTE: axis=1, 水平方向にsum
    conv_data = search_area.sum(axis=axis)

    # NOTE: サーチ方向を逆にする
    if inverse:
        conv_data = conv_data[::-1]

    # NOTE: 勾配を計算
    grad_data = np.gradient(conv_data)
    # NOTE: 次元そのままでカーネルで畳み込み
    grad_data = np.convolve(grad_data, kernel, mode='same')

    # NOTE: 端の誤検出防ぐために0で初期化
    grad_data[0] = 0.0
    grad_data[1] = 0.0
    grad_data[-1] = 0.0
    grad_data[-2] = 0.0

    # NOTE: bothの処理
    if edge_type == 'both':
        # NOTE: 勾配データを絶対値に
        grad_data = np.abs(grad_data)
        # NOTE: 検出ピークをpositiveに変更
        edge_type = 'positive'

    if peak_position == 'maximum':
        if edge_type == 'positive':
            # NOTE: 最大勾配のINDEX取得
            edge_idx = int(np.argmax(grad_data))
        elif edge_type == 'negative':
            # NOTE: 最小勾配のINDEX取得
            edge_idx = int(np.argmin(grad_data))
        else:
            return False, [-1, -1]
    else:
        edge_idx, peak_thresh = find_side_peak(input_array=grad_data,
                                               edge_type=edge_type,
                                               peak_position=peak_position,
                                               sigma_gain=sigma_gain)

        # NOTE: 計算失敗した時の保険
        if edge_idx < 0:
            if edge_type == 'positive':
                edge_idx = int(np.argmax(grad_data))
            elif edge_type == 'negative':
                edge_idx = int(np.argmin(grad_data))
            else:
                return False, [-1, -1]

    if direction_axis == 'horizontal':
        # NOTE: 水平方向のエッジ検出
        if subpixel:
            # NOTE: サブピクセル処理
            _, edge_pos = fine_search(roi_1d=conv_data,
                                      base_idx=int(edge_idx))
            edge_pixel = edge_pos
        else:
            edge_pixel = float(edge_idx)

        # NOTE: 逆転
        if inverse:
            edge_pixel = grad_data.size - edge_pixel

        # NOTE: 全体座標に変換
        x = round(x_bias + edge_pixel, 2)

    else:
        # NOTE: 垂直方向のエッジ検出
        if subpixel:
            # NOTE: サブピクセル処理
            _, edge_pos = fine_search(roi_1d=conv_data,
                                      base_idx=int(edge_idx))
            edge_pixel = edge_pos
        else:
            edge_pixel = float(edge_idx)

        # NOTE: 逆転
        if inverse:
            edge_pixel = grad_data.size - edge_pixel

        # NOTE: 全体座標に変換
        y = round(y_bias + edge_pixel, 2)

    return True, [x, y]


def line_detection(src: np.ndarray,
                   roi_data: List[int],  # [ymin, xmin, ymax, xmax]
                   *,
                   scan_direction: str = 'right',
                   edge_type: str = 'positive',
                   num_pt: int = 10,
                   search_width: int = 3,
                   peak_position: str = 'maximum',
                   kernel: np.ndarray = np.array([0.25, 0.5, 0.25]),
                   subpixel: bool = False,
                   sigma_gain: float = 3.0,
                   plot_gradient: bool = False) -> Tuple[bool, list]:
    """_summary_

    Args:
        src (np.ndarray): _description_
        roi_data (List[int]): 検査領域
        scan_direction (str, optional): スキャン方向(right, left, up, down)
        edge_type (str, optional): 黒->白(positive), 白->黒(negative).
        num (int, optional): 検出する点の個数
        search_width (int, optional): 点1個あたりの検査幅
        peak_position (str, optional): 検出するピーク位置(maximum, first, last)
        kernel (np.ndarray, optional): ノイズ対策
        subpixel (bool, optional): _description_. Defaults to False.
        sigma_gain (float, optional): _description_. Defaults to 3.0.
        plot_gradient (bool, optional): _description_. Defaults to False.

    Returns:
        Tuple[bool, list]: _description_
    """

    height, width = src.shape[:2]

    if search_width < 3:
        #return False, []
        search_width = 3

    # NOTE: ROIの整形 枠外超えないように
    roi_data = format_roi_data(roi_data, width, height)

    # NOTE: 探索領域を切り取り
    roi = crop_roi(src, roi_data)

    # NOTE: 3チャンネルで入力されたときにグレイスケールに変換
    if roi.ndim == 3:
        roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    roi_height, roi_width = roi.shape[:2]

    # NOTE: スキャン方向
    if scan_direction == 'right':
        direction_axis = 'horizontal'
        inverse = False
    elif scan_direction == 'left':
        direction_axis = 'horizontal'
        inverse = True
    elif scan_direction == 'down':
        direction_axis = 'vertical'
        inverse = False
    elif scan_direction == 'up':
        direction_axis = 'vertical'
        inverse = True
    else:
        return False, []

    # NOTE: インターバルを計算 両端無視するためnum+1
    if direction_axis == 'horizontal':  # >
        interval = (roi_data[2] - roi_data[0]) / (num_pt + 1)
    elif direction_axis == 'vertical':  # v
        interval = (roi_data[3] - roi_data[1]) / (num_pt + 1)
    else:
        return False, []

    # NOTE: インターバルが2ピクセル以下の時
    if interval < 2:
        # TODO: エラーにしろ
        num_pt = 1

    # NOTE: エッジ検出幅
    ofs_width = int(search_width / 2)

    edge_points: list = []

    for i in range(num_pt):
        # NOTE: 水平方向のエッジ検出
        if direction_axis == 'horizontal':
            # NOTE: 点一個の時の特別処理
            if num_pt == 1:
                search_roi = [
                    int(roi_height / 2) - ofs_width,
                    0,
                    int(roi_height / 2) + ofs_width,
                    roi_width
                ]
            else:
                # NOTE: 水平方向のエッジ検出
                search_roi = [
                    int((i + 1.0) * interval) - ofs_width,
                    0,
                    int((i + 1.0) * interval) + ofs_width,
                    roi_width
                ]

                # NOTE: ROI外の点で終了 保険
                if search_roi[0] < 0:
                    continue
                elif search_roi[2] > roi_height:
                    continue

        # NOTE: 垂直方向のエッジ検出
        elif direction_axis == 'vertical':
            # NOTE: 点一個の時の特別処理
            if num_pt == 1:
                search_roi = [
                    0,
                    int(roi_width / 2) - ofs_width,
                    roi_height,
                    int(roi_width / 2) + ofs_width,
                ]
            else:
                search_roi = [
                    0,
                    int((i + 1.0) * interval) - ofs_width,
                    roi_height,
                    int((i + 1.0) * interval) + ofs_width,
                ]

                # NOTE: ROI外の点で終了 保険
                if search_roi[1] < 0:
                    continue
                elif search_roi[3] > roi_width:
                    continue

        # NOTE: エッジ検出
        ret, pt = edge_detection(src=roi,
                                 roi_data=search_roi,
                                 direction_axis=direction_axis,
                                 edge_type=edge_type,
                                 peak_position=peak_position,
                                 kernel=kernel,
                                 inverse=inverse,
                                 subpixel=subpixel,
                                 sigma_gain=sigma_gain)

        if direction_axis == 'horizontal':
            # NOTE: 水平方向の座標オフセット
            x = round(roi_data[1] + pt[0], 2)
            y = round(roi_data[0] + pt[1], 2)

            # NOTE: 点一個の時の特別処理
            if num_pt == 1:
                edge_points.append([x, y - ofs_width])
                edge_points.append([x, y])
                edge_points.append([x, y + ofs_width])
                return True, edge_points

        elif direction_axis == 'vertical':
            # NOTE: 垂直方向の座標オフセット
            y = round(roi_data[0] + pt[1], 2)
            x = round(roi_data[1] + pt[0], 2)

            # NOTE: 点一個の時の特別処理
            if num_pt == 1:
                edge_points.append([x - ofs_width, y])
                edge_points.append([x, y])
                edge_points.append([x + ofs_width, y])
                return True, edge_points

        else:
            return False, []

        edge_points.append([x, y])

    # edge_points = np.array([x_points, y_points]).T
    return True, edge_points


def draw_scan_direction(dst: np.ndarray, rect: list, scan_direction: str, *,
                        thickness: int = 5, color: tuple = (20, 20, 200)) -> np.ndarray:
    ymin, xmin, ymax, xmax = rect
    if scan_direction == 'right':
        pt1 = (xmin, ymin)
        pt2 = (xmax, ymin)
    elif scan_direction == 'left':
        pt1 = (xmax, ymin)
        pt2 = (xmin, ymin)
    elif scan_direction == 'down':
        pt1 = (xmin, ymin)
        pt2 = (xmin, ymax)
    elif scan_direction == 'up':
        pt1 = (xmin, ymax)
        pt2 = (xmin, ymin)
    else:
        return dst
    return cv2.arrowedLine(dst,
                           pt1=pt1,
                           pt2=pt2,
                           color=color,
                           thickness=thickness,
                           line_type=cv2.LINE_4,
                           shift=0,
                           tipLength=0.6)


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    def imshow(src: np.ndarray):
        if src.ndim == 3:
            plt.imshow(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))  # type: ignore
            plt.show()
        else:
            plt.imshow(cv2.cvtColor(src, cv2.COLOR_GRAY2RGB))  # type: ignore
            plt.show()

    def draw_rect(img: np.ndarray, box: list):
        dst = cv2.rectangle(img, (box[1], box[0]), (box[3], box[2]), (0, 255, 0), 3)
        return dst

    sample_image = np.zeros((1000, 1000, 3), dtype=np.uint8)
    sample_image = cv2.rectangle(sample_image, (300, 300), (700, 700), (255, 255, 255), -1)
    imshow(sample_image)

    roi_data = [400, 200, 600, 500]

    dst = sample_image.copy()
    dst = draw_rect(dst, roi_data)
    imshow(dst)

    ret, points = line_detection(sample_image, roi_data=roi_data)
    for pt in points:
        cv2.circle(dst, (round(pt[0]), round(pt[1])), radius=3, color=(0, 0, 255), thickness=3)

    imshow(dst)
