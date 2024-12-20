from pymodbus.client.sync import ModbusTcpClient
# try:
#     from . import logger
# except Exception:
#     import logger

# logger = logger.get_module_logger(__name__)


def lower_check(str):
    try:
        return str.lower()
    except Exception:
        return str


def try_int(numeric_str):
    try:
        return int(numeric_str)
    except Exception:
        return int(numeric_str, 16)


def datasize_length(device, cmd):
    if not cmd["data"]:
        datalength = try_int(device["max"]) - try_int(device["min"])
    else:
        datalength = len(cmd["data"])
    return datalength


def main(network: dict, protocol: dict, device: dict, cmd: dict, *, optional={}):
    datalength = datasize_length(device=device, cmd=cmd)
    min = try_int(device["min"])
    response = {}
    try:
        unit = network["unit"]
    except Exception:
        unit = 0
    # connection
    try:
        client = ModbusTcpClient(network["ip"], port=network["port"])
        client.connect()
    except Exception as e:
        print("Connect Error: {}".format(str(e)))
    else:
        # Read Command Process
        if lower_check(cmd["cmd"]) in ["read", "r"]:
            return_array = []
            try:
                # Read Coil
                if lower_check(device["device"]) in ["coils", "coil", "c", "do", "01", "1"]:
                    rr_do = client.read_coils(min, datalength, unit=unit)
                    return_array = rr_do.bits
                # Read Input Status
                elif lower_check(device["device"]) in ["discreteinput", "discrete_input", "discrete input", "input", "status", "is", "di", "02", "2"]:
                    rr_di = client.read_discrete_inputs(
                        min, datalength, unit=unit)
                    return_array = rr_di.bits
                # Read Holding Register
                elif lower_check(device["device"]) in ["holdingregisters", "holding_registers", "holding registers", "holdingregister", "holding_register", "holding register", "hr", "ai", "03", "3"]:
                    rr_ai = client.read_holding_registers(
                        min, datalength, unit=unit)
                    return_array = rr_ai.registers
                # Read Input Register
                elif lower_check(device["device"]) in ["inputregisters", "input_registers", "input registers", "inputregister", "input_register", "input register", "ir", "ao", "04", "4"]:
                    rr_ao = client.read_input_registers(
                        min, datalength, unit=unit)
                    return_array = rr_ao.registers

                # # Diagnostics
                # elif lower_check(device["device"]) in ["diagnostics", "08", "8"]:
                #     pass
                # # Read Event Counter
                # elif lower_check(device["device"]) in ["event_counter", "11", "b"]:
                #     pass
                # # Read Event Log
                # elif lower_check(device["device"]) in ["event_counter", "12", "c"]:
                #     pass

                else:
                    raise Exception(
                        "The specified parameter is incorrect. Please check the setting.")
            except Exception as e:
                # logger.warning("Modbus error: {}".format(str(e)))
                return_array = []
                error_code = 10000
                message = str(e)
            else:
                error_code = 0
                message = "success"
            finally:
                client.close()
                response = {
                    "send_binaly": "",
                    "response": "",
                    "exists_data": return_array,
                    "error_code": error_code,
                    "message": message
                }

        # Write Command Process
        elif cmd["cmd"] in ["write", "WRITE", "Write", "w", "W"]:
            try:
                # Write Coil
                if lower_check(device["device"]) in ["coils", "coil", "c", "do", "05", "5"]:
                    if len(cmd["data"]) == 1:
                        rq_do = client.write_coil(min, cmd["data"][0])
                    else:
                        rq_do = client.write_coil(min, cmd["data"])
                    return_array = rq_do
                # Write Holding Register
                elif lower_check(device["device"]) in ["holdingregisters", "holding_registers", "holding registers", "holdingregister", "holding_register", "holding register", "ai", "06", "6"]:
                    if len(cmd["data"]) == 1:
                        rq_ai = client.write_registers(min, cmd["data"][0])
                    else:
                        rq_ai = client.write_registers(min, cmd["data"])
                    return_array = rq_ai
                else:
                    raise Exception(
                        "The specified parameter is incorrect. Please check the setting.")
            except Exception as e:
                # logger.warning("Modbus error: {}".format(str(e)))
                return_array = []
                error_code = 10000
                message = str(e)
            else:
                error_code = 0
                message = "success"
            finally:
                client.close()
                response = {
                    "send_binaly": "",
                    "response": "",
                    "exists_data": return_array,
                    "error_code": error_code,
                    "message": message
                }
    finally:
        # print(response)
        return response


