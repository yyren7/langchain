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