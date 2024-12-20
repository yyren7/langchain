# ===============================================================================
# Name      : template_matching_lib.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2024-01-06 15:41
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================
import numpy as np
import cv2
import matplotlib.pyplot as plt
from typing import Tuple, Optional, List, Union
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor

try:
    from .affine_h import (
        rotate_image,
        rotate_rectangle,
        rotate_polygon,
        rotate_point
    )
except Exception:
    from affine_h import (  # type: ignore
        rotate_image,
        rotate_rectangle,
        rotate_polygon,
        rotate_point
    )

try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


class CustomBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class SearchAngleRange(BaseModel):
    min_angle: float = -5.0
    max_angle: float = 5.0
    step: float = 1.0


class MatchResult(CustomBaseModel):
    pt: list = [-1.0, -1.0]
    angle: float = 0.0
    score: float = -1.0
    polygon: np.ndarray = Field(default_factory=lambda: np.array([[0, 0], [0, 0], [0, 0], [0, 0]]))
    rect: list = [0, 0, 0, 0]
    heatmap: np.ndarray = Field(default_factory=lambda: np.zeros((10, 10), dtype=np.uint8))
    pick_point: list = [0, 0]  # NOTE: マスクの中心、ワークの中心で座標を考慮する
    mask_poly_list: list = []  # NOTE: 多角形のリスト[poly1, poly2]


# ===============================================================================
# NOTE: 便利メソッド
# ===============================================================================

def crop_roi(src: np.ndarray, box: list) -> np.ndarray:
    return src[box[0]:box[2], box[1]:box[3]]


def ave_pt(polygon: np.ndarray) -> list:
    """重心算出"""
    [x_mean, y_mean] = np.mean(polygon, axis=0)  # type: ignore
    return [round(x_mean, 2), round(y_mean, 2)]


def imshow(src: np.ndarray) -> None:
    if src.ndim == 3:
        plt.imshow(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))  # type: ignore
        plt.show()
    else:
        plt.imshow(cv2.cvtColor(src, cv2.COLOR_GRAY2RGB))  # type: ignore
        plt.show()


def show_heatmap(match_result: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(match_result, cmap="jet")
    fig.colorbar(im)  # type: ignore
    plt.show()


def create_graph_image(fig: plt.Figure) -> np.ndarray:
    fig.canvas.draw()  # type: ignore
    graph_image = np.array(fig.canvas.renderer.buffer_rgba())  # type: ignore
    graph_image = cv2.cvtColor(graph_image, cv2.COLOR_RGBA2BGR)
    return graph_image


def get_heatmap(match_result: np.ndarray) -> np.ndarray:
    """ヒートマップ取得

    Args:
        match_result (np.ndarray): _description_

    Returns:
        np.ndarray: _description_
    """
    fig = plt.figure()  # 新しいFigureオブジェクトを作成
    ax = fig.add_subplot(111)
    # fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(match_result, cmap="jet")
    fig.colorbar(im)  # type: ignore
    img = create_graph_image(fig)
    # NOTE: 解放しないとメモリリーク
    plt.close()
    return img


def get_mask_center(mask: np.ndarray) -> Tuple[float, float]:
    mu = cv2.moments(array=cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY), binaryImage=False)
    x, y = int(mu["m10"] / mu["m00"]), int(mu["m01"] / mu["m00"])
    return x, y


def _conv_grayscale(src: np.ndarray, color: str = 'gray') -> np.ndarray:
    """
    グレイスケール化
    """
    if color == 'gray':
        return cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    elif color == 'red':
        _, _, red = cv2.split(src)
        return red
    elif color == 'green':
        _, green, _ = cv2.split(src)
        return green
    elif color == 'blue':
        blue, _, _ = cv2.split(src)
        return blue
    elif color == 'hue':
        hsv = cv2.cvtColor(src, cv2.COLOR_BGR2HSV)
        hue, _, _ = cv2.split(hsv)
        return hue
    elif color == 'saturation':
        hsv = cv2.cvtColor(src, cv2.COLOR_BGR2HSV)
        _, saturation, _ = cv2.split(hsv)
        return saturation
    elif color == 'value':
        hsv = cv2.cvtColor(src, cv2.COLOR_BGR2HSV)
        _, _, value = cv2.split(hsv)
        return value
    else:
        return src


