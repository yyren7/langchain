import redis
import subprocess
import os
from celery import Celery
from celery.exceptions import MaxRetriesExceededError
import json
import signal
import psutil

# import logging
from celery.app.log import Logging
# from task_logging import setup_logging
from datetime import datetime
# from logging.handlers import RotatingFileHandler

# Celery設定
app_celery_db0 = Celery('Program_Handler', broker='redis://127.0.0.1:6379/0', backend='redis://127.0.0.1:6379/0')
# app_celery_db1 = Celery('Command_Handler', broker='redis://127.0.0.1:6379/1', backend='redis://127.0.0.1:6379/1')
redis_client_db0 = redis.StrictRedis(host='localhost', port=6379, db=0)
redis_client_db1 = redis.StrictRedis(host='localhost', port=6379, db=1)

# celeryconfig.py から設定をロード
# app_celery_db0.config_from_object('celeryconfig')

# Redis データベース0をクリア
redis_client_db0.flushdb()

# Redis データベース初期化
# 各モードのステータスをまとめる
program_task = {'status': 'stop', 'TID': 'null', 'PID': 'null'}

# フィールドに対して更新
redis_client_db0.hset('program_task', 'auto', json.dumps(program_task))
redis_client_db0.hset('program_task', 'man', json.dumps(program_task))
redis_client_db0.hset('program_task', 'comm', json.dumps(program_task))

# program_task = {
#     'auto': {'status': 'stop', 'TID': 'null', 'PID': 'null'},
#     'man': {'status': 'stop', 'TID': 'null', 'PID': 'null'},
#     'comm': {'status': 'stop', 'TID': 'null', 'PID': 'null'}
# }

# # 一つのキー "program_task" に格納
# redis_client_db0.hset('program_task', json.dumps(program_task))

# ロギング設定
# log_directory = os.path.join(os.getcwd(), 'log')
# if not os.path.exists(log_directory):
#     os.makedirs(log_directory)

# today_date = datetime.now().strftime('%Y-%m-%d')
# logfile = os.path.join(log_directory, f'celery_{today_date}.log')
# logger = Logging(app_celery_db0)
# logger.setup(
#     loglevel='INFO',
#     logfile=logfile,
#     redirect_stdouts=True,
#     redirect_level='INFO'
# )


app_celery_db0.conf.update(
    broker_connection_retry_on_startup=True,
)

@app_celery_db0.task(bind=True, name='kickPy', rate_limit='1/s')
def kickPy(self, program_name: str, arg1: str = ''):
    # self.logger.info(f"{program_name} program is running ...")
    print(program_name + " program is running ...")
    try:
        result = None
        # プロセスを開始し、標準出力をパイプに設定
        # Windowsなら
        if os.name == 'nt':
            result = subprocess.Popen(
                ['python', program_name + '.py', arg1],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        # Linuxなら
        elif os.name == 'posix':
            result = subprocess.Popen(
                ['python', program_name + '.py', arg1],
                # stdout=subprocess.PIPE,  # 標準出力をパイプに設定
                # stderr=subprocess.PIPE,   # エラー出力も取得
            )
    
        # Redisにプロセス状態を書き込む
        process_id = result.pid
        redis_client_db0.hset('program_task', program_name, json.dumps({'status': 'run', 'TID': self.request.id, 'PID': process_id}))

        # プロセス完了まで待機
        result.wait()

        # プロセスが異常終了した場合のエラー処理
        print(f'returncode: {result.returncode}')
        if result.returncode != 0:
            print('calling subprocess.CalledProcessError...')
            raise subprocess.CalledProcessError(
                result.returncode,
                ' '.join(result.args),
                # output=stdout,
                # stderr=stderr
            )

        # プロセスが正常終了した場合の処理
        else:
            redis_client_db0.hset('program_task', program_name, json.dumps({'status': 'stop', 'TID': self.request.id, 'PID': 'null'}))
            success_message = f"started with PID: {process_id}"
            return success_message

    except subprocess.CalledProcessError as e:
        print('called subprocess.CalledProcessError')
        redis_client_db0.hset('program_task', program_name, json.dumps({'status': 'error', 'TID': self.request.id, 'PID': 'null'}))

@app_celery_db0.task(bind=True, name='stopPy', rate_limit='1/s')
def stopPy(self, program_name, PID):
    try:
        # result.terminate()
        pid = int(PID)
        process = psutil.Process(PID)
        # Windowsなら
        if os.name == 'nt':
            process.send_signal(signal.CTRL_BREAK_EVENT)
        # Linuxなら
        elif os.name == 'posix':
            process.send_signal(signal.SIGTERM)

        process.wait()

        redis_client_db0.hset('program_task', program_name, json.dumps({'status': 'stop', 'TID': self.request.id, 'PID': 'null'}))

        success_message = f"PID {PID} stopped"
        return success_message

    except Exception as e:
        error_message = f"Error occurred: {e}"
        return error_message

def start_worker():
    command = [
        'celery', '-A', 'celery_tasks', 'worker',
        '-l', 'info',
        '-P', 'eventlet',
        '-n', 'programSwitcher',
        '-c', '4'
    ]
    subprocess.run(command)

if __name__ == '__main__':
    start_worker()