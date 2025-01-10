from ryven.gui_env import *
from PySide2.QtWidgets import QLineEdit

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


class ActiveInputWidget(NodeInputWidget, QLineEdit):
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
        try:
            self.update_node()
        except:
            pass

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

class BasicNodeGui(NodeGUI):
    input_widget_classes = {'input': BasicInputWidget}

    def add_input(self, name):
        self.init_input_widgets[len(self.init_input_widgets)] = {'name':'input', 'pos':'below'}

    def __init__(self, params):
        super().__init__(params)

        for inp in self.node.inputs:
            self.input_widgets[inp] = {'name': 'input', 'pos': 'besides'}

class ActiveNodeGui(NodeGUI):
    input_widget_classes = {'input': ActiveInputWidget}

    def add_input(self, name):
        self.init_input_widgets[len(self.init_input_widgets)] = {'name':'input', 'pos':'below'}

    def __init__(self, params):
        super().__init__(params)

        for inp in self.node.inputs:
            self.input_widgets[inp] = {'name': 'input', 'pos': 'besides'}


export_guis([
    BasicNodeGui,
    ActiveNodeGui
])
