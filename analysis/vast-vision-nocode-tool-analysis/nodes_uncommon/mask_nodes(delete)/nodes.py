from ryven.node_env import *
import sys
import os
import numpy as np
from datetime import datetime
from cv_shapes_lib import CvShape
import re

sys.path.append(os.path.dirname(__file__))

script_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(os.path.dirname(script_path))
sys.path.insert(0, parent_dir)

from media_plugins.media_controller import media_controller

from nodes_uncommon.mask_nodes.mask_function import make_mask_img


import platform
if platform.system() != "Windows":
    server_path = "/opt/.VAST/file_server/"
else:
    server_path = "C:/file_server/"

guis = import_guis(__file__)


class NodeBase(Node):
    version = "v0.1"

    def have_gui(self):
        return hasattr(self, 'gui')


class Pre_Create_Mask_Node(NodeBase):
    title = 'ROI_CreateMask'
    init_inputs = [
        NodeInputType(type_="exec"),
        NodeInputType("img", type_="data"),
        NodeInputType("canvas", type_="data"),
        NodeInputType("inverse", type_="data"),
        NodeInputType("shape", type_="data"),
    ]
    init_outputs = [
        NodeOutputType(type_="exec"),
        NodeOutputType("mask")
    ]
    GUI = guis.CreateMaskGui

    def __init__(self, params):
        super().__init__(params)
        self.media_controller = media_controller()
        # self.shape = [Rectangle(x1=50, y1=50, x2=150, y2=150)] # debug用

    def update_event(self, inp=-1):
        # exec flow以外は無視
        if inp == 0:
            # 実行中表記
            try:
                # ヘッドレスモードではguiにアクセスできないのでtry-except
                self.gui.set_display_title(self.title + "<<<")
            except:
                pass

            try:
                inputs = self.get_processed_inputs()
                _mask = self.create_mask(*inputs)

                if _mask is not None:
                    self.save_and_output_data(_mask)
                try:
                    self.gui.set_display_title(self.title)
                except:
                    pass

                # フローをexec
                self.exec_output(0)

            except Exception as e:
                # TODO:ヘッドレスモードでエラー箇所をロガーに流せるように仕様を考える
                try:
                    self.gui.set_display_title(self.title + "(err)")
                except:
                    pass
                print(f"Error : {e}")

    # 汎用入力
    def get_processed_inputs(self):
        """入力を処理してリストを返す"""
        inputs = []
        for i in range(1, len(self.init_inputs)):  # input(0)はexec
            try:
                input_payload = self.input(i).payload
                inputs.append(input_payload)
            except AttributeError:
                print(f"Warning: input({i}) is None")
                inputs.append(None)
        processed_inputs = []

        pattern = r'^(?:[a-zA-Z]:[\\/])?(?:[\w-]+[\\/])*[\w-]+\.\w+$'
        for input_ in inputs:
            if input_ is None:
                processed_inputs.append(None)
            elif bool(re.match(pattern, input_)):
                processed_input = self.media_controller.read(input_, require_obj=np.ndarray)
                processed_inputs.append(processed_input)
            elif isinstance(input_, str):
                processed_input = self.media_controller.read(input_, require_obj=CvShape)
                processed_inputs.append(processed_input)
            else:
                processed_inputs.append(input_)

        return processed_inputs

    def create_mask(self, img, canvas, inverse, shape):
        """マスク画像を作成"""
        return make_mask_img(img=img, canvas=canvas, inverse=inverse, shape=shape)
        # return make_mask_img(img=img, canvas=canvas, inverse=inverse, shape=self.shape)

    def save_and_output_data(self, data):
        """マスクを保存し、出力に設定"""
        formatted_date = datetime.now().strftime('%Y%m%d_%H%M%S%f')
        path = f"{server_path}{self.__class__.__name__}_{formatted_date}"
        _path = self.media_controller.write(path, data)
        self.set_output_val(1, Data(_path))
        self.exec_output(0)


export_nodes([
    Pre_Create_Mask_Node,
])
