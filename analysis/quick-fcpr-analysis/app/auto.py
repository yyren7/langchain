# -*- coding : UTF-8 -*-
import time, json, os, sys, importlib, signal, copy, pickle
# To use globals var
from lib.utility.constant import DM, EM, R, MR, LR, CR, T
from lib.utility.common_globals import L, RD, RAC
from lib.utility.auto_globals import PLC_R_DM, PLC_MR_EM, error_yaml, number_param_yaml, initial_number_param_yaml
from lib.utility.constant import TEACH_FILE_PATH, NUMBER_PARAM_FILE_PATH, FLAG_PARAM_FILE_PATH, ERROR_FILE_PATH
# To use laddar func
import lib.utility.functions as func
import lib.utility.helper as helper
# To read sidebar
import lib.sidebar.teaching as teach
import lib.sidebar.number_parameter as num_param
import lib.sidebar.robot_io as rb_io

def signal_handler(sig, frame):
  func.cleanup()
  sys.exit(-1)

if os.name == 'nt':
  signal.signal(signal.SIGBREAK, signal_handler) 
elif os.name == 'posix':
  signal.signal(signal.SIGTERM, signal_handler) 
signal.signal(signal.SIGINT, signal_handler)

ERROR_INTERVAL = 5
TIMEOUT_MSEC = 30000

success = False
pallet_settings = {}
pallet_offset = [{'x': 0.0, 'y': 0.0, 'z': 0.0} for _ in range(10)]
current_pos = {'x': 0.0, 'y': 0.0, 'z': 0.0,'rx': 0.0, 'ry': 0.0, 'rz': 0.0}
camera_responded  = [False for _ in range(10)]
camera_connected = [False for _ in range(10)]
camera_instance = [None for _ in range(10)]
camera_offset = [{'x': 0.0, 'y': 0.0, 'r': 0.0} for _ in range(10)]


RB_is_connected = False
auto_status = 'AUTO MODE.'
L.EM_relay[0:0+len(helper.name_to_ascii16(auto_status, 40))] = helper.name_to_ascii16(auto_status, 40)

