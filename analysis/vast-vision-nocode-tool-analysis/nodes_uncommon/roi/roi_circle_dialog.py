from PySide2.QtWidgets import QPushButton, QDialog, QMainWindow, QApplication, QVBoxLayout
import pyqtgraph as pg
import os
import sys

sys.path.append(os.path.dirname(__file__))
from pyqtgraph_view import ViewWidget
from cv_shapes_lib import Circle
from typing import Union

class BasicROICircleDialog(QDialog):
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
                size[0] = size[1]
            else:
                h, w = self.vb.img.shape[:2]
                pos = [int(w / 3), int(h / 3)]
                size = [int(w / 3), int(h / 3)]
                size[0] = size[1]
        except:
            h, w = self.vb.img.shape[:2]
            pos = [int(w / 3), int(h / 3)]
            size = [int(w / 3), int(h / 3)]
            size[0] = size[1]

        # circleROI
        self.roi = pg.CircleROI(pos=pos, size=size)
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
        # 円形
        pos = self.roi.pos()
        size = self.roi.size()
        x, y, r = self.vb.pg2xyr(pos, size, self.vb.img)
        answer = [Circle(x=x, y=y, radius=r)]
        return answer

    def set_roi(self, shape=Circle):
        try:
            roi = self.vb.cv2pg_circle(circle=shape, img=self.vb.img)
            self.vb.removeItem(self.roi)
            self.vb.addItem(roi)
            self.roi = roi
        except:
            pass

if __name__ == "__main__":
    app = QApplication()
    hoge = QMainWindow()
    hoge = BasicROICircleDialog()
    ret = hoge.exec_()
    if ret:
        print("true")
    else:
        print("false")
