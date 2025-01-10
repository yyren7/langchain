import socket
import re
import os
import sys
import struct
import binascii
import itertools
import random
from pydantic import BaseModel
import psutil
from typing import Pattern

try:
    import devices
except Exception:
    try:
        from . import devices
    except Exception:
        try:
            from slmp import devices
        except Exception:
            try:
                from protocols.fins import devices
            except Exception:
                try:
                    from connection.protocols.fins import devices
                except Exception:
                    from src.connection.protocols.fins import devices


class Device(BaseModel):
    symbol: str = "DM"
    name: str = "Data memory"
    notation: str = "10"
    binary: int = 0x82
    offset: int = 0
    data_unit: str = "word"
    datarange: list = ["0", "32767"]


def find_device(symbol: str, *,
                manufacturer="omron",
                series="NJ",
                identify: str = "word") -> dict:

    if "omron" in manufacturer.lower():
        manufacturer = "omron"
        if "cv" in series.lower():
            series = "cv"
        if "cvm1" in series.lower():
            series = "cvm1"

    device_info = devices.device_list(manufacturer, series=series)

    return next(filter(lambda x: x["symbol"] == symbol, device_info["devices"]), None)
    # devices = [
    #     # {"symbol": "DM", "binary": 0x02, "identify": "bit",
    #     #     "decimal": "10", "name": "Data memory", "range": ["0.0", "32767.15"]},
    #     # {"symbol": "CIO", "binary": 0x30, "identify": "bit",
    #     #     "decimal": "10.16", "name": "Chanel I/O", "range": ["0.0", "6143.15"]},
    #     {"symbol": "CIO", "binary": 0xB0, "identify": "word",
    #         "decimal": "10", "name": "Chanel I/O", "range": ["0.0", "6143.15"]},

    #     {"symbol": "WR", "binary": 0xB1, "identify": "word",
    #         "decimal": "10", "name": "Internal auxiliary relay", "range": ["0", "511"]},
    #     {"symbol": "HR", "binary": 0xB2, "identify": "word",
    #         "decimal": "10", "name": "Holding relay", "range": ["0", "511"]},
    #     {"symbol": "AR", "binary": 0xB3, "identify": "word",
    #         "decimal": "10", "name": "Special auxiliary relay", "range": ["0", "447"]},

    #     {"symbol": "DR", "binary": 0xBC, "identify": "word",
    #         "decimal": "10", "name": "Data register", "range": ["0", "15"]},
    #     {"symbol": "DM", "binary": 0x82, "identify": "word",
    #         "decimal": "10", "name": "Data memory", "range": ["0", "32767"]},
    # ]
    # return next(filter(lambda x: x["symbol"].upper() == symbol.upper(), devices), None)


def flatten(data):
    return [element
            for item in data
            for element in (flatten(item) if hasattr(item, '__iter__') and not isinstance(item, str) and not isinstance(item, dict) else (item, ))]


def try_except(data: dict, key: str, *, exception=None):
    try:
        return data[key]
    except Exception:
        return exception


def try_integer(data: str, *, notation=10, exception="default"):
    try:
        return int(data, notation)
    except Exception:
        if exception == "default":
            return data
        else:
            return exception


def int_to_binary(n: int, bits: int = 16) -> str:
    """intを2進数に変換"""
    return ''.join([str(n >> i & 1) for i in reversed(range(0, bits))])


def reverse_bytes(message: bytes):
    return b"".join([int2byte_str(x, byte_len=1) for x in list(reversed([x for x in message]))])


def byte_str2int(message: bytes, *, byteorder="little", signed=False):
    return int.from_bytes(message, byteorder=byteorder, signed=signed)


def int2byte_str(number: int, *, byte_len: int = None, byteorder="little"):
    if byte_len is None:
        byte_len = (number.bit_length() + 7) // 8
    return number.to_bytes(byte_len, byteorder)


