import socket
import struct
import itertools
import re
import sys
import pathlib

try:
    from .. import const
    from .. import convert
    from .. import logger
except Exception:
    parent_dir = str(pathlib.Path(__file__).parent.parent.resolve())
    sys.path.append(parent_dir)
    import const
    import convert
    import logger

try:
    from . import devices
except Exception:
    import devices


logger = logger.get_module_logger(__name__)


def try_except_object(obj: dict, *, key: str = None, except_key: str = None, exception=""):
    if key is None:
        try:
            result = obj
        except Exception:
            result = exception
    else:
        try:
            result = obj[key]
        except Exception:
            if except_key is not None:
                try:
                    result = obj[except_key]
                except Exception:
                    result = exception
            else:
                result = exception
    return result


class Connection():
    def __init__(self):
        pass

    def __del__(self):
        try:
            self.sock.close()
        except Exception:
            pass

    def check_optional(self):
        self.telegram_data = []
        self.segment_length = []
        self.string_option = False
        self.cmd_option = try_except_object(self.cmd, key="option")

        self.optional_data_type = try_except_object(
            self.optional, key="data_type")

        # STRING OPTINONの確認。またはDataの型がstrの場合、強制的にSTRINGと扱う
        if self.cmd_cmd in const.WRITE_COMMAND:
            if self.cmd_option in const.STRING_DATA or self.optional_data_type in const.STRING_DATA:
                self.string_option = True
            else:
                if isinstance(self.cmd_data, list):
                    if (isinstance(s, str) for s in self.cmd_data):
                        self.string_option = True
                else:
                    if isinstance(self.cmd_data, str):
                        self.string_option = True

            if self.string_option is True:
                if isinstance(self.cmd_data, list):
                    if all(isinstance(s, str) for s in self.cmd_data):
                        self.cmd_data = "".join(self.cmd_data)

        # TIME OPTIONの確認
        # if self.cmd_option in const.TIME_DATA or self.optional_data_type in const.TIME_DATA:
        #     pass

        # 交信データコード(COMMUNICATION DATA CODE OPTION)の確認 Default: binary
        self.data_code = try_except_object(
            self.optional, key="data_code", except_key="communication_data_code", exception="binary")

    def check_withoutskip_optional(self):
        # SKIP OPTIONの確認 listに含まれているアドレスが必要なためスキップしない＝含まれない場合スキップ
        optional_without_skip = try_except_object(
            self.optional, key="without_skip", except_key="only_use_address", exception=[])
        self.without_skip_address = []
        if self.cmd_cmd in const.READ_COMMAND and len(optional_without_skip) > 0:
            for without_skip_address in optional_without_skip:
                without_address = convert.decimal_convert(
                    decimal=self.decimal, str_address=without_skip_address)
                self.without_skip_address.append(
                    without_address - self.int_min_address
                )

    def check_decimal_point(self):
        try:
            self.point_index = self.str_min_address.index('.')
        except ValueError:
            try:
                self.point_index = self.str_max_address.index('.')
            except ValueError:
                self.point_index = None

    def define_device_parameter(self):
        has_point = True if self.point_index is not None or try_except_object(
            self.protocol, key="point_index", exception=None) is not None else False

        device_list = devices.device_list(
            manufacture=self.manufacture, series=self.series,
            has_point=has_point,
        )

        _device_list_data = [x for x in device_list["devices"]
                             if x["symbol"] == self.device["device"]]
        try:
            device_list_data = _device_list_data[0]
        except Exception:
            raise ValueError("Device symbol is incorrect.")
        else:
            if self.data_code in const.ASCII_DATA_CODE:
                try:
                    self.device_code = [device_list_data["ascii"]]
                    self.max_communicate_address_length = int(
                        device_list["transfer_limit"] / 2)
                except Exception:
                    raise ValueError(
                        "ASCII communication data code is not supported.")
            else:
                self.device_code = [device_list_data["binary"]]
                self.max_communicate_address_length = device_list["transfer_limit"]
            self.prefix_byte = device_list["prefix_byte"]
            self.endian = device_list["endian"]
            self.bit_identify = device_list_data["identify"]
            self.decimal = device_list_data["decimal"]

            # アドレスを10進数数値に変換
            self.int_min_address = convert.decimal_convert(
                decimal=self.decimal, str_address=self.str_min_address)
            self.int_max_address = convert.decimal_convert(
                decimal=self.decimal, str_address=self.str_max_address)

            self.communicate_address_length = (
                self.int_max_address - self.int_min_address + 1)

    def define_parameter(self, network: dict, protocol: dict, device: dict, cmd: dict, *, optional: dict = None):
        try:
            self.ip_address = network["ip"]
            try:
                self.port = int(network["port"])
            except ValueError:
                self.port = network["port"]

            self.protocol = protocol
            self.device = device
            self.cmd = cmd
            self.optional = optional

            self.cmd_cmd = cmd["cmd"]
            self.cmd_data = cmd["data"]
            self.transport_layer_protocol = self.protocol["transport_layer"]
            self.manufacture = self.protocol["manufacture"]
            self.str_min_address = try_except_object(
                self.device, key="min", except_key="minimum", exception=None)
            self.str_max_address = try_except_object(
                self.device, key="max", except_key="maximum", exception=None)
            self.series = self.protocol["series"]
        except Exception:
            return {
                "error_code": 20001,
                "message": "There are some missing parts in the settings."
            }

        # Optionalの確認, 応じてself.cmd_dataを変更する
        try:
            self.check_optional()
        except Exception:
            return {
                "error_code": 20003,
                "message": "The option parameter setting is incorrect. "
            }

        # 小数点の指定(bitの指定)の確認
        self.check_decimal_point()

        # デバイスパラメータの定義
        try:
            self.define_device_parameter()
        except Exception:
            return {
                "error_code": 20002,
                "message": "Parameter setting is incorrect."
            }

        # 指定したアドレスを含む通信以外を無視する設定の確認
        # 要デバイスパラメータ定義
        try:
            self.check_withoutskip_optional()
        except Exception:
            return {
                "error_code": 20005,
                "message": "Setting without_skip optional has error"
            }

        try:
            # Socket定義
            if self.transport_layer_protocol in const.TRANSPORT_TCP:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(const.TRANSPORT_TIMEOUT)
        except Exception:
            return {
                "error_code": 20010,
                "message": "Socket communication could not be established."
            }

        return {
            "error_code": 0,
            "message": "success"
        }

    # Converts data to binary to be read to PLC.
    def read_command(self):
        cmd_data = []
        access_data_length = []
        first_address = []

        _segment = [
            x for x in range(0, self.communicate_address_length, self.max_communicate_address_length)]
        _segment.append(self.communicate_address_length)
        for i_segment in range(len(_segment)):
            try:
                min_segment = _segment[i_segment]
                max_segment = _segment[i_segment + 1]
            except Exception:
                break
            else:
                _segment_cmd_data = list(range(min_segment, max_segment))
                # Skip addressのチェック(without skipが存在し、かつsegmentと重複していないものをSkip扱いとする)
                if len(self.without_skip_address) > 0 and not (set(_segment_cmd_data) & set(self.without_skip_address)):
                    self.skip_address_index.append(i_segment)

                self.segment_length.append(len(_segment_cmd_data))

                _access_data_length = format(len(_segment_cmd_data), "04x")
                access_data_length.append(
                    [int(x, 16) for x in [_access_data_length[2:4], _access_data_length[0:2]]])

                if self.data_code in const.ASCII_DATA_CODE:
                    if self.decimal in ["10", "16"]:
                        _min_ad, _, _, = convert.each_convert(
                            decimal=self.decimal, int_address=(self.int_min_address + min_segment))
                        _first_address = list(
                            re.findall("..", _min_ad.zfill(6)))
                    else:
                        _min_ad = format(
                            self.int_min_address + min_segment, "06d")
                        _first_address = list(re.findall("..", _min_ad))

                else:
                    _min_ad = format(self.int_min_address + min_segment, "06x")
                    _first_address = [int(x, 16) for x in list(
                        reversed(list(re.findall("..", _min_ad))))]
                first_address.append(_first_address)

        return {
            "cmd_data": cmd_data,
            "access_data_length": access_data_length,
            "first_address": first_address
        }

    def write_string(self, data):
        _cmd_data = []

        if isinstance(data, list) is True:
            _data = "".join(data)
        else:
            _data = data

        _data_list = [format(ord(x), "02x") for x in list(_data)]

        it = iter(_data_list)
        for _a, _b in itertools.zip_longest(it, it, fillvalue="00"):
            _cmd_data.append([int(_b, 16), int(_a, 16)])

        _length, _mod = divmod(len(_data), 2)
        _length += _mod
        # The length of the string is stored at the head.
        if self.manufacture in const.MANUFACTURER_PANASONIC:
            self.int_min_address += 1
            _data_length = format(str(int(_length)), "0>4s")
            _cmd_data.insert(
                0, [int(_data_length[:-2]), int(_data_length[-2:])])
            _length += 1
        else:
            # 文字列のセパレータ。通常null(0x00, 0x00)がエンドコード
            # _cmd_data.append([0, 0])
            pass
        return _cmd_data, _length

    def write_word(self, data):
        _cmd_data = []
        for i in range(len(data)):
            # positive/negative judgment
            if data[i] >= 0:
                _data = format(data[i], "04x")
            else:
                _data = format(
                    data[i] & 0xffff, '04x')

            it = iter(_data)
            for _a, _b, _c, _d in zip(it, it, it, it):
                _cmd_data.append(
                    [int(_c + _d, 16), int(_a + _b, 16)])
        _length = len(_cmd_data)
        return _cmd_data, _length

    def write_bit(self, data):
        _cmd_data = []
        _data = [format(x, "01x") for x in data]
        it = iter(_data)
        for _a, _b in itertools.zip_longest(it, it, fillvalue="0"):
            _cmd_data.append(
                [int(_a + _b, 16)])
        _length = len(_cmd_data) * 2
        return _cmd_data, _length

    # TODO 動作確認必須
    # Converts data to binary to be written to PLC.
    def write_command(self) -> dict:
        cmd_data = []
        access_data_length = []
        first_address = []

        _segment = [
            x for x in range(0, self.communicate_address_length, self.max_communicate_address_length)]

        _segment.append(self.communicate_address_length)
        for i_segment in range(len(_segment)):
            try:
                min_segment = _segment[i_segment]
                max_segment = _segment[i_segment + 1]
            except Exception:
                break
            else:
                _length = 0
                _segment_cmd_data = self.cmd_data[min_segment: max_segment]
                _cmd_data = []
                # Word devices
                if self.bit_identify in const.WORD_DEVICE:
                    # Writing of character strings.
                    if self.string_option is True:
                        _cmd_data, _length = self.write_string(
                            _segment_cmd_data)
                    # Writing of integer or boolean.
                    else:
                        _cmd_data, _length = self.write_word(_segment_cmd_data)
                # TODO double device
                elif self.bit_identify in const.DOUBLE_DEVICE:
                    pass
                # Bit devices
                else:
                    _cmd_data, _length = self.write_bit(_segment_cmd_data)

                if _length > 0:
                    cmd_data.append(_cmd_data)
                    _access_data_length = format(_length, "04x")
                    access_data_length.append(
                        [int(x, 16) for x in [_access_data_length[2:4], _access_data_length[0:2]]])

                    if self.data_code in const.ASCII_DATA_CODE:
                        if self.decimal in ["10", "16"]:
                            _min_ad, _, _, = convert.each_convert(
                                decimal=self.decimal, int_address=(self.int_min_address + min_segment))
                            _first_address = list(
                                re.findall("..", _min_ad.zfill(6)))
                        else:
                            _min_ad = format(
                                self.int_min_address + min_segment, "06d")
                            _first_address = list(re.findall("..", _min_ad))

                    else:
                        _min_ad = format(
                            self.int_min_address + min_segment, "06x")
                        _first_address = [int(x, 16) for x in list(
                            reversed(list(re.findall("..", _min_ad))))]
                    first_address.append(_first_address)

                    # _min_ad = format(self.int_min_address + min_segment, "06x")
                    # first_address.append([
                    #     int(x, 16) for x in [_min_ad[4:6], _min_ad[2:4], _min_ad[0:2]]])

        return {
            "cmd_data": cmd_data,
            "access_data_length": access_data_length,
            "first_address": first_address,
        }

    # 電文生成
    def generate_telegram(self) -> dict:
        self.skip_address_index = []

        sub_header = [0x50, 0x00]
        network_number = [0x00]
        pc_number = [0xFF]
        destination_unit_io = [0xFF, 0x03]
        destination_unit_node_number = [0x00]
        cpu_monitoring_timer = [0x10, 0x00]

        if self.cmd_cmd in const.WRITE_COMMAND:
            command = [0x01, 0x14]
            command_data = self.write_command()
        else:
            command = [0x01, 0x04]
            command_data = self.read_command()
        arr_cmd_data = command_data["cmd_data"]
        arr_access_data_length = command_data["access_data_length"]
        arr_first_address = command_data["first_address"]

        if self.bit_identify in const.BIT_DEVICE:
            if self.series in const.SERIES_MITSUBISHI_IQR:
                sub_command = [0x03, 0x00]
            else:
                sub_command = [0x01, 0x00]
        else:
            if self.series in const.SERIES_MITSUBISHI_IQR:
                sub_command = [0x02, 0x00]
            else:
                sub_command = [0x00, 0x00]

        for i in range(len(arr_access_data_length)):
            access_data_length = arr_access_data_length[i]
            device_code = self.device_code
            first_address = arr_first_address[i]
            if self.data_code in const.ASCII_DATA_CODE:
                try:
                    cmd_data = list(
                        (itertools.chain.from_iterable([reversed(x) for x in arr_cmd_data[i]])))
                except Exception:
                    cmd_data = []

                request_data_length = list(
                    format(24 + (len(cmd_data) * 2), "04x"))

                _data = (
                    sub_header + network_number + pc_number +
                    list(reversed(destination_unit_io)) + destination_unit_node_number +
                    request_data_length + list(reversed(cpu_monitoring_timer)) +
                    list(reversed(command)) + list(reversed(sub_command)) +
                    device_code + first_address + list(reversed(access_data_length)) +
                    cmd_data
                )
                _binary = ""
                for x in _data:
                    try:
                        _binary += format(x, "02x")
                    except Exception:
                        _binary += x

                self.telegram_data.append(_binary.encode("ascii"))
            else:
                try:
                    cmd_data = list(
                        (itertools.chain.from_iterable(arr_cmd_data[i])))
                except Exception:
                    cmd_data = []

                _request_data_length = format(len(
                    cpu_monitoring_timer + command + sub_command + first_address + device_code + access_data_length + cmd_data), "04x")
                request_data_length = [
                    int(x, 16) for x in [_request_data_length[2:4], _request_data_length[0:2]]]

                _data = (
                    sub_header + network_number + pc_number +
                    destination_unit_io + destination_unit_node_number +
                    request_data_length + cpu_monitoring_timer +
                    command + sub_command +
                    first_address + device_code + access_data_length +
                    cmd_data
                )
                _binary = b""
                for x in _data:
                    _binary += struct.pack("B", x)
                self.telegram_data.append(bytes(_binary))
            self.access_data_length = access_data_length

        error_code = 0
        message = "generate success"
        return {
            "error_code": error_code,
            "message": message,
            "data": self.telegram_data,
        }

    # 電文送受信
    def send_telegram(self, *, telegram_data=None, skip_address_index=None) -> dict:
        some_send_data = []
        some_recv_data = []
        some_err_code = []
        some_err_message = []
        recv_data = ""
        if telegram_data is None:
            telegram_data = self.telegram_data
        elif isinstance(telegram_data, str):
            telegram_data = [telegram_data]

        if skip_address_index is None:
            try:
                skip_address_index = self.skip_address_index
            except Exception:
                skip_address_index = []
        else:
            skip_address_index = []

        # Connection
        try:
            self.sock.connect((self.ip_address, self.port))
        except socket.error as e:
            if e.errno is None:
                some_err_code.append(10060)
            else:
                some_err_code.append(e.errno)
            some_err_message.append(str(e))
        else:
            for index, telegram in enumerate(telegram_data):
                _recv = None
                if len(skip_address_index) > 0 and index in skip_address_index:
                    _recv = "skip"
                    _err_code = 0
                    _err_message = "SKIP"
                    recv_data += "0000" * self.segment_length[index]
                else:
                    _err_code = 9999
                    _err_message = ""
                    # 再送処理
                    for i in range(const.RETRY_COUNT):
                        logger.debug("send: {}".format(telegram.hex()))
                        print("send: {}".format(telegram.hex()))

                        # Send data
                        self.sock.send(telegram)
                        try:
                            # Recieved data.
                            _recv = self.sock.recv(1024).hex()
                            logger.debug("recv: {}".format(_recv))
                        except socket.timeout as e:
                            # WSAETIMEDOUT
                            _err_code = 10060
                            _err_message = str(e)
                        except socket.herror as e:
                            # WSAECONNREFUSED
                            _err_code = 10061
                            _err_message = str(e)
                        except socket.gaierror as e:
                            _err_code = 11001
                            _err_message = str(e)
                        except socket.error as e:
                            _err_code = 10065
                            _err_message = str(e)
                        else:
                            # ASCIIモードの場合、取得データをASCII1文字列->16進数文字列に変換
                            if self.data_code in const.ASCII_DATA_CODE:
                                _recv = "".join([chr(int(x, 16))
                                                for x in re.findall("..", _recv)])

                            if len(_recv) < self.prefix_byte:
                                _err_code = 9998 if _err_code == 9999 else _err_code
                                _err_message = "DATA MISSING"
                            else:
                                # エラーコードを取得
                                try:
                                    _err_code = int(
                                        _recv[self.prefix_byte -
                                              2: self.prefix_byte]
                                        + _recv[self.prefix_byte - 4:self.prefix_byte - 2], 16)

                                    logger.debug(
                                        "Error Code:{}".format(_err_code))

                                    # エラーコードのチェック
                                    # error code 0x00 is Success. others is Error.
                                    if _err_code == 0:
                                        # TODO データ欠落チェック
                                        # readの場合 and 送信データ数 == 受信データ数 -> "OK"
                                        # if self.cmd_cmd in const.READ_COMMAND:
                                        #     if self.bit_identify in const.BIT_DEVICE:
                                        #         if self.data_code in const.ASCII_DATA_CODE:
                                        #             bit_length = 1
                                        #         else:
                                        #             bit_length = 2
                                        #     else:
                                        #         bit_length = 4

                                        #     if (self.segment_length[index] * bit_length) == (len(_recv[self.prefix_byte:])):
                                        #         _err_message = "SUCCESS"
                                        #         break
                                        #     else:
                                        #         _err_message = "MISSING DATA"
                                        #         break
                                        # else:
                                        #     _err_message = "SUCCESS"
                                        #     break

                                        _err_message = "SUCCESS"
                                        break
                                    else:
                                        _err_message = "code:{}".format(
                                            _err_code)
                                except Exception as e:
                                    _err_code = 9999 if _err_code in [
                                        0, 9999] else _err_code
                                    _err_message = str(
                                        e) if _err_message == "" else _err_message
                    else:
                        logger.debug("Retry count: {}".format(i))
                        some_send_data.append(telegram)
                        some_recv_data.append(_recv)
                        some_err_code.append(_err_code)
                        some_err_message.append(_err_message)
                        break

                    recv_data += _recv[self.prefix_byte:]

                some_send_data.append(telegram)
                some_recv_data.append(_recv)
                some_err_code.append(_err_code)
                some_err_message.append(_err_message)

        try:
            some_send_data = [x.hex() for x in some_send_data]
        except Exception:
            pass

        self.recv_data = recv_data
        return {
            "recv_data": recv_data,
            "error_code": max(some_err_code),
            "some_send": some_send_data,
            "some_recv": some_recv_data,
            "some_err_code": some_err_code,
            "some_err_message": some_err_message,
        }

    # 文字列に変換
    @staticmethod
    def convert_ascii_string(data: str) -> str:
        _string_data = []

        if len(data) <= 2:
            # Asciiは0x00~0x1Fは制御文字のため文字列としてはNullと扱う
            _1st_str = chr(int(data[:2], 16)) if int(
                data[:2], 16) >= 20 else ""
            _string_data.append(_1st_str)
        else:
            # Asciiは0x00~0x1Fは制御文字のため文字列としてはNullと扱う
            _1st_str = chr(int(data[:2], 16)) if int(
                data[:2], 16) >= 20 else ""
            _2nd_str = chr(int(data[2:], 16)) if int(
                data[2:], 16) >= 20 else ""
            _string_data.append(_1st_str)
            _string_data.append(_2nd_str)

        return "".join(_string_data)

    # 受信電文を分割
    def devide_received(self, *, recv_data=None):
        if self.cmd_cmd in const.WRITE_COMMAND:
            return []
        else:
            if recv_data is None:
                _devide_data = self.recv_data
            else:
                _devide_data = recv_data
            _devide = []
            _word = 4
            _byte = 2

            _count = 0

            if self.bit_identify in const.BIT_DEVICE:
                _devide = [int(x, 16) for x in _devide_data]
            elif self.bit_identify in const.WORD_DEVICE:
                for i in range(0, len(_devide_data), _word):
                    if len(_devide_data[i: i + _word]) < _word:
                        _data = _devide_data[i: i + _word] + ("0" * _word)
                    else:
                        _data = _devide_data[i: i + _word]

                    # エンディアン調整
                    if self.endian in const.ENDIAN_LITTLE:
                        # ASCIIの場合big endianになる
                        if self.data_code in const.ASCII_DATA_CODE:
                            pass
                        else:
                            _data = _data[_byte:] + _data[:_byte]

                    # 文字列として返答
                    if self.cmd_option in const.STRING_DATA or self.optional_data_type in const.STRING_DATA:
                        # [0x00]で区切り文字。
                        # それ以降はバッファが含まれている可能性があるので無視する
                        for i in range(0, len(_data), _byte):
                            if len(_data[i: i + _byte]) < _byte:
                                _byte_data = _data[i: i +
                                                   _byte] + ("0" * _byte)
                            else:
                                _byte_data = _data[i: i + _byte]

                            if _byte_data == "00":
                                # パナソニック製PLCの場合、頭2wordは"格納領域数"と"データ数"のため除外
                                if self.manufacture in const.MANUFACTURER_PANASONIC:
                                    del _devide[:2]
                                break
                            else:
                                _string_data = self.convert_ascii_string(
                                    _byte_data)
                                _devide.append(_string_data)
                    # 数値として返答
                    else:
                        # wordデバイスをbitとして使用している場合の返答
                        if self.bit_identify in const.WORD_DEVICE and self.point_index is not None:
                            _bit_data = list(
                                reversed([int(x, 16) for x in list(format(int(_data, 16), "016b"))]))
                            if _count == 0 and self.communicate_address_length - 1 == 0:
                                _min_bit = int(
                                    self.str_min_address.rsplit(".", 1)[-1], 16)
                                _max_bit = int(
                                    self.str_max_address.rsplit(".", 1)[-1], 16)
                                _devide.extend(_bit_data[_min_bit:_max_bit])
                            elif _count == 0:
                                _min_bit = int(
                                    self.str_min_address.rsplit(".", 1)[-1], 16)
                                _devide.extend(_bit_data[_min_bit:])
                            elif _count == self.communicate_address_length - 1:
                                _max_bit = int(
                                    self.str_max_address.rsplit(".", 1)[-1], 16)
                                _devide.extend(_bit_data[:_max_bit])
                            else:
                                _devide.extend(_bit_data)
                        else:
                            _devide.append(int(_data, 16))
                        _count += 1

            # 文字列の場合、結合してtextで返答
            if self.cmd_option in const.STRING_DATA or self.optional_data_type in const.STRING_DATA:
                _devide = "".join(_devide)

            return _devide


