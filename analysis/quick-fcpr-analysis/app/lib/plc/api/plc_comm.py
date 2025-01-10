import os
import sys
import typing
import asyncio
import traceback
import re
import math
import struct
import datetime
import socket
# IF client pc is NOT Windows, need pip install
import psutil
try:
    import netifaces as ni
except Exception:
    pass

try:
    # Rev 0.9.4=
    from pyModbusTCP.client import ModbusClient
except Exception:
    pass
# other script
try:
    import logger
    import global_vars
    import device_list
    import convert_format
except Exception:
    from . import logger
    from . import global_vars
    from . import device_list
    from . import convert_format


# Logger
logger = logger.get_module_logger(__name__)


# Convert from negative value to signed hexadecimal.
def convert_signed(list_negative: list, *, word_count: int = 2) -> list:
    list_response = []
    for x in list_negative:
        len_hex = len('{:x}'.format(x).replace('-', ''))
        r_list = []
        value = x
        for i in range(int(word_count)):
            value, r = divmod(value, 65536)
            if int(x) >= 0:
                r_list.append(int(format(int(r), 'x'), 16))
            else:
                r_list.append(int(format(int(r) & 0xffff, 'x'), 16))
        if int(value) != 0 and int(value) != -1:
            if int(x) >= 0:
                hex_value = [int(format(int(int(value)), 'x'), 16)]
            else:
                hex_value = [int(format(int(int(value)) & 0xffff, 'x'), 16)]
        else:
            hex_value = []
        r_list.reverse()
        hex_value.extend(r_list)
        hex_value.reverse()
        list_response.extend(hex_value)
    return list_response


# vvv Pre-operation to secure a node for FINS communication vvv
def get_class_c_host_ip(ip_address) -> int:
    # Get the ClassC host of the IP address.
    # Windows.
    if os.name == "nt":
        iplist = socket.gethostbyname_ex(socket.gethostname())[2]
    # Linux or Mac.
    else:
        iplist = []
        address_list = psutil.net_if_addrs()
        for nic in address_list.keys():
            ni.ifaddresses(nic)
            try:
                ip = ni.ifaddresses(nic)[ni.AF_INET][0]['addr']
                if ip not in ["127.0.0.1"]:
                    iplist.append(ip)
            except KeyError as err:
                logger.debug(err)
    connection_ip = ip_address
    same_network_ip = connection_ip.rsplit('.', 1)[0]
    try:
        _client_ip = [x for x in iplist if same_network_ip in x]
        client_ip = _client_ip[0]
        class_c_host = int(client_ip.rsplit('.', 1)[1])
    except Exception as e:
        logger.warning(
            '{}:{}, {}'.format(
                sys._getframe().f_code.co_name, e, 'No connection found. Please check your communication settings.'
            )
        )
        # class_c_host = None
        class_c_host = int(iplist[0].rsplit('.', 1)[1])
    return class_c_host


def generate_node_telegram(protocol) -> bytes:
    if protocol in global_vars.g_FINS:
        header = (
            struct.pack('B', 0x46) +
            struct.pack('B', 0x49) +
            struct.pack('B', 0x4E) +
            struct.pack('B', 0x53)
        )  # header(only TCP)
        data_length = (
            struct.pack('B', 0x00) +
            struct.pack('B', 0x00) +
            struct.pack('B', 0x00) +
            struct.pack('B', 0x0C)
        )  # data length(only TCP)
        tcp_cmd = (
            struct.pack('B', 0x00) +
            struct.pack('B', 0x00) +
            struct.pack('B', 0x00) +
            struct.pack('B', 0x00)
        )  # command(only TCP)
        err_cd = (
            struct.pack('B', 0x00) +
            struct.pack('B', 0x00) +
            struct.pack('B', 0x00) +
            struct.pack('B', 0x00)
        )  # error code(only TCP)
        client_node_address = (
            struct.pack('B', 0x00) +
            struct.pack('B', 0x00) +
            struct.pack('B', 0x00) +
            struct.pack('B', 0x00)
        )  # client node address(only TCP)
        telegram_data = (
            header +
            data_length +
            tcp_cmd +
            err_cd +
            client_node_address
        )
    else:
        telegram_data = global_vars.g_CONNECTION_ERRORCODE
    return telegram_data
# ^^^ Pre-operation to secure a node for FINS communication ^^^


