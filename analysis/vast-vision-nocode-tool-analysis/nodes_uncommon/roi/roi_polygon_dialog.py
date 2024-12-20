from PySide2.QtWidgets import QPushButton, QDialog, QMainWindow, QApplication, QVBoxLayout
import pyqtgraph as pg
import os
import sys

sys.path.append(os.path.dirname(__file__))
from pyqtgraph_view import ViewWidget
from cv_shapes_lib import Polygon


class BasicROIPolygonDialog(QDialog):
    def __init__(self, pos=[]):
        QDialog.__init__(self)

        # QFrameを継承し、レイアウトとQGraphicsLayoutViewを載せる
        layout = QVBoxLayout(self)
        self.gl = ViewWidget()
        self.box_layout = self.gl.addLayout(row=0, col=0)
        self.box_layout.setBorder((255, 255, 255, 255), width=0.8)

        # QGraphicsLayoutViewにViewBoxを追加する
        self.vb = self.gl.add_viewbox()
        n = 5
        # 矩形ROIの初期座標計算
        try:
            if len(pos) == 4:
                h, w = self.vb.img.shape[:2]
                pos1 = [int(2 * h / 3), int(w / 3)]
                pos2 = [int(h / 2), int(2 * w / 3)]
                pos3 = [int(h / 3), int(w / 3)]
                pos4 = [int(h / 3), int(w / 4)]
                size = [int(h / 3), int(h / 3)]

            else:
                h, w = self.vb.img.shape[:2]
                pos1 = [int(2 * h / 3), int(w / 3)]
                pos2 = [int(h / 2), int(2 * w / 3)]
                pos3 = [int(h / 3), int(w / 3)]
                pos4 = [int(h / 3), int(w / 4)]
                size = [int(h / 3), int(h / 3)]
        except:
            h, w = self.vb.img.shape[:2]
            pos1 = [int(2 * h / 3), int(w / 3)]
            pos2 = [int(h / 2), int(2 * w / 3)]
            pos3 = [int(h / 3), int(w / 3)]
            pos4 = [int(h / 3), int(w / 4)]
            size = [int(h / 3), int(h / 3)]

        # polygonROI
        # movable=False,
        self.roi = pg.PolyLineROI(positions=[pos1, pos2, pos3], closed=True, rotatable=False, angle=0)
        self.vb.add_roi(self.roi)
        self.apply_button = QPushButton(text="Accept")
        self.apply_button.clicked.connect(lambda: self.accept_change())
        # self.apply_button.clicked.connect(lambda: self.get_roi())

        self.roi_pos = self.roi.pos()
        self.roi_size = self.roi.size()
        layout.addWidget(self.gl)
        layout.addWidget(self.apply_button)

    # when push accept button, keep shape
    def accept_change(self):
        self.roi_pos = self.roi.pos()
        self.roi_size = self.roi.size()
        points = self.get_polygon_points()
        points = self.vb.pg2cv_polygon(points, self.vb.img)
        self.accept()

    # when push x button, restore shape
    def reject(self):
        self.roi.setPos(self.roi_pos)
        self.roi.setSize(self.roi_size)
        super().reject()

    def set_image(self, img):
        try:
            self.vb.set_image(img)
        except:
            pass

    def get_roi(self):
        points = self.get_polygon_points()
        final_points = self.vb.pg2cv_polygon(points, self.vb.img)
        answer = [Polygon(points=final_points)]
        return answer

    def set_roi(self, shape=Polygon):
        try:
            roi = self.vb.cv2pg_polygon(polygon=shape, img=self.vb.img)
            self.vb.removeItem(self.roi)
            self.vb.addItem(roi)
            self.roi = roi
        except:
            pass

    def get_rotation_angle(self):
        """ 角度 """
        angle = self.roi.state.get('angle', 0) % 360
        return angle

    def get_polygon_points(self):
        """ 多角形端点座標 """
        """
        points = []
        shape = self.roi.shape()
        print("shape", shape)
        pts = self.roi.getSceneHandlePositions()
        for i in range(shape.elementCount()):
            element = shape.elementAt(i)
            if element.type == 1:
                # x = int(element.x)
                # y = int(element.y)
                points += [[element.x, element.y]]
        """
        pts = self.roi.getSceneHandlePositions()
        moved_points = []
        for pt in pts:
            element = self.roi.mapSceneToParent(pt[1])
            moved_points += [[element.x(), element.y()]]
        return moved_points


if __name__ == "__main__":
    app = QApplication()
    hoge = QMainWindow()
    hoge = BasicROIPolygonDialog()
    ret = hoge.exec_()
    if ret:
        print("true")
    else:
        print("false")
