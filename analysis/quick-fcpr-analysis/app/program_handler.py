from flask import Flask, request, jsonify
from flask_cors import CORS
import celery_tasks as ct
import time
from celery.exceptions import TimeoutError
import redis
import json
import os

app_flask = Flask(__name__)
CORS(app_flask)

redis_client_db0 = redis.StrictRedis(host='localhost', port=6379, db=0)

@app_flask.route('/kick_auto_py', methods=['POST'])
def kickAutoPy():
    # プログラムファイル生成
    code = request.get_data(as_text=True)
    current_file_path = os.getcwd()
    file_path = os.path.join(current_file_path, 'auto.py')
    with open(file_path, 'w') as file:
        file.write(code)

    # 起動中のプログラム確認
    # 自動
    auto_status_str = redis_client_db0.hget('program_task', 'auto')
    auto_prog = json.loads(auto_status_str)
    # 手動
    man_status_str = redis_client_db0.hget('program_task', 'man')
    man_prog = json.loads(man_status_str)

    # man.pyが起動中なら停止
    if (man_status_str):
        if (man_prog['status'] == 'run'):
            ct.stopPy.apply_async(kwargs={'program_name': 'man', 'PID': man_prog['PID']})

    # auto.pyを実行
    if (auto_status_str):
        if (auto_prog['status'] == 'run'):
            return jsonify({'message': 'Target program is running'}), 200
        elif ((auto_prog['status'] == 'stop') or (auto_prog['status'] == 'error')):
            task = ct.kickPy.apply_async(kwargs={'program_name': 'auto'})
            try:
                task.get(timeout=3.0)
                return 'error', 500 # タイムアウトしない=プログラム起動できなかった
            except TimeoutError:
                return jsonify({'task_id': task.id}), 200  # タイムアウトする=プログラム起動中
        else:
            return jsonify({'message': 'status of the program is stopping.'}), 200  
    else:
        return jsonify({'message': 'Redis is not running.'}), 200   

@app_flask.route('/kick_man_py', methods=['POST'])
def kickManPy():
    # 起動中のプログラム確認
    # 自動
    auto_status_str = redis_client_db0.hget('program_task', 'auto')
    auto_prog = json.loads(auto_status_str)
    # 手動
    man_status_str = redis_client_db0.hget('program_task', 'man')
    man_prog = json.loads(man_status_str)

    # auto.pyが起動中なら停止
    if (auto_status_str):
        if (auto_prog['status'] == 'run'):
            ct.stopPy.apply_async(kwargs={'program_name': 'auto', 'PID': auto_prog['PID']})

    # man.pyを実行
    if (man_status_str):
        if (man_prog['status'] == 'run'):
            return jsonify({'message': 'Man program is running'}), 200
        elif ((man_prog['status'] == 'stop') or (man_prog['status'] == 'error')):
            task = ct.kickPy.apply_async(kwargs={'program_name': 'man'})
            try:
                task.get(timeout=1.5)
                return 'error', 500 # タイムアウトしない=プログラム起動できなかった
            except TimeoutError:
                return jsonify({'task_id': task.id}), 200  # タイムアウトする=プログラム起動中
        else:
            return jsonify({'message': 'Man program is stopping.'}), 200   
    else:
        return jsonify({'message': 'Redis is not running.'}), 200   

@app_flask.route('/kick_comm_py', methods=['POST'])
def kickCommPy():
    # クエリ取得
    robot_name = request.args.get('q')

    # 起動中のプログラム確認
    comm_status_str = redis_client_db0.hget('program_task', 'comm')
    comm_prog = json.loads(comm_status_str)

    # comm.pyを実行
    if (comm_status_str):
        if (comm_prog['status'] == 'run'):
            return jsonify({'message': 'Target program is running'}), 200
        elif ((comm_prog['status'] == 'stop') or (comm_prog['status'] == 'error')):
            task = ct.kickPy.apply_async(kwargs={'program_name': 'comm', 'arg1': robot_name})
            try:
                task.get(timeout=1)
                return 'error', 500 # タイムアウトしない=プログラム起動できなかった
            except TimeoutError:
                return jsonify({'task_id': task.id}), 200  # タイムアウトする=プログラム起動中
        else:
            return jsonify({'message': 'status of the program is stopping.'}), 200 
    else:
        return jsonify({'message': 'Redis is not running.'}), 200   

@app_flask.route('/stop_auto_py', methods=['POST'])
def stopAutoPy():
    # プログラム状態確認
    auto_status_str = redis_client_db0.hget('program_task', 'auto')
    auto_prog = json.loads(auto_status_str)

    if (auto_status_str):
        # auto.pyが実行中なら停止
        if (auto_prog['status'] == 'run'):
            ct.stopPy.apply_async(kwargs={'program_name': 'auto', 'PID': auto_prog['PID']})
            return jsonify({'message': 'Auto Task was stopped'}), 200
        else:
            return jsonify({'message': 'Task is not running'}), 200
    else:
        return jsonify({'message': 'Redis is not running'}), 200

@app_flask.route('/stop_man_py', methods=['POST'])
def stopManPy():
    # 起動中のプログラム確認
    man_status_str = redis_client_db0.hget('program_task', 'man')
    man_prog = json.loads(man_status_str)

    if (man_status_str):
        # man.pyが実行中なら停止
        if (man_prog['status'] == 'run'):
            ct.stopPy.apply_async(kwargs={'program_name': 'man', 'PID': man_prog['PID']})
            return jsonify({'message': 'Man program was stopped'}), 200
        else:
            return jsonify({'message': 'Man program is not running'}), 200
    else:
        return jsonify({'message': 'Redis is not running'}), 200


@app_flask.route('/stop_comm_py', methods=['POST'])
def stopCommPy():
    # プログラム状態確認
    comm_status_str = redis_client_db0.hget('program_task', 'comm')
    comm_prog = json.loads(comm_status_str)

    if (comm_status_str):
        # comm.pyが実行中なら停止
        if (comm_prog['status'] == 'run'):
            ct.stopPy.apply_async(kwargs={'program_name': 'comm', 'PID': comm_prog['PID']})
            return jsonify({'message': 'Comm Task was stopped'}), 200
        else:
            return jsonify({'message': 'Task is not running'}), 200
    else:
        return jsonify({'message': 'Redis is not running'}), 200

@app_flask.route('/get_py', methods=['POST'])
def getPy():
    try:
        # クライアントから送信されたコードを取得
        code = request.get_data(as_text=True)
        print(f"Received code for: {code}")
        # ディレクトリパスを取得し、ファイルにPythonコードを書き出す
        current_file_path = os.getcwd()
        file_path = os.path.join(current_file_path, 'auto.py')
        with open(file_path, 'w') as file:
            file.write(code)

        response = {"status": "success", "message": f"Code processed for"}
        return jsonify(response), 200
    finally:
        pass

    # except Exception as e:
    #     # エラーハンドリング
    #     return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app_flask.run(host='0.0.0.0', debug=False, port=4000, threaded=True)
