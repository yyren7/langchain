from typing import Any
import numpy as np
import time
import copy
# IPC
from socket import socket, AF_INET, SOCK_DGRAM
import select

import subprocess
import os 

# To kill the process
import psutil
 
# To read .ini file
import configparser

# To read setting
from  setting  import (
                        SETTING_PATH,
                        SETTING_NAME
                        )

class PROCESS_CONTROLLER:
    def __init__(self):
        ##############################################################
        # 初期化
        ##############################################################
        print("Start to run process_controller.py")
        self.elapsed_time = 0
        self.referenced_time = 0
        
    def main(self):
        ##############################################################
        # 初期化
        ##############################################################
        IPC_node = IPC()  
        status_val = 0
        status_str = "INIT"
        timer_val = 10

        try:
            while 1:
                recv_data = IPC_node.recvData()  
                print("status: ", status_str)
                # print(status_val)
                print("recv: ", recv_data)
                time.sleep(0.1)
                
                ##############################################################
                # INIT
                ##############################################################
                if (status_val == 0):
                    status_str = "INIT"           
                    if (self.elapsed_time == 0):
                        print('Start to run program.')
                        # プログラム起動
                        stdbuf_cmd = ['stdbuf', '-oL']
                        cmd = ['python3', IPC_node.PROGRAM]
                        self.process = subprocess.Popen(stdbuf_cmd + cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)                    
                    elif (self.elapsed_time < timer_val ):  
                        print('Elapsed Time: ', self.elapsed_time)
                    elif (self.elapsed_time >= timer_val ): 
                        self.elapsed_time = 0
                        self.referenced_time = 0
                        # ステータス更新
                        status_val = 2
                    # 経過時間計測
                    self.elapsed_time = time.time() - self.referenced_time  
                    
                ##############################################################
                # IDLE
                ##############################################################                
                if (status_val == 1):
                    status_str = "IDLE" 
                    # if(recv_data == " start"):
                    if ("start" in recv_data):
                        # プログラム起動
                        print('Start to run program.')
                        # 標準出力を行バッファリングとする
                        stdbuf_cmd = ['stdbuf', '-oL']
                        cmd = ['python3', IPC_node.PROGRAM]
                        # 出力無し(出力有りにすると、プログラムが停止する不具合発生)
                        self.process = subprocess.Popen(stdbuf_cmd + cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False) # リスト形式:shell=False, 文字列形式:shell=True
                        # ステータス更新
                        status_val = 2
                    if ("reboot" in recv_data):
                        # プログラム再起動
                        print('Start to reboot program.')
                        cmd = ['sudo', 'reboot']
                        subprocess.Popen(cmd, shell=False)   
                        # ステータス更新
                        status_val = 0
                    if ("shutdown" in recv_data):
                        # プログラム再起動
                        print('Start to shutdown program.')
                        cmd = ['sudo', 'shutdown', 'now']
                        subprocess.Popen(cmd, shell=False)   
                        # ステータス更新
                        status_val = 0
                              
                ##############################################################
                # RUN
                ##############################################################                
                if (status_val == 2):
                    status_str = "RUN" 
                    print(recv_data)
                    # if(recv_data == " stop"):
                    if ("stop" in recv_data):
                        print('Stop program')
                        # プログラム終了
                        self.killProcess()
                        # ステータス更新
                        status_val = 1
                    if ("reboot" in recv_data):
                        # プログラム再起動
                        print('Start to reboot program.')
                        cmd = ['sudo', 'reboot']
                        subprocess.Popen(cmd, shell=False)   
                        # ステータス更新
                        status_val = 0
                    if ("shutdown" in recv_data):
                        # プログラム再起動
                        print('Start to shutdown program.')
                        cmd = ['sudo', 'shutdown', 'now']
                        subprocess.Popen(cmd, shell=False)   
                        # ステータス更新
                        status_val = 0
                        
        except KeyboardInterrupt:
            print("Handling KeyboardInterrupt")
            # プログラム終了
            self.killProcess()
        
    def killProcess(self):
        try:
            result = subprocess.check_output('ps aux | grep "[p]ython3 main.py"', shell=True)         # コマンドの結果取得
            decoded_result = result.decode()                                                          # デコード
            replaced_result = decoded_result.replace('\n', ' ')                                       # \nを空白で置き換え
            splited_result = replaced_result.split(' ')                                               # 空白で分割
            deleted_result = [data for data in splited_result if(data != '')]                         # 空白を要素を削除
            PID_str = [deleted_result[i+1] for i, data in enumerate(deleted_result) if(data == 'pi')] # 対象プログラムのPID取得
            # プロセス削除
            process = []
            for i, PID_i in enumerate(PID_str):
                process.append(psutil.Process(int(PID_i)))
                process[i].kill() 
        except:
            print("プログラムが起動していません。")

class IPC:
    def __init__(self):
        ############### Input ###############
        ########## 設定ファイル読込み
        self.current_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
        self.config = configparser.ConfigParser()
        self.config.read(self.current_dir + SETTING_PATH + SETTING_NAME)  
        ########## プロセス間通信
        # self.SEND_BUFFER_SIZE = 160
        # self.APPEND_ROW_DATA = u'\x00'
        self.DST_IP_ADDRRESS = self.config['settings']['dst_plc_ip_address']
        self.DST_PORT = int(self.config['settings']['dst_plc_port'])
        self.SRC_IP_ADDRRESS = self.config['settings']['src_ip_address']
        self.PROGRAM = self.config['settings']['program']
        self.SRC_PORT = 9000
        self.BUFFER_SIZE = 20  
        # self.BUFFER_SIZE = 1024  

        # IPC設定
        self.publisher = socket(AF_INET, SOCK_DGRAM)
        self.subscriber = socket(AF_INET, SOCK_DGRAM)
        self.subscriber.bind((self.SRC_IP_ADDRRESS, self.SRC_PORT))

    def sendData(self, recv_row_data, append_str):
        # print("Running socket send()")
        # UDP送信データ作成
        # recv_revised_data = recv_row_data.decode().replace(u'\x00', u'') + append_str        
        # recv_revised_data = append_str        
        # 送信データを0埋め
        # append_send_data = self.APPEND_ROW_DATA * (self.SEND_BUFFER_SIZE - len(recv_revised_data))
        # send_data = recv_revised_data + append_send_data
        # バイナリーデータに変換
        # pickled_data = send_data.encode()
        # 送信
        # self.publisher.sendto(pickled_data, (self.DST_IP_ADDRRESS, self.DST_PORT))
        print(append_str.encode())
        self.publisher.sendto(append_str.encode(), (self.DST_IP_ADDRRESS, self.DST_PORT))

    def recvData(self):
        # print("Running socket recv()")
        # received_data, addr = self.subscriber.recvfrom(self.BUFFER_SIZE)
        # output_data = pickle.loads(received_data) #バイナリデータを復元
        
        # タイムアウトの設定
        timeout_in_seconds = 5.0
        # データ受信
        ready = select.select([self.subscriber], [], [], timeout_in_seconds)
        # サーバーからのレスポンスがあれば
        if ready[0]:
            received_data, addr = self.subscriber.recvfrom(self.BUFFER_SIZE)
            # received_data = self.subscriber.recv(self.BUFFER_SIZE)
            # print(received_data)
            return received_data.decode()    
        else:
            return None

if __name__ == '__main__':
    node = PROCESS_CONTROLLER()
    node.main()