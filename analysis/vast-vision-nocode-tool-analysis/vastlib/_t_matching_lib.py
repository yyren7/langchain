# ===============================================================================
# Name      : template_matching_lib.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-11-10 09:47
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


class MatchResult(CustomBaseModel):
    pt: list = [-1.0, -1.0]
    angle: float = 0.0
    score: float = -1.0
    polygon: np.ndarray = Field(default_factory=lambda: np.array([[0, 0], [0, 0], [0, 0], [0, 0]]))
    rect: list = [0, 0, 0, 0]
    heatmap: np.ndarray = Field(default_factory=lambda: np.zeros((10, 10), dtype=np.uint8))
    center_pt: list = [0, 0]  # NOTE: マスクの中心、ワークの中心で座標を考慮する


# ===============================================================================
# NOTE: 便利メソッド
# ===============================================================================

def crop_roi(src: np.ndarray, box: list):
    return src[box[0]:box[2], box[1]:box[3]]


def ave_pt(polygon: np.ndarray) -> list:
    """重心算出"""
    [x_mean, y_mean] = np.mean(polygon, axis=0)  # type: ignore
    return [round(x_mean, 2), round(y_mean, 2)]


def imshow(src):
    plt.imshow(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))  # type: ignore
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
    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(match_result, cmap="jet")
    fig.colorbar(im)  # type: ignore
    img = create_graph_image(fig)
    # NOTE: 解放しないとメモリリーク
    plt.close()
    return img


def get_mask_center(mask: np.ndarray):
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
                src_mask: Optional[np.ndarray], templ_mask: Optional[np.ndarray] = None,
                scale: float = 1.0) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]:
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
    if img.ndim != t_img.ndim:
        if img.ndim == 3:
            img = _conv_grayscale(img)
        if t_img.ndim == 3:
            t_img = _conv_grayscale(t_img)

    m_img = None # srcマスク
    tm_img = None # tmplマスク
    # NOTE: マスクのチェック
    if src_mask is not None:
        m_img = src_mask.copy()
        m_img = cv2.resize(m_img, (int(scale * w), int(scale * h)))
        if m_img.ndim == 3:
            m_img = cv2.cvtColor(m_img, cv2.COLOR_BGR2GRAY)

    if templ_mask is not None:
        tm_img = templ_mask.copy()
        tm_img = cv2.resize(tm_img, (int(scale * t_w), int(scale * t_h)))
        if tm_img.ndim == 3:
            tm_img = cv2.cvtColor(tm_img, cv2.COLOR_BGR2GRAY)

    return img, t_img, m_img, tm_img




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


def get_best_match_pos(match: np.ndarray, t_size: tuple, shift: tuple,
                       scale: float = 1.0, score_th: float = 0.1, mask: np.ndarray = None) -> Tuple[list, float]:
    """一致度が最大の座標を取得

    Args:
        match (np.ndarray): _description_
        t_size (tuple): _description_
        shift (tuple): _description_
        scale (float, optional): _description_. Defaults to 1.0.
        score_th (float, optional): _description_. Defaults to 0.1.
        mask (np.ndarray, optional): _description_.
    Returns:
        Tuple[list, float]: _description_
    """

    max_score = None
    if mask is not None:
        try:
            # マスク上のマッチングスコアを0に下げる
            mask = cv2.resize(mask, match.shape[:2][::-1])
            mask_zero = mask == 0
            match[mask_zero] = 0
            # maping = get_heatmap(match)
            # print("shape:", match.shape[:2][::-1])
            # print("zero:", mask_zero)
            # cv2.imshow("test", maping)
            # cv2.imshow("mask", mask)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
        except:
            pass
        # 矩形中心がマスク上にある場合は無視
        # mh, mw = mask.shape[:2]
        # while not np.all(scores == 0):
        #     idx = np.argmax(scores)
        #     #cv2.destroyAllWindows()
        #     if mh < loc[0][idx] + int(t_size[0]/2) or mw < loc[1][idx] + int(t_size[1]):
        #         scores[idx] = 0
        #         continue
        #
        #     test = cv2.circle(cv2.cvtColor(mask.copy(), cv2.COLOR_GRAY2BGR), (loc[1][idx] + int(t_size[1]/2), loc[0][idx] + int(t_size[0])), 5,
        #                       (255, 0, 0), thickness=-1)
        #     # cv2.imshow("test", test)
        #     # cv2.waitKey(1)
        #     try:
        #         if mask[loc[0][idx] + int(t_size[0]/2)][loc[1][idx] + int(t_size[1])] == 255:
        #             max_pt = [loc[1][idx], loc[0][idx]]
        #             max_score = scores[idx]
        #             break
        #         else:
        #             scores[idx] = 0
        #             continue
        #     except Exception as e:
        #         print(e)
    # else:

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

    if max_score is None:
        return [0, 0, 0, 0], -1.0

    x_min = max_pt[0] + shift[0]
    y_min = max_pt[1] + shift[1]

    if scale < 0.99:
        x_min = round(x_min / scale)
        y_min = round(y_min / scale)

    roi = [y_min, x_min, y_min + t_size[0], x_min + t_size[1]]

    return roi, max_score


