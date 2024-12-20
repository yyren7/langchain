# ===============================================================================
# Name      : template_matching_lib.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-08-18 10:11
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================
import numpy as np
import cv2
from pydantic import BaseModel
import matplotlib.pyplot as plt
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont


try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


class CustomBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class MultiBoxesResult(CustomBaseModel):
    num_box: int = 0
    bboxes: list = []
    scores: list = []
    classes: list = []
    heatmap: np.ndarray = np.ndarray([0])
    message: str = ''


def create_graph_image(fig: plt.Figure) -> np.ndarray:
    fig.canvas.draw()  # type: ignore
    graph_image = np.array(fig.canvas.renderer.buffer_rgba())  # type: ignore
    graph_image = cv2.cvtColor(graph_image, cv2.COLOR_RGBA2BGR)
    return graph_image


def preprocess(src: np.ndarray, templ: np.ndarray,
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
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if t_img.ndim == 3:
        t_img = cv2.cvtColor(t_img, cv2.COLOR_BGR2GRAY)

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
    return img


def iou_np(box: np.ndarray, other_boxes: np.ndarray,
           box_area: int, other_box_areas: np.ndarray) -> np.ndarray:
    """矩形Aと他の矩形BのIoUを計算

    Args:
        box: array([xmin, ymin, xmax, ymax])
        other_boxes: array([box1, box2, box3,...])
        box_area: int
        other_box_areas: [a1, a2, ....]

    Returns:
        _type_: _description_
    """
    # NOTE: 対象矩形Aと他矩形Bの共通部分(intersection)の面積を計算するために、
    # N個のBについて、Aとの共通部分のxmin, ymin, xmax, ymaxを一気に計算
    abx_mn = np.maximum(box[0], other_boxes[:, 0])  # xmin
    aby_mn = np.maximum(box[1], other_boxes[:, 1])  # ymin
    abx_mx = np.minimum(box[2], other_boxes[:, 2])  # xmax
    aby_mx = np.minimum(box[3], other_boxes[:, 3])  # ymax
    # NOTE: 共通部分の幅を計算。共通部分が無ければ0
    w = np.maximum(0, abx_mx - abx_mn + 1)
    # NOTE: 共通部分の高さを計算。共通部分が無ければ0
    h = np.maximum(0, aby_mx - aby_mn + 1)
    # NOTE: 共通部分の面積を計算。共通部分が無ければ0
    intersect = w * h
    # NOTE: N個のBについて、AとのIoUを一気に計算
    iou_np = intersect / (box_area + other_box_areas - intersect)
    return iou_np


def nms_fast(bboxes: list, scores: list, classes: list = [],
             iou_thresh: float = 0.5
             ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Non-Maximum-Suppression

    Args:
        bboxes (list): _description_
        scores (list): _description_
        classes (list, optional): _description_. Defaults to [].
        iou_thresh (float, optional): _description_. Defaults to 0.5.

    Returns:
        _type_: _description_
    """
    bboxes_ = np.array(bboxes)
    scores_ = np.array(scores)
    classes_ = np.array(classes)

    # NOTE: bboxesの矩形の面積を一気に計算
    areas = (bboxes_[:, 2] - bboxes_[:, 0] + 1) \
        * (bboxes_[:, 3] - bboxes_[:, 1] + 1)

    # NOTE: scoreの昇順(小さい順)の矩形インデックスのリストを取得
    sort_index = np.argsort(scores_)

    i = -1  # NOTE: 未処理の矩形のindex
    while (len(sort_index) >= 2 - i):
        # NOTE: score最大のindexを取得
        max_score_index = sort_index[i]
        # NOTE: score最大以外のindexを取得
        index_list = sort_index[:i]
        # NOTE: score最大の矩形それ以外の矩形のIoUを計算
        iou = iou_np(bboxes_[max_score_index], bboxes_[index_list],
                     areas[max_score_index], areas[index_list])

        # NOTE: IoUが閾値iou_threshold以上の矩形を計算
        del_index = np.where(iou >= iou_thresh)
        # NOTE: IoUが閾値iou_threshold以上の矩形を削除
        sort_index = np.delete(sort_index, del_index)
        i -= 1  # NOTE: 未処理の矩形のindexを1減らす

    # NOTE: bboxes, scores, classesから削除されなかった矩形のindexのみを抽出
    bboxes_ = bboxes_[sort_index]
    scores_ = scores_[sort_index]
    if classes:
        classes_ = classes_[sort_index]

    return bboxes_, scores_, classes_


def multi_matching(src: np.ndarray, templ: np.ndarray, mask: Optional[np.ndarray],
                   score_th: float, iou_th: float, view_heatmap: bool = False
                   ) -> MultiBoxesResult:

    h, w = templ.shape[:2]
    heatmap = np.ndarray([0])

    match = cv2.matchTemplate(src, templ, cv2.TM_CCOEFF_NORMED, mask=mask)

    if view_heatmap:
        heatmap = get_heatmap(match)

    boxes: list = []
    loc = np.where((match >= score_th) & (match < 1.0))

    # NOTE: 各領域のスコア
    scores = match[loc]

    # NOTE: スコアのサイズがゼロの場合、該当領域なし
    if scores.size == 0:
        return MultiBoxesResult()

    # NOTE: 左上の座標とテンプレート幅から矩形情報を作成
    for pt in zip(*loc[::-1]):
        y_min = pt[1]
        x_min = pt[0]
        boxes.append([y_min, x_min, y_min + h, x_min + w])

    # NOTE: 重なった矩形を削除
    _boxes, _scores, _classes = nms_fast(bboxes=boxes, scores=scores, iou_thresh=iou_th)
    num_box = _boxes.shape[0]

    return MultiBoxesResult(num_box=num_box,
                            bboxes=_boxes.tolist(),
                            scores=np.round(_scores, decimals=2).tolist(),
                            classes=_classes.tolist(),
                            heatmap=heatmap)


def m_match(src: np.ndarray,
            templ: np.ndarray,
            *,
            search_area: Optional[list] = None,
            mask: Optional[np.ndarray] = None,
            compression_ratio: float = 100,
            score_th: float = 0,
            iou_th: float = 0,
            view_heatmap: bool = False
            ) -> MultiBoxesResult:

    # NOTE: 圧縮率の設定　低いほど解像度が悪くなり処理速度が早くなる
    if compression_ratio > 1.0:
        compression_ratio = compression_ratio / 100.0

    # NOTE: 画像と座標をリサイズ
    img, t_img, m_img = preprocess(src, templ, mask, compression_ratio)
    if search_area is not None:
        search_area = rescale_roi(search_area, compression_ratio)

    # NOTE: マッチング
    res = multi_matching(src=img,
                         templ=t_img,
                         mask=m_img,
                         score_th=score_th,
                         iou_th=iou_th,
                         view_heatmap=view_heatmap)

    # NOTE: スケール調整
    res.bboxes = [rescale_roi(box, 1.0 / compression_ratio) for box in res.bboxes]
    return res


def vis_bbox_cv2(dst: np.ndarray, bbox: list, label: str, score: float):
    dst = cv2.rectangle(dst, (bbox[1], bbox[0]), (bbox[3], bbox[2]), (0, 0, 255), 2, 1)
    dst = cv2.rectangle(dst, (int(bbox[1]), int(bbox[0] - 25)), (bbox[3], bbox[0]), (255, 255, 255), -1)
    p_str = f'{label}:{score:0.3f}'
    dst = cv2.putText(dst, p_str, (bbox[1], int(bbox[0] - 5)), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 0), 1)
    return dst


def draw_multi_bbox(dst: np.ndarray, bboxes: list, scores: list, classes: list = []):
    LABEL_DATA = ['0deg', '90deg', '180deg', '270deg']
    if not classes:
        classes = [0] * len(scores)

    for bbox, score, cls in zip(bboxes, scores, classes):
        label = LABEL_DATA[cls]
        dst = vis_bbox_cv2(dst, bbox, label, score)

    return dst


def get_text_color(color: tuple) -> str:
    r, g, b, _ = color
    brightness = r * 0.299 + g * 0.587 + b * 0.114
    return "black" if brightness > 180 else "white"


def draw_boxes(src: np.ndarray, bboxes: list, scores: list, classes: list = [], classlabels: list = []):
    if not classlabels:
        classlabels = ['0deg', '90deg', '180deg', '270deg']
    if not classes:
        classes = [0] * len(scores)

    # NOTE: numpy -> Image
    img = Image.fromarray(src)
    draw = ImageDraw.Draw(img, mode="RGBA")

    # NOTE: 色の一覧を作成する。
    cmap = plt.cm.get_cmap("hsv", len(classlabels) + 1)  # type:ignore

    # NOTE: フォントを作成する。
    fontsize = max(15, int(0.03 * min(img.size)))
    fontname = "meiryo.ttc"
    font = ImageFont.truetype(fontname, size=fontsize)

    for bbox, score, class_id in zip(bboxes, scores, classes):
        # NOTE: 色を取得する
        color = cmap(class_id, bytes=True)
        # NOTE: ラベル
        caption = classlabels[class_id]
        # NOTE: ラベルにスコアを追加
        caption += f" {score:.0%}"  # "score" が存在する場合はパーセントで表示する。
        # NOTE: 矩形を描画する。
        draw.rectangle(
            (bbox[1], bbox[0], bbox[3], bbox[2]), outline=color, width=3
        )

        # NOTE: ラベルを描画する。
        text_w, text_h = draw.textsize(caption, font=font)
        text_x2 = bbox[1] + text_w - 1
        text_y2 = bbox[0] + text_h - 1

        # NOTE: テキストカラーを取得
        text_color = get_text_color(color)
        draw.rectangle((bbox[1], bbox[0], text_x2, text_y2), fill=color)
        draw.text((bbox[1], bbox[0]), caption, fill=text_color, font=font)

    return np.array(img)


if __name__ == '__main__':
    # import os
    # import time
    pass
