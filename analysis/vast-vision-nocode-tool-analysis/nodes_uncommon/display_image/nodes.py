from ryven.node_env import *
import sys
import os

sys.path.append(os.path.dirname(__file__))

script_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(os.path.dirname(script_path))
sys.path.insert(0, parent_dir)

guis = import_guis(__file__)

class NodeBase(Node):
    version = "v0.1"

    def have_gui(self):
        return hasattr(self, 'gui')


# QGraphicsLayoutView(pyqtgraph)で画像を確認するノード
class BasicViewNode(NodeBase):
    title = 'Disp_DisplayImage'

    init_inputs = [
        NodeInputType(type_='data'),
        NodeInputType("name", type_='data')
    ]
    init_outputs = []

    GUI = guis.BasicViewNodeGui
    _FUNC = None # 外部ファンクションの受け皿

    def __init__(self, params):
        super().__init__(params)
        self.active = True

    def update_event(self, inp_num=-1):
        # gui.pyで更新処理が行われる
        if self._FUNC is not None:
            self._FUNC(self)


export_nodes([
    BasicViewNode,
])
