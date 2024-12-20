# ===============================================================================
# Name      : status_monitor.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2022-11-28 15:51
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================
import os
import subprocess
import psutil
from pydantic import BaseModel


class RpStatus(BaseModel):
    temp: str
    clock: str
    volts: str
    memory_cpu: str
    memory_gpu: str
    memory_userate: str


def run_shell_command(command_str: str) -> str:
    # unit_list = ['\'C', 'V', 'M']
    proc = subprocess.run(command_str, shell=True, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, text=True)
    result = proc.stdout.split("=")
    return result[1].replace('\n', '')


def unit_converter(value_str: str) -> str:
    value_str = value_str.replace('G', '000000')
    value_str = value_str.replace('M', '000')
    value_str = value_str.replace('K', '')
    return value_str


def get_raspberrypi_status() -> RpStatus:
    """ラズパイのステータス取得

    Returns:
        RpStatus: _description_
    """
    if os.name == 'nt':
        (temp, clock, volts, memory_cpu, memory_gpu, memory_userate) = \
            ('0.0', '0.0', '0.0', '0.0', '0.0', '0.0')

    else:
        temp = run_shell_command("vcgencmd measure_temp")
        clock = run_shell_command("vcgencmd measure_clock arm")
        volts = run_shell_command("vcgencmd measure_volts")
        memory_cpu = run_shell_command("vcgencmd get_mem arm")
        memory_gpu = run_shell_command("vcgencmd get_mem gpu")
        memory_userate = psutil.virtual_memory().percent
        temp = temp.replace('\'C', '')
        volts = volts.replace('V', '')
        memory_cpu = unit_converter(memory_cpu)
        memory_gpu = unit_converter(memory_gpu)

    return RpStatus(
        temp=temp,
        clock=clock,
        volts=volts,
        memory_cpu=memory_cpu,
        memory_gpu=memory_gpu,
        memory_userate=memory_userate
    )


if __name__ == '__main__':
    rp_status = get_raspberrypi_status()
    print(rp_status)
