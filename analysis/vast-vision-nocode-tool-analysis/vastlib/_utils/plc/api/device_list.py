import traceback
import sys
try:
    import global_vars
    import logger
except Exception:
    from . import global_vars
    from . import logger

logger = logger.get_module_logger(__name__)


def devicelist(
        manufacture: str, protocol: str, series: str, *,
        transport_layer: str = 'tcp', period_index: int = None) -> (dict, int, int, str):
    # A list of plc devices. (OLD VERSION)
    # '<device name of PLC>':['decimal system', 'device code', 'data unit', (offset)]
    try:
        # ==== Mitsubishi Electric ====
        if manufacture in global_vars.g_MITSUBISHI:
            byte_order = 'little_endian'
            if protocol in global_vars.g_MCPROTOCOL1E:
                transfer_limit = 255
                prefix_bit = 4
                dict_devices = {
                    'D': ['10', (0x44, 0x20), 'w'], 'R': ['10', (0x52, 0x20), 'w'], 'TN': ['10', (0x54, 0x4E), 'w'], 'TS': ['10', (0x54, 0x53), 'b'],
                    'CN': ['10', (0x43, 0x4E), 'w'], 'CS': ['10', (0x43, 0x53), 'b'], 'X': ['16', (0x58, 0x20), 'b'], 'Y': ['16', (0x59, 0x20), 'b'],
                    'M': ['10', (0x4D, 0x20), 'b'], 'S': ['10', (0x53, 0x20), 'b']
                }
            elif protocol in global_vars.g_MCPROTOCOL3E:
                if series in global_vars.g_SERIES_IQR:
                    transfer_limit = 960
                    prefix_bit = 22
                    dict_devices = {
                        'SM': ['10', 0x0091, 'b'], 'SD': ['10', 0x00A9, 'w'], 'X': ['16', 0x009C, 'b'], 'Y': ['16', 0x009D, 'b'],
                        'M': ['10', 0x0090, 'b'], 'L': ['10', 0x0092, 'b'], 'F': ['10', 0x0093, 'b'], 'V': ['10', 0x0094, 'b'],
                        'B': ['16', 0x00A0, 'b'], 'D': ['10', 0x00A8, 'w'], 'W': ['16', 0x00B4, 'w'], 'TS': ['10', 0x00C1, 'b'],
                        'TC': ['10', 0x00C0, 'b'], 'TN': ['10', 0x00C0, 'w'], 'STS': ['10', 0x00C7, 'b'], 'STC': ['10', 0x00C6, 'b'],
                        'STN': ['10', 0x00C8, 'w'], 'CS': ['10', 0x00C4, 'b'], 'CC': ['10', 0x00C3, 'b'], 'CN': ['10', 0x00C5, 'w'],
                        'SB': ['16', 0x00A1, 'b'], 'SW': ['16', 0x00B5, 'w'], 'DX': ['16', 0x00A2, 'b'], 'DY': ['16', 0x00A3, 'b'],
                        'Z': ['10', 0x00CC, 'w'], 'R': ['10', 0x00AF, 'w'], 'ZR': ['16', 0x00B0, 'w'], 'LTS': ['10', 0x0051, 'b'],
                        'LTC': ['10', 0x0050, 'b'], 'LTN': ['10', 0x0052, 'dw'], 'LSTS': ['10', 0x0059, 'b'], 'LSTC': ['10', 0x0058, 'b'],
                        'LSTN': ['10', 0x005A, 'dw'], 'LCS': ['10', 0x0055, 'b'], 'LCC': ['10', 0x0054, 'b'], 'LCN': ['10', 0x0056, 'dw'],
                        'LZ': ['10', 0x00CC, 'dw'], 'RD': ['10', 0x002C, 'w']
                    }
                else:
                    transfer_limit = 960
                    prefix_bit = 22
                    dict_devices = {
                        'SM': ['10', 0x91, 'b'], 'SD': ['10', 0xA9, 'w'], 'X': ['16', 0x9C, 'b'], 'Y': [16, 0x9D, 'b'],
                        'M': ['10', 0x90, 'b'], 'L': ['10', 0x92, 'b'], 'F': ['10', 0x93, 'b'], 'V': [10, 0x94, 'b'],
                        'B': ['16', 0xA0, 'b'], 'D': ['10', 0xA8, 'w'], 'W': ['16', 0xB4, 'w'], 'TS': [10, 0xC1, 'b'],
                        'TC': ['10', 0xC0, 'b'], 'TN': ['10', 0xC0, 'w'], 'STS': ['10', 0xC7, 'b'], 'STC': [10, 0xC6, 'b'],
                        'STN': ['10', 0xC8, 'w'], 'CS': ['10', 0xC4, 'b'], 'CC': ['10', 0xC3, 'b'], 'CN': [10, 0xC5, 'w'],
                        'SB': ['16', 0xA1, 'b'], 'SW': ['16', 0xB5, 'w'], 'DX': ['16', 0xA2, 'b'], 'DY': [16, 0xA3, 'b'],
                        'Z': ['10', 0xCC, 'w'], 'R': ['10', 0xAF, 'w'], 'ZR': ['16', 0xB0, 'w']
                    }
            elif protocol in global_vars.g_MCPROTOCOL4E:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol will be added in the future.'
                    )
                )
            # ikeikeike
            elif protocol in global_vars.g_COMPUTERLINK:
                transfer_limit = 99
                prefix_bit = 5
                dict_devices = {
                    'X': ['ascii', b'X', 'b'], 'Y': ['ascii', b'Y', 'b'],
                    'M': ['ascii', b'M', 'b'], 'L': ['ascii', b'L', 'b'], 'F': ['ascii', b'F', 'b'], 'V': ['ascii', 'V', 'b'],
                    'B': ['ascii', b'B', 'b'], 'D': ['ascii', b'D', 'w'], 'W': ['ascii', b'W', 'w'],
                    'Z': ['ascii', b'Z', 'w'], 'R': ['ascii', b'R', 'w']
                }
            # ikeikeike
            else:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol name is wrong OR is Not supported.'
                    )
                )
        # Keyence
        elif manufacture in global_vars.g_KEYENCE:
            byte_order = 'little_endian'
            if protocol in global_vars.g_MCPROTOCOL3E:
                transfer_limit = 960
                prefix_bit = 22
                dict_devices = {
                    'R': ['1010', 0x9c, 'b'], 'B': ['16', 0xA0, 'b'], 'MR': ['1010', 0x90, 'b'], 'LR': ['1010', 0x92, 'b'],
                    'CR': ['1010', 0x91, 'b'], 'CM': ['10', 0xA9, 'w'], 'DM': ['10', 0xA8, 'w'], 'EM': ['10', 0xA8, 'w'],
                    'FM': ['10', 0xAF, 'w'], 'ZF': ['16', 0xB0, 'w'], 'W': ['16', 0xB4, 'w'], 'TS': ['10', 0xC1, 'b'],
                    'TC': ['10', 0xC2, 'b'], 'CC': ['10', 0xC5, 'b'], 'CS': ['10', 0xC4, 'b'], 'D': ['10', 0xA8, 'w'],
                    'M': ['1010', 0x90, 'b'], 'T': ['10', 0xC1, 'b'], 'C': ['10', 0xC5, 'b'],
                }

            elif protocol in global_vars.g_HOSTLINK:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol is not supported.'
                    )
                )
            else:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol name is wrong OR is Not supported.'
                    )
                )
        # Panasonic
        elif manufacture in global_vars.g_PANASONIC:
            byte_order = 'big_endian'
            if protocol in global_vars.g_MCPROTOCOL3E:
                transfer_limit = 960
                prefix_bit = 22
                dict_devices = {
                    'X': ['1016', 0x9C, 'b'], 'Y': ['1016', 0x9D, 'b'], 'L': ['1016', 0xA0, 'b'], 'R': ['1016', 0x90, 'b'],
                    'R1': ['1016', 0x92, 'b'], 'DT': ['10', 0xA8, 'w'], 'LD': ['10', 0xB4, 'w'], 'EVT': ['10', 0xC2, 'w'],
                    'T': ['10', 0xC1, 'b'], 'EVC': ['10', 0xC5, 'w'], 'C': ['10', 0xC4, 'b'], 'SR': ['1016', 0x91, 'b', 9000],
                    'SD': ['10', 0xA9, 'w', 90000], 'SDT': ['10', 0xA9, 'w', 90000], 'D': ['10', 0xA8, 'w'],
                }
            elif protocol in global_vars.g_MEWTOCOL:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol is not supported.'
                    )
                )
            else:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol name is wrong OR is Not supported.'
                    )
                )
        # Omron
        elif manufacture in global_vars.g_OMRON:
            byte_order = 'big_endian'
            if protocol in global_vars.g_FINS:
                transfer_limit = 498
                if transport_layer in global_vars.g_UDPIP:
                    prefix_bit = 28
                elif transport_layer in global_vars.g_TCPIP:
                    prefix_bit = 76
                else:
                    prefix_bit = 76
                dict_devices = {
                    'CIO': ['10.10', 0x30, 'b'], 'W': ['10.10', 0x31, 'b'], 'H': ['10.10', 0x32, 'b'], 'A': ['10.10', 0x33, 'b'],
                    'DM': ['10.10', 0x02, 'b'], 'TK': ['10.10', 0x46, 'b'], 'IR': ['10', 0xDC, 'w'], 'DR': ['10', 0xBC, 'w'],
                    'EM0': ['10.10', 0xA0, 'b'], 'EM1': ['10.10', 0xA1, 'b'], 'EM2': ['10.10', 0xA2, 'b'], 'EM3': ['10.10', 0xA3, 'b'], 'EM4': ['10.10', 0xA4, 'b'],
                    'EM5': ['10.10', 0xA5, 'b'], 'EM6': ['10.10', 0xA6, 'b'], 'EM7': ['10.10', 0xA7, 'b'], 'EM8': ['10.10', 0xA8, 'b'], 'EM9': ['10.10', 0xA9, 'b'],
                    'EMA': ['10.10', 0xAA, 'b'], 'EMB': ['10.10', 0xAB, 'b'], 'EMC': ['10.10', 0xAC, 'b'], 'EMD': ['10.10', 0xAD, 'b'], 'EME': ['10.10', 0xAE, 'b'],
                    'EMF': ['10.10', 0xAF, 'b'], 'EM10': ['10.10', 0x60, 'b'], 'EM11': ['10.10', 0x61, 'b'], 'EM12': ['10.10', 0x62, 'b'], 'EM13': [10.10, 0x63, 'b'],
                    'EM14': ['10.10', 0x64, 'b'], 'EM15': ['10.10', 0x65, 'b'], 'EM16': ['10.10', 0x66, 'b'], 'EM17': ['10.10', 0x67, 'b'], 'EM18': ['10.10', 0x68, 'b'],
                    'EMCB': ['10', 0x98, 'w'],
                    'TIMS': ['10', 0x09, 'w'], 'CNTS': ['10', 0x09, 'w', 8000], 'TIMN': ['10', 0x89, 'w'], 'CNTN': ['10', 0x89, 'w', 8000],
                    'D': ['10.10', 0x82, 'b'],
                }
                if period_index is None:
                    dict_update_devices = {
                        'CIO': ['10', 0xB0, 'w'], 'W': ['10', 0xB1, 'w'], 'H': ['10', 0xB2, 'w'], 'A': ['10', 0xB3, 'w'],
                        'DM': ['10', 0x82, 'w'], 'TK': ['10', 0x46, 'w'],
                        'EM0': ['10', 0xA0, 'w'], 'EM1': ['10', 0xA1, 'w'], 'EM2': ['10', 0xA2, 'w'], 'EM3': ['10', 0xA3, 'w'], 'EM4': ['10', 0xA4, 'w'],
                        'EM5': ['10', 0xA5, 'w'], 'EM6': ['10', 0xA6, 'w'], 'EM7': ['10', 0xA7, 'w'], 'EM8': ['10', 0xA8, 'w'], 'EM9': ['10', 0xA9, 'w'],
                        'EMA': ['10', 0xAA, 'w'], 'EMB': ['10', 0xAB, 'w'], 'EMC': ['10', 0xAC, 'w'], 'EMD': ['10', 0xAD, 'w'], 'EME': ['10', 0xAE, 'w'],
                        'EMF': ['10', 0xAF, 'w'], 'EM10': ['10', 0x60, 'w'], 'EM11': ['10', 0x61, 'w'], 'EM12': ['10', 0x62, 'w'], 'EM13': ['10', 0x63, 'w'],
                        'EM14': ['10', 0x64, 'w'], 'EM15': ['10', 0x65, 'w'], 'EM16': ['10', 0x66, 'w'], 'EM17': ['10', 0x67, 'w'], 'EM18': ['10', 0x68, 'w'],
                    }
                    dict_devices.update(dict_update_devices)
            elif protocol in global_vars.g_CIP:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol is not supported.'
                    )
                )
            else:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol name is wrong OR is Not supported.'
                    )
                )
        # Rockwell
        elif manufacture in global_vars.g_ROCKWELL:
            if protocol in global_vars.g_MODBUSTCP:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol will be added in the future.'
                    )
                )
            else:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol name is wrong OR is Not supported.'
                    )
                )
        # Siemens
        elif manufacture in global_vars.g_SIEMENS:
            if protocol in global_vars.g_MODBUSTCP:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol will be added in the future.'
                    )
                )
            else:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol name is wrong OR is Not supported.'
                    )
                )
        # Schneider electric
        elif manufacture in global_vars.g_SCHNEIDERELECTRIC:
            if protocol in global_vars.g_MODBUSTCP:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol will be added in the future.'
                    )
                )
            else:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol name is wrong OR is Not supported.'
                    )
                )
        # ikeike-------------------------------------
        # Xinje
        elif manufacture in global_vars.g_XINJE:
            byte_order = 'little_endian'
            if protocol in global_vars.g_MODBUSRTU:
                transfer_limit = 24
                prefix_bit = 5
                # prefix_bit = 3
                dict_devices = {
                    'M': ['10', 0x01, 'b'], 'X': ['10', 0x01, 'b', 4000], 'Y': ['10', 0x01, 'b', 4800],
                    'D': ['10', 0x04, 'w'],
                }
            elif protocol in global_vars.g_MEWTOCOL:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol is not supported.'
                    )
                )
            else:
                raise ValueError(
                    '{},{}'.format(
                        sys._getframe().f_code.co_name, 'This protocol name is wrong OR is Not supported.'
                    )
                )
        # ikeike-------------------------------------
        # Other manufacure
        else:
            raise ValueError(
                '{},{}'.format(
                    sys._getframe().f_code.co_name, 'This manufacture name is wrong OR is Not supported.'
                )
            )

        key = ['decimal', 'binary', 'character']
        devices = {}
        for k, v in dict_devices.items():
            devices[k] = dict(zip(key, v))

        return {
            'device': devices,
            'transfer_limit': transfer_limit,
            'prefix_bit': prefix_bit,
            'byte_order': byte_order,
            'traceback': '',
        }
    except Exception:
        return {
            'device': {},
            'transfer_limit': 0,
            'prefix_bit': 0,
            'byte_order': '',
            'traceback': traceback.format_exc(),
        }


