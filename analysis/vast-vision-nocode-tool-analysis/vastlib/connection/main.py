import asyncio
# from multiprocessing import Process, Pool, Queue, active_children, Manager

# from multiprocessing.managers import BaseManager
import multiprocessing

import time
import random
import os
import re
from pydantic import BaseModel

import redis

from collections import defaultdict

from typing import Pattern

def try_except(data: dict, key: str, *, exception=None):
    try:
        return data[key]
    except Exception:
        return exception


g_check_name_list = {}

class Regexes(BaseModel):
    bit: Pattern = re.compile(r"(bit|boolean)")
    word: Pattern = re.compile(r"(word|short)")
    dword: Pattern = re.compile(r"(dword|doubleword|integer)")
    string: Pattern = re.compile(r"string")
    fraction: Pattern = re.compile(r"\\.")
    signed: Pattern = re.compile(r"(\\-|\\±|s_|signed_)")

    tcp: Pattern = re.compile(r"tcp", flags=re.IGNORECASE)
    udp: Pattern = re.compile(r"udp", flags=re.IGNORECASE)

    fins: Pattern = re.compile(r"fins", flags=re.IGNORECASE)
    slmp: Pattern = re.compile(r"(slmp|mc_protocol_3e_frame)", flags=re.IGNORECASE)
    focas2: Pattern = re.compile(r"focas2", flags=re.IGNORECASE)
    mtlinki: Pattern = re.compile(r"(mtlinki|mtlink_i|mt-linki)", flags=re.IGNORECASE)
    ncprotocol2: Pattern = re.compile(r"(NC専用通信装置通信プロトコル方式2|nc2|ncprotocol2|nc protocol 2|nc protocol2)", flags=re.IGNORECASE)
    smb: Pattern = re.compile(r"smb", flags=re.IGNORECASE)
    localfolder: Pattern = re.compile(r"localfolder", flags=re.IGNORECASE)


class Configure(BaseModel):
    ip_address: str = "127.0.0.1"
    port: int = 0
    type: str = "PLC"
    manufacturer: str = "Omron"
    series: str = "NJ"
    protocol: str = "FINS/UDP"
    attributes: dict = {}