# 任意の進数表記のアドレスを10進数数値に変換
def convert_decimal_notation_to_integer(address: str, notation: str) -> int:
    """
        任意の進数表記のアドレスを10進数数値に変換
    """
    if notation == "10":
        # ex: "1234" -> 1234
        return int(address, 10)
    elif notation in ["16", "F"]:
        # ex: "1234"(16) -> 4660
        return int(address, 16)

    elif notation == "108":
        # ex: "1234"(8) -> 668
        return int(address, 8)
    elif notation == "1016":
        # ex: "1210" -> "12"(10)*16 + "10"(16) -> 192 + 16 -> 208
        return int(address[:-2], 10) * 16 + int(address[-2:], 10)
    elif notation == "10F":
        # ex: "12A" -> "12"(10)*16 + "A"(16) -> 192 + 10 -> 202
        return int(address[:-1], 10) * 16 + int(address[-1:], 16)
    elif notation == "108":
        # ex: "127"(8) -> "12"(10)*8 + "7"(8) -> 96 + 7 -> 103
        return int(address[:-1], 10) * 8 + int(address[-1:], 8)
    else:
        raise ValueError(f"Notation {notation} is not supported")


def check_error_code(message, *, transport_layer: str = None):
    # TCP
    if transport_layer in ["tcp"]:
        tcp_command_code = byte_str2int(message[8:12])
        tcp_error_code = byte_str2int(message[12:16])

        exit_code = byte_str2int(message[36:38])
        # tcp_command_code = 0x00000002のときチェック不要
        if tcp_command_code != 2:
            if tcp_error_code != 0:
                response = {
                    "code": tcp_error_code,
                    "message": f"TCP error code: {tcp_error_code}"
                }

        # Bit7, Bit8はPLC本体の異常(バッテリ異常など)のため無視
        if exit_code not in [0, 64, 128]:
            response = {
                "code": exit_code
            }
        else:
            response = {
                "code": 0,
            }
    # UDP
    elif transport_layer in ["udp"]:
        exit_code = byte_str2int(message[12:14])    # Bit7, Bit8はPLC本体の異常(バッテリ異常など)のため無視
        if exit_code not in [0, 64, 128]:
            response = {
                "code": exit_code,
            }
        else:
            response = {
                "code": 0,
            }

    return response


def get_host_fourth_octet(ip_address, port):
    def get_local_ip(ip_address, port):
        from socket import socket, AF_INET, SOCK_DGRAM
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            s.connect((ip_address, port))
            ipaddr = s.getsockname()[0]
        except Exception:
            ipaddr = '127.0.0.1'
        finally:
            s.close()
        return ipaddr

    # Windows OS
    if os.name == "nt":
        iplist = socket.gethostbyname_ex(socket.gethostname())[2]
    # Mac OS or Linux OS
    else:
        iplist = []
        address_list = psutil.net_if_addrs()
        for _ in address_list.keys():
            local_ip = get_local_ip(ip_address, port)
            iplist.append(local_ip)

    same_network = ip_address.rsplit('.', 1)[0]
    if len(iplist) > 0:
        try:
            client_ip = [x for x in iplist if same_network in x]
            fourth_octet = int(client_ip[0].rsplit('.', 1)[1])
        except Exception as e:
            print(
                '{}:{}, {}, {}'.format(
                    sys._getframe().f_code.co_name, e, same_network, 'No connection found. Please check your communication settings.'))
            fourth_octet = int(iplist[0].rsplit('.', 1)[1])
    else:
        fourth_octet = None
    return fourth_octet


class Configure(BaseModel):
    ip_address: str = "127.0.0.1"
    port: int = 0
    type: str = "PLC"
    manufacturer: str = "Omron"
    series: str = "NJ"
    protocol: str = "FINS/UDP"
    attributes: dict = {}
    read_data: dict = {
        "word": [],
        "doubleword": [],
        "bulk": [],
    }
    write_data: dict = {
        "bit": [],
        "word": [],
        "doubleword": [],
        "string": [],
        "bulk": []
    }


class Regexes(BaseModel):
    bit: Pattern = re.compile(r"(bit|boolean)")
    word: Pattern = re.compile(r"(word|short)")
    dword: Pattern = re.compile(r"(dword|doubleword|integer)")
    string: Pattern = re.compile(r"string")
    fraction: Pattern = re.compile(r"\.")
    signed: Pattern = re.compile(r"(\-|\±|s_|signed_)")
    tcp: Pattern = re.compile(r"tcp", flags=re.IGNORECASE)
    udp: Pattern = re.compile(r"udp", flags=re.IGNORECASE)


