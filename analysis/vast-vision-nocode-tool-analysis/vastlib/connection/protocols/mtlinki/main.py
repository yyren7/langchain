"""



"""
import pymongo
import time
import datetime


def try_except(data: dict, key: str, *, exception=None):
    try:
        return data[key]
    except Exception:
        return exception


# class MtlinkiConnection():
#     def __init__(self):
#         self.command = "ProductResult_History_Active"
#         self.field = "productresult_accumulate"
#         self.machine_no = "MNC-779"

#     def connection(self):
#         self.client = pymongo.MongoClient("mongodb://mtlinki:mtlinki@127.0.0.1:27017/?authMechanism=DEFAULT&authSource=MTLINKi")
#         # self.client = pymongo.MongoClient("mongodb://mtlinki:mtlinki@192.168.0.2:27017/?authMechanism=DEFAULT&authSource=MTLINKi")

#     """
#         # 最新データが先頭になるソート -> L1Nameでグルーピング -> 最初のデータ(=最新データ)を取得
#         pipeline = [{"$sort": {"_id": -1}}, {"$group": {"_id": "$L1Name", "latest_data": {"$first": "$$ROOT"}} }]
#         [x for x in col.aggregate(pipeline)]
#     """

#     def find_data(self):
#         """
#             input: ProductResult_History_Active, L1Name, productname, updatedate, productresult_accumulate
#             output: ProductResult_History_Active, L1Name, productname, updatedate, productresult_accumulate
#             # product serial: ProductResult_History_Active, L1Name, productname, updatedate, productserialnumber
#             plan time: L1Signal_Pool_Active, PowOnTime(default false)
#             actual time: L1Signal_Pool_Active, RunTime(default false)
#             # actual time: L1Signal_Pool_Active, CutTime(default false)

#             cycle time: ProductResult_History L1Name, productname, timespan
#             standard ct: manual?
#             target output: ProductPlan_History L1Name, productname, productplan, updatedate
#             target ct: manual?
#             ng count: manual?
#             product model: ProductResult_History_Active, productname
#             product model: L1Signal_Pool_Active, ProductName

#             run trigger: L1_Pool_Opened L1Name, updatedate, signalname='condition', value = START
#             error trigger: Alarm_History L1Name, number, message, updatedate/enddate, level=4
#             error item: Alarm_History L1Name, number, message, updatedate/enddate, level=4
#             # emergency trigger: Alarm_History L1Name, number, message, updatedate/enddate, level=4
#             # emergency item: Alarm_History L1Name, number, message, updatedate/enddate, level=4
#             warning trigger: Alarm_History L1Name, number, message, updatedate/enddate, level=2
#             warning item: Alarm_History L1Name, number, message, updatedate/enddate, level=2

#             status: L1_Pool_Opened L1Name, updatedate, signalname='condition', value(機械切断(通信切断?), collector停止時はnull)
#             # status: L1Signal_Pool_Active, signalname -> OPERATE, STOP, WARNING, ALARM, EMERGENCY, SUSPEND, MANUAL, WARMUP, DISCONNECT

#             manual work ct: manual
#             manual work output: manual
#         """

#         # 生産履歴 アクティブ
#         if self.command == "ProductResult_History_Active":
#             """
#                 EX:
#                     ('_id': ObjectId('660b6314cc6b3e2988772b8c'),
#                     'L1Name': 'MNC-779',
#                     'productname': 'D01_CF1,2_CP_EMW01 23001',
#                     'updatedate': datetime.datetime(2024, 4, 2, 1, 44, 51, 500000),
#                     'productresult': 0,
#                     'productresult_accumulate': 80,
#                     'enddate': None,
#                     'timespan': 0.0,
#                     'resultflag': True,
#                     'productserialnumber': None
#             """
#             results = [
#                 x for x in self.client.MTLINKi.ProductResult_History_Active.find_one(
#                     filter={"L1Name": self.machine_no},
#                     sort=[("updatedate", pymongo.DESCENDING)]
#                 ).limit(1)
#             ]
#             for result in results:
#                 return result[self.field]

