from lib.utility.constant import DM, EM, R, MR, LR, CR, T
from lib.utility.common_globals import L, RD, RAC
# from lib.utility.auto_globals import number_param_yaml, initial_number_param_yaml
from lib.utility.constant import TEACH_FILE_PATH, NUMBER_PARAM_FILE_PATH, FLAG_PARAM_FILE_PATH, ERROR_FILE_PATH

# To set redis
import json
from itertools import accumulate

# To read sidebar
import lib.sidebar.teaching as teach
import lib.sidebar.number_parameter as num_param
import lib.sidebar.robot_io as rb_io

# To use laddar func
import lib.utility.helper as helper

# To split string
import re

import copy


def getPalletOffset(pallet, pallet_no):
  # オフセット量XYZ計算準備
  vec = {'AB':{},'AC':{}, 'BD':{},'CD':{}}
  vec['AB']['x'] = pallet[pallet_no-1]['B']['x'] - pallet[pallet_no-1]['A']['x']
  vec['AB']['y'] = pallet[pallet_no-1]['B']['y'] - pallet[pallet_no-1]['A']['y']
  vec['AB']['z'] = pallet[pallet_no-1]['B']['z'] - pallet[pallet_no-1]['A']['z']
  vec['AC']['x'] = pallet[pallet_no-1]['C']['x'] - pallet[pallet_no-1]['A']['x']
  vec['AC']['y'] = pallet[pallet_no-1]['C']['y'] - pallet[pallet_no-1]['A']['y']
  vec['AC']['z'] = pallet[pallet_no-1]['C']['z'] - pallet[pallet_no-1]['A']['z']
  vec['BD']['x'] = pallet[pallet_no-1]['D']['x'] - pallet[pallet_no-1]['B']['x']
  vec['BD']['y'] = pallet[pallet_no-1]['D']['y'] - pallet[pallet_no-1]['B']['y']
  vec['BD']['z'] = pallet[pallet_no-1]['D']['z'] - pallet[pallet_no-1]['B']['z']
  vec['CD']['x'] = pallet[pallet_no-1]['D']['x'] - pallet[pallet_no-1]['C']['x']
  vec['CD']['y'] = pallet[pallet_no-1]['D']['y'] - pallet[pallet_no-1]['C']['y']
  vec['CD']['z'] = pallet[pallet_no-1]['D']['z'] - pallet[pallet_no-1]['C']['z']
  vec_N = {}
  vec_N['a']  = vec['AB']['y'] * vec['AC']['z'] - vec['AB']['z'] * vec['AC']['y']
  vec_N['b']  = vec['AB']['z'] * vec['AB']['x'] - vec['AB']['x'] * vec['AC']['z']
  vec_N['c']  = vec['AB']['x'] * vec['AC']['y'] - vec['AB']['y'] * vec['AB']['x']
  # オフセット量XY計算準備
  MAX_row = pallet[pallet_no-1]['row']
  MAX_col = pallet[pallet_no-1]['col']
  dst_pocket = pallet[pallet_no-1]['dst_pocket']
  if ((dst_pocket <= MAX_row * MAX_col) and (dst_pocket > 0)):
    dst_row = (dst_pocket-1) % MAX_row + 1
    dst_col = int((dst_pocket-1) / MAX_row) + 1
  else:
    dst_row = 1
    dst_col = 1
  # 目標位置算出用の4点計算
  dst_row_index = dst_row - 1
  dst_col_index = dst_col - 1
  divided_row_num = MAX_row - 1
  divided_col_num = MAX_col - 1
  P = {'AB':{},'BD':{},'CD':{},'AC':{}}
  P['AB']['x'] = vec['AB']['x'] * (dst_row_index / divided_row_num) + pallet[pallet_no-1]['A']['x']
  P['AB']['y'] = vec['AB']['y'] * (dst_row_index / divided_row_num) + pallet[pallet_no-1]['A']['y']
  P['BD']['x'] = vec['AB']['x'] + vec['BD']['x'] * (dst_col_index / divided_col_num) + pallet[pallet_no-1]['A']['x']
  P['BD']['y'] = vec['AB']['y'] + vec['BD']['y'] * (dst_col_index / divided_col_num) + pallet[pallet_no-1]['A']['y']
  P['CD']['x'] = vec['AC']['x'] + vec['CD']['x'] * (dst_row_index / divided_row_num) + pallet[pallet_no-1]['A']['x']
  P['CD']['y'] = vec['AC']['y'] + vec['CD']['y'] * (dst_row_index / divided_row_num) + pallet[pallet_no-1]['A']['y']
  P['AC']['x'] = vec['AC']['x'] * (dst_col_index / divided_col_num) + pallet[pallet_no-1]['A']['x']
  P['AC']['y'] = vec['AC']['y'] * (dst_col_index / divided_col_num) + pallet[pallet_no-1]['A']['y']
  S1 = ((P['AC']['x'] - P['BD']['x']) * (P['AB']['y'] - P['BD']['y']) - (P['AC']['y'] - P['BD']['y']) * (P['AB']['x'] - P['BD']['x'])) / 2
  S2 = ((P['AC']['x'] - P['BD']['x']) * (P['BD']['y'] - P['CD']['y']) - (P['AC']['y'] - P['BD']['y']) * (P['BD']['x'] - P['CD']['x'])) / 2
  # オフセット量XYZ計算
  offset = {'x': 0.0, 'y': 0.0, 'z': 0.0}
  offset['x'] = round(P['AB']['x'] + (P['CD']['x']- P['AB']['x']) * (S1 / (S1 + S2)) - pallet[pallet_no-1]['A']['x'], 3)
  offset['y'] = round(P['AB']['y'] + (P['CD']['y']- P['AB']['y']) * (S1 / (S1 + S2)) - pallet[pallet_no-1]['A']['y'], 3)
  if (abs(vec_N['c']) > 0): offset['z'] = round((-1) * (vec_N['a'] * offset['x'] + vec_N['b'] * offset['y']) / vec_N['c'], 3)
  
  return offset