def convert_to_decimal(n_array: str, device_parameter: dict) -> dict:
    # Converts the number of digits set by each company to the number of
    # digits of the communication protocol.
    try:
        period_index = device_parameter['min'].index('.')
    except ValueError:
        period_index = None
    # Decimal number.  Ex) '1000' -> 1000(10)
    if n_array == '10':
        min_bit = int(device_parameter['min'],)
        try:
            max_bit = int(device_parameter['max'])
        except Exception:
            max_bit = min_bit
    # Hexadecimal number.  Ex) '1000' -> 4096(10)
    elif n_array == '16':
        min_bit = int(device_parameter['min'], 16)
        try:
            max_bit = int(device_parameter['max'], 16)
        except Exception:
            max_bit = min_bit
    # Upper digits are in decimal. The last 2 digit is a decimal number of n_array notation.
    #  Ex) '511.15' -> 51115(10)
    elif n_array == '10.10':
        min_integer = str(device_parameter['min'])[:period_index]
        if period_index is not None:
            min_n_array = str(device_parameter['min'])[period_index + 1:]
            min_bit = int(min_integer) * 16 + int(min_n_array)
            try:
                period_index_max = device_parameter['max'].index('.')
                max_bit = (
                    int(str(device_parameter['max'])[:period_index_max]) * 16
                    + int(str(device_parameter['max'])[period_index_max + 1:])
                )
            except Exception:
                max_bit = min_bit
        else:
            min_bit = int(min_integer)
            try:
                max_bit = int(str(device_parameter['max']))
            except Exception:
                max_bit = min_bit
    # Upper digits are in decimal. The last 2 digit is a Hexadecimal number of decimal notation.
    #  Ex) 199915 -> 1999*16+15 = 31999(10)
    elif n_array == '1010':
        if len(str(device_parameter['min'])) <= 2:
            min_bit = int(str(device_parameter['min']))
        else:
            min_bit = (
                int(str(device_parameter['min'])[:-2]) * 16
                + int(str(device_parameter['min'])[-2:])
            )
        try:
            if len(str(device_parameter['max'])) <= 2:
                max_bit = int(str(device_parameter['max']))
            else:
                max_bit = (
                    int(str(device_parameter['max'])[:-2]) * 16
                    + int(str(device_parameter['max'])[-2:])
                )
        except Exception:
            max_bit = min_bit
    # Upper digits are in decimal. The last 1 digit is a Hexadecimal number of Hexadecimal notation.
    # Ex) 109F -> 109*16+F = 1759(10)
    elif n_array == '1016':
        if len(str(device_parameter['min'])) <= 1:
            min_bit = int(str(device_parameter['min']), 16)
        else:
            min_bit = (
                int(str(device_parameter['min'])[:-1]) * 16
                + int(str(device_parameter['min'])[-1:], 16)
            )
        try:
            if len(str(device_parameter['max'])) <= 1:
                max_bit = int(str(device_parameter['max']), 16)
            else:
                max_bit = (
                    int(str(device_parameter['max'])[:-1]) * 16
                    + int(str(device_parameter['max'])[-1:], 16)
                )
        except Exception:
            max_bit = min_bit
    elif n_array == 'ascii':
        min_bit = int(device_parameter['min'])
        max_bit = int(device_parameter['max'])

    # Confirmation of large and small.
    if min_bit > max_bit:
        (temp_min, temp_max) = (min_bit, max_bit)
        (min_bit, max_bit) = (temp_max, temp_min)
    lead_number = min_bit
    # Number of communication data and times.
    send_length = max_bit - min_bit + 1
    return {
        'lead_number': lead_number,
        'send_length': send_length,
    }


