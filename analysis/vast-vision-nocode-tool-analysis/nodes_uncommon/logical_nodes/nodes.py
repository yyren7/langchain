from ryven.node_env import *
import sys
import os
import json
import threading
import time
from queue import Queue
from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout

sys.path.append(os.path.dirname(__file__))

script_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(os.path.dirname(script_path))
sys.path.insert(0, parent_dir)

guis = import_guis(__file__)


class NodeBase(Node):
    version = "v0.1"

    def have_gui(self):
        return hasattr(self, 'gui')


class PrgAndNode(NodeBase):
    title = 'Prg_And'
    name = 'Prg_And'
    init_inputs = [
        NodeInputType(type_="exec"),
        NodeInputType(type_="exec"),
    ]
    init_outputs = [
        NodeInputType(type_="exec")
    ]
    GUI = guis.PrgAndGui

    def __init__(self, params):
        super().__init__(params)
        self.input_1_triggered = False
        self.input_2_triggered = False
        self.active = True

    def update_event(self, input_called=-1):
        try:
            if input_called == 0:  # exec input 1 called
                self.input_1_triggered = True
                try:
                    self.gui.main_widget().update_label1()
                except:
                    pass
            elif input_called == 1:  # exec input 2 called
                self.input_2_triggered = True
                try:
                    self.gui.main_widget().update_label2()
                except:
                    pass
            if self.input_1_triggered and self.input_2_triggered:
                self.exec_output(0)  # trigger exec output
                self.input_1_triggered = False
                self.input_2_triggered = False
                try:
                    self.gui.main_widget().update_label_reset()
                except:
                    pass
            # self.input_label.setText(self.input_1_triggered)
        except Exception as e:
            print(f"Error sending message: {e}")


class PrgOrNode(NodeBase):
    title = 'Prg_Or'
    name = 'Prg_Or'
    init_inputs = [
        NodeInputType(type_="exec"),
        NodeInputType(type_="exec"),

    ]
    init_outputs = [
        NodeOutputType(type_="exec"),
    ]
    GUI = guis.PrgOrGui

    def __init__(self, params):
        super().__init__(params)
        self.input_2_triggered = False
        self.input_1_triggered = False

    def update_event(self, input_called=-1):
        print("EXEC!!")
        try:
            if input_called == 0:  # exec input 1 called
                self.exec_output(0)  # trigger exec output
                try:
                    self.gui.main_widget().update_label1()
                except:
                    pass
            elif input_called == 1:  # exec input 2 called
                self.exec_output(0)  # trigger exec output
                try:
                    self.gui.main_widget().update_label2()
                except:
                    pass
        except Exception as e:
            print(f"Error receiving message: {e}")


class PrgSwitchNode(NodeBase):
    title = 'Prg_Switch'
    name = 'Prg_Switch'
    init_inputs = [
        NodeInputType(type_="exec"),
        NodeInputType(type_="exec"),
    ]
    init_outputs = [
        NodeInputType(type_="exec")
    ]
    GUI = guis.PrgSwitchGui

    def __init__(self, params):
        super().__init__(params)
        self.input_1_triggered = False
        # self.input_2_triggered = False
        self.active = False

    def update_event(self, input_called=-1):
        try:
            if input_called == 0:  # exec input 1 called
                if self.input_1_triggered:
                    self.input_1_triggered = False
                    try:
                        self.gui.main_widget().update_label1()
                    except:
                        pass
                else:
                    self.input_1_triggered = True
                    try:
                        self.gui.main_widget().update_label1()
                    except:
                        pass
                    self.exec_output(0)
            elif input_called == 1:  # exec input 2 called
                # self.input_2_triggered = True
                try:
                    self.gui.main_widget().update_label2()
                except:
                    pass
            if self.input_1_triggered:
                self.exec_output(0)  # trigger exec output
                # self.gui.main_widget().update_label_reset()
            # self.input_label.setText(self.input_1_triggered)
        except Exception as e:
            print(f"Error sending message: {e}")

class PrgBranchNode(NodeBase):
    title = 'Prg_Branch'
    name = 'Prg_Branch'
    init_inputs = [
        NodeInputType(type_="exec"),
        NodeInputType("bool", type_="data"),
    ]
    init_outputs = [
        NodeInputType("True", type_="exec"),
        NodeInputType("False", type_="exec")
    ]

    def __init__(self, params):
        super().__init__(params)

    def update_event(self, inp=-1):
        if inp == 0:
            try:
                if self.input(1) is None:
                    # False
                    self.exec_output(1)
                else:
                    val = self.input(1).payload
                    if val == "True":
                        # True
                        self.exec_output(0)
                    elif val == "False":
                        # False
                        self.exec_output(1)
                    else:
                        if val:
                            # True
                            self.exec_output(0)
                        else:
                            # False
                            self.exec_output(1)
            except Exception as e:
                print(e)
                self.exec_output(1)


export_nodes([
    PrgAndNode,
    PrgOrNode,
    PrgSwitchNode,
    PrgBranchNode
])

if __name__ == "__main__":
    test = PrgSwitchNode
