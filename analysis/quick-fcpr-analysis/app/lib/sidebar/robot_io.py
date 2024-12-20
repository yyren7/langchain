from lib.utility.constant import DM, EM, R, MR, LR, CR, T
from lib.utility.common_globals import L, RD, RAC
from lib.utility.constant import TEACH_FILE_PATH, NUMBER_PARAM_FILE_PATH, FLAG_PARAM_FILE_PATH, ERROR_FILE_PATH
# from lib.utility.globals import error_yaml, number_param_yaml, initial_number_param_yaml

import lib.utility.functions as func
import lib.utility.helper as helper


def set_on_off_output(device_name, lamp_device_no, pin_no):
  L.LDP(device_name, lamp_device_no)
  if (L.aax & L.iix):
    RAC.send_command(f"setOutputON({pin_no})")
  L.LDF(device_name, lamp_device_no)
  if (L.aax & L.iix):
    RAC.send_command(f"setOutputOFF({pin_no})")

# input操作
def handle_input(robot_status):
  # DI0
  DI = 0
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI1
  DI = 2
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI2
  DI = 2
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI3
  DI = 3
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI4
  DI = 4
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI5
  DI = 5
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI6
  DI = 6
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI7
  DI = 7
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI8
  DI = 8
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI9
  DI = 9
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI10
  DI = 10
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI11
  DI = 11
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI12
  DI = 12
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI13
  DI = 13
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI14
  DI = 14
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)
  # DI15
  DI = 15
  RAC.send_command(f'getInput({DI+1})')
  L.LD(robot_status['input_signal'][DI])
  L.OUT(R, 5300+DI)

# Output操作
def handle_output():
  # DO0
  DO = 0
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO1
  DO = 1
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO2
  DO = 2
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO3
  DO = 3
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO4
  DO = 4
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO5
  DO = 5
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO6
  DO = 6
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO7
  DO = 7
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO8
  DO = 8
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO9
  DO = 9
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO10
  DO = 10
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO11
  DO = 11
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO12
  DO = 12
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO13
  DO = 13
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO14
  DO = 14
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)
  # DO15
  DO = 15
  func.create_bit_button(device_name=R, btn_device_no=100+DO, lamp_device_no=5100+DO)
  set_on_off_output(device_name=R, lamp_device_no=5100+DO, pin_no=1+DO)

  # func.create_bit_button(device_name=R, btn_device_no=200, lamp_device_no=5200)
  # func.create_bit_button(device_name=R, btn_device_no=201, lamp_device_no=5201)
  # func.create_bit_button(device_name=R, btn_device_no=202, lamp_device_no=5202)
  # func.create_bit_button(device_name=R, btn_device_no=203, lamp_device_no=5203)
  # func.create_bit_button(device_name=R, btn_device_no=204, lamp_device_no=5204)
  # func.create_bit_button(device_name=R, btn_device_no=205, lamp_device_no=5205)
  # func.create_bit_button(device_name=R, btn_device_no=206, lamp_device_no=5206)
  # func.create_bit_button(device_name=R, btn_device_no=207, lamp_device_no=5207)
  # func.create_bit_button(device_name=R, btn_device_no=208, lamp_device_no=5208)
  # func.create_bit_button(device_name=R, btn_device_no=209, lamp_device_no=5209)
  # func.create_bit_button(device_name=R, btn_device_no=210, lamp_device_no=5210)
  # func.create_bit_button(device_name=R, btn_device_no=211, lamp_device_no=5211)
  # func.create_bit_button(device_name=R, btn_device_no=212, lamp_device_no=5212)
  # func.create_bit_button(device_name=R, btn_device_no=213, lamp_device_no=5213)
  # func.create_bit_button(device_name=R, btn_device_no=214, lamp_device_no=5214)
  # func.create_bit_button(device_name=R, btn_device_no=215, lamp_device_no=5215)