#         # アラーム履歴 アクティブ
#         if self.command == "Alarm_History":
#             """
#                 アラーム履歴情報を管理します。
#                 発生期間、時間、各種情報を保持します。
#                 発生中の場合は終了時刻・発生時間がありません
#                 EX:
#                     ('_id': ObjectId('660b6314cc6b3e2988772b8c'),
#                     'L1Name': 'MNC-780',
#                     'L0Name': 'MNC-780',
#                     'number': '1003',
#                     'updatedate': datetime.datetime(2024, 4, 2, 1, 44, 7),
#                     'message': 'EMERGENCY STOP.',
#                     'enddate': datetime.datetime(2024, 4, 2, 1, 45, 12, 500000),
#                     'level': 4,
#                     'type': 'EX',
#                     'timespan': 65.5,
#             """
#             results = [
#                 x for x in self.client.MTLINKi.Alarm_History.find_one(
#                     filter={"L1Name": self.machine_no},
#                     sort=[("updatedate", pymongo.DESCENDING)]
#                 ).limit(1)
#             ]

#             for result in results:
#                 start_time = result["updatedate"]
#                 message = result["message"]

#                 if not result["enddate"]:
#                     end_time = datetime.datetime.now()
#                     timespan = end_time - start_time
#                 else:
#                     end_time = result["endtime"]
#                     timespan = result["timespan"]   # unit: second

#         if self.command == "Program_History":
#             results = [
#                 x for x in self.client.MTLINKi.Program_History.find_one(
#                     filter={"L1Name": self.machine_no},
#                     sort=[("updatedate", pymongo.DESCENDING)]
#                 ).limit(1)
#             ]
#             # TODO 発生中->enddate, timespan = None
#             """
#                 '_id': ObjectId('660b62e7cc6b3e2988772ad0'),
#                 'L1Name': 'MNC-779',
#                 'L0Name': 'MNC-779',
#                 'path': 'path1',
#                 'updatedate': datetime.datetime(2024, 4, 2, 1, 44, 7),
#                 'mainprogflg': False,
#                 'mainprog': '//CNC_MEM/USER/PATH1/O5000',
#                 'runningprog': '//CNC_MEM/USER/PATH1/O5000',
#                 'enddate': datetime.datetime(2024, 4, 2, 1, 44, 51, 500000),
#                 'timespan': 44.5
#             """

#         if self.command == "L1Signal_Pool_Active":
#             results = [
#                 x for x in self.client.MTLINKi.L1Signal_Pool_Active.find_one(
#                     filter={"L1Name": self.machine_no},
#                     sort=[("updatedate", pymongo.DESCENDING)]
#                 ).limit(1)
#             ]

#             """
#                 L1Signal_Pool_Active
#                 {'_id': ObjectId('660b6329cc6b3e2988772edc'),
#                 'L1Name': 'MNC-784',
#                 'updatedate': datetime.datetime(2024, 4, 2, 1, 45, 12, 500000),
#                 'enddate': None,
#                 'timespan': 0.0,
#                 'signalname': 'RadFan2SpindleAmpStatus_0_path1_MNC-784',
#                 # => signalname
#                         => "RunTime_path1_MNC-784" -> value = 運転時間の積算値(float)
#                         => "SigOP_path1_MNC-784" -> value = 自動運転中信号(boolean)


#                 'value': None,
#                 'filter': None,
#                 'TypeID': None,
#                 'Judge': None,
#                 'Error': None,
#                 'Warning': None},
#             """
def extract_arguments(data):
    keys = {}
    for entry in data:
        if entry.get("arguments"):
            for key, value in entry["arguments"].items():
                if key not in keys:
                    keys[key] = f"${key}"
    return keys


def create_pipeline(argument_keys):
    group_id = {key: value for key, value in argument_keys.items()}
    group_id["L1Name"] = "$L1Name"  # L1Nameを必ず追加
    pipeline = [
        {"$sort": {"_id": -1}},
        {
            "$group": {
                "_id": group_id,
                "latest_data": {"$first": "$$ROOT"}
            }
        }
    ]
    return pipeline