class ConnectToPlc:
    def __init__(self, plc_network: dict, plc_protocol: dict, device_parameter: dict, cmd_data: dict) -> None:  # Initialize Configure
        # Configure parameter.
        self.host = str(plc_network['ip'])
        self.port = int(plc_network['port'])
        self.manufacture = str(plc_protocol['manufacture']).lower()
        self.protocol = str(plc_protocol['protocol']).lower()
        self.series = str(plc_protocol['series']).lower()
        self.cmd = cmd_data['cmd']
        self.option = cmd_data['option']

        # Check Transport layer.
        try:
            self.transport_layer = str(plc_protocol['transport_layer']).lower()
        except Exception:
            self.transport_layer = 'tcp'

        # Check float parameter.
        try:
            self.period_index = device_parameter['min'].index('.')
        except ValueError:
            self.period_index = None

        # PLC register device parameter.
        device_info = device_list.device_list(
            self.manufacture, self.protocol, self.series, transport_layer=self.transport_layer, period_index=self.period_index)
        self.device_list = device_info['device']
        self.transfer_limit = device_info['transfer_limit']
        self.prefix_bit = device_info['prefix_bit']
        self.byte_order = device_info['byte_order']

        self.option = cmd_data['option']
        if self.option in global_vars.g_TIME_OPTION:
            self.time_option_configure()
        else:
            try:
                self.device = str(device_parameter['device']).upper()
                self.n_array = self.device_list[self.device][0]
                self.device_code = self.device_list[self.device][1]
                self.bit_identify = self.device_list[self.device][2]
            except Exception:
                self.device = None
                self.n_array = None
                self.device_code = None
                self.bit_identify = "bit"

            if self.cmd in global_vars.g_WRITE_COMMAND:
                if self.bit_identify in global_vars.g_IFY_WORD_DEVICE:
                    self.cmd_data, self.option = convert_format.check_string_and_convert_dhex(
                        cmd_data["data"], self.byte_order, self.option)
                    try:
                        self.cmd_data = convert_format.convert_negative_integer_to_signed_hex(
                            self.cmd_data, word_count=1)
                    except Exception:
                        pass
                else:
                    self.cmd_data = cmd_data["data"]
            else:
                self.cmd_data = []
            try:
                convert_decimal = device_list.convert_to_decimal(
                    self.n_array, device_parameter)
                self.lead_number = convert_decimal['lead_number']
                self.send_length = convert_decimal['send_length']
                self.transfer_count = math.ceil(
                    self.send_length / self.transfer_limit)
                if self.send_length % 2 != 0:
                    self.bit_odd_flag = True
                else:
                    self.bit_odd_flag = False
            except Exception:
                self.lead_number = None
                self.send_length = None
                self.transfer_count = 1
                self.bit_odd_flag = None

    # Get/Write timedata to PLC.
    def time_option_configure(self):
        device_parameter = {}
        if self.protocol in global_vars.g_MCPROTOCOL3E:
            if self.manufacture in global_vars.g_MITSUBISHI:
                device_parameter["device"] = "SD"
                device_parameter["min"] = "210"
                device_parameter["max"] = "216"
                self.device = str(device_parameter['device']).upper()
                self.n_array = self.device_list[self.device][0]
                self.device_code = self.device_list[self.device][1]
                self.bit_identify = self.device_list[self.device][2]
            elif self.manufacture in global_vars.g_PANASONIC:
                if self.series in ["fp7", "7"]:
                    pass
                else:
                    device_parameter["device"] = "SDT"
                    device_parameter["min"] = "54"
                    device_parameter["max"] = "57"
                self.device = str(device_parameter['device']).upper()
                self.n_array = self.device_list[self.device][0]
                self.device_code = self.device_list[self.device][1]
                self.bit_identify = self.device_list[self.device][2]
            elif self.manufacture in global_vars.g_KEYENCE:
                device_parameter["device"] = "CM"
                device_parameter["min"] = "700"
                device_parameter["max"] = "706"
                self.device = str(device_parameter['device']).upper()
                self.n_array = self.device_list[self.device][0]
                self.device_code = self.device_list[self.device][1]
                self.bit_identify = self.device_list[self.device][2]
        elif self.protocol in global_vars.g_FINS:
            if self.manufacture in global_vars.g_OMRON:
                self.device = None
                self.n_array = None
                self.device_code = None
                self.bit_identify = "bit"
        else:
            self.device = None
            self.n_array = None
            self.device_code = None

        if self.cmd in global_vars.g_WRITE_COMMAND:
            self.cmd_data = cmd_data['data']
        else:
            self.cmd_data = []
        try:
            convert_decimal = device_list.convert_to_decimal(
                self.n_array, device_parameter
            )
            self.lead_number = convert_decimal['lead_number']
            self.send_length = convert_decimal['send_length']
            self.transfer_count = math.ceil(
                self.send_length / self.transfer_limit)
            self.bit_odd_flag = False
        except Exception:
            self.lead_number = None
            self.send_length = None
            self.transfer_count = 1
            self.bit_odd_flag = None

    # Generate a telegram to be sent.
    def generate_telegram(self, current_count: int) -> bytes:
        try:
            # ======= ETHERNET CONNECTION =======
            # ======= MC Protocol / 1E Frame =======
            if self.protocol in global_vars.g_MCPROTOCOL1E:
                pc_number = struct.pack('B', 0xFF)
                cpu_speed = (struct.pack('B', 0x10) + struct.pack('B', 0x00))
                # The device code of a 1E frame consists of 4 bytes.
                device_code = (
                    struct.pack('B', self.device_code[1]) +
                    struct.pack('B', self.device_code[0])
                )
                # Extract each hexadecimal digit and reconvert for transmission.
                #  X, Y device need to be converted from octal descriptions to hexadecimal binaries.
                if self.device == 'X' or self.device == 'Y':
                    lead_device = (
                        int(self.lead_number, 8) +
                        current_count * self.transfer_limit
                    )
                else:
                    lead_device = (
                        self.lead_number +
                        current_count * self.transfer_limit
                    )
                bits = '{:08x}'.format(lead_device)
                hex_lead_bit = (
                    struct.pack('B', int(bits[6] + bits[7], 16)) +
                    struct.pack('B', int(bits[4] + bits[5], 16)) +
                    struct.pack('B', int(bits[2] + bits[3], 16)) +
                    struct.pack('B', int(bits[0] + bits[1], 16))
                )
                delimiter = struct.pack('B', 0x00)
                # For the Read command.
                if self.cmd in global_vars.g_READ_COMMAND:
                    remain_length = (
                        self.send_length -
                        current_count * self.transfer_limit
                    )
                    if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                        sub_header = struct.pack('B', 0x00)
                    elif self.bit_identify in global_vars.g_IFY_WORD_DEVICE:
                        sub_header = struct.pack('B', 0x01)
                    else:
                        raise ValueError(
                            '{}, {}'.format(
                                sys._getframe().f_code.co_name, 'This bit_identify is not supported.'
                            )
                        )
                # For the Write command
                elif self.cmd in global_vars.g_WRITE_COMMAND:
                    remain_length = (
                        self.send_length -
                        current_count * self.transfer_limit
                    )
                    if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                        sub_header = struct.pack('B', 0x02)
                    elif self.bit_identify in global_vars.g_IFY_WORD_DEVICE:
                        sub_header = struct.pack('B', 0x03)
                    else:
                        raise ValueError(
                            '{}, {}'.format(
                                sys._getframe().f_code.co_name, 'This bit_identify is not supported.'
                            )
                        )
                else:
                    raise ValueError(
                        '{}, {}'.format(
                            sys._getframe().f_code.co_name, 'This cmd is not supported.'
                        )
                    )
                # Check the transmission limit.
                if remain_length >= self.transfer_limit:
                    bits_dnum = '{:02x}'.format(self.transfer_limit)
                else:
                    bits_dnum = '{:02x}'.format(remain_length)
                data_count = (
                    struct.pack('B', int(bits_dnum[0] + bits_dnum[1], 16))
                )
                telegram_data = (
                    sub_header + pc_number + cpu_speed +
                    hex_lead_bit + device_code + data_count + delimiter
                )

            # ======= MC Protocol / 3E Frame =======
            elif self.protocol in global_vars.g_MCPROTOCOL3E:
                sub_header = (
                    struct.pack('B', 0x50) +
                    struct.pack('B', 0x00)
                )
                network = struct.pack('B', 0x00)
                pc_number = struct.pack('B', 0xff)
                unit_io = (
                    struct.pack('B', 0xff) +
                    struct.pack('B', 0x03)
                )
                unit_number = struct.pack('B', 0x00)
                cpu_speed = (
                    struct.pack('B', 0x10) +
                    struct.pack('B', 0x00)
                )
                if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                    sub_cmd = (
                        struct.pack('B', 0x01) +
                        struct.pack('B', 0x00)
                    )
                elif self.bit_identify in global_vars.g_IFY_WORD_DEVICE:
                    sub_cmd = (
                        struct.pack('B', 0x00) +
                        struct.pack('B', 0x00)
                    )
                else:
                    raise ValueError(
                        '{}, {}'.format(
                            sys._getframe().f_code.co_name, 'This bit_identify is not supported.'
                        )
                    )
                # Extract each hexadecimal digit and reconvert for transmission.
                lead_bit = (
                    self.lead_number + current_count * self.transfer_limit
                )
                device_code = struct.pack('B', self.device_code)
                # For the Read command
                if self.cmd in global_vars.g_READ_COMMAND:

                    # Number of bits acquired
                    bits = '{:06x}'.format(lead_bit)
                    hex_lead_bit = (
                        struct.pack('B', int(bits[4] + bits[5], 16)) +
                        struct.pack('B', int(bits[2] + bits[3], 16)) +
                        struct.pack('B', int(bits[0] + bits[1], 16))
                    )
                    remain_length = (
                        self.send_length - current_count * self.transfer_limit
                    )
                    if self.bit_identify in global_vars.g_IFY_WORD_DEVICE:
                        if remain_length % 2 != 0:
                            # remain_length += 1
                            self.odd_flag = True
                    if remain_length >= self.transfer_limit:
                        bits_vol = '{:04x}'.format(self.transfer_limit)
                    else:
                        bits_vol = '{:04x}'.format(remain_length)

                    data_count = (
                        struct.pack('B', int(bits_vol[2] + bits_vol[3], 16)) +
                        struct.pack(
                            'B', int(bits_vol[0] + bits_vol[1], 16))
                    )
                    cmd = struct.pack('B', 0x01) + struct.pack('B', 0x04)
                    data_length = (
                        struct.pack('B', 0x0c) + struct.pack('B', 0x00))
                    telegram_data = (
                        sub_header +
                        network +
                        pc_number +
                        unit_io +
                        unit_number +
                        data_length +
                        cpu_speed +
                        cmd +
                        sub_cmd +
                        hex_lead_bit +
                        device_code +
                        data_count
                    )

                    if self.option == 'comment':
                        telegram_data = (
                            sub_header +
                            network +
                            pc_number +
                            unit_io +
                            unit_number +
                            data_length +
                            cpu_speed +
                            (struct.pack('B', 0xa4) + struct.pack('B', 0x45)) +
                            (struct.pack('B', 0x10) + struct.pack('B', 0x03)) +
                            hex_lead_bit +
                            device_code +
                            data_count
                        )

                # For the Write command
                elif self.cmd in global_vars.g_WRITE_COMMAND:
                    if (self.option in global_vars.g_STRING_OPTION and self.bit_identify in global_vars.g_IFY_WORD_DEVICE):
                        if self.manufacture in global_vars.g_PANASONIC:
                            bits = '{:06x}'.format(lead_bit + 1)
                        else:
                            bits = '{:06x}'.format(lead_bit)
                    else:
                        bits = '{:06x}'.format(lead_bit)
                    hex_lead_bit = (
                        struct.pack('B', int(bits[4] + bits[5], 16)) +
                        struct.pack('B', int(bits[2] + bits[3], 16)) +
                        struct.pack('B', int(bits[0] + bits[1], 16))
                    )
                    cmd = (
                        struct.pack('B', 0x01) +
                        struct.pack('B', 0x14)
                    )
                    # Write data.
                    w_data = []
                    temp_data = []
                    length = 0
                    if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                        if len(self.cmd_data) % 2 != 0:
                            self.cmd_data.append(0)
                            self.bit_odd_flag = True
                        it = iter(self.cmd_data)
                        for i, j in zip(it, it):
                            w_data.append([j, i])

                    else:
                        for i in range(len(self.cmd_data)):
                            if self.cmd_data[i] >= 0:
                                _hex_w_data = '{:x}'.format(self.cmd_data[i])
                            else:
                                _hex_w_data = format(
                                    self.cmd_data[i] & 0xffff, 'x'
                                )
                            length += len(_hex_w_data) / 2
                            if self.option in global_vars.g_STRING_OPTION:
                                for j in range((int(len(_hex_w_data) // 4.01)) + 1):
                                    if len(_hex_w_data) >= 2:
                                        if j == 0:
                                            four_hex = '{:0>4s}'.format(
                                                _hex_w_data[-4:]
                                            )
                                        elif j == len(_hex_w_data) // 4:
                                            continue
                                        else:
                                            four_hex = '{:0>4s}'.format(
                                                _hex_w_data[
                                                    (j + 1) * (-4): j * (-4)
                                                ]
                                            )
                                        w_data.append(
                                            [
                                                int(four_hex[0] +
                                                    four_hex[1], 16),
                                                int(four_hex[2] +
                                                    four_hex[3], 16)
                                            ]
                                        )
                                    else:
                                        if len(temp_data) >= 2:
                                            temp_data = []
                                        if j == 0:
                                            if i % 2 == 0:
                                                temp_data.insert(
                                                    0, '{:0>2s}'.format(
                                                        _hex_w_data[-2:]
                                                    )
                                                )
                                                if i == len(self.cmd_data):
                                                    w_data.append(
                                                        [int(temp_data[0], 16), 0]
                                                    )
                                            else:
                                                temp_data.insert(
                                                    0, '{:0>2s}'.format(
                                                        _hex_w_data[-2:]
                                                    )
                                                )
                                                try:
                                                    w_data.append(
                                                        [
                                                            int(temp_data[0], 16),
                                                            int(temp_data[1], 16)
                                                        ]
                                                    )
                                                except Exception:
                                                    w_data.append(
                                                        [
                                                            int(temp_data[0], 16),
                                                            0
                                                        ]
                                                    )

                                        else:
                                            if i % 2 == 0:
                                                temp_data.insert(
                                                    0, '{:0>2s}'.format(
                                                        _hex_w_data[
                                                            (j + 1) * (-2):j * (-2)
                                                        ]
                                                    )
                                                )
                                                if i == len(self.cmd_data):
                                                    w_data.append(
                                                        [int(temp_data[0], 16), 0]
                                                    )
                                            else:
                                                temp_data.insert(
                                                    0, '{:0>2s}'.format(
                                                        _hex_w_data[
                                                            (j + 1) * (-2):j * (-2)
                                                        ]
                                                    )
                                                )
                                                try:
                                                    w_data.append(
                                                        [
                                                            int(temp_data[0], 16),
                                                            int(temp_data[1], 16)
                                                        ]
                                                    )
                                                except Exception:
                                                    w_data.append(
                                                        [
                                                            int(temp_data[0], 16),
                                                            0
                                                        ]
                                                    )

                                        if i == len(self.cmd_data):
                                            try:
                                                w_data.append(
                                                    [
                                                        int(temp_data[0], 16),
                                                        int(temp_data[1], 16)
                                                    ]
                                                )
                                            except Exception:
                                                w_data.append(
                                                    [int(temp_data[0], 16)]
                                                )
                            else:
                                for j in range(int((len(_hex_w_data) // 4.01)) + 1):
                                    if len(_hex_w_data) <= 4:
                                        four_hex = '{:0>4s}'.format(
                                            _hex_w_data[-4:]
                                        )
                                    else:
                                        four_hex = '{:0>4s}'.format(
                                            _hex_w_data[(j + 1) *
                                                        (-4):j * (-4)]
                                        )
                                    w_data.append(
                                        [
                                            int(four_hex[0] + four_hex[1], 16),
                                            int(four_hex[2] + four_hex[3], 16)
                                        ]
                                    )
                    # Number of bits acquired
                    if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                        remain_length = (
                            len(w_data) * 2 -
                            current_count * self.transfer_limit
                        )
                        if remain_length >= self.transfer_limit:
                            if self.bit_odd_flag:
                                bits_vol = '{:04x}'.format(
                                    self.transfer_limit - 1)
                            else:
                                bits_vol = '{:04x}'.format(self.transfer_limit)
                        else:
                            if self.bit_odd_flag:
                                bits_vol = '{:04x}'.format(remain_length - 1)
                            else:
                                bits_vol = '{:04x}'.format(remain_length)
                    else:
                        if self.option in global_vars.g_STRING_OPTION:
                            if self.manufacture in global_vars.g_PANASONIC:
                                w_data_length = '{:0>4s}'.format(
                                    str(int(length)))
                                w_data.insert(
                                    0, [
                                        int(w_data_length[:-2], 10),
                                        int(w_data_length[-2:], 10)
                                    ]
                                )
                            else:
                                w_data.append([0, 0])
                        remain_length = (
                            len(w_data) -
                            current_count * self.transfer_limit
                        )
                        if remain_length >= self.transfer_limit:
                            bits_vol = '{:04x}'.format(self.transfer_limit)
                        else:
                            bits_vol = '{:04x}'.format(remain_length)

                    data_count = (
                        struct.pack('B', int(bits_vol[2] + bits_vol[3], 16)) +
                        struct.pack('B', int(bits_vol[0] + bits_vol[1], 16))
                    )
                    # data_count = struct.pack('B', 2) + struct.pack('B', 0)

                    # Communication data length.
                    # If the write is bit, add to the command byte length 12, or
                    # If the writing is a word, add x2 to the command's byte length of 12.
                    cmd_data = b''
                    if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                        characters = 12 + int(remain_length / 2)
                        temp_dleng = '{:04x}'.format(characters)
                        data_length = (
                            struct.pack('B', int(temp_dleng[2] + temp_dleng[3], 16)) +
                            struct.pack(
                                'B', int(temp_dleng[0] + temp_dleng[1], 16)
                            )
                        )
                        for i, x in enumerate(w_data):
                            try:
                                cmd_data += struct.pack('B', x[1] * 16 + x[0])
                            except Exception:
                                cmd_data += struct.pack("B", x[0])

                    elif self.bit_identify in global_vars.g_IFY_WORD_DEVICE:
                        characters = 12 + remain_length * 2
                        temp_dleng = '{:04x}'.format(characters)
                        # temp_dleng = "001a"
                        data_length = (
                            struct.pack('B', int(temp_dleng[2] + temp_dleng[3], 16)) +
                            struct.pack(
                                'B', int(temp_dleng[0] + temp_dleng[1], 16)
                            )
                        )
                        for i, x in enumerate(w_data):
                            cmd_data += (
                                struct.pack('B', x[1]) +
                                struct.pack('B', x[0])
                            )
                    else:
                        raise ValueError(
                            '{}, {}'.format(
                                sys._getframe().f_code.co_name, 'This bit_identify is not supported.'
                            )
                        )

                    telegram_data = (
                        sub_header +
                        network +
                        pc_number +
                        unit_io +
                        unit_number +
                        data_length +
                        cpu_speed +
                        cmd +
                        sub_cmd +
                        hex_lead_bit +
                        device_code +
                        data_count +
                        cmd_data
                    )
                else:
                    raise ValueError(
                        '{}, {}'.format(
                            sys._getframe().f_code.co_name, 'This cmd is not supported.'
                        )
                    )

            # ======= FINS =======
            elif self.protocol in global_vars.g_FINS:
                # TCP header
                header = (
                    struct.pack('B', 0x46) +
                    struct.pack('B', 0x49) +
                    struct.pack('B', 0x4E) +
                    struct.pack('B', 0x53)
                )     # TCP header(only TCP)
                tcp_cmd = (
                    struct.pack('B', 0x00) +
                    struct.pack('B', 0x00) +
                    struct.pack('B', 0x00) +
                    struct.pack('B', 0x02)
                )     # TCP command(only TCP)
                err_cd = (
                    struct.pack('B', 0x00) +
                    struct.pack('B', 0x00) +
                    struct.pack('B', 0x00) +
                    struct.pack('B', 0x00)
                )     # TCP error code(only TCP)
                # FINS header
                # ICF. Bit7=1:fixed value, Bit6=0:command, Bit0=0:need response
                icf = struct.pack('B', 0x80)
                rsv = struct.pack('B', 0x00)                # RSV. fixed value
                # Number of allowable bridge passes. Basically 0x02, 0x07: When using network crossings up to 8 layers.
                gct = struct.pack('B', 0x02)
                # Destination network address. 0x00: Same network, 0x01~0x7F: Destination network
                dna = struct.pack('B', 0x00)
                if self.transport_layer in global_vars.g_UDPIP:
                    client_ip_address = get_class_c_host_ip(self.host)
                    da1 = struct.pack('B', 0x00)
                    sa1 = struct.pack('B', client_ip_address)
                else:
                    # Destination node address. # 0x00: in own PLC, 0x01~20: ControllerLink, 0x01~FE: Ethernet, 0xFF: Simultaneous broadcast
                    da1 = struct.pack('B', self.server_node)
                    # Source node address. # 0x01~FE TCP: Specify No. 5 of the response, UDP: 4th digit of the PC-side IP address.
                    sa1 = struct.pack('B', self.client_node)
                # Destination Unit Address. # 0x00: CPU unit, 0xFE: ControllerLink or Ethernet unit, 0x10~1F: CPU Advanced Function Unit, 0xE1: INNER board.
                da2 = struct.pack('B', 0x00)
                # Source network address. # 0x00: same network, 0x01~0x7F: source network.
                sna = struct.pack('B', 0x00)
                # Source address. # fixed value
                sa2 = struct.pack('B', 0x00)
                # Service ID. # 0x00~FF Any, source identifier.
                sid = struct.pack('B', 0x19)

                # no parameter format
                if self.option in global_vars.g_TIME_OPTION:
                    if self.cmd in global_vars.g_READ_COMMAND:
                        cmd_code = "0701"
                        cmd = (
                            struct.pack("B", int(cmd_code[0:2], 16)) +
                            struct.pack("B", int(cmd_code[2:4], 16))
                        )
                        # Transmission length.
                        data_length = (
                            struct.pack('B', 0x00) +
                            struct.pack('B', 0x00) +
                            struct.pack('B', 0x00) +
                            struct.pack('B', 0x1A)
                        )
                        if self.transport_layer in global_vars.g_UDPIP:
                            telegram_data = (
                                icf +
                                rsv +
                                gct +
                                dna +
                                da1 +
                                da2 +
                                sna +
                                sa1 +
                                sa2 +
                                sid +
                                cmd
                            )
                        else:
                            telegram_data = (
                                header +
                                data_length +
                                tcp_cmd +
                                err_cd +
                                icf +
                                rsv +
                                gct +
                                dna +
                                da1 +
                                da2 +
                                sna +
                                sa1 +
                                sa2 +
                                sid +
                                cmd
                            )
                    elif self.cmd in global_vars.g_WRITE_COMMAND:
                        cmd_code = "0702"
                        cmd = (
                            struct.pack("B", int(cmd_code[0:2], 16)) +
                            struct.pack("B", int(cmd_code[2:4], 16))
                        )
                        if len(self.cmd_data) == 5:
                            # 秒を00にして曜日算出
                            year = int(self.cmd_data[0])
                            month = int(self.cmd_data[1])
                            day = int(self.cmd_data[2])
                            if year >= 98:
                                year += 1900
                            else:
                                year += 2000
                            add_data = ["00", format(
                                datetime.date(year, month, day).weekday() + 1, "02")]
                            self.cmd_data.extend(add_data)
                        elif len(self.cmd_data) == 6:
                            # 曜日算出
                            year = int(self.cmd_data[0])
                            month = int(self.cmd_data[1])
                            day = int(self.cmd_data[2])
                            if year >= 98:
                                year += 1900
                            else:
                                year += 2000
                            add_data = [
                                format(datetime.date(year, month, day).weekday() + 1, "02")]
                            self.cmd_data.extend(add_data)
                        elif len(self.cmd_data) >= 7:
                            # 7データまでを入力
                            self.cmd_data = self.cmd_data[:7]
                        cmd_data = b''
                        for data in self.cmd_data:
                            try:
                                cmd_data += struct.pack("B",
                                                        int(str(data), 16))
                            except Exception:
                                pass
                        # Data length.
                        _data_len = '{:08x}'.format(
                            26 + (len(self.cmd_data) * 2))
                        data_length = (
                            struct.pack('B', int(_data_len[0] + _data_len[1], 16)) +
                            struct.pack('B', int(_data_len[2] + _data_len[3], 16)) +
                            struct.pack('B', int(_data_len[4] + _data_len[5], 16)) +
                            struct.pack(
                                'B', int(_data_len[6] + _data_len[7], 16))
                        )
                        if self.transport_layer in global_vars.g_UDPIP:
                            telegram_data = (
                                icf +
                                rsv +
                                gct +
                                dna +
                                da1 +
                                da2 +
                                sna +
                                sa1 +
                                sa2 +
                                sid +
                                cmd +
                                cmd_data
                            )
                        else:
                            telegram_data = (
                                header +
                                data_length +
                                tcp_cmd +
                                err_cd +
                                icf +
                                rsv +
                                gct +
                                dna +
                                da1 +
                                da2 +
                                sna +
                                sa1 +
                                sa2 +
                                sid +
                                cmd +
                                cmd_data
                            )
                elif self.option in ["warning"]:
                    cmd_code = '2102'
                    cmd = (
                        struct.pack('B', int(cmd_code[0:2], 16)) +
                        struct.pack('B', int(cmd_code[2:4], 16))
                    )
                    read_start = struct.pack(
                        'B', 0x00) + struct.pack('B', 0x00)
                    read_count = struct.pack(
                        'B', 0x01) + struct.pack('B', 0x00)

                    # Transmission length.
                    data_length = (
                        struct.pack('B', 0x00) +
                        struct.pack('B', 0x00) +
                        struct.pack('B', 0x00) +
                        struct.pack('B', 0x1A)
                    )
                    if self.transport_layer in global_vars.g_UDPIP:
                        telegram_data = (
                            icf +
                            rsv +
                            gct +
                            dna +
                            da1 +
                            da2 +
                            sna +
                            sa1 +
                            sa2 +
                            sid +
                            cmd +
                            read_start +
                            read_count
                        )
                    else:
                        telegram_data = (
                            header +
                            data_length +
                            tcp_cmd +
                            err_cd +
                            icf +
                            rsv +
                            gct +
                            dna +
                            da1 +
                            da2 +
                            sna +
                            sa1 +
                            sa2 +
                            sid +
                            cmd +
                            read_start +
                            read_count
                        )
                else:
                    # Devices code
                    device_code = struct.pack('B', self.device_code)

                    # Extract each hexadecimal digit and reconvert for transmission.
                    # The first and second bytes are device numbers,
                    # and the third byte is a bit number within the device. (In the case of word, this is basically '0x00'.)
                    lead_device = (
                        self.lead_number +
                        current_count * self.transfer_limit
                    )
                    if self.n_array == '10.10':
                        q, mod = divmod(lead_device, 16)
                        bits1 = '{:04x}'.format(q)
                        bits2 = '{:02x}'.format(mod)
                        temp1 = int(bits1[0] + bits1[1], 16)
                        temp2 = int(bits1[2] + bits1[3], 16)
                        temp3 = int(bits2[0] + bits2[1], 16)
                    else:
                        bits = '{:04x}'.format(lead_device)
                        temp1 = int(bits[0] + bits[1], 16)
                        temp2 = int(bits[2] + bits[3], 16)
                        temp3 = 0x00
                    lead_device_number = (
                        struct.pack('B', temp1) +
                        struct.pack('B', temp2) +
                        struct.pack('B', temp3)
                    )

                    # Read command telegram.
                    if self.cmd in global_vars.g_READ_COMMAND:
                        cmd = (
                            struct.pack('B', 0x01) +
                            struct.pack('B', 0x01)
                        )
                        # Transmission length.
                        data_length = (
                            struct.pack('B', 0x00) +
                            struct.pack('B', 0x00) +
                            struct.pack('B', 0x00) +
                            struct.pack('B', 0x1A)
                        )
                        # Number of bits acquired
                        if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                            integer_sendlength = (
                                str(self.send_length)[
                                    :len(str(self.send_length)) - 2
                                ]
                            )
                            if integer_sendlength == '':
                                integer_sendlength = 0
                            few_sendlength = (
                                str(self.send_length)[
                                    len(str(self.send_length)) - 2:
                                ]
                            )
                            remain_length = (
                                int(integer_sendlength) * 16 +
                                int(few_sendlength) -
                                current_count * self.transfer_limit
                            )
                        else:
                            remain_length = (
                                self.send_length -
                                current_count * self.transfer_limit
                            )

                        # Check the transmission limit.
                        if remain_length >= self.transfer_limit:
                            bits_dnum = '{:04x}'.format(self.transfer_limit)
                        else:
                            bits_dnum = '{:04x}'.format(remain_length)
                        device_count = (
                            struct.pack('B', int(bits_dnum[0] + bits_dnum[1], 16)) +
                            struct.pack(
                                'B', int(bits_dnum[2] + bits_dnum[3], 16))
                        )
                        if self.transport_layer in global_vars.g_UDPIP:
                            telegram_data = (
                                icf +
                                rsv +
                                gct +
                                dna +
                                da1 +
                                da2 +
                                sna +
                                sa1 +
                                sa2 +
                                sid +
                                cmd +
                                device_code +
                                lead_device_number +
                                device_count
                            )
                        else:
                            telegram_data = (
                                header +
                                data_length +
                                tcp_cmd +
                                err_cd +
                                icf +
                                rsv +
                                gct +
                                dna +
                                da1 +
                                da2 +
                                sna +
                                sa1 +
                                sa2 +
                                sid +
                                cmd +
                                device_code +
                                lead_device_number +
                                device_count
                            )
                    # Write command telegram.
                    elif self.cmd in global_vars.g_WRITE_COMMAND:
                        cmd = (
                            struct.pack('B', 0x01) +
                            struct.pack('B', 0x02)
                        )
                        # Converts write data into 2 bytes of hexadecimal numbers.
                        w_data = []
                        for i in range(len(self.cmd_data)):
                            if self.cmd_data[i] >= 0:
                                _hex_w_data = '{:x}'.format(self.cmd_data[i])
                            else:
                                _hex_w_data = format(
                                    self.cmd_data[i] & 0xffff, 'x'
                                )
                            for j in range((len(_hex_w_data) // 5) + 1):
                                if j == 0:
                                    four_hex = '{:0>4s}'.format(
                                        _hex_w_data[-4:])
                                else:
                                    four_hex = '{:0>4s}'.format(
                                        _hex_w_data[(j + 1) * (-4):j * (-4)]
                                    )
                                w_data.append(
                                    [
                                        int(four_hex[0] + four_hex[1], 16),
                                        int(four_hex[2] + four_hex[3], 16)
                                    ]
                                )
                        # For Big Endian, reverse order acquisition is further reversed to reverse order.
                        for i in range(len(w_data)):
                            if i == 0:
                                if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                                    cmd_data = struct.pack('B', w_data[i][1])
                                else:
                                    cmd_data = (
                                        struct.pack('B', w_data[i][0]) +
                                        struct.pack('B', w_data[i][1])
                                    )
                            else:
                                if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                                    cmd_data = (
                                        cmd_data +
                                        struct.pack('B', w_data[i][1])
                                    )
                                else:
                                    cmd_data = (
                                        cmd_data +
                                        struct.pack('B', w_data[i][0]) +
                                        struct.pack('B', w_data[i][1])
                                    )
                        for i in range(len(self.cmd_data)):
                            for j in range((self.cmd_data[i] // 65535) + 1):
                                # Number of bits acquired
                                if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                                    remain_length = (
                                        self.send_length * (len(w_data) // 17 + 1) -
                                        (current_count * self.transfer_limit)
                                    )
                                else:
                                    remain_length = (
                                        self.send_length -
                                        current_count * self.transfer_limit
                                    )
                                # Check the transmission limit.
                                if remain_length >= self.transfer_limit:
                                    if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                                        bits_dnum = '{:04x}'.format(
                                            self.transfer_limit
                                        )
                                    else:
                                        bits_dnum = '{:04x}'.format(
                                            self.transfer_limit
                                        )
                                elif remain_length < self.transfer_limit:
                                    if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                                        bits_dnum = '{:04x}'.format(
                                            remain_length)
                                    else:
                                        bits_dnum = '{:04x}'.format(
                                            remain_length)
                                device_count = (
                                    struct.pack('B', int(bits_dnum[0] + bits_dnum[1], 16)) +
                                    struct.pack(
                                        'B', int(bits_dnum[2] + bits_dnum[3], 16))
                                )
                        # Data length.
                        _data_len = '{:08x}'.format(26 + (len(w_data) * 2))
                        data_length = (
                            struct.pack('B', int(_data_len[0] + _data_len[1], 16)) +
                            struct.pack('B', int(_data_len[2] + _data_len[3], 16)) +
                            struct.pack('B', int(_data_len[4] + _data_len[5], 16)) +
                            struct.pack(
                                'B', int(_data_len[6] + _data_len[7], 16))
                        )
                        if self.transport_layer in global_vars.g_UDPIP:
                            telegram_data = (
                                icf +
                                rsv +
                                gct +
                                dna +
                                da1 +
                                da2 +
                                sna +
                                sa1 +
                                sa2 +
                                sid +
                                cmd +
                                device_code +
                                lead_device_number +
                                device_count +
                                cmd_data
                            )
                        else:
                            telegram_data = (
                                header +
                                data_length +
                                tcp_cmd +
                                err_cd +
                                icf +
                                rsv +
                                gct +
                                dna +
                                da1 +
                                da2 +
                                sna +
                                sa1 +
                                sa2 +
                                sid +
                                cmd +
                                device_code +
                                lead_device_number +
                                device_count +
                                cmd_data
                            )
                    else:
                        raise ValueError(
                            '{}, {}'.format(
                                sys._getframe().f_code.co_name, 'This cmd is not supported.'
                            )
                        )

            # ======= CIP =======
            elif self.protocol in global_vars.g_CIP:
                raise ValueError(
                    '{}, {}'.format(
                        sys._getframe().f_code.co_name, 'This cmd is not supported.'
                    )
                )

            # ======= HOST LINK (Jp:Joui LINK) =======
            elif self.protocol in global_vars.g_HOSTLINK:
                raise ValueError(
                    '{}, {}'.format(
                        sys._getframe().f_code.co_name, 'This cmd is not supported.'
                    )
                )

            # ======= EHTERNET IP ========
            elif self.protocol in global_vars.g_ETHERNETIP:
                raise ValueError(
                    '{}, {}'.format(
                        sys._getframe().f_code.co_name, 'This cmd is not supported.'
                    )
                )

            # ======= CONNECTION THROUGH RASPI-RC232C =======
            # ======= MODBUS RTU =======
            elif self.protocol in global_vars.g_MODBUSRTU:
                rp_header = (
                    struct.pack('B', 0x02) +
                    struct.pack('B', 0x02) +
                    struct.pack('B', 0x02)
                )
                slave_addr = struct.pack('B', 0x01)
                rp_footer = (
                    struct.pack('B', 0x03) +
                    struct.pack('B', 0x03) +
                    struct.pack('B', 0x03)
                )
                # Extract each hexadecimal digit and reconvert for transmission.
                lead_bit = (
                    self.lead_number +
                    current_count * self.transfer_limit
                )
                bits = '{:04x}'.format(lead_bit)
                hex_lead_bit = (
                    struct.pack('B', int(bits[0] + bits[1], 16)) +
                    struct.pack('B', int(bits[2] + bits[3], 16))
                )
                # device_code  = struct.pack('B', self.device_code)

                # For the Read command
                if self.cmd in global_vars.g_READ_COMMAND:
                    if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                        func_code = struct.pack('B', 0x01)
                    elif self.bit_identify in global_vars.g_IFY_WORD_DEVICE:
                        func_code = struct.pack('B', 0x03)
                    else:
                        raise ValueError(
                            '{}, {}'.format(
                                sys._getframe().f_code.co_name, 'This bit_identify is not supported.'
                            )
                        )

                    # Number of bits acquired
                    remain_length = (
                        self.send_length -
                        current_count * self.transfer_limit
                    )
                    if remain_length >= self.transfer_limit:
                        bits_vol = '{:04x}'.format(self.transfer_limit)
                    else:
                        bits_vol = '{:04x}'.format(remain_length)
                    data_count = (
                        struct.pack('B', int(bits_vol[0] + bits_vol[1], 16)) +
                        struct.pack('B', int(bits_vol[2] + bits_vol[3], 16))
                    )
                    row_data = (
                        slave_addr +
                        func_code +
                        hex_lead_bit +
                        data_count
                    )
                    telegram_data = (
                        rp_header +
                        row_data +
                        convert_format.make_crc(row_data) +
                        rp_footer
                    )
                # For the Write command
                elif self.cmd in global_vars.g_WRITE_COMMAND:
                    pass

            # ======= COMPUTER LINK =======
            elif self.protocol in global_vars.g_COMPUTERLINK:
                rp_header = (
                    struct.pack('B', 0x02) +
                    struct.pack('B', 0x02) +
                    struct.pack('B', 0x02)
                )
                slave_addr = b'\x0500FF'
                rp_footer = (
                    struct.pack('B', 0x03) +
                    struct.pack('B', 0x03) +
                    struct.pack('B', 0x03)
                )

                if self.cmd in global_vars.g_READ_COMMAND:
                    if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                        func_code = b'BR'
                    elif self.bit_identify in global_vars.g_IFY_WORD_DEVICE:
                        func_code = b'WR'
                    else:
                        raise ValueError(
                            '{}, {}'.format(
                                sys._getframe().f_code.co_name, 'This bit_identify is not supported.'
                            )
                        )

                timeout_addr = b'0'
                # Extract each hexadecimal digit and reconvert for transmission.
                device_code = struct.pack('B', self.device_code[0])
                lead_data = (
                    '{:04d}'.format(
                        self.lead_number +
                        current_count * self.transfer_limit
                    )
                ).encode()
                remain_length = (
                    self.send_length -
                    current_count * self.transfer_limit
                )
                if remain_length >= self.transfer_limit:
                    data_count = (
                        '{:02x}'.format(
                            self.transfer_limit
                        )
                    ).encode()
                else:
                    data_count = '{:02x}'.format(remain_length).encode()
                row_data = (
                    slave_addr +
                    func_code +
                    timeout_addr +
                    device_code +
                    lead_data +
                    data_count
                )
                telegram_data = (
                    rp_header +
                    row_data +
                    rp_footer
                )

            return telegram_data
        except Exception:
            logger.warning(traceback.format_exc())

    # Telegraphic data transmission.
    def sent_telegram(self) -> typing.Tuple[str, bytes, int]:
        loop_count = self.transfer_count
        res = ''
        try:
            # =============================
            # MODBUS-TCP (Modbus Protocol - TCP)
            # =============================
            if self.protocol in global_vars.g_MODBUSTCP:
                # Coil              Read-Write  1bit    (Discrete Output(DO)    1~9999)
                # Input Status      Read        1bit    (Discrete Input(DI)     10001~19999)
                # Input Register    Read        16bit   (Analog Input(AI)       30001~39999)
                # Holding Register  Read-Write  16bit   (Analog Output(AO)      40001~49999)
                con = ModbusClient()
                con.host(self.host)
                con.port(self.port)

                if self.cmd in global_vars.g_READ_COMMAND:
                    if self.device in ['COIL', 'DO', 'DISCRETE_OUTPUT']:
                        res = con.read_coils(self.lead_nuber, self.send_length)
                    elif self.device in ['INPUT_STATUS', 'DI', 'DISCRETE_INPUT']:
                        res = con.read_discrete_inputs(
                            self.lead_nuber, self.send_length)
                    elif self.device in ['INPUT_REGISTER', 'AI', 'ANALOG_INPUT']:
                        res = con.read_input_registers(
                            self.lead_nuber, self.send_length)
                    elif self.device in ['HOLDING_REGISTER', 'AO', 'ANALOG_OUTPUT']:
                        res = con.read_holding_register(
                            self.lead_nuber, self.send_length)
                    else:
                        raise ValueError(
                            '{},Ecode:{}'.format(
                                sys._getframe().f_code.co_name, 'Device name is wrong.'
                            )
                        )

                elif self.cmd in global_vars.g_WRITE_COMMAND:
                    if self.device in ['DO', 'COIL', 'DISCRETE_OUTPUT']:
                        con.write_multiple_coils(
                            self.lead_number, self.cmd_data)
                    elif self.device in ['HOLDING_REGISTER', 'AO', 'ANALOG_OUTPUT']:
                        con.write_multiple_registers(
                            self.lead_number, self.cmd_data)
                    else:
                        raise ValueError(
                            '{},Ecode:{}'.format(
                                sys._getframe().f_code.co_name, 'Device name is wrong.'
                            )
                        )
                else:
                    raise ValueError(
                        '{}, {}'.format(
                            sys._getframe().f_code.co_name, 'This command is not supported.'
                        )
                    )

            # =============================
            # Socket Connection
            # =============================
            else:
                # Connection initialize
                if self.transport_layer in global_vars.g_TCPIP:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                elif self.transport_layer in global_vars.g_UDPIP:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(global_vars.PLC_TIMEOUT_SECONDS)
                s.connect((self.host, self.port))

                # ===========================
                # Read Data Command
                # ===========================
                if self.cmd in global_vars.g_READ_COMMAND:
                    for i in range(loop_count):
                        # =============================
                        # MC Protocol(MELSEC Communication Protocol)
                        # =============================
                        if self.protocol in global_vars.g_MCPROTOCOL1E + global_vars.g_MCPROTOCOL3E:
                            # Generate telegram and sent.
                            senddata = self.generate_telegram(i)
                            s.send(bytes(senddata))
                            recv_data = s.recv(1024).hex()
                            s.close()

                            # =============================
                            # MC protocol/1E Frame
                            # =============================
                            # Check error code. '00' is success. other is error.
                            if self.protocol in global_vars.g_MCPROTOCOL1E:
                                ecode = recv_data[
                                    self.prefix_bit - 2: self.prefix_bit
                                ]
                                if int(ecode, 16) != 0:
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )

                            # =============================
                            # MC protocol/3E Frame, SLMP(Seamless Message Protocol)
                            # =============================
                            elif self.protocol in global_vars.g_MCPROTOCOL3E:
                                ecode = (
                                    recv_data[
                                        self.prefix_bit - 2: self.prefix_bit
                                    ] +
                                    recv_data[
                                        self.prefix_bit - 4: self.prefix_bit - 2
                                    ]
                                )
                                if int(ecode, 16) != 0:
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )
                            else:
                                raise ValueError(
                                    'Protcol is {}. Not support.'.format(
                                        self.protocol
                                    )
                                )

                            # Successfully completed.
                            ecode = 0
                            # Get bit status of all registers. Concatenate if register is transfer_limit or more
                            if i > 0:
                                e_bit = self.transfer_limit + self.prefix_bit
                                res += recv_data[self.prefix_bit: e_bit]
                            elif i == 0:
                                res = recv_data

                        # =============================
                        # FINS(Factory Interface Netwrok Service)
                        # =============================
                        elif self.protocol in global_vars.g_FINS:
                            if self.transport_layer in global_vars.g_UDPIP:
                                self.client_node = ''
                                self.server_node = ''
                            elif self.transport_layer in global_vars.g_TCPIP:
                                # Communication for obtaining node parameters.
                                send_nodeData = self.generate_node_telegram(
                                    self.protocol)
                                s.send(bytes(send_nodeData))
                                recv_nodeData = s.recv(1024).hex()
                                node_ecode1 = recv_nodeData[16:24]
                                node_ecode2 = recv_nodeData[24:32]
                                # Node error handling
                                if int(node_ecode1, 16) not in [1, 64, 128]:
                                    ecode = node_ecode1
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )
                                if int(node_ecode2, 16) not in [0, 64, 128]:
                                    ecode = node_ecode2
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )
                                self.client_node = int(
                                    '0x' +
                                    recv_nodeData[32:40], 16
                                )
                                self.server_node = int(
                                    '0x' + recv_nodeData[40:48], 16
                                )
                            else:
                                raise ValueError(
                                    '{},Ecode:{}'.format(
                                        sys._getframe().f_code.co_name, 'Transport layer name is wrong.'
                                    )
                                )

                            # Generate telegram and sent.
                            senddata = self.generate_telegram(i)
                            s.send(bytes(senddata))
                            recv_data = s.recv(1024).hex()
                            s.close()
                            # FINS connection Error check
                            # Check "Connection" error code. If command(only TCP) is not "2", error code is '00000000' is success. other is error.
                            # Check error code. '0000' is success. other is error.
                            if self.transport_layer in global_vars.g_UDPIP:
                                ecode = (
                                    recv_data[
                                        self.prefix_bit - 4: self.prefix_bit - 2
                                    ] +
                                    recv_data[
                                        self.prefix_bit - 2: self.prefix_bit
                                    ]
                                )
                                if int(ecode, 16) not in [0, 64, 128]:
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )
                            elif self.transport_layer in global_vars.g_TCPIP:
                                conn_ecode1 = recv_data[16:24]
                                conn_ecode2 = recv_data[24:32]
                                ecode = recv_data[
                                    self.prefix_bit - 4: self.prefix_bit
                                ]
                                if int(conn_ecode1, 16) not in [2, 64, 128] and int(conn_ecode2, 16) not in [0, 64, 128]:
                                    ecode = conn_ecode2 + ',' + ecode
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )
                                elif int(ecode, 16) not in [0, 64, 128]:
                                    ecode = (
                                        recv_data[
                                            self.prefix_bit - 4: self.prefix_bit - 2
                                        ] +
                                        recv_data[
                                            self.prefix_bit - 2: self.prefix_bit
                                        ]
                                    )
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )
                            else:
                                raise ValueError(
                                    '{},Ecode:{}'.format(
                                        sys._getframe().f_code.co_name, 'Transport layer name is wrong.'
                                    )
                                )
                            # Successfully completed.
                            ecode = 0
                            # Get bit status of all registers. Concatenate if register is transfer_limit or more
                            if i > 0:
                                e_bit = self.transfer_limit + self.prefix_bit
                                res += recv_data[self.prefix_bit:e_bit]
                            elif i == 0:
                                res = recv_data

                        # =============================
                        # MODBUS-RTU (Modbus Protocol - Remote Terminal Unit)
                        # =============================
                        elif self.protocol in global_vars.g_MODBUSRTU:
                            # Generate telegram and sent.
                            senddata = self.generate_telegram(i)
                            s.send(bytes(senddata))
                            recv_data_r = s.recv(1024)  # .hex()
                            s.close()
                            # Check CRC. success or error?
                            if len(recv_data_r) > 6:
                                row_data_r = recv_data_r[3:len(
                                    recv_data_r) - 5]
                                if convert_format.make_crc(row_data_r) != recv_data_r[len(recv_data_r) - 5:len(recv_data_r) - 3]:
                                    raise ValueError(
                                        '{}, {}'.format(
                                            recv_data_r, 'too short recieve data'
                                        )
                                    )
                            else:
                                raise ValueError(
                                    '{}, {}'.format(
                                        recv_data_r, 'too short recieve data'
                                    )
                                )
                            recv_data = row_data_r
                            # Get bit status of all registers. Concatenate if register is transfer_limit or more
                            if i > 0:
                                # このあたり不明
                                res += recv_data
                            elif i == 0:
                                # Successfully completed.
                                ecode = 0
                                res = recv_data

                        # =============================
                        # Computer Link (PC Link)
                        # =============================
                        elif self.protocol in global_vars.g_COMPUTERLINK:
                            # Generate telegram and sent.
                            senddata = self.generate_telegram(i)
                            s.send(bytes(senddata))
                            recv_data_r = s.recv(1024)  # .hex()
                            s.close()
                            # Check CRC. success or error?
                            if len(recv_data_r) > 6:
                                row_data_r = recv_data_r[3:len(
                                    recv_data_r) - 3]
                            else:
                                raise ValueError(
                                    '{}, {}'.format(
                                        recv_data_r, 'too short recieve data'
                                    )
                                )
                            recv_data = row_data_r
                            # Get bit status of all registers. Concatenate if register is transfer_limit or more
                            if i > 0:
                                # このあたり不明
                                res += recv_data
                            elif i == 0:
                                # Successfully completed.
                                ecode = 0
                                res = recv_data

                        else:
                            raise ValueError(
                                '{}, {}'.format(
                                    sys._getframe().f_code.co_name, 'This protocol is not supported.'
                                )
                            )

                # =============================
                # Write Data Command
                # =============================
                elif self.cmd in global_vars.g_WRITE_COMMAND:
                    for i in range(loop_count):
                        # =============================
                        # MC Protocol(MELSEC Communication Protocol)
                        # =============================
                        if self.protocol in global_vars.g_MCPROTOCOL1E + global_vars.g_MCPROTOCOL3E:
                            # Generate telegram and sent.
                            senddata = self.generate_telegram(i)
                            s.send(bytes(senddata))
                            recv_data = s.recv(1024).hex()
                            s.close()

                            # =============================
                            # MC protocol/1E Frame
                            # =============================
                            if self.protocol in global_vars.g_MCPROTOCOL1E:
                                ecode = recv_data[
                                    self.prefix_bit - 2: self.prefix_bit
                                ]
                                if int(ecode, 16) != 0:
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )

                            # =============================
                            # MC protocol/3E Frame, SLMP(Seamless Message Protocol)
                            # =============================
                            elif self.protocol in global_vars.g_MCPROTOCOL3E:
                                ecode = (
                                    recv_data[
                                        self.prefix_bit - 2: self.prefix_bit
                                    ] +
                                    recv_data[
                                        self.prefix_bit - 4: self.prefix_bit - 2
                                    ]
                                )
                                if int(ecode, 16) != 0:
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )
                            # Successful handling.
                            # Write command has no received.
                            ecode = 0
                            res = recv_data

                        # =============================
                        # FINS(Factory Interface Netwrok Service)
                        # =============================
                        elif self.protocol in global_vars.g_FINS:
                            if self.transport_layer in global_vars.g_UDPIP:
                                self.client_node = self.server_node = ''
                            elif self.transport_layer in global_vars.g_TCPIP:
                                # Communication for obtaining node parameters.
                                send_nodeData = self.generate_node_telegram(
                                    self.protocol)
                                s.send(bytes(send_nodeData))
                                recv_nodeData = s.recv(1024).hex()
                                node_ecode1 = recv_nodeData[16:24]
                                node_ecode2 = recv_nodeData[24:32]
                                # Node Error handling.
                                if int(node_ecode1, 16) not in [1, 64, 128]:
                                    ecode = node_ecode1
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_nodeData, send_nodeData, ecode
                                        )
                                    )
                                if int(node_ecode2, 16) not in [0, 64, 128]:
                                    ecode = node_ecode2
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_nodeData, send_nodeData, ecode
                                        )
                                    )
                                self.client_node = int(
                                    '0x' +
                                    recv_nodeData[32:40], 16
                                )
                                self.server_node = int(
                                    '0x' +
                                    recv_nodeData[40:48], 16
                                )
                            else:
                                raise ValueError(
                                    '{},Ecode:{}'.format(
                                        sys._getframe().f_code.co_name, 'Transport layer name is wrong.'
                                    )
                                )

                            # Generate telegram and sent.
                            senddata = self.generate_telegram(i)
                            s.send(bytes(senddata))
                            recv_data = s.recv(1024).hex()
                            s.close()

                            # FINS connection Error check
                            # Check "Connection" error code. If command(only TCP) is not "2", error code is '00000000' is success. other is error.
                            # Check error code. '0000' is success. other is error.
                            if self.transport_layer in global_vars.g_UDPIP:
                                ecode = (
                                    recv_data[
                                        self.prefix_bit - 4: self.prefix_bit - 2
                                    ] +
                                    recv_data[
                                        self.prefix_bit - 2: self.prefix_bit
                                    ]
                                )
                                if int(ecode, 16) not in [0, 64, 128]:
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )
                            elif self.transport_layer in global_vars.g_TCPIP:
                                conn_ecode1 = recv_data[16:24]
                                conn_ecode2 = recv_data[24:32]
                                ecode = recv_data[
                                    self.prefix_bit - 4: self.prefix_bit
                                ]

                                if int(conn_ecode1, 16) not in [2, 64, 128] and int(conn_ecode2, 16) not in [0, 64, 128]:
                                    ecode = conn_ecode2 + ',' + ecode
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )
                                elif int(ecode, 16) not in [0, 64, 128]:
                                    ecode = (
                                        recv_data[
                                            self.prefix_bit - 4: self.prefix_bit - 2
                                        ] +
                                        recv_data[
                                            self.prefix_bit - 2: self.prefix_bit
                                        ]
                                    )
                                    raise ValueError(
                                        '{}, Recv:{}, Send:{}, Ecode:{}'.format(
                                            sys._getframe().f_code.co_name, recv_data, senddata, ecode
                                        )
                                    )
                            else:
                                raise ValueError(
                                    '{},Ecode:{}'.format(
                                        sys._getframe().f_code.co_name, 'Transport layer name is wrong.'
                                    )
                                )
                            res = recv_data
                            ecode = 0

                        # =============================
                        # MODBUS-RTU (Modbus Protocol - Remote Terminal Unit)
                        # =============================
                        elif self.protocol in global_vars.g_MODBUSRTU:
                            pass

                        else:
                            raise ValueError(
                                '{}, {}'.format(
                                    sys._getframe().f_code.co_name, 'This protocol is not supported.'
                                )
                            )

                else:
                    raise ValueError(
                        '{}, {}'.format(
                            sys._getframe().f_code.co_name, 'This command is not supported.'
                        )
                    )
        # Error Response Handling.
        except Exception as err:
            try:
                if res == '':
                    res = recv_data
                else:
                    res
            except NameError:
                res = str(err)
            try:
                senddata.hex()
            except NameError:
                senddata = ''
            try:
                recv_data
            except NameError:
                recv_data = ''
            try:
                ecode
            except NameError:
                ecode = -1
            try:
                s.close()
            except Exception:
                logger.warning('Socket can not closed.')
        finally:
            try:
                senddata = senddata.hex()
            except Exception:
                pass
            finally:
                return res, senddata, ecode

    # Parse the data in bit/word units.
    # When it's bit, if you are reading an odd number of bits, a 0 is padded after the last bit.
    # When it's word, it'll consolidate four digits and convert hexadecimal numbers to decimal numbers.

    def extracting_elements(self, data: str, *, use_bcd: bool = False, optional: dict = {}) -> list:
        # logger.info('string_null:{}'.format(string_option_null_break))
        res = []
        message = ""
        try:
            data_len = int(len(data))
            # Perse bit unit
            if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                if self.manufacture in global_vars.g_OMRON:
                    for j in range(int((data_len - self.prefix_bit) / 2)):
                        st = self.prefix_bit + j * 2
                        ed = st + 2
                        temp_w_recv = data[st:ed]
                        if self.protocol in global_vars.g_FINS:
                            w_recv = temp_w_recv
                        res.append(w_recv)
                # ikeike
                elif self.protocol in global_vars.g_MODBUSRTU:
                    # 長すぎる場合は未対応data[self.prefix_bit - 1]
                    len_of_data = self.send_length
                    for j in range(data_len - self.prefix_bit):
                        val = int(data[j + self.prefix_bit])
                        for k in range(16):
                            if k >= len_of_data:
                                break
                            res.append(str(int(val % 2)))
                            val /= 2
                        len_of_data -= 16
                # ikeike
                # ikeikeike
                elif self.protocol in global_vars.g_COMPUTERLINK:
                    # 長すぎる場合は未対応data[self.prefix_bit - 1]
                    for j in range(0, data_len - self.prefix_bit - 1):
                        res.append(chr(data[j + self.prefix_bit]))
                # ikeikeike
                else:
                    for j in range(data_len - self.prefix_bit):
                        st = self.prefix_bit + j
                        ed = st + 1
                        b_recv = data[st:ed]
                        res.append(b_recv)
            # Perse word unit
            elif self.bit_identify in global_vars.g_IFY_WORD_DEVICE:
                if self.protocol in global_vars.g_MODBUSRTU:
                    for j in range(0, data_len - self.prefix_bit, 2):
                        try:
                            res.append(
                                format(int(data[j + self.prefix_bit]), '02x') +
                                format(
                                    int(data[j + 1 + self.prefix_bit]), '02x')
                            )
                        except Exception:
                            res.append(
                                format(int(data[j + self.prefix_bit], 16), '02x') +
                                format(
                                    int(data[j + 1 + self.prefix_bit], 16), '02x')
                            )
                elif self.protocol in global_vars.g_COMPUTERLINK:
                    for j in range(0, data_len - self.prefix_bit - 1, 4):
                        res.append(
                            format(
                                int((
                                    chr(data[self.prefix_bit + j]) +
                                    chr(data[self.prefix_bit + j + 1]) +
                                    chr(data[self.prefix_bit + j + 2]) +
                                    chr(data[self.prefix_bit + j + 3])
                                ).lower(), 16), '04x'
                            )
                        )
                else:
                    for j in range(int((data_len - self.prefix_bit) / 4)):
                        st = self.prefix_bit + j * 4
                        ed = st + 4
                        temp_w_recv = data[st:ed]
                        if self.protocol in global_vars.g_FINS:
                            w_recv = temp_w_recv
                        elif self.protocol in global_vars.g_MODBUSRTU:
                            if j < 2 and int(temp_w_recv[2:]) == 0:
                                w_recv = temp_w_recv[:2]
                            elif j < 2 and int(temp_w_recv[:2]) == 0:
                                w_recv = temp_w_recv[2:]
                            else:
                                w_recv = temp_w_recv[2:] + temp_w_recv[:2]
                        else:
                            w_recv = temp_w_recv[2:] + temp_w_recv[:2]
                        res.append(w_recv)

                if (self.option in global_vars.g_STRING_OPTION and self.cmd in global_vars.g_READ_COMMAND):
                    if self.manufacture in global_vars.g_PANASONIC:
                        _res = convert_format.check_hex_and_convert_integer(
                            res[2:], self.byte_order, dhex=True)
                        try:
                            try:
                                word_cnt = int(res[1], 16)
                            except Exception:
                                word_cnt = int(res[1])
                        except Exception:
                            word_cnt = 0
                        res = _res[:word_cnt]
                    # elif self.manufacture in global_vars.g_KEYENCE:
                    #     _res = convert_format.check_hex_and_convert_integer(
                    #         res, self.byte_order, dhex=True)
                    #     try:
                    #         try:
                    #             word_cnt = int(res[1], 16)
                    #         except Exception:
                    #             word_cnt = int(res[1])
                    #     except Exception:
                    #         word_cnt = 0
                    #     res = _res[:word_cnt]
                    else:
                        _res = convert_format.check_hex_and_convert_integer(
                            res, self.byte_order, dhex=True)
                        try:
                            string_option_null_break = optional['string_option_null_break']
                        except Exception:
                            string_option_null_break = True
                        if string_option_null_break:
                            for i, x in enumerate(_res):
                                if x == 0:
                                    res = _res[:i]
                                    break
                        else:
                            res = _res
                        # logger.info("Res:{}, null_break:{}".format(
                        #    res, string_option_null_break))
            else:
                raise ValueError(
                    '{}, {}'.format(
                        sys._getframe().f_code.co_name, 'This bit_identify is not supported.'
                    )
                )
            try:
                if use_bcd:
                    response = res
                else:
                    try:
                        response = [int(x, 16) for x in res]
                    except Exception:
                        response = res
                if self.bit_identify in global_vars.g_IFY_BIT_DEVICE:
                    if self.bit_odd_flag:
                        try:
                            if len(response) % 2 == 0:
                                response.pop()
                        except Exception:
                            pass
            except Exception:
                raise ValueError(
                    '{}, {}'.format(
                        sys._getframe().f_code.co_name, 'System error:Response format is incorrect.'
                    )
                )
        except Exception:
            logger.warning(traceback.format_exc())
            message = str(traceback.format_exc())
            response = None
        finally:
            # logger.info('Response:{}, {}'.format(response, message))
            return response, message


