# from pymodbus3.client.sync import ModbusTcpClient

# import logging
# UNIT = 0x1

# def run_sync_client():
#     try:
#         client = ModbusTcpClient('192.168.0.10', port=502)
#         # client = ModbusClient('localhost', port=502)
#         client.connect()
#         #connected =1

#     except:
#         print("modbus error")
#    # "Read write registeres simulataneously")
#     try:
#         rr = client.read_holding_registers(1, 4, unit=UNIT)
#         # following will write value 10 or 20 to address 1
#         rq = client.write_register(4, 20, unit=UNIT)
#         # close the client
#         client.close()
#         print(rr)
#         print(rr.registers)
#     except Exception as e:
#         print("Modbus Connection returned Error ", e)


# if __name__ == "__main__":
#     run_sync_client()


# from pyModbusTCP.client import ModbusClient
# c = ModbusClient(host="127.0.0.1", auto_open=True, auto_close=True)
# regs = c.read_holding_registers(0, 2)
# if regs:
#     print(regs)
# else:
#     print("read error")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# read_register
# read 10 registers and print result on stdout
# you can use the tiny modbus server "mbserverd" to test this code
# mbserverd is here: https://github.com/sourceperl/mbserverd
# the command line modbus client mbtget can also be useful
# mbtget is here: https://github.com/sourceperl/mbtget
from pyModbusTCP.client import ModbusClient
import time
SERVER_HOST = "192.168.0.10"  # 接続先ホスト
SERVER_PORT = 502
c = ModbusClient()
# uncomment this line to see debug message
# c.debug(True)
# define modbus server host, port
c.host(SERVER_HOST)
c.port(SERVER_PORT)
while True:
    # open or reconnect TCP to server
    if not c.is_open():
        if not c.open():
            print("unable to connect to "+SERVER_HOST+":"+str(SERVER_PORT))
    # if open() is ok, read register (modbus function 0x03)
    if c.is_open():

        # recs = c.read_coils(8192, 10)
        # print(recs)
        # if c.write_multiple_registers(10, [44, 55]):
        #     print("write ok")
        # else:
        #     print("write error")

        # read 10 registers at address 0, store result in regs list
        regs = c.read_holding_registers(0, 125)
        # if success display registers
        if regs:
            print("reg ad #0 to 9: "+str(regs))
    # sleep 2s before next polling
    time.sleep(2)
