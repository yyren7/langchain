import socket
import re
import struct
import itertools
from pydantic import BaseModel
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
                from protocols.slmp import devices
            except Exception:
                try:
                    from connection.protocols.slmp import devices
                except Exception:
                    from src.connection.protocols.slmp import devices


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


# デバイスコードを一覧から検索
def find_device(symbol: str, *, manufacturer="Mitsubishi Electric", series="MELSEC iQ-R") -> dict:
    if "mitsubishi" in manufacturer.lower():
        manufacturer = "mitsubishi"
        if "r" in series.lower():
            series = "iq-r"
    if "keyence" in manufacturer.lower():
        manufacturer = "keyence"
        if "nano" in series.lower():
            series = "nano"
    if "panasonic" in manufacturer.lower():
        manufacturer = "panasonic"
    if "omron" in manufacturer.lower():
        manufacturer = "omron"

    device_info = devices.device_list(manufacturer, series=series)
    # devicelist = [
    #     {"symbol": "D", "binary": 0xA8, "ascii": "D*", "identify": "word",
    #         "decimal": "10", "name": "Data register"},
    #     {"symbol": "X", "binary": 0x9C, "ascii": "X*", "identify": "bit",
    #         "decimal": "10", "name": "Input"},
    #     {"symbol": "W", "binary": 0xB4, "ascii": "W*", "identify": "word",
    #         "decimal": "16", "name": "Link register"},
    # ]
    return next(filter(lambda x: x["symbol"] == symbol, device_info["devices"]), None)


# 補数を負の10進数に変換
def signed_hex2int(signed_hex: int, digit: int) -> int:
    """
        補数を負の10進数に変換
    """
    signed = 0x01 << (digit - 1)
    mask = 0x00
    for num in range(digit):
        mask = mask | (0x01 << num)
    signed_int = (int(signed_hex ^ mask) * - 1) - 1 if (signed_hex & signed) else int(signed_hex)
    return signed_int


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
        return try_integer(address[:-2], notation=10, exception=0) * 16 + int(address[-2:], 10)
    elif notation == "10F":
        # ex: "12A" -> "12"(10)*16 + "A"(16) -> 192 + 10 -> 202
        return try_integer(address[:-1], notation=10, exception=0) * 16 + int(address[-1:], 16)
    elif notation == "108":
        # ex: "127"(8) -> "12"(10)*8 + "7"(8) -> 96 + 7 -> 103
        return try_integer(address[:-1], notation=10, exception=0) * 8 + int(address[-1:], 8)
    else:
        raise ValueError(f"Notation {notation} is not supported")


# 10進数数値のアドレスを任意の進数表記の文字列に変換
def convert_integer_to_decimal_notation(address: str, *, notation: str = 10, prefix_count: int = 8) -> int:
    """
        10進数数値のアドレスを任意の進数表記の文字列に変換
    """
    if notation == "10":
        # ex: 1234 -> "1234"
        return str(address, 10)
    elif notation in ["16", "F"]:
        # ex: 1234 -> 0x04d2
        return f'{address:0{prefix_count}x}'
    elif notation == "108":
        return f'{address:0{prefix_count}o}'
    # TODO
    # elif notation == "1016":
    #     # ex: "1210" -> "12"(10)*16 + "10"(16) -> 192 + 16 -> 208
    #     return try_integer(address[:-2], notation=10, exception=0) * 16 + int(address[-2:], 10)
    # elif notation == "10F":
    #     # ex: "12A" -> "12"(10)*16 + "A"(16) -> 192 + 10 -> 202
    #     return try_integer(address[:-1], notation=10, exception=0) * 16 + int(address[-1:], 16)
    # elif notation == "108":
    #     # ex: "127"(8) -> "12"(10)*8 + "7"(8) -> 96 + 7 -> 103
    #     return try_integer(address[:-1], notation=10, exception=0) * 8 + int(address[-1:], 8)
    else:
        raise ValueError(f"Notation {notation} is not supported")


