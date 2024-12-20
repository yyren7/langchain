# ===============================================================================
# Name      : pyqtgraph_view.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-09-28 11:51
# Copyirght 2022 Hiroya Aoyama
# ===============================================================================

import pyqtgraph as pg
import numpy as np
import copy
import cv2
from typing import Union, Tuple, Optional
from cv_shapes_lib import Rectangle, Circle, Ellipse, Polygon
import math

class CustomViewBox(pg.ViewBox):
    """
    ViewBoxのカスタム継承クラス

    Args:
        pg (_type_): _description_
    """

    def __init__(self, parent=None):
        super(CustomViewBox, self).__init__(parent)
        # NOTE: アスペクト比を固定
        self.setAspectLocked()
        # NOTE: 描画するアイテムを管理
        self.img = np.zeros((640, 480, 3), dtype=np.uint8)
        self.img_item = pg.ImageItem(image=self.img)
        self.addItem(self.img_item)
        self.default_state = self.getState()
        # NOTE: roiのみひとつのviewboxに複数描画する可能性がある
        self.rois = []

    def set_image(self, img: np.ndarray) -> None:
        """画像を貼り付け

        Args:
            img (_type_): _description_

        Returns:
            _type_: _description_
        """
        # NOTE: 3chに変換
        if img.ndim != 3:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # NOTE: setConfigOptionsか、dtypeのせいで方向がおかしい気がする
        img = np.rot90(img, 2)
        img = cv2.flip(img, 1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        self.img = img.copy()
        # NOTE: レベルを手動調整
        self.img_item.setImage(image=self.img, autoLevels=False)
        # self.img_item.setLevels([np.min(self.img), np.max(self.img)])
        self.img_item.setLevels([0, 255])
        self.default_state = self.getState()
        # NOTE: 画像全体が収まるように自動調整
        self.autoRange()
        self.set_roi_range()

    def set_roi_range(self):
        h, w = self.img.shape[:2]
        #     for roi in self.rois:
        #         roi.maxBounds = QRectF(0, 0, w, h)

    def set_frame(self, img: np.ndarray) -> None:
        """ストリーミングの貼り付け

        Args:
            img (_type_): _description_

        Returns:
            _type_: _description_
        """
        # NOTE: 3chに変換
        if img.ndim != 3:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # NOTE: setConfigOptionsか、dtypeのせいで方向がおかしい気がする
        img = np.rot90(img, 2)
        img = cv2.flip(img, 1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        self.img = img.copy()
        # NOTE: レベルを手動調整
        self.img_item.setImage(image=self.img, autoLevels=False)
        self.img_item.setLevels([0, 255])
        self.default_state = self.getState()
        self.set_roi_range()

    def reset_vb(self) -> None:
        """vbの状態を画像を貼り付けた初めの状態にリセット"""
        self.setState(copy.deepcopy(self.default_state))

    def get_roi_cvimg(self, roi: pg.ROI):
        success = True
        try:
            img_float64 = self.rois[0].getArrayRegion(self.img.copy(), self.img_item)
            img = img_float64.astype(np.uint8)
            img = np.rot90(img, 2)
            img = cv2.flip(img, 1)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            print(e)
            img = -1
            success = False

        return success, img

    def add_roi(self, roi: pg.ROI) -> None:
        """_summary_

        Args:
            roi (pg.ROI): _description_
        """
        self.addItem(roi)
        self.rois.append(roi)

    def reset_roi(self, img: np.ndarray) -> None:
        """
        Args:
            img (np.ndarray): _description_
        """
        self.clear()
        img = np.rot90(img, 2)
        img = cv2.flip(img, 1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.img_item = pg.ImageItem(image=img)
        self.addItem(self.img_item)

    def get_pt_rgb(self, src: np.ndarray, pt: tuple) -> Tuple[int, int, int]:
        """RGBの成分を返す"""
        h, w = src.shape[:2]
        if pt[0] < 0 or pt[0] > w - 1:
            return -1, -1, -1
        if pt[1] < 0 or pt[1] > h - 1:
            return -1, -1, -1
        b, g, r = src[pt[1], pt[0], :]
        return b, g, r

    def get_pt_gray(self, src: np.ndarray, pt: tuple) -> Tuple[int, int, int]:
        """RGBの成分を返す"""
        h, w = src.shape[:2]
        if pt[0] < 0 or pt[0] > w - 1:
            return -1, -1, -1
        if pt[1] < 0 or pt[1] > h - 1:
            return -1, -1, -1
        val = src[pt[1], pt[0]]
        return val, val, val

    @staticmethod
    def cv2pg(roi: Union[list, np.ndarray], img: np.ndarray) -> Tuple[list, list]:
        """ [xmin, ymin, xmax, ymax]をpyqtgraph座標の[x, y] [l_x, l_y]に変換"""
        h, _ = img.shape[:2]
        x = roi[0]
        l_x = roi[2] - roi[0]
        l_y = roi[3] - roi[1]
        y = h - roi[3]  # NOTE: yは正負逆
        return [x, y], [l_x, l_y]

    @staticmethod
    def _cv2pg(roi: Union[list, np.ndarray], h: int) -> Tuple[list, list]:
        x = roi[0]
        l_x = roi[2] - roi[0]
        l_y = roi[3] - roi[1]
        y = h - roi[3]
        return [x, y], [l_x, l_y]

    @staticmethod
    def pg2cv_polygon(origin_points: list[pg.Point], img: np.ndarray) -> list:
        # roi_polygon　[p1(x, y), p2...pn]
        h, w = img.shape[:2]
        points = []
        # print(h, w)
        # print(origin_points)
        for (x, y) in origin_points:
            points.append([int(x), int(h - y)])
        # x = int(element.x)
        # y = int(element.y)
        return points

    @staticmethod
    def pg2cv(pos: pg.Point, len: pg.Point, img: np.ndarray) -> list:
        # roi_transition_rect　[ymin, xmin, ymax, xmax]
        h, _ = img.shape[:2]
        xmin = int(pos[0])
        xmax = int(pos[0] + len[0])
        ymin = int(h - (pos[1] + len[1]))
        ymax = int(h - pos[1])

        return [ymin, xmin, ymax, xmax]

    @staticmethod
    def pg2cv_rotate_rect(pos: pg.Point, len: pg.Point, angle: int, img: np.ndarray) -> list[tuple[int, int]]:
        # roi_transition_rotate_rect　[p1(x, y), p2, p3, p4]
        h, _ = img.shape[:2]
        len1 = [len[0], 0]
        len2 = len
        len3 = [0, len[1]]
        rotation_matrix = np.array([[np.cos(np.deg2rad(angle)), -np.sin(np.deg2rad(angle))],
                                    [np.sin(np.deg2rad(angle)), np.cos(np.deg2rad(angle))]])
        p1 = np.dot(rotation_matrix, len1) + pos
        p2 = np.dot(rotation_matrix, len2) + pos
        p3 = np.dot(rotation_matrix, len3) + pos
        p4 = pos
        p1 = (int(p1[0]), int(h - p1[1]))
        p2 = (int(p2[0]), int(h - p2[1]))
        p3 = (int(p3[0]), int(h - p3[1]))
        p4 = (int(p4[0]), int(h - p4[1]))
        points = [p1, p2, p3, p4]
        return points

    @staticmethod
    def _pg2cv(pos: pg.Point, len: pg.Point, h: int) -> list:
        xmin = int(pos[0])
        xmax = int(pos[0] + len[0])
        ymin = int(h - (pos[1] + len[1]))
        ymax = int(h - pos[1])

        return [xmin, ymin, xmax, ymax]

    @staticmethod
    def xyr2pg(xyr: Union[list, np.ndarray], img: np.ndarray) -> Tuple[list, list]:
        h, _ = img.shape[:2]
        x = xyr[0] - xyr[2]
        l_x = int(xyr[2] * 2)
        l_y = int(xyr[2] * 2)
        y = h - (xyr[1] + xyr[2])

        return [x, y], [l_x, l_y]

    @staticmethod
    def pg2xyr(pos: pg.Point, len: pg.Point, img: np.ndarray) -> list:
        # roi_transition_circle　[x, y, r]
        h, _ = img.shape[:2]
        r = int(len[0] / 2)
        x = int(pos[0] + len[0] / 2)
        y_inv = int(pos[1] + len[1] / 2)
        y = h - y_inv

        return [x, y, r]

    @staticmethod
    def pg2xyr_ellipse(pos: pg.Point, len: pg.Point, angle: int, img: np.ndarray) -> list:
        # roi_transition_ellipse　[x, y, r_h平行軸, r_v垂直軸, angle]
        h, _ = img.shape[:2]
        r1 = int(len[0] / 2)
        r2 = int(len[1] / 2)
        rotation_matrix = np.array([[np.cos(np.deg2rad(angle)), -np.sin(np.deg2rad(angle))],
                                    [np.sin(np.deg2rad(angle)), np.cos(np.deg2rad(angle))]])
        # 中心点
        rotated_center = np.dot(rotation_matrix, len / 2) + pos
        # print('center', rotated_center)
        x = int(rotated_center[0])
        y = int(h - rotated_center[1])
        angle = int(-angle)
        return [x, y, r1, r2, angle]

    @staticmethod
    def rotate_reset_ellipse(pos: pg.Point, len: pg.Point, angle: int):
        # roi_transition_ellipse　[x, y, r_h平行軸, r_v垂直軸, angle]
        r1 = int(len[0] / 2)
        r2 = int(len[1] / 2)
        rotation_matrix = np.array([[np.cos(np.deg2rad(angle)), -np.sin(np.deg2rad(angle))],
                                    [np.sin(np.deg2rad(angle)), np.cos(np.deg2rad(angle))]])
        # 中心点
        rotated_center = np.dot(rotation_matrix, len / 2) + pos
        # print('center', rotated_center)
        x = int(rotated_center[0])-r1
        y = int(rotated_center[1])-r2
        pos=pg.Point(x,y)
        return pos

    @staticmethod
    def cv2pg_polygon(polygon: Polygon, img: np.ndarray):
        h, _ = img.shape[:2]
        points = []
        for (x, y) in polygon.points:
            points.append([int(x), int(h - y)])
        # polygonROI
        # movable=False,
        polygon_roi = pg.PolyLineROI(positions=[points], closed=True, rotatable=False, angle=0)
        return polygon_roi

    @staticmethod
    def cv2pg_ellipse(ellipse: Ellipse, img: np.ndarray):
        h, _ = img.shape[:2]
        size = ellipse.axis1 * 2, ellipse.axis2 * 2
        length = pg.Point(ellipse.axis1 * 2, ellipse.axis2 * 2)
        angle = -ellipse.angle
        rotation_matrix = np.array([[np.cos(np.deg2rad(angle)), -np.sin(np.deg2rad(angle))],
                                    [np.sin(np.deg2rad(angle)), np.cos(np.deg2rad(angle))]])
        pos = ellipse.x, h - ellipse.y
        rotated_center = -np.dot(rotation_matrix, length / 2) + pos
        pos = rotated_center
        ellipse_roi = pg.EllipseROI(pos=pos, size=size, angle=angle)
        return ellipse_roi

    @staticmethod
    def cv2pg_rect(rect: Rectangle, img: np.ndarray):
        # polygonROI
        # movable=False,
        h, _ = img.shape[:2]
        pos = rect.x1, h - rect.y2
        size = rect.x2 - rect.x1, rect.y2 - rect.y1
        rect_roi = pg.RectROI(pos=pos, size=size)
        return rect_roi

    @staticmethod
    def cv2pg_rect_rotate(rect: Polygon, img: np.ndarray):
        x = []
        y = []
        h, _ = img.shape[:2]
        for (_x, _y) in rect.points:
            x.append(_x)
            y.append(h - _y)
        pos = x[3], y[3]
        size = ((x[1] - x[2]) ** 2 + (y[1] - y[2]) ** 2) ** 0.5, ((x[0] - x[1]) ** 2 + (y[0] - y[1]) ** 2) ** 0.5
        angle = np.arctan2((y[0] - y[3]), (x[0] - x[3]))
        deg = math.degrees(angle)

        rect_roi = pg.RectROI(pos=pos, size=size, angle=deg)
        return rect_roi

    @staticmethod
    def cv2pg_circle(circle: Circle, img: np.ndarray):
        # polygonROI
        # movable=False,
        h, _ = img.shape[:2]
        size = circle.radius * 2, circle.radius * 2
        pos = circle.x - (size[0] / 2), h - (circle.y + size[1] / 2)
        circle_roi = pg.CircleROI(pos=pos, size=size)
        return circle_roi


class ViewWidget(pg.GraphicsLayoutWidget):
    pg.setConfigOptions(imageAxisOrder='row-major')

    def __init__(self):
        super(ViewWidget, self).__init__()
        self.box_layout = self.addLayout(row=0, col=0)
        self.box_layout.setContentsMargins(0, 0, 0, 0)
        self.box_layout.setBorder((255, 255, 255, 255), width=0.8)
        self.viewboxs = []
        self.default_state = []
        self.img_items = []
        self.imgs = []

    def add_viewbox(self, img: Optional[np.ndarray] = None,
                    row: int = 0, col: int = 0,
                    rowspan: int = 1, colspan: int = 1
                    ) -> CustomViewBox:
        """GraphicsLayoutWidgetにViewBoxとImageItemを追加"""
        # NOTE: ViewBoxを追加
        vb = CustomViewBox()
        self.box_layout.addItem(vb, row=row, col=col, rowspan=rowspan, colspan=colspan)
        # NOTE: 画像を加工して追加
        if img is None:
            img = np.zeros((640, 480, 3), dtype=np.uint8)
        vb.set_image(img)
        return vb