def main(connection):
    from collections import defaultdict
    # コマンド毎にデータを再リスト化
    command_datalist = defaultdict(list)
    for data in connection["data"]:
        command_datalist[data["command"]].append(data)
    print(command_datalist)

    username = try_except(connection["controller"]["attributes"], key="username", exception="")
    password = try_except(connection["controller"]["attributes"], key="password", exception="")
    hostname = try_except(connection["network"], key="ip_address", exception="")
    port = try_except(connection["network"], key="port", exception="")
    _auth_mechanism = try_except(connection["controller"]["attributes"], key="auth_mechanism", exception="")
    if _auth_mechanism != "":
        auth_mechanism = f"authMechanism={_auth_mechanism}"
    else:
        auth_mechanism = ""
    _auth_source = try_except(connection["controller"]["attributes"], key="auth_source", exception="")
    if _auth_source != "":
        if _auth_mechanism == "":
            auth_source = f"authSource={_auth_source}"
        else:
            auth_source = f"&authSource={_auth_source}"
    else:
        auth_source = ""

    print(f"Connection: mongodb://{username}:{password}@{hostname}:{port}/?{auth_mechanism}{auth_source}")
    # client = pymongo.MongoClient(f"mongodb://{username}:{password}@{hostname}:{port}/?authMechanism=DEFAULT&authSource=MTLINKi")
    client = pymongo.MongoClient(f"mongodb://{username}:{password}@{hostname}:{port}/?{auth_mechanism}{auth_source}")
    db = client.MTLINKi
    print(db)

    # TODO signalnameがあるとき、latest_dataはsignalnameの値が指定の値になっている最終データを取得する必要がある
    # pipeline = [{"$sort": {"_id": -1}}, {"$group": {"_id": "$L1Name", "latest_data": {"$first": "$$ROOT"}}}]

    result = []
    with pymongo.timeout(5):
        try:
            print(f"PIPE: {command_datalist}")
            if len(command_datalist) == 0:
                client.admin.command('ping')

            for cmd_k, data_list in command_datalist.items():
                # argumentsのキーと$付きのキーを抽出
                argument_keys = extract_arguments(data_list)

                # パイプラインの生成
                pipeline = create_pipeline(argument_keys)

                agg_result = None
                if cmd_k == "ProductResult_History_Active":
                    agg_result = [x for x in db.ProductResult_History_Active.aggregate(pipeline)]

                elif cmd_k == "ProductResult_History":
                    agg_result = [x for x in db.ProductResult_History.aggregate(pipeline)]

                elif cmd_k == "L1Signal_Pool_Active":
                    agg_result = [x for x in db.L1Signal_Pool_Active.aggregate(pipeline)]

                elif cmd_k == "L1_Pool_Opened":
                    agg_result = [x for x in db.L1_Pool_Opened.aggregate(pipeline)]

                elif cmd_k == "Alarm_History":
                    agg_result = [x for x in db.Alarm_History.aggregate(pipeline)]

                # argumentsがあれば合致チェック
                if agg_result is None:
                    result.extend(data_list)
                else:
                    for item in data_list:
                        arguments = item.get("arguments", {})

                        for res in agg_result:
                            if res["_id"]["L1Name"] == item.get("machine_no"):
                                if arguments is None:
                                    field_key = item.get("field")
                                    item["response"] = res["latest_data"].get(field_key)
                                    print(f"arguments: {arguments}, ITEM {item}")
                                    result.append(item)
                                    break
                                else:
                                    if all(arguments.get(key) in res["_id"][key] for key in arguments):
                                        field_key = item.get("field")
                                        item["response"] = res["latest_data"].get(field_key)
                                        print(f"arguments: {arguments}, ITEM {item}")
                                        result.append(item)
                                        break
                        else:
                            result.append(item)

        except Exception as e:
            print(e)
            return {
                "data_list": result,
                "error": str(e)
            }
        else:
            print(result)
            return {
                "data_list": result,
                "error": None
            }