def cleanup():
    print("Performing cleanup.....")
    # 全要素を0で初期化
    L.R_relay[:] = [0] * len(L.R_relay)
    L.MR_relay[:] = [0] * len(L.MR_relay)
    L.EM_relay[:] = [0] * len(L.EM_relay)
    send_command()

def send_command():
    # 二次元配列とコマンド文字列をJSON形式でエンコードして保存
    data = [L.R_relay, L.MR_relay, L.EM_relay]
    with RD.pipeline() as pipe:
        pipe.delete('device_list')
        pipe.rpush('device_list', json.dumps(data))
        pipe.execute()
        return True

# def send_command2():
#     # Redisから'device_list'を取得
#     device_list = RD.lindex('device_list', 0)
#     if device_list is not None:
#         # JSONデコードしてリストに変換
#         data = json.loads(device_list)
        
#         # device_listの2番目の要素 (MR_relay) を更新
#         data[1] = L.MR_relay  # L.MR_relayに新しい値を代入
        
#         # Redisに更新されたリストを保存
#         with RD.pipeline() as pipe:
#             pipe.delete('device_list')
#             pipe.rpush('device_list', json.dumps(data))
#             pipe.execute()
#     else:
#         print("Error: 'device_list' not found in Redis.")

# def create_bit_button():
#     # Puaseボタン
#     L.LDP(R, 3)
#     L.ANB(R, 5003)
#     L.LDPB(R, 3)
#     L.AND(R, 5003)
#     # L.ANB() MR007:Z1
#     L.ORL()
#     L.OUT(R, 5003)

def create_bit_button(device_name, btn_device_no, lamp_device_no):
    L.LDP(device_name, btn_device_no)
    L.ANB(device_name, lamp_device_no)
    L.LDPB(device_name, btn_device_no)
    L.AND(device_name, lamp_device_no)
    L.ORL()
    L.OUT(device_name, lamp_device_no)

def create_cycle_timer():
    # 500msecタイマー
    L.LDB(L.local_T['500msec_timer[1]']['name'], L.local_T['500msec_timer[1]']['addr'])
    L.TMS(L.local_T['500msec_timer[0]']['addr'], 500)
    L.LD(L.local_T['500msec_timer[0]']['name'], L.local_T['500msec_timer[0]']['addr'])
    L.TMS(L.local_T['500msec_timer[1]']['addr'], 500)

    # 1000msecタイマー
    L.LDB(L.local_T['1000msec_timer[1]']['name'], L.local_T['1000msec_timer[1]']['addr'])
    L.TMS(L.local_T['1000msec_timer[0]']['addr'], 1000)
    L.LD(L.local_T['1000msec_timer[0]']['name'], L.local_T['1000msec_timer[0]']['addr'])
    L.TMS(L.local_T['1000msec_timer[1]']['addr'], 1000)

