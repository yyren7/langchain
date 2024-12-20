from ryven.node_env import *
import sys
import os
import json
from copy import deepcopy

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
class BasicROIRectangleNode(NodeBase):
    title = 'ROI_Rectangle'
    name = 'ROI_Rectangle'

    GUI = guis.BasicROIRectangleNodeGui

    init_inputs = [
        NodeInputType(type_="exec"),
        NodeInputType("img", type_="data"),
        # save project時、保持するのに必要
        NodeInputType("roi", type_="data"),
        NodeInputType("offset", type_="data"),
    ]
    init_outputs = [
        NodeOutputType(type_="exec"),
        NodeOutputType("roi")
    ]

    def __init__(self, params):
        super().__init__(params)
        self.active = True

    def update_event(self, inp_num=-1):
        print("inpu_num", inp_num)
        try:
            # 画像の更新
            if self.input(1) is not None:
                for i, inp in enumerate(self.inputs):
                    if inp.label_str == "img":
                        # debugのThreads & Variablesで探せない超荒業
                        self.gui.input_widget(2).img_update_event(self.input(i))
        except:
            pass


        # ROIの更新
        coord = None

        if self.input(2) is not None:
            try:
                roi = self.input(2).payload
                self.gui.input_widget(2).set_roi(roi[0])
            except Exception as e:
                print(e)

            try:
                # 出力の更新（値はguiの方で更新）
                coord = deepcopy(self.input(2).payload)
                if coord is not None:
                    if self.input(3) is not None:
                        # オフセット量を取得
                        if type(self.input(3).payload) == str:
                            offsets = json.loads(self.input(3).payload)
                        else:
                            offsets = self.input(3).payload
                        # オフセット適用
                        if coord[0].shape_type == "rectangle":
                            coord[0].x1 += offsets[0]
                            coord[0].x2 += offsets[0]
                            coord[0].y1 += offsets[1]
                            coord[0].y2 += offsets[1]
                        elif coord[0].shape_type == "polygon":
                            offset_points = []
                            for point in coord[0].points:
                                offset_points.append(((point[0] + offsets[0]), (point[1] + offsets[1])))
                            coord[0].points = offset_points
            except:
                pass

            if coord is not None:
                # オブジェクトを辞書型に変換してアウトプット
                roi = coord[0].model_dump()
                self.set_output_val(1, Data(json.dumps(roi)))
            else:
                self.set_output_val(1, Data(None))

            # execフローを発行
            if inp_num == 0:
                self.exec_output(0)


class BasicROICircleNode(NodeBase):
    title = 'ROI_Circle'
    name = 'ROI_Circle'

    GUI = guis.BasicROICircleNodeGui

    init_inputs = [
        NodeInputType(type_="exec"),
        NodeInputType("img", type_="data"),
        NodeInputType("roi", type_="data"),
        NodeInputType("offset", type_="data"),
    ]
    init_outputs = [
        NodeOutputType(type_="exec"),
        NodeOutputType("roi")
    ]

    def __init__(self, params):
        super().__init__(params)
        self.active = True

    def update_event(self, inp_num=-1):
        try:
            # 画像の更新
            if self.input(1) is not None:
                for i, inp in enumerate(self.inputs):
                    if inp.label_str == "img":
                        # debugのThreads & Variablesで探せない超荒業
                        self.gui.input_widget(2).img_update_event(self.input(i))
        except:
            pass

        # ROIの更新
        coord = None
        if self.input(2) is not None:
            try:
                roi = self.input(2).payload
                self.gui.input_widget(2).set_roi(roi[0])
            except Exception as e:
                print(e)
            try:
                # 出力の更新（値はguiの方で更新）
                coord = deepcopy(self.input(2).payload)
                if coord is not None:
                    if self.input(3) is not None:
                        # オフセット量を取得
                        if type(self.input(3).payload) == str:
                            offsets = json.loads(self.input(3).payload)
                        else:
                            offsets = self.input(3).payload
                        # オフセット適用
                        coord[0].x += offsets[0]
                        coord[0].y += offsets[1]
            except:
                pass

            if coord is not None:
                # オブジェクトを辞書型に変換してアウトプット
                roi = coord[0].model_dump()
                self.set_output_val(1, Data(json.dumps(roi)))
            else:
                self.set_output_val(1, Data(None))

            # execフローを発行
            if inp_num == 0:
                self.exec_output(0)


