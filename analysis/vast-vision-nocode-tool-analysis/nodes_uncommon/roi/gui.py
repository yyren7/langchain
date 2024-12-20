from ryven.gui_env import *

from qtpy.QtWidgets import QPushButton, QFileDialog, QLineEdit
from media_plugins.media_controller import media_controller
import os
import sys

sys.path.append(os.path.dirname(__file__))
import platform
from vastlib.utils import get_img_from_fs

import numpy as np
from roi_rectangle_dialog import BasicROIRectangleDialog
from roi_circle_dialog import BasicROICircleDialog
from roi_ellipse_dialog import BasicROIEllipseDialog
from roi_polygon_dialog import BasicROIPolygonDialog



# 画像を表示するウィジェット
class BasicRoiRectangleWidget(NodeInputWidget, QPushButton):
    def __init__(self, params):
        NodeInputWidget.__init__(self, params)
        QPushButton.__init__(self)
        self.dlg = BasicROIRectangleDialog()
        self.media_controller = media_controller()
        self.clicked.connect(lambda: self.show_dialog())

    def show_dialog(self):
        self.update_node()
        self.dlg.exec_()
        # ノードに値をセット
        self.update_node_input(Data(self.dlg.get_roi()), silent=False)
        self.update_node()


    # ポートの値が更新された際画像であれば
    def img_update_event(self, val: Data):
        try:
            # 値を取得（画像のパス）
            path = val.payload

            if os.environ["VAST_SERVER"] != "127.0.0.1":
                # ファイル名でsambaサーバを検索
                res = get_img_from_fs(path=path, ip_address=os.environ["VAST_SERVER"])
            else:
                res = self.media_controller.read(path, np.ndarray)

            # ViewBoxに画像をセット
            self.set_image(res)
        except:
            pass

    def set_image(self, img):
        try:
            self.dlg.set_image(img)
        except Exception as e:
            print("gui.py set_image:", e)

    def set_roi(self, roi):
        try:
            self.dlg.set_roi(roi)
        except Exception as e:
            print("gui.py set_roi", e)


class BasicRoiCircleWidget(NodeInputWidget, QPushButton):
    def __init__(self, params):
        NodeInputWidget.__init__(self, params)
        QPushButton.__init__(self)

        # layout = QVBoxLayout(self)
        self.media_controller = media_controller()
        self.dlg = BasicROICircleDialog()
        self.clicked.connect(lambda: self.show_dialog())

    def show_dialog(self):
        self.update_node() # 前回値適用
        self.dlg.exec_()
        self.update_node_input(Data(self.dlg.get_roi()), silent=False)
        self.update_node()

    # ポートの値が更新された際に発火するイベント
    def img_update_event(self, val: Data):
        try:
            # 値を取得（画像のパス）
            path = val.payload

            if os.environ["VAST_SERVER"] != "127.0.0.1":
                # ファイル名でsambaサーバを検索
                res = get_img_from_fs(path=path, ip_address=os.environ["VAST_SERVER"])
            else:
                res = self.media_controller.read(path, np.ndarray)

            # ViewBoxに画像をセット
            self.set_image(res)
        except:
            pass

    def set_image(self, img):
        try:
            self.dlg.set_image(img)
        except Exception as e:
            print("gui.py set_image:", e)

    def set_roi(self, roi):
        try:
            self.dlg.set_roi(roi)
        except Exception as e:
            print("gui.py set_roi", e)


class BasicRoiEllipseWidget(NodeInputWidget, QPushButton):
    def __init__(self, params):
        NodeInputWidget.__init__(self, params)
        QPushButton.__init__(self)

        # layout = QVBoxLayout(self)
        self.media_controller = media_controller()
        self.dlg = BasicROIEllipseDialog()
        self.clicked.connect(lambda: self.show_dialog())

    def show_dialog(self):
        self.update_node() # 前回値適用
        self.dlg.exec_()
        self.update_node_input(Data(self.dlg.get_roi()), silent=False)
        self.update_node()

    # ポートの値が更新された際に発火するイベント
    def img_update_event(self, val: Data):
        try:
            # 値を取得（画像のパス）
            path = val.payload

            if os.environ["VAST_SERVER"] != "127.0.0.1":
                # ファイル名でsambaサーバを検索
                res = get_img_from_fs(path=path, ip_address=os.environ["VAST_SERVER"])
            else:
                res = self.media_controller.read(path, np.ndarray)

            # ViewBoxに画像をセット
            self.set_image(res)
        except:
            pass

    def set_image(self, img):
        try:
            self.dlg.set_image(img)
        except Exception as e:
            print("gui.py set_image:", e)

    def set_roi(self, roi):
        try:
            self.dlg.set_roi(roi)
        except Exception as e:
            print("gui.py set_roi", e)


