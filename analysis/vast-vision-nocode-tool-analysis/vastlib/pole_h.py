# ===============================================================================
# Name      : pole_h.py
# Version   : 1.0.0
# Brief     : 極座標変換
# Time-stamp: 2023-12-05 12:37
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================
import cv2
import numpy as np
from typing import Tuple, Union


def crop_roi(src: np.ndarray, box: list) -> np.ndarray:
    return src[box[0]:box[2], box[1]:box[3]]


def pixel2angle(pixel_pos: int, circuit_length: int, *, offset_length: int = 0) -> float:
    itv = 360.0 / circuit_length
    angle = (pixel_pos - offset_length) * itv
    return angle


def xy2pole(x_pts: list, y_pts: list, circuit_length: int, max_r: int, *, offset_length: int = 0) -> Tuple[list, list]:
    """極座標変換後のx,yから直交座標のradius,theta

    Args:
        x_pts (list): _description_
        y_pts (list): _description_
        circuit_length (int): _description_
        max_r (int): _description_
        offset_length (int, optional): _description_. Defaults to 0.

    Returns:
        Tuple[list, list]: _description_
        r_list, theta_list
    """
    theta_list = []
    for x in x_pts:
        theta_list.append(pixel2angle(x, circuit_length, offset_length=offset_length))

    r_np = max_r - np.array(y_pts)
    r_list = r_np.tolist()

    return r_list, theta_list


def pole2xy(radius: Union[list, np.ndarray], theta: Union[list, np.ndarray],
            center_pt: Union[list, tuple]) -> Tuple[np.ndarray, np.ndarray]:
    radius = np.array(radius)
    theta = np.deg2rad(theta)
    x = center_pt[0] + radius * np.cos(theta)
    y = center_pt[1] + radius * np.sin(theta)
    return x, y


def get_nearest_value(candidate_: list, val: int) -> int:
    """候補の中から近い値を返す"""
    idx = np.abs(np.asarray(candidate_) - val).argmin()
    return candidate_[idx]


def calc_length(radius: int, use_raw_value: bool = True) -> int:
    """外周を何ピクセルとして計算するか選択"""
    # NOTE: 角度高精度で計算しやすくするため候補を設定
    candidate_ = [180, 360, 540, 720, 900]
    circuit_length = int(2 * radius * np.pi)
    if use_raw_value:
        return circuit_length
    return get_nearest_value(candidate_, circuit_length)


def warp_polar(src: np.ndarray, center_pt: Union[tuple, list], min_r: int, max_r: int) -> np.ndarray:
    """
    極座標変換

    Args:
        src (np.ndarray): 画像
        center_pt (Union[tuple, list]): 円の中心
        min_r (int): 内円の半径
        max_r (int): 外円の半径

    Returns:
        np.ndarray: _description_
    """
    img = src.copy()
    radius = max_r
    circuit_length = calc_length(max_r)

    if isinstance(center_pt, list):
        center_pt = tuple(center_pt)

    # NOTE: キュービック補間 + 外れ値塗りつぶし + 極座標へリニアマッピング
    flags = cv2.INTER_CUBIC + cv2.WARP_FILL_OUTLIERS + cv2.WARP_POLAR_LINEAR

    # NOTE: 円周をwidthとして極座標変換
    p_img = cv2.warpPolar(src=img,
                          dsize=(radius, circuit_length),
                          center=center_pt,
                          maxRadius=radius,
                          flags=flags)

    p_img = cv2.rotate(p_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    diff_r = max_r - min_r
    p_img = crop_roi(p_img, [0, 0, diff_r, circuit_length])
    return p_img


def inv_warp_polar(src: np.ndarray, center_pt: Union[tuple, list],
                   im_shape: Union[tuple, list], min_r: int, max_r: int,
                   *, offset_length: int = -1) -> np.ndarray:
    """
    逆極座標変換

    Args:
        src (np.ndarray): _description_
        center_pt (Union[tuple, list]): (x, y)
        im_shape (Union[tuple, list]): (width, height)
        radius (int): r

    Returns:
        np.ndarray: _description_
    """
    img = src.copy()

    if isinstance(center_pt, list):
        center_pt = tuple(center_pt)

    if isinstance(im_shape, list):
        im_shape = tuple(im_shape)

    # NOTE: 左右のトリミング処理
    if offset_length > 0:
        h_, w_ = img.shape[:2]
        img = crop_roi(img, [0, offset_length, h_, w_ - offset_length])

    # NOTE: 削った分追加
    _, w = img.shape[:2]
    blank_img = np.zeros((min_r, w, 3), np.uint8)

    p_img = cv2.vconcat([img, blank_img])

    # NOTE: 逆変換
    flags = cv2.INTER_CUBIC + cv2.WARP_FILL_OUTLIERS + cv2.WARP_POLAR_LINEAR + cv2.WARP_INVERSE_MAP
    p_img = cv2.rotate(p_img, cv2.ROTATE_90_CLOCKWISE)
    p_img = cv2.warpPolar(src=p_img,
                          dsize=im_shape,
                          center=center_pt,
                          maxRadius=max_r,
                          flags=flags)
    return p_img


def expand_polar_image(src: np.ndarray, expansion_rate: float) -> Tuple[np.ndarray, int]:
    """
    極座標画像の拡張

    Args:
        src (np.ndarray): 極座標画像
        expansion_rate (float): 拡張率

    Returns:
        Tuple[np.ndarray, int]: _description_
        拡張画像、オフセットの長さ
    """
    h, w = src.shape[:2]
    offset_length = int(w * expansion_rate)

    # NOTE: 前後のイメージを作成
    header_img = crop_roi(src, [0, w - offset_length, h, w])
    footer_img = crop_roi(src, [0, 0, h, offset_length])

    img_join = cv2.hconcat([header_img, src, footer_img])

    return img_join, offset_length


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    def imshow(src: np.ndarray):
        if src.ndim == 3:
            plt.imshow(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))  # type: ignore
            plt.show()
        else:
            plt.imshow(cv2.cvtColor(src, cv2.COLOR_GRAY2RGB))  # type: ignore
            plt.show()

    impath = r'C:\Users\J100048001\Desktop\robot_vision\data\tray\model\Tray_1\templ.jpg'
    img = cv2.imread(impath)
    imshow(img)

    h, w = img.shape[:2]

    center_pt = (85, 78)
    r_min = 20
    r_max = 65

    im = warp_polar(img, center_pt, r_min, r_max)
    imshow(im)
    im, ofs = expand_polar_image(im, 0.2)
    imshow(im)
    im = inv_warp_polar(im, center_pt, (w, h), r_min, r_max, offset_length=ofs)
    imshow(im)
