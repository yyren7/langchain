
# vast-vision-nocode-tool-analysis

## nodes_common

### create_dummy.py

### content

import tempfile
import os

def create_dummy(controller):
    nodenames = controller.get_table_names()
    inputs_list = [item for item in nodenames if "inputs" in item.lower()]

    with tempfile.NamedTemporaryFile(dir=os.path.dirname(__file__), suffix=".py", delete=False) as temp_file:
        temp_file_path = temp_file.name
    # tempファイルに記述
        for i_name in inputs_list:
            source_code = f"""
class {i_name}(NodeBase):
    pass
                """
            with open(temp_file_path, 'a+') as f:
                f.write(source_code)
                f.seek(0)

    return temp_file_path

### analysis

This Python code defines a function `create_dummy` that generates a temporary Python file. It extracts table names from a controller, filters for those containing "inputs", and then creates a Python class for each matching name within the temporary file. The function returns the path to this temporary file. Essentially, it dynamically generates Python code based on input table names.


### gui.py

### content

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



### analysis

This code defines custom GUI elements for a node-based visual programming environment called Ryven. It introduces `BasicInputWidget` for simple text input and `BasicNodeGui` as a base for nodes with such inputs. It also includes `OperatorNodeBaseGui` which allows adding and removing input ports dynamically. The code sets up input widgets, manages their states, and connects them to node data. It also exports these custom GUIs for use within the Ryven environment.


### nodes.py

### content

from ryven.node_env import *
import sys
import os
sys.path.append(os.path.dirname(__file__))
import node_from_db
import create_dummy
import tempfile
import atexit

script_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(os.path.dirname(script_path))
sys.path.insert(0, parent_dir)
from database_lib import redis_lib_client
from vastlib.utils import read_json

def remove_temp(path):
    if os.path.exists(path):  # if file is existing then delete it
        os.remove(path)

# TODO: db configuration is read by config file (not hard cording)
# config = read_json("config/config.json")
# DATABASE_URL = config["db_url"]
# controller = db_lib.db_controller(DATABASE_URL)
controller = redis_lib_client.db_controller()

dummy_path = create_dummy.create_dummy(controller)
# delete dummy file when program ends
atexit.register(remove_temp, path=dummy_path)

# source code for dynamic class from metadata
with open(node_from_db.__file__, 'r') as f:
    node_from_db_code = f.read()

# dummy code for dynamic class
with open(dummy_path, 'r') as f:
    dummy_code = f.read()

# dummy file path (debug)
#path = os.path.dirname(os.path.abspath(__file__)) + "\\temp.py"

# merge dynamic class file and dummy class file
#with open(path, 'w+') as fw:
with tempfile.NamedTemporaryFile(dir=os.path.dirname(__file__), suffix=".py", delete=False) as temp_file:
    temp_file_path = temp_file.name
    with open(temp_file_path, 'a+') as fw:
        fw.write(node_from_db_code)
        fw.write(dummy_code)
        fw.seek(0)

atexit.register(remove_temp, path=temp_file_path)

file_path = os.path.dirname(temp_file_path)
sys.path.append(file_path)

# import merged file
mdl = __import__(os.path.basename(temp_file_path[:-3]), fromlist=['*'])

# export custom nodes
export_nodes([
    *mdl.get_nodes()
])



### analysis

This Python script dynamically creates and loads custom nodes for a visual programming environment (Ryven). It reads code from `node_from_db.py` and a dynamically generated dummy file, merges them into a temporary file, and imports it as a module. The script uses a Redis database client, creates a dummy file using `create_dummy.py`, and ensures temporary files are deleted upon program exit. Finally, it exports the custom nodes using `export_nodes`.


### node_from_db.py

### content

from ryven.node_env import *
import sys
import os
import time
from time import sleep
from copy import copy, deepcopy
from PySide2.QtCore import Signal, QObject, QThread
from database_lib import redis_lib_client
from functools import partial

script_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(os.path.dirname(script_path))
sys.path.insert(0, parent_dir)

guis = import_guis(__file__)
globalcount = 0
class NodeBase(Node):
    color = '#00a6ff'