class BasicRoiPolygonWidget(NodeInputWidget, QPushButton):
    def __init__(self, params):
        NodeInputWidget.__init__(self, params)
        QPushButton.__init__(self)

        # layout = QVBoxLayout(self)
        self.media_controller = media_controller()
        self.dlg = BasicROIPolygonDialog()
        self.clicked.connect(lambda: self.show_dialog())

    def show_dialog(self):
        self.update_node() # 前回値適用
        self.dlg.exec_()
        self.update_node_input(Data(self.dlg.get_roi()), silent=False)
        self.update_node()

    # ポートの値が更新された際に発火するイベント
    def img_update_event(self, val: Data):
        try:
            # 値を取得（画像のパス）
            path = val.payload

            if os.environ["VAST_SERVER"] != "127.0.0.1":
                # ファイル名でsambaサーバを検索
                res = get_img_from_fs(path=path, ip_address=os.environ["VAST_SERVER"])
            else:
                res = self.media_controller.read(path, np.ndarray)

            # ViewBoxに画像をセット
            self.set_image(res)
        except:
            pass

    def set_image(self, img):
        try:
            self.dlg.set_image(img)
        except Exception as e:
            print("gui.py set_image:", e)

    def set_roi(self, roi):
        try:
            self.dlg.set_roi(roi)
        except Exception as e:
            print("gui.py set_roi", e)


class ButtonTriggerWidget(NodeMainWidget, QPushButton):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QPushButton.__init__(self)

        self.clicked.connect(self.update_node)

import paramiko
class FileSelectWidget(NodeMainWidget, QPushButton):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QPushButton.__init__(self)

        self.file_dialog = QFileDialog()
        self.clicked.connect(self.update_node)

        if platform.system() == "Windows":
            self.file_dialog.setDirectory(os.getcwd())
        else:
            self.file_dialog.setDirectory("/media/usb")

    def dialog_exec(self):
        path = [""]
        if self.file_dialog.exec_():
            path = self.file_dialog.selectedFiles()
            self.file_dialog.setDirectory(os.path.dirname(path[0]))

        try:
            if platform.system() == "Windows" and os.environ["VAST_SERVER"] != "127.0.0.1":
                file_name = Path(path[0]).name
                res = sftp_file_transfer(os.environ["VAST_SERVER"], "vast", "ncpt-vast", path[0], [f"/media/usb/files/{file_name}", f"/tmp/files/{file_name}"],
                                         logger=None)
                path = [f"/tmp/files/{file_name}"]
        except Exception as e:
            print(e)

        return path[0]

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
            self.update_node_input(Data(self.text()), silent=False)
        except:
            pass

# ROI setter


class BasicROIRectangleNodeGui(NodeGUI):
    input_widget_classes = {
        'in': BasicRoiRectangleWidget,
    }
    color = '#99dd55'
    roi_node = None

    def __init__(self, params):
        super().__init__(params)
        for i, inp in enumerate(self.node.inputs):
            if inp.label_str == 'roi':
                self.roi_node = inp
                self.input_widgets[inp] = {'name': 'in', 'pos': 'besides'}



class BasicROICircleNodeGui(NodeGUI):
    input_widget_classes = {
        'in': BasicRoiCircleWidget,
    }
    color = '#99dd55'

    def __init__(self, params):
        super().__init__(params)
        for i, inp in enumerate(self.node.inputs):
            if inp.label_str == 'roi':
                self.roi_node = inp
                self.input_widgets[inp] = {'name': 'in', 'pos': 'besides'}


class BasicROIEllipseNodeGui(NodeGUI):
    input_widget_classes = {
        'in': BasicRoiEllipseWidget,
    }
    color = '#99dd55'

    def __init__(self, params):
        super().__init__(params)
        for i, inp in enumerate(self.node.inputs):
            if inp.label_str == 'roi':
                self.roi_node = inp
                self.input_widgets[inp] = {'name': 'in', 'pos': 'besides'}


class BasicROIPolygonNodeGui(NodeGUI):
    input_widget_classes = {
        'in': BasicRoiPolygonWidget,
    }
    color = '#99dd55'

    def __init__(self, params):
        super().__init__(params)
        for i, inp in enumerate(self.node.inputs):
            if inp.label_str == 'roi':
                self.roi_node = inp
                self.input_widgets[inp] = {'name': 'in', 'pos': 'besides'}


