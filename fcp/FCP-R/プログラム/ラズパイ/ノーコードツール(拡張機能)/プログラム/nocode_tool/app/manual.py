# -*- coding : UTF-8 -*-
import importlib
import sys, os, time
from lib.utility.globals import R, MR, LR, CR, T
from lib.utility.laddar_api import LaddarSeqAPI
from lib.utility.functions import getPalletOffset

import paho.mqtt.client as mqtt
import atexit, json, random

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
API_PATH = 'lib/robot/'
sys.path.append(current_dir + API_PATH)
L_web = LaddarSeqAPI(max_R_relay=100, max_MR_relay=100, max_EM_relay=100, max_LR_relay=100, max_T_relay=100, max_C_relay=100)
L = LaddarSeqAPI(max_R_relay=100, max_MR_relay=100, max_EM_relay=100, max_LR_relay=100, max_T_relay=100, max_C_relay=100)
pallet = {}
offset = {'x': 0.0, 'y': 0.0, 'z': 0.0}
current_pos = {'x': 0.0, 'y': 0.0, 'z': 0.0,'rx': 0.0, 'ry': 0.0, 'rz': 0.0}

# broker_address = 'broker.emqx.io'
broker_address = 'localhost'
port = 1883
sub_topic = 'control_robot'
pub_topic = 'feedback_robot'

def setPulse(relay_name, relay_no):
  L_web.setRelay(relay_name, relay_no)
  time.sleep(0.1)
  L_web.resetRelay(relay_name, relay_no)

def on_message(client, userdata, message):
  recv_msg = message.payload.decode()
  if('runRobot' == recv_msg): setPulse('R', 0)
  elif('pauseRobot' == recv_msg): setPulse('R', 1)
  elif('setServo' == recv_msg): setPulse('R', 1203)
  elif('selectJog' == recv_msg): setPulse('R', 800)
  elif('selectInching' == recv_msg): setPulse('R', 801)
  elif('runPlusX' == recv_msg): 
    offset['x'] = 5
    offset['y'] = 0
    offset['z'] = 0
    setPulse('R', 1000)
  elif('runMinusX' == recv_msg): setPulse('R', 1001)
  elif('getRobotStatus' == recv_msg): 
    data = {
    'MR_relay': L.MR_relay,
    'R_relay': L.R_relay,
    'current_pos': current_pos,
    }
    json_data = json.dumps(data)
    client.publish(pub_topic, json_data)

def exit_handler():
  client.loop_stop()
  client.disconnect()
  print('MQTT client disconnected.') 

client_id = f'publish-{random.randint(0, 1000)}'
client = mqtt.Client(client_id)
client.on_message = on_message
client.connect(broker_address, port)
client.subscribe(sub_topic)
client.loop_start()
atexit.register(exit_handler)

try:
  while True:
    print('------------ loop ------------')
    time.sleep(0.001)
    L.updateTime(); # 時間の更新処理
    L.R_relay[:50] = L_web.R_relay[:50].copy()
    L.ldlg = 0x0    # ブロック用変数
    L.aax  = 0x0    # 回路の状態保持変数
    L.trlg = 0x0    # ＭＰＳ／ＭＲＤ／ＭＰＰ
    L.iix  = 0x01   # ＭＣ用変数の初期化

    #;Process:select_robot_1
    L.LD(CR, 2002)
    L.MPS()
    L.ANB(MR, 1000)
    L.OUT(MR, 0)
    L.MPP()
    L.LDPB(MR, 0)
    L.OR(MR, 1000)
    L.ANL()
    L.OUT(MR, 1000)
    #;Post-Process:select_robot_1
    L.LDP(MR, 0)
    if (L.aax & L.iix):
      module = importlib.import_module('iai_3axis_tabletop_api')
      RB = module.RobotApi('192.168.250.101', 23, '/dev/ttyUSB0', 115200)
    if(RB):
      RB.getRobotStatus()
      input_port = RB.getInput()
      servo = RB.servo
      origin = RB.origin
      arrived = RB.arrived
      current_pos['x'] = RB.current_pos[0]
      current_pos['y'] = RB.current_pos[1]
      current_pos['z'] = RB.current_pos[2]
      
    # print(current_pos)

    #;ボタンランプ
    #;auto start 
    # L.LD(CR, 2002)
    # L.OUT(R, 5000)
    #;manual start 
    L.LD(CR, 2002)
    L.OUT(R, 6201)
    #;pause
    L.LDP(R, 1)
    L.ANB(R, 5001)
    L.LDPB(R, 1)
    L.AND(R, 5001)
    L.ORL()
    L.OUT(R, 5001)
    L.LDP(R, 5001)
    if (L.aax & L.iix):
      RB.stopRobot()
    #;servo
    L.LD(servo)
    L.OUT(R, 6203)
    L.LDP(R, 1203)
    L.AND(servo)
    if (L.aax & L.iix):
      RB.setServoOff()
    L.LDP(R, 1203)
    L.ANB(servo)
    if (L.aax & L.iix):
      RB.setServoOn()
    #;jog
    L.LDP(R, 800)
    L.LD(R, 5800)
    L.ANPB(R, 801)
    L.ORL()
    L.OUT(R, 5800)
    #;inching
    L.LDP(R, 801)
    L.LD(R, 5801)
    L.ANPB(R, 800)
    L.ORL()
    L.OUT(R, 5801)

    #;マニュアル動作
    #;inching:wait
    L.LD(CR, 2002)
    # L.ANB(LR, 1001)
    L.MPS()
    L.ANB(LR, 1000)
    L.OUT(LR, 0)
    L.MPP()
    L.LDP(R, 1000)
    L.OR(LR, 1000)
    L.ANL()
    L.OUT(LR, 1000)
    #;inching:move
    L.LD(LR, 1000)
    L.MPS()
    L.LDB(R, 5001)
    L.ANB(LR, 1001)
    L.ANL()
    L.OUT(LR, 1)
    L.MPP()
    L.LDB(R, 5001)
    L.AND(arrived)
    L.ANPB(LR, 1)
    L.OR(LR, 1001)
    L.ANL()
    L.OUT(LR, 1001)
    L.LDP(LR, 1)
    if (L.aax & L.iix):
      x, y, z, rx, ry, rz, vel, acc, dec, dist, wait = L.FB_setRobotParam(current_pos['x']+offset['x'], current_pos['y']+offset['y'], current_pos['z']+offset['z'], 0, 0, 0, 10, 0.1, 0.1, 0.1, 0, 0, 0, 0, 0, 0, 0, 100)
      RB.moveAbsoluteLine(x, y, z, rx, ry, rz, vel, acc, dec)
    L.LD(LR, 1)
    if (L.aax & L.iix):
      target_pos = []
      target_pos.append(current_pos['x']+offset['x'])
      target_pos.append(current_pos['y']+offset['y'])
      target_pos.append(current_pos['z']+offset['z'])
      target_pos.append(0)
      target_pos.append(0)
      target_pos.append(0)
      RB.waitArrive(target_pos, 0.1)      
      
    print("LR1000", L.getRelay(LR, 1000))         
    print("LR1001", L.getRelay(LR, 1001))         
    print("arrived", arrived)         

except Exception as e:  
  client.loop_stop()
  client.disconnect()
  print('MQTT client disconnected.')
  print(e)