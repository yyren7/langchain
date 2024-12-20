# -*- coding : UTF-8 -*-
# ===============================================================================
# Name      : mask_function.py
# Version   : 1.0.0
# Brief     :
# Time-stamp:2024-08-23 13:46
# Copyirght 2024 Tatsuya Sugino
# ===============================================================================
import cv2
import numpy as np
from typing import List, Optional, Tuple, Union

from cv_shapes_lib import CvShape, Rectangle, Circle, Ellipse, Polygon


def make_mask_img(img: np.ndarray,
                  canvas: Union[np.ndarray, None],
                  inverse: Union[bool, None],
                  shape: CvShape):
    # イメージが入力されていない場合キャンバスをコピー
    if img is None:
        # イメージ・キャンバスの両方が無い場合エラー
        if canvas is None:
            raise SystemError("Please input img or canvas.")
        else:
            img = canvas.copy()

    # 画像の大きさを取得
    height, width = img.shape[:2]

    # キャンバスが指定されていない場合、imgからキャンバスを作成
    if canvas is None:
        if inverse:
            canvas = np.full((height, width), 255, dtype=np.uint8)
        else:
            canvas = np.zeros((height, width), dtype=np.uint8)

    # 描画する色を設定
    # color = (255, 255, 255) if inverse else (0, 0, 0)
    # color = (0, 0, 0) if inverse else (255, 255, 255)
    if inverse:
        color = (0, 0, 0)
    else:
        color = (255, 255, 255)


    if not isinstance(shape, CvShape):
        raise TypeError(f"Shape data must be an instance of CvShape, got {type(shape_data)}")

    # draw_shapeメソッドを呼び出して形状を描画
    shape.draw_shape(canvas, color)

    return canvas


if __name__ == "__main__":
    # テスト用の画像とキャンバスを作成
    img = np.ones((300, 300, 3), dtype=np.uint8)
    img = img * 255
    canvas = None

    # 形状を定義
    rect = [Rectangle(x1=50, y1=50, x2=150, y2=150)]

    # マスク画像を作成
    mask = make_mask_img(img, canvas, inverse=False, shape=rect)

    # 結果を表示
    cv2.imshow("Mask", mask)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
