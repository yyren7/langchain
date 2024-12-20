# ===============================================================================
# Name      : blob_lib.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-11-20 15:47
# Copyirght 2022 Hiroya Aoyama
# ===============================================================================
import numpy as np
import cv2
import copy
from pydantic import BaseModel
from typing import Tuple, Optional, Union


class CustomBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class BlobResults(CustomBaseModel):
    dst: np.ndarray
    num_blob: int = 0
    points: list = []  # NOTE: 重心リスト
    areas: list = []
    circularitys: list = []
    msg: str = ''
    contours: list = []


class MaxBlobResult(CustomBaseModel):
    dst: np.ndarray
    contour: np.ndarray
    point: tuple = (-1.0, -1.0)
    area: float = -1.0
    circularity: float = -1.0
    msg: str = ''


def _fast_find_contours(src: np.ndarray) -> tuple:
    """ブロブのデータ取得(内側の輪郭も取ってしまう)"""
    # NOTE: https://imagingsolution.net/program/python/opencv-python/opencv-python-findcontours/
    # NOTE: cv2.__version__ < 4.0
    # cv2.__version__ > 4.0 => contours, hierarchy = cv2.findContours(src, 1, 2)
    contours, _ = cv2.findContours(src, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)
    return contours  # type: ignore


def _find_contours(src: np.ndarray) -> tuple:
    """外側の輪郭のみ抽出、内径は検出されない"""
    # src = np.zeros_like(src)
    contours, hierarchy = cv2.findContours(src, mode=cv2.RETR_CCOMP, method=cv2.CHAIN_APPROX_SIMPLE)
    # NOTE: hierarchy[0][輪郭番号][次の輪郭番号, 前の輪郭番号, 最初子供(内側)の輪郭番号, 親(外側)の輪郭番号]
    outer_contours = []
    # NOTE: 輪郭情報が一つもない場合
    if not contours:
        return ()

    contour_index = 0
    while True:
        outer_contours.append(copy.deepcopy(contours[contour_index]))
        contour_index = hierarchy[0][contour_index][0]
        if contour_index == -1:
            break

    return tuple(outer_contours)


def _get_moment(contour: np.ndarray) -> Tuple[float, float]:
    """ブロブの重心計算"""
    m = cv2.moments(contour)
    try:
        x, y = (m['m10'] / m['m00'], m['m01'] / m['m00'])
    except ZeroDivisionError:
        return -1.0, -1.0
    return x, y


def _get_blob_info(contour: np.ndarray) -> Tuple[bool, float, float, float, float]:
    """ブロブの重心と面積計算"""
    x, y = _get_moment(contour)
    if x < 0 and y < 0:
        return False, -1.0, -1.0, -1, -1
    area = cv2.contourArea(contour)
    length = cv2.arcLength(contour, True)
    return True, x, y, area, length


def calculate_gp(points: list) -> Tuple[float, float]:
    """全ブロブの重心"""
    [x_mean, y_mean] = np.mean(np.array(points), axis=0)  # type: ignore
    return round(x_mean, 2), round(y_mean, 2)


# def calc_gp(points: list, scores: list) -> Tuple[float, float]:
#     """ブロブの大きさで重み付を行った重心,加重平均"""
#     pts_np = np.array(points).T
#     x_mean = np.average(pts_np[0], weigths=scores)
#     y_mean = np.average(pts_np[1], weights=scores)
#     return round(x_mean, 2), round(y_mean, 2)


def calc_circularity(area: float, length: float) -> float:
    """真円度を計算"""
    score = 4 * np.pi * area / length / length
    return round(score, 2)


def contour2polygon(contour: np.ndarray) -> np.ndarray:
    """輪郭を多角形に変換"""
    polygon = np.squeeze(contour)
    return polygon


def contours2polygons(contours: Union[np.ndarray, list]) -> list:
    """輪郭リストを多角形リストに変換"""
    polygons = list(map(np.squeeze, contours))
    return polygons


def draw_contour(src: np.ndarray, contour: np.ndarray,
                 *, color: tuple = (0, 128, 0), thickness: int = 3) -> np.ndarray:
    """輪郭を描画"""
    dst = src.copy()
    dst = cv2.drawContours(dst, [contour], -1, color=color, thickness=thickness)
    return dst


def blob_filter(binary_image: np.ndarray,
                *,
                min_size: int = -1, max_size: int = -1,
                inv: bool = False) -> np.ndarray:

    img = binary_image.copy()
    if inv:
        img = cv2.bitwise_not(img)

    # NOTE:
    h, w = img.shape[:2]
    dst = np.zeros((h, w, 3), dtype=np.uint8)

    contours = _fast_find_contours(img)
    contours_ls = []

    for contour in contours:
        ret, _, _, area, _ = _get_blob_info(contour)
        # NOTE: ブロブが見つからない
        if not (ret):
            continue
        # NOTE: 面積が小さい
        if min_size > 0 and area < min_size:
            continue
        # NOTE: 面積が大きい
        if max_size > 0 and area > max_size:
            continue

        # # NOTE: 真円度が足りない
        # circularity = calc_circularity(area, length)
        # if circularity_th > 0:
        #     if circularity < circularity_th:
        #         continue

        contours_ls.append(copy.deepcopy(contour))

    dst = cv2.drawContours(dst, contours_ls, -1, color=(255, 255, 255), thickness=-1)
    dst = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)
    # masked_img = cv2.bitwise_and(binary_image, mask)
    return dst


