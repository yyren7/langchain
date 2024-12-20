from PySide2.QtWidgets import QPushButton, QDialog, QMainWindow, QApplication, QVBoxLayout
import pyqtgraph as pg
import os
import sys

sys.path.append(os.path.dirname(__file__))
from pyqtgraph_view import ViewWidget
from cv_shapes_lib import Rectangle, Polygon
from typing import Union

class BasicROIRectangleDialog(QDialog):
    def __init__(self, pos=[]):
        QDialog.__init__(self)

        # QFrameを継承し、レイアウトとQGraphicsLayoutViewを載せる
        layout = QVBoxLayout(self)
        self.gl = ViewWidget()
        self.box_layout = self.gl.addLayout(row=0, col=0)
        self.box_layout.setBorder((255, 255, 255, 255), width=0.8)

        # QGraphicsLayoutViewにViewBoxを追加する
        self.vb = self.gl.add_viewbox()

        # 矩形ROIの初期座標計算
        try:
            if len(pos) == 4:
                pos, size = self.vb.cv2pg(pos, self.vb.img)
                angle = 0

            else:
                h, w = self.vb.img.shape[:2]
                pos = [int(w / 3), int(h / 3)]
                size = [int(w / 3), int(h / 3)]
        except:
            h, w = self.vb.img.shape[:2]
            pos = [int(w / 3), int(h / 3)]
            size = [int(w / 3), int(h / 3)]

        # rectROI
        self.roi = pg.RectROI(pos=pos, size=size)
        self.roi.addRotateHandle([0, 0], [0.5, 0.5])
        self.vb.add_roi(self.roi)
        self.apply_button = QPushButton(text="Accept")
        self.apply_button2 = QPushButton(text="reset angle")
        self.apply_button.clicked.connect(lambda: self.accept_change())
        self.apply_button2.clicked.connect(lambda: self.reset_angle())
        # self.apply_button.clicked.connect(lambda: self.get_roi())

        self.roi_pos = self.roi.pos()
        self.roi_size = self.roi.size()

        layout.addWidget(self.gl)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.apply_button2)

    # when push accept button, keep shape
    def accept_change(self):
        self.roi_pos = self.roi.pos()
        self.roi_size = self.roi.size()
        self.accept()

    def reset_angle(self):
        self.roi.setAngle(0)

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
        angle = self.get_rotation_angle()
        if angle == 0:
            # 回転なし矩形
            pos = self.roi.pos()
            size = self.roi.size()
            y1, x1, y2, x2 = self.vb.pg2cv(pos, size, self.vb.img)
            answer = [Rectangle(x1=x1, y1=y1, x2=x2, y2=y2)]
            return answer
        else:
            # 回転あり矩形
            pos = self.roi.pos()
            size = self.roi.size()
            points = self.vb.pg2cv_rotate_rect(pos, size, angle, self.vb.img)
            answer = [Polygon(points=points)]
            return answer

    def set_roi(self, shape=Union[Rectangle, Polygon]):
        try:
            if shape.shape_type == "rectangle":
                roi = self.vb.cv2pg_rect(rect=shape, img=self.vb.img)
                roi.addRotateHandle([0, 0], [0.5, 0.5])
                self.vb.removeItem(self.roi)
                self.vb.addItem(roi)
                self.roi = roi
            elif shape.shape_type == "polygon":
                roi = self.vb.cv2pg_rect_rotate(rect=shape, img=self.vb.img)
                roi.addRotateHandle([0, 0], [0.5, 0.5])
                self.vb.removeItem(self.roi)
                self.vb.addItem(roi)
                self.roi = roi
        except:
            pass

    def get_rotation_angle(self):
        """ 回転角度 """
        angle = self.roi.state.get('angle', 0) % 360
        return angle


if __name__ == "__main__":
    app = QApplication()
    hoge = QMainWindow()
    hoge = BasicROIRectangleDialog()
    ret = hoge.exec_()
    if ret:
        print("true")
    else:
        print("false")
