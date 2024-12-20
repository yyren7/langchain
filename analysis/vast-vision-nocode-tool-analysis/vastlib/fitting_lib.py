# ===============================================================================
# Name      : fitting_lib.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-08-18 10:25
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================
import numpy as np
import cv2
from typing import Union, Tuple


def calc_vector_angle(u: np.ndarray, *, deg=False) -> float:
    """ベクトルの角度を求める

    Args:
        u (np.ndarray): ベクトル
        deg (bool, optional): _description_. Defaults to False.

    Returns:
        float: _description_
    """
    if deg:
        return np.rad2deg(np.arctan2(u[1], u[0]))
    return np.arctan2(u[1], u[0])


def classify_angle(angle_deg: float) -> float:
    """鈍角を鋭角に変換"""

    # NOTE: 鋭角判定
    if abs(angle_deg) < 90:
        return abs(angle_deg)
    # NOTE: 正の鈍角判定
    if angle_deg > 0:
        return 180 - angle_deg
    # NOTE: 負の鈍角判定
    if angle_deg < 0:
        return 180 + angle_deg
    return angle_deg


def calc_angle_formed_by_two_vector(u: np.ndarray, v: np.ndarray, *, deg=False) -> float:
    """ベクトルのなす角

    Args:
        u (np.ndarray): ベクトル１
        v (np.ndarray): ベクトル２
        deg (bool, optional): _description_. Defaults to False.

    Returns:
        float: _description_
    """
    numerator = np.inner(u, v)
    denominator = np.linalg.norm(u) * np.linalg.norm(v)  # type: ignore
    ans = numerator / denominator  # NOTE: radian
    if deg:
        theta = np.rad2deg(np.arccos(np.clip(ans, -1.0, 1.0)))
        return classify_angle(theta)

    return np.arccos(np.clip(ans, -1.0, 1.0))


def fit_line(pts: Union[np.ndarray, list]) -> Tuple[np.ndarray, np.ndarray]:
    """線形の最小二乗法(M推定)\n

    Args:
        pts (Union[np.ndarray, list]): _description_

    Returns:
        座標, 単位ベクトル
    """
    # NOTE: vx, vy 正規化された直線方向ベクトル\n
    # NOTE: x0, y0 直線上の点
    pts = np.array(pts)
    vx, vy, x0, y0 = cv2.fitLine(points=pts,
                                 distType=cv2.DIST_L2,
                                 param=0,
                                 reps=0.01,
                                 aeps=0.01)
    # NOTE: 直線上の点
    coord = np.array([x0[0], y0[0]])
    # NOTE: 単位ベクトル
    u = np.array([vx[0], vy[0]])
    return coord, u


def distance_point_to_line(pt: Union[np.ndarray, list],
                           coord: Union[np.ndarray, list],
                           vec: Union[np.ndarray, list]) -> Tuple[float, Tuple[float, float]]:
    """点と直線の距離を求める
    Args:
        x1 (float): 点のx座標
        y1 (float): 点のy座標
        x2 (float): 直線上の点のx座標
        y2 (float): 直線上の点のy座標
        u (float): 直線の単位ベクトルのx成分
        v (float): 直線の単位ベクトルのy成分

    Returns:
        tuple: 距離と交点の座標
    """
    x1, y1 = pt[0], pt[1]
    x2, y2 = coord[0], coord[1]
    u, v = vec[0], vec[1]

    # NOTE: ベクトルQを正規化
    q_normalized = np.array([u, v]) / np.linalg.norm([u, v])

    # NOTE: 点Pから点Cへのベクトルを計算
    vector_to_point = np.array([x1 - x2, y1 - y2])

    # NOTE: 法線ベクトルBを計算
    normal_vector_b = np.array([-q_normalized[1], q_normalized[0]])

    # NOTE: 点Eの座標を計算
    intersection_point = np.array([x1, y1]) - np.dot(vector_to_point, normal_vector_b) * normal_vector_b

    # NOTE: 距離を計算
    distance = np.linalg.norm(pt - intersection_point)

    return distance, tuple(intersection_point)

# def get_closs_point(coord1: Union[np.ndarray, list],
#                     uv1: Union[np.ndarray, list],
#                     coord2: Union[np.ndarray, list],
#                     uv2: Union[np.ndarray, list]) -> Tuple[bool, tuple]:
#     """交点算出

#     Args:
#         coord1 (Union[np.ndarray, list]): Line1上の点
#         uv1 (Union[np.ndarray, list]): Line1の単位ベクトル
#         coord2 (Union[np.ndarray, list]): Line2上の点
#         uv2 (Union[np.ndarray, list]): Line2の単位ベクトル

