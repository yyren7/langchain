import time
import redis
import json

class RobotApiClient:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=1):
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
        self.redis_client.delete('robot_commands')

    def send_command(self, command, timeout=30):
        # コマンドを送信する
        try:
            self.redis_client.rpush('robot_commands', command)
            print(f"Sent command: {command}")

            # レスポンスを取得するまでブロッキング
            start_time = time.time()
            while True:
                response = self.redis_client.lpop('command_results')  # レスポンスを取得 (ブロックせず)
                if response:
                    response_str = response.decode('utf-8')
                    print(f"Received response: {response_str}")
                    break
                else:
                    # タイムアウトのチェック
                    elapsed_time = time.time() - start_time
                    if elapsed_time > timeout:
                        print(f"Error: Timeout while waiting for response for command: {command}")
                        break
                    # print("Waiting for response...")
                    time.sleep(0.001)  # レスポンスを待つ間、少し待機

            # コマンドを削除する (必要であればここに削除ロジックを追加)
            self.redis_client.lrem('robot_commands', 1, command)

        except redis.ConnectionError as e:
            print(f"Error: Could not connect to Redis. {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_status(self):
        # ステータスを取得
        status_data = self.redis_client.lindex('robot_status', 0)  # リストの最初の要素を取得
        if status_data:
            return json.loads(status_data)
        return None