class Communication():
    def __init__(self, configure: dict):
        """
            Parameters
            ----------
            configure: dict
                network: dict
                    ip_address: str
                        IPアドレス
                    port: int
                        ポート番号
                controller: dict
                    type: str
                        コントローラ種別
                    manufacturer: str
                        コントローラのメーカ名
                    series: str
                        コントローラのシリーズ
                    protocol: str
                        使用プロトコル名
                    attribute: dict
                        その他オプション
                data: list in dict
                    データ毎の設定
        """
        self.regexes = Regexes()
        self.base_param = {
            "tcp_header": [0x46, 0x49, 0x4E, 0x53],     # 固定値 "FINS"
            "tcp_node_command": [0x00, 0x00, 0x00, 0x00],
            "tcp_command": [0x00, 0x00, 0x00, 0x02],
            "tcp_error_code": [0x00, 0x00, 0x00, 0x00],
            "tcp_client_node": [0x00, 0x00, 0x00, 0x00],

            "icf": [0x80],
            "rsv": [0x00],
            "gct": [0x02],      # 許容ブリッジ通過数 基本的に0x02
            "dna": [0x00],      # 相手先ネットワークアドレス 0x00: 同一ネットワーク, 0x01-7F: 他相手先ネットワーク
            "da1": [0x00],      # 相手先ノードアドレス 0x00: 自PLC, 0x01-20: Controller Link, 0x01-FE: Ethernet, 0xFF: 一斉同報
            "da2": [0x00],      # 0x00: CPUユニット,
            "sna": [0x00],      # 発信元ネットワークアドレス 0x00: 同一ネットワーク, 0x01-7F: 他ネットワーク

            "sa2": [0x00],      # 発信元号機アドレス 0x00: CPU固定値
        }
        network = try_except(configure, "network")
        controller = try_except(configure, "controller")
        self.conf = Configure(**network, **controller)
        self.data = try_except(configure, "data")

        self.request_messages = []

    def identification_unit(self):
        for data in self.data:
            if data["data_unit"]:
                # doubleword random read
                if ((self.regexes.dword.search(data["data_unit"]))):
                    self.conf.read_data["doubleword"].append(data)
                # word random read
                elif ((self.regexes.bit.search(data["data_unit"])) or (self.regexes.word.search(data["data_unit"]))):
                    self.conf.read_data["word"].append(data)
                # bulk read
                else:
                    self.conf.read_data["bulk"].append(data)
        return self.conf.read_data

    def set_request_node_address(self):
        tcp_data_length = [0x00, 0x00, 0x00, 0x0C]
        _message = [
            self.base_param["tcp_header"],
            tcp_data_length,
            self.base_param["tcp_node_command"],
            self.base_param["tcp_error_code"],
            self.base_param["tcp_client_node"],
        ]
        self.node_telegram = b""
        for x in flatten(_message):
            self.node_telegram = self.node_telegram + struct.pack("B", x)
        return self.node_telegram

    def divided_response_node(self, *, message):
        self.client_node = int("0x" + message[32:40], 16)
        self.server_node = int("0x" + message[40:48], 16)
        return {
            "client_node": self.client_node,
            "server_node": self.server_node
        }

    def device_code_address_encode(self, device: str, address, *, random_doubleword: bool = False) -> bytearray:
        """
            Return
                bytearray: [device_code(1byte), decimal part address(2byte), fractional part "0x00"(1byte)]
        """
        found_device = find_device(symbol=device, series=self.conf.series)
        decimal_notation = try_except(found_device, "decimal")
        device_code = try_except(found_device, "binary")
        if isinstance(address, str):
            address_integer = convert_decimal_notation_to_integer(address, decimal_notation)
        else:
            address_integer = address

        if random_doubleword:
            address = [int(x, 16) for x in re.findall("..", f"{address_integer:04x}")]
            d_address_integer = address_integer + 1
            d_address = [int(x, 16) for x in re.findall("..", f"{d_address_integer:04x}")]
            return bytearray(flatten([device_code, address, 0x00, device_code, d_address, 0x00]))
        else:
            address = [int(x, 16) for x in re.findall("..", f"{address_integer:04x}")]
            return bytearray(flatten([device_code, address, 0x00]))

    # Bulk read
    def set_request_message_bulk_read(self, *, node_data=None):
        # TODO TCP
        if self.regexes.tcp.search(self.conf.protocol):
            tcp_header = self.base_param["tcp_header"]
            tcp_command = self.base_param["tcp_command"]
            tcp_error_code = self.base_param["tcp_error_code"]
            if node_data:
                da1 = node_data["server_node"]
                sa1 = node_data["client_node"]
            else:
                da1 = self.server_node
                sa1 = self.client_node

            _base_request_message = [
                self.base_param["tcp_header"],
                # data length
                self.base_param["tcp_command"],
                self.base_param["tcp_error_code"],
                # client node address
                self.base_param["icf"],
                self.base_param["rsv"],
                self.base_param["gct"],
                self.base_param["dna"],
                da1,
                self.base_param["da2"],
                self.base_param["sna"],
                sa1,
                self.base_param["sa2"],
            ]

        elif self.regexes.udp.search(self.conf.protocol):
            da1 = [0x00]
            sa1 = get_host_fourth_octet(self.conf.ip_address, self.conf.port)
            _base_request_message = [
                self.base_param["icf"],
                self.base_param["rsv"],
                self.base_param["gct"],
                self.base_param["dna"],
                da1,
                self.base_param["da2"],
                self.base_param["sna"],
                sa1,
                self.base_param["sa2"],
            ]

        command = [0x01, 0x01]
        max_access_count = 498

        bulk_datas = self.conf.read_data["bulk"]
        each_device_data = {}
        for _data in bulk_datas:
            try:
                each_device_data[_data["device"]].append(_data)
            except Exception:
                each_device_data[_data["device"]] = [_data]

        for key, values in each_device_data.items():
            found_device = find_device(symbol=key, series=self.conf.series)
            decimal_notation = try_except(found_device, "decimal")

            min_value = min(
                [convert_decimal_notation_to_integer(x["address"].split(".")[0], decimal_notation) for x in values])

            max_value = max(
                [convert_decimal_notation_to_integer(x["address"].split(".")[0], decimal_notation) + int(try_except(x, key="data_length", exception="256")) for x in values])
            _request = {
                "min": min_value,
                "max": max_value
            }

            for i in range(((max_value - min_value) // max_access_count) + 1):
                _min_value = min_value + (max_access_count * i)
                _max_value = min_value + (max_access_count * (i + 1))
                if _max_value < max_value:
                    _request.update(split_min=_min_value, split_max=_max_value)
                else:
                    _request.update(split_min=_min_value, split_max=max_value)
                _request.update(device=key, count=_request["split_max"] - _request["split_min"])

                device_first_address = self.device_code_address_encode(key, _request['split_min'])

                address_count = bytearray(flatten(
                    [int(x, 16) for x in re.findall("..", f"{_request['count']:04x}")]))
                sid = random.randrange(0, 255, 1)

                message = bytearray([x for x in flatten(_base_request_message + [sid, command])]) + device_first_address + address_count
                self.request_messages.append({**_request, "message": message, "command": "bulk_read", "sid": sid})

        return self.request_messages

    # Random read
    def set_request_message_randam_read(self, *, node_data=None):
        # TODO TCP
        if self.regexes.tcp.search(self.conf.protocol):
            tcp_header = self.base_param["tcp_header"]
            tcp_command = self.base_param["tcp_command"]
            tcp_error_code = self.base_param["tcp_error_code"]
            if node_data:
                da1 = node_data["server_node"]
                sa1 = node_data["client_node"]
            else:
                da1 = self.server_node
                sa1 = self.client_node

            _base_request_message = [
                self.base_param["tcp_header"],
                # data length
                self.base_param["tcp_command"],
                self.base_param["tcp_error_code"],
                # client node address
                self.base_param["icf"],
                self.base_param["rsv"],
                self.base_param["gct"],
                self.base_param["dna"],
                da1,
                self.base_param["da2"],
                self.base_param["sna"],
                sa1,
                self.base_param["sa2"],
            ]

        elif self.regexes.udp.search(self.conf.protocol):
            da1 = [0x00]
            sa1 = get_host_fourth_octet(self.conf.ip_address, self.conf.port)
            _base_request_message = [
                self.base_param["icf"],
                self.base_param["rsv"],
                self.base_param["gct"],
                self.base_param["dna"],
                da1,
                self.base_param["da2"],
                self.base_param["sna"],
                sa1,
                self.base_param["sa2"],
            ]

        command = [0x01, 0x04]

        max_access_count = 165

        request_datas = []
        _message = b""
        word_datas = self.conf.read_data["word"]
        doubleword_datas = self.conf.read_data["doubleword"]
        word_data_count = 0
        doubleword_data_count = 0
        for data in word_datas:
            # over max_access_count more than data_count(word_datas)
            if word_data_count >= max_access_count:
                request_datas.append({
                    "message": _message,
                    "word_count": word_data_count,
                    "doubleword_count": doubleword_data_count,
                })
                word_data_count = 0
                _message = b""

            word_data_count = word_data_count + 1
            device = data["device"]
            address = data["address"].split(".")[0]
            _message = _message + self.device_code_address_encode(device, address)

        for data in doubleword_datas:
            # over max_access_count more than data_count(remain word_datas + double_datas)
            if (word_data_count + doubleword_data_count * 2) - 1 >= max_access_count:
                request_datas.append({
                    "message": _message,
                    "word_count": word_data_count,
                    "double_count": doubleword_data_count,
                })
                _message = b""
                word_data_count = 0
                doubleword_data_count = 0

            doubleword_data_count = doubleword_data_count + 1
            device = data["device"]
            address = data["address"].split(".")[0]
            _message = _message + self.device_code_address_encode(device, address, random_doubleword=True)

        if _message:
            request_datas.append({
                "message": _message,
                "word_count": word_data_count,
                "double_count": doubleword_data_count,
            })

        for data in request_datas:
            sid = random.randrange(0, 255, 1)
            message = bytearray([x for x in flatten(_base_request_message + [sid, command])]) + data["message"]
            self.request_messages.append({
                **data,
                "message": message,
                "command": "random_read",
                "sid": sid,
            })

        return self.request_messages

    def set_connection(self, *, transport_layer: str = None, timeout=10):
        if transport_layer is None:
            if self.regexes.tcp.search(self.conf.protocol):
                transport_layer = "tcp"
            elif self.regexes.udp.search(self.conf.protocol):
                transport_layer = "udp"
            else:
                raise ValueError(f"This protocol: {self.conf.protocol} is unsupported.")

        if transport_layer in ["tcp"]:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.transport_layer = "tcp"
        elif transport_layer in ["udp"]:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.transport_layer = "udp"
        else:
            raise ValueError(f"This protocol: {self.conf.protocol} is unsupported.")
        self.sock.settimeout(timeout)

    def open(self, *, ip_address: str = None, port: int = None):
        if ip_address is None:
            ip_address = self.conf.ip_address
        if port is None:
            port = self.conf.port
        print(f"ip_address: {ip_address}, port: {port}")
        self.sock.connect((ip_address, port))

    def connection(self, *, request_messages: list = None) -> dict:
        def retry_recieve(send_sid, *, retry_count: int = 0, max_retry_count: int = 2):
            recieve_message = self.sock.recv(1024)

            # check sid match
            recv_sid = recieve_message[10:12]
            if send_sid != recv_sid:
                if retry_count < max_retry_count:
                    recieve_message = retry_recieve(send_sid, retry_count=retry_count + 1, max_retry_count=max_retry_count)
                else:
                    raise ConnectionError("Sid mismatch")
            return recieve_message

        if request_messages is None:
            request_messages = self.request_messages

        self.responses = []
        connection_check = True
        for request in request_messages:
            response = {"request": request}
            if connection_check is False:
                response.update(connection={
                    "recieve_message": None,
                    "code": 10060,
                    "message": "Connection Error (skip)"
                })
            else:
                if isinstance(request, dict):
                    request_message = try_except(request, key="message", exception=request)
                else:
                    request_message = request
                send_sid = request_message[10:12]

                self.sock.send(request_message)
                # print(f"request_message: {request_message}")
                try:
                    recieve_message = retry_recieve(send_sid)
                    # print(recieve_message.hex())

                    response.update(connection={
                        "request_message": request_message.hex(),
                        "recieve_message": recieve_message,
                        "code": 0,
                        "message": "success"
                    })
                except Exception as e:
                    print(f"Error: {e}")
                    connection_check = False

                    response.update(connection={
                        "request_message": request_message.hex(),
                        "recieve_message": None,
                        "code": 10060,
                        "message": str(e)
                    })

            self.responses.append(response)
        return self.responses

    def close(self):
        try:
            self.sock.close()
        except Exception:
            print("Already closed")

    def divided_response_common(self, metainfo: dict) -> dict:
        """
            Argument:
                metainfo: dict
            Keyargument:
                ascii_mode: bool -> flag of ascii or binary, default is None = binary mode.
            Return:
                code: str -> error code
                judge: str -> result
                message: str -> error details
                response: str -> extraction data part from response message
        """
        message = metainfo["connection"]["recieve_message"]

        # error check and extact data part
        if self.regexes.tcp.search(self.conf.protocol):
            check_result = check_error_code(message, transport_layer="tcp")
            message_data_index = 38
        elif self.regexes.udp.search(self.conf.protocol):
            check_result = check_error_code(message, transport_layer="udp")
            message_data_index = 14
        else:
            raise ValueError(f"Not supported protocol: {self.conf.protocol}")

        finish_code = try_integer(check_result["code"], notation=16)
        if finish_code == 0:
            response_data = message[message_data_index:]
            check_result.update(response=response_data)
        else:
            check_result.update(response=None)

        metainfo.update(judge=check_result)
        return metainfo

    def divided_response_random_read(self):
        checked_response = [self.divided_response_common(metainfo=x)
                        for x in self.responses
                        if x["request"]["command"] in ["random_read"] and x["connection"]["code"] == 0]
        try:
            join_response = b"".join([x["judge"]["response"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) == 0])
        except Exception:
            try:
                join_response = "".join([x["judge"]["response"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) == 0])
            except Exception:
                print(f'Random read has error_code: {[x["judge"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) != 0]}')
                join_response = None

        if join_response:
            data_length = 0
            # word data convert
            for i, data in enumerate(self.conf.read_data["word"]):
                _data = join_response[i * 3:(i + 1) * 3]
                if _data:
                    data_length = (i + 1) * 3

                    # bit data
                    if (self.regexes.bit.search(data["data_unit"])) or self.regexes.fraction.search(data["address"]):
                        _binary = list(reversed(list(int_to_binary(byte_str2int(reverse_bytes(_data[1:3]), signed=False)))))
                        try:
                            # 0~15 or 0~F なので10~15分だけ識別すれば良い
                            if data["address"].split(".")[1].isdecimal():
                                fraction_index = int(data["address"].split(".")[1], 10)
                            else:
                                fraction_index = int(data["address"].split(".")[1], 16)
                        except Exception:
                            fraction_index = 0
                        res = _binary[fraction_index]

                    # word data
                    else:
                        if (self.regexes.signed.search(data["data_unit"])):
                            res = byte_str2int(reverse_bytes(_data[1:3]), signed=True)
                        else:
                            res = byte_str2int(reverse_bytes(_data[1:3]), signed=False)
                    data.update({"value": res})

            # doubleword word data convert
            # TODO double wordで取得設定、かつBitデータ設定
            for i, data in enumerate(self.conf.read_data["doubleword"]):
                _data = join_response[data_length + (i * 6):data_length + ((i + 1) * 6)]
                if _data:
                    if (self.regexes.signed.search(data["data_unit"])):
                        res = byte_str2int(b"" + reverse_bytes(_data[1:3]) + reverse_bytes(_data[4:6]), signed=True)
                    else:
                        res = byte_str2int(b"" + reverse_bytes(_data[1:3]) + reverse_bytes(_data[4:6]))
                    data.update({"value": res})
        return {
            "metainfo": checked_response,
            "data": self.conf.read_data
        }

    def divided_response_bulk_read(self):
        # デバイス名と開始アドレスで集約
        multi_responses = [list(res) for _, res in itertools.groupby(
            [x for x in self.responses if x["request"]["command"] in ["bulk_read"] and x["connection"]["code"] == 0], lambda x: (x["request"]["device"] and x["request"]["min"]))]

        for res in multi_responses:
            checked_response = [self.divided_response_common(metainfo=x) for x in res]
            try:
                join_response = b"".join([x["judge"]["response"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) == 0])
            except Exception:
                try:
                    join_response = "".join([x["judge"]["response"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) == 0])
                except Exception:
                    print(f'Bulk read has error_code: {[x["judge"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) != 0]}')
                    join_response = None

            if join_response:
                response_min = res[0]["request"]["min"]
                response_max = res[0]["request"]["max"]

                for data in self.conf.read_data["bulk"]:
                    if res[0]["request"]["device"] == data["device"]:

                        device = find_device(symbol=data["device"], series=self.conf.series)
                        decimal_notation = device["decimal"]
                        address_integer = convert_decimal_notation_to_integer(data["address"].split(".")[0], decimal_notation)
                        address_min = address_integer - response_min

                        # string data
                        if (self.regexes.string.search(data["data_unit"])):
                            length = try_except(data, key="data_length", exception=256)
                            address_max = address_min + length if address_min + length <= response_max else response_max

                            extraction_response = join_response[address_min: address_max]
                            if len(extraction_response) % 2:
                                extraction_response + b"\x00"

                            _data = ""
                            for i in range(0, len(extraction_response), 2):
                                upper = extraction_response[i]
                                lower = extraction_response[i + 1]
                                # Little Endian
                                if lower != 0:
                                    _data = _data + chr(lower)
                                else:
                                    break
                                if upper != 0:
                                    _data = _data + chr(upper)
                                else:
                                    break
                                # TODO Big Endian
                                if upper != 0:
                                    _data = _data + chr(upper)
                                else:
                                    break
                                if lower != 0:
                                    _data = _data + chr(lower)
                                else:
                                    break

                            if _data:
                                data.update({"value": _data})

                        # double word data
                        elif (self.regexes.dword.search(data["data_unit"])):
                            length = 4
                            address_max = address_min + length if address_min + length <= response_max else response_max

                            extraction_response = join_response[address_min: address_max]
                            if len(extraction_response) % 2:
                                extraction_response + b"\x00"

                            if (self.regexes.signed.search(data["data_unit"])):
                                res = byte_str2int(b"" + reverse_bytes(extraction_response[1:3]) + reverse_bytes(extraction_response[4:6]), signed=True)
                            else:
                                res = byte_str2int(b"" + reverse_bytes(extraction_response[1:3]) + reverse_bytes(extraction_response[4:6]))
                            data.update({"value": res})

                        # bit data
                        elif (self.regexes.bit.search(data["data_unit"])) or self.regexes.fraction.search(data["address"]):
                            length = 2
                            address_max = address_min + length if address_min + length <= response_max else response_max

                            extraction_response = join_response[address_min: address_max]
                            if len(extraction_response) % 2:
                                extraction_response + b"\x00"

                            _binary = list(reversed(list(int_to_binary(byte_str2int(extraction_response[1:3], signed=False)))))
                            try:
                                if data["address"].split(".")[1].isdecimal():
                                    fraction_index = int(data["address"].split(".")[1], 10)
                                else:
                                    fraction_index = int(data["address"].split(".")[1], 16)
                            except Exception:
                                fraction_index = 0
                            res = _binary[fraction_index]
                            data.update({"value": res})

                        # word data
                        elif self.regexes.word.search(data["data_unit"]):
                            length = 2
                            address_max = address_min + length if address_min + length <= response_max else response_max

                            extraction_response = join_response[address_min: address_max]
                            if len(extraction_response) % 2:
                                extraction_response + b"\x00"

                            _binary = list(reversed(list(int_to_binary(byte_str2int(extraction_response[1:3], signed=False)))))
                            if (self.regexes.signed.search(data["data_unit"])):
                                res = byte_str2int(reverse_bytes(extraction_response[1:3]), signed=True)
                            else:
                                res = byte_str2int(reverse_bytes(extraction_response[1:3]), signed=False)
                            data.update({"value": res})

                        # return Array
                        else:
                            extraction_response = join_response[address_min: response_max]
                            if len(extraction_response) % 2:
                                extraction_response + b"\x00"

                            _data = []
                            for i in range(0, len(extraction_response), 2):
                                _data.append(byte_str2int(extraction_response[i:i + 2]))

                            if _data:
                                data.update({"value": _data})

        return {
            "metainfo": multi_responses,
            "data": self.conf.read_data
        }

    def divided_read(self):
        return (
            self.conf.read_data["word"] + self.conf.read_data["doubleword"] + self.conf.read_data["bulk"]
        )

    def extract_error_connection(self, data_list: list):
        def metalist(data_list: list):
            return flatten([try_except(x, "metainfo", exception=[]) for x in data_list])

        meta = metalist(data_list)
        return [x["judge"] for x in meta
                if try_integer(try_except(try_except(x, "connection"), "code"), notation=16) != 0 or try_integer(try_except(try_except(x, "judge"), "code"), notation=16) != 0]


if __name__ == "__main__":
    configure = {
        "network": {
            "ip_address": "192.168.0.1",
            # "ip_address": "192.168.250.1",
            "port": 9600
        },
        "controller": {
            "type": "PLC",
            "manufacturer": "Omron",
            "series": "CJ",
            # "series": "NJ101",
            "protocol": "FINS/UDP",
            "attributes": {
            }
        },
        "data": [
            # # TODO Float
            # {
            #     "execute": "read",
            #     "machine_id": 1,
            #     # "group": "count",
            #     # "datatype": "input",
            #     # "trigger_value": None,
            #     # "item_value": None,
            #     "device": "DM",
            #     "address": "1004",
            #     # "data_length": 2,
            #     # "data_unit": "+integer",
            #     "data_unit": "float",
            # },
            {
                "execute": "read",
                "machine_id": 1,
                # "group": "count",
                # "datatype": "input",
                # "trigger_value": None,
                # "item_value": None,
                "device": "DM",
                "address": "100",
                # "data_length": 2,
                # "data_unit": "+integer",
                "data_unit": "integer",
            },
            {
                "execute": "read",
                "machine_id": 1,
                # "group": "count",
                # "datatype": "input",
                # "trigger_value": None,
                # "item_value": None,
                "device": "DM",
                "address": "100.5",
                # "data_length": 2,
                # "data_unit": "+integer",
                "data_unit": "integer",
            },
            # {
            #     "execute": "read",
            #     "machine_id": 1,
            #     # "group": "count",
            #     # "datatype": "input",
            #     # "trigger_value": None,
            #     # "item_value": None,
            #     "device": "DM",
            #     "address": "1000",
            #     # "data_length": 2,
            #     # "data_unit": "+integer",
            #     "data_unit": "s_short",
            # },
            # {
            #     "execute": "read",
            #     "machine_id": 1,
            #     # "group": "count",
            #     # "datatype": "input",
            #     # "trigger_value": None,
            #     # "item_value": None,
            #     "device": "DM",
            #     "address": "1001",
            #     # "data_length": 2,
            #     # "data_unit": "+integer",
            #     "data_unit": "s_short",
            # },
            # {
            #     "execute": "read",
            #     "machine_id": 1,
            #     # "group": "count",
            #     # "datatype": "input",
            #     # "trigger_value": None,
            #     # "item_value": None,
            #     "device": "DM",
            #     "address": "1000",
            #     # "data_length": 2,
            #     # "data_unit": "+integer",
            #     "data_unit": "s_integer",
            # },
            {
                "execute": "read",
                "machine_id": 1,
                # "group": "count",
                # "datatype": "input",
                # "trigger_value": None,
                # "item_value": None,
                "device": "DM",
                "address": "100",
                # "data_length": 2,
                # "data_unit": "+integer",
                "data_unit": "-short",
            },
            {
                "execute": "read",
                "machine_id": 1,
                # "group": "count",
                # "datatype": "input",
                # "trigger_value": None,
                # "item_value": None,
                "device": "DM",
                "address": "100",
                # "data_length": 256,
                "data_unit": "string"
            },
        ]
    }
    # configure["data"].extend(
    #     [
    #         {
    #             "execute": "read",
    #             "machine_id": 1,
    #             # "group": "count",
    #             # "datatype": "input",
    #             # "trigger_value": None,
    #             # "item_value": None,
    #             "device": "DM",
    #             "address": "1000",
    #             # "data_length": 2,
    #             "data_unit": "+integer",
    #             # "data_unit": "bulk"
    #         },
    #     ] * 165
    # )

    con = Communication(configure=configure)
    con.identification_unit()
    con.set_request_message_randam_read()
    con.set_request_message_bulk_read()
    con.set_connection()
    con.open()
    result = con.connection()
    con.close()

    con.divided_response_random_read()
    con.divided_response_bulk_read()
    response = con.divided_read()
    # node = con.set_request_node_address()
    # node_result = con.connection(request_messages=[node])
    # con.divided_response_node(message=node_result)

    print(response)