def _preprocess(src: np.ndarray, templ: np.ndarray,
                mask: Optional[np.ndarray] = None,
                scale: float = 1.0) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
    """前処理(次元,スケール合わせ)

    Args:
        src (np.ndarray): _description_
        templ (np.ndarray): _description_
        mask (Optional[np.ndarray], optional): _description_. Defaults to None.
        scale (float, optional): _description_. Defaults to 1.0.

    Returns:
        Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]: _description_
    """
    # NOTE: 前処理
    h, w = src.shape[:2]
    t_h, t_w = templ.shape[:2]

    # NOTE: コピー処理
    img = src.copy()
    t_img = templ.copy()

    # NOTE: リスケ―ル
    if scale < 0.999:
        img = cv2.resize(img, (int(scale * w), int(scale * h)))
        t_img = cv2.resize(t_img, (int(scale * t_w), int(scale * t_h)))

    # NOTE: 次元数チェック
    if img.ndim == 3:
        img = _conv_grayscale(img)
    if t_img.ndim == 3:
        t_img = _conv_grayscale(t_img)

    # NOTE: マスクのチェック
    if mask is not None:
        m_img = mask.copy()
        m_img = cv2.resize(mask, (int(scale * t_w), int(scale * t_h)))
        if m_img.ndim == 3:
            m_img = cv2.cvtColor(m_img, cv2.COLOR_BGR2GRAY)
        return img, t_img, m_img

    else:
        # NOTE: mask = Noneで返す
        return img, t_img, None


def rescale_roi(roi: list, scale: float) -> list:
    """ROIスケール調整"""
    if scale < 0.99 or scale > 1.01:
        return [int(val * scale) for val in roi]
    else:
        return roi


def rescale_search_area(roi: list, scale: float) -> list:
    """ROIスケール調整"""
    if scale < 0.99 or scale > 1.01:
        w = roi[3] - roi[1]
        h = roi[2] - roi[0]
        r_w = (scale * w)
        r_h = (scale * h)
        dw = w - r_w
        dh = h - r_h
        xmin = int(roi[1] + dw / 2.0)
        ymin = int(roi[0] + dh / 2.0)
        return [ymin, xmin, int(ymin + r_h), int(xmin + r_w)]

    else:
        return roi


def get_best_match_pos(match: np.ndarray, t_size: tuple,
                       scale: float = 1.0, score_th: float = 0.1) -> Tuple[list, float]:
    """一致度が最大の座標を取得

    Args:
        match (np.ndarray): _description_
        t_size (tuple): _description_
        scale (float, optional): _description_. Defaults to 1.0.
        score_th (float, optional): _description_. Defaults to 0.1.

    Returns:
        Tuple[list, float]: _description_
    """

    # NOTE: マスク有りだとたまにスコア1以上が出現するため、1以下を取得
    # NOTE: スコア1以上は変な場所を検出している気がする
    loc = np.where((match > score_th) & (match < 1.0))
    scores = match[loc]
    # NOTE: 何も見つからなかったとき
    if scores.size == 0:
        return [0, 0, 0, 0], -1.0

    idx = np.argmax(scores)
    max_score = scores[idx]

    max_pt = [loc[1][idx], loc[0][idx]]
    x_min = max_pt[0]
    y_min = max_pt[1]

    if scale < 0.99:
        x_min = round(x_min / scale)
        y_min = round(y_min / scale)

    roi = [y_min, x_min, y_min + t_size[0], x_min + t_size[1]]

    return roi, max_score


