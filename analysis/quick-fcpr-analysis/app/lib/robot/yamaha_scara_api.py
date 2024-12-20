# -*- coding : UTF-8 -*-

import RPi.GPIO as GPIO
from socket import *
import select
import time
from typing import Tuple, List, Union, Optional

# To read .ini file
import configparser

#############################################################
# グローバル変数定義
#############################################################  
X = 0
Y = 1
Z = 2
R = 3
XYZ_MAX_ACC = 7500
XYZ_MAX_VEL = 1000
CHECK_MOVING_DIFF = 0.1 

class RobotApi():   
    def __init__(self, dst_ip_address: str, dst_port: str, dev_port: str, baurate: str):  
        ##############################################################
        # ロボット状態通知用変数定義(数値)
        ##############################################################    
        self.current_pos     :list[float] = [0.0] * 4
        self.pre_current_pos :list[float] = [0.0] * 4
        self.error_id        :int = 0   
        ##############################################################
        # ロボット状態通知用変数定義(フラグ)
        ##############################################################   
        self.error       :bool = False     
        self.servo       :bool = False
        self.emerge      :bool = False
        self.origin      :bool = False 
        self.moving      :bool = False 
        self.dragging    :bool = False 
        self.arrived     :bool = False 
        self.robot_mode  :int = 5 
        self.waiting_end :bool = False # スカラ専用(END命令無視用フラグ)
        ##############################################################
        # ロボット接続開始
        ##############################################################  
        self.openRobot(dst_ip_address, dst_port)
        
    def __del__(self):
        ##############################################################
        # ロボット接続解除
        ##############################################################  
        self.closeRobot()
        print("Disconnected.")    

    #############################################################
    # ロボット共通関数
    #############################################################
    def openRobot(self, dst_ip_address: str, dst_port: str) -> None:
        """ ロボット通信を開始
        """
        # ソケットオブジェクトの作成
        print("Start to create socket.")
        self.tcp_client :socket = socket(AF_INET, SOCK_STREAM)
        print("Finished to create socket.")
        # ロボットサーバに接続
        print("Start to connet robot.")
        self.tcp_client.connect((dst_ip_address, int(dst_port)))
        print("Finished to connet robot.")
        print("Connected to: " + dst_ip_address)

    def closeRobot(self) -> None:
        """ ロボット通信を解除
        """
        # self.tcp_client.close()

    def getRobotStatus(self) -> None:
        """ ロボット状態を取得
        """
        ##############################################################
        # ロボット状態取得
        ##############################################################
        self.getDo0Base()
        self.origin = True
        ##############################################################
        # 現在地の直交座標取得
        ##############################################################
        self.current_pos = self.getCurrentPosBase()
        ##############################################################
        # Moving確認 (デジタルIOからは取得できないので)
        ##############################################################
        # 現在位置を1度でも取得していれば
        if (self.pre_current_pos == self.current_pos):
            # ループ間における現在位置の差分取得
            diff_pos = [abs(x - y) for (x, y) in zip(self.pre_current_pos, self.current_pos)]
            # 差分が設定値以上なら
            if ((diff_pos[X] >= CHECK_MOVING_DIFF) or
                (diff_pos[Y] >= CHECK_MOVING_DIFF) or
                (diff_pos[Z] >= CHECK_MOVING_DIFF) or
                (diff_pos[R] >= CHECK_MOVING_DIFF)):
                self.moving = True
            else: 
                self.moving = False
        self.pre_current_pos = self.current_pos
        ##############################################################
        # エラーステータス取得(エラー発生時のみ)
        ##############################################################
        if (self.error == True): self.error_id = self.getAlarmBase().replace('.','')
        else                   : self.error_id = 0

    def setTool(self, tool_no: int) -> None:
        """ ツール座標系設定
        tool_no : int
            ツール座標番号
        """
        # self.setHand(hand_no=tool_no)
        pass

    def getCurrentJoint(self) -> None:
        """ 現在地のジョイント座標取得
        """
        pass

    def waitArrive(self, target_pos: List[float], width: float) -> None:
        """ ロボットの到着まで待機
        Parameters
        ----------
        target_pos : list[float]
            X~R目標位置[mm]
        width : float
            位置決め幅[mm]
        """
        pass

    def setRobotParam(self, vel: float, acc: float, dec: float) -> None:
        """ ロボットのパラメータ変更
        Parameters
        ----------
        vel : float
            変更後速度[mm/s]
        acc : float
            変更後加速度[mm/s^2]
        dec : float
            変更後加速度[mm/s^2]
        """
        pass
        
    def stopRobot(self) -> None:
        """ ロボットを一時停止
        """
        self.waiting_end = False
        self.stopRobotBase()

    def moveAbsolutePtp(self, x: float, y: float, z: float, r: float, vel: int=100, acc: int=100, dec: int=100) -> None:
        """ ロボット絶対移動(PTP)
        Parameters
        ----------
        x : float
            目標x座標[mm]
        y : float
            目標y座標[mm]
        z : float
            目標z座標[mm]
        r : float
            目標r座標[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """ 
        self.moveAbsolutePtpBase(x, y, z, r, vel, acc, dec)

    def moveAbsoluteLine(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, vel: int=100, acc: int=100, dec: int=100) -> None:
        """ ロボット絶対移動(直線補間)
        Parameters
        ----------
        x : float
            目標x座標[mm]
        y : float
            目標y座標[mm]
        z : float
            目標z座標[mm]
        r : float
            目標r座標[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """        

        # %に換算
        # vel_line = int((vel/XYZ_MAX_VEL)*100)     
        # acc_line = int((acc/XYZ_MAX_ACC)*9800*100)
        # dec_line = int((acc/XYZ_MAX_ACC)*9800*100)


        print("############################## x  : ", x)    
        print("############################## y  : ", y)    
        print("############################## z  : ", z)  
        print("############################## r  : ", rz)          
        print("############################## vel: ", vel)    
        print("############################## acc: ", acc)    
        print("############################## dec: ", dec)    
    
        
        self.moveAbsoluteLineBase(x, y, z, rz, vel, acc, dec)
        self.waiting_end = True
        self.arrived = False

    def moveRelative(self, x: float, y: float, z: float, r: float, vel: int=100, acc: int=100, dec: int=100) -> None:
        """ ロボット相対移動
        Parameters
        ----------
        x : float
            x座標移動量[mm]
        y : float
            y座標移動量[mm]
        z : float
            z座標移動量[mm]
        r : float
            r座標移動量[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """
        print(x)
        print(y)
        print(z)
        print(r)
        print(vel)
        print(acc)
        print(dec)
        self.moveRelativeBase(x, y, z, r, vel, acc, dec)

    def moveOrigin(self) -> None:
        """ 原点復帰
        """ 
        pass

    def setServoOn(self):
        """ サーボ電源ON
        """
        self.setServoOnBase()

    def setServoOff(self):
        """ サーボ電源OFF
        """
        self.setServoOffBase()

    def resetError(self):
        """ エラーリセット
        """
        self.setServoOff()
        self.resetErrorBase()
        self.waiting_end = False

    def setRightForm(self) -> None:
        """ 右手系に変換
        """
        self.setRightFormBase()

    def setLeftForm(self) -> None:
        """ 左手系に変換
        """
        self.setLeftFormBase()

    def moveInching(self, width: int, axis_char_str: str, direction_char_str: str) -> None:
        """ 手動移動：インチング
        Parameters
        ----------
        width : int
            インチング幅[mm]　最大=10.000mm
        axis_char_str : str
            軸(ex. "x")
        direction_char_str : str
            回転方向(ex. "+")
        """
        self.moveInchingBase(width, axis_char_str, direction_char_str)

    def moveJog(self, axis_char_str: str, direction_char_str: str) -> None:
        """ 手動移動：ジョグ
        Parameters
        ----------
        axis_char_str : str
            軸(ex. "x")
        direction_char_str : str
            回転方向(ex. "+")
        """
        self.moveJogBase(axis_char_str, direction_char_str)
        self.waiting_end = True
        self.arrived = False
        
    def continueJog(self, axis_char_str: str, direction_char_str: str) -> None:
        """ ジョグ継続
        """
        self.continueJogBase()
        
    def stopJog(self) -> None:
        """ ジョグ継続
        """
        self.stopJogBase()

    def printRobotStatus(self) -> None:
        """ 変数表示(デバッグ用)
        """
        print("##########################  Status  ##############################################")
        print('X  = {0:.3f}'.format(self.current_pos[X]))
        print('Y  = {0:.3f}'.format(self.current_pos[Y]))
        print('Z  = {0:.3f}'.format(self.current_pos[Z]))
        print('R  = {0:.3f}'.format(self.current_pos[R]))
        print("emerge -> " + str(self.emerge) + ", " + "error -> ", str(self.error) + ", " + "servo -> ", str(self.servo) + ", " + "moving -> " + str(self.moving) + ", " + "origin -> ", str(self.origin) + ", " + "arrived -> ", str(self.arrived) + ", " + "dragging -> ", str(self.dragging))
        print("error id = ", self.error_id)
        print("##################################################################################")

    def getJoint2Pos(self) -> None:
        """ ジョイント座標系を直交座標系に変換
        """ 
        pass
    
    def getPos2joint(self) -> None:
        """ 直交座標系をジョイント座標系に変換
        """ 
        pass
    
    def getInput(self) -> None:
        """ ポート入力状態参照
        """
        pass
    
    def readyRobot(self) -> None:
        """ 運転準備時動作
        """ 
        # 制御権があれば
        if (self.getModeStatusBase() == True): self.setServoOn()
        else: pass
    #############################################################
    # ロボット固有関数
    #############################################################
    def sendCommandBase(self, cmd_str):
        """ 指令送信＆受信
        Parameters
        ----------
        cmd_str : str
            ロボットへ送信するコマンド(ex."@?ORIGIN\r\n")
        Returns
        -------
        joined_recv_str : str
            ロボットからの返答(ex."0 1,1,0,1\r\n")
        """
        # time.sleep(0.005)
        ########################### 変数定義 #############################
        cmd_val = ''.join(cmd_str) # 送信用データ
        raw_recv_ary_str = [] # 受信データ
        received_end = False
        ########################### 設定 #############################
        buffer_size = 1024
        timeout_in_seconds = 5.0
        self.tcp_client.setblocking(False) # Non-blockingモードに設定
        ########################### データ送信 #############################
        self.tcp_client.send(cmd_val.encode())
        ########################### データ受信 #############################
        while 1:
            # サーバーからのレスポンス格納し、タイムアウトを設定
            ready = select.select([self.tcp_client], [], [], timeout_in_seconds)
            # サーバーからのレスポンスがあれば
            if ready[0]:
                raw_recv_str = self.tcp_client.recv(buffer_size).decode().replace("\r\n", "")
                # print("recv_raw", raw_recv_str)
                # ロボットと初回通信確立後に通信するなら
                if (raw_recv_str != "Welcome to RCX340"):
                    # print(raw_recv_str)
                    # Move送信後のEND受信待ち状態で、ロボットバッファにENDがあれば
                    if (self.waiting_end == True) and (("END" in raw_recv_str) or (received_end == True)):
                        # print("################################# 入った ##########################")
                        received_end = True
                        # レスポンスに"OK"が含まれるなら
                        if ("OK" in raw_recv_str):
                            # 内部バッファの中身を初期化
                            joined_recv_str = ""
                            self.waiting_end = False
                            received_end = False
                            self.arrived = True
                            # print("################################# OK中 ##########################")
                            break
                        else :
                            # 何もしない
                            pass
                    # Move送信後のEND受信待ち状態では無いなら
                    else: 
                        # レスポンスに"OK"が含まれるなら
                        if ("OK" in raw_recv_str):
                            # OK前に空白を付けて、内部バッファに格納
                            index = raw_recv_str.find("OK")
                            raw_recv_ary_str.append(raw_recv_str[:index] + " " +raw_recv_str[index:])
                            joined_recv_str = "".join(raw_recv_ary_str)
                            break
                        # レスポンスに"END"が含まれるなら
                        elif ("END" in raw_recv_str):
                            # END前に空白を付けて、内部バッファに格納
                            index = raw_recv_str.find("END")
                            raw_recv_ary_str.append(raw_recv_str[:index] + " " +raw_recv_str[index:])
                            joined_recv_str = "".join(raw_recv_ary_str)
                            break
                        else :
                            # そのまま、内部バッファに格納
                            raw_recv_ary_str.append(raw_recv_str)
                            joined_recv_str = "".join(raw_recv_ary_str)
                                        
            else :
                print("Connection for robot is timed out.")
                self.error = True
                # self.error_id = joined_recv_str[3:]
                self.error_id = 9999 #仮の数値
                break

        return joined_recv_str
        ###################################################################

    def sendCommandOnlyBase(self, cmd_str: str) -> str:
        """ 指令送信のみ
        Parameters
        ----------
        cmd_str : str
            ロボットへ送信するコマンド(ex."@ORIGIN\r\n")
        Returns
        -------
        joined_recv_str : str
            ロボットからの返答(ex."0 1,1,0,1\r\n")
        """
        # time.sleep(0.005)
        ########################### 変数定義 #############################
        cmd_val = ''.join(cmd_str) # 送信用データ
        row_recv_ary_str = [] # 受信データ
        ########################### 設定 #############################
        buffer_size = 1024
        timeout_in_seconds = 10
        self.tcp_client.setblocking(False) # Non-blockingモードに設定
        ########################### データ送信 #############################
        self.tcp_client.send(cmd_val.encode())
        ########################### データ受信 #############################
        while 1:
            # サーバーからのレスポンス格納し、タイムアウトを設定
            ready = select.select([self.tcp_client], [], [], timeout_in_seconds)
            # サーバーからのレスポンスがあれば
            if ready[0]:
                raw_recv_str = self.tcp_client.recv(buffer_size).decode().replace("\r\n", "")
                # ロボットと初回通信確立後に通信するなら
                if (raw_recv_str != "Welcome to RCX340"):
                    row_recv_ary_str.append(raw_recv_str)
                    joined_recv_str = "".join(row_recv_ary_str)
                    # レスポンスに"RUN"があれば
                    if ("RUN" in raw_recv_str):
                        # print("############# RUN #####################################################")
                        break
            else :
                print("Connection for robot is timed out.")
                self.error = True
                self.error_id = 9999
                break
        return joined_recv_str
        ###################################################################

    def convertWord2BitBase(self, value: int, index :int) -> int:
        """ wordをbitに分解
        Parameters
        ----------
        value : int
            変換対象の数値
        index : int
            取り出す対象bit番号(0~15)
        -------
        bit : int
            対象bit値(0~1)
        """
        bit = (value >> index) & (0xFF >> (8 - 1))
        return bit 

    def stopRobotBase(self) -> None:
        """ P.157　プログラムを一時停止する
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('STOP')                                        # コマンド
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def moveAbsolutePtpBase(self, x: float, y: float, z: float, r: float, vel: int=100, acc: int=100, dec: int=100) -> None:
        """ P.181  ロボット絶対移動(直線)
        Parameters
        ----------
        x : float
            目標x座標[mm]
        y : float
            目標y座標[mm]
        z : float
            目標z座標[mm]
        r : float
            目標r座標[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """ 
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('MOVE ')                                       # コマンド
        cmd_str.append('P,')                                          # PTP移動
        cmd_str.append(str(x)+' ')                                    # 目標x座標[mm]
        cmd_str.append(str(y)+' ')                                    # 目標y座標[mm]
        cmd_str.append(str(z)+' ')                                    # 目標z座標[mm]
        cmd_str.append(str(r)+' ')                                    # 目標r座標[°]
        cmd_str.append(str(0.0)+' ')                                  # 目標5軸目座標[°]
        cmd_str.append(str(0.0)+',')                                  # 目標6軸目座標[°]
        cmd_str.append('S='+str(vel)+',')                             # 速度[%]
        cmd_str.append('ACC='+str(acc)+',')                           # 加速度[%]
        cmd_str.append('DEC='+str(dec)+',')                           # 減速度[%]
        cmd_str.append('CONT')                                        # CONT指定（連結動作）
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandOnlyBase(cmd_str)                      # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def moveAbsoluteLineBase(self, x: float, y: float, z: float, r: float, vel: int=100, acc: int=100, dec: int=100) -> None:
        """ P.181  ロボット絶対移動(直線)
        Parameters
        ----------
        x : float
            目標x座標[mm]
        y : float
            目標y座標[mm]
        z : float
            目標z座標[mm]
        r : float
            目標r座標[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """        
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('MOVE ')                                       # コマンド
        cmd_str.append('L,')                                          # 直線移動
        cmd_str.append(str(x)+' ')                                    # 目標x座標[mm]
        cmd_str.append(str(y)+' ')                                    # 目標y座標[mm]
        cmd_str.append(str(z)+' ')                                    # 目標z座標[mm]
        cmd_str.append(str(r)+' ')                                    # 目標r座標[°]
        cmd_str.append(str(0.0)+' ')                                  # 目標5軸目座標[°]
        cmd_str.append(str(0.0)+',')                                  # 目標6軸目座標[°]
        cmd_str.append('S='+str(vel)+',')                             # 速度[%]
        cmd_str.append('ACC='+str(acc)+',')                           # 加速度[%]
        cmd_str.append('DEC='+str(dec)+',')                           # 減速度[%]
        # cmd_str.append('STOPON DI(20)=1')                           # CONT指定（連結動作）
        cmd_str.append('CONT')                                        # CONT指定（連結動作）
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandOnlyBase(cmd_str)                  # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        print(recv_str)
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def moveRelativeBase(self, x: float, y: float, z: float, r: float, vel: int=100, acc: int=100, dec: int=100) -> None:
        """ P.198　ロボット相対移動
        Parameters
        ----------
        x : float
            x座標移動量[mm]
        y : float
            y座標移動量[mm]
        z : float
            z座標移動量[mm]
        r : float
            r座標移動量[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('MOVEI ')                                      # コマンド
        cmd_str.append('P,')                                          # PTP
        cmd_str.append(str(x)+' ')                                    # 目標x座標[mm]
        cmd_str.append(str(y)+' ')                                    # 目標y座標[mm]
        cmd_str.append(str(z)+' ')                                    # 目標z座標[mm]
        cmd_str.append(str(r)+' ')                                    # 目標r座標[°]
        cmd_str.append(str(0.0)+' ')                                  # 目標5軸目座標[°]
        cmd_str.append(str(0.0)+',')                                  # 目標6軸目座標[°]
        cmd_str.append('S='+str(vel)+',')                             # 速度[%]
        cmd_str.append('ACC='+str(acc)+',')                           # 加速度[%]
        cmd_str.append('DEC='+str(dec))                               # 減速度[%]
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                      # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def moveOriginBase(self) -> None:
        """ P.209　原点復帰
        """ 
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('ORIGIN')                                      # コマンド
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandOnlyBase(cmd_str)                      # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def setServoOnBase(self):
        """ P.256 サーボ電源ON
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('SERVO')                                       # コマンド
        cmd_str.append(' ON')                                         # ON
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def setServoOffBase(self):
        """ P.256 サーボ電源OFF
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('SERVO')                                       # コマンド
        cmd_str.append(' OFF')                                        # OFF
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def resetErrorBase(self):
        """ P.429 アラームリセット
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('ALMRST')                                      # コマンド
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        self.error_id = 0                                             # id初期化
        #############################################################

    def moveInchingBase(self, width: int, axis_char_str: str, direction_char_str: str) -> None:
        """ P.452 手動移動：インチング
        Parameters
        ----------
        width : int
            インチング幅[mm]　最大=10.000mm
        axis_char_str : str
            軸(ex. "x")
        direction_char_str : str
            回転方向(ex. "+")
        """
        ##############################################################
        # 処理
        ##############################################################
        self.setInchingWidthBase(width)                               # インチング幅設定
        if   (axis_char_str == "x"):  axis_val_str = "1"              # 1軸目設定
        elif (axis_char_str == "y"):  axis_val_str = "2"              # 2軸目設定
        elif (axis_char_str == "z"):  axis_val_str = "3"              # 3軸目設定
        elif (axis_char_str == "r"): axis_val_str  = "4"              # 4軸目設定
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('INCHXY ')                                     # コマンド
        cmd_str.append(axis_val_str)                                  # 軸番号 -> 1～6
        cmd_str.append(direction_char_str)                            # 移動方向 -> +／-
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                      # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        #############################################################

    def moveJogBase(self, axis_char_str: str, direction_char_str: str) -> None:
        """ P.453 手動移動：ジョグ
        Parameters
        ----------
        axis_char_str : str
            軸(ex. "x")
        direction_char_str : str
            回転方向(ex. "+")
        """
        ##############################################################
        # 処理
        ##############################################################
        if   (axis_char_str == "x"):  axis_val_str = "1"              # 1軸目設定
        elif (axis_char_str == "y"):  axis_val_str = "2"              # 2軸目設定
        elif (axis_char_str == "z"):  axis_val_str = "3"              # 3軸目設定
        elif (axis_char_str == "r"):  axis_val_str = "4"              # 4軸目設定
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('JOGXY ')                                      # コマンド
        cmd_str.append(axis_val_str)                                  # 軸番号 -> 1～6
        cmd_str.append(direction_char_str)                            # 移動方向 -> +／-
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandOnlyBase(cmd_str)                      # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        #############################################################

    def setHand(self, hand_no: int) -> None:
        """ P.118　ハンドデータを切り替える
        Parameters
        ----------
        hand_no : int
            ハンド番号
        """
        ##############################################################
        # 処理
        ##############################################################
        if   (hand_no == -1):  hand_str = 'OFF'                       # 指定なし
        elif (hand_no >=  0):  hand_str = 'H' + str(hand_no)          # 指定あり
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('CHANGE ')                                     # コマンド
        cmd_str.append(hand_str)                                      # ハンド番号
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                  # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def setContPulseBase(self, pulse: int, axis_char_str: str = 'all') -> None:
        """ P.118　ロボットのCONTパルスパラメータを設定／取得する
        Parameters
        ----------
        axis_char_str : str
            対象軸(ex."x")
        pulse : int
            公差[pulse]
        """
        ##############################################################
        # 処理
        ##############################################################
        if   (axis_char_str == "x"):  axis_val_str = "1"              # 1軸目設定
        elif (axis_char_str == "y"):  axis_val_str = "2"              # 2軸目設定
        elif (axis_char_str == "z"):  axis_val_str = "3"              # 3軸目設定
        elif (axis_char_str == "r"): axis_val_str = "4"              # 4軸目設定
        elif (axis_char_str == "all"): axis_val_str = "100"           # 全軸設定
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                      # 初期化
        cmd_str.append('@')                                               # ヘッダー
        cmd_str.append('CONTPLS ')                                        # コマンド
        if (axis_val_str != "100"):cmd_str.append("("+axis_val_str+")=")  # 対象軸
        cmd_str.append(str(pulse))                                        # 設定値[pulse]
        cmd_str.append('\r')                                              # CR
        cmd_str.append('\n')                                              # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def getDo0Base(self) -> None:
        """ P.137　パラレルポートに出力または出力状態を取得する
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@?')                                          # ヘッダー
        cmd_str.append('DO')                                          # コマンド
        cmd_str.append('0()')                                         # ポート
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                      # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        if (recv_str_ary[0] != "") and ("NG" not in recv_str_ary[0]):
            # print(recv_str_ary[0])
            self.emerge = True if self.convertWord2BitBase(value=int(recv_str_ary[0]), index=0) == 1 else False  # 非常停止
            # self.cpu    = True if self.convertWord2BitBase(value=int(recv_str_ary[0]), index=1) == 1 else False  # CPU OK
            self.servo  = True if self.convertWord2BitBase(value=int(recv_str_ary[0]), index=2) == 1 else False  # サーボON出力
            self.error  = True if self.convertWord2BitBase(value=int(recv_str_ary[0]), index=3) == 1 else False  # アラーム出力

    def getDo1Base(self) -> None:
        """ P.137　パラレルポートに出力または出力状態を取得する
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@?')                                          # ヘッダー
        cmd_str.append('DO')                                          # コマンド
        cmd_str.append('1()')                                         # ポート
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                      # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        # self.auto      = True if self.convertWord2BitBase(value=int(recv_str_ary[0]), index=0) == 1 else False # 自動モード出力
        # self.origin    = True if self.convertWord2BitBase(value=int(recv_str_ary[0]), index=1) == 1 else False # 原点復帰完了
        # self.seq_run   = True if self.convertWord2BitBase(value=int(recv_str_ary[0]), index=2) == 1 else False # シーケンスプログラム実行中
        # self.run       = True if self.convertWord2BitBase(value=int(recv_str_ary[0]), index=3) == 1 else False # ロボットプログラム運転中
        # self.reset     = True if self.convertWord2BitBase(value=int(recv_str_ary[0]), index=4) == 1 else False # プログラムリセット状態出力
        # self.warning   = True if self.convertWord2BitBase(value=int(recv_str_ary[0]), index=5) == 1 else False # ワーニング出力

    def setLeftFormBase(self):
        """ P.167　左手座標系に変更 
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('LEFTY')                                       # コマンド
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def setOutPosBase(self, pulse: int, axis_char_str: str = 'all') -> None:
        """ P.211　アウト有効位置設定 
        Parameters
        ----------
        axis_char_str : str
            対象軸(ex."x")
        pulse : int
            公差[pulse]
        """
        ##############################################################
        # 処理
        ##############################################################
        if   (axis_char_str == "x"):  axis_val_str = "1"              # 1軸目設定
        elif (axis_char_str == "y"):  axis_val_str = "2"              # 2軸目設定
        elif (axis_char_str == "z"):  axis_val_str = "3"              # 3軸目設定
        elif (axis_char_str == "r"): axis_val_str = "4"              # 4軸目設定
        elif (axis_char_str == "all"): axis_val_str = "100"           # 全軸設定
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                      # 初期化
        cmd_str.append('@')                                               # ヘッダー
        cmd_str.append('OUTPOS ')                                         # コマンド
        if (axis_val_str != "100"):cmd_str.append("("+axis_val_str+")=")  # 対象軸
        cmd_str.append(str(pulse))                                        # 設定値[pulse]
        cmd_str.append('\r')                                              # CR
        cmd_str.append('\n')                                              # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def setRightFormBase(self):
        """ P.250　右手座標系に変更 
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('RIGHTY')                                      # コマンド
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def setToleranceBase(self, pulse: int, axis_char_str: str = 'all') -> None:
        """ P.284 公差パラメータ設定
        Parameters
        ----------
        axis_char_str : str
            対象軸(ex."x")
        pulse : int
            公差[pulse]
        """
        ##############################################################
        # 処理
        ##############################################################
        if   (axis_char_str == "x"):  axis_val_str = "1"              # 1軸目設定
        elif (axis_char_str == "y"):  axis_val_str = "2"              # 2軸目設定
        elif (axis_char_str == "z"):  axis_val_str = "3"              # 3軸目設定
        elif (axis_char_str == "r"): axis_val_str = "4"              # 4軸目設定
        elif (axis_char_str == "all"): axis_val_str = "100"           # 全軸設定
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                      # 初期化
        cmd_str.append('@')                                               # ヘッダー
        cmd_str.append('TOLE ')                                           # コマンド
        if (axis_val_str != "100"):cmd_str.append("("+axis_val_str+")=")  # 対象軸
        cmd_str.append(str(pulse))                                        # 設定値[pulse]
        cmd_str.append('\r')                                              # CR
        cmd_str.append('\n')                                              # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def setWeightBase(self, weight: int) -> None:
        """ P.292　先端質量（g）パラメータを設定
        Parameters
        ----------
        weight : int
            公差(mm)
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('WEIGHTG ')                                    # コマンド
        cmd_str.append(str(weight))                                   # 設定値[g]
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def getCurrentPosBase(self) -> List[float]:
        """ P.296 アーム現在位置を直交座標で取得
        Returns
        -------
        pos : list[str]
            1~6軸(0=x,1=y,2=z,3=r)の現在位置
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@?')                                          # ヘッダー
        cmd_str.append('WHRXY')                                       # コマンド
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                      # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        # if (recv_str_ary[0] != "") and ("END" not in recv_str_ary[0]):
        if (recv_str_ary[0] != "") and ("NG" not in recv_str_ary[0]):
            pos = list(map(float, recv_str_ary[:6]))                      # 1~6軸目座標 キャスト済(str -> flot)
            return (pos)
        #############################################################

    def getOriginStatusBase(self) -> bool:
        """ P.434 原点復帰状態取得
        Returns
        -------
        result : bool
            False=未了／True=完了
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@?')                                          # ヘッダー
        cmd_str.append('ORIGIN')                                     # コマンド
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        status = recv_str_ary[0]                                      # ロボット原点復帰状態 -> 0:未了／1:完了
        if(status == "1"): result = True
        else:              result = False
        return result
        #############################################################

    def getServoStatusBase(self) -> bool:
        """ P.435 サーボ状態取得
        Returns
        -------
        result : bool
            False=未了／True=完了
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@?')                                          # ヘッダー
        cmd_str.append('SERVO')                                       # コマンド
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        status = recv_str_ary[0]                                      # ロボットサーボ状態 -> 0:未了／1:完了
        if(status == "1"): result = True
        else:              result = False
        return result
        #############################################################

    def getAlarmBase(self) -> str:
        """ P.446 アラーム状態取得
        Returns
        -------
        NG_code : str
            0.0=正常, その他=異常(詳細は"RCX340/RCX320　ユーザーマニュアル")
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@?')                                          # ヘッダー
        cmd_str.append('ALM')                                         # コマンド
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        NG_code = recv_str_ary[0]
        return NG_code
        #############################################################

    def setInchingWidthBase(self, width: int) -> None:
        """ P.429 インチング移動距離変更
        Parameters
        ----------
        width : int
            インチング幅[mm]　最大=10.000mm
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@')                                           # ヘッダー
        cmd_str.append('IDIST ')                                      # コマンド
        cmd_str.append(str(int(width*1000)))                          # インチング幅 -> MAX:10.000mm
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        pass
        #############################################################

    def getModeStatusBase(self) -> bool:
        """ P.435 サーボ状態取得
        Returns
        -------
        result : bool
            False=未了／True=完了
        """
        ##############################################################
        # 送信
        ##############################################################
        cmd_str = []                                                  # 初期化
        cmd_str.append('@?')                                          # ヘッダー
        cmd_str.append('MODE')                                        # コマンド
        cmd_str.append('\r')                                          # CR
        cmd_str.append('\n')                                          # LF
        ##############################################################
        # 受信
        ##############################################################
        recv_str = self.sendCommandBase(cmd_str)                          # 結果受け取り
        recv_str_ary = recv_str.split(" ")                            # 分割
        ##############################################################
        # 処理
        ##############################################################
        status = recv_str_ary[0]                                      # ロボットサーボ状態 -> 0:手動モード／1:自動モード（ 制御権：プログラミングボックス）／2:自動モード（ 制御権開放）／-1:不正モード
        if(status == "2"): result = True
        else:              result = False
        return result
        #############################################################

    def continueJogBase(self) -> None:
        """ P.453 手動移動：ジョグ動作継続
        """       
        ########################### データ送信 #############################
        self.tcp_client.send(b'\x16\x0d\x0a')   
        time.sleep(0.05)
        # self.sendSYNCommand()
        ###################################################################

    def stopJogBase(self) -> None:
        """ P.453 手動移動：ジョグ動作終了
        """
        # ########################### データ送信 #############################
        self.tcp_client.send(b'\x03\x0d\x0a')
        # ###################################################################


if __name__ == '__main__':
    node = RobotApi('192.168.250.101', 23, '/dev/ttyUSB0', 115200)
    
    ##############################################################
    # 鈴木さん実験用
    ##############################################################  
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(14, GPIO.OUT)  
    # GPIO.output(14, 0)
    # node.sendCommandBase('@LEFTY\r\n')
    # node.sendCommandBase('@SHIFT S0\r\n')
    # node.sendCommandBase('@WEIGHTG 3560\r\n')
    # node.sendCommandBase('@ACCEL 100\r\n')
    # node.sendCommandBase('@DECEL 100\r\n')
    # node.sendCommandBase('@SPEED 100\r\n')
    # GPIO.output(14, 1)
    # test1 = node.sendCommandBase('@MOVE P,P1,S=100,ACC=100,DEC=100\r\n')
    # test1 = node.sendCommandBase('@MOVE L,P1,S=100,ACC=100,DEC=100\r\n')
    # print(test1)
    # test2 = node.sendCommandBase('@MOVE P,P0,S=100,ACC=100,DEC=100\r\n')
    # test2 = node.sendCommandBase('@MOVE L,P0,S=100,ACC=100,DEC=100\r\n')
    # print(test2)
    # GPIO.output(14, 0)
    # time.sleep(1)
    
    # GPIO.cleanup() 
    
    ##############################################################
    # デバッグ
    ##############################################################  
    # node.resetError()
    # node.setRightForm()
    # node.setServoOff()
    # node.moveOrigin()
    # pos = node.getCurrentPosBase()
    # node.setToleranceBase(80, "all")
    # node.setRightFormBase()
    # node.setLeftFormBase()
    # origin = node.getOriginStatusBase()
    # servo = node.getServoStatusBase()
    # code = node.getAlarmBase()
    # node.moveInching(10.0, "y", "-")
    # node.setOutPosBase(10000)
    # node.setContPulseBase(10000)
    # node.setWeightBase(4000)
    # node.moveRelative(x=163.0, y=175.0, z=0.0, r=251, vel=100, acc=98, dec=98)
    # node.getRobotStatus()

    # node.moveAbsoluteLine(x=163.0, y=175.0, z=10.0, r=251, vel=300, acc=0.3, dec=0.3)
    # time.sleep(2)

    # for i in range(100):
    #     start = time.time() 
    #     pos = node.getCurrentPosBase()
    #     end = time.time() - start
    #     print(pos)
    #     print(end)


    # node.moveAbsoluteLine(x=250.000, y=300.000, z=0.0, r=65.0, vel=5, acc=100, dec=100)
    # time.sleep(0.1)
    # node.stopRobot()
    
    node.setServoOn()
    ##################### Jog #####################
    node.moveJog("x", "-")
    for i in range(3):
        node.continueJogBase()
        print(i)
        # if(i == 50):
        #     node.stopJogBase()
    ###############################################
    
    # node.setServoOn()
    # # node.setServoOff()
    # # node.setLeftFormBase()
    # for i in range(30): 
    #     node.moveInching(0.5, "x", "+")
