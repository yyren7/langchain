# ===============================================================================
# Name      : file_handler.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2024-01-25 13:30
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================
import datetime
import cv2
import numpy as np
import json
import csv
import os
import shutil
import configparser
from abc import ABCMeta
from typing import Union, Tuple, Optional, Any
import difflib
from pprint import pformat

try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)

CHANGE_LOG = 'change_log.log'  # NOTE: 変更履歴
OPERATION_HISTORY = 'operation_history.log'  # NOTE: 操作履歴
SAVE_CHANGE_LOG = False
SAVE_OPERATION_HISTORY = False


def to_string_lines(obj: Any) -> list:
    """dictのオブジェクトを文字列に変換&改行で分割したリストを返却"""
    return pformat(obj).split('\n')


def difference_check(dict1: dict, dict2: dict) -> str:
    """差分チェック"""
    lines1 = to_string_lines(dict1)
    lines2 = to_string_lines(dict2)
    result = difflib.Differ().compare(lines1, lines2)
    # print(result)
    res_str = '\n'.join(result)
    res_list = res_str.split('\n')
    res_list = [v for v in res_list if ('+' in v) or ('-' in v) or ('?' in v)]
    return '\n'.join(res_list)


class FileHandlerABC(metaclass=ABCMeta):
    def __init__(self, header: str):
        self._header = header
        # NOTE: private variable
        self._old_config_dir: str = ''
        self._old_config_list: list = []
        self._error_state: bool = False
        self._error_details: str = ''

    def _set_error_state(self, msg: str = '') -> None:
        if msg == '':
            self._error_state = False
            self._error_details = ''
        else:
            self._error_state = True
            self._error_details = msg

    @property
    def error_state(self) -> bool:
        return self._error_state

    @property
    def error_details(self) -> str:
        return self._error_details

    @property
    def old_config_dir(self) -> str:
        return self._old_config_dir

    @old_config_dir.setter
    def old_config_dir(self, modelname: str) -> None:
        self._old_config_dir = os.path.join(self._header, f'.{modelname}')
        print(f'Set old config dir:{self._old_config_dir}')
        self._old_config_list = self._get_filelist(self._old_config_dir)

    @property
    def old_config_list(self) -> list:
        self._old_config_list = self._get_filelist(self._old_config_dir)
        return self._old_config_list

    def _write_file(self,
                    path: str,
                    filetype: str,
                    data: dict,
                    mode: str = 'w',
                    allow_user: bool = False) -> None:
        """ファイルの書き込み

        Args:
            path (str): _description_
            filetype (str): json, log, csv
            data (dict): _description_
            mode (str, optional): w, a
            allow_user (bool, optional): _description_. Defaults to False.
        """
        try:
            with open(path, mode) as f:
                if filetype == 'json':
                    json.dump(data, f, indent=4)
                elif filetype == 'log':
                    f.write(data.get('message', 'nothing'))
                elif filetype == 'csv':
                    writer = csv.writer(f, lineterminator='\n')
                    # writer.writerow([data[k] for k, v in data.items()])
                    writer.writerow([v for v in data.values()])
                self._set_error_state()
        except Exception as e:
            logger.error(str(e))
            self._set_error_state(str(e))
            return

        if allow_user:
            os.chmod(path, 0o777)

    def _read_file(self, path: str, filetype: str) -> Union[dict, None]:
        """ファイルの読込

        Args:
            path (str): _description_
            filetype (str): json, log, csv

        Returns:
            Union[dict, None]: _description_
        """
        try:
            with open(path, 'r') as f:
                if filetype == 'json':
                    data = json.load(f)
                elif filetype == 'ini':
                    data = configparser.ConfigParser()
                    data.read_file(f)
                self._set_error_state()
                return data

        except Exception as e:
            logger.error(str(e))
            self._set_error_state(str(e))
            return None

    def _delete_file(self, path: str) -> bool:
        try:
            os.remove(path)
            self._set_error_state()
            return True
        except Exception as e:
            logger.error(str(e))
            self._set_error_state(str(e))
            return False

    def _save_image(self, path: str, img: np.ndarray) -> None:
        ret = cv2.imwrite(path, img)
        if ret:
            return
        else:
            self.error_type = "Write image Error"
            self.message = 'path:' + path
            self.is_usb_inserted = False

    def _check_file_exist(self, path: str) -> bool:
        ret = os.path.exists(path)
        return ret

    def _get_filelist(self, path: str) -> list:
        filelist = []
        try:
            print(f'Try to get file list from:{path}')
            filelist = os.listdir(path)
        except Exception as e:
            print(e)
            filelist = []

        return filelist

    def _make_dir(self, path: str, allow_user: bool = False) -> None:
        try:
            if os.path.exists(path):
                print(f'Already exist:{path}')
            else:
                print(f'Try to make dir:{path}')
                os.makedirs(path, exist_ok=True)
        except Exception as e:
            self.error_type = "Make dir Error"
            self.message = 'path:' + path + '\n' + str(e)
        else:
            if allow_user:
                os.chmod(path, 0o777)

    def _copy_file(self, path_from: str, path_to: str) -> None:
        try:
            print('Try to copy file')
            print(f'original:{path_from}')
            print(f'copy:{path_to}')
            shutil.copyfile(path_from, path_to)
        except Exception as e:
            self.error_type = "Copy Error"
            self.message = f'path from:{path_from}\npath to:{path_to}\n' + str(e)
            self.is_usb_inserted = False
        else:
            os.chmod(path_to, 0o777)

    def _copy_folder(self, path_from: str, path_to: str) -> None:
        try:
            shutil.copytree(path_from, path_to)
        except Exception as e:
            self.error_type = "Copy Error"
            self.message = f'path from:{path_from}\npath to:{path_to}\n' + str(e)
            print(self.message)
            self.is_usb_inserted = False
        else:
            os.chmod(path_to, 0o777)

    def _save_change_log(self, time: str, diff: str) -> None:
        if SAVE_CHANGE_LOG:
            data = dict(message=f'{time}\n{diff}\n')
            path = os.path.join(self._header, CHANGE_LOG)
            self._write_file(path, 'log', data, 'a', True)

    def _create_datetime_str(self) -> Tuple[str, str, str, str]:
        # NOTE: 日付データを一括生成
        now = datetime.datetime.now()
        year = now.strftime('%Y')
        month = now.strftime('%Y_%m')
        day = now.strftime('%Y_%m_%d')
        time = now.strftime('%Y_%m_%d_%H_%M_%S')
        return year, month, day, time

    def _get_current_time(self) -> str:
        now = datetime.datetime.now()
        return now.strftime('%Y-%m-%d-%H-%M-%S-%f')[:-3]


