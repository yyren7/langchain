# ===============================================================================
# Name      : circle_lib.py
# Version   : 1.0.0
# Brief     : 円検出
# Time-stamp: 2023-12-25 14:59
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================
import cv2
import numpy as np
from typing import Tuple, Optional, Union

from . import pole_h
from .edge_lib import edge_detection
try:
    from ..rv_lib.calibration_h import circle_estimation, EstimatedCircle
except Exception:
    from rv_lib.calibration_h import circle_estimation, EstimatedCircle  # type: ignore
from pydantic import BaseModel
from .affine_h import rotate_rectangle


class CustomBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class CircleResult(CustomBaseModel):
    success: bool = False
    dst: np.ndarray
    x: float = -1.0
    y: float = -1.0
    r: float = -1.0
    rmse: float = -1.0
    msg: str = ''
    polor_image: Optional[np.ndarray] = None
    edge_points: list = []  # NOTE: 円のエッジ
    edge_points_removed_outlier: list = []  # NOTE: 外れ値除去後のエッジ
    roi_regions: list = []  # NOTE: 検査枠


def get_roi_regions(angle_list: list, center_pt: Union[tuple, list],
                    radius: int, box_width: int, box_height: int) -> list:
    """検査矩形を計算"""
    if isinstance(center_pt, tuple):
        _center_pt = list(center_pt)
    else:
        _center_pt = center_pt

    # NOTE: 検出幅(描画用に大きめにしてます)
    # NOTE: 描画用に大きめにしてます
    box_w_offset = int((box_width - 1) / 2 + 4)
    # NOTE: エッジの探索領域(min-max)
    min_radius = radius - int(box_height / 2)
    max_radius = radius + int(box_height / 2)
    # NOTE: 0度の検査矩形を生成
    xmin = center_pt[0] + min_radius
    xmax = center_pt[0] + max_radius
    ymin = center_pt[1] - box_w_offset
    ymax = center_pt[1] + box_w_offset
    region = [ymin, xmin, ymax, xmax]
    roi_regions = []  # NOTE: 検査領域の座標リスト
    for angle in angle_list:
        poly = rotate_rectangle(rectangle=region,
                                rot_center=_center_pt,
                                rot_angle=angle,
                                convert_int=True)
        roi_regions.append(poly.tolist())

    return roi_regions


def calc_angles(num_pt: int) -> list:
    """点群数から角度のリストを生成"""
    itv = 360.0 / num_pt
    return [round(itr * itv, 1) for itr in range(num_pt)]


def angle2xpt(angle_list: list, circuit_length: int, offset_length: int = 0) -> list:
    """角度のリストから極座標変換時のxのリストを生成"""
    point_list = []
    itv = circuit_length / 360.0
    for angle in angle_list:
        x = round(itv * angle) + offset_length
        point_list.append(int(x))
    return point_list


def remove_outlier(x_data: list,
                   y_data: list,
                   min_num_edge: int) -> Tuple[Optional[EstimatedCircle], list, list]:
    """min_num_edgeの個数まで減らしていく外れ値除去"""
    num_edge = len(x_data)
    min_rmse = 65535.0
    champion_x_data: list = []
    champion_y_data: list = []

    # NOTE: 指定の数までポイントを減らしたら推定結果を返す
    if num_edge <= min_num_edge:
        result = circle_estimation(x_data=x_data, y_data=y_data)
        return result, x_data, y_data

    else:
        for i in range(num_edge):
            # NOTE: 元データをコピー
            x_list = x_data.copy()
            y_list = y_data.copy()

            # NOTE: 順番にiの要素のデータを削除
            del x_list[i]
            del y_list[i]

            # NOTE: 円推定
            result = circle_estimation(x_data=x_list, y_data=y_list)
            # NOTE: 計算に失敗したらNoneを返す
            if result is None:
                return result, [], []

            # NOTE: RMSEが小さいデータセットを残していく
            if result.rmse < min_rmse:
                min_rmse = result.rmse
                champion_x_data = x_list
                champion_y_data = y_list

        # NOTE: RMSEが一番小さいデータセットで次のフェーズに移行（再帰）
        return (
            remove_outlier(
                champion_x_data,
                champion_y_data,
                min_num_edge
            )
        )


def remove_outlier2(pts: list,
                    min_num_edge: int) -> Tuple[Optional[EstimatedCircle], list]:
    """min_num_edgeの個数まで減らしていく外れ値除去"""
    num_edge = len(pts)
    min_rmse = 65535.0
    champion_pts: list = []

    # NOTE: 指定の数までポイントを減らしたら推定結果を返す
    if num_edge <= min_num_edge:
        result = circle_estimation(pts=pts)
        return result, pts

    else:
        for i in range(num_edge):
            # NOTE: 元データをコピー
            _pts = pts.copy()

            # NOTE: 順番にiの要素のデータを削除
            del _pts[i]

            # NOTE: 円推定
            result = circle_estimation(pts=_pts)
            # NOTE: 計算に失敗したらNoneを返す
            if result is None:
                return result, []

            # NOTE: RMSEが小さいデータセットを残していく
            if result.rmse < min_rmse:
                min_rmse = result.rmse
                champion_pts = _pts.copy()

        # NOTE: RMSEが一番小さいデータセットで次のフェーズに移行（再帰）
        return (
            remove_outlier2(
                champion_pts,
                min_num_edge
            )
        )