def adjust_max_characters_of_case_of_string(plc_network: dict, plc_protocol: dict, device_parameter: dict, cmd_data: dict):
    # In the case of string reading, the maximum number of characters is read from the PLC first.
    #  Adjust the maximum number of characters for string reading.
    try:
        if (cmd_data["option"] in global_vars.g_STRING_OPTION and
            cmd_data["cmd"] in global_vars.g_READ_COMMAND and
                plc_protocol["manufacture"] in global_vars.g_PANASONIC):
            _device_info = device_list.device_list(
                plc_protocol["manufacture"], plc_protocol["protocol"], plc_protocol[
                    "series"], transport_layer=plc_protocol["transport_layer"], period_index=plc_protocol["period_index"]
            )
            if _device_info["device"][device_parameter["device"]][2] == "w":
                _device_parameter = device_parameter
                _device_parameter["max"] = _device_parameter["min"]
                _cmd_data = cmd_data
                _cmd_data["option"] = ""
                _connect = ConnectToPlc(
                    plc_network,
                    plc_protocol,
                    _device_parameter,
                    _cmd_data
                )
                _res, _send, _err = _connect.sent_telegram()

                if re.fullmatch("[0-9a-f]+", _res, re.I):
                    # Parse the data in bit/word units.
                    _res_element, _message_element = _connect.extracting_elements(
                        _res)
                    logger.debug('Adjust Res Element:{}'.format(_res_element))
                else:
                    raise ValueError(
                        '{}, {}'.format(
                            sys._getframe().f_code.co_name, 'Error.'
                        )
                    )
                _cnv_leaddev = device_list.convert_to_decimal(
                    _device_info["device"][_device_parameter["device"]][0], _device_parameter)
                _cnv_minmax = device_list.convert_to_n_array(
                    _device_info["device"][_device_parameter["device"]][0], _cnv_leaddev["lead_number"], _res_element[0] + 2)
                device_parameter["min"] = _cnv_minmax["min_bit"]
                device_parameter["max"] = _cnv_minmax["max_bit"]
                cmd_data["option"] = global_vars.g_STRING_OPTION[0]
    except Exception:
        pass
    finally:
        return plc_network, plc_protocol, device_parameter, cmd_data