def register_error(no, message, error_yaml):
    error_yaml[f'code{no}']['message'] = message

def raise_error(no, error_yaml):
    device = error_yaml[f'code{no}']['addr']
    device_name, device_no = split_device(device)
    L.setRelay(device_name, device_no)
    # raise ValueError(error_yaml[f'code{no}']['message'])

def blink_reset_button():
    L.LD(MR, 501)
    L.AND(L.local_T['500msec_timer[0]']['name'], L.local_T['500msec_timer[0]']['addr'])
    L.OUT(R, 5005)

def check_api_error(robot_status, error_yaml):
    if (robot_status['error'] == True):
        if (error_yaml):
            func.raise_error(no=int(robot_status['error_id']), error_yaml=error_yaml)
        else:
            error_yaml = helper.read_yaml(ERROR_FILE_PATH)
            func.raise_error(no=int(robot_status['error_id']), error_yaml=error_yaml)
    error_val = sum(L.EM_relay[3800:3900])
    L.LDG(error_val, 0)
    L.OUT(MR, 501)

def update_man_status():
    # Error発生
    L.LD(MR, 501)
    if (L.aax & L.iix):
        status = 'Error'
        L.EM_relay[0:0+len(helper.name_to_ascii16(status, 40))] = helper.name_to_ascii16(status, 40)

    # Errorリセット
    L.LD(R, 5)
    L.AND(MR, 501)
    L.OUT(L.local_R['reset_program[0]']['name'], L.local_R['reset_program[0]']['addr'])
    if (L.aax & L.iix):
        # エラー配列初期化
        L.EM_relay[3800:3900] = [0] * 100
        # ステータス更新
        status = 'MANUAL'
        L.EM_relay[0:0+len(helper.name_to_ascii16(status, 40))] = helper.name_to_ascii16(status, 40)
        

def update_auto_status(number_param_yaml, initial_number_param_yaml):
    # Error
    L.LD(MR, 501)
    if (L.aax & L.iix):
        auto_status = 'Error'
        L.EM_relay[0:0+len(helper.name_to_ascii16(auto_status, 40))] = helper.name_to_ascii16(auto_status, 40)

    # リセットボタン点滅
    # L.LD(MR, 501)
    # # L.MPS()
    # L.AND(L.local_T['500msec_timer[0]']['name'], L.local_T['500msec_timer[0]']['addr'])
    # L.OUT(R, 5005)
    # # L.MPP()
    # # L.OUT(R, 5003)

    # Pause
    L.LDP(R, 5003)
    if (L.aax & L.iix):
        auto_status = 'Pausing ...'
        L.EM_relay[0:0+len(helper.name_to_ascii16(auto_status, 40))] = helper.name_to_ascii16(auto_status, 40)

    # Error Reset
    L.LD(R, 5)
    L.AND(MR, 501)
    L.OUT(L.local_R['reset_program[0]']['name'], L.local_R['reset_program[0]']['addr'])
    if (L.aax & L.iix):
        L.EM_relay[3800:3900] = [0] * 100
        auto_status = 'Program was reset ...'

        # パラメータ初期化
        # param_yaml.clear()
        number_param_yaml.update(copy.deepcopy(initial_number_param_yaml))

        # ステータス更新
        L.EM_relay[0:0+len(helper.name_to_ascii16(auto_status, 40))] = helper.name_to_ascii16(auto_status, 40)

def check_auto_error(error_yaml):
    error_val = sum(L.EM_relay[3800:3900])
    L.LDG(error_val, 0)
    L.OUT(MR, 501)

    # エラーファイル更新
    L.LDP(MR, 501)
    if (L.aax & L.iix):
        helper.write_yaml(ERROR_FILE_PATH, error_yaml)