def communication(configure: dict, *, strage: list = [], test_mode: bool = False):
    """

    """
    network = try_except(configure, "network")
    controller = try_except(configure, "controller")
    conf = Configure(**network, **controller)
    regexes = Regexes()

    data = try_except(configure, "data", exception=None)
    print(f"=-=-=-=-= DATA LOCATION: {data} =-=-=-=-= ")

    # =========================================
    # DEVICE MEMORY
    # FINS
    if regexes.fins.search(conf.protocol):
        try:
            import protocols.fins.main as fins
        except Exception:
            try:
                import connection.protocols.fins.main as fins
            except Exception:
                import src.connection.protocols.fins.main as fins

        con = fins.Communication(configure=configure)
        con.set_connection(timeout=5)

        identification = con.identification_unit()
        print(f"identification: {identification}")

        con.set_request_message_randam_read()
        con.set_request_message_bulk_read()

        # TODO timeout時の返答
        try:
            con.open()
            recv = con.connection()
            con.close()
            print(f"DEBUG, recv: {recv}")

        except Exception as e:
            data_list = None
            error_info = [{
                "code": 10060,
                "message": f"Connection Error: {e}"
            }]
        else:
            error_info = [x for x in recv if x["connection"]["code"] != 0]
            if error_info:
                data_list = None
            else:
                randam_res = con.divided_response_random_read()
                bulk_res = con.divided_response_bulk_read()
                data_list = con.divided_read()
                error_info = con.extract_error_connection([randam_res, bulk_res])

        return {
            "data_list": data_list,
            "error": error_info
        }

    # SLMP
    elif regexes.slmp.search(conf.protocol):
        try:
            import protocols.slmp.main as slmp
        except Exception:
            try:
                import connection.protocols.slmp.main as slmp
            except Exception:
                import src.connection.protocols.slmp.main as slmp

        con = slmp.Communication(configure=configure)
        con.set_connection(timeout=5)
        con.identification_unit()

        con.set_request_random_read()
        con.set_request_bulk_read()

        try:
            con.open()
            recv = con.connection()
            con.close()
            print(f"DEBUG, recv: {recv}")
        except Exception as e:
            data_list = None
            error_info = [{
                "code": 10060,
                "message": f"Connection Error: {e}"
            }]
        else:
            error_info = [x for x in recv if x["connection"]["code"] != 0]
            if error_info:
                data_list = None
            else:
                randam_res = con.divided_response_randam_read()
                bulk_res = con.divided_response_bulk_read()
                print(f'randam_res: {randam_res["metainfo"]}')
                print(f'bulk_res: {bulk_res["metainfo"]}')
                data_list = con.divided_read()
                error_info = con.extract_error_connection([randam_res, bulk_res])

        return {
            "data_list": data_list,
            "error": error_info
        }

    # =========================================
    # COMMANDS
    # MTLINKi
    elif regexes.mtlinki.search(conf.protocol):
        try:
            import protocols.mtlinki.main as mtlinki
        except Exception:
            try:
                import connection.protocols.mtlinki.main as mtlinki
            except Exception:
                import src.connection.protocols.mtlinki.main as mtlinki

        try:
            result = mtlinki.main(connection=configure)
            # for x in result["data_list"]:
            #     if try_except(x, key="updatedate"):
            #         x["time"] = x["updatedate"]
            print(f"MTLINKi RESULT: {result}")
        except Exception as e:
            result = {
                "data_list": [],
                "error": str(e)
            }
            print(e)

        print(f'MTLINKi datalist: {result["data_list"]}, error:{result["error"]}')
        return result

    # FOCAS2
    # TODO
    elif regexes.focas2.search(conf.protocol):
        try:
            import protocols.focas2.main as focas2
        except Exception:
            try:
                import connection.protocols.focas2.main as focas2
            except Exception:
                import src.connection.protocols.focas2.main as focas2

        try:
            # print(f"FOCAS2 CONF: {configure}")
            dllpath = os.path.dirname(os.path.abspath(__file__))
            dllname = 'fwlibe64.dll'
            # host = '10.7.56.38:8193'
            # host = '127.0.0.1:0'
            host = connection["network"]["ip_address"] + ":" + str(connection["network"]["port"])
            con = focas2.Connect(dllpath, dllname, host).get_connection(dllpath, dllname, host)
            # print(f"test:{con}")

            cmd = defaultdict(list)
            data = try_except(configure, key="data", exception=None)
            for item in data:
                # cmd[f'{item["command"]},{item["param"]["number"]}'].append(item)
                cmd[f'{item["command"]}'].append(item)

            data_list = []
            for key, value in cmd.items():
                command_result = None

                # CNCステータス情報のリード(2)
                if key == "statinfo2":
                    command_result = con.statinfo2()
                    """
                    {
                        "result": 0, "hdck": 0, "tmmode": 0, "aut": 4, "run": 0, "motion": 0, "mstb": 0, "emergency": 0, "alarm": 0, "edit": 0, "warning": 0, "o3dchk": 0, "ext_opt": 0, "restart": 0
                    }
                    """

                # アラームステータスのリード(2)
                if key == "alarm2":
                    command_result = con.alarm2()
                    """
                    {
                        "result": 0, "alarm": 0
                    }
                    """

                #  CNC用エラー詳細の取得
                if key == "getdtailerr":
                    command_result = con.getdtailerr()
                    """
                    {
                        'result': 0, 'err_no': 0, 'err_dtno': 0
                    }
                    """

                # CNCシステム情報のリード
                if key == "sysinfo":
                    command_result = con.sysinfo()
                    """
                    {
                        'result': 0, 'addinfo': 514, 'max_axis': 32, 'cnc_type': b'31', 'mt_type': b'MM', 'series': b'G433', 'version': b'32.4', 'axes': b'06'
                    }
                    """

                for item in value:
                    _arguments = try_except(item, key="arguments", exception=None)
                    arguments = _arguments.copy()
                    regist_flg = True

                    # パラメータのリード
                    if key == "rdparam":
                        maxaxis = try_except(arguments, key="maxaxis", exception=32)
                        axisnum = try_except(arguments, key="axisnum", exception=-1)
                        datalen = try_except(arguments, key="datalen", exception=132)
                        paranum = try_except(arguments, key="paranum", exception=None)
                        if paranum is None:
                            item["error"] = 20001  # コマンドの引数が不正＿引数入力を1つ以上確認できないため取得実行せず
                            regist_flg = False
                        else:
                            for i in ["maxaxis", "axisnum", "datalen", "paranum"]:
                                try:
                                    del arguments[i]
                                except Exception:
                                    pass
                            command_result = con.rdparam(maxaxis, paranum, axisnum, datalen)
                            """
                            {
                                "result": 0, "datano": 6750, "type": 0, "cdata": b'\x04', "idata": -3068, "ldata": 1897476, "prm_val": 1897476, "dec_val": 0, "cdatas": b'\x04\xf4\x1c', "idatas[0]": -3068, "ldatas[0]": 1897476, "prm_val[0]": 1897476, "dec_val[0]": 0
                            }
                            """

                    # タイマーデータ
                    if key == "rdtimer":
                        typenum = try_except(arguments, key="typenum", exception=None)
                        if typenum is None:
                            item["error"] = 20001  # コマンドの引数が不正＿引数入力を1つ以上確認できないため取得実行せず
                            regist_flg = False
                        else:
                            del arguments['typenum']
                            command_result = con.rdparam(maxaxis, paranum, axisnum, datalen)
                            """
                            {
                                "result": 0, "minute": 1897465, "msec": 0
                            }
                            """

                    # アラームメッセージの一括リード(2)
                    if key == "rdalmmsg2":
                        typenum = try_except(arguments, key="typenum", exception=None)
                        pointnum = try_except(arguments, key="pointnum", exception=None)
                        if typenum is None or pointnum is None:
                            item["error"] = 20001  # コマンドの引数が不正＿引数入力を1つ以上確認できないため取得実行せず
                            regist_flg = False
                        else:
                            del arguments['typenum'], arguments['pointnum']
                            """
                            {
                                'result': 0, 'num': 0, 'alm_no': 0, 'type': 0, 'axis': 0, 'dummy': 0, 'msg_len': 0, 'alm_msg': b''
                            }
                            """

                    if regist_flg and command_result is None:
                        item["error"] = 20004  # コマンド指定が不正＿command入力値が実行コマンド名に一致しない
                    else:
                        # データ取得処理
                        if regist_flg and arguments:
                            for arg_key, arg_value in arguments.items():
                                r_data = try_except(command_result, key=arg_key, exception=None)
                                if r_data is not None:
                                    if str(r_data) != str(arg_value):
                                        if float(r_data) != float(arg_value):
                                            if int(r_data) != int(arg_value):
                                                regist_flg = False
                                                item["error"] = 20000  # 取得スキップ＿データがarguments指定条件に一致しない
                                    break
                            if r_data is None:
                                regist_flg = False
                                item["error"] = 20003  # arguments指定が不正＿引数以外のatguments入力値が返答データに含まれない

                        if regist_flg:
                            r_result = try_except(command_result, key="result", exception=None)
                            if r_result != 0:
                                item["error"] = command_result  # 完了コード＿コマンド実行部でエラー
                            else:
                                r_data = try_except(command_result, key=item["field"], exception=None)
                                if r_data is None:
                                    item["error"] = 20002  # 取得データ指定が不正＿field入力値が返答データに含まれない
                                else:
                                    item["response"] = r_data
                                    item["error"] = None

                data_list.extend(value)
                result = {
                    "data_list": data_list,
                    "error": None
                }

        except Exception as e:
            result = {
                "data_list": [],
                "error": str(e)
            }
        print(f'FOCAS2 datalist: {result["data_list"]}, error:{result["error"]}')
        return result

    # NC Protocol 2
    elif regexes.ncprotocol2.search(conf.protocol):
        try:
            import protocols.nc_protocol2.ncunit_protocol2 as ncunit_protocol2
        except Exception:
            try:
                import connection.protocols.nc_protocol2.ncunit_protocol2 as ncunit_protocol2
            except Exception:
                import src.connection.protocols.nc_protocol2.ncunit_protocol2 as ncunit_protocol2

        from collections import defaultdict

        try:
            # Create a dictionary to store lists by command
            grouped_by_command = defaultdict(list)

            # Iterate over each item and group by 'command'
            data = try_except(configure, key="data", exception=None)
            for item in data:
                grouped_by_command[item['command']].append(item)

            # Convert defaultdict to a regular dict if needed
            grouped_by_command = dict(grouped_by_command)

            # print(grouped_by_command)
            con = ncunit_protocol2.Connect(conf.ip_address, conf.port)
            data_list = []
            for key, value in grouped_by_command.items():
                # print(key, value)
                command_result = None

                # 生産データ2(時間表示)
                if key == "PRDC2":
                    command_result = con.load_prdc2(flag=True)
                    """
                        {
                            'L01': {'cycletime1': '000000256', 'cuttingtime1': '000000173', 'cycletime2': '000000000',
                                'cuttingtime2': '000000000', 'prg1': '5000', 'prg2': '0000', 'prgfolder1': "'/       '",
                                'prgfolder2': "'        '", 'memstaus1': '0', 'memstaus2': '0'
                                },
                            'N00': {'date': '20230731', 'time': '000107', 'count': '2', 'energization': ' 65849'},
                            'result': 0
                        }
                    """

                # 生産データ2（時間表示）
                if key == "PRDD2":
                    command_result = con.load_prdd2()
                    """
                        {
                            "L01": {
                                    "cycletime1": "000005005", "cuttingtime1": "000003531", "othertime1": "049",
                                    "cycletime2": "000000000", "cuttingtime2": "000000000", "othertime2": "000",
                                    "prg1": "8000                            ", "prg2": "0000                            ",
                                    "prgfolder1": "CK3MQBREV1                       ", "prgfolder2": "                                 ",
                                    "prgstatus1": "0", "prgstatus2": "0", "memstatus1": "0", "memstatus2": "0", "count": "8055"
                                },
                            'result': 0
                        }
                    """

                # 生産データ3(状態履歴)
                if key == "PRD3":
                    command_result = con.load_prd3()
                    """
                    {
                        'C01': {'currtime': '20230731104231', 'currstatus': '5', 'currlang': '0',
                            'currstatinfo': '050518', 'currfolder': "'        '", 'memstatus': '0'},
                        'result': 0
                    }
                    """

                # 生産データ3(状態履歴)
                if key == "PRDD3":
                    command_result = con.load_prdd3()
                    """
                    {
                        "C01": {"currtime": "20240627170138", "currstatus": "5", "currlang": "0",
                            "currstatinfo": "900500                          ", "currfolder": "                                 ", "memstatus": "0"},
                        'result': 0
                    }
                    """

                # 機械モニタ用データ（生産データ4）
                if key == "MONTR":
                    command_result = con.load_montr()
                    """
                    {
                        "T01": {"actualtime": "046725542", "energization": "114900041", "operating": "046635210"},
                        'result': 0
                    }
                    """

                for item in value:
                    _arguments = try_except(item, key="arguments", exception=None)
                    arguments = _arguments.copy()
                    regist_flg = True

                    # 工具データ(タイプ1)
                    if key == "TOLN":
                        toolunit = try_except(arguments, key="tool_unit", exception=None)
                        toolno = try_except(arguments, key="tool_no", exception=None)
                        if toolunit is None or toolno is None:
                            item["error"] = 20001   # コマンドの引数が不正＿引数入力を1つ以上確認できないため取得実行せず
                            regist_flg = False
                        else:
                            command_result = con.load_toln(unit=toolunit, num=toolno)
                            del arguments['tool_unit'], arguments['tool_no']

                    # PLC信号データ (TEST)
                    if key == "PLCD":
                        devicename = try_except(arguments, key="device_name", exception=None)
                        devicenum = try_except(arguments, key="device_num", exception=None)
                        if toolunit is None or toolno is None:
                            item["error"] = 20001   # コマンドの引数が不正＿引数入力を1つ以上確認できないため取得実行せず
                            regist_flg = False
                        else:
                            command_result = con.read_plcd(devicename, devicenum)
                            del arguments['device_name'], arguments['device_num']

                    # データ取得処理
                    if regist_flg and command_result is None:
                        item["error"] = 20004  # コマンド指定が不正＿command入力値が実行コマンド名に一致しない
                    else:
                        if regist_flg and arguments:
                            for arg_key, arg_value in arguments.items():
                                for r_key, r_value in command_result.items():
                                    if r_key != "result":
                                        r_data = try_except(r_value, key=arg_key, exception=None)
                                        if r_data is not None:
                                            if str(r_data) != str(arg_value):
                                                if float(r_data) != float(arg_value):
                                                    if int(r_data) != int(arg_value):
                                                        regist_flg = False
                                                        item["error"] = 20000  # 取得スキップ＿データがarguments指定条件に一致しない
                                            break
                                if r_data is None:
                                    regist_flg = False
                                    item["error"] = 20003  # 引数以外のatguments入力値が返答データに含まれない

                        if regist_flg:
                            for r_key, r_value in command_result.items():
                                if r_key != "result":
                                    r_data = try_except(r_value, key=item["field"], exception=None)
                                    if r_data is None:
                                        item["error"] = 20002  # 取得データ指定が不正＿field入力値が返答データに含まれない
                                    else:
                                        item["response"] = r_data
                                        item["error"] = None
                                        break
                                else:
                                    if r_value != 0:
                                        item["error"] = r_value  # コマンド実行部でエラーの場合は完了コード
                                        break
                data_list.extend(value)
                result = {
                    "data_list": data_list,
                    "error": None
                }

        except Exception as e:
            result = {
                "data_list": [],
                "error": str(e)
            }

        print(f'NC Protocol 2 datalist: {result["data_list"]}, error:{result["error"]}')
        return result

    # =========================================
    # FILE ACCESS
    # SMB
    elif regexes.smb.search(conf.protocol):
        try:
            import protocols.smb.main as smb
        except Exception:
            try:
                import connection.protocols.smb.main as smb
            except Exception:
                import src.connection.protocols.smb.main as smb

        result = smb.main(configure=configure, strage=strage, mode="diff")
        print(f"==== SMB: {result}")
        return result

    # local file
    elif regexes.localfolder.search(conf.protocol):
        try:
            import protocols.smb.main as smb
        except Exception:
            try:
                import connection.protocols.smb.main as smb
            except Exception:
                import src.connection.protocols.smb.main as smb

        result = smb.main(configure=configure, strage=strage, mode="diff")
        print(f"==== LocalFolderFile: {result}")
        return result

    else:
        print(f"None Communication: {conf}")


