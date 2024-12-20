from ryven.gui_env import *

from qtpy.QtWidgets import QPushButton, QWidget, QFrame, QVBoxLayout, QFileDialog, QLabel
import pyqtgraph as pg
from PySide2 import QtCore
import os
import sys

sys.path.append(os.path.dirname(__file__))
import numpy as np


class PrgAndWidget(NodeMainWidget, QLabel):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QLabel.__init__(self)

        # Create a QLabel to display some text
        self.label1 = QLabel(' default')
        self.label2 = QLabel(' status')
        self.label1.setAlignment(QtCore.Qt.AlignCenter)
        self.label2.setAlignment(QtCore.Qt.AlignCenter)

        # Set the widget's layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.label1)
        self.layout.addWidget(self.label2)

    def update_label1(self):
        self.label1.setText('input1=1')
        self.label2.setText('input2=0')
        # print('input1=1')

    def update_label2(self):
        self.label1.setText('input1=0')
        self.label2.setText('input2=1')
        # print('input2=1')

    def update_label_reset(self):
        self.label1.setText('input 1+2')
        self.label2.setText('activated')
        # print('reset')


class PrgOrWidget(NodeMainWidget, QLabel):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QLabel.__init__(self)

        # Create a QLabel to display some text
        self.label1 = QLabel(' default')
        self.label2 = QLabel(' status')
        self.label1.setAlignment(QtCore.Qt.AlignCenter)
        self.label2.setAlignment(QtCore.Qt.AlignCenter)

        # Set the widget's layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.label1)
        self.layout.addWidget(self.label2)

    def update_label1(self):
        self.label1.setText('input1')
        self.label2.setText('activated')
        # print('input1=1')

    def update_label2(self):
        self.label1.setText('input2')
        self.label2.setText('activated')
        # print('input2=1')


class PrgSwitchWidget(NodeMainWidget, QLabel):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QLabel.__init__(self)

        # Create a QLabel to display some text
        self.label1 = QLabel('switch button')
        self.label2 = QLabel('loop entrance')
        self.label1.setAlignment(QtCore.Qt.AlignCenter)
        self.label2.setAlignment(QtCore.Qt.AlignCenter)

        # Set the widget's layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.label1)
        self.layout.addWidget(self.label2)

    def update_label1(self):
        if self.label1.text() == 'button negative' or self.label1.text() == 'switch button':
            self.label1.setText('button active')
        elif self.label1.text() == 'button active':
            self.label1.setText('button negative')
        # print('input1=1')

    def update_label2(self):
        if self.label1.text() == 'button negative' or self.label1.text() == 'switch button':
            self.label2.setText('loop negative')
        elif self.label1.text() == 'button active':
            self.label2.setText('looping')
        # print('input2=1')

    def update_label_reset(self):
        self.label1.setText('input1=1')
        self.label2.setText('input2=1')
        # print('reset')


class PrgAndGui(NodeGUI):
    main_widget_class = PrgAndWidget
    main_widget_pos = 'between ports'
    color = '#99dd55'

    def __init__(self, params):
        super().__init__(params)
        pass

    # def update_label(self, text):
    #     print('gui',text)
    #     if self.main_widget_class:
    #         self.main_widget_class.update_label(self,text)


class PrgOrGui(NodeGUI):
    main_widget_class = PrgOrWidget
    main_widget_pos = 'between ports'
    color = '#99dd55'

    def __init__(self, params):
        super().__init__(params)
        pass


class PrgSwitchGui(NodeGUI):
    main_widget_class = PrgSwitchWidget
    main_widget_pos = 'between ports'
    color = '#99dd55'

    def __init__(self, params):
        super().__init__(params)
        pass


export_guis([
    PrgAndGui,
    PrgOrGui,
    PrgSwitchGui
])

if __name__ == "__main__":
    test = PrgSwitchWidget
    print(test)