# データの差分確認
previous_command = None
def get_command():
    global previous_command  # 関数内でグローバル変数を使用することを明示
    # 配列のデータを取得
    command_value = RD.get('command')
    # キーが存在しなければ
    if (command_value is None):
        pass
        # print("Command is None.")
    else:
        decoded_command = command_value.decode('utf-8')
        if (decoded_command != previous_command):
            print("Command changed:", decoded_command)
            # 差分があった場合の処理をここに追加
            print("Processing command change...")
            lengths = [2, 6, 4]
            # 累積インデックスを生成
            indices = list(accumulate(lengths, initial=0))
            # スライスして分解
            parts = [decoded_command[indices[i]:indices[i+1]] for i in range(len(lengths))]
            device_name = parts[0]
            device_no = int(parts[1])
            device_cnt = int(parts[2])
            ########## Rデバイスの処理 ##########
            if ('R' in device_name):
                device_values = []
                duration = 1
                start_index = indices[len(lengths)-1] + len(parts[2])
                for i in range(device_cnt):
                    end_index = start_index + duration
                    device_values.append(int(decoded_command[start_index:end_index]))
                    start_index = end_index
                # データ書き換え
                for index, element in enumerate(device_values):
                    # ビットONの場合
                    if (element == 1):
                        L.setRelay('R', device_no)
                    # ビットOFFの場合
                    else:
                        L.resetRelay('R', device_no)
            ########## MRデバイスの処理 ##########
            elif ('MR' in device_name):
                device_values = []
                duration = 1
                start_index = indices[len(lengths)-1] + len(parts[2])
                for i in range(device_cnt):
                    end_index = start_index + duration
                    device_values.append(int(decoded_command[start_index:end_index]))
                    start_index = end_index
                # データ書き換え
                for index, element in enumerate(device_values):
                    # ビットONの場合
                    if (element == 1):
                        L.setRelay('MR', device_no)
                    # ビットOFFの場合
                    else:
                        L.resetRelay('MR', device_no)
            ########## EMデバイスの処理 ##########
            elif ('EM' in device_name):
                # 4文字ごとに分割して、デバイス値を16進数文字列→10進数に変換して取得
                device_values = []
                duration = 4
                start_index = indices[len(lengths)-1] + len(parts[2])
                for i in range(device_cnt):
                    end_index = start_index + duration
                    device_values.append(int(decoded_command[start_index:end_index], 16))
                    start_index = end_index
                # データ書き換え
                for index, element in enumerate(device_values):
                    L.EM_relay[device_no+index] = element
            # データベースのコマンドを消去
            RD.delete('command')
        # 前回のコマンドを更新
        previous_command = decoded_command

def split_device(device):
    # 正規表現を使って、最初の文字列と数字部分を分ける
    match = re.match(r'([A-Za-z]+)(\d+)\.(\d+)', device)
    if match:
        device_name = match.group(1)
        device_no = int(match.group(2) + match.group(3))
        return device_name, device_no
    else:
        raise ValueError("Invalid input format")

def handle_man_sidebar(robot_status):
    # 画面処理
    ############################################################
    #################### ティーチングサイドバー
    ############################################################
    L.LDEQ(L.EM_relay[55010], 1)
    L.OUT(L.local_R['show_sidebar[1]']['name'], L.local_R['show_sidebar[1]']['addr'])
    # 立ち上がり
    L.LDP(L.local_R['show_sidebar[1]']['name'], L.local_R['show_sidebar[1]']['addr'])
    if (L.aax & L.iix):
        L.EM_relay[2005] = 10 # 最大ページ番号
        L.EM_relay[2006] = 1 # 現在ページ番号
        L.DM_relay[3805] = 10 # Jog速度
        L.setRelay(R, 900) # PosランプON
        L.setRelay(R, 801) # InchingランプON
        L.setRelay(R, 802) # Jog速度10mm/sランプON           
    # 常時
    L.LD(L.local_R['show_sidebar[1]']['name'], L.local_R['show_sidebar[1]']['addr'])
    if (L.aax & L.iix):
        # テーブル処理
        teach.update_page_no()
        teach.update_point_no()
        teach.update_table_pos()
        teach.update_table_vel()
        teach.update_table_acc()
        teach.update_table_dec()
        teach.update_table_setting()
        teach.write_teaching()
        teach.get_robot_pos()
        teach.copy_teaching()
        teach.paste_teaching()
        # ボタン操作
        teach.select_move_mode()
        teach.select_jog_speed()
        # ロボット操作
        teach.get_robot_data(robot_status)
        teach.handle_servo(robot_status)
        teach.move_inching(robot_status)
        teach.move_jog()

    ############################################################
    #################### パラメータサイドバー
    ############################################################
    L.LDEQ(L.EM_relay[55010], 2)
    L.OUT(L.local_R['show_sidebar[2]']['name'], L.local_R['show_sidebar[2]']['addr'])
    # 立ち上がり
    L.LDP(L.local_R['show_sidebar[2]']['name'], L.local_R['show_sidebar[2]']['addr'])
    if (L.aax & L.iix):
        L.EM_relay[2000] = 15 # 最大パラメータページ番号
        L.EM_relay[2001] = 1 # 現在パラメータページ番号
        num_param.read_param()
    # 常時
    L.LD(L.local_R['show_sidebar[2]']['name'], L.local_R['show_sidebar[2]']['addr'])
    if (L.aax & L.iix):
        # テーブル処理
        num_param.update_page_no()
        num_param.update_data_no()
        num_param.write_param()
        
    ############################################################
    #################### ロボットIOサイドバー
    ############################################################
    L.LDEQ(L.EM_relay[55010], 4)
    L.OUT(L.local_R['show_sidebar[4]']['name'], L.local_R['show_sidebar[4]']['addr'])
    # 立ち上がり
    L.LDP(L.local_R['show_sidebar[4]']['name'], L.local_R['show_sidebar[4]']['addr'])
    if (L.aax & L.iix):
        pass          
    # 常時
    L.LD(L.local_R['show_sidebar[4]']['name'], L.local_R['show_sidebar[4]']['addr'])
    if (L.aax & L.iix):
        rb_io.handle_input(robot_status)
        rb_io.handle_output()