# Use asyncio to connect to multiple PLCs in parallel.
async def parallel_communication_to_plc(plc_network: dict, plc_protocol: dict, device_parameter: dict, cmd_data: dict, *, optional: dict = {}) -> dict:
    res = ''
    send = ''
    res_element = ''
    try:
        # If can read max string length, fixed max device.
        plc_network, plc_protocol, device_parameter, cmd_data = adjust_max_characters_of_case_of_string(
            plc_network, plc_protocol, device_parameter, cmd_data)

        # Connection to PLC
        connect = ConnectToPlc(
            plc_network,
            plc_protocol,
            device_parameter,
            cmd_data
        )
        # Generate telegram and transmission telegram to PLC.
        res, send, err = connect.sent_telegram()

        # Is data format BCD?
        use_bcd: bool = False
        try:
            if cmd_data["option"] in ["time", "warning"]:
                if plc_protocol["manufacture"] in (global_vars.g_MITSUBISHI + global_vars.g_PANASONIC + global_vars.g_OMRON):
                    use_bcd = True
                elif plc_protocol["manufacture"] in global_vars.g_KEYENCE:
                    use_bcd = False
        except Exception:
            use_bcd = False

        if re.fullmatch("[0-9a-f]+", res, re.I):
            # Parse the data in bit/word units.
            res_element, message_element = connect.extracting_elements(
                res, use_bcd=use_bcd, optional=optional)
            logger.debug("Extract:{}".format(res_element))
            # convert date format.
            if cmd_data["option"] in global_vars.g_TIME_OPTION:
                res_element = convert_format.convert_date_format(
                    plc_protocol, cmd_data, res_element)
        else:
            raise ValueError(
                '{}, {}'.format(
                    sys._getframe().f_code.co_name, 'Error.'
                )
            )

    except Exception as e:
        if not res or res == ['']:
            res = [e]
            err = e
        if not send:
            send = ''
        if not res_element or res_element == 0:
            res_element = 0
    finally:
        return {
            'response': res,
            'exists_data': res_element,
            'send_binary': send,
            'error_code': err,
            'message': err,
        }