#     Returns:
#         _type_: _description_
#     """
#     # NOTE: Line1の2点
#     x1, y1 = np.array(coord1)
#     x2, y2 = np.array(coord1) + np.array(100 * uv1)
#     # NOTE: Line2の2点
#     x3, y3 = np.array(coord2)
#     x4, y4 = np.array(coord2) + np.array(100 * uv2)

#     # NOTE: 値が0のとき、ベクトルは平行
#     denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
#     if abs(denom) < 0.001:
#         return False, (-1, -1)

#     nua = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
#     # nub = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)

#     ua = nua / denom
#     # ub = nub / denom

#     x = x1 + ua * (x2 - x1)
#     y = y1 + ua * (y2 - y1)

#     return True, (np.round(x, 2), np.round(y, 2))


def get_closs_point(coord1: Union[np.ndarray, list],
                    u1: Union[np.ndarray, list],
                    coord2: Union[np.ndarray, list],
                    u2: Union[np.ndarray, list]) -> Tuple[bool, tuple]:
    """交点算出

    Args:
        coord1 (Union[np.ndarray, list]): Line1上の点
        uv1 (Union[np.ndarray, list]): Line1の単位ベクトル
        coord2 (Union[np.ndarray, list]): Line2上の点
        uv2 (Union[np.ndarray, list]): Line2の単位ベクトル

    Returns:
        _type_: _description_
    """
    # NOTE: Line1の2点
    x1, y1 = np.array(coord1)
    # NOTE: Line2の2点
    x2, y2 = np.array(coord2)

    # NOTE: 値が0のとき、ベクトルは平行
    denom = u2[1] * u1[0] - u2[0] * u1[1]
    if abs(denom) < 0.001:
        return False, (-1, -1)

    nua = u2[0] * (y1 - y2) - u2[1] * (x1 - x2)

    ua = nua / denom
    # ub = nub / denom

    x = x1 + ua * (u1[0])
    y = y1 + ua * (u1[1])

    return True, (np.round(x, 2), np.round(y, 2))


# ===============================================================================
# NOTE: 外れ値除去関連
# ===============================================================================

def estimate_points(coord: Union[tuple, list, np.ndarray],
                    u: Union[tuple, list, np.ndarray],
                    pts: np.ndarray) -> list:
    """近似線から点を推定"""
    predict_pts = []
    vec = pts.T
    vx, vy = u[0], u[1]
    x0, y0 = coord[0], coord[1]

    if abs(vx) > abs(vy):
        # NOTE: x軸方向で等間隔な点
        for x_ in vec[0]:
            dx = x0 - x_
            ey = y0 - (vy / vx) * dx
            predict_pts.append([x_, ey])
    else:
        # NOTE: y軸方向で等間隔な点
        for y_ in vec[1]:
            dy = y0 - y_
            ex = x0 - (vx / vy) * dy
            predict_pts.append([ex, y_])

    return predict_pts


def get_rmse(coord: np.ndarray,
             uv: np.ndarray,
             pts: Union[list, np.ndarray]) -> Tuple[float, list]:
    """RMSEの計算"""
    errors = []
    cross_pts = []
    pts = np.array(pts)
    angle = calc_vector_angle(uv, deg=True)
    nv = np.array([np.cos(np.radians(angle + 90)), np.sin(np.radians(angle + 90))])

    # # NOTE: 角度が指定されておらず、|a| > 1の場合y誤差を計算
    # if abs(uv[0]) > abs(uv[1]):
    #     nv = np.array([0, 1])
    # # NOTE: 角度が指定されておらず、|a| < 1の場合x誤差を計算
    # else:
    #     nv = np.array([1, 0])

    for pt in pts:
        ret, res = get_closs_point(pt, nv, coord, uv)
        error_vec = pt - res
        cross_pts.append(res)
        errors.append(np.linalg.norm(error_vec)**2)  # type: ignore

    rmse = np.average(errors)
    rmse = np.sqrt(rmse)

    return rmse, cross_pts


def remove_outlier(pts: np.ndarray):
    """外れ値除去"""
    pass


# ===============================================================================
# NOTE: 描画関数
# ===============================================================================