def match4para(theta: float, img: np.ndarray, t_img: np.ndarray, m_img: Optional[np.ndarray],
               t_size: tuple, use_mask: bool, scale: float) -> Tuple[float, list, float]:
    """並列処理用テンプレートマッチング関数

    Args:
        theta (float): _description_
        img (np.ndarray): _description_
        t_img (np.ndarray): _description_
        m_img (Optional[np.ndarray]): _description_
        t_size (tuple): _description_
        search_area (Optional[list]): _description_
        use_mask (bool): _description_
        scale (float): _description_

    Returns:
        Tuple[float, list, float]: _description_
    """
    # NOTE: 回転させてからcropすることで回転軸を同じにする
    # => 処理は遅くなるが座標変換の手間を省く
    input = rotate_image(img, theta)

    # NOTE: マッチング
    if use_mask:
        # match = cv2.matchTemplate(input, t_img, cv2.TM_CCORR_NORMED, mask=m_img)
        # NOTE: こっちの方がよい
        match = cv2.matchTemplate(input, t_img, cv2.TM_CCOEFF_NORMED, mask=m_img)
    else:
        # match = cv2.matchTemplate(input, t_img, cv2.TM_CCORR_NORMED)
        # NOTE: こっちの方がよい
        match = cv2.matchTemplate(input, t_img, cv2.TM_CCOEFF_NORMED)

    roi, max_score = get_best_match_pos(match=match, t_size=t_size, scale=scale)

    return round(max_score, 3), roi, round(theta, 3)


def calc_heatmap(img: np.ndarray, t_img: np.ndarray, m_img: Optional[np.ndarray],
                 theta: float, use_mask: bool) -> np.ndarray:
    """ヒートマップ取得用
    """
    input = rotate_image(img, theta)

    # NOTE: マッチング
    if use_mask:
        match = cv2.matchTemplate(input, t_img, cv2.TM_CCOEFF_NORMED, mask=m_img)
    else:
        match = cv2.matchTemplate(input, t_img, cv2.TM_CCOEFF_NORMED)

    heatmap = get_heatmap(match)

    return heatmap


def proc_for_chamfer_matching(img: np.ndarray,
                              templ: np.ndarray,
                              thresh: int = 100) -> Tuple[np.ndarray, np.ndarray]:
    # NOTE: 二値化前提
    img_ = img.copy()
    # NOTE: 一次元化
    if img_.ndim == 3:
        img_ = _conv_grayscale(img_)
    _, img_ = cv2.threshold(img_, thresh, 255, cv2.THRESH_BINARY)
    img_ = cv2.bitwise_not(img_)
    img_ = cv2.distanceTransform(img_, cv2.DIST_L2, 3)
    templ_ = templ.copy()
    # NOTE: 一次元化
    if templ_.ndim == 3:
        templ_ = _conv_grayscale(templ_)
    _, templ_ = cv2.threshold(templ_, thresh, 255, cv2.THRESH_BINARY)
    templ_ = cv2.bitwise_not(templ_).astype(np.float32)
    return img_, templ_