async def parallel_connect(plc_network: dict, plc_protocol: dict, device_parameter: dict, cmd_data: dict, *, optional: dict = {}):
    # Communicate in parallel
    if not optional:
        for k in plc_network:
            optional[k] = {}
    all_groups = await asyncio.gather(
        *[
            parallel_communication_to_plc(
                plc_network[i],
                plc_protocol[i],
                device_parameter[i],
                cmd_data[i],
                optional=optional[i]
            ) for i in device_parameter.keys()
        ]
    )
    return {[j for j in device_parameter.keys()][i]: x for i, x in enumerate(all_groups)}


def single_communication_to_plc(plc_network: dict, plc_protocol: dict, device_parameter: dict, cmd_data: dict) -> dict:
    res = send = res_element = ''
    try:
        # If can read max string length, fixed max device.
        plc_network, plc_protocol, device_parameter, cmd_data = adjust_max_characters_of_case_of_string(
            plc_network, plc_protocol, device_parameter, cmd_data)

        # Connection to PLC
        connect = ConnectToPlc(
            plc_network,
            plc_protocol,
            device_parameter,
            cmd_data
        )
        # Generate telegram and transmission telegram to PLC.
        res, send, err = connect.sent_telegram()

        # Is data format BCD?
        use_bcd: bool = False
        try:
            if cmd_data["option"] in ["time", "warning"]:
                if plc_protocol["manufacture"] in (global_vars.g_MITSUBISHI + global_vars.g_PANASONIC + global_vars.g_OMRON):
                    use_bcd = True
                elif plc_protocol["manufacture"] in global_vars.g_KEYENCE:
                    use_bcd = False
        except Exception:
            use_bcd = False

        if re.fullmatch("[0-9a-f]+", res, re.I):
            # Parse the data in bit/word units.
            res_element, message_element = connect.extracting_elements(
                res, use_bcd=use_bcd)

            # convert date format.
            res_element = convert_format.convert_date_format(
                plc_protocol, cmd_data, res_element)
        else:
            raise ValueError(
                '{}, {}'.format(
                    sys._getframe().f_code.co_name, 'Error.'
                )
            )
    except Exception as e:
        if not res or res == ['']:
            res = [e]
            err = e
        if not send:
            send = ''
        if not res_element or res_element == 0:
            res_element = 0
        # print(traceback.format_exc())
    finally:
        return {
            'response': res,
            'exists_data': res_element,
            'send_binary': send,
            'error_code': err,
            'message': err,
        }


