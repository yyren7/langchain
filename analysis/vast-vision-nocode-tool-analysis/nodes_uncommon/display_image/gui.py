from ryven.gui_env import *

from qtpy.QtWidgets import QLineEdit, QFrame, QVBoxLayout
import cv2
import pyqtgraph as pg

import os
import sys
sys.path.append(os.path.dirname(__file__))
import numpy as np
from vastlib.utils import get_img_from_fs
from media_plugins.media_controller import media_controller

# class BasicViewWidget(NodeInputWidget, QGraphicsView):
#     def __init__(self, params):
#         NodeInputWidget.__init__(self, params)
#         QGraphicsView.__init__(self)
#         # シーンの定義
#         self.graphics_scene = QGraphicsScene()
#         self.setScene(self.graphics_scene)
#
#         self.img = np.zeros((640, 480, 3), dtype=np.uint8)
#         self.image_item = pg.ImageItem(image=self.img)
#         self.graphics_scene.addItem(self.image_item)
#         #self.image_item = None
#
#     def val_update_event(self, val: Data):
#         super().val_update_event(val)
#         path = val.payload
#         file_name = os.path.basename(path)
#         res = samba_lib.get_image(
#             "vast",
#             "vast",
#             "pysmb",
#             "vast",
#             "",
#             "192.168.0.100",
#             file_name
#         )
#         self.set_image(res)
#
#
#     def set_image(self, img):
#         img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#         self.image_item.setImage(image=img, autoLevels=False)
#         #self.graphics_scene.clear()

# 画像を表示するウィジェット
class BasicViewWidget(NodeInputWidget, QFrame):
    def __init__(self, params):
        NodeInputWidget.__init__(self, params)
        QFrame.__init__(self)

        self.media_controller = media_controller()

        # QFrameを継承し、レイアウトとQGraphicsLayoutViewを載せる
        layout = QVBoxLayout(self)
        self.gl = pg.GraphicsLayoutWidget()
        self.box_layout = self.gl.addLayout(row=0, col=0)
        self.box_layout.setBorder((255, 255, 255, 255), width=0.8)

        # QGraphicsLayoutViewにViewBoxを追加する
        self.vb = pg.ViewBox()
        self.vb.setAspectLocked()
        self.box_layout.addItem(self.vb, row=0, col=0, rowspan=1, colspan=1)

        # 画像を貼り付けておく
        img = np.zeros((640, 480, 3), dtype=np.uint8)
        self.img_item = pg.ImageItem(image=img)
        self.vb.addItem(self.img_item)

        # サイズ指定
        # TODO:画像に合わせて変わるもしくは指定できるようにする
        self.setMinimumWidth(640)
        self.setMinimumHeight(480)

        layout.addWidget(self.gl)


    # ポートの値が更新された際に発火するイベント
    def val_update_event(self, val: Data):
        super().val_update_event(val)
        try:
            # 値を取得（画像のパス）
            path = val.payload

            if os.environ["VAST_SERVER"] != "127.0.0.1":
                # ファイル名でsambaサーバを検索
                res = get_img_from_fs(path=path, ip_address=os.environ["VAST_SERVER"])
            else:
                res = self.media_controller.read(path, np.ndarray)

            # ViewBoxに画像をセット
            self.set_image(res)
        except:
            pass

    def set_image(self, img):
        try:
            # self.vb.clear()
            img = np.rot90(img, 2)
            img = cv2.flip(img, 1)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.img_item.setImage(image=img, autoLevels=False)
            # self.graphics_scene.clear()
        except:
            pass

class BasicInputWidget(NodeInputWidget, QLineEdit):
    def __init__(self, params):
        NodeInputWidget.__init__(self, params)
        QLineEdit.__init__(self)

        self.setMinimumWidth(60)
        self.setMaximumWidth(100)
        self.setStyleSheet("background-color:black;")

        ## loadしたとき毎回発火してしまう->silent=Trueで解決
        self.textChanged.connect(lambda: self.text_changed())
        self.init_value()

    def text_changed(self):
        self.update_node_input(Data(self.text()), silent=True)

    def get_state(self) -> dict:
        return {'value': self.text()}

    def set_state(self, data: dict):
        try:
            self.setText(data['value'])
        except:
            pass

    def init_value(self):
        # input the default value
        self.set_state({"value": self.input.default})

    def val_update_event(self, val: Data):
        try:
            super().val_update_event(val)
            # 値を取得（画像のパス）
            data = val.payload
            self.setText(str(data))
        except:
            pass

# 画像確認用のGUI
class BasicViewNodeGui(NodeGUI):
    # inputのポートの横に、BasicViewWidgetが付く
    input_widget_classes = {'input': BasicViewWidget,
                            'display_name': BasicInputWidget}
    def __init__(self, params):
        super().__init__(params)
        for i, inp in enumerate(self.node.inputs):
            if i == 0:
                self.input_widgets[inp] = {'name': 'input', 'pos': 'besides'}
            else:
                self.input_widgets[inp] = {'name': 'display_name', 'pos': 'besides'}


export_guis([
    BasicViewNodeGui,
])