# プロセス強制終了
def process_terminate(process):
    """
        各プロセスに対してTerminateを送信して強制終了させる
    """
    # redis set stop
    redis.set(process.name, "stop")
    print(f"Terminate Process: {process.name}")

    process.terminate()



if __name__ == "__main__":
    connections = [
        {
            "network": {
                "ip_address": "192.168.250.10",
                "port": 9000,
            },
            "controller": {
                "type": "PLC",
                "manufacturer": "KEYENCE",
                "series": "KV",
                "protocol": "SLMP/TCP",
                "attributes": {}
            },
            "data": [
                {
                    "execute": "read",
                    "machine_id": 1,
                    "group": "count",
                    "datatype": "input",
                    "device": "D",
                    "address": "100",
                    "data_unit": "integer",
                    "trigger": None,
                    "item": None,
                },
                {
                    "machine_id": 2,
                    "group": "count",
                    "datatype": "input",
                    "device": "D",
                    "address": "102",
                    "data_unit": "integer",
                    "trigger": None,
                    "item": None,
                },
                {
                    "machine_id": 1,
                    "group": "count",
                    "datatype": "cycletime",
                    "device": "D",
                    "address": "200",
                    "data_unit": "float",
                    "trigger": None,
                    "item": None,
                },
                {
                    "machine_id": 1,
                    "group": "error",
                    "datatype": "error_trigger",
                    "device": "D",
                    "address": "300",
                    "data_unit": "boolean",
                    "trigger": 1,
                    "item": None,
                },
                {
                    "machine_id": 1,
                    "group": "error",
                    "datatype": "error_item",
                    "device": "D",
                    "address": "301",
                    "data_unit": "integer",
                    "trigger": 100,
                    "item": "Machine Error 1",
                },
                {
                    "machine_id": 1,
                    "group": "custom",
                    "datatype": "date",
                    "device": "D",
                    "address": "400",
                    "data_unit": "integer",
                    "bcd": True,
                    "trigger": None,
                    "item": None,
                },
                {
                    "machine_id": 1,
                    "group": "custom",
                    "datatype": "x-field",
                    "device": "D",
                    "address": "500",
                    "data_unit": "s_integer",
                    "trigger": None,
                    "item": None,
                },
            ],
        },
        # {
        #     "network": {
        #         "ip_address": "192.168.250.1",
        #         "port": 9600,
        #     },
        #     "controller": {
        #         "type": "PLC",
        #         "manufacturer": "Omron",
        #         "series": "NJ101",
        #         "protocol": "FINS/UDP",
        #         "attributes": {}
        #     },
        #     "data": [
        #         {
        #             "execute": "read",
        #             "machine_id": 1,
        #             "group": "count",
        #             "datatype": "input",
        #             "device": "dm",
        #             "address": "100",
        #             "data_unit": "integer",
        #             "trigger": None,
        #             "item": None,
        #         },
        #         {
        #             "machine_id": 2,
        #             "group": "count",
        #             "datatype": "input",
        #             "device": "dm",
        #             "address": "102",
        #             "data_unit": "integer",
        #             "trigger": None,
        #             "item": None,
        #         },
        #         {
        #             "machine_id": 1,
        #             "group": "count",
        #             "datatype": "cycletime",
        #             "device": "dm",
        #             "address": "200",
        #             # "data_unit": "float",
        #             "data_unit": "integer",
        #             "trigger": None,
        #             "item": None,
        #         },
        #         {
        #             "machine_id": 1,
        #             "group": "error",
        #             "datatype": "error_trigger",
        #             "device": "wr",
        #             "address": "300",
        #             "data_unit": "boolean",
        #             "trigger": 1,
        #             "item": None,
        #         },
        #         {
        #             "machine_id": 1,
        #             "group": "error",
        #             "datatype": "error_item",
        #             "device": "dm",
        #             "address": "301",
        #             "data_unit": "integer",
        #             "trigger": 100,
        #             "item": "Machine Error 1",
        #         },
        #         {
        #             "machine_id": 1,
        #             "group": "custom",
        #             "datatype": "date",
        #             "device": "dm",
        #             "address": "400",
        #             "data_unit": "integer",
        #             "bcd": True,
        #             "trigger": None,
        #             "item": None,
        #         },
        #         {
        #             "machine_id": 1,
        #             "group": "custom",
        #             "datatype": "x-field",
        #             "device": "dm",
        #             "address": "500",
        #             "data_unit": "s_integer",
        #             "trigger": None,
        #             "item": None,
        #         },
        #     ],
        # },
        # {
        #     "network": {
        #         "ip_address": "192.168.250.2",
        #         "port": 9600,
        #     },
        #     "controller": {
        #         "type": "PLC",
        #         "manufacturer": "Omron",
        #         "series": "NJ101",
        #         "protocol": "FINS/UDP",
        #         "attributes": {}
        #     },
        #     "data": [
        #         {
        #             "execute": "read",
        #             "machine_id": 1,
        #             "group": "count",
        #             "datatype": "input",
        #             "device": "dm",
        #             "address": "100",
        #             "data_unit": "integer",
        #             "trigger": None,
        #             "item": None,
        #         },
        #         {
        #             "machine_id": 2,
        #             "group": "count",
        #             "datatype": "input",
        #             "device": "dm",
        #             "address": "102",
        #             "data_unit": "integer",
        #             "trigger": None,
        #             "item": None,
        #         },
        #         {
        #             "machine_id": 1,
        #             "group": "count",
        #             "datatype": "cycletime",
        #             "device": "dm",
        #             "address": "200",
        #             "data_unit": "float",
        #             "trigger": None,
        #             "item": None,
        #         },
        #         {
        #             "machine_id": 1,
        #             "group": "error",
        #             "datatype": "error_trigger",
        #             "device": "wr",
        #             "address": "300",
        #             "data_unit": "boolean",
        #             "trigger": 1,
        #             "item": None,
        #         },
        #         {
        #             "machine_id": 1,
        #             "group": "error",
        #             "datatype": "error_item",
        #             "device": "dm",
        #             "address": "301",
        #             "data_unit": "integer",
        #             "trigger": 100,
        #             "item": "Machine Error 1",
        #         },
        #         {
        #             "machine_id": 1,
        #             "group": "custom",
        #             "datatype": "date",
        #             "device": "dm",
        #             "address": "400",
        #             "data_unit": "integer",
        #             "bcd": True,
        #             "trigger": None,
        #             "item": None,
        #         },
        #         {
        #             "machine_id": 1,
        #             "group": "custom",
        #             "datatype": "x-field",
        #             "device": "dm",
        #             "address": "500",
        #             "data_unit": "s_integer",
        #             "length": 2,
        #             "trigger": None,
        #             "item": None,
        #         },
        #     ],
        # },
        # {
        #     "network": {
        #         "ip_address": "192.168.10.1",
        #         "port": 500,
        #     },
        #     "controller": {
        #         "type": "cnc",
        #         "manufacturer": "fanuc",
        #         "series": "i31",
        #         "protocol": "focas2",
        #         "attributes": {}
        #     },
        #     "data": [
        #         {
        #             "machine_id": 10,
        #             "group": "custom",
        #             "datatype": "file_name",
        #             # "file_comments", "file_type", "file_size", "file_updatedtime"
        #             "command": "ds_rdhdddir",
        #             "field": "",
        #             "key": "",
        #             "trigger": None,
        #             "item": None
        #         },
        #     ]
        # },
        # {
        #     "network": {
        #         "ip_address": "192.168.20.2",
        #         "port": 9000,
        #     },
        #     "controller": {
        #         "type": "pc",
        #         "manufacturer": "fanuc",
        #         "series": "i31",
        #         "protocol": "MT-LINKi",
        #         "attributes": {
        #             "authsource": "MTLINKi",
        #             "username": "mtlinki",
        #             "password": "password123456"
        #         }
        #     },
        #     "data": [
        #         {
        #             "machine_id": 20,
        #             "group": "input",
        #             "datatype": None,
        #             "command": "",
        #             "field": "",
        #             "key": "",
        #             "trigger": None,
        #             "item": None
        #         },
        #     ]
        # },
        # {
        #     "network": {
        #         "ip_address": "192.168.20.3",
        #         "port": 9000,
        #     },
        #     "controller": {
        #         "type": "pc",
        #         "manufacturer": "microsoft",
        #         "series": "windows10",
        #         "protocol": "SMB",
        #         "attributes": {
        #             "remotename": "n0013034",
        #             "domain": "jp",
        #             "username": "j100046119",
        #             "password": "password123456",
        #             "directory": "/"
        #         }
        #     },
        #     "data": [
        #         {
        #             "machine_id": 21,
        #             "group": "input",
        #             "datatype": None,
        #             "sharefolder": "share12",
        #             "path": "/data/",
        #             "fileregex": "20*_123456.csv",
        #             "culumnname": "INPUT",
        #             "trigger": None,
        #             "item": None
        #         },
        #     ]

        # }
    ]

    stop_event = multiprocessing.Event()
    # Process Start
    for connection in connections:
        process_start(connection, stop_event)

    while True:
        active_processes = multiprocessing.active_children()
        print(f"ACTIVE PROCESSES: {active_processes}")
        if active_processes == []:
            break

        time.sleep(3)

        # # 指定した名前のプロセスのみ停止させるテスト
        # terminate_process_name = active_processes[0].name
        # print(f"Terminate: {terminate_process_name}")
        # process_terminate(process_name=terminate_process_name)
        # time.sleep(3)

    # connections = [
    #     {
    #         "network": {
    #             "ip_address": "192.168.1.0",
    #             "port": 9000,
    #         },
    #         "controller": {
    #             "type": "PLC",
    #             "manufacturer": "Mitsubisi Electric",
    #             "series": "MELSEC iQ-R",
    #             "protocol": "SLMP/TCP",
    #             "attributes": {}
    #         },
    #         "data": [{
    #             "execute": "read",
    #             "machine_id": 1,
    #             "group": "count",
    #             "datatype": "input",
    #             "command": "cnc_alart",
    #             "field": "alartvalue",
    #             "param": {
    #                 "alm_type": "",
    #                 "length": ""
    #             },
    #             # "trigger_value": None,
    #             # "item_value": None,
    #         }]
    #     }
    # ]
    # result = process_test(connections)
    # print(result)