def main(network: dict, protocol: dict, device: dict, cmd: dict, *, optional=None):
    connection = Connection()
    defines = connection.define_parameter(
        network, protocol, device, cmd, optional=optional)

    if defines["error_code"] != 0:
        logger.warning(defines)
        result = {
            "extract": "",
            "send": "",
            "receive": "",
            "error_code": defines["error_code"],
            "message": defines["message"]
        }
    else:
        # 送信電文生成
        generated_telegram = connection.generate_telegram()
        logger.debug("send: {}".format(generated_telegram))

        # 電文送受信
        receive_data = connection.send_telegram()
        logger.debug("receive: {}".format(receive_data))

        # 受信電文からデータ部を分離
        devided_data = connection.devide_received()
        logger.debug("devide: {}".format(devided_data))

        error_code = receive_data["error_code"]
        result = {
            "extract": devided_data,
            "send": try_except_object(generated_telegram, key="data", exception=""),
            "receive": receive_data["recv_data"],
            "error_code": error_code,
            "some_receive": receive_data["some_recv"],
            "some_error_code": receive_data["some_err_code"],
            "some_error_message": receive_data["some_err_message"],
        }
    try:
        del connection
    except Exception as e:
        logger.warning(e)
    logger.debug("result: {}".format(result))
    return result