def rotation_matching(src: np.ndarray,
                      templ: np.ndarray,
                      angle_range_table: List[SearchAngleRange],
                      pick_point: tuple,
                      *,
                      mask: Optional[np.ndarray] = None,
                      mask_poly_list: Optional[list] = None,
                      compression_ratio: float = 100,
                      use_chamfer: bool = False,
                      view_heatmap: bool = False
                      ) -> MatchResult:
    """回転マッチング

    Args:
        src (np.ndarray): _description_
        templ (np.ndarray): _description_
        search_area (list, optional): _description_. Defaults to None.
        mask (np.ndarray, optional): _description_. Defaults to None.
        scale (float, optional): _description_. Defaults to 100.
        min_angle (float, optional): _description_. Defaults to -3.0.
        max_angle (float, optional): _description_. Defaults to 3.0.
        step_angle (float, optional): _description_. Defaults to 0.1.
        view_heatmap (bool, optional): _description_. Defaults to False.

    Returns:
        MatchResult: _description_
    """
    champ_score: float = 0
    champ_angle: float = 0
    champ_roi: list = [0, 0, 0, 0]
    futures: list = []

    height, width = src.shape[:2]
    t_h, t_w = templ.shape[:2]
    t_size = (t_h, t_w)

    # NOTE: マスク有無
    if mask is None:
        use_mask = False
    else:
        use_mask = True

    # NOTE: リスケ―ル
    if compression_ratio > 1.0:
        compression_ratio = compression_ratio / 100.0

    if use_chamfer:
        src_c, templ_c = proc_for_chamfer_matching(src, templ)
        img, t_img, m_img = _preprocess(src_c, templ_c, mask, scale=compression_ratio)
    else:
        # NOTE: リサイズ、次元削減の前処理
        img, t_img, m_img = _preprocess(src, templ, mask, scale=compression_ratio)

    # NOTE: 並列処理用に検出を行う角度のリストを作成
    a_list_table = []

    for a_info in angle_range_table:
        a_list = [round((val * a_info.step), 2) for val in
                  range(int(a_info.min_angle / a_info.step),
                        int(a_info.max_angle / a_info.step) + 1, 1)]
        a_list_table.append(a_list.copy())

    result_list: List[list] = []

    # NOTE: 実行
    for a_list_ in a_list_table:
        # NOTE: 並列処理でタクト短縮
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="thread") as pool:
            for angle in a_list_:
                future = pool.submit(match4para, angle, img, t_img, m_img, t_size, use_mask, compression_ratio)
                futures.append(future)

        # NOTE: 並列処理で取得したデータから最大スコアの情報を抜き出す
        max_score = -10.0
        for future in futures:
            # NOTE: スコア,位置,角度を取得
            score, roi, theta = future.result()
            # NOTE: スコア更新ならず
            if score < max_score:
                continue
            max_score = score
            champ_score = score
            champ_angle = theta
            champ_roi = roi

        result_list.append([champ_score, champ_roi, champ_angle])

    # NOTE: 異なる角度レンジの最高スコア同士を比較
    max_score = -10.0
    for res in result_list:
        score, roi, theta = res
        # NOTE: スコア更新ならず
        if score < max_score:
            continue
        max_score = score
        champ_score = score
        champ_angle = theta
        champ_roi = roi

    # NOTE: 何も見つからなかったとき
    if max_score < 0.0:
        logger.debug('Not found Matching Area')
        return MatchResult()

    # NOTE: ptを抜き出し
    ymin, xmin, _, _ = champ_roi

    # NOTE: 回転した検出枠を計算
    polygon = rotate_rectangle(rectangle=champ_roi,
                               rot_center=[round(width / 2), round(height / 2)],
                               rot_angle=champ_angle)

    # NOTE: 回転したマスク領域を計算
    m_p_list = []
    if mask_poly_list is not None:
        for mask_poly_ in mask_poly_list:
            poly_ = rotate_polygon(np.array(mask_poly_) + np.array([xmin, ymin]),
                                   rot_center=[round(width / 2), round(height / 2)],
                                   rot_angle=champ_angle)
            m_p_list.append(poly_.copy().tolist())

    # NOTE: グローバルで計算
    m_x, m_y = rotate_point(pt=[xmin + pick_point[0], ymin + pick_point[1]],
                            rot_center=[round(width / 2), round(height / 2)],
                            rot_angle=champ_angle)

    # NOTE: ヒートマップの計算
    if view_heatmap:
        heatmap_ = calc_heatmap(img=img, t_img=t_img, m_img=m_img,
                                theta=champ_angle, use_mask=use_mask)
    else:
        heatmap_ = np.array([0])

    return MatchResult(pt=[xmin, ymin], angle=champ_angle,
                       score=champ_score, polygon=polygon,
                       rect=champ_roi, heatmap=heatmap_,
                       pick_point=[m_x, m_y],
                       mask_poly_list=m_p_list)


def draw_rotation_rectangle(src: np.ndarray,
                            rectangle: List[int],
                            *,
                            polygon: Optional[np.ndarray] = None,
                            rot_center: Optional[List[int]] = None,
                            rot_angle: float = 0.0,
                            color: tuple = (0, 255, 0),
                            thickness: Optional[int] = None) -> np.ndarray:
    dst = src.copy()

    height, width = dst.shape[:2]
    # NOTE: 入力の指定がなければ、画像中心で回転
    if rot_center is None:
        rot_center = [int(width / 2), int(height / 2)]
    # NOTE: 入力の指定がなければ、自動で太さを計算
    if thickness is None:
        thickness = int((height + width) / 400)

    # NOTE: 入力がrectの時
    if polygon is None:
        # NOTE: 回転角度が0.1以上であれば回転、そうでなければ0度として描画
        if abs(rot_angle) >= 0.1:
            polygon = rotate_rectangle(rectangle=rectangle,
                                       rot_center=rot_center,
                                       rot_angle=rot_angle)
        else:
            (ymin, xmin, ymax, xmax) = rectangle
            polygon = np.array([[xmin, ymin], [xmin, ymax],
                                [xmax, ymax], [xmax, ymin]])

    polygon_ = np.round(polygon).astype(np.int32)  # type: ignore

    dst = cv2.polylines(
        img=dst,
        pts=[polygon_],
        isClosed=True,
        color=color,
        thickness=thickness
    )

    return dst


