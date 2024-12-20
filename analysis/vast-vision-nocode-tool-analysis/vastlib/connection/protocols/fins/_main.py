import os
import re
import psutil
import socket
import random
import itertools
import struct
import traceback
import inspect

try:
    from .. import const
    from .. import convert
    from .. import logger
except Exception:
    import sys
    import pathlib
    parent_dir = str(pathlib.Path(__file__).parent.parent.resolve())
    sys.path.append(parent_dir)
    import const
    import convert
    import logger

try:
    from . import devices
except Exception:
    import src.connection.protocols.fins.devices as devices

logger = logger.get_module_logger(__name__, level="DEBUG")


class Base():
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

    def try_except_int(val, *, base_number=10, exception=None):
        try:
            return int(val, base_number)
        except Exception:
            if exception is None:
                return val
            else:
                return exception

    def try_except_str(val, *, exception=None):
        try:
            return str(val)
        except Exception:
            if exception is None:
                return val
            else:
                return exception


class Connect():
    # 通信設定をセット
    def __init__(self, network: dict, protocol: dict, device: dict, cmd: dict, *, optional: dict = None):
        self.network = network
        self.protocol = protocol
        self.device = device
        self.cmd = cmd
        self.optional = optional

        self.ip_address = self.network["ip"]
        self.port = Base.try_except_int(network["port"])

        self.cmd_cmd = self.cmd["cmd"]
        self.cmd_data = self.cmd["data"]
        self.transport_layer_protocol = self.protocol["transport_layer"]
        self.manufacture = self.protocol["manufacture"]
        self.series = self.protocol["series"]

        self.str_min_address = Base.try_except_object(
            self.device, key="min", except_key="minimum", exception=None)
        self.str_max_address = Base.try_except_object(
            self.device, key="max", except_key="maximum", exception=None)

        self.skip_address_index = []

    # Optionのチェック
    def check_optional(self):
        try:
            self.telegram_data = []
            self.segment_length = []
            self.cmd_option = Base.try_except_object(self.cmd, key="option")

            self.optional_data_type = Base.try_except_object(
                self.optional, key="data_type")

            # STRING OPTINONのチェック。Dataの型がstrの場合、PLCに読み書きするデータを強制的にSTRINGデータとして扱う
            self.string_option = False
            if self.cmd_cmd in const.WRITE_COMMAND and (self.cmd_option in const.STRING_DATA or self.optional_data_type in const.STRING_DATA):
                self.string_option = True
                if isinstance(self.cmd_data, list) and all(isinstance(s, str) for s in self.cmd_data):
                    self.cmd_data = "".join(self.cmd_data)

            # TIME OPTIONのチェック
            self.time_option = False
            if (self.cmd_option in const.TIME_DATA or self.optional_data_type in const.TIME_DATA):
                self.time_option = True

        except Exception as e:
            logger.warning(traceback.format_exc())
            return {
                "error_code": 20003,
                "message": "The option parameter setting is incorrect. ",
                "traceback": str(e)
            }
        else:
            return {
                "error_code": 0,
                "message": f"Success: {inspect.getframeinfo(inspect.currentframe()).function}"
            }

    # Min, MaxのAddressに小数点が含まれているかのチェック
    def check_decimalpoint(self):
        try:
            self.point_index = self.str_min_address.index('.')
        except ValueError:
            try:
                self.point_index = self.str_max_address.index('.')
            except ValueError:
                self.point_index = False
        finally:
            return {
                "error_code": 0,
                "message": f"Success: {inspect.getframeinfo(inspect.currentframe()).function}"
            }

    # SKIP OPTIONの確認 listに含まれているアドレスが必要なためスキップしない＝含まれない場合スキップ
    def check_withoutskip(self):
        try:
            optional_without_skip = Base.try_except_object(
                self.optional, key="without_skip", except_key="only_use_address", exception=[])
            self.without_skip_address = []
            if self.cmd_cmd in const.READ_COMMAND and len(optional_without_skip) > 0:
                for without_skip_address in optional_without_skip:
                    without_address = convert.decimal_convert(
                        decimal=self.decimal, str_address=without_skip_address)
                    self.without_skip_address.append(
                        without_address - self.int_min_address
                    )
        except Exception as e:
            logger.warning(traceback.format_exc())
            return {
                "error_code": 20005,
                "message": "Setting without_skip optional has error.",
                "traceback": str(e)
            }
        else:
            return {
                "error_code": 0,
                "message": f"Success: {inspect.getframeinfo(inspect.currentframe()).function}"
            }

    # PLCのデバイス値などの固定値をdevice_list.pyから取得し変換
    def set_device_parameter(self):
        try:
            has_point = Base.try_except_object(
                self.protocol, key="point_index", exception=None)

            device_list = devices.device_list(
                manufacture=self.manufacture, series=self.series,
                transport=self.transport_layer_protocol,
                has_point=(has_point or self.point_index)
            )
            self.max_communicate_address_length = device_list["transfer_limit"]
            self.prefix_byte = device_list["prefix_byte"]
            self.endian = device_list["endian"]

            device_list_data = [x for x in device_list["devices"]
                                if x["symbol"] == self.device["device"]][0]
            self.device_code = [device_list_data["binary"]]
            self.bit_identify = device_list_data["identify"]
            self.decimal = device_list_data["decimal"]

            self.int_min_address = convert.decimal_convert(
                decimal=self.decimal, str_address=self.str_min_address)
            self.int_max_address = convert.decimal_convert(
                decimal=self.decimal, str_address=self.str_max_address)

            self.communicate_address_length = (
                self.int_max_address - self.int_min_address + 1)

        except Exception as e:
            logger.warning(traceback.format_exc())
            return {
                "error_code": 20002,
                "message": "Parameter setting is incorrect.",
                "traceback": str(e)
            }
        else:
            return {
                "error_code": 0,
                "message": f"Success: {inspect.getframeinfo(inspect.currentframe()).function}"
            }

    def set_parameter(self):
        result_check_optional = self.check_optional()
        if result_check_optional["error_code"] == 0:
            result_check_withoutskip = self.check_withoutskip()
            if result_check_withoutskip["error_code"] == 0:
                result_check_decimalpoint = self.check_decimalpoint()
                if result_check_decimalpoint["error_code"] == 0:
                    result_set_device_parameter = self.set_device_parameter()
                    if result_check_decimalpoint["error_code"] == 0:
                        return {
                            "error_code": 0,
                            "error_message": "SUCCESS",
                        }
                    else:
                        return result_set_device_parameter
                else:
                    return result_check_decimalpoint
            else:
                return result_check_withoutskip
        else:
            return result_check_optional

    # =================================================================
    # ネットワークの第4オクテットを取得(FINS通信設定に必要)
    def get_host_fourth_octet(self, ip_address, port):
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
                logger.warning(
                    '{}:{}, {}'.format(
                        sys._getframe().f_code.co_name, e, 'No connection found. Please check your communication settings.'))
                fourth_octet = int(iplist[0].rsplit('.', 1)[1])
        else:
            fourth_octet = None
        return fourth_octet

    # 連続読出しコマンド生成
    def sequence_read(self):
        cmd_data = []
        access_data_length = []
        first_address = []

        _segment = [x for x in range(0, self.communicate_address_length, self.max_communicate_address_length)]
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
                # アドレスが整数指定の場合
                if self.point_index is None:
                    _min_ad = format(self.int_min_address + min_segment, "04x")

                    # エンディアンの調整
                    if self.endian in const.ENDIAN_BIG:
                        access_data_length.append([int(x, 16) for x in list(re.findall("..", _access_data_length))])
                        _first_address = [int(x, 16) for x in list(re.findall("..", _min_ad))]
                    else:
                        access_data_length.append([int(x, 16) for x in list(reversed(list(re.findall("..", _access_data_length))))])
                        _first_address = [int(x, 16) for x in list(reversed(list(re.findall("..", _min_ad))))]
                    _first_address.append(0)

                # アドレスが小数指定の場合
                else:
                    _, quotient, remainder = convert.each_convert(self.decimal, self.int_min_address + min_segment)
                    padded_quotient = quotient.rjust(4, "0")
                    padded_remainder = remainder.rjust(2, "0")
                    padded = list(re.findall("..", padded_quotient)) + [padded_remainder]

                    # エンディアンの調整
                    if self.endian in const.ENDIAN_BIG:
                        access_data_length.append([int(x, 16) for x in list(re.findall("..", _access_data_length))])
                        _first_address = [int(x, 16) for x in padded]
                    else:
                        access_data_length.append([int(x, 16) for x in list(reversed(list(re.findall("..", _access_data_length))))])
                        _first_address = [int(x, 16) for x in list(reversed(padded))]

                first_address.append(_first_address)

        return {
            "cmd_data": cmd_data,
            "access_data_length": access_data_length,
            "first_address": first_address,
        }

    # 文字列書き込みコマンド生成
    def convert_write_string(self, data):
        cmd_data = []

        if isinstance(data, list) is True:
            _data = "".join(data)
        else:
            _data = data

        _data_list = [format(ord(x), "02x") for x in list(_data)]

        it = iter(_data_list)
        for _a, _b in itertools.zip_longest(it, it, fillvalue="00"):
            cmd_data.append([int(_b, 16), int(_a, 16)])

        length, _mod = divmod(len(_data), 2)
        length += _mod
        return cmd_data, length

    # WORD書き込みコマンド生成
    def convert_write_word(self, data: list):
        cmd_data = []
        for i in range(len(data)):
            # positive/negative judgment
            if data[i] >= 0:
                _data = format(data[i], "04x")
            else:
                _data = format(
                    data[i] & 0xffff, '04x')

            it = iter(_data)
            for _a, _b, _c, _d in zip(it, it, it, it):
                if self.endian in const.ENDIAN_BIG:
                    cmd_data.append(
                        [int(_a + _b, 16), int(_c + _d, 16)])
                else:
                    cmd_data.append(
                        [int(_c + _d, 16), int(_a + _b, 16)])
        length = len(cmd_data)
        return cmd_data, length

    # BIT書き込みコマンド生成
    def convert_write_bit(self, data: list):
        cmd_data = []
        if self.point_index is None:
            _data = [format(x, "01x") for x in data]
            it = iter(_data)
            for _a, _b in itertools.zip_longest(it, it, fillvalue="0"):
                cmd_data.append(
                    [int(_a + _b, 16)])
            length = len(cmd_data) * 2
        else:
            cmd_data.append(data)
            length = len(data)
        return cmd_data, length

    # 連続書き込みコマンド生成
    def sequence_write(self):
        # Ex: W1.00 ~ W1.05 [1,1,0,0,1,0]
        # a = b"\x46\x49\x4E\x53\x00\x00\x00\x20\x00\x00\x00\x02\x00\x00\x00\x00\x80\x00\x02\x00\x01\x00\x00\xef\x00\x19\x01\x02\x31\x00\x00\x01\x00\x06\x01\x01\x00\x00\x01\x00"
        # Ex: W1 ~ W5 [1,1,0,0,1,0]
        # a = b"\x46\x49\x4e\x53\x00\x00\x00\x26\x00\x00\x00\x02\x00\x00\x00\x00\x80\x00\x02\x00\x01\x00\x00\xef\x00\x19\x01\x02\xb1\x00\x01\x00\x00\x06\x00\x01\x00\x01\x00\x00\x00\x00\x00\x01\x00\x00"

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

                # 書き込みコマンドの変換
                # Word devices
                if self.bit_identify in const.WORD_DEVICE:
                    # Writing of character strings.
                    if self.string_option is True:
                        _cmd_data, _length = self.convert_write_string(
                            _segment_cmd_data)
                    # Writing of integer or boolean.
                    else:
                        _cmd_data, _length = self.convert_write_word(_segment_cmd_data)
                # TODO double device
                elif self.bit_identify in const.DOUBLE_DEVICE:
                    pass
                # Bit devices
                else:
                    _cmd_data, _length = self.convert_write_bit(_segment_cmd_data)

                if _length > 0:
                    cmd_data.append(_cmd_data)
                    _access_data_length = format(_length, "04x")
                    if self.point_index is None:
                        _min_ad = format(
                            self.int_min_address + min_segment, "04x")
                        if self.endian in const.ENDIAN_BIG:
                            access_data_length.append(
                                [int(x, 16) for x in list(re.findall("..", _access_data_length))])
                            _first_address = [int(x, 16) for x in list(
                                re.findall("..", _min_ad))]
                        else:
                            access_data_length.append([int(x, 16) for x in list(
                                reversed(list(re.findall("..", _access_data_length))))])
                            _first_address = [int(x, 16) for x in list(
                                reversed(list(re.findall("..", _min_ad))))]
                        _first_address.append(0)
                    # TODO
                    else:
                        _, quotient, remainder = convert.each_convert(
                            self.decimal, self.int_min_address + min_segment)
                        padded_quotient = quotient.rjust(4, "0")
                        padded_remainder = remainder.rjust(2, "0")
                        padded = list(re.findall(
                            "..", padded_quotient)) + [padded_remainder]

                        if self.endian in const.ENDIAN_BIG:
                            access_data_length.append(
                                [int(x, 16) for x in list(re.findall("..", _access_data_length))])
                            _first_address = [
                                int(x, 16) for x in padded]
                        else:
                            access_data_length.append([int(x, 16) for x in list(
                                reversed(list(re.findall("..", _access_data_length))))])
                            _first_address = [
                                int(x, 16) for x in list(reversed(padded))]

                    first_address.append(_first_address)

        return {
            "cmd_data": cmd_data,
            "access_data_length": access_data_length,
            "first_address": first_address,
        }

    # ノード通信電文生成
    def generate_node_telegram(self):
        if self.transport_layer_protocol in const.TRANSPORT_TCP:
            header = [0x46, 0x49, 0x4E, 0x53]
            length = [0x00, 0x00, 0x00, 0x0C]
            tcp_command = [0x00, 0x00, 0x00, 0x00]
            error_code = [0x00, 0x00, 0x00, 0x00]
            client_node = [0x00, 0x00, 0x00, 0x00]
            node_telegram = (
                header + length + tcp_command + error_code + client_node
            )
            binary = b""
            for x in node_telegram:
                binary += struct.pack("B", x)
            self.node_telegram = binary
            return self.node_telegram

    # 通信電文生成
    def generate_telegram(self, *, node_data=None):
        # self.skip_address_index = []

        if self.transport_layer_protocol in const.TRANSPORT_TCP:
            header = [0x46, 0x49, 0x4E, 0x53]
            tcp_command = [0x00, 0x00, 0x00, 0x02]
            error_code = [0x00, 0x00, 0x00, 0x00]
            if node_data is not None and node_data["error_code"] == 0:
                da1 = [node_data["server_node"]]
                sa1 = [node_data["client_node"]]
            else:
                return node_data

        elif self.transport_layer_protocol in const.TRANSPORT_UDP:
            header = []
            tcp_command = []
            error_code = []
            client_ip = self.get_host_fourth_octet(self.ip_address, self.port)
            client_ip = 52
            da1 = [0x00]
            sa1 = [client_ip]

        # Bit7=1:fixed value, Bit6=0:command, Bit0=0:need response
        # icf = [0x00]
        icf = [0x80]
        rsv = [0x00]
        # Number of allowable bridge passes.
        # Basically 0x02, 0x07: When using network crossings up to 8 layers.
        gct = [0x02]
        # Destination network address.
        # 0x00: Same network, 0x01~0x7F: Destination network
        dna = [0x00]
        da2 = [0x00]
        sna = [0x00]
        sa2 = [0x00]
        self.sid = random.randrange(0, 255, 1)
        sid = [self.sid]

        device_code = self.device_code

        # Readコマンド
        if self.cmd_cmd in const.READ_COMMAND:
            command = [0x01, 0x01]
            command_data = self.sequence_read()
            arr_cmd_data = command_data["cmd_data"]
            arr_access_data_length = command_data["access_data_length"]
            arr_first_address = command_data["first_address"]
        # Writeコマンド
        else:
            command = [0x01, 0x02]
            command_data = self.sequence_write()
            arr_cmd_data = command_data["cmd_data"]
            arr_access_data_length = command_data["access_data_length"]
            arr_first_address = command_data["first_address"]

        for i in range(len(arr_access_data_length)):
            try:
                cmd_data = list(
                    (itertools.chain.from_iterable(arr_cmd_data[i])))
            except Exception:
                cmd_data = []
            access_data_length = arr_access_data_length[i]
            first_address = arr_first_address[i]

            if self.transport_layer_protocol in const.TRANSPORT_TCP:
                length_count = len(
                    tcp_command + error_code + icf + rsv + gct + dna + da1 + da2 + sna + sa1 + sa2 + sid + command + device_code + first_address + access_data_length + cmd_data
                )

                _length = [int(x, 16) for x in list(
                    re.findall("..", format(length_count, "08x")))]
            else:
                _length = []

            if self.endian in const.ENDIAN_BIG:
                length = _length
            else:
                length = list(reversed(_length))

        _data = (
            header + length + tcp_command + error_code + icf + rsv + gct + dna + da1 + da2 + sna + sa1 + sa2 + sid + command + device_code + first_address + access_data_length + cmd_data
        )

        _binary = b""
        for x in _data:
            _binary += struct.pack("B", x)
        self.telegram_data.append(_binary)
        self.access_data_length = access_data_length
        return {
            "error_code": 0,
            "message": "SUCCESS",
            "data": self.telegram_data,
            "check": self.sid
        }

    # =================================================================
    # Socketの定義
    def set_connection(self):
        try:
            # Socket定義
            if self.transport_layer_protocol in const.TRANSPORT_TCP:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(const.TRANSPORT_TIMEOUT)
        except Exception as e:
            logger.warning(traceback.format_exc())
            return {
                "error_code": 20010,
                "message": "Socket communication could not be established.",
                "traceback": str(e)
            }
        else:
            return {
                "error_code": 0,
                "message": f"Success: {inspect.getframeinfo(inspect.currentframe()).function}"
            }

    # 送受信電文のIDチェック
    def check_sid(self, recv):
        try:
            recv_sid = int(recv[self.prefix_byte - 10: self.prefix_byte - 8], 16)
            if recv_sid == self.sid:
                error_message = "SUCCESS"
                err_code = 0
            else:
                err_code = 221 if err_code in [0, 9999] else err_code
                error_message = "SID for sending and receiving are different."
        except Exception as e:
            err_code = 222 if err_code in [0, 9999] else err_code
            error_message = str(e)
        finally:
            return {
                "error_code": err_code,
                "error_message": error_message
            }

    # エラーコードの判定
    def check_error_code(self, recv):
        if self.transport_layer_protocol in const.TRANSPORT_UDP:
            ecode = (recv[self.prefix_byte - 4: self.prefix_byte - 2] + recv[self.prefix_byte - 2: self.prefix_byte])
            # Bit7, Bit8はPLC本体の異常(バッテリ異常など)のため無視
            if int(ecode, 16) not in [0, 64, 128]:
                err_code = ecode
                error_message = f"ErrorCode: {err_code}"
            else:
                err_code = 0
                error_message = "SUCCESS"
        elif self.transport_layer_protocol in const.TRANSPORT_TCP:
            conn_ecode1 = recv[16:24]
            conn_ecode2 = recv[24:32]
            ecode = recv[self.prefix_byte - 4: self.prefix_byte]

            # Bit7, Bit8はPLC本体の異常(バッテリ異常など)のため無視
            if int(conn_ecode1, 16) not in [2, 64, 128] and int(conn_ecode2, 16) not in [0, 64, 128]:
                ecode = conn_ecode2 + ',' + conn_ecode2
                err_code = ecode if err_code in [0, 9999] else err_code
                error_message = f"ErrorCode: {err_code}"
            elif int(ecode, 16) not in [0, 64, 128]:
                ecode = (
                    recv[self.prefix_byte - 4: self.prefix_byte - 2] + recv[self.prefix_byte - 2: self.prefix_byte]
                )
                err_code = ecode if err_code in [0, 9999] else err_code
                error_message = f"ErrorCode: {err_code}"
            else:
                err_code = 0
                error_message = "SUCCESS"

        return {
            "error_code": err_code,
            "error_message": error_message
        }

    # TCP通信の場合、通信前に必要なノード通信を実施
    def send_node_telegram(self):
        self.client_node = None
        self.server_node = None
        self.generate_node_telegram()
        try:
            self.sock.connect((self.ip_address, self.port))
            self.sock.send(bytes(self.node_telegram))
            recv_node = self.sock.recv(1024).hex()
        except socket.error as e:
            logger.warning(e)
            self.node_ecode = 10060
            self.node_error_message = str(e)
        else:
            node_ecode1 = recv_node[16:24]
            node_ecode2 = recv_node[24:32]

            # Node error handling.
            if int(node_ecode1, 16) not in [1, 64, 128]:
                self.node_ecode = 30098
                self.node_error_message = "node ecode1: {}".format(
                    node_ecode1)
            elif int(node_ecode2, 16) not in [0, 64, 128]:
                self.node_ecode = 30099
                self.node_error_message = "node ecode2: {}".format(
                    node_ecode2)
            else:
                self.client_node = int("0x" + recv_node[32:40], 16)
                self.server_node = int("0x" + recv_node[40:48], 16)
                self.node_ecode = 0
                self.node_error_message = "node success"

        return {
            "error_code": self.node_ecode,
            "message": self.node_error_message,
            "client_node": self.client_node,
            "server_node": self.server_node,
        }

    # 通信
    def send_telegram(self, *, telegram_data=None, skip_address_index=None) -> dict:
        some_send_data = []
        some_recv_data = []
        some_err_code = []
        some_err_message = []
        recv_data = ""

        # スキップのチェック
        if skip_address_index is None:
            try:
                skip_address_index = self.skip_address_index
            except Exception:
                skip_address_index = []
        else:
            skip_address_index = []

        # Connection
        try:
            self.set_connection()
            # TCPの場合、ノード通信を実行
            if self.transport_layer_protocol in const.TRANSPORT_TCP:
                node_data = self.send_node_telegram()
            else:
                node_data = None
                self.sock.connect((self.ip_address, self.port))

            # 送信電文を生成
            if telegram_data is None:
                telegram_obj = self.generate_telegram(node_data=node_data)
                telegram_data = telegram_obj["data"]
            elif isinstance(telegram_data, str):
                telegram_data = [telegram_data]
        except socket.error as e:
            if e.errno is None:
                some_err_code.append(10060)
            else:
                some_err_code.append(e.errno)
            some_err_message.append(str(e))
        else:
            # 小分けした電文毎に通信・成功判定
            for index, telegram in enumerate(telegram_data):
                recv = None
                # スキップインデックスの場合処理をスキップ
                if len(skip_address_index) > 0 and index in skip_address_index:
                    recv = "skip"
                    error_code = 0
                    error_message = "SKIP"
                    recv_data += "0000" * self.segment_length[index]
                else:
                    error_code = 9999
                    error_message = ""
                    for i in range(const.RETRY_COUNT):
                        logger.debug(f"send telegram: {telegram}")

                        # 電文送信, 失敗した場合Retry countの回数分再送
                        self.sock.send(bytes(telegram))

                        # Recieved data.
                        try:
                            recv = self.sock.recv(1024).hex()
                            logger.debug("recv: {}".format(recv))
                        # WSAETIMEDOUT
                        except socket.timeout as e:
                            error_code = 10060
                            error_message = str(e)
                        # WSAECONNREFUSED
                        except socket.herror as e:
                            error_code = 10061
                            error_message = str(e)
                        except socket.gaierror as e:
                            error_code = 11001
                            error_message = str(e)
                        except socket.error as e:
                            error_code = 10065
                            error_message = str(e)
                        else:
                            try:
                                # エラーコードのチェック
                                checked_error_code = self.check_error_code(recv)
                                # SIDのチェック
                                checked_sid = self.check_sid(recv)

                                if checked_error_code["error_code"] == 0 and checked_sid["error_code"] == 0:
                                    error_code = checked_error_code["error_code"]
                                    error_message = checked_error_code["error_message"]
                                    break
                                else:
                                    error_code = checked_error_code["error_code"] if checked_error_code["error_code"] in [0, 9999] else checked_sid["error_code"]
                                    error_message = checked_error_code["error_message"] if checked_error_code["error_message"] in ["", "success", "SUCCESS"] else checked_sid["error_message"]

                            except Exception as e:
                                error_code = 9999 if error_code in [0, 9999] else error_code
                                error_message = str(e) if error_message == "" else error_message

                    else:
                        logger.debug(f"Retry count: {i+1}, Errcd: {error_code}, Message: {error_message}")
                        some_err_code.append(error_code)
                        some_err_message.append(error_message)
                        break

                    recv_data += recv[self.prefix_byte:]

                some_send_data.append(telegram)
                some_recv_data.append(recv)
                some_err_code.append(error_code)
                some_err_message.append(error_message)

        # 電文返答をデコード
        try:
            some_send_data = [x.hex() for x in some_send_data]
        except Exception:
            pass

        self.recv_data = recv_data
        error_code = max(some_err_code) if len(some_err_code) > 0 else None
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
    def convert_ascii_string(data: str, *, endian="") -> str:
        _string_data = []

        if len(data) <= 2:
            # Asciiは0x00~0x1Fは制御文字のため文字列としてはNullと扱う
            _1st_str = chr(int(data[:2], 16)) if int(
                data[:2], 16) >= 20 else ""
            _string_data.append(_1st_str)
        else:
            # Asciiは0x00~0x1Fは制御文字のため文字列としてはNullと扱う
            if endian in const.ENDIAN_BIG:
                _1st_str = chr(int(data[2:], 16)) if int(
                    data[2:], 16) >= 20 else ""
                _2nd_str = chr(int(data[:2], 16)) if int(
                    data[:2], 16) >= 20 else ""
            else:
                _1st_str = chr(int(data[:2], 16)) if int(
                    data[:2], 16) >= 20 else ""
                _2nd_str = chr(int(data[2:], 16)) if int(
                    data[2:], 16) >= 20 else ""
            _string_data.append(_1st_str)
            _string_data.append(_2nd_str)

        return "".join(_string_data)

    # 取得データをWord/Bit単位に分割
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
            _bit = 1

            _count = 0
            if self.bit_identify in const.BIT_DEVICE:
                for i in range(0, len(_devide_data), _byte):
                    if len(_devide_data[i: i + _byte]) < _byte:
                        _data = _devide_data[i: i + _byte] + ("0" * _byte)
                    else:
                        _data = _devide_data[i: i + _byte]

                    if self.endian in const.ENDIAN_LITTLE:
                        _data = _data[_bit:] + _data[:_bit]

                    _devide.append(int(_data, 16))

            elif self.bit_identify in const.WORD_DEVICE:
                for i in range(0, len(_devide_data), _word):
                    if len(_devide_data[i: i + _word]) < _word:
                        _data = _devide_data[i: i + _word] + ("0" * _word)
                    else:
                        _data = _devide_data[i: i + _word]

                    if self.endian in const.ENDIAN_LITTLE:
                        _data = _data[_byte:] + _data[:_byte]

                    # 文字列として返答
                    if self.cmd_option in const.STRING_DATA or self.optional_data_type in const.STRING_DATA:
                        # [0x00, 0x00]で区切り文字。それ以降はバッファが含まれる可能性があるので無視する
                        if _data == "0000":
                            break
                        else:
                            _string_data = self.convert_ascii_string(
                                _data, endian=self.endian)
                            _devide.append(_string_data)

                    # wordデバイスをbitとして使用している場合の返答
                    elif self.bit_identify in const.WORD_DEVICE and self.point_index is not None:
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
    try:
        connect = Connect(network, protocol, device, cmd, optional=optional)
    except Exception:
        result = {
            "error_code": 20001,
            "message": "There are some missing parts in the settings."
        }
    else:
        result_set_parameter = connect.set_parameter()
        logger.info(result_set_parameter)
        if result_set_parameter["error_code"] != 0:
            result = {
                "extract": [],
                "send": "",
                "receive": "",
                "error_code": result_set_parameter["error_code"],
                "message": Base.try_except_object(result_set_parameter, key="message", except_key="error_message", exception="")
            }
        else:
            result_send_telegram = connect.send_telegram()

            logger.info(result_send_telegram)
            if not (result_send_telegram["error_code"] == 0 and result_send_telegram["recv_data"] != []):
                result = {
                    "extract": [],
                    "send": result_send_telegram["some_send"],
                    "receive": result_send_telegram["some_recv"],
                    "error_code": result_send_telegram["error_code"],
                    "message": Base.try_except_object(result_send_telegram, key="some_err_message", except_key="error_message", exception="")
                }
            else:
                result_devide_received = connect.devide_received(recv_data=result_send_telegram["recv_data"])
                logger.info(result_devide_received)

                result = {
                    "extract": result_devide_received,
                    "send": result_send_telegram["some_send"],
                    "receive": result_send_telegram["some_recv"],
                    "error_code": result_send_telegram["error_code"],
                    "message": Base.try_except_object(result_send_telegram, key="some_err_message", except_key="error_message", exception="")
                }
    finally:
        try:
            del connect
        except Exception as e:
            logger.debug(str(e))
        finally:
            logger.debug(result)
            return result


