# ===============================================================================
# Name      : henkan.py
# Version   : 1.0.0
# Brief     : 座標の回転に関わる計算
# Time-stamp: 2023-09-22 14:16
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================
import numpy as np
import cv2
from typing import List, Union, Optional, Tuple

try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


def affine_rotation(matrix_in: Union[np.ndarray, list, tuple],
                    rot_center: List[int],
                    rot_angle: float,
                    ) -> np.ndarray:
    """回転座標変換

    Args:
        matrix_in (Union[np.ndarray, list, tuple]): _description_
        rot_center (List[int]): [x_c, y_c]
        rot_angle (float): degree

    Returns:
        np.ndarray: _description_
    """

    # NOTE: 回転中心(x,y)
    [xc, yc] = rot_center
    # NOTE: 回転角度(r)
    dr = rot_angle * np.pi / 180

    # NOTE: list or tupleの場合np.arrayにキャスト
    if isinstance(matrix_in, list) or isinstance(matrix_in, tuple):
        matrix_in = np.array(matrix_in)

    row, col = matrix_in.shape[:2]

    # NOTE: 入力が n x 2
    # [[x1,y1], [x2,y2], ... , [xn, yn]]
    if col == 2 and row != 2:
        mat_in = np.vstack((matrix_in.T, np.ones(row)))

    # NOTE: 入力が 2 x n
    # [[x1,x2,...,xn], [y1,y2,...,yn]]
    elif row == 2 and col != 2:
        mat_in = np.vstack((matrix_in, np.ones(col)))

    else:
        # TODO: 例外処理を加えろ
        return np.array([0])

    # NOTE: 指定の軸を中心に座標変換する行列
    # [cos -sin t1]
    # [sin cos t2]
    rotation_matrix = np.array([
        [np.cos(dr), -np.sin(dr), xc - xc * np.cos(dr) + yc * np.sin(dr)],
        [np.sin(dr), np.cos(dr), yc - xc * np.sin(dr) - yc * np.cos(dr)]
    ])

    # NOTE: 2 x n で出力
    # [[x1,x2,...,xn], [y1,y2,...,yn]]
    matrix_out = np.dot(rotation_matrix, mat_in)

    # NOTE: n x 2 で出力
    # [[x1,y1], [x2,y2], ... , [xn, yn]]
    return matrix_out.T


def rotate_point(pt: list,
                 rot_center: list,
                 rot_angle: float) -> Tuple[float, float]:
    matrix_out = affine_rotation(
        matrix_in=np.array([pt]),
        rot_center=rot_center,
        rot_angle=rot_angle,
    )
    m_ = np.round(matrix_out, decimals=2)
    return m_[0][0], m_[0][1]  # type:ignore


def rotate_rectangle(rectangle: list,
                     rot_center: list,
                     rot_angle: float,
                     *,
                     convert_int: bool = False) -> np.ndarray:
    """矩形座標の回転

    Args:
        rectangle (List[int]): [ymin,xmin,ymax,xmax]
        rot_center (List[int]): [x_c, y_c]
        rot_angle (float): degree

    Returns:
        np.ndarray: _description_
    """

    [ymin, xmin, ymax, xmax] = rectangle
    matrix_in = np.array([
        [xmin, ymin],
        [xmin, ymax],
        [xmax, ymax],
        [xmax, ymin]
    ])

    matrix_out = affine_rotation(
        matrix_in=matrix_in,
        rot_center=rot_center,
        rot_angle=rot_angle,
    )

    if convert_int:
        return np.round(matrix_out).astype(np.int32)  # type:ignore
    else:
        return np.round(matrix_out, decimals=2)


def rotate_polygon(polygon: Union[np.ndarray, list],
                   rot_center: List[int],
                   rot_angle: float) -> np.ndarray:
    """ポリゴンの座標回転

    Args:
        polygon (Union[np.ndarray, list]): [[x1,y1], [x2,y2]...]
        rot_center (List[int]): [x_c, y_c]
        rot_angle (float): degree

    Returns:
        np.ndarray: _description_
    """

    matrix_out = affine_rotation(
        matrix_in=polygon,
        rot_center=rot_center,
        rot_angle=rot_angle,
    )

    return np.round(matrix_out, decimals=2)


def rotate_image(src: np.ndarray,
                 angle: float,
                 *,
                 rotation_point: Optional[list] = None
                 ) -> np.ndarray:
    """画像の回転\n
    rotation_pointを入力しない場合,画像の中心で回転

    Args:
        src (np.ndarray): _description_
        angle (float): _description_
        rotation_point (Optional[list], optional): _description_. Defaults to None.

    Returns:
        np.ndarray: _description_
    """
    h, w = src.shape[:2]
    if h == 0 or w == 0:
        logger.error('Image has zero Dimention')

    if rotation_point is None:
        trans = cv2.getRotationMatrix2D(center=(int(w / 2), int(h / 2)),
                                        angle=angle, scale=1)
    else:
        trans = cv2.getRotationMatrix2D(center=(rotation_point[0], rotation_point[1]),
                                        angle=angle, scale=1)

    img = cv2.warpAffine(src, trans, (w, h))

    return img


def _find_homography(src_pts: np.ndarray, dst_pts: np.ndarray):
    """ホモグラフィ行列の計算"""
    matrix, _ = cv2.findHomography(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=5.0)
    return matrix


def calculate_homography(src_pts: np.ndarray, dst_pts: np.ndarray):
    """ホモグラフィ行列の計算"""
    # matches = _bf_match(src_pts, dst_pts)
    # print(matches)
    matrix = _find_homography(src_pts, dst_pts)
    return matrix


if __name__ == '__main__':
    rect = [0, 0, 200, 200]
    poly = [[100, 100]]
    rotc = [0, 0]
    angle = 90
    pts = rotate_rectangle(rect, rotc, angle)
    print(pts)
    pts = rotate_polygon(poly, rotc, angle)
    print(pts)