def handle_auto_sidebar(robot_status):
    # 画面処理
    ############################################################
    #################### ティーチングサイドバー
    ############################################################
    L.LDEQ(L.EM_relay[55010], 1)
    L.OUT(L.local_R['show_sidebar[1]']['name'], L.local_R['show_sidebar[1]']['addr'])
    # 立ち上がり
    L.LDP(L.local_R['show_sidebar[1]']['name'], L.local_R['show_sidebar[1]']['addr'])
    if (L.aax & L.iix):
        L.EM_relay[2005] = 10 # 最大ページ番号
        L.EM_relay[2006] = 1 # 現在ページ番号
        L.DM_relay[3805] = 10 # Jog速度
        L.setRelay(R, 900) # PosランプON
        L.setRelay(R, 801) # InchingランプON
        L.setRelay(R, 802) # Jog速度10mm/sランプON           
    # 常時
    L.LD(L.local_R['show_sidebar[1]']['name'], L.local_R['show_sidebar[1]']['addr'])
    if (L.aax & L.iix):
        # テーブル処理
        teach.update_page_no()
        teach.update_point_no()
        teach.update_table_pos()
        teach.update_table_vel()
        teach.update_table_acc()
        teach.update_table_dec()
        teach.update_table_setting()
        # teach.write_teaching()
        # teach.get_robot_pos()
        # teach.copy_teaching()
        # teach.paste_teaching()
        # ボタン操作
        # teach.select_move_mode()
        # teach.select_jog_speed()
        # ロボット操作
        teach.get_robot_data(robot_status)
        # teach.handle_servo(robot_status)
        # teach.move_inching(robot_status)
        # teach.move_jog()

    ############################################################
    #################### パラメータサイドバー
    ############################################################
    L.LDEQ(L.EM_relay[55010], 2)
    L.OUT(L.local_R['show_sidebar[2]']['name'], L.local_R['show_sidebar[2]']['addr'])
    # 立ち上がり
    L.LDP(L.local_R['show_sidebar[2]']['name'], L.local_R['show_sidebar[2]']['addr'])
    if (L.aax & L.iix):
        L.EM_relay[2000] = 15 # 最大パラメータページ番号
        L.EM_relay[2001] = 1 # 現在パラメータページ番号
        num_param.read_param()
    # 常時
    L.LD(L.local_R['show_sidebar[2]']['name'], L.local_R['show_sidebar[2]']['addr'])
    if (L.aax & L.iix):
        # テーブル処理
        num_param.update_page_no()
        num_param.update_data_no()
        # num_param.write_param()
        
    ############################################################
    #################### ロボットIOサイドバー
    ############################################################
    L.LDEQ(L.EM_relay[55010], 4)
    L.OUT(L.local_R['show_sidebar[4]']['name'], L.local_R['show_sidebar[4]']['addr'])
    # 立ち上がり
    L.LDP(L.local_R['show_sidebar[4]']['name'], L.local_R['show_sidebar[4]']['addr'])
    if (L.aax & L.iix):
        pass          
    # 常時
    L.LD(L.local_R['show_sidebar[4]']['name'], L.local_R['show_sidebar[4]']['addr'])
    if (L.aax & L.iix):
        pass
        # rb_io.handle_input(robot_status)
        # rb_io.handle_output()