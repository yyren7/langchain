import traceback
import sys
from vast_base_objects import Errors, BaseInputs
from datetime import datetime
import numpy as np
import cv2
import json
import platform
if platform.system() == "Windows":
    from smb import SMBConnection
import io
import os

# ファイルパス情報を抜いたトレースバックを取得
# Errorオブジェクトをリターン
# tracebackで直前のエラーを取得するので、try-exceptしたらすぐ呼び出すこと
def get_error(obj: BaseInputs):
    t, v, tb = sys.exc_info()
    messages = traceback.format_exception(t, v, tb)
    message = messages[1].splitlines()[1] + ": " + messages[2]

    err = Errors(
        module=obj.__class__.__name__.lower(),
        input_id=obj.id,
        date=datetime.now(),
        message=message
    )
    return err


def get_image(file_path, grayscale: bool = False):
    # if argument is array, return that.
    if isinstance(file_path, np.ndarray):
        return file_path
    # if argument is str, read array.
    try:
        if ".npy" in file_path:
            img = np.load(file_path, allow_pickle=True)
            if grayscale and len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            if grayscale:
                img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            else:
                img = cv2.imread(file_path, cv2.IMREAD_COLOR)

        return img

    except Exception as e:
        return e


def write_array(name, array, input_source):
    # if argument is array, return that.
    if isinstance(input_source, np.ndarray):
        return input_source
    # TODO: avoid hard cording
    server_path = "/opt/.VAST/file_server/"
    date = datetime.now()
    path = server_path + name + date.strftime("%Y-%m-%d_%H-%M-%S.%f") + ".npy"
    np.save(path, array)
    return path, date

def read_json(path):
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        return e

def get_image(username, password, my_name, remote_name, domain, ip_address, img_path, service_name):
    try:
        conn = SMBConnection.SMBConnection(
            username=username,
            password=password,
            my_name=my_name,
            remote_name=remote_name,
            domain=domain
        )
        # Sambaに接続
        conn.connect(ip_address, 139)

        # 画像ファイルをバイト列としてメモリ上に取得（fileオブジェクトを渡すとローカルに保存してしまう）
        with io.BytesIO() as file_obj:
            conn.retrieveFile(service_name, img_path, file_obj)
            # ndarrayにデコード
            #image_array = np.frombuffer(file_obj.getvalue(), dtype=np.uint8)
            file_obj.seek(0)
            image_array = np.load(file_obj)

        # コネクション終了
        conn.close()
        #print(image_array)

        # OpenCVで扱える形にデコード
        #image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        return image_array

    except Exception as e:
        try:
            conn.close()
        except:
            pass
        print(e)

def get_img_from_fs(path, ip_address):
    file_name = os.path.basename(path)
    res = get_image(
        username="vast",
        password="vast",
        my_name="pysmb",
        remote_name="vast",
        domain="",
        ip_address=ip_address,
        img_path=file_name,
        service_name="share"
    )
    return res


def init_main():
    pass

def init_dev():
    pass
def init_run():
    pass