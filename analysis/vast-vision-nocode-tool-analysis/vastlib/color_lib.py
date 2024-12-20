# ===============================================================================
# Name      : blob_lib.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2024-01-25 17:27
# Copyirght 2022 Hiroya Aoyama
# ===============================================================================
from __future__ import (
    division, absolute_import, print_function, unicode_literals)
import cv2
import numpy as np
from typing import Tuple, Optional, Union
from pydantic import BaseModel


class CustomBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class ColorJudgeResults(CustomBaseModel):
    dst: np.ndarray
    bin: np.ndarray
    offset_region: list = []
    n_pixel: int = 0
    n_pixel_in_region: int = 0
    rect: list = []
    msg: str = ''


def _find_contours(src: np.ndarray) -> tuple:
    """ブロブのデータ取得(内側の輪郭も取ってしまう)"""
    # NOTE: https://imagingsolution.net/program/python/opencv-python/opencv-python-findcontours/
    # NOTE: cv2.__version__ < 4.0
    # cv2.__version__ > 4.0 => contours, hierarchy = cv2.findContours(src, 1, 2)
    contours, _ = cv2.findContours(src, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)
    return contours  # type:ignore

# def _contours2polygons(contours: Union[np.ndarray, list]) -> list:
#     """輪郭リストを多角形リストに変換"""
#     polygons = list(map(np.squeeze, contours))
#     return polygons


def _draw_contours(src: np.ndarray, contours: Union[np.ndarray, list, tuple], *,
                   color: tuple = (0, 0, 255), thickness: int = 3) -> np.ndarray:
    """輪郭リストを多角形リストに変換"""
    dst = cv2.drawContours(src, contours, -1, color=color, thickness=thickness)  # type:ignore
    return dst


def crop_roi(src: np.ndarray, box: list) -> np.ndarray:
    """画像の切り抜き"""
    return src[box[0]:box[2], box[1]:box[3]]


def average_lab_value(target_image: np.ndarray) -> Tuple[np.ndarray, float, float, float]:
    """labの平均値を取得"""
    result = cv2.cvtColor(target_image, cv2.COLOR_BGR2LAB)
    avg_l = np.average(result[:, :, 0])
    avg_a = np.average(result[:, :, 1])
    avg_b = np.average(result[:, :, 2])

    return result, avg_l, avg_a, avg_b


def calc_wb_parameters(target_image: np.ndarray) -> list:
    """パラメータを計算(with Gray Paper)"""
    _, avg_l, avg_a, avg_b = average_lab_value(target_image)
    wb_parameters = [255 / avg_l, 128 / avg_a, 128 / avg_b]
    return wb_parameters


def adjust_wb(target_image: np.ndarray, wb_parameters: list) -> np.ndarray:
    """ゲイン調整"""
    lab_image = cv2.cvtColor(target_image, cv2.COLOR_BGR2LAB)
    proc_img = np.array(wb_parameters) * lab_image[:, :, ]
    proc_img = np.where(proc_img > 255, 255, proc_img)
    proc_img = proc_img.astype(np.uint8)
    proc_img = cv2.cvtColor(proc_img, cv2.COLOR_LAB2BGR)
    return proc_img


def edit_incoming_image(target_image: np.ndarray,
                        data: list,
                        *,
                        l_val: int = 1) -> np.ndarray:
    """パラメータを適用"""
    parameters = [l_val, data[1], data[2]]
    result = adjust_wb(target_image, parameters)
    return result


def create_mask_image(image: np.ndarray, polygons: Union[np.ndarray, list]) -> np.ndarray:
    """マスク生成"""
    h, w = image.shape[:2]
    mask = np.zeros((h, w, 3), dtype=np.uint8)
    for poly in polygons:
        mask = cv2.fillPoly(img=mask, pts=[np.array(poly)], color=(255, 255, 255))
    return cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)  # NOTE: 一次元化