def convert_to_n_array(
        n_array: str, lead_number: int,
        send_length: int) -> (str, str):
    # Converts the number of digits set by each company to the number of digits of the communication protocol.
    # Decimal number.  Ex) 1000(10) -> '1000'
    if n_array == '10':
        min_bit = lead_number
        min_bit = str(min_bit)
        max_bit = str(lead_number + send_length)
    # Hexadecimal number.  Ex) 4096(10) -> '1000'
    elif n_array == '16':
        min_bit = lead_number
        min_bit = format(min_bit, 'x')
        max_bit = format(lead_number + send_length - 1, 'x')
    # Upper digits are in decimal. The last 2 digit is a decimal number of decimal notation.
    #  Ex) 51115(10) '511.15'
    elif n_array == '10.10':
        min_integer, min_n_array = divmod(lead_number, 16)
        max_integer, max_n_array = divmod(lead_number + send_length, 16)
        min_bit = str(min_integer) + "." + "{02}".format(min_n_array)
        max_bit = str(max_integer) + "." + "{02}".format(max_n_array)
    # Upper digits are in decimal. The last 2 digit is a Hexadecimal number of decimal notation.
    #  Ex) 31999(10) = 1999*16+15 -> 199915
    elif n_array == '1010':
        min_integer, min_n_array = divmod(lead_number, 16)
        max_integer, max_n_array = divmod(lead_number + send_length, 16)
        min_bit = str(min_integer) + '{02}'.format(min_n_array)
        max_bit = str(max_integer) + '{02}'.format(max_n_array)
    # Upper digits are in decimal. The last 1 digit is a Hexadecimal number of Hexadecimal notation.
    # Ex) 1759(10) = 109*16+F -> 109F
    elif n_array == '1016':
        min_integer, min_n_array = divmod(lead_number, 16)
        max_integer, max_n_array = divmod(lead_number + send_length, 16)
        min_bit = str(min_integer) + format(min_n_array, '01x')
        max_bit = str(max_integer) + format(max_n_array, '01x')
    elif n_array == 'ascii':
        min_bit = lead_number
        max_bit = min_bit
    return {
        'min_bit': min_bit,
        'max_bit': max_bit,
    }