def single_connect(plc_network: dict, plc_protocol: dict, device_parameter: dict, cmd_data: dict):
    key = [i for i in device_parameter.keys()][0]
    # Communicate in parallel
    all_groups = single_communication_to_plc(
        plc_network[key],
        plc_protocol[key],
        device_parameter[key],
        cmd_data[key]
    )
    return {key: all_groups}


def communication_to_plc(plc_network: dict, plc_protocol: dict, device_parameter: dict, cmd_data: dict) -> typing.Tuple[str, list, str, int]:
    res = send = res_element = ''
    try:
        # If can read max string length, fixed max device.
        plc_network, plc_protocol, device_parameter, cmd_data = adjust_max_characters_of_case_of_string(
            plc_network, plc_protocol, device_parameter, cmd_data)

        # Connection to PLC
        connect = ConnectToPlc(
            plc_network,
            plc_protocol,
            device_parameter,
            cmd_data
        )
        # Generate telegram and transmission telegram to PLC.
        res, send, err = connect.sent_telegram()

        # Is data format BCD?
        use_bcd: bool = False
        try:
            if cmd_data["option"] in ["time", "warning"]:
                if plc_protocol["manufacture"] in (global_vars.g_MITSUBISHI + global_vars.g_PANASONIC + global_vars.g_OMRON):
                    use_bcd = True
                elif plc_protocol["manufacture"] in global_vars.g_KEYENCE:
                    use_bcd = False
        except Exception:
            use_bcd = False

        if re.fullmatch("[0-9a-f]+", res, re.I):
            # Parse the data in bit/word units.
            res_element, message_element = connect.extracting_elements(
                res, use_bcd=use_bcd)

            # convert date format.
            res_element = convert_format.convert_date_format(
                plc_protocol, cmd_data, res_element)
        else:
            raise ValueError(
                '{}, {}'.format(
                    sys._getframe().f_code.co_name, 'Error.'
                )
            )

    except Exception as e:
        if not res or res == ['']:
            res = [e]
            err = e
        if not send:
            send = ''
        if not res_element or res_element == 0:
            res_element = 0
        # print(traceback.format_exc())
    return res, res_element, send, err