class Connection():
    def __init__(self):
        pass

    def __del__(self):
        try:
            self.sock.close()
        except socket.error as e:
            logger.warning(str(e))
        except Exception as e:
            logger.warning(str(e))

    # Optionの確認
    def check_optional(self):
        self.telegram_data = []
        self.segment_length = []
        self.cmd_option = Base.try_except_object(self.cmd, key="option")

        self.optional_data_type = Base.try_except_object(
            self.optional, key="data_type")

        # STRING OPTINONの確認。Dataの型がstrの場合、強制的にSTRINGと扱う
        self.string_option = False
        if self.cmd_cmd in const.WRITE_COMMAND and (self.cmd_option in const.STRING_DATA or self.optional_data_type in const.STRING_DATA):
            self.string_option = True
            if isinstance(self.cmd_data, list) and all(isinstance(s, str) for s in self.cmd_data):
                self.cmd_data = "".join(self.cmd_data)

        # TIME OPTIONの確認
        self.time_option = False
        if (self.cmd_option in const.TIME_DATA or self.optional_data_type in const.TIME_DATA):
            self.time_option = True

    def check_decimal_point(self):
        try:
            self.point_index = self.str_min_address.index('.')
        except ValueError:
            try:
                self.point_index = self.str_max_address.index('.')
            except ValueError:
                self.point_index = None

    # デバイス/アドレス情報の定義
    def define_device_parameter(self):
        has_point = Base.try_except_object(
            self.protocol, key="point_index", exception=None)

        device_list = devices.device_list(
            manufacture=self.manufacture, series=self.series,
            transport=self.transport_layer_protocol,
            has_point=(has_point or self.point_index)
        )
        self.max_communicate_address_length = device_list["transfer_limit"]
        self.prefix_byte = device_list["prefix_byte"]
        self.endian = device_list["endian"]

        device_list_data = [x for x in device_list["devices"]
                            if x["symbol"] == self.device["device"]][0]
        self.device_code = [device_list_data["binary"]]
        self.bit_identify = device_list_data["identify"]
        self.decimal = device_list_data["decimal"]

        self.int_min_address = convert.decimal_convert(
            decimal=self.decimal, str_address=self.str_min_address)
        self.int_max_address = convert.decimal_convert(
            decimal=self.decimal, str_address=self.str_max_address)

        self.communicate_address_length = (
            self.int_max_address - self.int_min_address + 1)

    def check_withoutskip_optional(self):
        # SKIP OPTIONの確認 listに含まれているアドレスが必要なためスキップしない＝含まれない場合スキップ
        optional_without_skip = Base.try_except_object(
            self.optional, key="without_skip", except_key="only_use_address", exception=[])
        self.without_skip_address = []
        if self.cmd_cmd in const.READ_COMMAND and len(optional_without_skip) > 0:
            for without_skip_address in optional_without_skip:
                without_address = convert.decimal_convert(
                    decimal=self.decimal, str_address=without_skip_address)
                self.without_skip_address.append(
                    without_address - self.int_min_address
                )

    def define_parameter(self, network: dict, protocol: dict, device: dict, cmd: dict, *, optional: dict = None):
        try:
            self.network = network
            self.protocol = protocol
            self.device = device
            self.cmd = cmd
            self.optional = optional

            self.ip_address = self.network["ip"]
            try:
                self.port = int(network["port"])
            except ValueError:
                self.port = network["port"]
            self.cmd_cmd = self.cmd["cmd"]
            self.cmd_data = self.cmd["data"]
            self.transport_layer_protocol = self.protocol["transport_layer"]
            self.manufacture = self.protocol["manufacture"]
            self.series = self.protocol["series"]

            self.str_min_address = Base.try_except_object(
                self.device, key="min", except_key="minimum", exception=None)
            self.str_max_address = Base.try_except_object(
                self.device, key="max", except_key="maximum", exception=None)
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
        # 小数点の指定(bitの指定)があるかどうか
        self.check_decimal_point()

        # device parameterの定義
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

    def get_host_fourth_octet(self, ip_address, port):
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

        # logger.info(iplist)
        same_network = ip_address.rsplit('.', 1)[0]
        if len(iplist) > 0:
            try:
                client_ip = [x for x in iplist if same_network in x]
                fourth_octet = int(client_ip[0].rsplit('.', 1)[1])
            except Exception as e:
                logger.debug(
                    '{}:{}, {}'.format(
                        sys._getframe().f_code.co_name, e, 'No connection found. Please check your communication settings.'))
                fourth_octet = int(iplist[0].rsplit('.', 1)[1])
        else:
            fourth_octet = None
        return fourth_octet

    def generate_node_telegram(self):
        if self.transport_layer_protocol in const.TRANSPORT_TCP:
            header = [0x46, 0x49, 0x4E, 0x53]
            length = [0x00, 0x00, 0x00, 0x0C]
            tcp_command = [0x00, 0x00, 0x00, 0x00]
            error_code = [0x00, 0x00, 0x00, 0x00]
            client_node = [0x00, 0x00, 0x00, 0x00]
            node_telegram = (
                header + length + tcp_command + error_code + client_node
            )
            binary = b""
            for x in node_telegram:
                binary += struct.pack("B", x)
            self.node_telegram = binary

    def send_node_telegram(self):
        self.client_node = None
        self.server_node = None
        self.generate_node_telegram()
        try:
            self.sock.connect((self.ip_address, self.port))
            self.sock.send(bytes(self.node_telegram))
            recv_node = self.sock.recv(1024).hex()
        except socket.error as e:
            logger.warning(e)
            self.node_ecode = 10060
            self.node_error_message = str(e)
        else:
            node_ecode1 = recv_node[16:24]
            node_ecode2 = recv_node[24:32]

            # Node error handling.
            if int(node_ecode1, 16) not in [1, 64, 128]:
                self.node_ecode = 30098
                self.node_error_message = "node ecode1: {}".format(
                    node_ecode1)
            elif int(node_ecode2, 16) not in [0, 64, 128]:
                self.node_ecode = 30099
                self.node_error_message = "node ecode2: {}".format(
                    node_ecode2)
            else:
                self.client_node = int("0x" + recv_node[32:40], 16)
                self.server_node = int("0x" + recv_node[40:48], 16)
                self.node_ecode = 0
                self.node_error_message = "node success"

        return {
            "error_code": self.node_ecode,
            "message": self.node_error_message,
            "client_node": self.client_node,
            "server_node": self.server_node,
        }

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
                if self.point_index is None:
                    _min_ad = format(self.int_min_address + min_segment, "04x")
                    if self.endian in const.ENDIAN_BIG:
                        access_data_length.append(
                            [int(x, 16) for x in list(re.findall("..", _access_data_length))])
                        _first_address = [int(x, 16) for x in list(
                            re.findall("..", _min_ad))]
                    else:
                        access_data_length.append([int(x, 16) for x in list(
                            reversed(list(re.findall("..", _access_data_length))))])
                        _first_address = [int(x, 16) for x in list(
                            reversed(list(re.findall("..", _min_ad))))]
                    _first_address.append(0)
                # TODO
                else:
                    _, quotient, remainder = convert.each_convert(
                        self.decimal, self.int_min_address + min_segment)
                    padded_quotient = quotient.rjust(4, "0")
                    padded_remainder = remainder.rjust(2, "0")
                    padded = list(re.findall("..", padded_quotient)
                                  ) + [padded_remainder]

                    if self.endian in const.ENDIAN_BIG:
                        access_data_length.append(
                            [int(x, 16) for x in list(re.findall("..", _access_data_length))])
                        _first_address = [
                            int(x, 16) for x in padded]
                    else:
                        access_data_length.append([int(x, 16) for x in list(
                            reversed(list(re.findall("..", _access_data_length))))])
                        _first_address = [
                            int(x, 16) for x in list(reversed(padded))]

                first_address.append(_first_address)

        return {
            "cmd_data": cmd_data,
            "access_data_length": access_data_length,
            "first_address": first_address,
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
        return _cmd_data, _length

    def write_word(self, data: list):
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
                if self.endian in const.ENDIAN_BIG:
                    _cmd_data.append(
                        [int(_a + _b, 16), int(_c + _d, 16)])
                else:
                    _cmd_data.append(
                        [int(_c + _d, 16), int(_a + _b, 16)])
        _length = len(_cmd_data)
        return _cmd_data, _length

    def write_bit(self, data: list):
        _cmd_data = []
        if self.point_index is None:
            _data = [format(x, "01x") for x in data]
            it = iter(_data)
            for _a, _b in itertools.zip_longest(it, it, fillvalue="0"):
                _cmd_data.append(
                    [int(_a + _b, 16)])
            _length = len(_cmd_data) * 2
        else:
            _cmd_data.append(data)
            _length = len(data)
        return _cmd_data, _length

    # TODO
    def write_command(self):
        # Ex: W1.00 ~ W1.05 [1,1,0,0,1,0]
        # a = b"\x46\x49\x4E\x53\x00\x00\x00\x20\x00\x00\x00\x02\x00\x00\x00\x00\x80\x00\x02\x00\x01\x00\x00\xef\x00\x19\x01\x02\x31\x00\x00\x01\x00\x06\x01\x01\x00\x00\x01\x00"
        # Ex: W1 ~ W5 [1,1,0,0,1,0]
        # a = b"\x46\x49\x4e\x53\x00\x00\x00\x26\x00\x00\x00\x02\x00\x00\x00\x00\x80\x00\x02\x00\x01\x00\x00\xef\x00\x19\x01\x02\xb1\x00\x01\x00\x00\x06\x00\x01\x00\x01\x00\x00\x00\x00\x00\x01\x00\x00"

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
                    # _access_data_length = format(_length, "04x")
                    # _min_ad = format(
                    #     self.int_min_address + min_segment, "04x")

                    # if self.endian in const.ENDIAN_BIG:
                    #     access_data_length.append(
                    #         [int(x, 16) for x in list(re.findall("..", _access_data_length))])
                    #     _first_address = [int(x, 16) for x in list(
                    #         re.findall("..", _min_ad))]
                    # else:
                    #     access_data_length.append([int(x, 16) for x in list(
                    #         reversed(list(re.findall("..", _access_data_length))))])

                    #     _first_address = [int(x, 16) for x in list(
                    #         reversed(list(re.findall("..", _min_ad))))]
                    # first_address.append(_first_address)

                    _access_data_length = format(_length, "04x")
                    if self.point_index is None:
                        _min_ad = format(
                            self.int_min_address + min_segment, "04x")
                        if self.endian in const.ENDIAN_BIG:
                            access_data_length.append(
                                [int(x, 16) for x in list(re.findall("..", _access_data_length))])
                            _first_address = [int(x, 16) for x in list(
                                re.findall("..", _min_ad))]
                        else:
                            access_data_length.append([int(x, 16) for x in list(
                                reversed(list(re.findall("..", _access_data_length))))])
                            _first_address = [int(x, 16) for x in list(
                                reversed(list(re.findall("..", _min_ad))))]
                        _first_address.append(0)
                    # TODO
                    else:
                        _, quotient, remainder = convert.each_convert(
                            self.decimal, self.int_min_address + min_segment)
                        padded_quotient = quotient.rjust(4, "0")
                        padded_remainder = remainder.rjust(2, "0")
                        padded = list(re.findall(
                            "..", padded_quotient)) + [padded_remainder]

                        if self.endian in const.ENDIAN_BIG:
                            access_data_length.append(
                                [int(x, 16) for x in list(re.findall("..", _access_data_length))])
                            _first_address = [
                                int(x, 16) for x in padded]
                        else:
                            access_data_length.append([int(x, 16) for x in list(
                                reversed(list(re.findall("..", _access_data_length))))])
                            _first_address = [
                                int(x, 16) for x in list(reversed(padded))]

                    first_address.append(_first_address)

        return {
            "cmd_data": cmd_data,
            "access_data_length": access_data_length,
            "first_address": first_address,
        }

    def generate_telegram(self) -> list:
        self.skip_address_index = []

        if self.transport_layer_protocol in const.TRANSPORT_TCP:
            header = [0x46, 0x49, 0x4E, 0x53]
            tcp_command = [0x00, 0x00, 0x00, 0x02]
            error_code = [0x00, 0x00, 0x00, 0x00]
            node_data = self.send_node_telegram()
            if node_data["error_code"] == 0:
                da1 = [node_data["server_node"]]
                sa1 = [node_data["client_node"]]
            else:
                return node_data
        elif self.transport_layer_protocol in const.TRANSPORT_UDP:
            header = []
            tcp_command = []
            error_code = []
            client_ip = self.get_host_fourth_octet(self.ip_address, self.port)
            # client_ip = 52
            da1 = [0x00]
            sa1 = [client_ip]

        # Bit7=1:fixed value, Bit6=0:command, Bit0=0:need response
        # icf = [0x00]
        icf = [0x80]
        rsv = [0x00]
        # Number of allowable bridge passes.
        # Basically 0x02, 0x07: When using network crossings up to 8 layers.
        gct = [0x02]
        # Destination network address.
        # 0x00: Same network, 0x01~0x7F: Destination network
        dna = [0x00]
        da2 = [0x00]
        sna = [0x00]
        sa2 = [0x00]
        self.sid = random.randrange(0, 255, 1)
        sid = [self.sid]

        device_code = self.device_code

        if self.cmd_cmd in const.READ_COMMAND:
            command = [0x01, 0x01]
            command_data = self.read_command()
        else:
            # TODO
            command = [0x01, 0x02]
            command_data = self.write_command()

        arr_cmd_data = command_data["cmd_data"]
        arr_access_data_length = command_data["access_data_length"]
        arr_first_address = command_data["first_address"]
        for i in range(len(arr_access_data_length)):
            try:
                cmd_data = list(
                    (itertools.chain.from_iterable(arr_cmd_data[i])))
            except Exception:
                cmd_data = []
            access_data_length = arr_access_data_length[i]
            first_address = arr_first_address[i]

            if self.transport_layer_protocol in const.TRANSPORT_TCP:
                length_count = len(tcp_command + error_code + icf + rsv + gct + dna + da1 + da2 + sna + sa1 +
                                   sa2 + sid + command + device_code + first_address + access_data_length + cmd_data)

                _length = [int(x, 16) for x in list(
                    re.findall("..", format(length_count, "08x")))]
            else:
                _length = []

            if self.endian in const.ENDIAN_BIG:
                length = _length
            else:
                length = list(reversed(_length))

        _data = (
            header + length + tcp_command + error_code +
            icf + rsv + gct + dna + da1 + da2 + sna + sa1 + sa2 + sid +
            command + device_code + first_address + access_data_length + cmd_data
        )

        _binary = b""
        for x in _data:
            _binary += struct.pack("B", x)
        self.telegram_data.append(_binary)
        self.access_data_length = access_data_length
        return {
            "error_code": 0,
            "message": "SUCCESS",
            "data": self.telegram_data,
            "check": self.sid
        }

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
            if self.transport_layer_protocol in const.TRANSPORT_UDP:
                self.sock.connect((self.ip_address, self.port))
            # else:
            #     self.sock.connect((self.ip_address, self.port))
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
                        logger.debug("send: {}".format(telegram))

                        # Send data
                        self.sock.send(bytes(telegram))
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
                            # エラーコードを取得
                            try:
                                if self.transport_layer_protocol in const.TRANSPORT_UDP:
                                    ecode = (
                                        _recv[
                                            self.prefix_byte - 4: self.prefix_byte - 2
                                        ] +
                                        _recv[
                                            self.prefix_byte - 2: self.prefix_byte
                                        ]
                                    )
                                    # Bit7, Bit8はPLC本体の異常(バッテリ異常など)のため無視
                                    if int(ecode, 16) not in [0, 64, 128]:
                                        _err_code = ecode
                                    else:
                                        _err_code = 0
                                elif self.transport_layer_protocol in const.TRANSPORT_TCP:
                                    conn_ecode1 = _recv[16:24]
                                    conn_ecode2 = _recv[24:32]
                                    ecode = _recv[
                                        self.prefix_byte - 4: self.prefix_byte
                                    ]
                                    if int(conn_ecode1, 16) not in [2, 64, 128] and int(conn_ecode2, 16) not in [0, 64, 128]:
                                        ecode = conn_ecode2 + ',' + conn_ecode2
                                        _err_code = ecode if _err_code in [
                                            0, 9999] else _err_code
                                    elif int(ecode, 16) not in [0, 64, 128]:
                                        ecode = (
                                            _recv[
                                                self.prefix_byte - 4: self.prefix_byte - 2
                                            ] +
                                            _recv[
                                                self.prefix_byte - 2: self.prefix_byte
                                            ]
                                        )
                                        _err_code = ecode if _err_code in [
                                            0, 9999] else _err_code
                                    else:
                                        _err_code = 0

                                logger.debug("Error Code:{}".format(ecode))

                                # エラーコードのチェック
                                # error code 0x00 is Success. others is Error.
                                if _err_code == 0:
                                    # 送受信のidチェック
                                    try:
                                        recv_sid = int(
                                            _recv[self.prefix_byte - 10: self.prefix_byte - 8], 16)
                                        if recv_sid == self.sid:
                                            _error_message = "SUCCESS"
                                            _err_code = 0
                                            break
                                        else:
                                            _err_code = 221 if _err_code in [
                                                0, 9999] else _err_code
                                            _error_message = "SID for sending and receiving are different." if _err_message == "" else _err_message
                                    except Exception as e:
                                        _err_code = 222 if _err_code in [
                                            0, 9999] else _err_code
                                        _error_message = str(
                                            e) if _err_message == "" else _err_message
                            except Exception as e:
                                _err_code = 9999 if _err_code in [
                                    0, 9999] else _err_code
                                _err_message = str(
                                    e) if _err_message == "" else _err_message
                    else:
                        logger.debug("Retry count: {}".format(i + 1))
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
    def convert_ascii_string(data: str, *, endian="") -> str:
        _string_data = []

        if len(data) <= 2:
            # Asciiは0x00~0x1Fは制御文字のため文字列としてはNullと扱う
            _1st_str = chr(int(data[:2], 16)) if int(
                data[:2], 16) >= 20 else ""
            _string_data.append(_1st_str)
        else:
            # Asciiは0x00~0x1Fは制御文字のため文字列としてはNullと扱う
            if endian in const.ENDIAN_BIG:
                _1st_str = chr(int(data[2:], 16)) if int(
                    data[2:], 16) >= 20 else ""
                _2nd_str = chr(int(data[:2], 16)) if int(
                    data[:2], 16) >= 20 else ""
            else:
                _1st_str = chr(int(data[:2], 16)) if int(
                    data[:2], 16) >= 20 else ""
                _2nd_str = chr(int(data[2:], 16)) if int(
                    data[2:], 16) >= 20 else ""
            _string_data.append(_1st_str)
            _string_data.append(_2nd_str)

        return "".join(_string_data)

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
            _bit = 1

            _count = 0
            if self.bit_identify in const.BIT_DEVICE:
                for i in range(0, len(_devide_data), _byte):
                    if len(_devide_data[i: i + _byte]) < _byte:
                        _data = _devide_data[i: i + _byte] + ("0" * _byte)
                    else:
                        _data = _devide_data[i: i + _byte]

                    if self.endian in const.ENDIAN_LITTLE:
                        _data = _data[_bit:] + _data[:_bit]

                    _devide.append(int(_data, 16))

            elif self.bit_identify in const.WORD_DEVICE:
                for i in range(0, len(_devide_data), _word):
                    if len(_devide_data[i: i + _word]) < _word:
                        _data = _devide_data[i: i + _word] + ("0" * _word)
                    else:
                        _data = _devide_data[i: i + _word]

                    if self.endian in const.ENDIAN_LITTLE:
                        _data = _data[_byte:] + _data[:_byte]

                    # 文字列として返答
                    if self.cmd_option in const.STRING_DATA or self.optional_data_type in const.STRING_DATA:
                        # [0x00, 0x00]で区切り文字。それ以降はバッファが含まれる可能性があるので無視する
                        if _data == "0000":
                            break
                        else:
                            _string_data = self.convert_ascii_string(
                                _data, endian=self.endian)
                            _devide.append(_string_data)

                    # wordデバイスをbitとして使用している場合の返答
                    elif self.bit_identify in const.WORD_DEVICE and self.point_index is not None:
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


def _main(network: dict, protocol: dict, device: dict, cmd: dict, *, optional=None):
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
        send_data = connection.generate_telegram()
        logger.debug("send_data: {}".format(send_data))
        if send_data["error_code"] != 0:
            return {
                "extract": [],
                "send": [],
                "receive": [],
                "error_code": send_data["error_code"]
            }
        else:
            receive_data = connection.send_telegram()
            logger.debug("receive: {}".format(receive_data))

            devided_data = connection.devide_received()
            logger.debug("devide: {}".format(devided_data))
            error_code = receive_data["error_code"]
            result = {
                "extract": devided_data,
                "send": receive_data["some_send"],
                "receive": receive_data["recv_data"],
                "error_code": error_code,
                "some_receive": receive_data["some_recv"],
                "some_error_code": receive_data["some_err_code"],
                "some_error_message": receive_data["some_err_message"],
            }
    try:
        del connection
    except Exception:
        pass
    return result


if __name__ == "__main__":
    # オムロン
    network = {"ip": "192.168.250.1", "port": 9600}
    protocol = {"manufacture": "omron", "series": "nj",
                "protocol": "fins", "transport_layer": "udp", "point_index": None, }
    # device = {"device": "WR", "min": "1", "max": "5"}
    # device = {"device": "WR", "min": "1", "max": "1.10"}
    # device = {"device": "DM", "min": "5850", "max": "5860"}
    # device = {"device": "DM", "min": "5854", "max": "5857"}
    device = {"device": "DM", "min": "2000", "max": "2010"}
    cmd = {"cmd": "read", "data": [], "option": ""}
    # cmd = {"cmd": "write", "data": [1, 1, 1, 1, 1, 1], "option": ""}
    # cmd = {"cmd": "write", "data": [222, 333, 444, 555], "option": ""}
    # cmd = {"cmd": "write", "data": ["abcde"], "option": ""}
    optional = {
        # "without_skip": ["503", "1001"],
        "data_type": "string",

        # TODO
        # "data_type": "time",  # read: 0701, write: 0702
        # "data_type": "cycletime",  # read: 0620(min, max, average)
        # "data_type": "unit_status",  # read: 0601
        # "data_type": "alert",  # read: 2102
        # "data_type": "parameter_area",  # read: 0201, write: 0202
        # "data_type": "program_area",  # read: 0306, write: 0307
        # "data_type": "filename",  # read: 2201, rename: 2208
        # "data_type": "file_area",  # read: 2202, write: 2203, delete: 2205, copy: 2207
    }

    result = _main(
        network=network,
        protocol=protocol,
        device=device,
        cmd=cmd,
        optional=optional
    )
    logger.info(result)
    logger.info("=================================")
    # device = {"device": "DM", "min": "5854.00", "max": "5860.00"}
    # cmd = {"cmd": "read", "data": [], "option": ""}

    # result = _main(
    #     network=network,
    #     protocol=protocol,
    #     device=device,
    #     cmd=cmd,
    #     optional=optional
    # )
    # logger.info(result)