import time, json, os, sys, importlib, signal, copy, pickle
# To use globals var
from lib.utility.constant import DM, EM, R, MR, LR, CR, T
from lib.utility.common_globals import L, RD, RAC
# To use laddar func
import lib.utility.functions as func
import lib.utility.helper as helper

def signal_handler(sig, frame):
    func.cleanup()
    sys.exit(0)

# プログラム終了時にcleanup関数を呼び出す
# Windowsなら
if os.name == 'nt':
    signal.signal(signal.SIGBREAK, signal_handler) 
# Linuxなら
elif os.name == 'posix':
    signal.signal(signal.SIGTERM, signal_handler) 

signal.signal(signal.SIGINT, signal_handler)

# 初期化
L.EM_relay[3000] = 10000 # インチング幅10mm
auto_status = 'MANUAL MODE'
L.EM_relay[0:0+len(helper.name_to_ascii16(auto_status, 40))] = helper.name_to_ascii16(auto_status, 40) # 自動運転ステータス

error_yaml = None

while True:
    # print('Man program is running...')
    start = time.perf_counter()
    func.send_command() # Resid経由でコマンド送信
    time.sleep(0.001) # 動作安定用タイマ 
    L.updateTime()  # 時間の更新処理
    L.ldlg = 0x0    # ブロック用変数
    L.aax  = 0x0    # 回路の状態保持変数
    L.trlg = 0x0    # ＭＰＳ／ＭＲＤ／ＭＰＰ
    L.iix  = 0x01   # ＭＣ用変数の初期化
    func.get_command() # Resid経由でコマンド受信
    func.create_cycle_timer()  # 定周期タイマー作成
    robot_status = RAC.get_status() # ロボットステータス更新

    ############################################################
    #################### APIエラー処理
    ############################################################
    # APIエラー状態監視
    func.check_api_error(robot_status, error_yaml)
    # ステータスバー内容更新
    func.update_man_status()
    # リセットボタン点滅
    func.blink_reset_button()
    # ロボットリセット
    L.LDP(L.local_R['reset_program[0]']['name'], L.local_R['reset_program[0]']['addr'])
    if (L.aax & L.iix):
        RAC.send_command('resetError()')

    ############################################################
    #################### サイドバー処理
    ############################################################
    func.handle_man_sidebar(robot_status)   

    ############################################################
    #################### サイクルタイム計測
    ############################################################
    end = time.perf_counter()
    elapsed_time = end - start
    # print('cycle time[msec]', elapsed_time)
