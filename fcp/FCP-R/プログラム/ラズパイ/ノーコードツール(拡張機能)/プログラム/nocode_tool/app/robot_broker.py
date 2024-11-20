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
print(current_dir)
API_PATH = 'lib/robot/'
sys.path.append(current_dir + API_PATH)
L_web = LaddarSeqAPI(max_R_relay=100, max_MR_relay=100, max_EM_relay=100, max_LR_relay=100, max_T_relay=100, max_C_relay=100)
L = LaddarSeqAPI(max_R_relay=100, max_MR_relay=100, max_EM_relay=100, max_LR_relay=100, max_T_relay=100, max_C_relay=100)
pallet = {}
offset = {'x': 0.0, 'y': 0.0, 'z': 0.0}

broker_address = 'broker.emqx.io'
port = 1883
sub_topic = 'control_robot'
pub_topic = 'feedback_robot'

def on_message(client, userdata, message):
  recv_msg = message.payload.decode()
  if('run' == recv_msg): 
    L_web.setRelay('R', 0)
    time.sleep(0.1)
    L_web.resetRelay('R', 0)
  elif('pause' == recv_msg): 
    L_web.setRelay('R', 1)
    time.sleep(0.1)
    L_web.resetRelay('R', 1)
  elif('status' == recv_msg): 
    data = {
    'MR_relay': L.MR_relay,
    'R_relay': L.R_relay
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
    time.sleep(0.1)
    L.updateTime(); # 時間の更新処理
    L.R_relay[:50] = L_web.R_relay[:50].copy()
    L.ldlg = 0x0    # ブロック用変数
    L.aax  = 0x0    # 回路の状態保持変数
    L.trlg = 0x0    # ＭＰＳ／ＭＲＤ／ＭＰＰ
    L.iix  = 0x01   # ＭＣ用変数の初期化

    #;ボタンランプ
    #;start
    L.LD(CR, 2002)
    L.OUT(R, 5000)
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


except Exception as e:  
  client.loop_stop()
  client.disconnect()
  print('MQTT client disconnected.')
  print(e)