def device_list(manufacture: str, protocol: str, series: str, *,
                transport_layer: str = 'tcp', period_index: int = None) -> (dict, int, int, str):
    # A list of plc devices.(LATEST VERSION)
    # '<device name of PLC>':['decimal system', 'device code', 'data unit', (offset)]
    try:
        # Mitsubishi electric
        if manufacture in global_vars.g_MITSUBISHI:
            byte_order = 'little_endian'
            if protocol in global_vars.g_MCPROTOCOL1E:
                dict_devices = {
                    'D': ['10', (0x44, 0x20), 'w'], 'R': ['10', (0x52, 0x20), 'w'], 'TN': ['10', (0x54, 0x4E), 'w'], 'TS': ['10', (0x54, 0x53), 'b'],
                    'CN': ['10', (0x43, 0x4E), 'w'], 'CS': ['10', (0x43, 0x53), 'b'], 'X': ['16', (0x58, 0x20), 'b'], 'Y': ['16', (0x59, 0x20), 'b'],
                    'M': ['10', (0x4D, 0x20), 'b'], 'S': ['10', (0x53, 0x20), 'b']
                }
                transfer_limit = 255
                prefix_bit = 4
            elif protocol in global_vars.g_MCPROTOCOL3E:
                if series in global_vars.g_SERIES_IQR:
                    dict_devices = {
                        'SM': ['10', 0x0091, 'b'], 'SD': ['10', 0x00A9, 'w'], 'X': ['16', 0x009C, 'b'], 'Y': ['16', 0x009D, 'b'],
                        'M': ['10', 0x0090, 'b'], 'L': ['10', 0x0092, 'b'], 'F': ['10', 0x0093, 'b'], 'V': ['10', 0x0094, 'b'],
                        'B': ['16', 0x00A0, 'b'], 'D': ['10', 0x00A8, 'w'], 'W': ['16', 0x00B4, 'w'], 'TS': ['10', 0x00C1, 'b'],
                        'TC': ['10', 0x00C0, 'b'], 'TN': ['10', 0x00C0, 'w'], 'STS': ['10', 0x00C7, 'b'], 'STC': ['10', 0x00C6, 'b'],
                        'STN': ['10', 0x00C8, 'w'], 'CS': ['10', 0x00C4, 'b'], 'CC': ['10', 0x00C3, 'b'], 'CN': ['10', 0x00C5, 'w'],
                        'SB': ['16', 0x00A1, 'b'], 'SW': ['16', 0x00B5, 'w'], 'DX': ['16', 0x00A2, 'b'], 'DY': ['16', 0x00A3, 'b'],
                        'Z': ['10', 0x00CC, 'w'], 'R': ['10', 0x00AF, 'w'], 'ZR': ['16', 0x00B0, 'w'], 'LTS': ['10', 0x0051, 'b'],
                        'LTC': ['10', 0x0050, 'b'], 'LTN': ['10', 0x0052, 'dw'], 'LSTS': ['10', 0x0059, 'b'], 'LSTC': ['10', 0x0058, 'b'],
                        'LSTN': ['10', 0x005A, 'dw'], 'LCS': ['10', 0x0055, 'b'], 'LCC': ['10', 0x0054, 'b'], 'LCN': ['10', 0x0056, 'dw'],
                        'LZ': ['10', 0x00CC, 'dw'], 'RD': ['10', 0x002C, 'w']
                    }
                    transfer_limit = 960
                    prefix_bit = 22
                else:
                    dict_devices = {
                        'SM': ['10', 0x91, 'b'], 'SD': ['10', 0xA9, 'w'], 'X': ['16', 0x9C, 'b'], 'Y': [16, 0x9D, 'b'],
                        'M': ['10', 0x90, 'b'], 'L': ['10', 0x92, 'b'], 'F': ['10', 0x93, 'b'], 'V': [10, 0x94, 'b'],
                        'B': ['16', 0xA0, 'b'], 'D': ['10', 0xA8, 'w'], 'W': ['16', 0xB4, 'w'], 'TS': [10, 0xC1, 'b'],
                        'TC': ['10', 0xC0, 'b'], 'TN': ['10', 0xC0, 'w'], 'STS': ['10', 0xC7, 'b'], 'STC': [10, 0xC6, 'b'],
                        'STN': ['10', 0xC8, 'w'], 'CS': ['10', 0xC4, 'b'], 'CC': ['10', 0xC3, 'b'], 'CN': [10, 0xC5, 'w'],
                        'SB': ['16', 0xA1, 'b'], 'SW': ['16', 0xB5, 'w'], 'DX': ['16', 0xA2, 'b'], 'DY': [16, 0xA3, 'b'],
                        'Z': ['10', 0xCC, 'w'], 'R': ['10', 0xAF, 'w'], 'ZR': ['16', 0xB0, 'w']
                    }
                    transfer_limit = 960
                    prefix_bit = 22
            elif protocol in global_vars.g_MCPROTOCOL4E:
                raise ValueError('{},{}'.format(
                    sys._getframe().f_code.co_name, 'This protocol will be added in the future.'))
            elif protocol in global_vars.g_COMPUTERLINK:
                transfer_limit = 99
                prefix_bit = 5
                dict_devices = {
                    'X': ['ascii', b'X', 'b'], 'Y': ['ascii', b'Y', 'b'],
                    'M': ['ascii', b'M', 'b'], 'L': ['ascii', b'L', 'b'], 'F': ['ascii', b'F', 'b'], 'V': ['ascii', 'V', 'b'],
                    'B': ['ascii', b'B', 'b'], 'D': ['ascii', b'D', 'w'], 'W': ['ascii', b'W', 'w'],
                    'Z': ['ascii', b'Z', 'w'], 'R': ['ascii', b'R', 'w']
                }
            else:
                raise ValueError('{},{}'.format(sys._getframe(
                ).f_code.co_name, 'This protocol name is wrong OR is Not supported.'))
        # Keyence
        elif manufacture in global_vars.g_KEYENCE:
            byte_order = 'little_endian'
            if protocol in global_vars.g_MCPROTOCOL3E:
                dict_devices = {
                    'R': ['1010', 0x9c, 'b'], 'B': ['16', 0xA0, 'b'], 'MR': ['1010', 0x90, 'b'], 'LR': ['1010', 0x92, 'b'],
                    'CR': ['1010', 0x91, 'b'], 'CM': ['10', 0xA9, 'w'], 'DM': ['10', 0xA8, 'w'], 'EM': ['10', 0xA8, 'w'],
                    'FM': ['10', 0xAF, 'w'], 'ZF': ['16', 0xB0, 'w'], 'W': ['16', 0xB4, 'w'], 'TS': ['10', 0xC1, 'b'],
                    'TC': ['10', 0xC2, 'b'], 'CC': ['10', 0xC5, 'b'], 'CS': ['10', 0xC4, 'b'], 'D': ['10', 0xA8, 'w'],
                    'M': ['1010', 0x90, 'b'], 'T': ['10', 0xC1, 'b'], 'C': ['10', 0xC5, 'b'],
                }

                transfer_limit = 960
                prefix_bit = 22
            elif protocol in global_vars.g_HOSTLINK:
                raise ValueError('{},{}'.format(
                    sys._getframe().f_code.co_name, 'This protocol is not supported.'))
            else:
                raise ValueError('{},{}'.format(sys._getframe(
                ).f_code.co_name, 'This protocol name is wrong OR is Not supported.'))
        # Panasonic
        elif manufacture in global_vars.g_PANASONIC:
            byte_order = 'big_endian'
            if protocol in global_vars.g_MCPROTOCOL3E:
                dict_devices = {
                    'X': ['1016', 0x9C, 'b'], 'Y': ['1016', 0x9D, 'b'], 'L': ['1016', 0xA0, 'b'], 'R': ['1016', 0x90, 'b'],
                    'R1': ['1016', 0x92, 'b'], 'DT': ['10', 0xA8, 'w'], 'LD': ['10', 0xB4, 'w'], 'EVT': ['10', 0xC2, 'w'],
                    'T': ['10', 0xC1, 'b'], 'EVC': ['10', 0xC5, 'w'], 'C': ['10', 0xC4, 'b'], 'SR': ['1016', 0x91, 'b', 9000],
                    'SD': ['10', 0xA9, 'w', 90000], 'SDT': ['10', 0xA9, 'w', 90000], 'D': ['10', 0xA8, 'w'],
                }
                transfer_limit = 960
                prefix_bit = 22
            elif protocol in global_vars.g_MEWTOCOL:
                raise ValueError('{},{}'.format(
                    sys._getframe().f_code.co_name, 'This protocol is not supported.'))
            else:
                raise ValueError('{},{}'.format(sys._getframe(
                ).f_code.co_name, 'This protocol name is wrong OR is Not supported.'))
        # Omron
        elif manufacture in global_vars.g_OMRON:
            byte_order = 'big_endian'
            if protocol in global_vars.g_FINS:
                dict_devices = {
                    'CIO': ['10.10', 0x30, 'b'], 'W': ['10.10', 0x31, 'b'], 'H': ['10.10', 0x32, 'b'], 'A': ['10.10', 0x33, 'b'],
                    'DM': ['10.10', 0x02, 'b'], 'TK': ['10.10', 0x46, 'b'], 'IR': ['10', 0xDC, 'w'], 'DR': ['10', 0xBC, 'w'],
                    'EM0': ['10.10', 0xA0, 'b'], 'EM1': ['10.10', 0xA1, 'b'], 'EM2': ['10.10', 0xA2, 'b'], 'EM3': ['10.10', 0xA3, 'b'], 'EM4': ['10.10', 0xA4, 'b'],
                    'EM5': ['10.10', 0xA5, 'b'], 'EM6': ['10.10', 0xA6, 'b'], 'EM7': ['10.10', 0xA7, 'b'], 'EM8': ['10.10', 0xA8, 'b'], 'EM9': ['10.10', 0xA9, 'b'],
                    'EMA': ['10.10', 0xAA, 'b'], 'EMB': ['10.10', 0xAB, 'b'], 'EMC': ['10.10', 0xAC, 'b'], 'EMD': ['10.10', 0xAD, 'b'], 'EME': ['10.10', 0xAE, 'b'],
                    'EMF': ['10.10', 0xAF, 'b'], 'EM10': ['10.10', 0x60, 'b'], 'EM11': ['10.10', 0x61, 'b'], 'EM12': ['10.10', 0x62, 'b'], 'EM13': [10.10, 0x63, 'b'],
                    'EM14': ['10.10', 0x64, 'b'], 'EM15': ['10.10', 0x65, 'b'], 'EM16': ['10.10', 0x66, 'b'], 'EM17': ['10.10', 0x67, 'b'], 'EM18': ['10.10', 0x68, 'b'],
                    'EMCB': ['10', 0x98, 'w'],
                    'TIMS': ['10', 0x09, 'w'], 'CNTS': ['10', 0x09, 'w', 8000], 'TIMN': ['10', 0x89, 'w'], 'CNTN': ['10', 0x89, 'w', 8000]
                }
                if period_index is None:
                    dict_update_devices = {
                        'CIO': ['10', 0xB0, 'w'], 'W': ['10', 0xB1, 'w'], 'H': ['10', 0xB2, 'w'], 'A': ['10', 0xB3, 'w'],
                        'DM': ['10', 0x82, 'w'], 'TK': ['10', 0x46, 'w'],
                        'EM0': ['10', 0xA0, 'w'], 'EM1': ['10', 0xA1, 'w'], 'EM2': ['10', 0xA2, 'w'], 'EM3': ['10', 0xA3, 'w'], 'EM4': ['10', 0xA4, 'w'],
                        'EM5': ['10', 0xA5, 'w'], 'EM6': ['10', 0xA6, 'w'], 'EM7': ['10', 0xA7, 'w'], 'EM8': ['10', 0xA8, 'w'], 'EM9': ['10', 0xA9, 'w'],
                        'EMA': ['10', 0xAA, 'w'], 'EMB': ['10', 0xAB, 'w'], 'EMC': ['10', 0xAC, 'w'], 'EMD': ['10', 0xAD, 'w'], 'EME': ['10', 0xAE, 'w'],
                        'EMF': ['10', 0xAF, 'w'], 'EM10': ['10', 0x60, 'w'], 'EM11': ['10', 0x61, 'w'], 'EM12': ['10', 0x62, 'w'], 'EM13': ['10', 0x63, 'w'],
                        'EM14': ['10', 0x64, 'w'], 'EM15': ['10', 0x65, 'w'], 'EM16': ['10', 0x66, 'w'], 'EM17': ['10', 0x67, 'w'], 'EM18': ['10', 0x68, 'w'],
                    }
                    dict_devices.update(dict_update_devices)
                transfer_limit = 498
                if transport_layer in global_vars.g_UDPIP:
                    prefix_bit = 28
                elif transport_layer in global_vars.g_TCPIP:
                    prefix_bit = 76
                else:
                    prefix_bit = 76
            elif protocol in global_vars.g_CIP:
                raise ValueError('{},{}'.format(
                    sys._getframe().f_code.co_name, 'This protocol is not supported.'))
            else:
                raise ValueError('{},{}'.format(sys._getframe(
                ).f_code.co_name, 'This protocol name is wrong OR is Not supported.'))
        # Rockwell
        elif manufacture in global_vars.g_ROCKWELL:
            if protocol in global_vars.g_MODBUS:
                raise ValueError('{},{}'.format(
                    sys._getframe().f_code.co_name, 'This protocol will be added in the future.'))
            else:
                raise ValueError('{},{}'.format(sys._getframe(
                ).f_code.co_name, 'This protocol name is wrong OR is Not supported.'))
        # Siemens
        elif manufacture in global_vars.g_SIEMENS:
            if protocol in global_vars.g_MODBUS:
                raise ValueError('{},{}'.format(
                    sys._getframe().f_code.co_name, 'This protocol will be added in the future.'))
            else:
                raise ValueError('{},{}'.format(sys._getframe(
                ).f_code.co_name, 'This protocol name is wrong OR is Not supported.'))
        # Schneider electric
        elif manufacture in global_vars.g_SCHNEIDERELECTRIC:
            if protocol in global_vars.g_MODBUS:
                raise ValueError('{},{}'.format(
                    sys._getframe().f_code.co_name, 'This protocol will be added in the future.'))
            else:
                raise ValueError('{},{}'.format(sys._getframe(
                ).f_code.co_name, 'This protocol name is wrong OR is Not supported.'))
        # Xinje
        elif manufacture in global_vars.g_XINJE:
            byte_order = 'little_endian'
            if protocol in global_vars.g_MODBUSRTU:
                transfer_limit = 960
                prefix_bit = 3
                dict_devices = {
                    'M': ['10', 0x01, 'b'], 'X': ['10', 0x01, 'b', 4000], 'Y': ['10', 0x01, 'b', 4800],
                    'D': ['10', 0x04, 'w'],
                }
            elif protocol in global_vars.g_MEWTOCOL:
                raise ValueError('{},{}'.format(
                    sys._getframe().f_code.co_name, 'This protocol is not supported.'))
            else:
                raise ValueError('{},{}'.format(sys._getframe(
                ).f_code.co_name, 'This protocol name is wrong OR is Not supported.'))
        # Other manufacure
        else:
            raise ValueError('{},{}'.format(sys._getframe(
            ).f_code.co_name, 'This manufacture name is wrong OR is Not supported.'))
        return {
            'device': dict_devices,
            'transfer_limit': transfer_limit,
            'prefix_bit': prefix_bit,
            'byte_order': byte_order,
            'traceback': '',
        }
    except Exception:
        return {
            'device': {},
            'transfer_limit': 0,
            'prefix_bit': 0,
            'byte_order': '',
            'traceback': traceback.format_exc(),
        }


if __name__ == '__main__':
    a = []
    for i in range(2):
        # a.append(device_list('panasonic', 'mc_3e', 'q', transport_layer='tcp'))
        # a.append(devicelist('panasonic', 'mc_3e', 'q', transport_layer='tcp'))
        a.append(list(device_list('mitsubishi', 'slmp', '')['device'].keys()))
    print(a)