def calc_hist(img: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
    """ROIの画素ヒストグラムを生成
    """
    hist = cv2.calcHist([img], [0], mask, [256], [0, 256])
    return hist


def count_zero_pixel(bin: np.ndarray) -> int:
    """ゼロピクセルをカウント"""
    zero_pixels = cv2.countNonZero(bin)
    zero_pixels = bin.size - zero_pixels
    return zero_pixels


def count_non_zero_pixel(bin: np.ndarray) -> int:
    """ゼロ以外のピクセルをカウント"""
    zero_pixels = cv2.countNonZero(bin)
    return zero_pixels


def get_hist_in_region(image: np.ndarray, polygons: Optional[Union[np.ndarray, list]] = None,
                       ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """領域内のヒストグラムを計算

    Args:
        image (np.ndarray): _description_
        polygons (Union[np.ndarray, list]): _description_

    Returns:
        ch1_hist: blue, hue
        ch2_hist: green, saturation
        ch3_hist: red, value
    """
    ch1, ch2, ch3 = cv2.split(image)
    if polygons is None:
        mask = None
    else:
        mask = create_mask_image(image, polygons=polygons)
    ch1_hist = calc_hist(ch1, mask)
    ch2_hist = calc_hist(ch2, mask)
    ch3_hist = calc_hist(ch3, mask)
    return ch1_hist, ch2_hist, ch3_hist


def get_region(src: np.ndarray,
               lower: Union[tuple, list],
               upper: Union[tuple, list]) -> np.ndarray:
    """領域を取得"""
    if isinstance(lower, list) or isinstance(upper, list):
        lower_ = tuple(lower)
        upper_ = tuple(upper)
    else:
        lower_ = lower
        upper_ = upper
    bin_img = cv2.inRange(src, lower_, upper_)
    return bin_img


def visualize_edge(img: np.ndarray, lower: Union[list, tuple], upper: Union[list, tuple],
                   *, color: tuple = (0, 255, 0), thickness: int = 3
                   ) -> Tuple[np.ndarray, np.ndarray]:
    """色抽出した領域のエッジを可視化"""
    if isinstance(lower, list):
        lower = tuple(lower)
    if isinstance(upper, list):
        upper = tuple(upper)

    bin_img = get_region(img, lower=lower, upper=upper)
    contours = _find_contours(bin_img)
    dst = _draw_contours(img, contours,
                         color=color, thickness=thickness)
    return dst, bin_img


def get_rect_region_include_polygon(region: list) -> list:
    """多角形が入った矩形エリアを返す->min,maxを取得して加工"""
    # NOTE: 転置してx[] y[]に分離
    arr = np.array(region).T
    x_, y_ = arr[0], arr[1]
    xmin, xmax = round(x_.min()), round(x_.max())
    ymin, ymax = round(y_.min()), round(y_.max())
    return [ymin, xmin, ymax, xmax]


def convert_color_space(image: np.ndarray, mode: str) -> np.ndarray:
    if mode == 'rgb':
        return image
    elif mode == 'hsv':
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    elif mode == 'lab':
        return cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    else:
        return image


def offset_polygon(region: list, rect: list) -> list:
    ofs_arr = np.array(region) - np.array([rect[1], rect[0]])
    ofs_arr_i = ofs_arr.astype(np.uint32)
    return ofs_arr_i.tolist()


def judge_region(src: np.ndarray,
                 region: list,
                 mode: str,
                 lower_value: Union[tuple, list],
                 upper_value: Union[tuple, list]) -> ColorJudgeResults:

    img = src.copy()
    # NOTE: 変換
    if isinstance(lower_value, list):
        lower_value = tuple(lower_value)
    if isinstance(upper_value, list):
        upper_value = tuple(upper_value)

    # NOTE: ROIを作成
    rect = get_rect_region_include_polygon(region)
    roi = crop_roi(img, rect)
    roi_converted = convert_color_space(roi, mode)
    # NOTE: ROI内で特定の色エリアを抽出
    roi_1ch = get_region(src=roi_converted, lower=lower_value, upper=upper_value)
    # NOTE: MASKを作成
    mask = create_mask_image(img, [region])
    mask = crop_roi(mask, rect)
    # NOTE: 領域のピクセル数
    n_pixel_in_region = count_non_zero_pixel(mask)
    # NOTE: ROIとMASKでANDをとる
    bin = cv2.bitwise_and(roi_1ch, mask)
    # NOTE: 領域内の指定範囲の色のピクセル数
    n_pixel = count_non_zero_pixel(bin)
    # NOTE: オフセットされたポリゴンを計算
    ofs_region = offset_polygon(region, rect)
    # NOTE: 描画
    dst = roi.copy()
    dst[mask == 255] = cv2.cvtColor(bin, cv2.COLOR_GRAY2BGR)[mask == 255]

    return ColorJudgeResults(
        dst=dst,
        bin=bin,
        n_pixel=n_pixel,
        n_pixel_in_region=n_pixel_in_region,
        offset_region=ofs_region,
        rect=rect
    )


def remap(gray: np.ndarray, lower_v: int, upper_v: int) -> np.ndarray:
    if lower_v == 0 and upper_v == 0:
        # NOTE: 255を返す（FH仕様）
        # return np.clip(gray, 0, 0)  # type: ignore
        return np.zeros_like(gray) + 255
    elif lower_v == 255 and upper_v == 255:
        # NOTE: 0を返す（FH仕様）
        # return np.clip(gray, 255, 255)  # type:ignore
        return np.zeros_like(gray)
    elif lower_v == upper_v:
        return np.clip((gray - lower_v) * 255.0, 0, 255)
    else:
        return np.clip((gray - lower_v) * (255.0 / (upper_v - lower_v)), 0, 255)


def map_range(img: np.ndarray, lower: list, upper: list) -> np.ndarray:
    # NOTE: BGR画像をチャンネルごとに分割
    b, g, r = cv2.split(img.astype(np.float32))
    # NOTE: 各チャンネルをマッピング
    b_mapped = remap(b, lower[0], upper[0])
    g_mapped = remap(g, lower[1], upper[1])
    r_mapped = remap(r, lower[2], upper[2])

    # NOTE: マッピングされた各チャンネルを結合
    img_mapped = cv2.merge([b_mapped, g_mapped, r_mapped])

    return img_mapped.astype(np.uint8)


if __name__ == '__main__':
    pass
