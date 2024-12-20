import re
from ryven.gui_env import *
#from special_nodes import *

from qtpy.QtGui import QFont
from qtpy.QtCore import Qt, Signal, QEvent
from qtpy.QtWidgets import QPushButton, QComboBox, QSlider, QTextEdit, QPlainTextEdit, QWidget, QVBoxLayout, QLineEdit, \
    QDialog, QMessageBox

# QLineEditのシンプルな入力GUI
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
"""
    generic base classes
"""

# 入力部にQLineEditが付いたGUI
class BasicNodeGui(NodeGUI):
    input_widget_classes = {'input': BasicInputWidget}

    def add_input(self, name):
        self.init_input_widgets[len(self.init_input_widgets)] = {'name':'input', 'pos':'below'}

    def __init__(self, params):
        super().__init__(params)

        for inp in self.node.inputs:
            self.input_widgets[inp] = {'name': 'input', 'pos': 'besides'}


"""
    operator nodes
"""
## 以下はryvenにもともと載っていたサンプルコード（参考）
class GuiBase(NodeGUI):
    pass

class OperatorNodeBaseGui(GuiBase):
    input_widget_classes = {
        'in': inp_widgets.Builder.evaled_line_edit(size='s', resizing=True),
    }
    # init_input_widgets = {
    #     0: {'name': 'in', 'pos': 'besides'},
    #     1: {'name': 'in', 'pos': 'besides'},
    # }
    style = 'small'

    def __init__(self, params):
        super().__init__(params)
        self.actions['add input'] = {'method': self.add_operand_input}
        self.actions['remove input'] = {}

        for inp in self.node.inputs:
            self.input_widgets[inp] = {'name': 'in', 'pos': 'besides'}

    def initialized(self):
        super().initialized()
        self.rebuild_remove_actions()

    def add_operand_input(self):
        self.register_new_operand_input(self.node.num_inputs + 1)
        self.node.add_op_input()

    def register_new_operand_input(self, index):
        self.actions[f'remove input'][f'{index}'] = {
            'method': self.remove_operand_input,
            'data': index
        }

    def remove_operand_input(self, index):
        self.node.remove_op_input(index)
        self.rebuild_remove_actions()

    def rebuild_remove_actions(self):
        try:
            self.actions['remove input'] = {}
            for i in range(self.node.num_inputs):
                self.actions[f'remove input'][f'{i}'] = \
                    {'method': self.remove_operand_input, 'data': i}
        except Exception as e:
            print(e)



export_guis([
    # DualNodeBaseGui,
    #
    # CheckpointNodeGui,
    # OperatorNodeBaseGui,
    BasicNodeGui
    # LogicNodeBaseGui,
    # ArithNodeBaseGui,
    # CompNodeBaseGui,
    #
    # CSNodeBaseGui,
    # ForLoopGui,
    # ForEachLoopGui,
    #
    # SpecialNodeGuiBase,
    # ButtonNodeGui,
    # ClockNodeGui,
    # LogNodeGui,
    # SliderNodeGui,
    # DynamicPortsGui,
    # ExecNodeGui,
    # EvalNodeGui,
    # InterpreterConsoleGui,
    # StorageNodeGui,
    # LinkIN_NodeGui,
    # LinkOUT_NodeGui,
])