# エラーコードを検索
def check_error_code(code: str) -> dict:
    try:
        if int(code) == 0:
            return {
                "code": code,
                "judge": "success",
                "message": "success"
            }
        else:
            return {
                "code": code,
                "judge": "error",
                "message": "error"
            }
    except Exception:
        return {
            "code": code,
            "judge": "error",
            "message": "error"
        }


def check_error_message(message, *, code: str = None, ascii_mode: bool = False):
    if ascii_mode:
        return check_error_code(message[18:22])
    else:
        return check_error_code(message[20:22] + message[18:20])


class Configure(BaseModel):
    ip_address: str = "127.0.0.1"
    port: int = 0
    type: str = "PLC"
    manufacturer: str = "Mitsubishi Electric"
    series: str = "Q/L"
    protocol: str = "SLMP/TCP"
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
            "sub_header": [0x50, 0x00],     # 固定値 3Eフレーム
            "network_no": [0x00],           # 0: 自局, 1-239: 他局
            "pc_no": [0xFF],                # FF: 自局, 01-EF,FE: 他局
            "recipient_io": [0x03, 0xFF],   # 03FF: 自局CPU, 03D0-03D3: 制御/待機CPU, 03E0-03E3: マルチCPU, 0000-01FF: マルチドロップ接続上のC24の管理CPU
            "recipient_node": [0x00],       # 00: マルチドロップ以外, 01~1F: マルチドロップ接続上の局
            "cpu_timer": [0x00, 0x10],      # CPU監視タイマ 0: 処理完了まで待機, 1-65535: 値*250ms
        }
        network = try_except(configure, "network")
        controller = try_except(configure, "controller")
        self.conf = Configure(**network, **controller)
        self.data = try_except(configure, "data")
        self.ascii_mode = try_except(self.conf.attributes, key="encode_mode") in ["ascii", "ASCII"]

        self.request_messages = []

    def identification_unit(self):
        # Backup 2024/05/08
        # for data in self.data:
        #     # word random read
        #     if ((re.search("bit", data["data_unit"])) or (re.search("word", data["data_unit"]) and data["data_length"] == 1)):
        #         self.conf.read_data["word"].append(data)
        #     # doubleword random read
        #     elif ((re.search("doubleword", data["data_unit"])) or (re.search("word", data["data_unit"]) and data["data_length"] == 2)):
        #         self.conf.read_data["doubleword"].append(data)
        #     # bulk read
        #     else:
        #         self.conf.read_data["bulk"].append(data)

        for data in self.data:
            print(f"SLMP DATA CHECK: {data}")
            if try_except(data, key="data_unit"):
                # doubleword random read
                if ((self.regexes.dword.search(data["data_unit"]))):
                    self.conf.read_data["doubleword"].append(data)
                # word random read
                elif ((self.regexes.bit.search(data["data_unit"])) or (self.regexes.word.search(data["data_unit"]))):
                    self.conf.read_data["word"].append(data)
                # bulk read
                else:
                    self.conf.read_data["bulk"].append(data)
            else:
                pass
        return self.conf.read_data

    # bulk read
    def set_request_bulk_read(self):
        """
            一括読出しメッセージを生成する
        """
        # bulk read command set
        self.base_param.update(command=[0x04, 0x01], sub_command=[0x00, 0x00])

        bulk_data = self.conf.read_data['bulk']
        each_device_data = {}
        for data in bulk_data:
            try:
                each_device_data[data["device"]].append(data)
            except Exception:
                each_device_data[data["device"]] = [data]

        # TODO: Q/L Q3UDVCPU: 399 -> OK, 400 -> NG
        max_access_count = 399

        for key, values in each_device_data.items():
            device = find_device(symbol=key, manufacturer=self.conf.manufacturer, series=self.conf.series)
            decimal_notation = device["decimal"]

            min_value = min([
                convert_decimal_notation_to_integer(x["address"].split(".")[0], decimal_notation)
                + convert_decimal_notation_to_integer(try_except(device, key="offset", exception="0"), decimal_notation)
                for x in values
            ])
            # max_value = max([convert_decimal_notation_to_integer(x["address"].split(".")[0], decimal_notation) + int(x["data_length"]) for x in values])
            # TODO 最小のアドレス～最大のアドレス+256
            max_value = max([
                convert_decimal_notation_to_integer(x["address"].split(".")[0], decimal_notation)
                + convert_decimal_notation_to_integer(try_except(device, key="offset", exception="0"), decimal_notation)
                + 256 for x in values
            ])
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

                # ASCIIモード
                if self.ascii_mode:
                    data_count = [
                        int(x, 16) for x in re.findall("..", f"{24:04x}")]
                    request_data = [
                        self.base_param["sub_header"],
                        self.base_param["network_no"],
                        self.base_param["pc_no"],
                        self.base_param["recipient_io"],
                        self.base_param["recipient_node"],
                        data_count,
                        self.base_param["cpu_timer"],
                        self.base_param["command"],         # command
                        self.base_param["sub_command"],     # sub command
                    ]
                    device_code = device["ascii"]
                    # address = f"{_request['split_min']:06}"
                    reconvert_notation = try_except(device, "decimal_to_ascii", exception="10")
                    address = convert_integer_to_decimal_notation(_request['split_min'], notation=reconvert_notation, prefix_count=6)

                    address_count = f"{_request['count']:04}"
                    request_data = request_data + [device_code, address, address_count]
                    request_message = ""
                    for x in flatten(request_data):
                        try:
                            request_message = request_message + format(x, "02x")
                        except Exception:
                            request_message = request_message + x
                    request_message = request_message.encode('ascii')
                    # print(f"request_message ASCII: {request_message}")
                    self.request_messages.append({**_request, "message": request_message, "command": "bulk_read"})

                # Binaryモード
                else:
                    data_count = [
                        int(x, 16) for x in re.findall("..", f"{12:04x}")]

                    request_data = [
                        self.base_param["sub_header"],
                        self.base_param["network_no"],
                        self.base_param["pc_no"],
                        list(reversed(self.base_param["recipient_io"])),
                        self.base_param["recipient_node"],
                        list(reversed(data_count)),
                        list(reversed(self.base_param["cpu_timer"])),
                        list(reversed(self.base_param["command"])),         # command
                        list(reversed(self.base_param["sub_command"])),     # sub command
                    ]
                    device_code = device["binary"]
                    address = list(reversed([int(x, 16) for x in re.findall("..", f"{_request['split_min']:06x}")]))
                    address_count = list(reversed([int(x, 16) for x in re.findall("..", f"{_request['count']:04x}")]))
                    request_data = request_data + [address, device_code, address_count]

                    request_message = b""
                    for x in flatten(request_data):
                        request_message = request_message + struct.pack("B", x)
                    # print(f"request_message Binary: {request_message.hex()}")
                    self.request_messages.append({**_request, "message": request_message, "command": "bulk_read"})
        return self.request_messages

    # random read
    def set_request_random_read(self) -> dict:
        """
            ランダム読出しメッセージを生成する
            Return

        """
        def device_code_address_encode(data: dict):
            device = find_device(symbol=data["device"], manufacturer=self.conf.manufacturer, series=self.conf.series)
            decimal_notation = device["decimal"]

            data_address = data["address"].split(".")[0]
            address_integer = convert_decimal_notation_to_integer(data_address, decimal_notation)
            try:
                address_integer = address_integer + convert_decimal_notation_to_integer(device["offset"], decimal_notation)
            except Exception:
                pass

            if self.ascii_mode:
                device_code = device["ascii"]
                reconvert_notation = try_except(device, "decimal_to_ascii", exception="10")
                address = convert_integer_to_decimal_notation(address_integer, notation=reconvert_notation, prefix_count=6)
                # address = data_address.rjust(6, "0")
                return device_code + address
            else:
                device_code = device["binary"]

                address = list(reversed([int(x, 16) for x in re.findall("..", f"{address_integer:06x}")]))
                return address + [device_code]

        # random read command set
        self.base_param.update(command=[0x04, 0x03], sub_command=[0x00, 0x00])

        # max_access_count from device_data
        max_access_count = 192

        # Add word address request
        word_datas = []
        for data in self.conf.read_data['word']:
            word_datas.append(device_code_address_encode(data))

        # Add doubleword address request
        double_datas = []
        for data in self.conf.read_data['doubleword']:
            double_datas.append(device_code_address_encode(data))

        request_datas = []
        request_message_data = "" if self.ascii_mode else b""
        word_data_count = 0
        double_data_count = 0
        for data in word_datas:
            word_data_count = word_data_count + 1
            if self.ascii_mode:
                try:
                    request_message_data = request_message_data + format(data, "02x")
                except Exception:
                    request_message_data = request_message_data + data
            else:
                for x in data:
                    request_message_data = request_message_data + struct.pack("B", x)
            # over max_access_count more than word_datas
            if word_data_count >= max_access_count:
                request_datas.append({
                    "data": request_message_data,
                    "word_count": word_data_count,
                    "double_count": double_data_count,
                })
                request_message_data = "" if self.ascii_mode else b""
                word_data_count = 0

        for data in double_datas:
            double_data_count = double_data_count + 1
            if self.ascii_mode:
                try:
                    request_message_data = request_message_data + format(data, "02x")
                except Exception:
                    request_message_data = request_message_data + data
            else:
                for x in data:
                    request_message_data = request_message_data + struct.pack("B", x)
            # over max_access_count more than data_count(remain word_datas + double_datas)
            if (word_data_count + double_data_count) >= max_access_count:
                request_datas.append({
                    "data": request_message_data,
                    "word_count": word_data_count,
                    "double_count": double_data_count,
                })
                request_message_data = "" if self.ascii_mode else b""
                word_data_count = 0
                double_data_count = 0

        if request_message_data:
            request_datas.append({
                "data": request_message_data,
                "word_count": word_data_count,
                "double_count": double_data_count,
            })

        # リクエストメッセージを生成
        for data in request_datas:
            word_data_count = data["word_count"]
            double_data_count = data["double_count"]
            # ASCIIモード
            if self.ascii_mode:
                data_count = [
                    int(x, 16) for x in re.findall("..", f"{(8 + (4 * (word_data_count + double_data_count))) * 2:04x}")]
                request_data = [
                    self.base_param["sub_header"],
                    self.base_param["network_no"],
                    self.base_param["pc_no"],
                    self.base_param["recipient_io"],
                    self.base_param["recipient_node"],
                    data_count,
                    self.base_param["cpu_timer"],
                    self.base_param["command"],         # command
                    self.base_param["sub_command"],     # sub command
                    word_data_count,                    # word access count
                    double_data_count,                  # doubleword access count
                    data["data"]
                ]
                request_message = ""
                for x in flatten(request_data):
                    try:
                        request_message = request_message + format(x, "02x")
                    except Exception:
                        request_message = request_message + x
                request_message = request_message.encode('ascii')
                # print(f"request_message ASCII: {request_message}")
                self.request_messages.append({
                    **data,
                    "message": request_message,
                    "command": "random_read"
                })
            # Binaryモード
            else:
                data_count = [
                    int(x, 16) for x in re.findall("..", f"{8 + (4 * (word_data_count + double_data_count)):04x}")]
                request_data = [
                    self.base_param["sub_header"],
                    self.base_param["network_no"],
                    self.base_param["pc_no"],
                    list(reversed(self.base_param["recipient_io"])),
                    self.base_param["recipient_node"],
                    list(reversed(data_count)),
                    list(reversed(self.base_param["cpu_timer"])),
                    list(reversed(self.base_param["command"])),         # command
                    list(reversed(self.base_param["sub_command"])),     # sub command
                    word_data_count,                                    # word access count
                    double_data_count,                                  # doubleword access count
                    data["data"]
                ]
                request_message = b""
                for x in flatten(request_data):
                    request_message = request_message + struct.pack("B", x)
                # print(f"request_message Binary: {request_message.hex()}")
                self.request_messages.append({**data, "message": request_message, "command": "random_read"})
        return self.request_messages

    # TODO bulk write
    def set_request_message_bulk_write(self):
        self.identification_unit()
        """
            一括書き込みメッセージを生成する
        """

    # TODO random write
    def set_request_message_random_write(self):
        self.identification_unit()
        """
            ランダム書き込みメッセージを生成する
        """

    def set_connection(self, *, transport_layer: str = None, timeout=10):
        if transport_layer is None:
            # Backup 2024-05-08
            # if re.search("tcp", self.conf.protocol, flags=re.IGNORECASE):
            #     transport_layer = "tcp"
            # elif re.search("udp", self.conf.protocol, flags=re.IGNORECASE):
            #     transport_layer = "udp"
            # else:
            #     raise ValueError(f"This protocol: {self.conf.protocol} is unsupported.")

            if self.regexes.tcp.search(self.conf.protocol):
                transport_layer = "tcp"
            elif self.regexes.udp.search(self.conf.protocol):
                transport_layer = "udp"
            else:
                raise ValueError(f"This protocol: {self.conf.protocol} is unsupported.")

        if transport_layer in ["tcp"]:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif transport_layer in ["udp"]:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            raise ValueError(f"This protocol: {self.conf.protocol} is unsupported.")
        self.sock.settimeout(timeout)

    def open(self, *, ip_address: str = None, port: int = None):
        if ip_address is None:
            ip_address = self.conf.ip_address
        if port is None:
            port = self.conf.port
        # print(f"ip_address: {ip_address}, port: {port}")
        self.sock.connect((ip_address, port))

    def connection(self, *, request_messages: list = None) -> dict:
        if request_messages is None:
            request_messages = self.request_messages

        self.responses = []
        for request in self.request_messages:
            response = {"request": request}

            if isinstance(request, dict):
                request_message = try_except(request, key="message")
            else:
                request_message = request

            self.sock.send(request_message)
            try:
                recieve_message = self.sock.recv(1024).hex()
                response.update(
                    connection={
                        "request_message": request_message.hex(),
                        "recieve_message": recieve_message,
                        "code": 0,
                        "message": "success"
                    }
                )
            except Exception as e:
                # print(f"Error: {e}")
                response.update(
                    connection={
                        "request_message": request_message.hex(),
                        "recieve_message": None,
                        "code": 10060,
                        "message": str(e)
                    }
                )
            self.responses.append(response)
        return self.responses

    def close(self):
        try:
            self.sock.close()
        except Exception:
            print("Already closed")

    def divided_response_common(self, metainfo: dict, *, ascii_mode: bool = None):
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

        if ascii_mode is None:
            ascii_mode = self.ascii_mode

        if ascii_mode:
            check_response = "".join([chr(int(x, 16)) for x in re.findall("..", message)])
        else:
            check_response = message

        check_result = check_error_message(
            message=check_response,
            ascii_mode=ascii_mode
        )

        finish_code = try_integer(check_result["code"], notation=16)
        if finish_code == 0:
            if ascii_mode:
                response_data = "".join([chr(int(x, 16)) for x in re.findall("..", message)])[22:]
            else:
                response_data = message[22:]
            check_result.update(response=response_data)
        else:
            check_result.update(response=None)
        metainfo.update(judge=check_result)
        return metainfo

    # TODO bulk read
    def divided_response_bulk_read(self, *, ascii_mode=None):
        if ascii_mode is None:
            ascii_mode = self.ascii_mode

        # デバイス名と開始アドレスで集約
        multi_responses = [list(res) for _, res in itertools.groupby([x for x in self.responses if x["request"]["command"] in ["bulk_read"] and x["connection"]["code"] == 0], lambda x: (x["request"]["device"] and x["request"]["min"]))]

        for res in multi_responses:
            checked_response = [self.divided_response_common(metainfo=x, ascii_mode=ascii_mode) for x in res]
            try:
                join_response = b"".join([x["judge"]["response"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) == 0])
            except Exception:
                try:
                    join_response = "".join([x["judge"]["response"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) == 0])
                except Exception:
                    # print(f'Bulk read has error_code: {[x["judge"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) != 0]}')
                    join_response = None

            if join_response:
                for i, data in enumerate(self.conf.read_data["bulk"]):
                    # resは同じデバイス名で集約している
                    if res[0]["request"]["device"] == data["device"]:
                        res_hex = re.findall("....", join_response)

                        response_min = res[0]["request"]["min"]
                        # response_max = res[0]["request"]["max"]
                        device = find_device(symbol=data["device"], manufacturer=self.conf.manufacturer, series=self.conf.series)
                        decimal_notation = device["decimal"]
                        address_integer = convert_decimal_notation_to_integer(data["address"].split(".")[0], decimal_notation) + convert_decimal_notation_to_integer(try_except(device, key="offset", exception="0"), decimal_notation)
                        address_min = address_integer - response_min
                        # address_max = address_min + data["data_length"] if address_min + data["data_length"] <= response_max else response_max
                        # extraction_response = res_hex[address_min: address_max]
                        extraction_response = res_hex[address_min:]

                        if data["data_unit"] in ["string"]:
                            _data = []
                            for extract in extraction_response:
                                try:
                                    if ascii_mode:
                                        _word_data = re.findall("..", extract)
                                    else:
                                        _word_data = list(reversed(re.findall("..", extract)))

                                    if "mitsubishi" in self.conf.manufacturer.lower():
                                        for x in reversed(_word_data):
                                            if int(x, 16) == 0:
                                                raise ValueError("separate null")
                                            else:
                                                _data.append(chr(int(x, 16)))
                                    else:
                                        for x in _word_data:
                                            if int(x, 16) == 0:
                                                raise ValueError("separate null")
                                            else:
                                                _data.append(chr(int(x, 16)))
                                except Exception:
                                    break
                            response_string = "".join(flatten(_data))
                            data.update({"response": response_string})
                        else:
                            _data = []
                            for extract in extraction_response:
                                if ascii_mode:
                                    _word_data = re.findall("..", extract)
                                else:
                                    _word_data = list(reversed(re.findall("..", extract)))
                                _data.append(int("".join(_word_data), 16))
                            data.update({"response": _data})
        return {
            "metainfo": multi_responses,
            "data": self.conf.read_data
        }

    # random read
    def divided_response_randam_read(self, *, ascii_mode=None):
        if ascii_mode is None:
            ascii_mode = self.ascii_mode

        checked_response = [self.divided_response_common(metainfo=x, ascii_mode=ascii_mode)
                        for x in self.responses
                        if x["request"]["command"] in ["random_read"] and x["connection"]["code"] == 0]
        try:
            join_response = b"".join([x["judge"]["response"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) == 0])
        except Exception:
            try:
                join_response = "".join([x["judge"]["response"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) == 0])
            except Exception:
                # print(f'Random read has error_code: {[x["judge"] for x in checked_response if try_integer(x["judge"]["code"], notation=16) != 0]}')
                join_response = None

        if join_response:
            data_length = 0
            # word data convert
            for i, data in enumerate(self.conf.read_data["word"]):
                _data = join_response[i * 4:(i + 1) * 4]

                if ascii_mode:
                    res = int("".join(re.findall("..", _data)), 16)
                    data_length = (i + 1) * 2
                else:
                    res = int("".join(list(reversed(re.findall("..", _data)))), 16)
                    data_length = (i + 1) * 4

                # bit data
                # if data["data_unit"] in ["bit"] or re.search("\\.", data["address"]):
                if (self.regexes.bit.search(data["data_unit"])) or self.regexes.fraction.search(data["address"]):
                    res_bit = list(reversed(list(f"{res:016b}")))
                    try:
                        if data["address"].split(".")[1].isdecimal():
                            decimal_func = int(data["address"].split(".")[1], 10)
                        else:
                            decimal_func = int(data["address"].split(".")[1], 16)
                    except Exception:
                        decimal_func = 0
                    data.update({"response": int(res_bit[decimal_func])})

                # word data
                else:
                    # negative
                    # if (re.search("\\-", data["data_unit"]) or re.search("\\±", data["data_unit"])):
                    if (self.regexes.signed.search(data["data_unit"])):
                        data.update({"response": signed_hex2int(res, 16)})
                    # positive
                    else:
                        data.update({"response": res})

            # doubleword word data convert
            for i, data in enumerate(self.conf.read_data["doubleword"]):
                _data = join_response[data_length + (i * 8):data_length + ((i + 1) * 8)]
                if ascii_mode:
                    res = int("".join(re.findall("..", _data)), 16)
                else:
                    res = int("".join(list(reversed(re.findall("..", _data)))), 16)

                # negative
                # if (re.search("\\-", data["data_unit"]) or re.search("\\±", data["data_unit"])):
                if (self.regexes.signed.search(data["data_unit"])):
                    data.update({"response": signed_hex2int(res, 32)})
                # positive
                else:
                    data.update({"response": res})

        return {
            "metainfo": checked_response,
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


def test_code():
    configure = {
        "network": {
            # Mitsubishi PLC in NCPT
            "ip_address": "192.168.250.39",
            "port": 9600
        },
        "controller": {
            "type": "PLC",
            "manufacturer": "Mitsubishi Electric",
            "series": "MELSEC iQ-R",
            "protocol": "SLMP/TCP",
            "attributes": {
                "encode_mode": "binary"
                # "encode_mode": "ascii"
            }
        },
        # "network": {
        #     # Panasonic PLC in NCPT
        #     # パナソニックはランダム読み出し非対応!!!!!!!
        #     "ip_address": "192.168.250.5",
        #     "port": 9600
        # },
        # "controller": {
        #     "type": "PLC",
        #     "manufacturer": "Panasonic",
        #     "series": "FP-7",
        #     "protocol": "SLMP/TCP",
        #     "attributes": {
        #         "encode_mode": "binary"
        #         # "encode_mode": "ascii"
        #     }
        # },
        "data": [
            {
                "execute": "read",
                "machine_id": 1,
                # "group": "count",
                # "datatype": "input",
                # "trigger_value": None,
                # "item_value": None,
                "device": "D",
                "address": "1000",
                "data_length": 2,
                "data_unit": "+word",
                # "data_unit": "bulk"
            },
            {
                "execute": "read",
                "machine_id": 1,
                "group": "count",
                "datatype": "output",
                "trigger_value": None,
                "item_value": None,
                "device": "D",
                "address": "1000",
                "data_length": 2,
                "data_unit": "+word"
            },
            {
                "execute": "read",
                "machine_id": 2,
                "group": "count",
                "datatype": "input",
                "trigger_value": None,
                "item_value": None,
                "device": "D",
                "address": "1000",
                "data_length": 2,
                "data_unit": "-word"
            },
            {
                "execute": "read",
                "machine_id": 2,
                "group": "count",
                "datatype": "output",
                "trigger_value": None,
                "item_value": None,
                "device": "D",
                "address": "1002",
                "data_length": 2,
                "data_unit": "+word"
            },
            {
                "execute": "read",
                "machine_id": 2,
                "group": "count",
                "datatype": "output",
                "trigger_value": None,
                "item_value": None,
                "device": "D",
                "address": "1002",
                "data_length": 2,
                "data_unit": "-word"
            },
            {
                "execute": "read",
                "machine_id": 2,
                "group": "count",
                "datatype": "output",
                "trigger_value": None,
                "item_value": None,
                "device": "D",
                "address": "1002",
                "data_length": 2,
                "data_unit": "±word"
            },
            {
                "execute": "read",
                "machine_id": 2,
                "group": "error",
                "datatype": "error_trigger",
                "trigger_value": None,
                "item_value": None,
                "device": "D",
                "address": "1000",
                "data_length": 1,
                "data_unit": "word"
            },
            {
                "execute": "read",
                "machine_id": 2,
                "group": "error",
                "datatype": "error_trigger",
                "trigger_value": None,
                "item_value": None,
                "device": "D",
                "address": "1000",
                "data_length": 1,
                "data_unit": "bit"
            },
            {
                "execute": "read",
                "machine_id": 2,
                "group": "error",
                "datatype": "error_trigger",
                "trigger_value": None,
                "item_value": None,
                "device": "D",
                "address": "1002.1",
                "data_length": 1,
                "data_unit": "bit"
            },
            {
                "execute": "read",
                "machine_id": 1,
                "group": "custom",
                "datatype": "productname",
                "trigger_value": None,
                "item_value": None,
                "device": "D",
                "address": "1000",
                "data_length": 10,
                "data_unit": "string"
            },
            {
                "execute": "read",
                "machine_id": 1,
                "group": "custom",
                "datatype": "productname",
                "trigger_value": None,
                "item_value": None,
                "device": "D",
                "address": "1000",
                "data_length": 20,
                "data_unit": "bulk"
            },
            {
                "execute": "read",
                "machine_id": 1,
                "group": "custom",
                "datatype": "productname",
                "trigger_value": None,
                "item_value": None,
                "device": "D",
                "address": "1100",
                "data_length": 20,
                "data_unit": "bulk"
            },
            {
                "execute": "read",
                "machine_id": 1,
                "group": "custom",
                "datatype": "productname",
                "trigger_value": None,
                "item_value": None,
                "device": "W",
                "address": "1000",
                "data_length": 10,
                "data_unit": "string"
            },
        ]
    }
    test_data_word = [
        {
            "execute": "read",
            "machine_id": 1,
            "device": "D",
            "address": "1000",
            "data_length": 1,
            "data_unit": "+word",
        },
    ] * 200
    test_data_double = [
        {
            "execute": "read",
            "machine_id": 1,
            "device": "D",
            "address": "1000",
            "data_length": 2,
            "data_unit": "+word",
        },
    ] * 200
    configure["data"].extend(test_data_word)
    configure["data"].extend(test_data_double)

    configure = {
        'network': {'ip_address': '192.168.250.39', 'port': 9600},
        'controller': {'type': 'PLC', 'manufacturer': 'Mitsubishi Electric', 'series': 'MELSEC iQ-R', 'protocol': 'SLMP/TCP', 'attributes': {}},
        'data': [{'execute': 'read', 'machine_id': 1, 'datatype': 'Input', 'device': 'D', 'address': '500', 'data_unit': 'word', 'trigger': None, 'item': None},
                 {'execute': 'read', 'machine_id': 1, 'datatype': 'NG count', 'device': 'D', 'address': '5000', 'data_unit': 'word', 'trigger': '100', 'item': 'NGITEM 100'},
                 {'execute': 'read', 'machine_id': 1, 'datatype': 'Input', 'device': 'D', 'address': '223', 'data_unit': 'word', 'trigger': None, 'item': None},
                 {'execute': 'read', 'machine_id': 1, 'datatype': 'Actual Time', 'device': 'D', 'address': '12233', 'data_unit': '±word', 'trigger': '', 'item': None}]
    }

    con = Communication(configure=configure)
    con.identification_unit()
    con.set_request_random_read()
    con.set_request_bulk_read()
    con.set_connection()
    con.open()
    recv = con.connection()
    con.close()
    # print(f"recv: {recv}")

    result_random = con.divided_response_randam_read()
    if result_random:
        print(f"Random read meta: {result_random['metainfo']}\n")
        print(f"Word data: {result_random['data']['word']}\n")
        print(f"doubleword word data: {result_random['data']['doubleword']}\n")

    result_bulk = con.divided_response_bulk_read()
    if result_bulk:
        print(f"Bulk read meta: {result_bulk['metainfo']}\n")
        print(f"Bulk data: {result_bulk['data']['bulk']}\n")

    response = con.divided_read()
    data_list = [result_random, result_bulk]
    error_connection = con.extract_error_connection(data_list)
    print(error_connection)


if __name__ == "__main__":
    manufacturer = "mitsubishi"
    series = "iq"
    symbol = "D"
    # device = devices.device_list(manufacturer, series=series)
    device = find_device(symbol=symbol, manufacturer=manufacturer, series=series)
    print(device)
    # test_code()