class BasicNode(NodeBase):
    version = 'v0.1'
    title = 'base'
    name = 'base'
    counter = 0
    message = {}
    _FUNC = None

    INSTANCES = []
    controller = None

    def __init__(self, params):
        super().__init__(params)
        self.activate = True
        global comm
        self.comm = comm
        self.message_recv_slot = partial(self.get_message, self)
        self.connect = False

    def __start(self):
        if not self.connect:
            self.comm.recv_signal.connect(self.message_recv_slot)
            self.connect = True

    def __stop(self):
        if self.connect:
            self.comm.recv_signal.disconnect(self.message_recv_slot)
            self.connect = False

    def have_gui(self):
        return hasattr(self, 'gui')

    def get_message(self, _self, _recv_message):
        recv_message = _recv_message

        try:
            obj_name, id_num = recv_message.split(":")
        except Exception as e:
            # if message format is not correct, continue recv
            return

        if "Errors" in obj_name:
            # check error message
            ret = self.check_err(obj_name, id_num, self.message)
            # if "module" and "id" in error message are matched, stop recv
            try:
                if ret:
                    self.gui.set_display_title(self.title + "(err)")
                    self.__stop()
                    # display log on headless gui
                    if self._FUNC is not None:
                        self._FUNC(self.name[:-6], "Error")
                    return
                else:
                    return
            except:
                pass


        # check name and id
        if (obj_name[:-7] == self.name[:-6] and int(id_num) == int(self.message["id"])):
            # if name and id is correct, stop recv
            self.__stop()
            pass
        else:
            return

        # get result record
        record_dict = self.controller.get_record_client(obj_name, id_num)
        # write recode to output ports
        for i, outp in enumerate(self.outputs):
            if outp.type_ == "exec":
                continue
            self.set_output_val(i, Data(record_dict[outp.label_str]))

        # exec flow
        try:
            self.gui.set_display_title(self.title)
        except:
            pass
        # display log on headless gui
        if self._FUNC is not None:
            self._FUNC(self.name[:-6], "Done")
        self.exec_output(0)



    # main function of nodes
    def update_event(self, inp_num=-1):
        # update only for exec flow
        if inp_num == 0:
            # reset input port color
            self.reset_color()
            # check id
            self.counter = self.controller.check_key(self.title + "Inputs", self.counter)
            # create message
            message = {"id": copy(self.counter)}
            self.counter += 1
            for i, inp in enumerate(self.inputs):
                if inp.type_ == "exec":
                    continue
                try:
                    if self.input(i).payload != "None":
                        message[inp.label_str] = self.input(i).payload
                except:
                    pass

            self.message = deepcopy(message)

            self.__stop()
            self.__start()

            res = self.controller.set_record_and_notify_client(self.title + "Inputs",
                                                               message,
                                                               "input",
                                                               message["id"]
            )
            try:
                self.gui.set_display_title(self.title + "<<<")
            except:
                pass

            if self._FUNC is not None:
                self._FUNC(self.name[:-6], "start")

    def check_err(self, obj_name, id_num, send_message):
        # get result record
        try:
            record_dict = self.controller.get_record_client(obj_name, id_num)
            if record_dict["input_id"] == send_message["id"] and self.title in record_dict["module"]:
                if obj_name == "FlowErrors":
                    for name in record_dict["message"]:
                        for num, input in enumerate(self.inputs):
                            if num == 0:
                                continue
                            if name == input.label_str:
                                self.gui.input_widget(num).setStyleSheet("background-color:red;")
                return True
            else:
                return False
        except:
            return False

    def reset_color(self):
        try:
            for i in range(len(self.gui.input_widgets)):
                if i == 0:
                    continue
                self.gui.input_widget(i).setStyleSheet("background-color:black;")
        except:
            pass


# matching xxinputs and xxoutputs
def extract_nodenames(names):
    inputs_list = [item for item in names if "inputs" in item.lower()]
    results_list = [item for item in names if "outputs" in item.lower()]

    mapping = {}
    for item in inputs_list:
        prefix = item[:-6]
        matching_result = [result for result in results_list if result.startswith(prefix)]
        if matching_result:
            mapping[item] = matching_result[0]

    return mapping

def get_nodes():
    controller = redis_lib_client.db_controller()
    nodenames = controller.get_table_names()
    io_pairs = extract_nodenames(nodenames)
    _nodes = []

    # create node class
    for i, (i_name, r_name) in enumerate(io_pairs.items()):
        i_columns = controller.get_columns(i_name)
        r_columns = controller.get_columns(r_name)

        cls = type(i_name, (BasicNode,), {})

        init_record = controller.get_record_client(table_name=i_name, record_id=0)

        cls.name = i_name
        cls.title = i_name[:-6]

        node_inputs = [NodeInputType(type_='exec')]
        node_outputs = [NodeOutputType(type_='exec')]

        for i, i_column in enumerate(i_columns):
            if i_column["name"] != "id" and i_column["name"] != "date":
                if type(init_record) == dict:
                        try:
                            node_inputs.append(NodeInputType(i_column["name"], default=str(init_record[i_column["name"]])))
                        except:
                            node_inputs.append(NodeInputType(i_column["name"]))
                else:
                    node_inputs.append(NodeInputType(i_column["name"]))
        for i, r_column in enumerate(r_columns):
            if r_column["name"] != "id" and r_column["name"] != "date":
                node_outputs.append(NodeOutputType(r_column["name"]))
        cls.init_inputs = node_inputs
        cls.init_outputs = node_outputs

        cls.num_inputs = len(i_columns)
        # cls.GUI = guis.OperatorNodeBaseGui
        cls.GUI = guis.BasicNodeGui

        # TODO:this inplementation may be bad.
        cls.controller = controller

        _nodes.append(cls)

    return _nodes

class Communicate(QObject):
    # カスタムシグナルの定義
    recv_signal = Signal(str)
    def __init__(self, controller):
        super().__init__()
        self.thread = listen_thread(controller)
        self.thread.message_signal.connect(lambda v: self._notification(v))

    def _start(self):
        self.thread.running = True
        self.thread.start()
        while not self.thread.isRunning():
            time.sleep(0.001)

    def _stop(self):
        self.thread.stop()
        self.thread.wait()

    def _notification(self, message):
        self.recv_signal.emit(message)

    def __del__(self):
        self._stop()

class listen_thread(QThread):
    message_signal = Signal(str)
    def __init__(self, controller):
        super().__init__()
        self.running = True
        self.controller = controller

    def run(self):
        while self.running:
            try:
                sleep(0.001)
                recv_message = self.controller._listen_message(channels=["output", "error"],
                                                              timeout=0
                                                              )
                if recv_message is not None:
                    self.message_signal.emit(recv_message)
                    continue
                else:
                    continue
            except:
                continue

        return

    def set_controller(self, controller):
        self.controller = controller

    def stop(self):
        self.running = False

controller = redis_lib_client.db_controller()
comm = Communicate(controller)
comm._start()

### analysis

This code defines a system for creating and managing nodes that interact with a Redis database. It includes classes for basic nodes, communication, and a listener thread. Nodes are dynamically generated based on database table names, with inputs and outputs corresponding to table columns. The system uses signals and slots for inter-node communication and updates node states based on database changes. It also handles error messages and provides a basic GUI for node interaction. The code establishes a connection to a Redis database and sets up a communication system for nodes to interact with it.


## nodes_common\calculation_nodes
