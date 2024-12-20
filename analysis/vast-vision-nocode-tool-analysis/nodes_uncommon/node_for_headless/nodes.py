from ryven.node_env import *
import sys
import os
guis = import_guis(__file__)

class NodeBase(Node):
    version = "v0.1"

    def have_gui(self):
        return hasattr(self, 'gui')

class Value_Node(NodeBase):
    title = 'Disp_ShowValue'
    init_inputs = [
        NodeInputType("name", type_="data"),
        NodeInputType("val", type_="data")
    ]
    GUI = guis.BasicNodeGui
    _FUNC = None

    def __init__(self, params):
        super().__init__(params)
        self.active = True

    def update_event(self, inp=-1):
        if self._FUNC is not None:
            self._FUNC(self)

class Judge_Node(NodeBase):
    title = 'Disp_Judge'
    init_inputs = [
        NodeInputType("name", type_="data"),
        NodeInputType("val", type_="data")
    ]
    GUI = guis.BasicNodeGui
    _FUNC = None

    def update_event(self, inp=-1):
        if self._FUNC is not None:
            self._FUNC(self)

class Adjust_Node(NodeBase):
    title = 'Disp_Adjust'
    init_inputs = [
        NodeInputType("name", type_="data"),
        NodeInputType("val", type_="data")
    ]
    init_outputs = [
        NodeOutputType("val", type_="data")
    ]
    GUI = guis.BasicNodeGui
    _FUNC = None

    def update_event(self, inp=-1):
        if inp == 1:
            try:
                self.set_output_val(0, Data(self.input(1).payload))
            except:
                self.set_output_val(0, Data(None))

    def update_value(self, val):
        self.input(1).set_data(Data(val))
        self.set_output_val(0, Data(val))

# export custom nodes
export_nodes([
    Value_Node,
    Judge_Node,
    Adjust_Node
])