def match4para(theta: float, img: np.ndarray, t_img: np.ndarray, m_img: Optional[np.ndarray],
               tm_img: Optional[np.ndarray], t_size: tuple, search_area: Optional[list], use_mask: bool,
               scale: float) -> Tuple[float, list, float]:
    """並列処理用テンプレートマッチング関数

    Args:
        theta (float): _description_
        img (np.ndarray): _description_
        t_img (np.ndarray): _description_
        tm_img (np.ndarray): _description_
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
    if search_area is not None:
        input = crop_roi(input, search_area)
        if m_img is not None:
            m_img = crop_roi(m_img, search_area)

    # NOTE: マッチング
    if tm_img is not None:
        # match = cv2.matchTemplate(input, t_img, cv2.TM_CCORR_NORMED, mask=m_img)
        # NOTE: こっちの方がよい
        match = cv2.matchTemplate(input, t_img, cv2.TM_CCOEFF_NORMED, mask=tm_img)
    else:
        # match = cv2.matchTemplate(input, t_img, cv2.TM_CCORR_NORMED)
        # NOTE: こっちの方がよい
        match = cv2.matchTemplate(input, t_img, cv2.TM_CCOEFF_NORMED)

    # NOTE: シフト量設定
    if search_area is None:
        shift = (0, 0)
    else:
        shift = (search_area[1], search_area[0])

    roi, max_score = get_best_match_pos(match=match, t_size=t_size, shift=shift, scale=scale, mask=m_img)

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


def rotation_matching(src: np.ndarray,
                      templ: np.ndarray,
                      *,
                      src_mask: [np.ndarray] = None,
                      search_area: Optional[list] = None,
                      templ_mask: Optional[np.ndarray] = None,
                      compression_ratio: float = 100,
                      min_angle: float = -3.0,
                      max_angle: float = 3.0,
                      step_angle: float = 0.1,
                      #   subpixel: bool = False,
                      view_heatmap: bool = False
                      ) -> MatchResult:
    """回転マッチング
    Args:
        src (np.ndarray): _description_
        templ (np.ndarray): _description_
        src_mask (list, optional): _description_. Defaults to None.
        search_area (list, optional): _description_. Defaults to None.
        templ_mask (np.ndarray, optional): _description_. Defaults to None.
        compression_ratio (float, optional): _description_. Defaults to 100.
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
    if templ_mask is None:
        use_mask = False
        m_x, m_y = 0.0, 0.0
    else:
        use_mask = True
        # NOTE: マスクの中心座標を計算（アライメント時に必要）
        m_x, m_y = get_mask_center(templ_mask)

    # NOTE: リスケ―ル
    if compression_ratio > 1.0:
        compression_ratio = compression_ratio / 100.0

    # NOTE: リサイズ、次元削減の前処理
    img, t_img, m_img, mt_img = _preprocess(src, templ, src_mask, templ_mask,
                                    scale=compression_ratio)

    # NOTE: リサイズに合わせて検査領域もリサイズ
    if search_area is not None:
        search_area = rescale_roi(search_area, compression_ratio)

    # NOTE: 並列処理用に検出を行う角度のリストを作成
    angles = [round((val * step_angle), 2) for val in range(int(min_angle / step_angle), int(max_angle / step_angle) + 1, 1)]

    # NOTE: 並列処理でタクト短縮
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="thread") as pool:
        for angle in angles:
            future = pool.submit(match4para, angle, img, t_img, m_img, mt_img, t_size, search_area, use_mask, compression_ratio)
            futures.append(future)

    # NOTE: 並列処理で取得したデータから最大スコアの情報を抜き出す
    max_score = -10.0
    for future in futures:
        score, roi, theta = future.result()
        if score > max_score:
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

    if templ_mask is not None:
        m_x, m_y = rotate_point(pt=[xmin + m_x, ymin + m_y],
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
                       center_pt=[m_x, m_y])


def no_rot_matching(src: np.ndarray,
                    templ: np.ndarray,
                    *,
                    search_area: Optional[list] = None,
                    mask: Optional[np.ndarray] = None,
                    compression_ratio: float = 100,
                    view_heatmap: bool = False
                    ) -> MatchResult:
    """無回転マッチング

    Args:
        src (np.ndarray): _description_
        templ (np.ndarray): _description_
        search_area (list, optional): _description_. Defaults to None.
        mask (np.ndarray, optional): _description_. Defaults to None.
        compression_ratio (float, optional): _description_. Defaults to 100.
        view_heatmap (bool, optional): _description_. Defaults to False.

    Returns:
        MatchResult: _description_
    """

    # height, width = src.shape[:2]
    t_h, t_w = templ.shape[:2]
    t_size = (t_h, t_w)

    if mask is None:
        use_mask = False
    else:
        use_mask = True

    # NOTE: リスケ―ル
    if compression_ratio > 1.0:
        compression_ratio = compression_ratio / 100.0

    img, t_img, m_img = _preprocess(src, templ, mask, compression_ratio)

    if search_area is not None:
        search_area = rescale_roi(search_area, compression_ratio)

    score, box, _ = match4para(0, img, t_img, m_img, t_size, search_area, use_mask, compression_ratio)

    # NOTE: 何も見つからなかったとき
    if score < 0.0:
        logger.debug('Not found Mathcing Area')
        return MatchResult()

    ymin, xmin, _, _ = box

    # NOTE: ヒートマップの計算
    if view_heatmap:
        heatmap = calc_heatmap(img=img, t_img=t_img, m_img=m_img,
                               theta=0, use_mask=use_mask)
    else:
        heatmap = np.array([0])

    return MatchResult(pt=[xmin, ymin], angle=0,
                       score=score,
                       polygon=np.array([[0, 0], [0, 0], [0, 0], [0, 0]]),
                       rect=box, heatmap=heatmap)


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

    data = no_rot_matching(src=src,
                           templ=templ,
                           mask=mask,
                           view_heatmap=True)

    imshow(data.heatmap)
