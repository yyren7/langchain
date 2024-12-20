import sys
import re
import itertools
import more_itertools
try:
    import logger
    import global_vars
except Exception:
    from . import logger
    from . import global_vars
logger = logger.get_module_logger(__name__)


def make_crc(orgcommand: bytes) -> bytes:
    # 最初のCRCレジスタ値をFFFFhに設定
    crc_registor = 0xFFFF
    for data_byte in orgcommand:
        # CRCレジスタとデータバイトのXOR
        tmp = crc_registor ^ data_byte
        # シフト回数を記憶
        shift_num = 0
        # シフトが 8回になるまで繰り返す
        while(shift_num < 8):
            if(tmp & 1 == 1):  # 桁あふれが1なら
                tmp = tmp >> 1
                shift_num += 1
                tmp = 0xA001 ^ tmp
            else:
                tmp = tmp >> 1
                shift_num += 1
        # 計算結果をcrc_registorにセット
        crc_registor = tmp
    # 計算結果をbytes型へ変換
    return crc_registor.to_bytes(2, 'little')


def convert_integer_to_double_hex(data: list, *, endian: str = 'big') -> list:
    # Ex)
    # big endian   : [10, 11, 12, 13] -> [2826, 3340]
    # little endian: [10, 11, 12, 13] -> [2571, 3085]
    convert_data = []
    if endian in ["big", "big_endian"]:
        for i in range(0, len(data), 2):
            try:
                convert_data.append(
                    int(format(data[i + 1], '02x') + format(data[i], '02x'), 16))
            except Exception:
                convert_data.append(
                    int(format(0, '02x') + format(data[i], '02x'), 16))
    else:
        for i in range(0, len(data), 2):
            try:
                convert_data.append(
                    int(format(data[i], '02x') + format(data[i + 1], '02x'), 16))
            except Exception:
                convert_data.append(
                    int(format(data[i], '02x') + format(0, '02x'), 16))

    logger.debug('{}, {}'.format(sys._getframe().f_code.co_name, convert_data))
    return convert_data


def convert_double_hex_to_integer(data: list, *, dhex: bool = False, endian: str = 'big') -> list:
    # Ex)
    # big endian   : [2571, 3085] -> [11, 10, 13, 12]
    # little endian: [2571, 3085] -> [10, 11, 12, 13]
    convert_data = []
    if endian in ["big", "big_endian"]:
        for i in range(len(data)):
            string_data = format(data[i], '0x').zfill(
                int(len(format(data[i], '0x')) + len(format(data[i], '0x')) % 2))
            try:
                convert_data.extend(
                    [int(string_data[-2:], 16), int(string_data[-4:-2], 16)])
            except Exception:
                if dhex:
                    convert_data.extend(
                        [int(string_data[-2:], 16), 0])
                else:
                    convert_data.extend([int(string_data[-2:], 16)])
    else:
        for i in range(len(data)):
            string_data = format(data[i], '0x').zfill(
                int(len(format(data[i], '0x')) + len(format(data[i], '0x')) % 2))
            try:
                convert_data.extend(
                    [int(string_data[-4:-2], 16), int(string_data[-2:], 16)])
            except Exception:
                if dhex:
                    convert_data.extend(
                        [0, int(string_data[-2:], 16)])
                else:
                    convert_data.extend([int(string_data[-2:], 16)])

    logger.debug('{}, {}'.format(sys._getframe().f_code.co_name, convert_data))
    return convert_data


def check_string_and_convert_dhex(data: list, byte_order: str, option: str) -> list:
    try:
        # check: data is "string" or "integer"
        string_data = list(itertools.chain.from_iterable(
            list(map(lambda x: list(x), data))))
    except Exception:
        new_data = data
        option = option
    else:
        # case string
        cmd_data = list(map(lambda x: ord(x), string_data))
        try:
            tmp_data = list(more_itertools.chunked(cmd_data, 2))
        except Exception:
            tmp_data = [cmd_data[i: i + 2] for i in range(0, len(cmd_data), 2)]
        finally:
            new_data = list(itertools.chain.from_iterable(list(
                map(lambda x: convert_integer_to_double_hex(x, endian=byte_order), tmp_data))))
            option = global_vars.g_STRING_OPTION[0]
    finally:
        return new_data, option


def check_hex_and_convert_integer(data: list, byte_order: str, *, dhex: bool = False, zero_padding: bool = True) -> list:
    try:
        tmp_data = [int(x, 16) for x in data]
        print(tmp_data)
    except Exception:
        new_data = data
    else:
        if dhex:
            new_data = convert_double_hex_to_integer(
                tmp_data, dhex=dhex, endian=byte_order)
        else:
            new_data = tmp_data
    finally:
        return new_data


def convert_integer_to_another_base_number_as_string(value: int, base: int) -> str:
    if (int(value / base)):
        return convert_integer_to_another_base_number_as_string(int(value / base), base) + str(value % base)
    return str(value % base)


def convert_number_as_string_to_another_base_and_hex_notation(value: str, base: int, *, paddings=0):
    # 数値(string)を指定した底に変換したあと、16進数で表示する
    try:
        conv_hex = '0{}x'.format(paddings)
        res_value = ''.join([format(int(i, base), conv_hex) for i in re.split(
            '{}{}{}'.format('(', '.' * base, ')'), value) if i != ''])
    except Exception:
        res_value = value
    return res_value


def convert_negative_integer_to_signed_hex(list_negative: list, *, word_count: int = 2) -> list:
    # Convert from negative value to signed hexadecimal.
    list_response = []
    for x in list_negative:
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


def convert_date_format(plc_protocol, cmd_data, res_element):
    if cmd_data["option"] in global_vars.g_TIME_OPTION:
        if plc_protocol["manufacture"] in global_vars.g_MITSUBISHI:
            if len(res_element) >= 4:
                exists_data = []
                for data in res_element:
                    try:
                        exists_data.append(int(data, 16))
                    except Exception:
                        exists_data.append(int(data))
                res_element = exists_data
        elif plc_protocol["manufacture"] in global_vars.g_PANASONIC:
            if len(res_element) >= 4:
                if plc_protocol["series"] in ["fp7", "7"]:
                    exists_data = []
                    for data in res_element:
                        exists_data.append(int(data))
                    res_element = exists_data
                else:
                    exists_data = [
                        int(res_element[2][:2]),  # year
                        int(res_element[2][2:]),  # month
                        int(res_element[1][:2]),  # day
                        int(res_element[1][2:]),  # hour
                        int(res_element[0][:2]),  # minute
                        int(res_element[0][2:]),  # second
                        int(res_element[3][2:])   # weekday
                    ]
                    res_element = exists_data
        elif plc_protocol["manufacture"] in global_vars.g_KEYENCE:
            exists_data = []
            for data in res_element:
                exists_data.append(int(data))
            res_element = exists_data
        elif plc_protocol["manufacture"] in global_vars.g_OMRON:
            exists_data = []
            for data in res_element:
                exists_data.append(int(data))
            res_element = exists_data
    return res_element
