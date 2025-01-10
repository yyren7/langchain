
import re
import io
import os
import glob
import pathlib
from pydantic import BaseModel
from typing import Pattern
from itertools import groupby
from operator import itemgetter
import platform
import polars
import datetime


const_share_name = ""
const_path_name = "/vast/seasv2/data"


def try_except(data: dict, key: str, *, exception=None):
    try:
        return data[key]
    except Exception:
        return exception


def get_filename_objects(*, path_name="/", pattern=".*\\.(csv|CSV)"):
    _path = pathlib.Path(path_name)
    filelist = [p for p in _path.glob('**/*') if re.search(pattern, str(p))]

    fileobjects = []
    for _filename in filelist:
        last_write_time = os.path.getmtime(_filename)
        filename = str(_filename).replace("\\", "/").split("/")[-1]
        fileobjects.append({
            "filename": filename,
            "last_write_time": last_write_time
        })
    return fileobjects


def get_csv_data(agg_data: dict, *, strage: list = [], mode: str = "diff", path_change: bool = False):
    flg_getdata = False

    if path_change is True:
        share_name = try_except(agg_data, key="share_name", exception=None)
        path_name = try_except(agg_data, key="path", exception="/")
    else:
        share_name = const_share_name
        path_name = const_path_name
    reg_filename = try_except(agg_data, key="regex_filename", exception=".*.csv")
    group_name = share_name + path_name + reg_filename

    _fileobjs = get_filename_objects(path_name=path_name)
    fileobjs = [x for x in _fileobjs if re.findall(reg_filename, x["filename"]) != []]

    if fileobjs != []:
        latest_fileobj = max(fileobjs, key=lambda x: x["last_write_time"])
        filename = latest_fileobj["filename"]

        strage_fileobj = next((item for item in strage if item["group"] == group_name), None)
        if strage_fileobj is None:
            strage.append({"group": group_name, "filename": filename})

        print(f"========== MODE: {mode}, Strage: {strage}")
        if mode == "diff":
            # ファイル名かファイルサイズが異なる場合データ取得
            pre_filename = try_except(strage_fileobj, key="filename")
            print(f"===== {pre_filename}, {filename}")
            if pre_filename != filename:
                flg_getdata = True
                strage = [{**item, "filename": filename} if item["group"] == group_name else item for item in strage]
            else:
                pass
        else:
            flg_getdata = True
            strage = [{**item, "filename": filename} if item["group"] == group_name else item for item in strage]

        print(f"FLAG: {flg_getdata}")
        if flg_getdata is True:
            # カンマ区切りとタブ区切りの両対応
            # タブ区切りで読み取った時にColumnsが1以下の場合にカンマ区切りで再読出し
            csv_data = polars.read_csv(path_name + "/" + latest_fileobj["filename"], encoding="utf8", has_header=True, separator="\t")
            if len(csv_data.columns) <= 1:
                csv_data = polars.read_csv(path_name + "/" + latest_fileobj["filename"], encoding="utf8", has_header=True, separator=",")

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


def main(configure: dict, *, strage: list = []):
    conf_data = try_except(configure, key="data")

    # Sort data by the keys we want to group by
    sorted_data = sorted(conf_data, key=itemgetter('share_name', 'path', 'regex_filename'))

    # Group by 'share_name', 'path', 'regex_filename'
    grouped_data = [
        list(group) for _, group in groupby(sorted_data, key=itemgetter('share_name', 'path', 'regex_filename'))
    ]

    for datas in grouped_data:
        result = get_csv_data(datas[0], strage=strage, mode="diff")
        result_data = try_except(result, key="data")

        # エラーコードが0 = SUCCESS or 9999 = SKIP以外の時、エラーコードを出力
        if result["error"] in [0, 9999] and result_data is not None:
            error_info = None

            if result["error"] == 0:
                for data in datas:
                    column_name = try_except(data, key="column_name")
                    if column_name:
                        column = next((col for col in result_data.columns if col.lower().replace(" ", "") == column_name.lower().replace(" ", "")), None)
                        if column:
                            last_row = result_data.filter(result_data[column].is_not_null()).tail(1)

                            # datetimeの値を取得
                            datetime_value = last_row["datetime"][0] if "datetime" in last_row.columns else None

                            # dateとtimeの値を取得し結合
                            date_value = last_row["date"][0] if "date" in last_row.columns else ""
                            time_value = last_row["time"][0] if "time" in last_row.columns else ""
                            combined_date_time = f"{date_value} {time_value}".strip()

                            # yyyy/mm/ddとhh:mm:ssの値を取得し結合
                            date_str_ymd_slash = last_row["yyyy/mm/dd"][0] if "yyyy/mm/dd" in last_row.columns else ""
                            date_str_ymd_hyphen = last_row["yyyy-mm-dd"][0] if "yyyy-mm-dd" in last_row.columns else ""
                            date_str_mdy_slash = last_row["mm/dd/yyyy"][0] if "mm/dd/yyyy" in last_row.columns else ""
                            date_str_mdy_hyphen = last_row["mm-dd-yyyy"][0] if "mm-dd-yyyy" in last_row.columns else ""
                            date_str_dmy_slash = last_row["dd/mm/yyyy"][0] if "dd/mm/yyyy" in last_row.columns else ""
                            date_str_dmy_hyphen = last_row["dd-mm-yyyy"][0] if "dd-mm-yyyy" in last_row.columns else ""
                            time_str = last_row["hh:mm:ss"][0] if "hh:mm:ss" in last_row.columns else ""
                            date_str = date_str_ymd_slash or date_str_ymd_hyphen or date_str_mdy_slash or date_str_mdy_hyphen or date_str_dmy_slash or date_str_dmy_hyphen
                            combined_date_time_str = f"{date_str} {time_str}".strip()

                            # 値が存在する方のみ返す
                            timestamp = ((
                                datetime_value or combined_date_time or combined_date_time_str
                            ).replace("/", "-") or datetime.datetime.now().replace(microsecond=0))

                            data["response"] = last_row[column][0]
                            data["response_datetime"] = timestamp

        else:
            error_info = [{
                "code": result["error"],
                "message": "Not find file"
            }]

    data_list = [item for sublist in grouped_data for item in sublist]
    return {
        "data_list": data_list,
        "error": error_info,
        "strage": strage
    }


