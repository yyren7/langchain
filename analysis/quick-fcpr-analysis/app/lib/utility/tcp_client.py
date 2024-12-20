import socket
import select
import time

class TCPClient:
    def __init__(self, host, port, retry_limit=3, retry_delay=2, open_timeout=3, recv_timeout=0.001):
        self.host = host
        self.port = port
        self.retry_limit = retry_limit
        self.retry_delay = retry_delay
        self.open_timeout = open_timeout
        self.recv_timeout = recv_timeout
        self.sock = None

    def __del__(self):
        print('tcp_client.py is closed.')
        self.close()

    def connect(self):
        """サーバーへの接続を確立。リトライ機能付き。"""
        retries = 0
        while retries < self.retry_limit:
            try:
                self.sock = socket.create_connection((self.host, self.port), timeout=self.open_timeout)
                print(f"Connected to {self.host}:{self.port}")
                return True
            except Exception as e:
                retries += 1
                print(f"Connection failed (attempt {retries}/{self.retry_limit}): {e}")
                if retries < self.retry_limit:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
        print("Max retries reached. Failed to connect.")
        return False

    def send_message(self, message):
        """メッセージを送信する。"""
        if self.sock is None:
            print("Not connected. Attempting to reconnect...")
            if not self.connect():
                return
        
        try:
            print(f"Send: {message}")
            self.sock.sendall(message.encode())
        except Exception as e:
            print(f"Error during communication: {e}")
            self.close()

    def receive_message(self):
        """受信データをチェックする。"""
        if self.sock is None:
            print("Not connected.")
            return

        try:
            # selectで受信可能なデータがあるかチェックする
            ready_to_read, _, _ = select.select([self.sock], [], [], self.recv_timeout)
            if ready_to_read:
                data = self.sock.recv(1024)  # 1024バイトまで受信
                if data:
                    return data.decode()
                    # print(f"Received: {data.decode()}")
                else:
                    print("Connection closed by the server.")
                    self.close()
                    return None
            # else:
                # print("No data received within the recv_timeout period.")
        except Exception as e:
            print(f"Error during communication: {e}")
            self.close()

    def close(self):
        """接続を閉じる。"""
        if self.sock:
            print("Closing the connection")
            self.sock.close()
            self.sock = None

def main():
    client = TCPClient('192.168.250.14', 4001)

    # 接続を確立
    if client.connect():
        # メッセージを送信
        client.send_message('Hello World!')

        # 他の処理を行いながら受信をチェックする
        for _ in range(5):  # 例えば5回チェックする
            print("Performing other tasks...")
            client.receive_message()  # 受信処理
            time.sleep(1)  # 他の処理を行うためにスリープ
    
        # 接続を閉じる
        client.close()

if __name__ == '__main__':
    main()