class BasicROIEllipseNode(NodeBase):
    title = 'ROI_Ellipse'
    name = 'ROI_Ellipse'

    GUI = guis.BasicROIEllipseNodeGui

    init_inputs = [
        NodeInputType(type_="exec"),
        NodeInputType("img", type_="data"),
        NodeInputType("roi", type_="data"),
        NodeInputType("offset", type_="data"),
    ]
    init_outputs = [
        NodeOutputType(type_="exec"),
        NodeOutputType("roi")
    ]

    def __init__(self, params):
        super().__init__(params)
        self.active = True

    def update_event(self, inp_num=-1):
        try:
            # 画像の更新
            if self.input(1) is not None:
                for i, inp in enumerate(self.inputs):
                    if inp.label_str == "img":
                        # debugのThreads & Variablesで探せない超荒業
                        self.gui.input_widget(2).img_update_event(self.input(i))
        except:
            pass

        # ROIの更新
        coord = None

        if self.input(2) is not None:
            try:
                roi = self.input(2).payload
                self.gui.input_widget(2).set_roi(roi[0])
            except Exception as e:
                print(e)

            try:
                # 出力の更新（値はguiの方で更新）
                coord = deepcopy(self.input(2).payload)
                if coord is not None:
                    if self.input(3) is not None:
                        # オフセット量を取得
                        if type(self.input(3).payload) == str:
                            offsets = json.loads(self.input(3).payload)
                        else:
                            offsets = self.input(3).payload
                        # オフセット適用
                        coord[0].x += offsets[0]
                        coord[0].y += offsets[1]
            except:
                pass

            if coord is not None:
                # オブジェクトを辞書型に変換してアウトプット
                roi = coord[0].model_dump()
                self.set_output_val(1, Data(json.dumps(roi)))
            else:
                self.set_output_val(1, Data(None))

            # execフローを発行
            if inp_num == 0:
                self.exec_output(0)


class BasicROIPolygonNode(NodeBase):
    title = 'ROI_Polygon'
    name = 'ROI_Polygon'

    GUI = guis.BasicROIPolygonNodeGui

    init_inputs = [
        NodeInputType(type_="exec"),
        NodeInputType("img", type_="data"),
        NodeInputType("roi", type_="data"),
        NodeInputType("offset", type_="data"),
    ]
    init_outputs = [
        NodeOutputType(type_="exec"),
        NodeOutputType("roi")
    ]

    def __init__(self, params):
        super().__init__(params)
        self.active = True

    def update_event(self, inp_num=-1):
        try:
            # 画像の更新
            if self.input(1) is not None:
                for i, inp in enumerate(self.inputs):
                    if inp.label_str == "img":
                        # debugのThreads & Variablesで探せない超荒業
                        self.gui.input_widget(2).img_update_event(self.input(i))
        except:
            pass

        # ROIの更新
        coord = None

        if self.input(2) is not None:
            try:
                roi = self.input(2).payload
                self.gui.input_widget(2).set_roi(roi[0])
            except Exception as e:
                print(e)

            try:
                # 出力の更新（値はguiの方で更新）
                coord = deepcopy(self.input(2).payload)
                if coord is not None:
                    if self.input(3) is not None:
                        # オフセット量を取得
                        if type(self.input(3).payload) == str:
                            offsets = json.loads(self.input(3).payload)
                        else:
                            offsets = self.input(3).payload
                        # オフセット適用
                        offset_points = []
                        for point in coord[0].points:
                            offset_points.append(((point[0] + offsets[0]), (point[1] + offsets[1])))
                        coord[0].points = offset_points
            except:
                pass

            if coord is not None:
                # オブジェクトを辞書型に変換してアウトプット
                roi = coord[0].model_dump()
                self.set_output_val(1, Data(json.dumps(roi)))
            else:
                self.set_output_val(1, Data(None))

            # execフローを発行
            if inp_num == 0:
                self.exec_output(0)


class Button_Node(NodeBase):
    title = 'Trg_Button'
    init_inputs = [
        NodeInputType("name", type_="data")
    ]
    init_outputs = [
        NodeOutputType(type_="exec")
    ]
    GUI = guis.ButtonTrrigerGui

    def update_event(self, inp=-1):
        if str(inp) != "0":
            self.exec_output(0)


class File_Select_Node(NodeBase):
    title = 'Utl_FileSelect'
    init_inputs = [
        NodeInputType("path", type_="data")
    ]
    init_outputs = [
        NodeOutputType(type_="exec"),
        NodeOutputType("path")
    ]
    GUI = guis.FileSelectGui

    def update_event(self, inp=-1):
        if inp == -1:
            try:
                path = self.gui.get_path()
                self.gui.input_widget(0).val_update_event(Data(path))
            except Exception as e:
                print(e)
        else:
            if self.input(0) is not None:
                self.set_output_val(1, Data(self.input(0).payload))
                self.exec_output(0)

from media_plugins.media_controller import media_controller
import numpy as np
import cv2
class Image_Save_Node(NodeBase):
    title = "Utl_SaveImage"
    init_input = [
        NodeInputType(type_="exec"),
        NodeInputType("img", type_="data"),
        NodeInputType("path", type_="data")
    ]
    init_outputs = [
        NodeOutputType("success", type_="data")
    ]
    GUI = guis.BasicInputGui

    mc = media_controller()

    def update_event(self, inp=-1):
        if inp == 0:
            try:
                img = media_controller.read(self.input(1).payload, np.ndarray)
                cv2.imwrite(self.input(2).payload, img)
                try:
                    self.GUI.transfar_image(self.input(2).payload)
                except:
                    pass
            except Exception as e:
                print(e)


export_nodes([
    BasicROIRectangleNode,
    BasicROICircleNode,
    BasicROIEllipseNode,
    BasicROIPolygonNode,
    Button_Node,
    File_Select_Node,
])
