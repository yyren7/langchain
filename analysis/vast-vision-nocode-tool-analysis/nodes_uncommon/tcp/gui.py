from ryven.gui_env import *

from qtpy.QtWidgets import QPushButton, QLabel, QLineEdit


import os
import sys

sys.path.append(os.path.dirname(__file__))
import numpy as np
from tcpserver_dialog import TCPDialog


class TCPServerRecvWidget(NodeMainWidget, QPushButton):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QPushButton.__init__(self)

        self.dlg = TCPDialog()
        self.clicked.connect(lambda: self.show_dialog())

    def show_dialog(self):
        self.dlg.exec_()
        self.update_node

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

    def val_update_event(self, val: Data):
        try:
            super().val_update_event(val)
            # 値を取得（画像のパス）
            data = val.payload
            self.setText(str(data))
        except:
            pass

    def init_value(self):
        # input the default value
        self.set_state({"value": self.input.default})

class TCPServerSendWidget(NodeMainWidget, QLabel):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QLabel.__init__(self)


class VASTTCPServerRecvWidget(NodeMainWidget, QPushButton):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QPushButton.__init__(self)

        self.dlg = TCPDialog()
        self.clicked.connect(lambda: self.show_dialog())

    def show_dialog(self):
        self.dlg.exec_()
        self.update_node


class VASTTCPServerSendWidget(NodeMainWidget, QLabel):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QLabel.__init__(self)


class TCPServerRecvGui(NodeGUI):
    main_widget_class = TCPServerRecvWidget
    main_widget_pos = 'between ports'
    color = '#99dd55'


class TCPServerSendGui(NodeGUI):
    input_widget_classes = {
        'in': BasicInputWidget,
    }
    main_widget_class = TCPServerSendWidget
    main_widget_pos = 'between ports'
    color = '#99dd55'

    def __init__(self, params):
        super().__init__(params)
        for inp in self.node.inputs:
            self.input_widgets[inp] = {'name': 'in', 'pos': 'besides'}


class VASTTCPServerRecvGui(NodeGUI):
    main_widget_class = VASTTCPServerRecvWidget
    main_widget_pos = 'between ports'
    color = '#99dd55'


class VASTTCPServerSendGui(NodeGUI):
    main_widget_class = VASTTCPServerSendWidget
    main_widget_pos = 'between ports'
    color = '#99dd55'


export_guis([
    TCPServerRecvGui,
    TCPServerSendGui,
    VASTTCPServerRecvGui,
    VASTTCPServerSendGui
])