if __name__ == '__main__':
  while True:
    try:
      #print('Auto program is running...')
      func.send_command()
      time.sleep(0.001)
      L.updateTime()
      L.ldlg = 0x0
      L.aax  = 0x0 
      L.trlg = 0x0 
      L.iix  = 0x01
      func.get_command()
      func.create_cycle_timer()
      func.check_auto_error(error_yaml)
      func.update_auto_status(number_param_yaml, initial_number_param_yaml)
      func.blink_reset_button()

      L.LD(CR, 2008)
      L.OR(L.local_R['start_program[0]']['name'], L.local_R['start_program[0]']['addr'])
      L.ANB(L.local_R['reset_program[0]']['name'], L.local_R['reset_program[0]']['addr'])
      L.OUT(L.local_R['start_program[0]']['name'], L.local_R['start_program[0]']['addr'])

      #;Process:select_robot@1
      L.LD(L.local_R['start_program[0]']['name'], L.local_R['start_program[0]']['addr'])
      L.MPS()
      L.LDB(L.local_MR['seq_step[2000]']['name'], L.local_MR['seq_step[2000]']['addr'])
      L.ANB(RB_is_connected)
      L.ANL()
      L.OUT(L.local_MR['seq_step[0]']['name'], L.local_MR['seq_step[0]']['addr'])
      L.MPP()
      L.LD(RB_is_connected)
      L.OR(L.local_MR['seq_step[2000]']['name'], L.local_MR['seq_step[2000]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2000]']['name'], L.local_MR['seq_step[2000]']['addr'])
      #;Post-Process:select_robot@1
      L.LDP(L.local_MR['seq_step[0]']['name'], L.local_MR['seq_step[0]']['addr'])
      if (L.aax & L.iix):
        RB_is_connected = True
      if(RB_is_connected):
        L.LDP(L.local_R['reset_program[0]']['name'], L.local_R['reset_program[0]']['addr'])
        if (L.aax & L.iix):
          RAC.send_command('resetError()')
        robot_status = RAC.get_status()
        servo = robot_status['servo']
        origin = robot_status['origin']
        arrived = robot_status['arrived']
        error = robot_status['error']
        error_id = robot_status['error_id']
        input_signal = robot_status['input_signal']
        func.handle_auto_sidebar(robot_status)
        L.LDP(R, 5003)
        L.ORP(MR, 501)
        if (L.aax & L.iix):
          RAC.send_command('stopRobot()')
          print(robot_status['error_id'])
        L.LD(R, 5003)
        L.OR(MR, 501)
        L.OUT(MR, 4)
        if robot_status['current_pos']:
          current_pos['x'] = robot_status['current_pos'][0]
          current_pos['y'] = robot_status['current_pos'][1]
          current_pos['z'] = robot_status['current_pos'][2]
          current_pos['rx'] = robot_status['current_pos'][3]
          current_pos['ry'] = robot_status['current_pos'][4]
          current_pos['rz'] = robot_status['current_pos'][5]

      #;Process:set_pallet@1
      L.LD(L.local_MR['seq_step[2000]']['name'], L.local_MR['seq_step[2000]']['addr'])
      L.MPS()
      L.ANB(L.local_MR['seq_step[2001]']['name'], L.local_MR['seq_step[2001]']['addr'])
      L.OUT(L.local_MR['seq_step[1]']['name'], L.local_MR['seq_step[1]']['addr'])
      L.MPP()
      L.LDPB(L.local_MR['seq_step[1]']['name'], L.local_MR['seq_step[1]']['addr'])
      L.OR(L.local_MR['seq_step[2001]']['name'], L.local_MR['seq_step[2001]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2001]']['name'], L.local_MR['seq_step[2001]']['addr'])
      #;Post-Process:set_pallet@1
      L.LDP(L.local_MR['seq_step[1]']['name'], L.local_MR['seq_step[1]']['addr'])
      if (L.aax & L.iix):
        contents = {}
        contents['dst_pocket'] = 1
        contents['row'] = 2
        contents['col'] = 2
        contents['A'] = {'x':218, 'y':235, 'z':17.8}
        contents['B'] = {'x':218, 'y':268, 'z':17.8}
        contents['C'] = {'x':135, 'y':235, 'z':17.8}
        contents['D'] = {'x':135, 'y':268, 'z':17.8}
        pallet_settings[1-1] = contents.copy()

      #;Process:set_motor@1
      L.LD(L.local_MR['seq_step[2001]']['name'], L.local_MR['seq_step[2001]']['addr'])
      L.MPS()
      L.ANB(L.local_MR['seq_step[2002]']['name'], L.local_MR['seq_step[2002]']['addr'])
      L.OUT(L.local_MR['seq_step[2]']['name'], L.local_MR['seq_step[2]']['addr'])
      L.MPP()
      L.LD(servo)
      L.OR(L.local_MR['seq_step[2002]']['name'], L.local_MR['seq_step[2002]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2002]']['name'], L.local_MR['seq_step[2002]']['addr'])
      #;Post-Process:set_motor@1
      L.LDP(L.local_MR['seq_step[2]']['name'], L.local_MR['seq_step[2]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command('setServoOn()')

      #;Process:loop@1
      L.LD(L.local_MR['seq_step[2002]']['name'], L.local_MR['seq_step[2002]']['addr'])
      L.ANB(L.local_MR['seq_step[2023]']['name'], L.local_MR['seq_step[2023]']['addr'])
      L.MPS()
      L.ANB(L.local_MR['seq_step[2003]']['name'], L.local_MR['seq_step[2003]']['addr'])
      L.OUT(L.local_MR['seq_step[3]']['name'], L.local_MR['seq_step[3]']['addr'])
      L.MPP()
      L.LDPB(L.local_MR['seq_step[3]']['name'], L.local_MR['seq_step[3]']['addr'])
      L.OR(L.local_MR['seq_step[2003]']['name'], L.local_MR['seq_step[2003]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2003]']['name'], L.local_MR['seq_step[2003]']['addr'])

      #;Process:moveL@1
      L.LD(L.local_MR['seq_step[2003]']['name'], L.local_MR['seq_step[2003]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2004]']['name'], L.local_MR['seq_step[2004]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[4]']['name'], L.local_MR['seq_step[4]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[4]']['name'], L.local_T['move_static_timer[4]']['addr'])
      L.ANPB(L.local_MR['seq_step[4]']['name'], L.local_MR['seq_step[4]']['addr'])
      L.OR(L.local_MR['seq_step[2004]']['name'], L.local_MR['seq_step[2004]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2004]']['name'], L.local_MR['seq_step[2004]']['addr'])
      #;Post-Process:moveL@1
      #;timeout:moveL@1
      L.LDP(L.local_MR['seq_step[4]']['name'], L.local_MR['seq_step[4]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+4*ERROR_INTERVAL+(1-1), message='moveL@1:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[4]']['name'], L.local_MR['seq_step[4]']['addr'])
      L.TMS(L.local_T['block_timeout[4]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[4]']['name'], L.local_MR['seq_step[4]']['addr'])
      L.LDP(L.local_T['block_timeout[4]']['name'], L.local_T['block_timeout[4]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+4*ERROR_INTERVAL+(1-1), error_yaml=error_yaml)
      #;action:moveL@1
      L.LDP(L.local_MR['seq_step[4]']['name'], L.local_MR['seq_step[4]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(335, 0, 70, 0, 0, -10.989, 100, 100, 100, 0, 0, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[4]']['name'], L.local_MR['seq_step[4]']['addr'])
      L.ANB(L.local_MR['seq_step[2004]']['name'], L.local_MR['seq_step[2004]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0)')
      L.LD(L.local_MR['seq_step[4]']['name'], L.local_MR['seq_step[4]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[4]']['addr'], 0)
      #;error:moveL@1
      L.LD(L.local_MR['seq_step[4]']['name'], L.local_MR['seq_step[4]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+4*ERROR_INTERVAL+(1-1)+1, message=f"moveL@1:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+4*ERROR_INTERVAL+(1-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+4*ERROR_INTERVAL+(1-1)+2, message='moveL@1:Target velocity is zero.')
          func.raise_error(no=801+4*ERROR_INTERVAL+(1-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+4*ERROR_INTERVAL+(1-1)+3, message='moveL@1:Target acceleration is zero.')
          func.raise_error(no=801+4*ERROR_INTERVAL+(1-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+4*ERROR_INTERVAL+(1-1)+4, message='moveL@1:Target deceleration is zero.')
          func.raise_error(no=801+4*ERROR_INTERVAL+(1-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+4*ERROR_INTERVAL+(1-1)+5, message='moveL@1:Servo is off.')
          func.raise_error(no=801+4*ERROR_INTERVAL+(1-1)+5, error_yaml=error_yaml)

      #;Process:moveL@2
      L.LD(L.local_MR['seq_step[2004]']['name'], L.local_MR['seq_step[2004]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2005]']['name'], L.local_MR['seq_step[2005]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[5]']['name'], L.local_MR['seq_step[5]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[5]']['name'], L.local_T['move_static_timer[5]']['addr'])
      L.ANPB(L.local_MR['seq_step[5]']['name'], L.local_MR['seq_step[5]']['addr'])
      L.OR(L.local_MR['seq_step[2005]']['name'], L.local_MR['seq_step[2005]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2005]']['name'], L.local_MR['seq_step[2005]']['addr'])
      #;Post-Process:moveL@2
      #;timeout:moveL@2
      L.LDP(L.local_MR['seq_step[5]']['name'], L.local_MR['seq_step[5]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+5*ERROR_INTERVAL+(2-1), message='moveL@2:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[5]']['name'], L.local_MR['seq_step[5]']['addr'])
      L.TMS(L.local_T['block_timeout[5]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[5]']['name'], L.local_MR['seq_step[5]']['addr'])
      L.LDP(L.local_T['block_timeout[5]']['name'], L.local_T['block_timeout[5]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+5*ERROR_INTERVAL+(2-1), error_yaml=error_yaml)
      #;action:moveL@2
      L.LDP(L.local_MR['seq_step[5]']['name'], L.local_MR['seq_step[5]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(335, 0, -67, 0, 0, -10.989, 100, 100, 100, 0.1, 1000, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[5]']['name'], L.local_MR['seq_step[5]']['addr'])
      L.ANB(L.local_MR['seq_step[2005]']['name'], L.local_MR['seq_step[2005]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0.1)')
      L.LD(L.local_MR['seq_step[5]']['name'], L.local_MR['seq_step[5]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[5]']['addr'], 1000)
      #;error:moveL@2
      L.LD(L.local_MR['seq_step[5]']['name'], L.local_MR['seq_step[5]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+5*ERROR_INTERVAL+(2-1)+1, message=f"moveL@2:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+5*ERROR_INTERVAL+(2-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+5*ERROR_INTERVAL+(2-1)+2, message='moveL@2:Target velocity is zero.')
          func.raise_error(no=801+5*ERROR_INTERVAL+(2-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+5*ERROR_INTERVAL+(2-1)+3, message='moveL@2:Target acceleration is zero.')
          func.raise_error(no=801+5*ERROR_INTERVAL+(2-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+5*ERROR_INTERVAL+(2-1)+4, message='moveL@2:Target deceleration is zero.')
          func.raise_error(no=801+5*ERROR_INTERVAL+(2-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+5*ERROR_INTERVAL+(2-1)+5, message='moveL@2:Servo is off.')
          func.raise_error(no=801+5*ERROR_INTERVAL+(2-1)+5, error_yaml=error_yaml)

      #;Process:set_output@1
      L.LD(L.local_MR['seq_step[2005]']['name'], L.local_MR['seq_step[2005]']['addr'])
      L.MPS()
      L.ANB(L.local_MR['seq_step[2006]']['name'], L.local_MR['seq_step[2006]']['addr'])
      L.OUT(L.local_MR['seq_step[6]']['name'], L.local_MR['seq_step[6]']['addr'])
      L.MPP()
      L.LDPB(L.local_MR['seq_step[6]']['name'], L.local_MR['seq_step[6]']['addr'])
      L.OR(L.local_MR['seq_step[2006]']['name'], L.local_MR['seq_step[2006]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2006]']['name'], L.local_MR['seq_step[2006]']['addr'])
      #;Post-Process:set_output@1
      #;timeout:set_output@1
      L.LDP(L.local_MR['seq_step[6]']['name'], L.local_MR['seq_step[6]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+6*ERROR_INTERVAL+(1-1), message='set_output@1:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[6]']['name'], L.local_MR['seq_step[6]']['addr'])
      L.TMS(L.local_T['block_timeout[6]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[6]']['name'], L.local_MR['seq_step[6]']['addr'])
      L.LDP(L.local_T['block_timeout[6]']['name'], L.local_T['block_timeout[6]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+6*ERROR_INTERVAL+(1-1), error_yaml=error_yaml)
      L.LDP(L.local_MR['seq_step[6]']['name'], L.local_MR['seq_step[6]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command('setOutputON(1)')

      #;Process:moveL@3
      L.LD(L.local_MR['seq_step[2006]']['name'], L.local_MR['seq_step[2006]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2007]']['name'], L.local_MR['seq_step[2007]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[7]']['name'], L.local_MR['seq_step[7]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[7]']['name'], L.local_T['move_static_timer[7]']['addr'])
      L.ANPB(L.local_MR['seq_step[7]']['name'], L.local_MR['seq_step[7]']['addr'])
      L.OR(L.local_MR['seq_step[2007]']['name'], L.local_MR['seq_step[2007]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2007]']['name'], L.local_MR['seq_step[2007]']['addr'])
      #;Post-Process:moveL@3
      #;timeout:moveL@3
      L.LDP(L.local_MR['seq_step[7]']['name'], L.local_MR['seq_step[7]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+7*ERROR_INTERVAL+(3-1), message='moveL@3:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[7]']['name'], L.local_MR['seq_step[7]']['addr'])
      L.TMS(L.local_T['block_timeout[7]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[7]']['name'], L.local_MR['seq_step[7]']['addr'])
      L.LDP(L.local_T['block_timeout[7]']['name'], L.local_T['block_timeout[7]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+7*ERROR_INTERVAL+(3-1), error_yaml=error_yaml)
      #;action:moveL@3
      L.LDP(L.local_MR['seq_step[7]']['name'], L.local_MR['seq_step[7]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(335, 0, 70, 0, 0, -10.989, 100, 100, 100, 0, 0, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[7]']['name'], L.local_MR['seq_step[7]']['addr'])
      L.ANB(L.local_MR['seq_step[2007]']['name'], L.local_MR['seq_step[2007]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0)')
      L.LD(L.local_MR['seq_step[7]']['name'], L.local_MR['seq_step[7]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[7]']['addr'], 0)
      #;error:moveL@3
      L.LD(L.local_MR['seq_step[7]']['name'], L.local_MR['seq_step[7]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+7*ERROR_INTERVAL+(3-1)+1, message=f"moveL@3:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+7*ERROR_INTERVAL+(3-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+7*ERROR_INTERVAL+(3-1)+2, message='moveL@3:Target velocity is zero.')
          func.raise_error(no=801+7*ERROR_INTERVAL+(3-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+7*ERROR_INTERVAL+(3-1)+3, message='moveL@3:Target acceleration is zero.')
          func.raise_error(no=801+7*ERROR_INTERVAL+(3-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+7*ERROR_INTERVAL+(3-1)+4, message='moveL@3:Target deceleration is zero.')
          func.raise_error(no=801+7*ERROR_INTERVAL+(3-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+7*ERROR_INTERVAL+(3-1)+5, message='moveL@3:Servo is off.')
          func.raise_error(no=801+7*ERROR_INTERVAL+(3-1)+5, error_yaml=error_yaml)

      #;Process:moveL@4
      L.LD(L.local_MR['seq_step[2007]']['name'], L.local_MR['seq_step[2007]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2008]']['name'], L.local_MR['seq_step[2008]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[8]']['name'], L.local_MR['seq_step[8]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[8]']['name'], L.local_T['move_static_timer[8]']['addr'])
      L.ANPB(L.local_MR['seq_step[8]']['name'], L.local_MR['seq_step[8]']['addr'])
      L.OR(L.local_MR['seq_step[2008]']['name'], L.local_MR['seq_step[2008]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2008]']['name'], L.local_MR['seq_step[2008]']['addr'])
      #;Post-Process:moveL@4
      #;timeout:moveL@4
      L.LDP(L.local_MR['seq_step[8]']['name'], L.local_MR['seq_step[8]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+8*ERROR_INTERVAL+(4-1), message='moveL@4:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[8]']['name'], L.local_MR['seq_step[8]']['addr'])
      L.TMS(L.local_T['block_timeout[8]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[8]']['name'], L.local_MR['seq_step[8]']['addr'])
      L.LDP(L.local_T['block_timeout[8]']['name'], L.local_T['block_timeout[8]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+8*ERROR_INTERVAL+(4-1), error_yaml=error_yaml)
      #;action:moveL@4
      L.LDP(L.local_MR['seq_step[8]']['name'], L.local_MR['seq_step[8]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(290, -232, 70, 0, 0, -7.893, 100, 100, 100, 0.1, 0, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[8]']['name'], L.local_MR['seq_step[8]']['addr'])
      L.ANB(L.local_MR['seq_step[2008]']['name'], L.local_MR['seq_step[2008]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0.1)')
      L.LD(L.local_MR['seq_step[8]']['name'], L.local_MR['seq_step[8]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[8]']['addr'], 0)
      #;error:moveL@4
      L.LD(L.local_MR['seq_step[8]']['name'], L.local_MR['seq_step[8]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+8*ERROR_INTERVAL+(4-1)+1, message=f"moveL@4:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+8*ERROR_INTERVAL+(4-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+8*ERROR_INTERVAL+(4-1)+2, message='moveL@4:Target velocity is zero.')
          func.raise_error(no=801+8*ERROR_INTERVAL+(4-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+8*ERROR_INTERVAL+(4-1)+3, message='moveL@4:Target acceleration is zero.')
          func.raise_error(no=801+8*ERROR_INTERVAL+(4-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+8*ERROR_INTERVAL+(4-1)+4, message='moveL@4:Target deceleration is zero.')
          func.raise_error(no=801+8*ERROR_INTERVAL+(4-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+8*ERROR_INTERVAL+(4-1)+5, message='moveL@4:Servo is off.')
          func.raise_error(no=801+8*ERROR_INTERVAL+(4-1)+5, error_yaml=error_yaml)

      #;Process:moveL@5
      L.LD(L.local_MR['seq_step[2008]']['name'], L.local_MR['seq_step[2008]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2009]']['name'], L.local_MR['seq_step[2009]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[9]']['name'], L.local_MR['seq_step[9]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[9]']['name'], L.local_T['move_static_timer[9]']['addr'])
      L.ANPB(L.local_MR['seq_step[9]']['name'], L.local_MR['seq_step[9]']['addr'])
      L.OR(L.local_MR['seq_step[2009]']['name'], L.local_MR['seq_step[2009]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2009]']['name'], L.local_MR['seq_step[2009]']['addr'])
      #;Post-Process:moveL@5
      #;timeout:moveL@5
      L.LDP(L.local_MR['seq_step[9]']['name'], L.local_MR['seq_step[9]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+9*ERROR_INTERVAL+(5-1), message='moveL@5:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[9]']['name'], L.local_MR['seq_step[9]']['addr'])
      L.TMS(L.local_T['block_timeout[9]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[9]']['name'], L.local_MR['seq_step[9]']['addr'])
      L.LDP(L.local_T['block_timeout[9]']['name'], L.local_T['block_timeout[9]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+9*ERROR_INTERVAL+(5-1), error_yaml=error_yaml)
      #;action:moveL@5
      L.LDP(L.local_MR['seq_step[9]']['name'], L.local_MR['seq_step[9]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(290, -232, 43, 0, 0, -7.893, 100, 100, 100, 0.1, 5000, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[9]']['name'], L.local_MR['seq_step[9]']['addr'])
      L.ANB(L.local_MR['seq_step[2009]']['name'], L.local_MR['seq_step[2009]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0.1)')
      L.LD(L.local_MR['seq_step[9]']['name'], L.local_MR['seq_step[9]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[9]']['addr'], 5000)
      #;error:moveL@5
      L.LD(L.local_MR['seq_step[9]']['name'], L.local_MR['seq_step[9]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+9*ERROR_INTERVAL+(5-1)+1, message=f"moveL@5:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+9*ERROR_INTERVAL+(5-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+9*ERROR_INTERVAL+(5-1)+2, message='moveL@5:Target velocity is zero.')
          func.raise_error(no=801+9*ERROR_INTERVAL+(5-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+9*ERROR_INTERVAL+(5-1)+3, message='moveL@5:Target acceleration is zero.')
          func.raise_error(no=801+9*ERROR_INTERVAL+(5-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+9*ERROR_INTERVAL+(5-1)+4, message='moveL@5:Target deceleration is zero.')
          func.raise_error(no=801+9*ERROR_INTERVAL+(5-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+9*ERROR_INTERVAL+(5-1)+5, message='moveL@5:Servo is off.')
          func.raise_error(no=801+9*ERROR_INTERVAL+(5-1)+5, error_yaml=error_yaml)

      #;Process:set_output@2
      L.LD(L.local_MR['seq_step[2009]']['name'], L.local_MR['seq_step[2009]']['addr'])
      L.MPS()
      L.ANB(L.local_MR['seq_step[2010]']['name'], L.local_MR['seq_step[2010]']['addr'])
      L.OUT(L.local_MR['seq_step[10]']['name'], L.local_MR['seq_step[10]']['addr'])
      L.MPP()
      L.LDPB(L.local_MR['seq_step[10]']['name'], L.local_MR['seq_step[10]']['addr'])
      L.OR(L.local_MR['seq_step[2010]']['name'], L.local_MR['seq_step[2010]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2010]']['name'], L.local_MR['seq_step[2010]']['addr'])
      #;Post-Process:set_output@2
      #;timeout:set_output@2
      L.LDP(L.local_MR['seq_step[10]']['name'], L.local_MR['seq_step[10]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+10*ERROR_INTERVAL+(2-1), message='set_output@2:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[10]']['name'], L.local_MR['seq_step[10]']['addr'])
      L.TMS(L.local_T['block_timeout[10]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[10]']['name'], L.local_MR['seq_step[10]']['addr'])
      L.LDP(L.local_T['block_timeout[10]']['name'], L.local_T['block_timeout[10]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+10*ERROR_INTERVAL+(2-1), error_yaml=error_yaml)
      L.LDP(L.local_MR['seq_step[10]']['name'], L.local_MR['seq_step[10]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command('setOutputOFF(1)')

      #;Process:moveL@6
      L.LD(L.local_MR['seq_step[2010]']['name'], L.local_MR['seq_step[2010]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2011]']['name'], L.local_MR['seq_step[2011]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[11]']['name'], L.local_MR['seq_step[11]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[11]']['name'], L.local_T['move_static_timer[11]']['addr'])
      L.ANPB(L.local_MR['seq_step[11]']['name'], L.local_MR['seq_step[11]']['addr'])
      L.OR(L.local_MR['seq_step[2011]']['name'], L.local_MR['seq_step[2011]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2011]']['name'], L.local_MR['seq_step[2011]']['addr'])
      #;Post-Process:moveL@6
      #;timeout:moveL@6
      L.LDP(L.local_MR['seq_step[11]']['name'], L.local_MR['seq_step[11]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+11*ERROR_INTERVAL+(6-1), message='moveL@6:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[11]']['name'], L.local_MR['seq_step[11]']['addr'])
      L.TMS(L.local_T['block_timeout[11]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[11]']['name'], L.local_MR['seq_step[11]']['addr'])
      L.LDP(L.local_T['block_timeout[11]']['name'], L.local_T['block_timeout[11]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+11*ERROR_INTERVAL+(6-1), error_yaml=error_yaml)
      #;action:moveL@6
      L.LDP(L.local_MR['seq_step[11]']['name'], L.local_MR['seq_step[11]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(290, -232, 70, 0, 0, -7.893, 100, 100, 100, 0.1, 0, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[11]']['name'], L.local_MR['seq_step[11]']['addr'])
      L.ANB(L.local_MR['seq_step[2011]']['name'], L.local_MR['seq_step[2011]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0.1)')
      L.LD(L.local_MR['seq_step[11]']['name'], L.local_MR['seq_step[11]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[11]']['addr'], 0)
      #;error:moveL@6
      L.LD(L.local_MR['seq_step[11]']['name'], L.local_MR['seq_step[11]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+11*ERROR_INTERVAL+(6-1)+1, message=f"moveL@6:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+11*ERROR_INTERVAL+(6-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+11*ERROR_INTERVAL+(6-1)+2, message='moveL@6:Target velocity is zero.')
          func.raise_error(no=801+11*ERROR_INTERVAL+(6-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+11*ERROR_INTERVAL+(6-1)+3, message='moveL@6:Target acceleration is zero.')
          func.raise_error(no=801+11*ERROR_INTERVAL+(6-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+11*ERROR_INTERVAL+(6-1)+4, message='moveL@6:Target deceleration is zero.')
          func.raise_error(no=801+11*ERROR_INTERVAL+(6-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+11*ERROR_INTERVAL+(6-1)+5, message='moveL@6:Servo is off.')
          func.raise_error(no=801+11*ERROR_INTERVAL+(6-1)+5, error_yaml=error_yaml)

      #;Process:moveL@7
      L.LD(L.local_MR['seq_step[2011]']['name'], L.local_MR['seq_step[2011]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2012]']['name'], L.local_MR['seq_step[2012]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[12]']['name'], L.local_MR['seq_step[12]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[12]']['name'], L.local_T['move_static_timer[12]']['addr'])
      L.ANPB(L.local_MR['seq_step[12]']['name'], L.local_MR['seq_step[12]']['addr'])
      L.OR(L.local_MR['seq_step[2012]']['name'], L.local_MR['seq_step[2012]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2012]']['name'], L.local_MR['seq_step[2012]']['addr'])
      #;Post-Process:moveL@7
      #;timeout:moveL@7
      L.LDP(L.local_MR['seq_step[12]']['name'], L.local_MR['seq_step[12]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+12*ERROR_INTERVAL+(7-1), message='moveL@7:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[12]']['name'], L.local_MR['seq_step[12]']['addr'])
      L.TMS(L.local_T['block_timeout[12]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[12]']['name'], L.local_MR['seq_step[12]']['addr'])
      L.LDP(L.local_T['block_timeout[12]']['name'], L.local_T['block_timeout[12]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+12*ERROR_INTERVAL+(7-1), error_yaml=error_yaml)
      #;action:moveL@7
      L.LDP(L.local_MR['seq_step[12]']['name'], L.local_MR['seq_step[12]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(290, -120, 70, 0, 0, -7.893, 100, 100, 100, 0.1, 0, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[12]']['name'], L.local_MR['seq_step[12]']['addr'])
      L.ANB(L.local_MR['seq_step[2012]']['name'], L.local_MR['seq_step[2012]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0.1)')
      L.LD(L.local_MR['seq_step[12]']['name'], L.local_MR['seq_step[12]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[12]']['addr'], 0)
      #;error:moveL@7
      L.LD(L.local_MR['seq_step[12]']['name'], L.local_MR['seq_step[12]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+12*ERROR_INTERVAL+(7-1)+1, message=f"moveL@7:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+12*ERROR_INTERVAL+(7-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+12*ERROR_INTERVAL+(7-1)+2, message='moveL@7:Target velocity is zero.')
          func.raise_error(no=801+12*ERROR_INTERVAL+(7-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+12*ERROR_INTERVAL+(7-1)+3, message='moveL@7:Target acceleration is zero.')
          func.raise_error(no=801+12*ERROR_INTERVAL+(7-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+12*ERROR_INTERVAL+(7-1)+4, message='moveL@7:Target deceleration is zero.')
          func.raise_error(no=801+12*ERROR_INTERVAL+(7-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+12*ERROR_INTERVAL+(7-1)+5, message='moveL@7:Servo is off.')
          func.raise_error(no=801+12*ERROR_INTERVAL+(7-1)+5, error_yaml=error_yaml)

      #;Process:set_output_during@1
      L.LD(L.local_MR['seq_step[2012]']['name'], L.local_MR['seq_step[2012]']['addr'])
      L.MPS()
      L.ANB(L.local_MR['seq_step[2013]']['name'], L.local_MR['seq_step[2013]']['addr'])
      L.OUT(L.local_MR['seq_step[13]']['name'], L.local_MR['seq_step[13]']['addr'])
      L.MPP()
      L.LD(L.local_T['block_timer1[13]']['name'], L.local_T['block_timer1[13]']['addr'])
      L.OR(L.local_MR['seq_step[2013]']['name'], L.local_MR['seq_step[2013]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2013]']['name'], L.local_MR['seq_step[2013]']['addr'])
      #;Post-Process:set_output_during@1
      #;timeout:set_output_during@1
      L.LDP(L.local_MR['seq_step[13]']['name'], L.local_MR['seq_step[13]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+13*ERROR_INTERVAL+(1-1), message='set_output_during@1:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[13]']['name'], L.local_MR['seq_step[13]']['addr'])
      L.TMS(L.local_T['block_timeout[13]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[13]']['name'], L.local_MR['seq_step[13]']['addr'])
      L.LDP(L.local_T['block_timeout[13]']['name'], L.local_T['block_timeout[13]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+13*ERROR_INTERVAL+(1-1), error_yaml=error_yaml)
      L.LDP(L.local_MR['seq_step[13]']['name'], L.local_MR['seq_step[13]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command('setOutputON(2)')
      L.LD(L.local_MR['seq_step[13]']['name'], L.local_MR['seq_step[13]']['addr'])
      L.TMS(L.local_T['block_timer1[13]']['addr'], wait_msec=number_param_yaml['D485']['value'])
      L.LDP(L.local_MR['seq_step[2013]']['name'], L.local_MR['seq_step[2013]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command('setOutputOFF(2)')

      #;Process:wait_input@1
      L.LD(L.local_MR['seq_step[2013]']['name'], L.local_MR['seq_step[2013]']['addr'])
      L.MPS()
      L.ANB(L.local_MR['seq_step[2014]']['name'], L.local_MR['seq_step[2014]']['addr'])
      L.OUT(L.local_MR['seq_step[14]']['name'], L.local_MR['seq_step[14]']['addr'])
      L.MPP()
      L.LD(True if robot_status['input_signal'][0] else False)
      L.ANPB(L.local_MR['seq_step[14]']['name'], L.local_MR['seq_step[14]']['addr'])
      L.OR(L.local_MR['seq_step[2014]']['name'], L.local_MR['seq_step[2014]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2014]']['name'], L.local_MR['seq_step[2014]']['addr'])
      #;timeout:wait_input@1
      L.LDP(L.local_MR['seq_step[14]']['name'], L.local_MR['seq_step[14]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+14*ERROR_INTERVAL+(1-1), message='wait_input@1:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[14]']['name'], L.local_MR['seq_step[14]']['addr'])
      L.TMS(L.local_T['block_timeout[14]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[14]']['name'], L.local_MR['seq_step[14]']['addr'])
      L.LDP(L.local_T['block_timeout[14]']['name'], L.local_T['block_timeout[14]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+14*ERROR_INTERVAL+(1-1), error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[14]']['name'], L.local_MR['seq_step[14]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command('getInput(1)')

      #;Process:moveL@8
      L.LD(L.local_MR['seq_step[2014]']['name'], L.local_MR['seq_step[2014]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2015]']['name'], L.local_MR['seq_step[2015]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[15]']['name'], L.local_MR['seq_step[15]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[15]']['name'], L.local_T['move_static_timer[15]']['addr'])
      L.ANPB(L.local_MR['seq_step[15]']['name'], L.local_MR['seq_step[15]']['addr'])
      L.OR(L.local_MR['seq_step[2015]']['name'], L.local_MR['seq_step[2015]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2015]']['name'], L.local_MR['seq_step[2015]']['addr'])
      #;Post-Process:moveL@8
      #;timeout:moveL@8
      L.LDP(L.local_MR['seq_step[15]']['name'], L.local_MR['seq_step[15]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+15*ERROR_INTERVAL+(8-1), message='moveL@8:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[15]']['name'], L.local_MR['seq_step[15]']['addr'])
      L.TMS(L.local_T['block_timeout[15]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[15]']['name'], L.local_MR['seq_step[15]']['addr'])
      L.LDP(L.local_T['block_timeout[15]']['name'], L.local_T['block_timeout[15]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+15*ERROR_INTERVAL+(8-1), error_yaml=error_yaml)
      #;action:moveL@8
      L.LDP(L.local_MR['seq_step[15]']['name'], L.local_MR['seq_step[15]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(290, -120, 43, 0, 0, -7.893, 100, 100, 100, 0.1, 0, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[15]']['name'], L.local_MR['seq_step[15]']['addr'])
      L.ANB(L.local_MR['seq_step[2015]']['name'], L.local_MR['seq_step[2015]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0.1)')
      L.LD(L.local_MR['seq_step[15]']['name'], L.local_MR['seq_step[15]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[15]']['addr'], 0)
      #;error:moveL@8
      L.LD(L.local_MR['seq_step[15]']['name'], L.local_MR['seq_step[15]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+15*ERROR_INTERVAL+(8-1)+1, message=f"moveL@8:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+15*ERROR_INTERVAL+(8-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+15*ERROR_INTERVAL+(8-1)+2, message='moveL@8:Target velocity is zero.')
          func.raise_error(no=801+15*ERROR_INTERVAL+(8-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+15*ERROR_INTERVAL+(8-1)+3, message='moveL@8:Target acceleration is zero.')
          func.raise_error(no=801+15*ERROR_INTERVAL+(8-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+15*ERROR_INTERVAL+(8-1)+4, message='moveL@8:Target deceleration is zero.')
          func.raise_error(no=801+15*ERROR_INTERVAL+(8-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+15*ERROR_INTERVAL+(8-1)+5, message='moveL@8:Servo is off.')
          func.raise_error(no=801+15*ERROR_INTERVAL+(8-1)+5, error_yaml=error_yaml)

      #;Process:set_output@3
      L.LD(L.local_MR['seq_step[2015]']['name'], L.local_MR['seq_step[2015]']['addr'])
      L.MPS()
      L.ANB(L.local_MR['seq_step[2016]']['name'], L.local_MR['seq_step[2016]']['addr'])
      L.OUT(L.local_MR['seq_step[16]']['name'], L.local_MR['seq_step[16]']['addr'])
      L.MPP()
      L.LDPB(L.local_MR['seq_step[16]']['name'], L.local_MR['seq_step[16]']['addr'])
      L.OR(L.local_MR['seq_step[2016]']['name'], L.local_MR['seq_step[2016]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2016]']['name'], L.local_MR['seq_step[2016]']['addr'])
      #;Post-Process:set_output@3
      #;timeout:set_output@3
      L.LDP(L.local_MR['seq_step[16]']['name'], L.local_MR['seq_step[16]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+16*ERROR_INTERVAL+(3-1), message='set_output@3:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[16]']['name'], L.local_MR['seq_step[16]']['addr'])
      L.TMS(L.local_T['block_timeout[16]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[16]']['name'], L.local_MR['seq_step[16]']['addr'])
      L.LDP(L.local_T['block_timeout[16]']['name'], L.local_T['block_timeout[16]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+16*ERROR_INTERVAL+(3-1), error_yaml=error_yaml)
      L.LDP(L.local_MR['seq_step[16]']['name'], L.local_MR['seq_step[16]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command('setOutputON(1)')

      #;Process:moveL@9
      L.LD(L.local_MR['seq_step[2016]']['name'], L.local_MR['seq_step[2016]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2017]']['name'], L.local_MR['seq_step[2017]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[17]']['name'], L.local_MR['seq_step[17]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[17]']['name'], L.local_T['move_static_timer[17]']['addr'])
      L.ANPB(L.local_MR['seq_step[17]']['name'], L.local_MR['seq_step[17]']['addr'])
      L.OR(L.local_MR['seq_step[2017]']['name'], L.local_MR['seq_step[2017]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2017]']['name'], L.local_MR['seq_step[2017]']['addr'])
      #;Post-Process:moveL@9
      #;timeout:moveL@9
      L.LDP(L.local_MR['seq_step[17]']['name'], L.local_MR['seq_step[17]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+17*ERROR_INTERVAL+(9-1), message='moveL@9:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[17]']['name'], L.local_MR['seq_step[17]']['addr'])
      L.TMS(L.local_T['block_timeout[17]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[17]']['name'], L.local_MR['seq_step[17]']['addr'])
      L.LDP(L.local_T['block_timeout[17]']['name'], L.local_T['block_timeout[17]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+17*ERROR_INTERVAL+(9-1), error_yaml=error_yaml)
      #;action:moveL@9
      L.LDP(L.local_MR['seq_step[17]']['name'], L.local_MR['seq_step[17]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(290, -120, 70, 0, 0, -7.893, 100, 100, 100, 0.1, 0, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[17]']['name'], L.local_MR['seq_step[17]']['addr'])
      L.ANB(L.local_MR['seq_step[2017]']['name'], L.local_MR['seq_step[2017]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0.1)')
      L.LD(L.local_MR['seq_step[17]']['name'], L.local_MR['seq_step[17]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[17]']['addr'], 0)
      #;error:moveL@9
      L.LD(L.local_MR['seq_step[17]']['name'], L.local_MR['seq_step[17]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+17*ERROR_INTERVAL+(9-1)+1, message=f"moveL@9:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+17*ERROR_INTERVAL+(9-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+17*ERROR_INTERVAL+(9-1)+2, message='moveL@9:Target velocity is zero.')
          func.raise_error(no=801+17*ERROR_INTERVAL+(9-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+17*ERROR_INTERVAL+(9-1)+3, message='moveL@9:Target acceleration is zero.')
          func.raise_error(no=801+17*ERROR_INTERVAL+(9-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+17*ERROR_INTERVAL+(9-1)+4, message='moveL@9:Target deceleration is zero.')
          func.raise_error(no=801+17*ERROR_INTERVAL+(9-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+17*ERROR_INTERVAL+(9-1)+5, message='moveL@9:Servo is off.')
          func.raise_error(no=801+17*ERROR_INTERVAL+(9-1)+5, error_yaml=error_yaml)

      #;Process:moveL@10
      L.LD(L.local_MR['seq_step[2017]']['name'], L.local_MR['seq_step[2017]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2018]']['name'], L.local_MR['seq_step[2018]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[18]']['name'], L.local_MR['seq_step[18]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[18]']['name'], L.local_T['move_static_timer[18]']['addr'])
      L.ANPB(L.local_MR['seq_step[18]']['name'], L.local_MR['seq_step[18]']['addr'])
      L.OR(L.local_MR['seq_step[2018]']['name'], L.local_MR['seq_step[2018]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2018]']['name'], L.local_MR['seq_step[2018]']['addr'])
      #;Post-Process:moveL@10
      #;timeout:moveL@10
      L.LDP(L.local_MR['seq_step[18]']['name'], L.local_MR['seq_step[18]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+18*ERROR_INTERVAL+(10-1), message='moveL@10:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[18]']['name'], L.local_MR['seq_step[18]']['addr'])
      L.TMS(L.local_T['block_timeout[18]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[18]']['name'], L.local_MR['seq_step[18]']['addr'])
      L.LDP(L.local_T['block_timeout[18]']['name'], L.local_T['block_timeout[18]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+18*ERROR_INTERVAL+(10-1), error_yaml=error_yaml)
      #;action:moveL@10
      L.LDP(L.local_MR['seq_step[18]']['name'], L.local_MR['seq_step[18]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        offset_x = offset_x + pallet_offset[1-1]['x']
        offset_y = offset_y + pallet_offset[1-1]['y']
        offset_z = offset_z + pallet_offset[1-1]['z']
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(218, 235, 70, 0, 0, -7.893, 100, 100, 100, 0.1, 0, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[18]']['name'], L.local_MR['seq_step[18]']['addr'])
      L.ANB(L.local_MR['seq_step[2018]']['name'], L.local_MR['seq_step[2018]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0.1)')
      L.LD(L.local_MR['seq_step[18]']['name'], L.local_MR['seq_step[18]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[18]']['addr'], 0)
      #;error:moveL@10
      L.LD(L.local_MR['seq_step[18]']['name'], L.local_MR['seq_step[18]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+18*ERROR_INTERVAL+(10-1)+1, message=f"moveL@10:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+18*ERROR_INTERVAL+(10-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+18*ERROR_INTERVAL+(10-1)+2, message='moveL@10:Target velocity is zero.')
          func.raise_error(no=801+18*ERROR_INTERVAL+(10-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+18*ERROR_INTERVAL+(10-1)+3, message='moveL@10:Target acceleration is zero.')
          func.raise_error(no=801+18*ERROR_INTERVAL+(10-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+18*ERROR_INTERVAL+(10-1)+4, message='moveL@10:Target deceleration is zero.')
          func.raise_error(no=801+18*ERROR_INTERVAL+(10-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+18*ERROR_INTERVAL+(10-1)+5, message='moveL@10:Servo is off.')
          func.raise_error(no=801+18*ERROR_INTERVAL+(10-1)+5, error_yaml=error_yaml)

      #;Process:moveL@11
      L.LD(L.local_MR['seq_step[2018]']['name'], L.local_MR['seq_step[2018]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2019]']['name'], L.local_MR['seq_step[2019]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[19]']['name'], L.local_MR['seq_step[19]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[19]']['name'], L.local_T['move_static_timer[19]']['addr'])
      L.ANPB(L.local_MR['seq_step[19]']['name'], L.local_MR['seq_step[19]']['addr'])
      L.OR(L.local_MR['seq_step[2019]']['name'], L.local_MR['seq_step[2019]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2019]']['name'], L.local_MR['seq_step[2019]']['addr'])
      #;Post-Process:moveL@11
      #;timeout:moveL@11
      L.LDP(L.local_MR['seq_step[19]']['name'], L.local_MR['seq_step[19]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+19*ERROR_INTERVAL+(11-1), message='moveL@11:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[19]']['name'], L.local_MR['seq_step[19]']['addr'])
      L.TMS(L.local_T['block_timeout[19]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[19]']['name'], L.local_MR['seq_step[19]']['addr'])
      L.LDP(L.local_T['block_timeout[19]']['name'], L.local_T['block_timeout[19]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+19*ERROR_INTERVAL+(11-1), error_yaml=error_yaml)
      #;action:moveL@11
      L.LDP(L.local_MR['seq_step[19]']['name'], L.local_MR['seq_step[19]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        offset_x = offset_x + pallet_offset[1-1]['x']
        offset_y = offset_y + pallet_offset[1-1]['y']
        offset_z = offset_z + pallet_offset[1-1]['z']
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(218, 235, 17.8, 0, 0, -7.893, 100, 100, 100, 0.1, 0, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[19]']['name'], L.local_MR['seq_step[19]']['addr'])
      L.ANB(L.local_MR['seq_step[2019]']['name'], L.local_MR['seq_step[2019]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0.1)')
      L.LD(L.local_MR['seq_step[19]']['name'], L.local_MR['seq_step[19]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[19]']['addr'], 0)
      #;error:moveL@11
      L.LD(L.local_MR['seq_step[19]']['name'], L.local_MR['seq_step[19]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+19*ERROR_INTERVAL+(11-1)+1, message=f"moveL@11:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+19*ERROR_INTERVAL+(11-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+19*ERROR_INTERVAL+(11-1)+2, message='moveL@11:Target velocity is zero.')
          func.raise_error(no=801+19*ERROR_INTERVAL+(11-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+19*ERROR_INTERVAL+(11-1)+3, message='moveL@11:Target acceleration is zero.')
          func.raise_error(no=801+19*ERROR_INTERVAL+(11-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+19*ERROR_INTERVAL+(11-1)+4, message='moveL@11:Target deceleration is zero.')
          func.raise_error(no=801+19*ERROR_INTERVAL+(11-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+19*ERROR_INTERVAL+(11-1)+5, message='moveL@11:Servo is off.')
          func.raise_error(no=801+19*ERROR_INTERVAL+(11-1)+5, error_yaml=error_yaml)

      #;Process:set_output@4
      L.LD(L.local_MR['seq_step[2019]']['name'], L.local_MR['seq_step[2019]']['addr'])
      L.MPS()
      L.ANB(L.local_MR['seq_step[2020]']['name'], L.local_MR['seq_step[2020]']['addr'])
      L.OUT(L.local_MR['seq_step[20]']['name'], L.local_MR['seq_step[20]']['addr'])
      L.MPP()
      L.LDPB(L.local_MR['seq_step[20]']['name'], L.local_MR['seq_step[20]']['addr'])
      L.OR(L.local_MR['seq_step[2020]']['name'], L.local_MR['seq_step[2020]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2020]']['name'], L.local_MR['seq_step[2020]']['addr'])
      #;Post-Process:set_output@4
      #;timeout:set_output@4
      L.LDP(L.local_MR['seq_step[20]']['name'], L.local_MR['seq_step[20]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+20*ERROR_INTERVAL+(4-1), message='set_output@4:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[20]']['name'], L.local_MR['seq_step[20]']['addr'])
      L.TMS(L.local_T['block_timeout[20]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[20]']['name'], L.local_MR['seq_step[20]']['addr'])
      L.LDP(L.local_T['block_timeout[20]']['name'], L.local_T['block_timeout[20]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+20*ERROR_INTERVAL+(4-1), error_yaml=error_yaml)
      L.LDP(L.local_MR['seq_step[20]']['name'], L.local_MR['seq_step[20]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command('setOutputOFF(1)')

      #;Process:moveL@12
      L.LD(L.local_MR['seq_step[2020]']['name'], L.local_MR['seq_step[2020]']['addr'])
      L.MPS()
      L.LDB(MR, 4)
      L.ANB(L.local_MR['seq_step[2021]']['name'], L.local_MR['seq_step[2021]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[21]']['name'], L.local_MR['seq_step[21]']['addr'])
      L.MPP()
      L.LDB(MR, 4)
      L.AND(arrived)
      L.AND(L.local_T['move_static_timer[21]']['name'], L.local_T['move_static_timer[21]']['addr'])
      L.ANPB(L.local_MR['seq_step[21]']['name'], L.local_MR['seq_step[21]']['addr'])
      L.OR(L.local_MR['seq_step[2021]']['name'], L.local_MR['seq_step[2021]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2021]']['name'], L.local_MR['seq_step[2021]']['addr'])
      #;Post-Process:moveL@12
      #;timeout:moveL@12
      L.LDP(L.local_MR['seq_step[21]']['name'], L.local_MR['seq_step[21]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+21*ERROR_INTERVAL+(12-1), message='moveL@12:A timeout occurred.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[21]']['name'], L.local_MR['seq_step[21]']['addr'])
      L.TMS(L.local_T['block_timeout[21]']['addr'], TIMEOUT_MSEC)
      L.LD(L.local_MR['seq_step[21]']['name'], L.local_MR['seq_step[21]']['addr'])
      L.LDP(L.local_T['block_timeout[21]']['name'], L.local_T['block_timeout[21]']['addr'])
      if (L.aax & L.iix):
        func.raise_error(no=801+21*ERROR_INTERVAL+(12-1), error_yaml=error_yaml)
      #;action:moveL@12
      L.LDP(L.local_MR['seq_step[21]']['name'], L.local_MR['seq_step[21]']['addr'])
      if (L.aax & L.iix):
        offset_x = 0
        offset_y = 0
        offset_z = 0
        offset_rx = 0
        offset_ry = 0
        offset_rz = 0
        offset_x = offset_x + pallet_offset[1-1]['x']
        offset_y = offset_y + pallet_offset[1-1]['y']
        offset_z = offset_z + pallet_offset[1-1]['z']
        x, y, z, rx, ry, rz, vel, acc, dec, dist, stime = L.FB_setRobotParam(218, 235, 70, 0, 0, -7.893, 100, 100, 100, 0.1, 0, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, 100)
        RAC.send_command(f'moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})')
      L.LD(L.local_MR['seq_step[21]']['name'], L.local_MR['seq_step[21]']['addr'])
      L.ANB(L.local_MR['seq_step[2021]']['name'], L.local_MR['seq_step[2021]']['addr'])
      if (L.aax & L.iix):
        RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0.1)')
      L.LD(L.local_MR['seq_step[21]']['name'], L.local_MR['seq_step[21]']['addr'])
      L.AND(arrived)
      L.TMS(L.local_T['move_static_timer[21]']['addr'], 0)
      #;error:moveL@12
      L.LD(L.local_MR['seq_step[21]']['name'], L.local_MR['seq_step[21]']['addr'])
      if (L.aax & L.iix):
        if (error == True):
          func.register_error(no=801+21*ERROR_INTERVAL+(12-1)+1, message=f"moveL@12:Robot API error occurred: No.{error_id}")
          func.raise_error(no=801+21*ERROR_INTERVAL+(12-1)+1, error_yaml=error_yaml)
        if (vel == 0):
          func.register_error(no=801+21*ERROR_INTERVAL+(12-1)+2, message='moveL@12:Target velocity is zero.')
          func.raise_error(no=801+21*ERROR_INTERVAL+(12-1)+2, error_yaml=error_yaml)
        if (acc == 0):
          func.register_error(no=801+21*ERROR_INTERVAL+(12-1)+3, message='moveL@12:Target acceleration is zero.')
          func.raise_error(no=801+21*ERROR_INTERVAL+(12-1)+3, error_yaml=error_yaml)
        if (dec == 0):
          func.register_error(no=801+21*ERROR_INTERVAL+(12-1)+4, message='moveL@12:Target deceleration is zero.')
          func.raise_error(no=801+21*ERROR_INTERVAL+(12-1)+4, error_yaml=error_yaml)
        if (servo == False):
          func.register_error(no=801+21*ERROR_INTERVAL+(12-1)+5, message='moveL@12:Servo is off.')
          func.raise_error(no=801+21*ERROR_INTERVAL+(12-1)+5, error_yaml=error_yaml)

      #;Process:move_next_pallet@1
      L.LD(L.local_MR['seq_step[2021]']['name'], L.local_MR['seq_step[2021]']['addr'])
      L.MPS()
      L.ANB(L.local_MR['seq_step[2022]']['name'], L.local_MR['seq_step[2022]']['addr'])
      L.OUT(L.local_MR['seq_step[22]']['name'], L.local_MR['seq_step[22]']['addr'])
      L.MPP()
      L.LDPB(L.local_MR['seq_step[22]']['name'], L.local_MR['seq_step[22]']['addr'])
      L.OR(L.local_MR['seq_step[2022]']['name'], L.local_MR['seq_step[2022]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2022]']['name'], L.local_MR['seq_step[2022]']['addr'])
      #;Post-Process:move_next_pallet@1
      L.LDP(L.local_MR['seq_step[22]']['name'], L.local_MR['seq_step[22]']['addr'])
      if (L.aax & L.iix):
        MAX_row = pallet_settings[1-1]['row']
        MAX_col = pallet_settings[1-1]['col']
        dst_pocket = pallet_settings[1-1]['dst_pocket']
        if ((dst_pocket <= MAX_row * MAX_col) and (dst_pocket > 0)):
          number_param_yaml['D'+str(490+1-1)]['value'] = pallet_settings[1-1]['dst_pocket']
          pallet_settings[1-1]['dst_pocket'] = pallet_settings[1-1]['dst_pocket'] + 1
          pallet_offset[1-1] = func.getPalletOffset(pallet_settings, 1)

      #;Process:return@1
      L.LD(L.local_MR['seq_step[2022]']['name'], L.local_MR['seq_step[2022]']['addr'])
      L.MPS()
      L.ANB(L.local_MR['seq_step[2023]']['name'], L.local_MR['seq_step[2023]']['addr'])
      L.OUT(L.local_MR['seq_step[23]']['name'], L.local_MR['seq_step[23]']['addr'])
      L.MPP()
      L.LDPB(L.local_MR['seq_step[23]']['name'], L.local_MR['seq_step[23]']['addr'])
      L.OR(L.local_MR['seq_step[2023]']['name'], L.local_MR['seq_step[2023]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2023]']['name'], L.local_MR['seq_step[2023]']['addr'])


      #;Process:start_thread@1
      L.LD(L.local_R['start_program[0]']['name'], L.local_R['start_program[0]']['addr'])
      L.ANB(R, 5)
      L.MPS()
      L.ANB(L.local_MR['seq_step[2024]']['name'], L.local_MR['seq_step[2024]']['addr'])
      L.OUT(L.local_MR['seq_step[24]']['name'], L.local_MR['seq_step[24]']['addr'])
      L.MPP()
      L.LD(True)
      L.OR(L.local_MR['seq_step[2024]']['name'], L.local_MR['seq_step[2024]']['addr'])
      L.ANL()
      L.OUT(L.local_MR['seq_step[2024]']['name'], L.local_MR['seq_step[2024]']['addr'])

      #;Process:check_error@1
      L.LD(True if (number_param_yaml['D490']['value'] == 1) else False)
      L.OR(L.local_MR['seq_step[2026]']['name'], L.local_MR['seq_step[2026]']['addr'])
      L.AND(L.local_MR['seq_step[2024]']['name'], L.local_MR['seq_step[2024]']['addr'])
      L.OUT(L.local_MR['seq_step[2026]']['name'], L.local_MR['seq_step[2026]']['addr'])
      L.LDP(L.local_MR['seq_step[2026]']['name'], L.local_MR['seq_step[2026]']['addr'])
      if (L.aax & L.iix):
        func.register_error(no=801+1-1, message='Pallet No.1 is empty.', error_yaml=error_yaml)
      L.LD(L.local_MR['seq_step[2026]']['name'], L.local_MR['seq_step[2026]']['addr'])
      if (L.aax & L.iix):
        try:
          func.raise_error(no=801+1-1, error_yaml=error_yaml)
        except ValueError as e:
          print(f"Error:check_error@1: {e}")
        else:
          pass

    except Exception as e:  
      func.cleanup()
      print(e)
      sys.exit(-1)

