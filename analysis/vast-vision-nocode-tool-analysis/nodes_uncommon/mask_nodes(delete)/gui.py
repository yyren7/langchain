from ryven.gui_env import *

from qtpy.QtWidgets import QPushButton, QFrame, QVBoxLayout, QFileDialog, QLabel
import pyqtgraph as pg

import os
import sys

sys.path.append(os.path.dirname(__file__))
import numpy as np


class CreateMaskWidget(NodeMainWidget, QLabel):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QLabel.__init__(self)


class CreateMaskGui(NodeGUI):
    main_widget_class = CreateMaskWidget
    main_widget_pos = 'between ports'
    color = '#99dd55'


export_guis([
    CreateMaskGui,
])