def remove_outlier_op(x_data: list,
                      y_data: list,
                      min_num_edge: int,
                      radius: float,
                      acceptable_rate: float) -> Tuple[Optional[EstimatedCircle], list, list]:
    """min_num_edgeの個数まで減らしていく外れ値除去"""
    num_edge = len(x_data)
    min_rmse = 65535.0
    champion_x_data: list = []
    champion_y_data: list = []
    if acceptable_rate < 5:
        result = circle_estimation(x_data=x_data, y_data=y_data)
        return result, x_data, y_data
    r_upper = round(radius * (1.0 + acceptable_rate / 100), 1)
    r_lower = round(radius * (1.0 - acceptable_rate / 100), 1)

    # NOTE: 指定の数までポイントを減らしたら推定結果を返す
    if num_edge <= min_num_edge:
        result = circle_estimation(x_data=x_data, y_data=y_data)
        return result, x_data, y_data

    else:
        for i in range(num_edge):
            # NOTE: 元データをコピー
            x_list = x_data.copy()
            y_list = y_data.copy()

            # NOTE: 順番にiの要素のデータを削除
            del x_list[i]
            del y_list[i]

            # NOTE: 円推定
            result = circle_estimation(x_data=x_list, y_data=y_list)
            # NOTE: 計算に失敗したらNoneを返す
            if result is None:
                return result, [], []

            # NOTE: 共用幅
            if result.r > r_upper:
                continue
            elif result.r < r_lower:
                continue

            # NOTE: RMSEが小さいデータセットを残していく
            if result.rmse < min_rmse:
                min_rmse = result.rmse
                champion_x_data = x_list
                champion_y_data = y_list

        # NOTE: RMSEが一番小さいデータセットで次のフェーズに移行（再帰）
        return (
            remove_outlier(
                champion_x_data,
                champion_y_data,
                min_num_edge
            )
        )


