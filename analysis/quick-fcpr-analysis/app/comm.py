# -*- coding: UTF-8 -*-
import time
import redis
import json
import os
import sys
import importlib
import signal
import ast

import lib.utility.helper as helper

# シグナルハンドラの設定
def signal_handler(sig, frame):
    sys.exit(-1)

if os.name == 'nt':
    signal.signal(signal.SIGBREAK, signal_handler)
elif os.name == 'posix':
    signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# 実行時の引数を取得
args = sys.argv

# 引数の表示
print("コマンドライン引数:", args)

# 引数の処理
if len(args) > 1:
    print(f"最初の引数: {args[1]}")
else:
    print("引数がありません。")
    sys.exit(-1)  # 引数がない場合は終了

class ModuleImporter:
    def __init__(self, module_name):
        # 動的にロボットAPIをインポートする準備
        # current_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
        current_dir = os.path.abspath(os.path.dirname(__file__))
        sys.path.append(current_dir)
        API_PATH = 'lib/robot/'
        sys.path.append(os.path.join(current_dir, API_PATH))

        self.module_name = module_name
        self.module = None
        self.robot_api = None
        self.import_robot_api()

    def import_robot_api(self):
        try:
            self.module = importlib.import_module(self.module_name + '_api')
            self.robot_api = self.module.RobotApi('192.168.250.101', 23, '/dev/ttyUSB0', 115200)
        except ImportError as e:
            print(f"Error: Could not import module '{self.module_name + '_api'}'. {e}")
            sys.exit(-1)
        except AttributeError as e:
            print(f"Error: The module does not contain 'RobotApi'. {e}")
            sys.exit(-1)

    def write_robot_error(self):
        base_error_list = {
            f'code{i+1}': {
                'message': '',
                'timestamp': None,
                'addr': f'EM38{str(i//16).zfill(2)}.{str(i%16).zfill(2)}',
                'condition': True
            }
            for i in range(0, 1600)
        }
        
        for index, (error_code, error_message) in enumerate(self.robot_api.error_list.items(), start=1):
            base_error_list[f'code{error_code}'] = base_error_list.pop(f'code{index}')
            base_error_list[f'code{error_code}']['message'] = error_message
        
        helper.write_yaml(f'../../public/config/error.yaml', base_error_list)

class RobotStatus:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=2):
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

    def set_robot_status(self, servo, origin, arrived, error, error_id, current_pos, input_signal):
        # ステータスを辞書形式で作成
        data = {
            'servo': servo,
            'origin': origin,
            'arrived': arrived,
            'error': error,
            'error_id': error_id,
            'current_pos': current_pos,
            'input_signal': input_signal,
        }

        # Redis に pipeline を使って一括で書き込む
        with self.redis_client.pipeline() as pipe:
            pipe.delete('robot_status')  # 古いデータを削除
            pipe.rpush('robot_status', json.dumps(data))  # データをリストとして追加
            pipe.execute()  # pipeline 実行

class CommandReceiver:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=2):
      self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

    def listen_for_commands(self):
      # ノンブロッキングでコマンドを取得
      command = self.redis_client.lpop('robot_commands')  # コマンドを取得 (ブロックせず)
      if command:
          command_str = command.decode('utf-8')
          print(f"Received command: {command_str}")

          if command_str == 'None':
              print("Exiting command loop.")
              return None  # 'None'の場合、Noneを返す

          # コマンドを処理して結果を返す
          result = self.process_command(command_str)
          # 結果を返す
          self.redis_client.rpush('command_results', result)

    def process_command(self, command):
        command_mapping = {
            'getRobotStatus': RB.getRobotStatus,
            'setServoOn': RB.setServoOn,
            'setServoOff': RB.setServoOff,
            'moveAbsoluteLine': RB.moveAbsoluteLine,
            'moveJog': RB.moveJog,
            'stopRobot': RB.stopRobot,
            'resetError': RB.resetError,
            'stopJog': RB.stopJog,
            'waitArrive': RB.waitArrive,
            'getInput': RB.getInput,
            'setOutputON': RB.setOutputON,
            'setOutputOFF': RB.setOutputOFF,
        }

        # 関数名と引数の分解
        command_parts = command.split('(', 1)
        command_name = command_parts[0]

        # 引数部分の処理
        # if len(command_parts[1]) > 2:
        # 引数が無いなら
        if (command_parts[1] == ')'):
          args = []
        # 引数が有るなら
        else:
          args_str = command_parts[1].rstrip(')')
          # 引数にリストが含まれているかどうかの確認
          if '[' in args_str and ']' in args_str:
              # リストの部分を安全に評価する
              list_start = args_str.index('[')
              list_end = args_str.index(']') + 1
              list_str = args_str[list_start:list_end]
              other_args_str = args_str[list_end:].strip(',').strip()
              
              # リストと他の引数をパース
              try:
                  parsed_list = ast.literal_eval(list_str)  # リスト部分を安全に評価
              except Exception as e:
                  return f"Error: Invalid list format in command: {command}. {e}"

              # 残りの引数をパース
              other_args = [
                  float(arg.strip()) if '.' in arg.strip() else
                  int(arg.strip()) if arg.strip().lstrip('-').isdigit() else
                  arg.strip()
                  for arg in other_args_str.split(',') if arg.strip()
              ]

              args = [parsed_list] + other_args
          else:
              # 通常の引数を処理
            args = [
                float(arg.strip()) if '.' in arg.strip() else
                int(arg.strip()) if arg.strip().lstrip('-').isdigit() else
                str(arg.strip())
                for arg in args_str.split(',')
            ]
          
        # print(args)

        # コマンド実行
        action = command_mapping.get(command_name)
        if action:
            action(*args)
            return f"Result of {command}"
        else:
            return f"Error: Invalid command {command}'"

if __name__ == '__main__':
    # ロボットAPIを動的に読み込み
    module_importer = ModuleImporter(args[1])  # モジュールのインポート
    RB = module_importer.robot_api  # RobotApi インスタンスを取得
    module_importer.write_robot_error() # 共通エラーファイルにAPIエラーを書き込み

    robot_status = RobotStatus()
    command_receiver = CommandReceiver()
    
    # ループ動作開始
    while True:
        try:
            # print("comm is running ...")
            # start = time.perf_counter()
            # time.sleep(0.001)

            # コマンド受信
            command_receiver.listen_for_commands()

            # ステータスと位置を一括で設定
            RB.getRobotStatus()
            robot_status.set_robot_status(
                servo=RB.servo,
                origin=RB.origin,
                arrived=RB.arrived,
                error=RB.error,
                error_id=RB.error_id,
                current_pos=RB.current_pos,
                input_signal=RB.input_signal,
            )

            # end = time.perf_counter()
            # elapsed_time = end - start
            # print('cycle time[msec]', elapsed_time)

        except Exception as e:
            print(e)
            sys.exit(-1)