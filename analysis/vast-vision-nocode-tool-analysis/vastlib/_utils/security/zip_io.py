# ===============================================================================
# Name      : zip_io.py
# Version   : 1.0.0
# Brief     : 設定ファイルやプログラムのZIP化
# Time-stamp: 2023-07-13 09:22
# Copyirght 2023 Hiroya Aoyama
# ===============================================================================
import os
import subprocess
import zipfile
import traceback
from pathlib import Path
from queue import Queue


def get_traceback_info() -> str:
    """エラートレース"""
    traceback_info = traceback.format_exc()
    return traceback_info


def _remove_last_path_element(path: str) -> str:
    """
    input : /aaa/bbb/ccc/ \n
    output: /aaa/bbb
    """
    path_obj = Path(path)
    return str(path_obj.parent)


def _get_last_path_element(path: str) -> str:
    """
    input : /aaa/bbb/ccc/ \n
    output: ccc/
    """
    path_obj = Path(path)
    return str(path_obj.name) + os.sep


def _zip_proc_on_linux(in_path: str, out_path: str, pwd: str) -> bool:
    """Linux用PW付きZIP生成(AES256) \n
    [/aaa/bbb/ccc/]の[ccc/]を[/ddd/eee.zip]として出力 \n
    Args:
        in_path (str): 圧縮したいフォルダのパス(/aaa/bbb/ccc)
        out_path (str): zipファイルの出力先(/ddd/eee.zip)
        pwd (str): ZIPに適用するパスワード

    Returns:
        bool: _description_
    """
    dist_dir = _remove_last_path_element(in_path)  # NOTE: /aaa/bbb/
    rel_dir = _get_last_path_element(in_path)  # NOTE: ccc/
    # NOTE ZIP CRYPTO
    # cmd = f'cd {dist_dir} && zip -e -r -P {pwd} {out_path} {rel_dir}'
    # NOTE: AES256
    cmd = f'cd {dist_dir} && 7za a -tzip -p{pwd} -mem=AES256 {out_path} {rel_dir}'
    subprocess.run(cmd, shell=True)
    return True


def _unzip_proc_on_linux(in_path: str, out_path: str, pwd: str) -> bool:
    """Linux用PW付きZIP解凍(AES256) \n
    [/aaa/bbb/ccc.zip]の[ddd/]を[/eee/ddd/]として出力 \n

    Args:
        in_path (str): 解凍したいフォルダのパス(/aaa/bbb/ccc.zip)
        out_path (str): zipファイルの出力先(/eee/)
        pwd (str): ZIPに適用されたパスワード

    Returns:
        bool: _description_
    """
    # cmd = f'unzip -P {pwd} -d {out_path} {in_path}'
    cmd = f'7za x -p{pwd} -mem=AES256 -o{out_path} {in_path}'
    subprocess.run(cmd, shell=True)
    return True


def _zip_proc_on_windows(in_path: str, out_path: str, pwd: str) -> bool:
    """Windows用PW付きZIP生成(AES256) \n
    [/aaa/bbb/ccc/]の[ccc/]を[/ddd/eee.zip]として出力 \n
    Args:
        in_path (str): 圧縮したいフォルダのパス(/aaa/bbb/ccc)
        out_path (str): zipファイルの出力先(/ddd/eee.zip)
        pwd (str): ZIPに適用するパスワード

    Returns:
        bool: _description_
    """
    try:
        import pyzipper
        in_path_ = Path(in_path)
        with pyzipper.AESZipFile(out_path, 'w',
                                 encryption=pyzipper.WZ_AES) as zf:

            zf.setpassword(pwd.encode())
            for file_path in in_path_.glob("**/*"):
                if file_path.is_file():
                    arcname_ = in_path_.name + os.sep + str(file_path.relative_to(in_path_))
                    zf.write(file_path, arcname=arcname_,
                             compress_type=pyzipper.ZIP_DEFLATED)
        return True
    except Exception:
        print(get_traceback_info())
        return False


def _unzip_proc_on_windows(in_path: str, out_path: str, pwd: str):
    """Windows用PW付きZIP解凍(AES256) \n
    [/aaa/bbb/ccc.zip]の[ddd/]を[/eee/ddd/]として出力 \n

    Args:
        in_path (str): 解凍したいフォルダのパス(/aaa/bbb/ccc.zip)
        out_path (str): zipファイルの出力先(/eee/)
        pwd (str): ZIPに適用されたパスワード

    Returns:
        bool: _description_
    """
    try:
        import pyzipper
        with pyzipper.AESZipFile(in_path) as zf:
            zf.setpassword(pwd.encode())
            zf.extractall(out_path)

        return True
    except Exception:
        print(get_traceback_info())
        return False


def zip_folder(in_path: str, out_path: str, queue: Queue) -> None:
    """フォルダのZIP化

    Args:
        in_path (str): 圧縮したいフォルダのパス(/aaa/bbb/ccc)
        out_path (str): zipファイルの出力先(/ddd/eee.zip)
        queue (Queue): 並列処理結果を返すためのキュー

    Examples:
        res_queue: Queue = Queue()
        thread = threading.Thread(target=zio.zip_folder, args=(in_path, out_path, res_queue))
        thread.start()
        display_progress_bar(thread)
        ret = res_queue.get()
    """
    pwd = 'nidecncpt0723'
    if os.path.exists(out_path):
        # NOTE: 削除
        os.remove(out_path)

    if os.name == 'nt':
        ret = _zip_proc_on_windows(in_path, out_path, pwd)
    else:
        ret = _zip_proc_on_linux(in_path, out_path, pwd)
    queue.put(ret)


def unzip_folder(in_path: str, out_path: str, queue: Queue) -> None:
    """ZIPの解凍

    Args:
        in_path (str): 解凍したいフォルダのパス(/aaa/bbb/ccc.zip)
        out_path (str): zipファイルの出力先(/eee/)
        queue (Queue): 並列処理結果を返すためのキュー

    Examples:
        res_queue: Queue = Queue()
        thread = threading.Thread(target=zio.unzip_folder, args=(in_path, out_path, res_queue))
        thread.start()
        display_progress_bar(thread)
        ret = res_queue.get()
    """
    pwd = 'nidecncpt0723'
    if os.name == 'nt':
        ret = _unzip_proc_on_windows(in_path, out_path, pwd)
    else:
        ret = _unzip_proc_on_linux(in_path, out_path, pwd)
    queue.put(ret)


def is_zip_password_protected(zip_path: str) -> bool:
    """ZIPにパスワードが適用されているかチェック

    Args:
        zip_path (str): _description_

    Returns:
        bool: _description_
    """
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        try:
            zip_file.testzip()
            return False
        except RuntimeError:
            return True