if __name__ == "__main__":
    connection = {
        "network": {
            # "ip_address": "192.168.100.1",
            "ip_address": "localhost",
            # "ip_address": "mongodb",
            "port": 27017,
        },
        "controller": {
            "controller_type": "PC",
            "manufacturer": "FANUC",
            "series": "30i",
            "protocol": "MT-LINKi",
            "attributes": {
                # "auth_source": "MTLINKi",
                "auth_source": "",
                "username": "mtlinki",
                "password": "mtlinki"
            }
        },
        "data": [
            {
                "machine_id": 1,
                "machine_no": "MNC-827",
                "group": "count",
                "datatype": "Product Model",
                "command": "ProductResult_History_Active",
                "field": "productname",
                "trigger_value": None,
                "item_value": None,
                "arguments": None
            },
            {
                "machine_id": 1,
                "machine_no": "MNC-827",
                "group": "count",
                'datatype': "Actial Time",
                "command": "L1Signal_Pool_Active",
                "field": "value",
                "trigger_value": None,
                "item_value": None,
                "arguments": {
                    "signalname": "RunTime"
                }
            },
            {
                "machine_id": 1,
                "machine_no": "MNC-827",
                "group": "count",
                'datatype': "Plan Time",
                "command": "L1Signal_Pool_Active",
                "field": "value",
                "trigger_value": None,
                "item_value": None,
                "arguments": {
                    "signalname": "PowOnTime"
                }
            },
            {
                "machine_id": 1,
                "machine_no": "MNC-828",
                "group": "count",
                'datatype': "Actial Time",
                "command": "L1Signal_Pool_Active",
                "field": "value",
                "trigger_value": None,
                "item_value": None,
                "arguments": {
                    "signalname": "RunTime"
                }
            },
            {
                "machine_id": 1,
                "machine_no": "MNC-8285",
                "group": "count",
                'datatype': "Actial Time",
                "command": "L1Signal_Pool_Active",
                "field": "value",
                "trigger_value": None,
                "item_value": None,
                "arguments": {
                    "signalname": "AAAA"
                }
            },
            {
                "machine_id": 1,
                "machine_no": "MNC-835",
                "group": "count",
                'datatype': "Actial Time",
                "command": "L1Signal_Pool_Active",
                "field": "value",
                "trigger_value": None,
                "item_value": None,
                "arguments": {
                    "signalname": "RunTime"
                }
            },
            # {
                # "machine_id": 1,
                # "machine_no": "MNC-801",
                # "group": "count",
                # "datatype": "output",
                # "command": "ProductResult_History_Active",
                # "field": "productresult_accumulate",
                # "trigger_value": None,
                # "item_value": None,
                # "attributes": {
                #     # "number": 2
                # }
            # },
                # }, {
                #     "machine_id": 2,
                #     "machine_no": "MNC-800",
                #     "group": "count",
                #     "datatype": "input",
                #     "command": "ProductResult_History_Active",
                #     "field": "productresult_accumulate",
                #     "trigger_value": None,
                #     "item_value": None,
                #     "attributes": {
                #         "number": 3
                #     }
                # }, {
                #     "machine_id": 2,
                #     "machine_no": "MNC-800",
                #     "group": "count",
                #     "datatype": "output",
                #     "command": "ProductResult_History_Active",
                #     "field": "productresult_accumulate",
                #     "trigger_value": None,
                #     "item_value": None,
                #     "attributes": {
                #         "number": 4
                #     }
        ]
    }

    # {
    #     "network": {
    #         "ip_address": "0.0.0.1",
    #         "port": 27017,
    #     },
    #     "controller": {
    #         "controller_type": "PC",
    #         "manufacturer": "FANUC",
    #         "series": "30i",
    #         "protocol": "MT-LINKi",
    #         "attributes": {
    #             "auth_source": "MTLINKi",
    #             "username": "mtlinki",
    #             "password": "password"
    #         }
    #     },
    #     "data": [
    #         {
    #             "machine_id": 11,
    #             "group": "count",
    #             "datatype": "input",
    #             "command": "ProductResult_History_Active",
    #             "field": "productresult_accumulate",
    #             "trigger_value": None,
    #             "item_value": None,
    #             "attributes": {
    #                 "number": 1
    #             }
    #         }, {
    #             "machine_id": 11,
    #             "group": "count",
    #             "datatype": "output",
    #             "command": "ProductResult_History_Active",
    #             "field": "productresult_accumulate",
    #             "trigger_value": None,
    #             "item_value": None,
    #             "attributes": {
    #                 "number": 2
    #             }
    #         }, {
    #             "machine_id": 12,
    #             "group": "count",
    #             "datatype": "input",
    #             "command": "ProductResult_History_Active",
    #             "field": "productresult_accumulate",
    #             "trigger_value": None,
    #             "item_value": None,
    #             "attributes": {
    #                 "number": 3
    #             }
    #         }, {
    #             "machine_id": 12,
    #             "group": "count",
    #             "datatype": "output",
    #             "command": "ProductResult_History_Active",
    #             "field": "productresult_accumulate",
    #             "trigger_value": None,
    #             "item_value": None,
    #             "attributes": {
    #                 "number": 4
    #             }
    #         },
    #     ]
    # },

    datalist = main(connection)
    print(datalist)