def draw_predict_line(dst: np.ndarray,
                      coord: Union[tuple, list, np.ndarray],
                      u: Union[tuple, list, np.ndarray],
                      *,
                      color=(0, 255, 0),
                      thickness=3
                      ) -> np.ndarray:
    """近似直線の描画"""
    h, w = dst.shape[:2]
    if thickness < 0:
        thickness = int((h + w) / 500)
    p1 = (int(u[0] * (h + w) + coord[0]),
          int(u[1] * (h + w) + coord[1]))
    p2 = (int(u[0] * -(h + w) + coord[0]),
          int(u[1] * -(h + w) + coord[1]))
    dst = cv2.line(dst, p1, p2, color, thickness=thickness)
    return dst


def draw_points(dst: np.ndarray,
                points: list,
                *,
                thickness: int = 1,
                color: tuple = (0, 255, 255),
                radius: int = 1) -> np.ndarray:
    """検出点を描画"""
    for pt in points:
        dst = cv2.circle(dst, center=(round(pt[0]), round(pt[1])),
                         radius=radius,
                         color=color,
                         thickness=thickness,
                         lineType=cv2.LINE_4,
                         shift=0)
    return dst


def draw_rectangles(dst: np.ndarray,
                    rects: list,
                    *,
                    thickness: int = 3,
                    color: tuple = (0, 255, 255)) -> np.ndarray:
    """矩形描画"""
    for rect in rects:
        dst = cv2.rectangle(img=dst, pt1=(rect[1], rect[0]), pt2=(rect[3], rect[2]),
                            color=color, thickness=thickness)
    return dst


def draw_error_norm(dst: np.ndarray, pts: Union[list, np.ndarray], cross_pts: Union[list, np.ndarray],
                    *, color=(0, 0, 255)) -> np.ndarray:
    """誤差ノルムの描画"""
    pts = np.array(pts)
    cross_pts = np.array(cross_pts)
    h, w = dst.shape[:2]
    size = int((h + w) / 500)
    for i in range(pts.shape[0]):
        p1 = (round(pts[i][0]), round(pts[i][1]))
        p2 = (round(cross_pts[i][0]), round(cross_pts[i][1]))
        dst = cv2.line(dst, p1, p2, color, thickness=size)
    return dst


def line_fitting(
        pts: Union[np.ndarray, list],
        direction: str = None,
        least_num: int = None,
        img: np.ndarray = None,
        origin_pts: Union[np.ndarray, list] = None) -> dict:

    # 外れ値除去されたポイントの描画に利用
    if origin_pts is None:
        origin_pts = pts.copy()

    # np.ndarrayに変換
    pts = np.array(pts)

    # 変数の準備
    pts_count = len(pts)
    champion_pts = []
    champion_line = []
    errors = []
    min_rmse = 65535

    if least_num is None:
        least_num = pts_count

    # 外れ値除去計算のループ
    for i in range(pts_count):
        # 外れ値除去しない場合
        if pts_count <= least_num:
            pts_ = pts
        else:
            pts_ = np.delete(pts, i, 0)
        # 極と単位ベクトルを取得
        coord, uv = fit_line(pts_)

        if direction is None:
            # 角度が指定されておらず、|a| > 1の場合y誤差を計算
            if abs(uv[0]) > abs(uv[1]):
                nv = np.array([0, 1])
            # 角度が指定されておらず、|a| < 1の場合x誤差を計算
            else:
                nv = np.array([1, 0])
        else:
            if direction == "up" or direction == "down":
                #print(direction)
                nv = np.array([0, 1])
            else:
                #print(direction)
                nv = np.array([1, 0])

        # 正しい座標との誤差を計算
        for j, pt in enumerate(pts_):
            #uv_var = np.array([-uv[1], uv[0]])
            ret, res = get_closs_point(pt, nv, coord, uv)
            error_vec = pt - np.array([res[0], res[1]])
            errors.append(np.linalg.norm(error_vec))

        rmse = np.average(errors)

        # rmseが最も小さくなるように外れ値を選択
        if rmse < min_rmse:
            min_rmse = rmse
            champion_pts = pts_
            champion_line = {"coord": coord, "uv": uv}
            outlier_index = i

    # 既定の数まで入力座標数が減っていれば結果を返す
    if len(champion_pts) <= least_num:
        # 全ての座標を黄色で描画
        if img is not None:
            for i, cpt in enumerate(origin_pts):
                h, w = img.shape[:2]
                size = int((h + w) / 500)
                cv2.circle(img, (int(cpt[0]), int(cpt[1])), size, (0, 255, 255), thickness=-1)
        # 直線を描画
        if img is not None:
            h, w = img.shape[:2]
            size = int((h + w) / 500)
            p1 = (int(champion_line["uv"][0] * (h + w) + champion_line["coord"][0]),
                  int(champion_line["uv"][1] * (h + w) + champion_line["coord"][1]))
            p2 = (int(champion_line["uv"][0] * -(h + w) + champion_line["coord"][0]),
                  int(champion_line["uv"][1] * -(h + w) + champion_line["coord"][1]))
            cv2.line(img, p1, p2, (255, 0, 0), thickness=size)
            # 採用した座標を緑色で描画
            for i, cpt in enumerate(champion_pts):
                cv2.circle(img, (int(cpt[0]), int(cpt[1])), size, (0, 255, 0), thickness=-1)

                #debug
                # rett, ress = get_closs_point(cpt, nv, champion_line["coord"], champion_line["uv"])
                # cv2.line(img, (int(cpt[0]), int(cpt[1])), (int(ress[0]), int(ress[1])), (255, 0, 0), thickness=size)

        return {"coord": champion_line["coord"],
                "uv": champion_line["uv"],
                "rmse": min_rmse,
                "pts": champion_pts,
                "img": img
                }

    # 既定の数まで減っていなければ再起呼び出し
    return (
        line_fitting(
            pts=champion_pts,
            least_num=least_num,
            direction=direction,
            img=img,
            origin_pts=origin_pts
        )
    )