def get_blob(binary_image: np.ndarray,
             *,
             min_size: int = -1, max_size: int = -1,
             inv: bool = False,
             draw_value: bool = False,
             canvas_image: Optional[np.ndarray] = None,
             thickness: int = 2,
             marker_size: int = 5,
             circularity_th: float = -1.0) -> BlobResults:
    """ブロブ検出

    Args:
        binary_image (np.ndarray): 二値化画像
        min_size (int, optional): ブロブ検出する面積の下限
        max_size (int, optional): ブロブ検出する面積の上限
        inv (bool, optional): ネガ画像で入力
        draw_value (bool, optional): 出力画像に面積を描画する
        canvas_image (np.ndarray, optional): ブロブを描画するキャンバス画像
        thickness (int, optional): ブロブを描画する線の太さ
        marker_size (int, optional): ブロブの中心マーカの大きさ
        circularity_th (float, optional): 真円度の閾値

    Returns:
        BlobResults: 描画画像,ブロブの重心,ブロブの面積
    """
    img = binary_image.copy()
    if inv:
        img = cv2.bitwise_not(img)

    contours = _find_contours(img)

    if canvas_image is not None:
        dst = canvas_image.copy()
    else:
        dst = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    num_blob = 0
    contours_ls = []
    scores = []
    points = []
    circularity_ls = []

    for contour in contours:
        ret, x, y, area, length = _get_blob_info(contour)
        # NOTE: ブロブが見つからない
        if not (ret):
            continue
        # NOTE: 面積が小さい
        if min_size > 0 and area < min_size:
            continue
        # NOTE: 面積が大きい
        if max_size > 0 and area > max_size:
            continue

        # NOTE: 真円度が足りない
        circularity = calc_circularity(area, length)
        if circularity_th > 0:
            if circularity < circularity_th:
                continue

        contours_ls.append(copy.deepcopy(contour))
        points.append([x, y])
        scores.append(np.round(area))
        circularity_ls.append(circularity)
        num_blob += 1

        dst = cv2.drawMarker(dst, (round(x), round(y)), (0, 255, 0), markerSize=marker_size)

    dst = cv2.drawContours(dst, contours_ls, -1, color=(0, 0, 255), thickness=thickness)

    # NOTE:ブロブ面積の描画
    if draw_value:
        for pt, score in zip(points, scores):
            dst = cv2.putText(dst, text=str(int(score)), org=(round(pt[0]), round(pt[1])),
                              fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=1,
                              color=(255, 255, 0), thickness=1, lineType=cv2.LINE_AA)

    return BlobResults(dst=dst,
                       num_blob=round(num_blob),
                       points=points,
                       areas=scores,
                       contours=contours_ls,
                       circularitys=circularity_ls)


def get_max_blob(binary_image: np.ndarray, *,
                 min_size: int = -1, max_size: int = -1,
                 inv: bool = False,
                 draw_value: bool = False,
                 canvas_image: Optional[np.ndarray] = None,
                 thickness: int = 2,
                 marker_size: int = 5,
                 circularity_th: float = -1.0) -> MaxBlobResult:
    """最大ブロブ検出

    Args:
        binary_image (np.ndarray): 二値化画像
        min (int, optional): ブロブ検出する面積の下限
        max (int, optional): ブロブ検出する面積の上限
        inv (bool, optional): ネガ画像で入力
        draw_value (bool, optional): 出力画像に面積を描画する
        canvas_image (np.ndarray, optional): ブロブを描画するキャンバス画像
        thickness (int, optional): ブロブを描画する線の太さ
        marker_size (int, optional): ブロブの中心マーカの大きさ
        circularity_th (float, optional): 真円度の閾値

    Returns:
        BlobResult 描画画像,ブロブの重心,ブロブの面積
    """
    img = binary_image.copy()
    if inv:
        img = cv2.bitwise_not(img)

    contours = _find_contours(img)

    if canvas_image is not None:
        dst = canvas_image.copy()
        if dst.ndim != 3:
            dst = cv2.cvtColor(dst, cv2.COLOR_GRAY2BGR)
    else:
        dst = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    champ_contour = None
    champ_area = 0
    champ_point = None
    champ_circularity = -1.0

    for contour in contours:
        ret, x, y, area, length = _get_blob_info(contour)
        # NOTE: ブロブが見つからない
        if not (ret):
            continue
        # NOTE: 面積が小さい
        if min_size > 0 and area < min_size:
            continue
        # NOTE: 面積が大きい
        if max_size > 0 and area > max_size:
            continue

        # NOTE: 真円度が足りない
        if circularity_th > 0:
            circularity = calc_circularity(area, length)
            if circularity < circularity_th:
                continue

        # NOTE: 大きさ更新ならず
        if area < champ_area:
            continue

        champ_contour = copy.deepcopy(contour)
        champ_point = (x, y)
        champ_area = round(area)
        champ_circularity = calc_circularity(area, length)
        # dst = cv2.drawMarker(dst, (round(x), round(y)), (0, 255, 0), markerSize=marker_size)
        # dst = cv2.drawContours(dst, [contour], -1, color=(0, 0, 255), thickness=thickness)

    if champ_contour is None or champ_point is None:
        return MaxBlobResult(dst=dst, contour=np.array([0]), area=-1)

    dst = cv2.drawMarker(dst, (round(champ_point[0]), round(champ_point[1])),
                         (0, 255, 0), markerSize=marker_size)
    dst = cv2.drawContours(dst, [champ_contour], -1, color=(0, 0, 255), thickness=thickness)

    # NOTE:ブロブ面積の描画
    if draw_value:
        dst = cv2.putText(dst, text=str(int(champ_area)),
                          org=(round(champ_point[0]), round(champ_point[1])),
                          fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=1,
                          color=(255, 255, 0), thickness=1, lineType=cv2.LINE_AA)

    return MaxBlobResult(dst=dst,
                         point=champ_point,
                         area=champ_area,
                         circularity=champ_circularity,
                         contour=champ_contour)


if __name__ == '__main__':
    pass