if __name__ == "__main__":
    # 三菱
    network = {"ip": "192.168.250.39", "port": 9600}
    protocol = {"manufacture": "mitsubishi", "series": "q",
                "protocol": "slmp", "transport_layer": "tcp", "point_index": None,
                }
    # device = {"device": "M", "min": "100", "max": "115"}  # decimal=10 bit
    device = {"device": "D", "min": "1000", "max": "1004"}  # decimal=10 word
    # device = {"device": "B", "min": "100", "max": "115"}  # decimal=16 bit
    # device = {"device": "W", "min": "100", "max": "115"}  # decimal=16 word

    # """
    # パナソニック
    # network = {"ip": "192.168.250.5", "port": 9600}
    # protocol = {"manufacture": "panasonic", "series": "fp7",
    #             "protocol": "slmp", "transport_layer": "tcp", "point_index": None, }
    # # device = {"device": "X", "min": "10", "max": "1F"}
    # # device = {"device": "X", "min": "1.0", "max": "1.0"}
    # # device = {"device": "DT", "min": "5100", "max": "5101"}
    # device = {"device": "DT", "min": "5000", "max": "5003"}
    # """

    # """
    # キーエンス
    # network = {"ip": "192.168.250.10", "port": 5000}
    # protocol = {"manufacture": "keyence", "series": "7500",
    #             "protocol": "slmp", "transport_layer": "tcp", "point_index": None,
    #             }
    # # device = {"device": "T_TS", "min": "100", "max": "115"}  # decimal=10 bit
    # device = {"device": "DM", "min": "100", "max": "103"}  # decimal=10 word
    # # device = {"device": "B", "min": "100", "max": "103"}  # decimal=16 bit
    # # device = {"device": "W", "min": "100", "max": "115"}  # decimal=16 word
    # # device = {"device": "M", "min": "100", "max": "103"}  # decimal=1016 bit
    # """

    # cmd = {"cmd": "write", "data": [1, 0, 0, 1], "option": ""}  # bit write
    # cmd = {"cmd": "write", "data": [100, 1111,
    #                                 22222, 33], "option": ""}  # word write
    # cmd = {"cmd": "write", "data": "abcd", "option": ""}  # string word write
    cmd = {"cmd": "read", "data": [], "option": ""}  # read
    optional = {
        # "data_type": None, or "integer",
        # "data_type": "string",
        # "data_type": "time",
        # "without_skip": ["503", "1001"],
        # "data_code": "ascii"  # "binary" or "ascii", default: "binary"
    }
    result = main(
        network=network,
        protocol=protocol,
        device=device,
        cmd=cmd,
        optional=optional
    )
    logger.info(result)
    print(result)

'''
    動作確認
        三菱 Q61P(iQ)
            word device     int read        ...2022/12/16
                                write       ...2022/12/16
                            bit read        ...2022/12/16
                                write
                            str read        ...2022/12/16
                                write       ...2022/12/16
            bit device      bit read
                                write

        三菱 (iQ-R)
            word device     int read
                                write
                            bit read
                                write
                            str read
                                write
            bit device      bit read
                                write
            double device   int read
                                write
                            bit read
                                wirte
                            str read
                                write

        キーエンス (KV-7000)
        キーエンス (KV-Nano)

        パナソニック (FP-7)
            word device     int read    ...2022/12/19
                                write
                            bit read
                                write
                            str read
                                write
            bit device      bit read
                                write

'''