class ButtonTrrigerGui(NodeGUI):
    input_widget_classes = {
        'in': inp_widgets.Builder.str_line_edit(size='m', resizing=True),
    }
    main_widget_class = ButtonTriggerWidget
    main_widget_pos = 'between ports'
    color = '#99dd55'

    def __init__(self, params):
        super().__init__(params)
        for inp in self.node.inputs:
            self.input_widgets[inp] = {'name': 'in', 'pos': 'below'}


class FileSelectGui(NodeGUI):
    input_widget_classes = {
        'in': BasicInputWidget
    }
    main_widget_class = FileSelectWidget
    main_widget_pos = 'between ports'
    color = '#99dd55'

    def __init__(self, params):
        super().__init__(params)
        for inp in self.node.inputs:
            self.input_widgets[inp] = {'name': 'in', 'pos': 'below'}

    def get_path(self):
        return self.main_widget().dialog_exec()


class BasicInputGui(NodeGUI):
    input_widget_classes = {
        'in': BasicInputWidget
    }
    color = '#99dd55'

    def __init__(self, params):
        super().__init__(params)
        for inp in self.node.inputs:
            self.input_widgets[inp] = {'name': 'in', 'pos': 'beside'}

    def transfar_image(self, path):
        if platform.system() == "Windows" and os.environ["VAST_SERVER"] != "127.0.0.1":
            file_name = Path(path).name
            res = sftp_file_transfer(os.environ["VAST_SERVER"], "vast", "ncpt-vast", path[0],
                                     [f"/media/usb/files/{file_name}", f"/tmp/files/{file_name}"],
                                     logger=None)
            path = [f"/tmp/files/{file_name}"]

from pathlib import Path
def sftp_file_transfer(host_ip, username, password, local_file_path, remote_file_paths, logger=None):
    try:
        # SSHクライアントを作成
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # ホストに接続
        ssh.connect(hostname=host_ip, username=username, password=password, timeout=5)

        # SFTPクライアントを作成
        sftp = ssh.open_sftp()

        # リモートディレクトリが存在しない場合は作成する
        remote_dirs = []
        for file_path in remote_file_paths:
            remote_dirs.append(os.path.dirname(file_path))
        for remote_dir in remote_dirs:
            create_remote_directory(sftp, ssh, remote_dir)

        # ファイルサイズを取得
        file_size = os.path.getsize(local_file_path)

        # 進捗表示用の関数
        def progress_callback(transferred, total):
            if logger is not None:
                logger.info(f"転送中... {transferred}/{total} bytes ({transferred / total * 100:.2f}%)")
            else:
                print(f"転送中... {transferred}/{total} bytes ({transferred / total * 100:.2f}%)")

        # ファイルをアップロード
        # MEMO: USBメモリに直接置こうとするとpermission deniedになるのでデスクトップに置いてからmv
        for file_path in remote_file_paths:
            desktop_path = "/home/vast/Desktop/" + Path(file_path).name
            sftp.put(local_file_path, desktop_path, callback=progress_callback, confirm=True)
            ssh.exec_command(f'sudo mv {desktop_path} {file_path}')
        ssh.exec_command(f'sudo rm {desktop_path}')

        return (f"ファイル '{local_file_path}' をアップロードしました")

    except paramiko.AuthenticationException:
        return "認証エラー: ユーザー名またはパスワードが正しくありません"
    except paramiko.SSHException as sshException:
        return f"SSH接続エラー: {sshException}"
    except Exception as ex:
        return f"ファイル転送中にエラーが発生しました: {ex}"
    finally:
        # 接続を閉じる
        ssh.close()

def create_remote_directory(sftp, ssh, remote_dir_path):
    try:
        # ディレクトリが存在するかチェック
        sftp.stat(remote_dir_path)
    except IOError:
        # ディレクトリが存在しない場合は作成する
        parent_dir = os.path.dirname(remote_dir_path.rstrip('/'))
        if parent_dir:
            create_remote_directory(sftp, ssh, parent_dir)
        # sftp.mkdir(remote_dir_path)
        ssh.exec_command(f'sudo mkdir {remote_dir_path}')

export_guis([
    BasicROIRectangleNodeGui,
    BasicROIEllipseNodeGui,
    BasicROICircleNodeGui,
    BasicROIPolygonNodeGui,
    ButtonTrrigerGui,
    FileSelectGui,
    BasicInputGui
])