class FileHandler(FileHandlerABC):

    def __init__(self, header: str):
        super().__init__(header=header)

    def set_header(self, header: str) -> None:
        self._header = header

    def log_message(self, modelname: str, mode: str, path: str, stat: str = '') -> str:
        _, _, _, current_time = self._create_datetime_str()
        return f'{current_time}, {modelname}, {mode}, {path}, {stat}\n'

    def save_operation_history(self, path: str,
                               history_path: str,
                               modelname: str, operation: str,
                               msg: str = '',
                               mode: str = 'a'):
        if SAVE_OPERATION_HISTORY:
            message = self.log_message(modelname, operation, path, msg)
            self._write_file(path=history_path,
                             filetype='log',
                             mode=mode,
                             data=dict(message=message))

    def create_image_folder(self, basedir: str) -> str:
        # NOTE: directory layer '%Y/%Y-%m/%Y-%m-%d'
        _year, _month, _day, _ = self._create_datetime_str()
        dirpath = os.path.join(basedir, _year, _month, _day)
        ret = self._check_file_exist(dirpath)
        if not ret:
            self._make_dir(dirpath, allow_user=True)
        return dirpath

    def create_log_folder(self, basedir: str) -> str:
        # NOTE: directory layer '%Y/%Y-%m/'
        _year, _month, _, _ = self._create_datetime_str()
        dirpath = os.path.join(basedir, _year, _month)
        ret = self._check_file_exist(dirpath)
        if not ret:
            self._make_dir(dirpath, allow_user=True)
        return dirpath

    def create_csv_file(self, path: str, data_items: dict = {}) -> str:
        ret = self._check_file_exist(path)
        if not ret:
            self._write_file(path, 'csv', data_items)

        return path

    # def check_exist_and_copy_config(self, path_from: str, path_to: str) -> None:
    #     ret = self._check_file_exist(path_to)
    #     if not ret:
    #         self._make_dir(path_to, allow_user=True)
    #         dirname = os.path.basename(os.path.dirname(path_from))
    #         self._copy_folder(path_from, os.path.join(path_to, dirname))

    def create_new_file(self, fpath: str, data: dict) -> None:
        """ファイル生成"""
        self._write_file(path=fpath, filetype='json', data=data)

    def load_config(self, path: str, modelname: str, *,
                    key: str = "", no_log: bool = False) -> Optional[dict]:
        data = self._read_file(path=path, filetype='json')
        if no_log:
            return data

        history_path = os.path.join(self._header, OPERATION_HISTORY)

        if data is None:
            # NOTE: データがない時、エラー内容を記載
            self.save_operation_history(path=path,
                                        history_path=history_path,
                                        modelname=modelname,
                                        operation='load',
                                        msg=self._error_details,
                                        )
            # message = self.log_message(modelname, 'load', path, self._error_details)
            # self._write_file(path=path,
            #                  filetype='log',
            #                  mode='a',
            #                  data=dict(message=message))
        else:
            # NOTE: データがあるけどkeyがない時
            if key != "":
                data = data.get('key', None)
                if data is None:
                    self.save_operation_history(path=path,
                                                history_path=history_path,
                                                modelname=modelname,
                                                operation='load',
                                                msg='no keyword')
                    # message = self.log_message(modelname, 'load', path, 'no keyword')
                    # self._write_file(path=path,
                    #                  filetype='log',
                    #                  mode='a',
                    #                  data=dict(message=message))
                    return None

            self.save_operation_history(path=path,
                                        history_path=history_path,
                                        modelname=modelname,
                                        operation='load')
            # message = self.log_message(modelname, 'load', path)
            # self._write_file(path=path,
            #                  filetype='log',
            #                  mode='a',
            #                  data=dict(message=message))

        return data

    def save_config(self, path: str, modelname: str, new_param: dict) -> bool:
        old_param = self.load_config(path, modelname, no_log=True)
        if old_param is None:
            return False
        history_path = os.path.join(self._header, OPERATION_HISTORY)
        try:
            # NOTE: 差分があれば履歴保存
            ret = self.save_config_change_log(modelname, new_param, old_param)
            if ret:
                # NOTE: 差分があればパラメータ更新
                self._write_file(path=path, filetype='json', data=new_param)
                # NOTE: 操作履歴
                self.save_operation_history(path=path,
                                            history_path=history_path,
                                            modelname=modelname,
                                            operation='save')
                # message = self.log_message(modelname, 'save', path)
                # self._write_file(path=history_path,
                #                  filetype='log',
                #                  mode='a',
                #                  data=dict(message=message))
        except Exception as e:
            logger.error(str(e))
            # NOTE: save operation history
            self.save_operation_history(path=path,
                                        history_path=history_path,
                                        modelname=modelname,
                                        operation='save',
                                        msg=self._error_details)
            # message = self.log_message(modelname, 'save', path, self._error_details)
            # self._write_file(path=history_path,
            #                  filetype='log',
            #                  mode='a',
            #                  data=dict(message=message))
            return False

        return True

    def save_config_change_log(self,
                               modelname: str,
                               new_param: dict,
                               old_param: dict) -> bool:

        # NOTE: フォルダの有り無し確認.無ければ生成.
        self.old_config_dir = modelname
        ret = self._check_file_exist(self.old_config_dir)
        if not ret:
            self._make_dir(self.old_config_dir, allow_user=True)

        # NOTE: 差分チェック
        diff_str = difference_check(old_param, new_param)

        # NOTE: 差分があった場合(Save Setteingsの空押しに対応)
        if diff_str != '':
            _, _, _, _time = self._create_datetime_str()

            self._save_change_log(_time, diff_str)

            _old_config = os.path.join(self._old_config_dir, f'{_time}.json')

            self._write_file(path=_old_config, filetype='json', data=new_param)

            ret = self._check_file_exist(self._old_config_dir)
            if ret:
                self._old_config_list = self._get_filelist(self._old_config_dir)

            # NOTE: 過去ログ5超えたらpop
            if len(self._old_config_list) > 5:
                self._old_config_list = sorted(self._old_config_list)
                _path = os.path.join(self._old_config_dir, self._old_config_list[0])
                self._delete_file(_path)
            return True
        else:
            return False


if __name__ == '__main__':
    pass