if __name__ == "__main__":

    configure = {
        'network': {'ip_address': "localhost", 'port': None},
        'controller': {
            'type': 'PC', 'manufacturer': 'Microsoft', 'series': 'Windows10', 'protocol': 'LocalFolder',
            'attributes': {"Connection_waittime": 20}
        },
        'data': [
            {
                'machine_id': 4, 'machine_no': 'ccc', 'controller_connection_id': 5, 'data_location_id': 5,
                'datatype': 'Input', 'record_table': 't_record_count', 'method': 'datafile',
                'path': '/vast/seasv2/data',
                # 'path': 'C:/Develop/DockerImage/VAST/VAST-DB/app/vast/seasv2/data',
                'share_name': 'share', 'column_name': 'input', 'regex_filename': '20.*_SUS_1.csv',
                'trigger': None, 'item': None, 'is_valid': True
            },
            # {
            #     'machine_id': 4, 'machine_no': 'ccc', 'controller_connection_id': 5, 'data_location_id': 6,
            #     'datatype': 'Output', 'record_table': 't_record_count', 'method': 'datafile', 'path': '/',
            #     'share_name': 'share', 'column_name': 'output', 'regex_filename': '20.*_SUS_1.csv',
            #     'trigger': None, 'item': None, 'is_valid': True
            # },
            # {
            #     'machine_id': 4, 'machine_no': 'ccc', 'controller_connection_id': 5, 'data_location_id': 7,
            #     'datatype': 'Cycle time', 'record_table': 't_record_count', 'method': 'datafile', 'path': '/',
            #     'share_name': 'share', 'column_name': 'cycletime', 'regex_filename': '20.*_SUS_1.csv',
            #     'trigger': None, 'item': None, 'is_valid': True
            # },
            # {
            #     'machine_id': 4, 'machine_no': 'ccc', 'controller_connection_id': 5, 'data_location_id': 8,
            #     'datatype': 'Product Model', 'record_table': 't_record_count', 'method': 'datafile', 'path': '/',
            #     'share_name': 'share', 'column_name': 'Model', 'regex_filename': '20.*_SUS_1.csv',
            #     'trigger': None, 'item': None, 'is_valid': True
            # },
            {
                'machine_id': 5, 'machine_no': 'ddd', 'controller_connection_id': 5, 'data_location_id': 9,
                'datatype': 'Input', 'record_table': 't_record_count', 'method': 'datafile',
                'path': '/vast/seasv2/data',
                # 'path': 'C:/Develop/DockerImage/VAST/VAST-DB/app/vast/seasv2/data',
                'share_name': 'share', 'column_name': 'input', 'regex_filename': '20.*_SUS_2.csv',
                'trigger': None, 'item': None, 'is_valid': True
            },
            # {
            #     'machine_id': 5, 'machine_no': 'ddd', 'controller_connection_id': 5, 'data_location_id': 10,
            #     'datatype': 'Output', 'record_table': 't_record_count', 'method': 'datafile', 'path': '/',
            #     'share_name': 'share', 'column_name': 'output', 'regex_filename': '20.*_SUS_2.csv',
            #     'trigger': None, 'item': None, 'is_valid': True
            # },
        ]
    }

    strage = []

    result = main(configure=configure, strage=strage)
    print(result)








