import socket
import re
import io
import struct
import itertools
from pydantic import BaseModel
from typing import Pattern
from itertools import groupby
from operator import itemgetter
import platform
import polars
import datetime

from smb.SMBConnection import SMBConnection


def try_except(data: dict, key: str, *, exception=None):
    try:
        return data[key]
    except Exception:
        return exception


class Connect():
    def __init__(self, username, password, remote_name, domain):
        my_name = platform.uname().node
        print(f"SMB CONNECTION: username: {username}, password: {password}, my_name: {my_name}, remote_name: {remote_name}, domain: {domain}", )

        self.conn = SMBConnection(
            username=username,
            password=password,
            my_name=my_name,
            remote_name=remote_name,
            domain=domain,
            # use_ntlm_v2=True,
            # is_direct_tcp=True
        )

    def open(self, *, host: str = "0.0.0.0", port: int = 0, timeout=5):
        """
            usernameやpasswordが間違っている場合はNotReadyError
            remote_nameが間違っている場合はNotConnectedError
            ipやportが間違っている場合はTimeoutError
        """
        try:
            conn = self.conn.connect(host, port, timeout=timeout)
            self.__isopen = conn
        except Exception as e:
            self.message = str(e)
            self.__isopen = False
        return self.__isopen

    def close(self):
        if self.__isopen:
            self.conn.close()

    def __del__(self):
        try:
            self.conn.close()
        except Exception as e:
            print(e)

    def is_open(self):
        try:
            return self.__isopen
        except Exception:
            return False

    def get_filename_objects(self, service_name, path_name, *, host="0.0.0.0", port=0):
        if self.is_open is False:
            self.__open(host=host, port=port)

        _files = self.conn.listPath(service_name, path_name)
        self.file_list = [{
            "filename": f.filename,
            "filesize": f.file_size,
            "last_write_time": f.last_write_time
        } for f in _files if f.isDirectory is False]
        return self.file_list

    def get_data(self, service_name, path_name, file_name):
        with io.BytesIO() as file:
            self.conn.retrieveFile(
                service_name, path_name + file_name, file)
            file.seek(0)
            data = file.read().decode()
        return data


def get_csv_data(conn, agg_data: dict, *, strage: list = [], mode: str = "diff"):
    flg_getdata = False

    share_name = try_except(agg_data, key="share_name", exception=None)
    path_name = try_except(agg_data, key="path", exception="/")
    reg_filename = try_except(agg_data, key="regex_filename", exception=".*.csv")
    group_name = share_name + path_name + reg_filename

    _fileobjs = conn.get_filename_objects(service_name=share_name, path_name=path_name)
    fileobjs = [x for x in _fileobjs if re.findall(reg_filename, x["filename"]) != []]

    if fileobjs != []:
        latest_fileobj = max(fileobjs, key=lambda x: x["last_write_time"])
        filename = latest_fileobj["filename"]
        filesize = latest_fileobj["filesize"]

        strage_fileobj = next((item for item in strage if item["group"] == group_name), None)
        if strage_fileobj is None:
            strage.append({"group": group_name, "filename": filename, "filesize": filesize})

        print(f"========== MODE: {mode}, Strage: {strage}")
        if mode == "diff":
            # ファイル名かファイルサイズが異なる場合データ取得
            pre_filename = try_except(strage_fileobj, key="filename")
            pre_filesize = try_except(strage_fileobj, key="filesize")
            print(f"===== {pre_filename}, {filename}, {pre_filesize}, {filesize}")
            if pre_filename != filename:
                flg_getdata = True
                strage = [{**item, "filename": filename, "filesize": filesize} if item["group"] == group_name else item for item in strage]
            else:
                if pre_filesize != filesize:
                    flg_getdata = True
                    strage = [{**item, "filename": filename, "filesize": filesize} if item["group"] == group_name else item for item in strage]
        else:
            flg_getdata = True
            strage = [{**item, "filename": filename, "filesize": filesize} if item["group"] == group_name else item for item in strage]

        print(f"FLAG: {flg_getdata}")
        if flg_getdata is True:
            csv_data = conn.get_data(share_name, path_name, latest_fileobj["filename"])
            err = 0
            message = "success"
        else:
            csv_data = None
            err = 9999
            message = "skip"
    else:
        csv_data = None
        err = 10000
        message = "no file"

    result = {
        "data": csv_data,
        "strage": strage,
        "error": err,
        "message": message
    }
    print(f"====== RESULT: {result}")
    return result


