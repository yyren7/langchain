try:
    from .. import const
except Exception:
    import sys
    import pathlib
    parent_dir = str(pathlib.Path(__file__).parent.parent.resolve())
    sys.path.append(parent_dir)
    import const


class DeviceList():
    def __init__(self, *, manufacture="omron", series="default", has_point=False, transport="udp"):
        self.manufacture = manufacture
        self.series = series
        self.has_point = has_point
        self.transport = transport
        self.endian = ""
        self.transfer_limit = 0
        self.perfix_bit = 0

    def plc_omron(self):
        self.endian = "big"
        self.transfer_limit = 498
        if self.transport in const.TRANSPORT_UDP:
            self.prefix_byte = 28
        else:
            self.prefix_byte = 60

        if self.series in ["cvm1", "cv"]:
            devices = [
                {"symbol": "CIO", "binary": 0x00, "identify": "bit",
                    "decimal": "10.15", "name": "Chanel I/O", "range": ["0.0", "2555.15"]},
                {"symbol": "AR[RO]", "binary": 0x00, "identify": "bit",
                    "decimal": "10.15", "name": "Special auxiliary relay", "range": ["0.0", "447.15"],
                    "offset": 2816, "optional": "readonly", },
                {"symbol": "AR", "binary": 0x00, "identify": "bit",
                    "decimal": "10.15", "name": "Special auxiliary relay", "range": ["0.0", "959.15"], "offset": 2816},
                # Memory
                {"symbol": "DM", "binary": 0x82, "identify": "bit",
                    "decimal": "10", "name": "Data memory", "range": ["0", "32767"]},
                # Timer
                {"symbol": "TIM", "binary": 0x01, "identify": "word",
                    "decimal": "10", "name": "Timer up flag", "range": ["0", "2047"]},
                {"symbol": "TIM[C]", "binary": 0x81, "identify": "word",
                    "decimal": "10", "name": "Timer current value", "range": ["0", "2047"]},
                # Counter
                {"symbol": "CNT", "binary": 0x01, "identify": "word",
                    "decimal": "10", "name": "Counter up flag", "range": ["0", "2047"], "offset": 8000},
                {"symbol": "CNT[C]", "binary": 0x81, "identify": "word",
                    "decimal": "10", "name": "Counter current value", "range": ["0", "2047"], "offset": 8000},
                {"symbol": "EM_0", "binary": 0x90, "identify": "word",
                    "decimal": "10", "name": "Expansion memory 0", "range": ["0", "32767"]},
                {"symbol": "EM_1", "binary": 0x91, "identify": "word",
                    "decimal": "10", "name": "Expansion memory 1", "range": ["0", "32767"]},
                {"symbol": "EM_2", "binary": 0x92, "identify": "word",
                    "decimal": "10", "name": "Expansion memory 2", "range": ["0", "32767"]},
                {"symbol": "EM_3", "binary": 0x93, "identify": "word",
                    "decimal": "10", "name": "Expansion memory 3", "range": ["0", "32767"]},
                {"symbol": "EM_4", "binary": 0x94, "identify": "word",
                    "decimal": "10", "name": "Expansion memory 4", "range": ["0", "32767"]},
                {"symbol": "EM_5", "binary": 0x95, "identify": "word",
                    "decimal": "10", "name": "Expansion memory 5", "range": ["0", "32767"]},
                {"symbol": "EM_6", "binary": 0x96, "identify": "word",
                    "decimal": "10", "name": "Expansion memory 6", "range": ["0", "32767"]},
                {"symbol": "EM_7", "binary": 0x97, "identify": "word",
                    "decimal": "10", "name": "Expansion memory 7", "range": ["0", "32767"]},
                {"symbol": "EM[C]", "binary": 0x98, "identify": "word",
                    "decimal": "10", "name": "Expansion memory current bank", "range": ["0", "32767"]},
                # Data register
                {"symbol": "DR", "binary": 0x9C, "identify": "word",
                    "decimal": "10", "name": "Data register", "range": ["0", "2"]},
            ]
            if self.has_point is not True:
                update_devices = [
                    {"symbol": "CIO", "binary": 0x80, "identify": "word",
                        "decimal": "10", "name": "Chanel I/O", "range": ["0", "2555"]},
                    {"symbol": "AR[RO]", "binary": 0x80, "identify": "word",
                        "decimal": "10", "name": "Special auxiliary relay", "range": ["0", "447"],
                        "offset": 2816, "optional": "readonly", },
                    {"symbol": "AR", "binary": 0x80, "identify": "word",
                        "decimal": "10", "name": "Special auxiliary relay", "range": ["0", "959"], "offset": 2816},
                ]
                devices = [
                    x if x["symbol"] not in [y["symbol"] for y in update_devices]
                    else [z for z in update_devices if z["symbol"] == x["symbol"]][0] for x in devices]

        # ["cs", "cj", "cp", "nsj"]
        else:
            devices = [
                # Relay
                {"symbol": "CIO", "binary": 0x30, "identify": "bit",
                    "decimal": "10.15", "name": "Chanel I/O", "range": ["0.0", "6143.15"]},
                {"symbol": "WR", "binary": 0x31, "identify": "bit",
                    "decimal": "10.15", "name": "Internal auxiliary relay", "range": ["0.0", "511.15"]},
                {"symbol": "HR", "binary": 0x32, "identify": "bit",
                    "decimal": "10.15", "name": "Holding relay", "range": ["0.0", "511.15"]},
                {"symbol": "AR[RO]", "binary": 0x33, "identify": "bit",
                    "decimal": "10.15", "name": "Special auxiliary relay", "range": ["0.0", "447.15"], "optional": "readonly"},
                {"symbol": "AR", "binary": 0x33, "identify": "bit",
                    "decimal": "10.15", "name": "Special auxiliary relay", "range": ["0.0", "959.15"]},
                # Memory
                {"symbol": "DM", "binary": 0x02, "identify": "bit",
                    "decimal": "10.15", "name": "Data memory", "range": ["0.0", "32767.15"]},
                # Expansion memory
                {"symbol": "EM_0", "binary": 0x20, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 0", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_1", "binary": 0x21, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 1", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_2", "binary": 0x22, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 2", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_3", "binary": 0x23, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 3", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_4", "binary": 0x24, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 4", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_5", "binary": 0x25, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 5", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_6", "binary": 0x26, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 6", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_7", "binary": 0x27, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 7", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_8", "binary": 0x28, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 8", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_9", "binary": 0x29, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 9", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_A", "binary": 0x2A, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory A", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_B", "binary": 0x2B, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory B", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_C", "binary": 0x2C, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory C", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_D", "binary": 0x2D, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory D", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_E", "binary": 0x2E, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory E", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_F", "binary": 0x2F, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory F", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_10", "binary": 0xE0, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 10", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_11", "binary": 0xE1, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 11", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_12", "binary": 0xE2, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 12", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_13", "binary": 0xE3, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 13", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_14", "binary": 0xE4, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 14", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_15", "binary": 0xE5, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 15", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_16", "binary": 0xE6, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 16", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_17", "binary": 0xE7, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 17", "range": ["0.0", "32767.15"]},
                {"symbol": "EM_18", "binary": 0xE8, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory 18", "range": ["0.0", "32767.15"]},
                {"symbol": "EM[C]", "binary": 0x0A, "identify": "bit",
                    "decimal": "10.15", "name": "Expansion memory current bank", "range": ["0.0", "32767.15"]},
                # Task flag
                {"symbol": "TK", "binary": 0x06, "identify": "bit",
                    "decimal": "10", "name": "Task flag", "range": ["0", "31"]},
                # Index register
                {"symbol": "IR", "binary": 0xDC, "identify": "word",
                    "decimal": "10", "name": "Index register", "range": ["0", "15"]},
                # Data register
                {"symbol": "DR", "binary": 0xBC, "identify": "word",
                    "decimal": "10", "name": "Data register", "range": ["0", "15"]},
                # Timer
                {"symbol": "TIM", "binary": 0x09, "identify": "word",
                    "decimal": "10", "name": "Timer up flag", "range": ["0", "4095"]},
                {"symbol": "TIM[C]", "binary": 0x89, "identify": "word",
                    "decimal": "10", "name": "Timer current value", "range": ["0", "4095"]},
                # Counter
                {"symbol": "CNT", "binary": 0x09, "identify": "word",
                    "decimal": "10", "name": "Counter up flag", "range": ["0", "4095"], "offset": 8000},
                {"symbol": "CNT[C]", "binary": 0x89, "identify": "word",
                    "decimal": "10", "name": "Counter current value", "range": ["0", "4095"], "offset": 8000},
            ]
            if self.has_point is not True:
                update_devices = [
                    {"symbol": "CIO", "binary": 0xB0, "identify": "word",
                        "decimal": "10", "name": "Chanel I/O", "range": ["0", "6143"]},
                    {"symbol": "WR", "binary": 0xB1, "identify": "word",
                        "decimal": "10", "name": "Internal auxiliary relay", "range": ["0", "511"]},
                    {"symbol": "HR", "binary": 0xB2, "identify": "word",
                        "decimal": "10", "name": "Holding relay", "range": ["0", "511"]},
                    {"symbol": "AR[RO]", "binary": 0xB3, "identify": "word",
                        "decimal": "10", "name": "Special auxiliary relay", "range": ["0", "447"], "optional": "readonly"},
                    {"symbol": "AR", "binary": 0xB3, "identify": "word",
                        "decimal": "10", "name": "Special auxiliary relay", "range": ["0", "959"]},
                    # Memory
                    {"symbol": "DM", "binary": 0x82, "identify": "word",
                        "decimal": "10", "name": "Data memory", "range": ["0", "32767"]},
                    # Expansion memory
                    {"symbol": "EM_0", "binary": 0xA0, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 0", "range": ["0", "32767"]},
                    {"symbol": "EM_1", "binary": 0xA1, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 1", "range": ["0", "32767"]},
                    {"symbol": "EM_2", "binary": 0xA2, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 2", "range": ["0", "32767"]},
                    {"symbol": "EM_3", "binary": 0xA3, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 3", "range": ["0", "32767"]},
                    {"symbol": "EM_4", "binary": 0xA4, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 4", "range": ["0", "32767"]},
                    {"symbol": "EM_5", "binary": 0xA5, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 5", "range": ["0", "32767"]},
                    {"symbol": "EM_6", "binary": 0xA6, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 6", "range": ["0", "32767"]},
                    {"symbol": "EM_7", "binary": 0xA7, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 7", "range": ["0", "32767"]},
                    {"symbol": "EM_8", "binary": 0xA8, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 8", "range": ["0", "32767"]},
                    {"symbol": "EM_9", "binary": 0xA9, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 9", "range": ["0", "32767"]},
                    {"symbol": "EM_A", "binary": 0xAA, "identify": "word",
                        "decimal": "10", "name": "Expansion memory A", "range": ["0", "32767"]},
                    {"symbol": "EM_B", "binary": 0xAB, "identify": "word",
                        "decimal": "10", "name": "Expansion memory B", "range": ["0", "32767"]},
                    {"symbol": "EM_C", "binary": 0xAC, "identify": "word",
                        "decimal": "10", "name": "Expansion memory C", "range": ["0", "32767"]},
                    {"symbol": "EM_D", "binary": 0xAD, "identify": "word",
                        "decimal": "10", "name": "Expansion memory D", "range": ["0", "32767"]},
                    {"symbol": "EM_E", "binary": 0xAE, "identify": "word",
                        "decimal": "10", "name": "Expansion memory E", "range": ["0", "32767"]},
                    {"symbol": "EM_F", "binary": 0xAF, "identify": "word",
                        "decimal": "10", "name": "Expansion memory F", "range": ["0", "32767"]},
                    {"symbol": "EM_10", "binary": 0x60, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 10", "range": ["0", "32767"]},
                    {"symbol": "EM_11", "binary": 0x61, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 11", "range": ["0", "32767"]},
                    {"symbol": "EM_12", "binary": 0x62, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 12", "range": ["0", "32767"]},
                    {"symbol": "EM_13", "binary": 0x63, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 13", "range": ["0", "32767"]},
                    {"symbol": "EM_14", "binary": 0x64, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 14", "range": ["0", "32767"]},
                    {"symbol": "EM_15", "binary": 0x65, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 15", "range": ["0", "32767"]},
                    {"symbol": "EM_16", "binary": 0x66, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 16", "range": ["0", "32767"]},
                    {"symbol": "EM_17", "binary": 0x67, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 17", "range": ["0", "32767"]},
                    {"symbol": "EM_18", "binary": 0x68, "identify": "word",
                        "decimal": "10", "name": "Expansion memory 18", "range": ["0", "32767"]},
                    {"symbol": "EM[C]", "binary": 0x90, "identify": "word",
                        "decimal": "10", "name": "Expansion memory current bank", "range": ["0", "32767"]},
                    # Task flag
                    {"symbol": "TK", "binary": 0x46, "identify": "word",
                        "decimal": "10", "name": "Task flag", "range": ["0", "31"]},
                ]
                devices = [
                    x if x["symbol"] not in [y["symbol"] for y in update_devices]
                    else [z for z in update_devices if z["symbol"] == x["symbol"]][0] for x in devices]

        return devices

    # Device list
    def devices(self):
        if self.manufacture in const.MANUFACTURER_OMRON:
            devices = self.plc_omron()
        else:
            devices = []

        return {
            "transfer_limit": self.transfer_limit,
            "prefix_byte": self.prefix_byte,
            "endian": self.endian,
            "devices": devices
        }


def device_list(manufacture, *, series=None, has_point=False, transport="udp"):
    if series is None:
        # Default series
        if manufacture in const.MANUFACTURER_OMRON:
            series = ""

    if has_point is None or has_point is False:
        has_point = False
    else:
        has_point = True

    d = DeviceList(
        manufacture=manufacture,
        series=series, has_point=has_point,
        transport=transport
    )
    _devices = d.devices()
    return _devices


if __name__ == "__main__":
    manufacture = "mitsubishi"
    series = "iq"
    has_point = False
    transport = "udp"

    devices = device_list(
        manufacture=manufacture,
        series=series, has_point=has_point, transport=transport)
    print(devices)