# ===============================================================================
# NOTE: メイン関数
# ===============================================================================

def all_function(pts: Union[np.ndarray, list]):
    """オールインワン関数の予定地"""
    pts = np.array(pts)
    coord, uv = fit_line(pts)


if __name__ == '__main__':
    """test"""
    import matplotlib.pyplot as plt

    def imshow(src: np.ndarray):
        if src.ndim == 3:
            plt.imshow(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))  # type: ignore
            plt.show()
        else:
            plt.imshow(cv2.cvtColor(src, cv2.COLOR_GRAY2RGB))  # type: ignore
            plt.show()

    NOISE_MIN = -50
    NOISE_MAX = 50

    # pt1 = np.array([[100, 100], [100, 1000]])
    # pt2 = np.array([[100, 1000], [1000, 1000]])

    pt1 = np.array([[100, 100], [1000, 1000]])
    pt2 = np.array([[100, 1000], [1000, 1000]])

    # NOTE: ノイズを含んだ点群を生成
    coord1, u1 = fit_line(pt1)
    coord2, u2 = fit_line(pt2)
    dummy_array = np.concatenate([[np.arange(1, 1000, 10)], [np.arange(1, 1000, 10)]], 0)
    dummy_array = dummy_array.T
    pts1 = estimate_points(coord1, u1, dummy_array)
    pts2 = estimate_points(coord2, u2, dummy_array)
    noise = np.random.randint(NOISE_MIN, NOISE_MAX, (len(pts1), 2))  # type: ignore
    pts1 = np.array(pts1) - noise
    pts2 = np.array(pts2) - noise

    # NOTE: 線近似
    coord1, u1 = fit_line(pts1)
    coord2, u2 = fit_line(pts2)

    # NOTE: 描画用の画像を用意
    img = np.zeros([1100, 1100, 3], dtype=np.uint8)

    # NOTE: 点群を描画
    for i in range(len(pts1)):
        img = cv2.circle(img, center=(int(pts1[i][0]), int(pts1[i][1])),
                         radius=1,
                         color=(0, 255, 0),
                         thickness=3,
                         lineType=cv2.LINE_4,
                         shift=0)

        img = cv2.circle(img, center=(int(pts2[i][0]), int(pts2[i][1])),
                         radius=1,
                         color=(255, 0, 0),
                         thickness=3,
                         lineType=cv2.LINE_4,
                         shift=0)

    # NOTE: 近似線を描画
    img = draw_predict_line(img, coord1, u1)
    img = draw_predict_line(img, coord2, u2)

    a = calc_angle_formed_by_two_vector(u1, u2, deg=True)
    ret, cross_pt = get_closs_point(coord1, u1, coord2, u2)

    img = cv2.circle(img, center=(int(cross_pt[0]), int(cross_pt[1])),
                     radius=1,
                     color=(0, 0, 255),
                     thickness=3,
                     lineType=cv2.LINE_4,
                     shift=0)
    # rmse1, cross_pt1 = get_rmse(coord1, u1, pts1)
    # rmse2, cross_pt2 = get_rmse(coord2, u2, pts2)

    # img = draw_error_norm(img, pts1, cross_pt1)
    # img = draw_error_norm(img, pts2, cross_pt2)

    print(f'二直線の為す角：{a}deg')
    # print(f'RMSE1: {rmse1}')
    # print(f'RMSE2: {rmse2}')

    imshow(img)