def get_rotate_polygon(template_size: tuple,  # NOTE: テンプレート画像のサイズ(w, h)
                       detected_polygon: Union[np.ndarray, list],  # NOTE: 見つかったテンプレートの枠座標
                       mask_polygon: Union[np.ndarray, list],  # NOTE: マスクの座標
                       rot_angle: float) -> list:

    # NOTE: オフセットで対応できないので検出された領域（回転矩形の中心を使って計算）
    # NOTE: rotation_matchingにマスクの点データを渡すのが一番早いかも？
    rot_center = [int(template_size[0] / 2), int(template_size[1] / 2)]
    # NOTE: 多角形の回転(マスクのポリゴンは複数のポリゴンを持つ)
    center_point_of_detected_polygon = ave_pt(np.array(detected_polygon))
    rotated_poly_list = []
    for msk_poly in mask_polygon:
        poly = rotate_polygon(polygon=msk_poly,
                              rot_angle=rot_angle,
                              rot_center=rot_center)

        # NOTE: 中心からのベクトルに変換した後、検出されたポリゴンの中心点を加算
        vec_polygon = poly - np.array(rot_center)
        n_polygon = vec_polygon + np.array(center_point_of_detected_polygon)
        n_polygon = np.round(n_polygon).astype(np.int32)
        rotated_poly_list.append(n_polygon.copy())

    return rotated_poly_list


def draw_rotate_polygon(src: np.ndarray,
                        template_size: tuple,  # NOTE: テンプレート画像のサイズ(w, h)
                        detected_polygon: Union[np.ndarray, list],  # NOTE: 見つかったテンプレートの枠座標
                        mask_polygon: Union[np.ndarray, list],  # NOTE: マスクの座標
                        rot_angle: float,
                        *,
                        color: tuple = (0, 255, 0),
                        thickness: Optional[int] = None) -> np.ndarray:

    dst = src.copy()

    height, width = dst.shape[:2]
    # NOTE: 入力の指定がなければ、自動で太さを計算
    if thickness is None:
        thickness = int((height + width) / 400)

    rot_center = [int(template_size[0] / 2), int(template_size[1] / 2)]

    # NOTE: 多角形の回転(マスクのポリゴンは複数のポリゴンを持つ)
    center_point_of_detected_polygon = ave_pt(np.array(detected_polygon))
    rotated_poly_list = []
    for msk_poly in mask_polygon:
        poly = rotate_polygon(polygon=msk_poly,
                              rot_angle=rot_angle,
                              rot_center=rot_center)

        # NOTE: 中心からのベクトルに変換した後、検出されたポリゴンの中心点を加算
        vec_polygon = poly - np.array(rot_center)
        n_polygon = vec_polygon + np.array(center_point_of_detected_polygon)
        n_polygon = np.round(n_polygon).astype(np.int32)
        rotated_poly_list.append(n_polygon.copy())

    for pll in rotated_poly_list:
        dst = cv2.polylines(
            img=dst,
            pts=[pll],
            isClosed=True,
            color=color,
            thickness=thickness
        )

    return dst


if __name__ == '__main__':
    import os
    import time
    DATA_DIR = '../../data/connector/model/-H008-C-X5'
    ORIG_IMG = os.path.join(DATA_DIR, 'sss.bmp')
    TEMPL_IMG = os.path.join(DATA_DIR, 'templ.jpg')
    MASK_IMG = os.path.join(DATA_DIR, 'mask.png')

    t1 = time.time()
    src = cv2.imread(ORIG_IMG)
    templ = cv2.imread(TEMPL_IMG)
    mask = cv2.imread(MASK_IMG)

    h, w = src.shape[:2]
