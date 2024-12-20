import socket
from PySide2 import QtCore
from typing import Any
try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


class PLC_Thread(QtCore.QThread):
    # シグナルを設定
    __version__ = '1.0.0'
    sig_comm: Any = QtCore.Signal(dict)

    def __init__(self, parent=None, ip_address="localhost", port=5000):
        super(PLC_Thread, self).__init__()
        self.mutex = QtCore.QMutex()
        self.ip = ip_address
        self.port = port
        self.comm = {"address": self.ip + ":" + str(self.port)}
        self.buffer_size = 4096
        self.client = None
        self.stopped = True
        # self.init_flag = True

    def _init_socket(self, listen_num: int = 1):
        # ソケットの生成
        # self.init_flag = False

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # ソケットに割り当てるアドレスを設定。
        self.sock.settimeout(1)
        try:
            self.sock.bind((self.ip, int(self.port)))
        except Exception:
            self.ip = 'localhost'
            self.port = '5055'
            self.sock.bind((self.ip, int(self.port)))
        # ソケットを接続待ちの状態にする。
        self.sock.listen(listen_num)

    def _release_socket(self):
        logger.info('Relase Event')
        # self.sock.shutdown(socket.SHUT_RD)
        # self.sock.close()
        # del self.sock
        # logger.info(self.sock)

    def stop(self):
        with QtCore.QMutexLocker(self.mutex):
            # Prohibit access to other resources
            self.stopped = True

    def set_network(self, ip_address: str, port: str):
        self.ip = ip_address
        self.port = port

    # 返信用メソッド
    def send(self, send_data):
        if self.client is not None:
            self.client.send(send_data)

    def run(self):
        self.stopped = False
        # if self.init_flag:
        self._init_socket()

        while not self.stopped:
            try:
                self.client, address = self.sock.accept()
                # loop
            except Exception:
                continue

            self.client.settimeout(1)
            try:
                recv_data = self.client.recv(self.buffer_size)
            except Exception:
                continue
            # self.client.timeout(1)
            self.comm["recv_data"] = recv_data
            if recv_data == b"":
                pass
            else:
                self.sig_comm.emit(self.comm)  # シグナルでメッセージを飛ばす
        try:
            if self.client is not None:
                self.client.close()
            # self.sock.close()
        except Exception:
            # self.sock.close()
            pass