def circle_detection(src: np.ndarray,
                     center_pt: tuple,
                     radius: int,
                     *,
                     canvas: Optional[np.ndarray] = None,
                     box_width: int = 5,
                     box_height: int = 15,
                     num_pt: int = -1,
                     angle_list: list = [],
                     edge_type: str = 'positive',
                     peak_position: str = 'maximum',
                     enable_outlier_removal: bool = False,
                     removal_rate: int = 0,
                     sigma_gain: float = 1.5,
                     convert_int: bool = False,
                     draw_edges: bool = False,
                     thickness: int = 3) -> CircleResult:
    """円検出\n
    検出角度の指定方法\n
    点数で指定: num_pt\n
    角度のリストで指定: angle_list

    Args:
        src (np.ndarray): _description_
        center_pt (tuple): 円の中心
        box_width (int, optional): 検出幅 奇数限定
        num_pt (int, optional): _description_. Defaults to -1.
        angle_list (list, optional): _description_. Defaults to [].
    """
    img = src.copy()
    if canvas is None:
        canvas = src.copy()

    # NOTE: 入力チェック
    # NOTE: アングルリストを生成
    if num_pt > 3:
        angle_list = calc_angles(num_pt=num_pt)

    # NOTE: angle_listが空っぽの時
    if len(angle_list) < 4:
        return CircleResult(dst=img, msg='Lack of input data')

    # NOTE: 検出幅
    box_w_offset = (box_width - 1) / 2
    # NOTE: エッジの探索領域(min-max)
    min_r = radius - int(box_height / 2)
    max_r = radius + int(box_height / 2)

    # NOTE: 検出枠の計算
    roi_regions = get_roi_regions(angle_list=angle_list,
                                  center_pt=center_pt,
                                  radius=radius,
                                  box_width=box_width,
                                  box_height=box_height)

    # NOTE: 極座標変換
    polar_img = pole_h.warp_polar(img, center_pt=center_pt, min_r=min_r, max_r=max_r)
    box_height, circuit_length = polar_img.shape[:2]
    polar_img, offset_length = pole_h.expand_polar_image(polar_img, 0.2)

    # NOTE: 極座標時のx座標を計算
    x_pts_polar = angle2xpt(angle_list, circuit_length, offset_length)
    y_pts_polar = []

    if polar_img.ndim == 3:
        gray = cv2.cvtColor(polar_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = polar_img

    for x in x_pts_polar:
        roi_data = [0, x - box_w_offset, box_height, x + box_w_offset]
        roi_data = [int(val) for val in roi_data]
        ret, pt = edge_detection(src=gray, roi_data=roi_data, direction_axis='vertical',
                                 edge_type=edge_type, peak_position=peak_position,
                                 sigma_gain=sigma_gain)
        if not ret:
            return CircleResult(dst=img, msg='Failed to process in edge detection')

        y_pts_polar.append(int(pt[1]))

    # NOTE: 極座標から直交座標に変換
    r_list, theta_list = pole_h.xy2pole(x_pts_polar, y_pts_polar, circuit_length, max_r, offset_length=offset_length)
    x_pts, y_pts = pole_h.pole2xy(r_list, theta_list, center_pt=center_pt)

    # NOTE: 外れ値除去
    if enable_outlier_removal:
        num_pt_ = len(x_pts.tolist())
        min_edge_ = int(num_pt_ * (removal_rate / 100))
        res, x_pts_removed_outlier, y_pts_removed_outlier = remove_outlier(x_data=x_pts.tolist(),
                                                                           y_data=y_pts.tolist(),
                                                                           min_num_edge=min_edge_,
                                                                           )
        if res is None:
            return CircleResult(dst=img, msg='Failed to estimate circle')
    else:
        # NOTE: 除去しない
        res = circle_estimation(x_data=x_pts.tolist(), y_data=y_pts.tolist())
        x_pts_removed_outlier, y_pts_removed_outlier = [], []
        if res is None:
            return CircleResult(dst=img, msg='Failed to estimate circle')

    # NOTE: 描画のために3チャンネルに復元
    if polar_img.ndim != 3:
        polar_img = cv2.cvtColor(polar_img, cv2.COLOR_GRAY2BGR)

    dst = canvas.copy()
    if dst.ndim != 3:
        dst = cv2.cvtColor(dst, cv2.COLOR_GRAY2BGR)

    # NOTE: 極座標画像に描画
    dst_polar = draw_points(polar_img, x_pts_polar, y_pts_polar, thickness=thickness)

    # NOTE: 描画
    dst = draw_point(dst, (int(res.x), int(res.y)), thickness=thickness)  # NOTE: 中心
    dst = draw_point(dst, (int(res.x), int(res.y)), radius=int(res.r),
                     thickness=thickness, color=(0, 255, 0))  # NOTE: 円
    dst = draw_points(dst, x_pts.tolist(), y_pts.tolist(),
                      thickness=thickness)  # NOTE: エッジ
    dst = draw_roi_regions(dst, roi_regions, thickness=thickness)  # NOTE: キャリパ

    # NOTE: 検出点
    pts_e = np.array([x_pts, y_pts])
    pts_e = pts_e.T

    # NOTE: 外れ値除去後の検出点
    pts_removed_outlier = np.array([x_pts_removed_outlier, y_pts_removed_outlier])
    pts_removed_outlier = pts_removed_outlier.T

    return CircleResult(success=True, dst=dst, x=res.x, y=res.y, r=res.r,
                        rmse=res.rmse, polor_image=dst_polar,
                        edge_points=pts_e.tolist(),
                        edge_points_removed_outlier=pts_removed_outlier.tolist(),
                        roi_regions=roi_regions)


##############
# NOTE: 描画
##############
def draw_marker(dst: np.ndarray, pt: tuple):
    """中心を描画"""
    dst = cv2.drawMarker(dst,
                         position=pt,
                         color=(0, 255, 0),
                         markerType=cv2.MARKER_CROSS,
                         markerSize=20,
                         thickness=2,
                         line_type=cv2.LINE_4
                         )
    return dst


def draw_point(dst: np.ndarray, pt: tuple, radius: int = 1,
               thickness: int = 1, color: tuple = (255, 0, 0)) -> np.ndarray:
    """点を描画"""
    dst = cv2.circle(dst,
                     center=pt,
                     radius=radius,
                     color=color,
                     thickness=thickness,
                     lineType=cv2.LINE_4,
                     shift=0)
    return dst


def draw_points(dst: np.ndarray, x_pts: list, y_pts: list,
                thickness: int = 1, color: tuple = (255, 0, 0)) -> np.ndarray:
    """円エッジの描画"""
    for x, y in zip(x_pts, y_pts):
        dst = draw_point(dst, (int(x), int(y)), thickness=thickness, color=color)
    return dst


def draw_roi_regions(dst: np.ndarray, roi_regions: list,
                     thickness: int = 3, color: tuple = (255, 0, 0)) -> np.ndarray:
    """検査枠を描画"""
    for region in roi_regions:
        dst = cv2.polylines(dst, [np.array(region)], isClosed=True, color=color, thickness=thickness)
    return dst


if __name__ == '__main__':
    # import matplotlib.pyplot as plt

    # def imshow(src: np.ndarray):
    #     if src.ndim == 3:
    #         plt.imshow(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))  # type: ignore
    #         plt.show()
    #     else:
    #         plt.imshow(cv2.cvtColor(src, cv2.COLOR_GRAY2RGB))  # type: ignore
    #         plt.show()

    # impath = r'C:\Users\J100048001\Desktop\robot_vision\data\tray\model\Tray_1\templ.jpg'
    impath = r'C:\Users\Owner\Desktop\robot_vision\data\tray\model\Tray_1\orig.bmp'
    img = cv2.imread(impath)