def main(configure: dict, *, strage: list = [], mode: str = "diff"):
    print(configure)

    conf_network = try_except(configure, key="network")
    ctrl_attr = try_except(try_except(configure, key="controller"), key="attributes")
    conf_data = try_except(configure, key="data")

    # Sort data by the keys we want to group by
    sorted_data = sorted(conf_data, key=itemgetter('share_name', 'path', 'regex_filename'))

    # Group by 'share_name', 'path', 'regex_filename'
    grouped_data = [
        list(group) for _, group in groupby(sorted_data, key=itemgetter('share_name', 'path', 'regex_filename'))
    ]

    conn = Connect(
        username=try_except(ctrl_attr, key="username"),
        password=try_except(ctrl_attr, key="password"),
        remote_name=try_except(ctrl_attr, key="remotename"),
        domain=try_except(ctrl_attr, key="domain")
    )

    opened = conn.open(
        host=try_except(conf_network, key="ip_address"),
        port=try_except(conf_network, key="port")
    )

    error_info = [{
        "code": 4339346,
        "message": "Unknown Error"
    }]
    if opened is True:
        for datas in grouped_data:
            result = get_csv_data(conn, datas[0], strage=strage, mode=mode)

            # エラーコードが0 = SUCCESS or 9999 = SKIP以外の時、エラーコードを出力
            if result["error"] in [0, 9999]:
                error_info = None

                if result["error"] == 0:
                    df = polars.read_csv(io.StringIO(result["data"]))

                    for data in datas:
                        column_name = try_except(data, key="column_name")
                        if column_name:
                            column = next((col for col in df.columns if col.lower().replace(" ", "") == column_name.lower().replace(" ", "")), None)
                            if column:
                                # last_row = df.tail(1)
                                last_row = df.filter(df[column].is_not_null()).tail(1)

                                # datetimeの値を取得
                                datetime_value = last_row["datetime"][0] if "datetime" in last_row.columns else None

                                # dateとtimeの値を取得し結合
                                date_value = last_row["date"][0] if "date" in last_row.columns else ""
                                time_value = last_row["time"][0] if "time" in last_row.columns else ""
                                combined_date_time = f"{date_value} {time_value}".strip()

                                # yyyy/mm/ddとhh:mm:ssの値を取得し結合
                                date_str = last_row["yyyy/mm/dd"][0] if "yyyy/mm/dd" in last_row.columns else ""
                                time_str = last_row["hh:mm:ss"][0] if "hh:mm:ss" in last_row.columns else ""
                                combined_date_time_str = f"{date_str} {time_str}".strip()

                                # 値が存在する場合のみ返す
                                timestamp = ((datetime_value or combined_date_time or combined_date_time_str).replace("/", "-") or datetime.datetime.now().replace(microsecond=0))

                                # print(f"RESULT: {timestamp}, {datetime.datetime.now().replace(microsecond=0)}")

                                data["response"] = last_row[column][0]
                                data["response_datetime"] = timestamp

            else:
                error_info = [{
                    "code": result["error"],
                    "message": "Not find file"
                }]
    else:
        error_info = [{
            "code": 10060,
            "message": "Connection Error"
        }]
        print("not opend")

    data_list = [item for sublist in grouped_data for item in sublist]
    return {
        "data_list": data_list,
        "error": error_info,
        "strage": strage
    }


if __name__ == '__main__':
    configure = {
        # 'network': {'ip_address': '10.66.64.197', 'port': 139},
        'network': {'ip_address': '192.168.16.143', 'port': 139},
        'controller': {
            'type': 'PC', 'manufacturer': 'Microsoft', 'series': 'Windows10', 'protocol': 'SMB',
            'attributes': {
                'domain': 'JP', 'password': 'ncj46119', 'username': 'J100046119',
                'directory': '/', 'remotename': 'N0013034'}},
        'data': [
            {
                'machine_id': 4, 'machine_no': 'ccc', 'controller_connection_id': 5, 'data_location_id': 5,
                'datatype': 'Input', 'record_table': 't_record_count', 'method': 'datafile', 'path': '/',
                'share_name': 'share', 'column_name': 'input', 'regex_filename': '20.*_SUS_1.csv',
                'trigger': None, 'item': None, 'is_valid': True
            },
            {
                'machine_id': 4, 'machine_no': 'ccc', 'controller_connection_id': 5, 'data_location_id': 6,
                'datatype': 'Output', 'record_table': 't_record_count', 'method': 'datafile', 'path': '/',
                'share_name': 'share', 'column_name': 'output', 'regex_filename': '20.*_SUS_1.csv',
                'trigger': None, 'item': None, 'is_valid': True
            },
            {
                'machine_id': 4, 'machine_no': 'ccc', 'controller_connection_id': 5, 'data_location_id': 7,
                'datatype': 'Cycle time', 'record_table': 't_record_count', 'method': 'datafile', 'path': '/',
                'share_name': 'share', 'column_name': 'cycletime', 'regex_filename': '20.*_SUS_1.csv',
                'trigger': None, 'item': None, 'is_valid': True
            },
            {
                'machine_id': 4, 'machine_no': 'ccc', 'controller_connection_id': 5, 'data_location_id': 8,
                'datatype': 'Product Model', 'record_table': 't_record_count', 'method': 'datafile', 'path': '/',
                'share_name': 'share', 'column_name': 'Model', 'regex_filename': '20.*_SUS_1.csv',
                'trigger': None, 'item': None, 'is_valid': True
            },
            {
                'machine_id': 5, 'machine_no': 'ddd', 'controller_connection_id': 5, 'data_location_id': 9,
                'datatype': 'Input', 'record_table': 't_record_count', 'method': 'datafile', 'path': '/',
                'share_name': 'share', 'column_name': 'input', 'regex_filename': '20.*_SUS_2.csv',
                'trigger': None, 'item': None, 'is_valid': True
            },
            {
                'machine_id': 5, 'machine_no': 'ddd', 'controller_connection_id': 5, 'data_location_id': 10,
                'datatype': 'Output', 'record_table': 't_record_count', 'method': 'datafile', 'path': '/',
                'share_name': 'share', 'column_name': 'output', 'regex_filename': '20.*_SUS_2.csv',
                'trigger': None, 'item': None, 'is_valid': True
            },
        ]
    }
    strage = []

    result = main(configure=configure, strage=strage)
    print(result)

