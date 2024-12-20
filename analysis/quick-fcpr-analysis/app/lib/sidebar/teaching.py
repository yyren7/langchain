from lib.utility.constant import DM, EM, R, MR, LR, CR, T
from lib.utility.common_globals import L, RD, RAC
from lib.utility.constant import TEACH_FILE_PATH, NUMBER_PARAM_FILE_PATH, FLAG_PARAM_FILE_PATH, ERROR_FILE_PATH
# from lib.utility.globals import error_yaml, number_param_yaml, initial_number_param_yaml

import lib.utility.helper as helper


# YAMLファイルから位置を読み込む関数
def read_pos():
  teaching_yaml = helper.read_yaml(TEACH_FILE_PATH)
  current_page_no = L.EM_relay[2006]
  offset_point_no = (current_page_no-1)*10
  for point_no in range(1, 11):
      key = teaching_yaml[f'P{point_no+offset_point_no}']
      L.EM_relay[800+(point_no-1)*20:800+len(helper.name_to_ascii16(key['name'], 40))+(point_no-1)*20] = helper.name_to_ascii16(key['name'], 40)
      L.EM_relay[2500+(point_no-1)*2:2500+len(helper.int32_to_uint16s(int(key['x_pos']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['x_pos']*1000))
      L.EM_relay[2550+(point_no-1)*2:2550+len(helper.int32_to_uint16s(int(key['y_pos']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['y_pos']*1000))
      L.EM_relay[2600+(point_no-1)*2:2600+len(helper.int32_to_uint16s(int(key['z_pos']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['z_pos']*1000))
      L.EM_relay[2650+(point_no-1)*2:2650+len(helper.int32_to_uint16s(int(key['rx_pos']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['rx_pos']*1000))
      L.EM_relay[2700+(point_no-1)*2:2700+len(helper.int32_to_uint16s(int(key['ry_pos']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['ry_pos']*1000))
      L.EM_relay[2750+(point_no-1)*2:2750+len(helper.int32_to_uint16s(int(key['rz_pos']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['rz_pos']*1000))

# YAMLファイルから速度を読み込む関数
def read_vel():
  teaching_yaml = helper.read_yaml(TEACH_FILE_PATH)
  current_page_no = L.EM_relay[2006]
  offset_point_no = (current_page_no-1)*10
  for point_no in range(1, 11):
      key = teaching_yaml[f'P{point_no+offset_point_no}']
      L.EM_relay[800+(point_no-1)*20:800+len(helper.name_to_ascii16(key['name'], 40))+(point_no-1)*20] = helper.name_to_ascii16(key['name'], 40)
      L.EM_relay[2500+(point_no-1)*2:2500+len(helper.int32_to_uint16s(int(key['vel']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['vel']*1000))
      L.EM_relay[2550+(point_no-1)*2:2550+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2600+(point_no-1)*2:2600+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2650+(point_no-1)*2:2650+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2700+(point_no-1)*2:2700+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2750+(point_no-1)*2:2750+2+(point_no-1)*2] = [0, 0]

# YAMLファイルから加速度を読み込む関数
def read_acc():
  teaching_yaml = helper.read_yaml(TEACH_FILE_PATH)
  current_page_no = L.EM_relay[2006]
  offset_point_no = (current_page_no-1)*10
  for point_no in range(1, 11):
      key = teaching_yaml[f'P{point_no+offset_point_no}']
      L.EM_relay[800+(point_no-1)*20:800+len(helper.name_to_ascii16(key['name'], 40))+(point_no-1)*20] = helper.name_to_ascii16(key['name'], 40)
      L.EM_relay[2500+(point_no-1)*2:2500+len(helper.int32_to_uint16s(int(key['acc']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['acc']*1000))
      L.EM_relay[2550+(point_no-1)*2:2550+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2600+(point_no-1)*2:2600+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2650+(point_no-1)*2:2650+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2700+(point_no-1)*2:2700+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2750+(point_no-1)*2:2750+2+(point_no-1)*2] = [0, 0]

# YAMLファイルから減速度を読み込む関数
def read_dec():
  teaching_yaml = helper.read_yaml(TEACH_FILE_PATH)
  current_page_no = L.EM_relay[2006]
  offset_point_no = (current_page_no-1)*10
  for point_no in range(1, 11):
      key = teaching_yaml[f'P{point_no+offset_point_no}']
      L.EM_relay[800+(point_no-1)*20:800+len(helper.name_to_ascii16(key['name'], 40))+(point_no-1)*20] = helper.name_to_ascii16(key['name'], 40)
      L.EM_relay[2500+(point_no-1)*2:2500+len(helper.int32_to_uint16s(int(key['dec']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['dec']*1000))
      L.EM_relay[2550+(point_no-1)*2:2550+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2600+(point_no-1)*2:2600+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2650+(point_no-1)*2:2650+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2700+(point_no-1)*2:2700+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2750+(point_no-1)*2:2750+2+(point_no-1)*2] = [0, 0]

# YAMLファイルから設定値を読み込む関数
def read_setting():
  teaching_yaml = helper.read_yaml(TEACH_FILE_PATH)
  current_page_no = L.EM_relay[2006]
  offset_point_no = (current_page_no-1)*10
  for point_no in range(1, 11):
      key = teaching_yaml[f'P{point_no+offset_point_no}']
      L.EM_relay[800+(point_no-1)*20:800+len(helper.name_to_ascii16(key['name'], 40))+(point_no-1)*20] = helper.name_to_ascii16(key['name'], 40)
      L.EM_relay[2500+(point_no-1)*2:2500+len(helper.int32_to_uint16s(int(key['dist']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['dist']*1000))
      L.EM_relay[2550+(point_no-1)*2:2550+len(helper.int32_to_uint16s(int(key['stime']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['stime']*1000))
      L.EM_relay[2600+(point_no-1)*2:2600+len(helper.int32_to_uint16s(int(key['tool']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['tool']*1000))
      L.EM_relay[2650+(point_no-1)*2:2650+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2700+(point_no-1)*2:2700+2+(point_no-1)*2] = [0, 0]
      L.EM_relay[2750+(point_no-1)*2:2750+2+(point_no-1)*2] = [0, 0]

# 表のタイトルを読み込む関数
def read_title_pos():
  L.EM_relay[1000 : 1000 + len(helper.name_to_ascii16('  X [mm]', 10))] = helper.name_to_ascii16('  X [mm]', 10)
  L.EM_relay[1010 : 1010 + len(helper.name_to_ascii16('  Y [mm]', 10))] = helper.name_to_ascii16('  Y [mm]', 10)
  L.EM_relay[1020 : 1020 + len(helper.name_to_ascii16('  Z [mm]', 10))] = helper.name_to_ascii16('  Z [mm]', 10)
  L.EM_relay[1030 : 1030 + len(helper.name_to_ascii16('  Rz [deg]', 10))] = helper.name_to_ascii16('  Rz [deg]', 10)
  L.EM_relay[1040 : 1040 + len(helper.name_to_ascii16('  Ry [deg]', 10))] = helper.name_to_ascii16('  Ry [deg]', 10)
  L.EM_relay[1050 : 1050 + len(helper.name_to_ascii16('  Rx [deg]', 10))] = helper.name_to_ascii16('  Rx [deg]', 10)

# Jog動作
def move_jog():
  # Jog速度
  vel = L.DM_relay[3805]
  # +X軸動作
  L.LDP(R, 1000)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveJog(x', '+', {vel})")
    # RB.('x', '+', vel)
  L.LDF(R, 1000)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"stopJog()")
  # -X軸動作
  L.LDP(R, 1001)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveJog(x', '-', {vel})")
    # RB.moveJog('x', '-', vel)
  L.LDF(R, 1001)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"stopJog()")
  # +Y軸動作
  L.LDP(R, 1002)
  L.AND(R, 5800)
  if (L.aax & L.iix): 
    RAC.send_command(f"moveJog(y', '+', {vel})")
  L.LDF(R, 1002)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"stopJog()")
  # -Y軸動作
  L.LDP(R, 1003)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveJog(y', '-', {vel})")
  L.LDF(R, 1003)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"stopJog()")
  # +Z軸動作
  L.LDP(R, 1004)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveJog(z', '+', {vel})")
  L.LDF(R, 1004)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"stopJog()")
  # -Z軸動作
  L.LDP(R, 1005)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveJog(z', '-', {vel})")
  L.LDF(R, 1005)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"stopJog()")
  # +R軸動作
  L.LDP(R, 1006)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveJog(rz', '+', {vel})")
  L.LDF(R, 1006)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"stopJog()")
  # -R軸動作
  L.LDP(R, 1007)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveJog(rz', '-', {vel})")
  L.LDF(R, 1007)
  L.AND(R, 5800)
  if (L.aax & L.iix):  
    RAC.send_command(f"stopJog()")

# Inching動作
def move_inching(robot_status):
  # 目標値設定
  inch_width = helper.uint16s_to_int32(L.EM_relay[3000], L.EM_relay[3001]) / 1000
  x = robot_status['current_pos'][0]
  y = robot_status['current_pos'][1]
  z = robot_status['current_pos'][2]
  rx = robot_status['current_pos'][3]
  ry = robot_status['current_pos'][4]
  rz = robot_status['current_pos'][5]
  global target_pos
  vel = 10
  acc = 10
  dec = 10
  # シーケンス1
  L.LD(CR, 2002)
  L.ANB(L.local_R['inch_seq[3]']['name'], L.local_R['inch_seq[3]']['addr'])
  L.MPS()
  L.ANB(L.local_R['inch_seq[1]']['name'], L.local_R['inch_seq[1]']['addr'])
  L.OUT(L.local_R['inch_seq[0]']['name'], L.local_R['inch_seq[0]']['addr'])
  L.MPP()
  L.LDP(R, 1000)
  L.ORP(R, 1001)
  L.ORP(R, 1002)
  L.ORP(R, 1003)
  L.ORP(R, 1004)
  L.ORP(R, 1005)
  L.ORP(R, 1006)
  L.ORP(R, 1007)
  L.ORP(R, 1008)
  L.ORP(R, 1009)
  L.ORP(R, 1010)
  L.ORP(R, 1011)
  L.OR(L.local_R['inch_seq[1]']['name'], L.local_R['inch_seq[1]']['addr'])
  L.ANL()
  L.OUT(L.local_R['inch_seq[1]']['name'], L.local_R['inch_seq[1]']['addr'])
  # シーケンス2
  L.LD(L.local_R['inch_seq[1]']['name'], L.local_R['inch_seq[1]']['addr'])
  L.MPS()
  L.ANB(L.local_R['inch_seq[3]']['name'], L.local_R['inch_seq[3]']['addr'])
  L.OUT(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.MPP()
  L.LD(robot_status['arrived'])
  L.ANPB(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.OR(L.local_R['inch_seq[3]']['name'], L.local_R['inch_seq[3]']['addr'])
  L.ANL()
  L.OUT(L.local_R['inch_seq[3]']['name'], L.local_R['inch_seq[3]']['addr'])

  # print('R0', L.getRelay(L.local_R['inch_seq[1]']['name'], L.local_R['inch_seq[0]']['addr']))
  # print('R1', L.getRelay(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[1]']['addr']))
  # print('R2', L.getRelay(L.local_R['inch_seq[3]']['name'], L.local_R['inch_seq[2]']['addr']))
  # print('R3', L.getRelay(L.local_R['inch_seq[3]']['name'], L.local_R['inch_seq[3]']['addr']))

  # +X軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1000)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x + inch_width}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})")
    x = x + inch_width
    y = y
    z = z
    rx = rx
    ry = ry
    rz = rz
  # -X軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1001)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x - inch_width}, {y}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})")
    x = x - inch_width
    y = y
    z = z
    rx = rx
    ry = ry
    rz = rz
  # +Y軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1002)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x}, {y + inch_width}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})")
    x = x
    y = y + inch_width
    z = z
    rx = rx
    ry = ry
    rz = rz
  # -Y軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1003)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x}, {y - inch_width}, {z}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})")
    x = x
    y = y - inch_width
    z = z
    rx = rx
    ry = ry
    rz = rz
  # +Z軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1004)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x}, {y}, {z + inch_width}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})")
    x = x
    y = y
    z = z + inch_width
    rx = rx
    ry = ry
    rz = rz
  # -Z軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1005)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x}, {y}, {z - inch_width}, {rx}, {ry}, {rz}, {vel}, {acc}, {dec})")
    x = x
    y = y
    z = z - inch_width
    rx = rx
    ry = ry
    rz = rz
  # +Rx軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1006)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x}, {y}, {z}, {rx + inch_width}, {ry}, {rz}, {vel}, {acc}, {dec})")
    x = x
    y = y
    z = z
    rx = rx + inch_width
    ry = ry
    rz = rz
  # -Rx軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1007)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x}, {y}, {z}, {rx - inch_width}, {ry}, {rz}, {vel}, {acc}, {dec})")
    x = x
    y = y
    z = z
    rx = rx - inch_width
    ry = ry
    rz = rz
  # +Ry軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1008)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry + inch_width}, {rz}, {vel}, {acc}, {dec})")
    x = x
    y = y
    z = z
    rx = rx
    ry = ry + inch_width
    rz = rz
  # -Ry軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1009)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry - inch_width}, {rz}, {vel}, {acc}, {dec})")
    x = x
    y = y
    z = z
    rx = rx
    ry = ry - inch_width
    rz = rz
  # +Rz軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1010)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz + inch_width}, {vel}, {acc}, {dec})")
    x = x
    y = y
    z = z
    rx = rx
    ry = ry
    rz = rz + inch_width
  # -Rz軸動作
  L.LDP(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 1011)
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f"moveAbsoluteLine({x}, {y}, {z}, {rx}, {ry}, {rz - inch_width}, {vel}, {acc}, {dec})")
    x = x
    y = y
    z = z
    rx = rx
    ry = ry
    rz = rz - inch_width
  # 目標位置到達確認
  L.LD(L.local_R['inch_seq[2]']['name'], L.local_R['inch_seq[2]']['addr'])
  L.AND(R, 5801)
  if (L.aax & L.iix):  
    RAC.send_command(f'waitArrive([{x}, {y}, {z}, {rx}, {ry}, {rz}], 0.1)')

  # # -X軸動作
  # L.LDP(R, 1001)
  # L.AND(R, 5801)
  # if (L.aax & L.iix):  
  #   RB.moveAbsoluteLine(x - inch_width, y, z, rx, ry ,rz, vel, acc, dec)
  # # +Y軸動作
  # L.LDP(R, 1002)
  # L.AND(R, 5801)
  # if (L.aax & L.iix):  
  #   RB.moveAbsoluteLine(x, y + inch_width, z, rx, ry ,rz, vel, acc, dec)
  # # -Y軸動作
  # L.LDP(R, 1003)
  # L.AND(R, 5801)
  # if (L.aax & L.iix):  
  #   RB.moveAbsoluteLine(x, y - inch_width, z, rx, ry ,rz, vel, acc, dec)
  # # +Z軸動作
  # L.LDP(R, 1004)
  # L.AND(R, 5801)
  # if (L.aax & L.iix):  
  #   RB.moveAbsoluteLine(x, y, z + inch_width, rx, ry ,rz, vel, acc, dec)
  # # -Z軸動作
  # L.LDP(R, 1005)
  # L.AND(R, 5801)
  # if (L.aax & L.iix):  
  #   RB.moveAbsoluteLine(x, y, z - inch_width, rx, ry ,rz, vel, acc, dec)
  # # +R軸動作
  # L.LDP(R, 1010)
  # L.AND(R, 5801)
  # if (L.aax & L.iix):  
  #   RB.moveAbsoluteLine(x, y, z, rx, ry ,rz + inch_width, vel, acc, dec)
  # # -R軸動作
  # L.LDP(R, 1011)
  # L.AND(R, 5801)
  # if (L.aax & L.iix):  
  #   RB.moveAbsoluteLine(x, y, z, rx, ry ,rz - inch_width, vel, acc, dec)

# 表の書き込み
def write_teaching():
  L.LD(R, 1100)
  L.OUT(R, 6100)
  L.LDP(R, 1100)
  if (L.aax & L.iix):
    teaching_yaml = helper.read_yaml(TEACH_FILE_PATH)
    current_page_no = L.EM_relay[2006]
    offset_point_no = (current_page_no-1)*10
    for point_no in range(1, 11):
      key = teaching_yaml[f'P{point_no+offset_point_no}']
      # 位置
      L.LD(R, 5900)
      if (L.aax & L.iix):
        key['name'] = helper.ascii16_to_name(L.EM_relay[800+(point_no-1)*20:820+(point_no-1)*20])
        key['x_pos'] = helper.uint16s_to_int32(L.EM_relay[2500+(point_no-1)*2], L.EM_relay[2501+(point_no-1)*2]) / 1000.0
        key['y_pos'] = helper.uint16s_to_int32(L.EM_relay[2550+(point_no-1)*2], L.EM_relay[2551+(point_no-1)*2]) / 1000.0
        key['z_pos'] = helper.uint16s_to_int32(L.EM_relay[2600+(point_no-1)*2], L.EM_relay[2601+(point_no-1)*2]) / 1000.0
        key['rx_pos'] = helper.uint16s_to_int32(L.EM_relay[2650+(point_no-1)*2], L.EM_relay[2651+(point_no-1)*2]) / 1000.0
        key['ry_pos'] = helper.uint16s_to_int32(L.EM_relay[2700+(point_no-1)*2], L.EM_relay[2701+(point_no-1)*2]) / 1000.0
        key['rz_pos'] = helper.uint16s_to_int32(L.EM_relay[2750+(point_no-1)*2], L.EM_relay[2751+(point_no-1)*2]) / 1000.0
      # 速度
      L.LD(R, 5901)
      if (L.aax & L.iix):
        key['name'] = helper.ascii16_to_name(L.EM_relay[800+(point_no-1)*20:820+(point_no-1)*20])
        key['vel'] = helper.uint16s_to_int32(L.EM_relay[2500+(point_no-1)*2], L.EM_relay[2501+(point_no-1)*2]) / 1000.0
      # 加速度
      L.LD(R, 5902)
      if (L.aax & L.iix):
        key['name'] = helper.ascii16_to_name(L.EM_relay[800+(point_no-1)*20:820+(point_no-1)*20])
        key['acc'] = helper.uint16s_to_int32(L.EM_relay[2500+(point_no-1)*2], L.EM_relay[2501+(point_no-1)*2]) / 1000.0
      # 減速度
      L.LD(R, 5903)
      if (L.aax & L.iix):
        key['name'] = helper.ascii16_to_name(L.EM_relay[800+(point_no-1)*20:820+(point_no-1)*20])
        key['dec'] = helper.uint16s_to_int32(L.EM_relay[2500+(point_no-1)*2], L.EM_relay[2501+(point_no-1)*2]) / 1000.0
      # 設定値
      L.LD(R, 5904)
      if (L.aax & L.iix):
        key['name'] = helper.ascii16_to_name(L.EM_relay[800+(point_no-1)*20:820+(point_no-1)*20])
        key['dist'] = helper.uint16s_to_int32(L.EM_relay[2500+(point_no-1)*2], L.EM_relay[2501+(point_no-1)*2]) / 1000.0
        key['stime'] = helper.uint16s_to_int32(L.EM_relay[2550+(point_no-1)*2], L.EM_relay[2551+(point_no-1)*2]) / 1000.0
        key['tool'] = helper.uint16s_to_int32(L.EM_relay[2600+(point_no-1)*2], L.EM_relay[2601+(point_no-1)*2]) / 1000.0

    helper.write_yaml(TEACH_FILE_PATH, teaching_yaml)

# ティーチングデータのコピー
def copy_teaching():
  L.LD(R, 1102)
  L.OUT(R, 6102)
  L.LDP(R, 1102)
  if (L.aax & L.iix):
    L.DM_relay[3801] = L.EM_relay[2014]

# ティーチングデータのペースト
def paste_teaching():
  L.LD(R, 1103)
  L.OUT(R, 6103)
  L.LDP(R, 1103)
  if (L.aax & L.iix):
    src_point_no = L.DM_relay[3801]
    dst_point_no = L.EM_relay[2014] % 10 or 10 # 余りが0なら10にする
    teaching_yaml = helper.read_yaml(TEACH_FILE_PATH)
    key = teaching_yaml[f'P{src_point_no}']
    L.EM_relay[2500 + (dst_point_no-1)*2 : 2500 + len(helper.int32_to_uint16s(int(key['x_pos']*1000)))+(dst_point_no-1)*2] = helper.int32_to_uint16s(int(key['x_pos']*1000))
    L.EM_relay[2550 + (dst_point_no-1)*2 : 2550 + len(helper.int32_to_uint16s(int(key['y_pos']*1000)))+(dst_point_no-1)*2] = helper.int32_to_uint16s(int(key['y_pos']*1000))  
    L.EM_relay[2600 + (dst_point_no-1)*2 : 2600 + len(helper.int32_to_uint16s(int(key['z_pos']*1000)))+(dst_point_no-1)*2] = helper.int32_to_uint16s(int(key['z_pos']*1000))  
    L.EM_relay[2650 + (dst_point_no-1)*2 : 2650 + len(helper.int32_to_uint16s(int(key['rx_pos']*1000)))+(dst_point_no-1)*2] = helper.int32_to_uint16s(int(key['rx_pos']*1000))  
    L.EM_relay[2700 + (dst_point_no-1)*2 : 2700 + len(helper.int32_to_uint16s(int(key['ry_pos']*1000)))+(dst_point_no-1)*2] = helper.int32_to_uint16s(int(key['ry_pos']*1000))  
    L.EM_relay[2750 + (dst_point_no-1)*2 : 2750 + len(helper.int32_to_uint16s(int(key['rz_pos']*1000)))+(dst_point_no-1)*2] = helper.int32_to_uint16s(int(key['rz_pos']*1000))  

# ロボット情報取得
def get_robot_data(robot_status):
  # 現在位置更新
  L.EM_relay[3150:3150+len(helper.int32_to_uint16s(int(robot_status['current_pos'][0]*1000)))] = helper.int32_to_uint16s(int(robot_status['current_pos'][0]*1000))
  L.EM_relay[3152:3152+len(helper.int32_to_uint16s(int(robot_status['current_pos'][1]*1000)))] = helper.int32_to_uint16s(int(robot_status['current_pos'][1]*1000))
  L.EM_relay[3154:3154+len(helper.int32_to_uint16s(int(robot_status['current_pos'][2]*1000)))] = helper.int32_to_uint16s(int(robot_status['current_pos'][2]*1000))
  L.EM_relay[3156:3156+len(helper.int32_to_uint16s(int(robot_status['current_pos'][3]*1000)))] = helper.int32_to_uint16s(int(robot_status['current_pos'][3]*1000))
  L.EM_relay[3158:3158+len(helper.int32_to_uint16s(int(robot_status['current_pos'][4]*1000)))] = helper.int32_to_uint16s(int(robot_status['current_pos'][4]*1000))
  L.EM_relay[3160:3160+len(helper.int32_to_uint16s(int(robot_status['current_pos'][5]*1000)))] = helper.int32_to_uint16s(int(robot_status['current_pos'][5]*1000))


# サーボ操作
def handle_servo(robot_status):
  # サーボ状態フィードバック
  servo = robot_status['servo']
  L.LD(servo)
  L.OUT(R, 6203)
  # サーボON/OFF
  L.LDP(R, 1203)
  L.AND(servo)
  if (L.aax & L.iix):
    RAC.send_command('setServoOff()')
    # RB.setServoOff()
  L.LDP(R, 1203)
  L.ANB(servo)
  if (L.aax & L.iix):
    RAC.send_command('setServoOn()')
    # RB.setServoOn()

# Jog速度切り替え
def select_jog_speed():
  # 10mm/s
  btn_addr = 802
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 803)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, btn_addr)
  if (L.aax & L.iix):
    L.DM_relay[3805] = 10
  # 50mm/s
  btn_addr = 803
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 802)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, btn_addr)
  if (L.aax & L.iix):
    L.DM_relay[3805] = 50

# Jog/Inch切り替え
def select_move_mode():
  # Jog
  btn_addr = 800
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 801)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  # Inch
  btn_addr = 801
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 800)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)

# 現在位置の取り込み
def get_robot_pos():
  L.LD(R, 1101)
  L.OUT(R, 6101)
  L.LDP(R, 1101)
  if (L.aax & L.iix):
    point_no = L.EM_relay[2014] % 10 or 10 # 余りが0なら10にする
    # X
    L.EM_relay[2500+(point_no-1)*2] = L.EM_relay[3150]
    L.EM_relay[2501+(point_no-1)*2] = L.EM_relay[3151]
    # Y
    L.EM_relay[2550+(point_no-1)*2] = L.EM_relay[3152]
    L.EM_relay[2551+(point_no-1)*2] = L.EM_relay[3153]
    # Z
    L.EM_relay[2600+(point_no-1)*2] = L.EM_relay[3154]
    L.EM_relay[2601+(point_no-1)*2] = L.EM_relay[3155]
    # Rx
    L.EM_relay[2650+(point_no-1)*2] = L.EM_relay[3156]
    L.EM_relay[2651+(point_no-1)*2] = L.EM_relay[3157]
    # Ry
    L.EM_relay[2700+(point_no-1)*2] = L.EM_relay[3158]
    L.EM_relay[2701+(point_no-1)*2] = L.EM_relay[3159]
    # Rz
    L.EM_relay[2750+(point_no-1)*2] = L.EM_relay[3160]
    L.EM_relay[2751+(point_no-1)*2] = L.EM_relay[3161]

# 表の更新（位置）
def update_table_pos():
  L.LDP(R, 900)
  L.LD(R, 5900)
  L.ANPB(R, 901)
  L.ANPB(R, 902)
  L.ANPB(R, 903)
  L.ANPB(R, 904)
  L.ORL()
  L.OUT(R, 5900)
  L.LDP(R, 900)
  if (L.aax & L.iix):
    read_pos()
    read_title_pos()

# 表の更新（速度）
def update_table_vel():
  L.LDP(R, 901)
  L.LD(R, 5901)
  L.ANPB(R, 900)
  L.ANPB(R, 902)
  L.ANPB(R, 903)
  L.ANPB(R, 904)
  L.ORL()
  L.OUT(R, 5901)
  L.LDP(R, 901)
  if (L.aax & L.iix):
    read_vel()
    L.EM_relay[1000 : 1000 + len(helper.name_to_ascii16(' [mm/s]', 10))] = helper.name_to_ascii16(' [mm/s]', 10)
    L.EM_relay[1010 : 1010 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1020 : 1020 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1030 : 1030 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1040 : 1040 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1050 : 1050 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)

# 表の更新（加速度）
def update_table_acc():
  L.LDP(R, 902)
  L.LD(R, 5902)
  L.ANPB(R, 901)
  L.ANPB(R, 900)
  L.ANPB(R, 903)
  L.ANPB(R, 904)
  L.ORL()
  L.OUT(R, 5902)
  L.LDP(R, 902)
  if (L.aax & L.iix):
    read_acc()
    L.EM_relay[1000 : 1000 + len(helper.name_to_ascii16(' [G]', 10))] = helper.name_to_ascii16(' [G]', 10)
    L.EM_relay[1010 : 1010 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1020 : 1020 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1030 : 1030 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1040 : 1040 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1050 : 1050 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)

# 表の更新（加速度）
def update_table_dec():
  L.LDP(R, 903)
  L.LD(R, 5903)
  L.ANPB(R, 901)
  L.ANPB(R, 902)
  L.ANPB(R, 900)
  L.ANPB(R, 904)
  L.ORL()
  L.OUT(R, 5903)
  L.LDP(R, 903)
  if (L.aax & L.iix):
    read_dec()
    L.EM_relay[1000 : 1000 + len(helper.name_to_ascii16(' [G]', 10))] = helper.name_to_ascii16(' [G]', 10)
    L.EM_relay[1010 : 1010 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1020 : 1020 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1030 : 1030 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1040 : 1040 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1050 : 1050 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)

# 表の更新（設定値）
def update_table_setting():
  L.LDP(R, 904)
  L.LD(R, 5904)
  L.ANPB(R, 901)
  L.ANPB(R, 902)
  L.ANPB(R, 903)
  L.ANPB(R, 900)
  L.ORL()
  L.OUT(R, 5904)
  L.LDP(R, 904)
  if (L.aax & L.iix):
    read_setting()
    L.EM_relay[1000 : 1000 + len(helper.name_to_ascii16(' D [mm]', 10))] = helper.name_to_ascii16(' D[mm]', 10)
    L.EM_relay[1010 : 1010 + len(helper.name_to_ascii16(' T [millsec]', 10))] = helper.name_to_ascii16(' T[millsec]', 10)
    L.EM_relay[1020 : 1020 + len(helper.name_to_ascii16(' Tool', 10))] = helper.name_to_ascii16(' Tool', 10)
    L.EM_relay[1030 : 1030 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1040 : 1040 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)
    L.EM_relay[1050 : 1050 + len(helper.name_to_ascii16('', 10))] = helper.name_to_ascii16('', 10)

# 現在ページ番号更新
def update_page_no():
  # インクリメント
  L.LDP(R, 915)
  L.ANDLDL(L.EM_relay[2006], L.EM_relay[2005])
  L.OUT(L.local_R['teach_page[0]']['name'], L.local_R['teach_page[0]']['addr'])
  if (L.aax & L.iix):
    L.EM_relay[2006] = L.EM_relay[2006] + 1
    L.EM_relay[2014] = L.EM_relay[2014] + L.EM_relay[2005]
  # デクリメント
  L.LDP(R, 914)
  L.ANDLDG(L.EM_relay[2006], 1)
  L.OUT(L.local_R['teach_page[1]']['name'], L.local_R['teach_page[1]']['addr'])
  if (L.aax & L.iix):
    L.EM_relay[2006] = L.EM_relay[2006] - 1
    L.EM_relay[2014] = L.EM_relay[2014] - L.EM_relay[2005]
  # 表の更新
  L.LD(L.local_R['teach_page[0]']['name'], L.local_R['teach_page[0]']['addr'])
  L.OR(L.local_R['teach_page[1]']['name'], L.local_R['teach_page[1]']['addr'])
  if (L.aax & L.iix):
    # 位置
    L.LD(R, 5900)
    if (L.aax & L.iix):
      read_pos()
    # 速度
    L.LD(R, 5901)
    if (L.aax & L.iix):
      read_vel()
    # 加速度
    L.LD(R, 5902)
    if (L.aax & L.iix):
      read_acc()
    # 減速度
    L.LD(R, 5903)
    if (L.aax & L.iix):
      read_dec()
    # 設定値
    L.LD(R, 5904)
    if (L.aax & L.iix):
      read_setting()
  
# 選択中ポイント番号更新
def update_point_no():
  # P1
  btn_addr = 700
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 701)
  L.ANPB(R, 702)
  L.ANPB(R, 703)
  L.ANPB(R, 704)
  L.ANPB(R, 705)
  L.ANPB(R, 706)
  L.ANPB(R, 707)
  L.ANPB(R, 708)
  L.ANPB(R, 709)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2014] = btn_addr - 700 + 1 + (L.EM_relay[2006] - 1) * L.EM_relay[2005]
  # P2
  btn_addr = 701
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 700)
  L.ANPB(R, 702)
  L.ANPB(R, 703)
  L.ANPB(R, 704)
  L.ANPB(R, 705)
  L.ANPB(R, 706)
  L.ANPB(R, 707)
  L.ANPB(R, 708)
  L.ANPB(R, 709)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2014] = btn_addr - 700 + 1 + (L.EM_relay[2006] - 1) * L.EM_relay[2005]
  # P3
  btn_addr = 702
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 701)
  L.ANPB(R, 700)
  L.ANPB(R, 703)
  L.ANPB(R, 704)
  L.ANPB(R, 705)
  L.ANPB(R, 706)
  L.ANPB(R, 707)
  L.ANPB(R, 708)
  L.ANPB(R, 709)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2014] = btn_addr - 700 + 1 + (L.EM_relay[2006] - 1) * L.EM_relay[2005]
  # P4
  btn_addr = 703
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 701)
  L.ANPB(R, 702)
  L.ANPB(R, 700)
  L.ANPB(R, 704)
  L.ANPB(R, 705)
  L.ANPB(R, 706)
  L.ANPB(R, 707)
  L.ANPB(R, 708)
  L.ANPB(R, 709)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2014] = btn_addr - 700 + 1 + (L.EM_relay[2006] - 1) * L.EM_relay[2005]
  # P5
  btn_addr = 704
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 701)
  L.ANPB(R, 702)
  L.ANPB(R, 703)
  L.ANPB(R, 700)
  L.ANPB(R, 705)
  L.ANPB(R, 706)
  L.ANPB(R, 707)
  L.ANPB(R, 708)
  L.ANPB(R, 709)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2014] = btn_addr - 700 + 1 + (L.EM_relay[2006] - 1) * L.EM_relay[2005]
  # P6
  btn_addr = 705
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 701)
  L.ANPB(R, 702)
  L.ANPB(R, 703)
  L.ANPB(R, 704)
  L.ANPB(R, 700)
  L.ANPB(R, 706)
  L.ANPB(R, 707)
  L.ANPB(R, 708)
  L.ANPB(R, 709)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2014] = btn_addr - 700 + 1 + (L.EM_relay[2006] - 1) * L.EM_relay[2005]
  # P7
  btn_addr = 706
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 701)
  L.ANPB(R, 702)
  L.ANPB(R, 703)
  L.ANPB(R, 704)
  L.ANPB(R, 705)
  L.ANPB(R, 700)
  L.ANPB(R, 707)
  L.ANPB(R, 708)
  L.ANPB(R, 709)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2014] = btn_addr - 700 + 1 + (L.EM_relay[2006] - 1) * L.EM_relay[2005]
  # P8
  btn_addr = 707
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 701)
  L.ANPB(R, 702)
  L.ANPB(R, 703)
  L.ANPB(R, 704)
  L.ANPB(R, 705)
  L.ANPB(R, 706)
  L.ANPB(R, 700)
  L.ANPB(R, 708)
  L.ANPB(R, 709)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2014] = btn_addr - 700 + 1 + (L.EM_relay[2006] - 1) * L.EM_relay[2005]
  # P9
  btn_addr = 708
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 701)
  L.ANPB(R, 702)
  L.ANPB(R, 703)
  L.ANPB(R, 704)
  L.ANPB(R, 705)
  L.ANPB(R, 706)
  L.ANPB(R, 707)
  L.ANPB(R, 700)
  L.ANPB(R, 709)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2014] = btn_addr - 700 + 1 + (L.EM_relay[2006] - 1) * L.EM_relay[2005]
  # P10
  btn_addr = 709
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 701)
  L.ANPB(R, 702)
  L.ANPB(R, 703)
  L.ANPB(R, 704)
  L.ANPB(R, 705)
  L.ANPB(R, 706)
  L.ANPB(R, 707)
  L.ANPB(R, 708)
  L.ANPB(R, 700)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2014] = btn_addr - 700 + 1 + (L.EM_relay[2006] - 1) * L.EM_relay[2005]