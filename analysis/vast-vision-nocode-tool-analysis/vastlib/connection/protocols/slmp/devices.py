try:
    from .. import const
except Exception:
    import sys
    import pathlib
    parent_dir = str(pathlib.Path(__file__).parent.parent.resolve())
    sys.path.append(parent_dir)
    import const


class DeviceList():
    def __init__(self, *, manufacture="mitsubishi", series="default", has_point=False, transport="udp"):
        self.manufacture = manufacture
        self.series = series
        self.has_point = has_point
        self.transport = transport
        self.endian = ""
        self.transfer_limit = 0
        self.prefix_byte = 0
        self.word_length = 16

    def plc_mitsubishi(self):
        self.endian = "little"
        if self.series in const.SERIES_MITSUBISHI_IQR:
            self.transfer_limit = 960
            self.prefix_byte = 22
            devices = [
                # Relay devices
                {"symbol": "X", "binary": 0x009C, "ascii": "X***", "identify": "bit",
                    "decimal": "10", "name": "Input"},
                {"symbol": "Y", "binary": 0x009D, "ascii": "Y***", "identify": "bit",
                    "decimal": "10", "name": "Output"},
                {"symbol": "M", "binary": 0x0090, "ascii": "M***", "identify": "bit",
                    "decimal": "10", "name": "Internal relay"},
                {"symbol": "L", "binary": 0x0092, "ascii": "L***", "identify": "bit",
                    "decimal": "10", "name": "Latching relay"},
                {"symbol": "F", "binary": 0x0093, "ascii": "F***", "identify": "bit",
                    "decimal": "10", "name": "Annunciator"},
                {"symbol": "V", "binary": 0x0094, "ascii": "V***", "identify": "bit",
                    "decimal": "10", "name": "Edge relay"},
                {"symbol": "B", "binary": 0x00A0, "ascii": "B***", "identify": "bit",
                    "decimal": "16", "name": "Link relay"},
                # Register devices
                {"symbol": "D", "binary": 0x00A8, "ascii": "D***", "identify": "word",
                    "decimal": "10", "name": "Data register"},
                {"symbol": "W", "binary": 0x00B4, "ascii": "W***", "identify": "word",
                    "decimal": "16", "name": "Link register"},
                # Timer devices
                {"symbol": "TS", "binary": 0x00C1, "ascii": "TS**", "identify": "bit",
                    "decimal": "10", "name": "Contact timer"},
                {"symbol": "TC", "binary": 0x00C0, "ascii": "TC**", "identify": "bit",
                    "decimal": "10", "name": "Coil timer"},
                {"symbol": "TN", "binary": 0x00C2, "ascii": "TN**", "identify": "word",
                    "decimal": "10", "name": "Current timer"},
                {"symbol": "LTS", "binary": 0x0051, "ascii": "LTS*", "identify": "bit",
                    "decimal": "10", "name": "Long contact timer"},
                {"symbol": "LTC", "binary": 0x0050, "ascii": "LTC*", "identify": "bit",
                    "decimal": "10", "name": "Long coil timer"},
                {"symbol": "LTN", "binary": 0x0052, "ascii": "LTN*", "identify": "double",
                    "decimal": "10", "name": "Long current timer"},
                # Retentive timer devices
                {"symbol": "STS", "binary": 0x00C7, "ascii": "STS*", "identify": "bit",
                    "decimal": "10", "name": "Contact retentive timer"},
                {"symbol": "STC", "binary": 0x00C6, "ascii": "STC*", "identify": "bit",
                    "decimal": "10", "name": "Coil retentive timer"},
                {"symbol": "STN", "binary": 0x00C8, "ascii": "STN*", "identify": "word",
                    "decimal": "10", "name": "Current retentive timer"},
                {"symbol": "LSTS", "binary": 0x0059, "ascii": "LSTS", "identify": "bit",
                    "decimal": "10", "name": "Long contact retentive timer"},
                {"symbol": "LSTC", "binary": 0x0058, "ascii": "LSTC", "identify": "bit",
                    "decimal": "10", "name": "Long coil retentive timer"},
                {"symbol": "LSTN", "binary": 0x005A, "ascii": "LSTN", "identify": "double",
                    "decimal": "10", "name": "Long current retentive timer"},
                # Counter devices
                {"symbol": "CS", "binary": 0x00C4, "ascii": "CS**", "identify": "bit",
                    "decimal": "10", "name": "Contact counter"},
                {"symbol": "CC", "binary": 0x00C3, "ascii": "CC**", "identify": "bit",
                    "decimal": "10", "name": "Coil counter"},
                {"symbol": "CN", "binary": 0x00C5, "identify": "word",
                    "decimal": "10", "name": "Current counter"},
                {"symbol": "LCS", "binary": 0x00C4, "ascii": "LCS*", "identify": "bit",
                    "decimal": "10", "name": "Long contact counter"},
                {"symbol": "LCC", "binary": 0x00C3, "ascii": "LCC*", "identify": "bit",
                    "decimal": "10", "name": "Long coil counter"},
                {"symbol": "LCN", "binary": 0x00C5, "ascii": "LCN*", "identify": "double",
                    "decimal": "10", "name": "Long current counter"},
                # Special devices
                {"symbol": "SM", "binary": 0x0091, "ascii": "SM**", "identify": "bit",
                    "decimal": "10", "name": "Special relay"},
                {"symbol": "SD", "binary": 0x00A9, "ascii": "SD**", "identify": "word",
                    "decimal": "10", "name": "Special register"},
                {"symbol": "SB", "binary": 0x00A1, "ascii": "SB**", "identify": "bit",
                    "decimal": "16", "name": "Link special relay"},
                {"symbol": "SW", "binary": 0x00B5, "ascii": "SW**", "identify": "word",
                    "decimal": "16", "name": "Link special register"},
                # Direct access devices
                {"symbol": "DX", "binary": 0x00A2, "ascii": "DX**", "identify": "bit",
                    "decimal": "16", "name": "Direct access input"},
                {"symbol": "DY", "binary": 0x00A3, "ascii": "DY**", "identify": "bit",
                    "decimal": "16", "name": "Direct access output"},
                # Index register
                {"symbol": "LZ", "binary": 0x0062, "ascii": "LZ**", "identify": "double",
                    "decimal": "10", "name": "Long Index register"},
                # File register
                {"symbol": "R", "binary": 0x00AF, "ascii": "R***", "identify": "word",
                    "decimal": "10", "name": "Switching file register"},
                {"symbol": "ZR", "binary": 0x00B0, "ascii": "ZR**", "identify": "word",
                    "decimal": "16", "name": "Sequential file register"},
                # Refresh register
                {"symbol": "RD", "binary": 0x002C, "ascii": "RD**", "identify": "word",
                    "decimal": "10", "name": "Refresh data register"},
                # Unit access devices
                {"symbol": "U_G", "binary": 0x00AB, "ascii": "G***", "identify": "word",
                    "decimal": "10", "name": "Unit access device"},
                # CPU buffer memory access devices
                {"symbol": "U3E_G", "binary": 0x00AB, "ascii": "G*", "identify": "word",
                    "decimal": "10", "name": "CPU buffer memory access devices"},
                {"symbol": "U3E_HG", "binary": 0x002E, "ascii": "HG**", "identify": "word",
                    "decimal": "10", "name": "CPU buffer memory access devices"},
            ]
        # Default iQ
        else:
            # if self.series in const.SERIES_MITSUBISHI_QNA:
            #     self.transfer_limit = 480
            # elif self.series in const.SERIES_MITSUBISHI_A:
            #     self.transfer_limit = 64
            # else:
            self.transfer_limit = 960
            self.prefix_byte = 22
            devices = [
                # Relay devices
                {"symbol": "X", "binary": 0x9C, "ascii": "X*", "identify": "bit",
                    "decimal": "10", "name": "Input"},
                {"symbol": "Y", "binary": 0x9D, "ascii": "Y*", "identify": "bit",
                    "decimal": "10", "name": "Output"},
                {"symbol": "M", "binary": 0x90, "ascii": "M*", "identify": "bit",
                    "decimal": "10", "name": "Internal relay"},
                {"symbol": "L", "binary": 0x92, "ascii": "L*", "identify": "bit",
                    "decimal": "10", "name": "Latching relay"},
                {"symbol": "F", "binary": 0x93, "ascii": "F*", "identify": "bit",
                    "decimal": "10", "name": "Annunciator"},
                {"symbol": "V", "binary": 0x94, "ascii": "V*", "identify": "bit",
                    "decimal": "10", "name": "Edge relay"},
                {"symbol": "B", "binary": 0xA0, "ascii": "B*", "identify": "bit",
                    "decimal": "16", "name": "Link relay"},
                # Register devices
                {"symbol": "D", "binary": 0xA8, "ascii": "D*", "identify": "word",
                    "decimal": "10", "name": "Data register"},
                {"symbol": "W", "binary": 0xB4, "ascii": "W*", "identify": "word",
                    "decimal": "16", "name": "Link register"},
                # Timer devices
                {"symbol": "TS", "binary": 0xC1, "ascii": "TS", "identify": "bit",
                    "decimal": "10", "name": "Contact timer"},
                {"symbol": "TC", "binary": 0xC0, "ascii": "TC", "identify": "bit",
                    "decimal": "10", "name": "Coil timer"},
                {"symbol": "TN", "binary": 0xC2, "ascii": "TN", "identify": "word",
                    "decimal": "10", "name": "Current timer"},
                # Retentive timer devices
                {"symbol": "STS", "binary": 0xC7, "ascii": "SS", "identify": "bit",
                    "decimal": "10", "name": "Contact retentive timer"},
                {"symbol": "STC", "binary": 0xC6, "ascii": "SC", "identify": "bit",
                    "decimal": "10", "name": "Coil retentive timer"},
                {"symbol": "STN", "binary": 0xC8, "ascii": "SN", "identify": "word",
                    "decimal": "10", "name": "Current retentive timer"},
                # Counter devices
                {"symbol": "CS", "binary": 0xC4, "ascii": "CS", "identify": "bit",
                    "decimal": "10", "name": "Contact counter"},
                {"symbol": "CC", "binary": 0xC3, "ascii": "CC", "identify": "bit",
                    "decimal": "10", "name": "Coil counter"},
                {"symbol": "CN", "binary": 0xC5, "ascii": "CN", "identify": "word",
                    "decimal": "10", "name": "Current counter"},
                # Special devices
                {"symbol": "SM", "binary": 0x91, "ascii": "SM", "identify": "bit",
                    "decimal": "10", "name": "Special relay"},
                {"symbol": "SD", "binary": 0xA9, "ascii": "SD", "identify": "word",
                    "decimal": "10", "name": "Special register"},
                {"symbol": "SB", "binary": 0xA1, "ascii": "SB", "identify": "bit",
                    "decimal": "16", "name": "Link special relay"},
                {"symbol": "SW", "binary": 0xB5, "ascii": "SW", "identify": "word",
                    "decimal": "16", "name": "Link special register"},
                # Direct access devices
                {"symbol": "DX", "binary": 0xA2, "ascii": "DX", "identify": "bit",
                    "decimal": "16", "name": "Direct access input"},
                {"symbol": "DY", "binary": 0xA3, "ascii": "DY", "identify": "bit",
                    "decimal": "16", "name": "Direct access output"},
                # Index register
                {"symbol": "Z", "binary": 0xCC, "ascii": "Z*", "identify": "word",
                    "decimal": "10", "name": "Index register"},
                # File register
                {"symbol": "R", "binary": 0xAF, "ascii": "R*", "identify": "word",
                    "decimal": "10", "name": "Switching file register"},
                {"symbol": "ZR", "binary": 0xB0, "ascii": "ZR", "identify": "word",
                    "decimal": "16", "name": "Sequential file register"},
                # Expansion register
                {"symbol": "D_EX", "binary": 0xA8, "ascii": "D*", "identify": "word",
                    "decimal": "10", "name": "Expansion data register"},
                {"symbol": "W_EX", "binary": 0xB4, "ascii": "W*", "identify": "word",
                    "decimal": "16", "name": "Expansion link register"},
                # Unit access devices
                {"symbol": "U_G", "binary": 0xAB, "ascii": "G", "identify": "word",
                    "decimal": "10", "name": "Unit access device"},
            ]
        return devices

    def plc_keyence(self):
        self.endian = "little"
        if self.series in const.SERIES_KEYENCE_KVNANO:
            self.transfer_limit = 960
            self.prefix_byte = 22
            devices = [
                # Relay
                {"symbol": "R_X", "binary": 0x9C, "ascii": "X*", "identify": "bit",
                    "decimal": "1016", "name": "Input", "decimal_to_ascii": "16"},
                {"symbol": "R_Y", "binary": 0x9D, "ascii": "Y*", "identify": "bit",
                    "decimal": "1016", "name": "Output", "decimal_to_ascii": "16"},
                {"symbol": "R(X)", "binary": 0x9C, "ascii": "X*", "identify": "bit",
                    "decimal": "1016", "name": "Input", "decimal_to_ascii": "16"},
                {"symbol": "R(Y)", "binary": 0x9D, "ascii": "Y*", "identify": "bit",
                    "decimal": "1016", "name": "Output", "decimal_to_ascii": "16"},
                {"symbol": "B", "binary": 0xA0, "ascii": "B*", "identify": "bit",
                    "decimal": "16", "name": "Link relay", "decimal_to_ascii": "16"},
                {"symbol": "MR", "binary": 0x90, "ascii": "M*", "identify": "bit",
                    "decimal": "1016", "name": "Internal relay"},
                {"symbol": "M", "binary": 0x90, "ascii": "M*", "identify": "bit",
                    "decimal": "1016", "name": "Internal relay((MC Compatible))"},
                {"symbol": "LR", "binary": 0x92, "ascii": "L*", "identify": "bit",
                    "decimal": "1016", "name": "Latching relay"},
                # Control
                {"symbol": "CR", "binary": 0x91, "ascii": "SM", "identify": "bit",
                    "decimal": "1016", "name": "Control relay"},
                {"symbol": "CM", "binary": 0xA9, "ascii": "SD", "identify": "word",
                    "decimal": "10", "name": "Control register"},
                # Register
                {"symbol": "DM", "binary": 0xA8, "ascii": "D*", "identify": "word",
                    "decimal": "10", "name": "Data register"},
                {"symbol": "D", "binary": 0xA8, "ascii": "D*", "identify": "word",
                    "decimal": "10", "name": "Data register(MC Compatible)"},
                # Link register
                {"symbol": "W", "binary": 0xB4, "ascii": "W*", "identify": "word",
                    "decimal": "16", "name": "Link register", "decimal_to_ascii": "16"},
                # Timer
                {"symbol": "T_TN", "binary": 0xC2, "ascii": "TN", "identify": "word",
                    "decimal": "10", "name": "Current timer"},
                {"symbol": "T_TS", "binary": 0xC1, "ascii": "TS", "identify": "bit",
                    "decimal": "10", "name": "Contact timer"},
                # Counter
                {"symbol": "C_CN", "binary": 0xC5, "ascii": "CN", "identify": "word",
                    "decimal": "10", "name": "Current timer"},
                {"symbol": "C_CS", "binary": 0xC4, "ascii": "CS", "identify": "bit",
                    "decimal": "10", "name": "Contact counter"},
            ]
        # Default KV7XXX & KV5XXX
        else:
            self.transfer_limit = 960
            self.prefix_byte = 22
            devices = [
                # Relay
                {"symbol": "R_X", "binary": 0x9C, "ascii": "X*", "identify": "bit",
                    "decimal": "1016", "name": "Input", "decimal_to_ascii": "16"},
                {"symbol": "R_Y", "binary": 0x9D, "ascii": "Y*", "identify": "bit",
                    "decimal": "1016", "name": "Output", "decimal_to_ascii": "16"},
                {"symbol": "R(X)", "binary": 0x9C, "ascii": "X*", "identify": "bit",
                    "decimal": "1016", "name": "Input", "decimal_to_ascii": "16"},
                {"symbol": "R(Y)", "binary": 0x9D, "ascii": "Y*", "identify": "bit",
                    "decimal": "1016", "name": "Output", "decimal_to_ascii": "16"},
                {"symbol": "B", "binary": 0xA0, "ascii": "B*", "identify": "bit",
                    "decimal": "16", "name": "Link relay", "decimal_to_ascii": "16"},
                {"symbol": "MR", "binary": 0x90, "ascii": "M*", "identify": "bit",
                    "decimal": "1016", "name": "Internal relay"},
                {"symbol": "M", "binary": 0x90, "ascii": "M*", "identify": "bit",
                    "decimal": "1016", "name": "Internal relay(MC Compatible)"},
                {"symbol": "LR", "binary": 0x92, "ascii": "L*", "identify": "bit",
                    "decimal": "1016", "name": "Latching relay"},
                # Control
                {"symbol": "CR", "binary": 0x91, "ascii": "SM", "identify": "bit",
                    "decimal": "1016", "name": "Control relay"},
                {"symbol": "CM", "binary": 0xA9, "ascii": "SD", "identify": "word",
                    "decimal": "10", "name": "Control register"},
                # Register
                {"symbol": "DM", "binary": 0xA8, "ascii": "D*", "identify": "word",
                    "decimal": "10", "name": "Data register"},
                {"symbol": "D", "binary": 0xA8, "ascii": "D*", "identify": "word",
                    "decimal": "10", "name": "Data register(MC Compatible)"},
                {"symbol": "EM", "binary": 0xA8, "ascii": "D*", "identify": "word",
                    "decimal": "10", "offset": "100000", "name": "Expansion register"},
                # File register
                {"symbol": "FM", "binary": 0xAF, "ascii": "R*", "identify": "word",
                    "decimal": "10", "name": "Switching file register"},
                {"symbol": "ZF", "binary": 0xB0, "ascii": "ZR", "identify": "word",
                    "decimal": "10", "name": "Sequential file register", "decimal_to_ascii": "16"},
                # Link register
                {"symbol": "W", "binary": 0xB4, "ascii": "W*", "identify": "word",
                    "decimal": "16", "name": "Link register", "decimal_to_ascii": "16"},
                # Timer
                {"symbol": "T_TN", "binary": 0xC2, "ascii": "TN", "identify": "word",
                    "decimal": "10", "name": "Current timer"},
                {"symbol": "T_TS", "binary": 0xC1, "ascii": "TS", "identify": "bit",
                    "decimal": "10", "name": "Contact timer"},
                # Counter
                {"symbol": "C_CN", "binary": 0xC5, "ascii": "CN", "identify": "word",
                    "decimal": "10", "name": "Current timer"},
                {"symbol": "C_CS", "binary": 0xC4, "ascii": "CS", "identify": "bit",
                    "decimal": "10", "name": "Contact counter"},
            ]
        return devices

    def plc_panasonic(self):
        self.endian = "little"
        self.transfer_limit = 960
        self.prefix_byte = 22
        devices = [
            {"symbol": "X", "binary": 0x9C, "identify": "bit",
                "decimal": "10F", "name": "Input"},
            {"symbol": "Y", "binary": 0x9D, "identify": "bit",
                "decimal": "10F", "name": "Output"},
            {"symbol": "L", "binary": 0xA0, "identify": "bit",
                "decimal": "10F", "name": "Link relay"},
            {"symbol": "R", "binary": 0x90, "identify": "bit",
                "decimal": "10F", "name": "Internal relay"},
            {"symbol": "M", "binary": 0x90, "identify": "bit",
                "decimal": "10F", "name": "Internal relay(MC Compatible)"},
            {"symbol": "R_L", "binary": 0x92, "identify": "bit",
                "decimal": "10F", "name": "Latching relay"},
            {"symbol": "DT", "binary": 0xA8, "identify": "word",
                "decimal": "10", "name": "Data register"},
            {"symbol": "D", "binary": 0xA8, "identify": "word",
                "decimal": "10", "name": "Data register(MC Compatible)"},
            {"symbol": "LD", "binary": 0xB4, "identify": "word",
                "decimal": "10", "name": "Link register"},
            {"symbol": "TE", "binary": 0xC2, "identify": "word",
                "decimal": "10", "name": "Current timer"},
            {"symbol": "T", "binary": 0xC1, "identify": "word",
                "decimal": "10", "name": "Contact timer", "writeable": False},
            {"symbol": "CE", "binary": 0xC5, "identify": "word",
                "decimal": "10", "name": "Current counter"},
            {"symbol": "C", "binary": 0xC4, "identify": "word",
                "decimal": "10", "name": "Contact counter", "writeable": False},
            {"symbol": "SR", "binary": 0xC1, "identify": "bit",
                "decimal": "10", "name": "Special relay", "offset": "90000", "writeable": False},
            {"symbol": "SD", "binary": 0xC5, "identify": "word",
                "decimal": "10", "name": "Special data register", "offset": "90000", "writeable": False},
        ]

        # FP7シリーズの場合、File registerを追加
        if self.series in const.SERIES_PANASONIC_FP7:
            update_devices = [
                {"symbol": "DT_R", "binary": 0xAF, "identify": "word", "decimal": "10",
                    "name": "Switching file register", "offset": "100000"},
                {"symbol": "DT_ZR", "binary": 0xB0, "identify": "word", "decimal": "10",
                    "name": "Sequential file register", "offset": "100000"},
            ]
            devices = [
                x if x["symbol"] not in [y["symbol"] for y in update_devices]
                else [z for z in update_devices if z["symbol"] == x["symbol"]] for x in devices]

        # bitとwordが同時指定可能で、symbolが同じだが、オプションが異なる場合
        # アドレスの指定に"."(小数点)がある場合、該当デバイスの設定を下記に変換
        if self.has_point is True:
            update_devices = [
                {"symbol": "X", "binary": 0x9C, "identify": "bit",
                    "decimal": "10.F", "name": "Input"},
                {"symbol": "Y", "binary": 0x9D, "identify": "bit",
                    "decimal": "10.F", "name": "Output"},
                {"symbol": "L", "binary": 0xA0, "identify": "bit",
                    "decimal": "10.F", "name": "Link relay"},
                {"symbol": "R", "binary": 0x90, "identify": "bit",
                    "decimal": "10.F", "name": "Internal relay"},
                {"symbol": "M", "binary": 0x90, "identify": "bit",
                    "decimal": "10.F", "name": "Internal relay(MC Compatible)"},
                {"symbol": "T", "binary": 0xA8, "identify": "bit",
                    "decimal": "10.10", "name": "Data register"},
                {"symbol": "C", "binary": 0xC2, "identify": "bit",
                    "decimal": "10.10", "name": "Current timer"},
                {"symbol": "SR", "binary": 0xC1, "identify": "bit",
                    "decimal": "10.10", "name": "Contact timer", "offset": "90000", "writeable": False},
            ]
            devices = [
                x if x["symbol"] not in [y["symbol"] for y in update_devices]
                else [z for z in update_devices if z["symbol"] == x["symbol"]][0] for x in devices]
        return devices

    # Device list
    def devices(self):
        if self.manufacture in const.MANUFACTURER_MITSUBISHI:
            devices = self.plc_mitsubishi()

        elif self.manufacture in const.MANUFACTURER_KEYENCE:
            devices = self.plc_keyence()

        elif self.manufacture in const.MANUFACTURER_PANASONIC:
            devices = self.plc_panasonic()
        else:
            devices = []

        return {
            "transfer_limit": self.transfer_limit,
            "prefix_byte": self.prefix_byte,
            "endian": self.endian,
            "devices": devices,
            "word_length": self.word_length
        }


def device_list(manufacture, *, series=None, has_point=False, transport="udp"):
    if series is None:
        # Default series
        if manufacture in const.MANUFACTURER_MITSUBISHI:
            series = "iq"
        elif manufacture in const.MANUFACTURER_KEYENCE:
            series = "7000"
        elif manufacture in const.MANUFACTURER_PANASONIC:
            series = "fp0"

    if has_point is None or has_point is False:
        has_point = False
    else:
        has_point = True

    d = DeviceList(
        manufacture=manufacture,
        series=series, has_point=has_point, transport=transport
    )
    _devices = d.devices()
    return _devices


if __name__ == "__main__":
    manufacture = "mitsubishi"
    series = "iq"
    has_point = False
    transport = "tcp"

    devices = device_list(
        manufacture=manufacture,
        series=series, has_point=has_point, transport=transport,
    )
    print(devices)