def _main(configure):
    ip_address = configure["network"]["ip_address"]
    port = configure["network"][""]
    # connection
    try:
        client = ModbusTcpClient(ip_address, port=port)
        client.connect()
    except Exception as e:
        print("Connect Error: {}".format(str(e)))
    else:
        # TODO Readのみ

        # UNITは基本的に0
        unit = 0

        datas = configure["data"]
        for data in datas:
            data_unit = data["data_unit"]
            if data_unit in ["integer"]:
                data_length = 4


        return_array = []
        # Read Coil
        # if lower_check(device["device"]) in ["coils", "coil", "c", "do", "01", "1"]:
        #     rr_do = client.read_coils(min, datalength, unit=unit)
        #     return_array = rr_do.bits
        # # Read Input Status
        # elif lower_check(device["device"]) in ["discreteinput", "discrete_input", "discrete input", "input", "status", "is", "di", "02", "2"]:
        #     rr_di = client.read_discrete_inputs(
        #         min, datalength, unit=unit)
        #     return_array = rr_di.bits
        # Read Holding Register
        # elif lower_check(device["device"]) in ["holdingregisters", "holding_registers", "holding registers", "holdingregister", "holding_register", "holding register", "hr", "ai", "03", "3"]:
            rr_ai = client.read_holding_registers(
                min, datalength, unit=unit)
            return_array = rr_ai.registers
        # # Read Input Register
        # elif lower_check(device["device"]) in ["inputregisters", "input_registers", "input registers", "inputregister", "input_register", "input register", "ir", "ao", "04", "4"]:
        #     rr_ao = client.read_input_registers(
        #         min, datalength, unit=unit)
        #     return_array = rr_ao.registers



if __name__ == "__main__":
    network = {"ip": "192.168.16.112", "port": 502, "unit": 0}
    # network = {"ip": "192.168.16.73", "port": 502}
    protocol = {"manufacture": "fanuc", "series": "nj",
                "protocol": "modbus", "transport_layer": "tcp", "period_index": None, }
    device = {"device": "HOLDING_REGISTERS", "min": "0", "max": "10"}
    cmd = {"cmd": "read", "data": [], "option": ""}
    optional = {}
    response = main(
        network=network,
        protocol=protocol,
        device=device,
        cmd=cmd,
        optional=optional
    )

    print(response)

    configure = {
        'network': {'ip_address': '192.168.250.39', 'port': 9600},
        'controller': {'type': 'PLC', 'manufacturer': 'Mitsubishi Electric', 'series': 'MELSEC iQ-R', 'protocol': 'SLMP/TCP', 'attributes': {}},
        'data': [
            {
                'execute': 'read',
                'machine_id': 1,
                'datatype': 'Input',
                'device': 'HOLDING_REGISTERS', 'address': 0,
                'data_unit': 'integer',
                'trigger': None, 'item': None
            },
            {
                'execute': 'read',
                'machine_id': 1,
                'datatype': 'Input',
                'device': 'HOLDING_REGISTERS', 'address': 10,
                'data_unit': 'integer',
                'trigger': None, 'item': None
            },
        ]
    }


    """
        HOLDING_REGISTERS: ['10', 0x00, 'w'],
        # INPUT_REGISTERS: ['10', 0x00, 'w'],
        # DISCRETE_INPUT: ['10', 0x00, 'b'],
        # COILS: ['10', 0x00, 'b'],

    """