def _main(plc_network: list, plc_protocol: list, device_parameter: list, cmd_data: list):
    # Communicate only.
    all_groups = communication_to_plc(
        plc_network[0], plc_protocol[0], device_parameter[0], cmd_data[0])
    return all_groups


if __name__ == '__main__':
    _plc_network = {
        "pqm_address": {'ip': '10.224.136.114', 'port': '5000'},
        # "pqm_model": {'ip': '10.224.136.114', 'port': '5000'},
        # "pqm_runmode": {'ip': '10.224.136.114', 'port': '5000'},
        # "pqm_time": {'ip': '10.224.136.114', 'port': '5000'},
    }
    _plc_protocol = {
        "pqm_address": {'manufacture': 'keyence', 'series': 'kv7500', 'protocol': 'slmp', 'transport_layer': 'tcp', 'period_index': None},
        # "pqm_model": {'manufacture': 'keyence', 'series': 'kv7500', 'protocol': 'slmp', 'transport_layer': 'tcp', 'period_index': None},
        # "pqm_runmode": {'manufacture': 'keyence', 'series': 'kv7500', 'protocol': 'slmp', 'transport_layer': 'tcp', 'period_index': None},
        # "pqm_time": {'manufacture': 'keyence', 'series': 'kv7500', 'protocol': 'slmp', 'transport_layer': 'tcp', 'period_index': None},
    }
    _device_parameter = {
        "pqm_address": {"device": "D", "min": "200", "max": "230"},
        # "pqm_model": {"device": "D", "min": "400", "max": "520"},
        # "pqm_runmode": {"device": "D", "min": "700", "max": "720"},
        # "pqm_time": {"device": "D", "min": "200", "max": "201"},
    }
    _cmd_data = {
        "pqm_address": {"cmd": "read", "data": [], "option": ""},
        # "pqm_model": {"cmd": "read", "data": [], "option": "string"},
        # "pqm_runmode": {"cmd": "read", "data": [], "option": "string"},
        # "pqm_time": {"cmd": "read", "data": [], "option": "time"},
    }
    _optional = {
        # "pqm_address": {},
        # "pqm_model": {"string_option_null_break": False},
        # "pqm_runmode": {"string_option_null_break": False},
        # "pqm_time": {},
    }
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(parallel_connect(
        _plc_network, _plc_protocol, _device_parameter, _cmd_data, optional=_optional))
    logger.info(
        'result(recv, recv_parameter(n_array), send):{}'.format(result))
