#! /usr/bin/python
# -*- coding: utf-8 -*-

from typing import Tuple, List, Union, Optional
import numpy as np
import time
import copy


# TabletopRobotController
import serial
  
#############################################################
# グローバル変数定義
#############################################################  
X = 0
Y = 1
Z = 2
R = 3
XYZ_MAX_ACC = 3000
XYZ_MAX_VEL = 250
CHECK_MOVING_DIFF = 0.1 
# 伝文データ作成用
HEADER_NUM     = 1
HEADER_STRING  = '!'
STATION_NUM    = 2
STATION_STRING = '99'

class RobotApi():   
    def __init__(self, dst_ip_address: str, dst_port: str, dev_port: str, baurate: int):  
        ##############################################################
        # ロボット状態通知用変数定義(数値)
        ##############################################################    
        self.current_pos     :List[float] = [0.0] * 4
        self.pre_current_pos :List[float] = [0.0] * 4
        self.error_id        :int = 0   
        ##############################################################
        # ロボット状態通知用変数定義(フラグ)
        ##############################################################   
        self.error     :bool = False     
        self.servo     :bool = False
        self.emerge    :bool = False
        self.origin    :bool = False 
        self.moving    :bool = False 
        self.dragging  :bool = False 
        self.arrived   :bool = False    
        # これ以降IAI卓ロボ専用   
        self.moving_axis     :List[float] = [False] * 4
        self.origin_axis     :List[float] = [False] * 4
        self.servo_axis      :List[float] = [False] * 4
        self.cmd_result_axis :List[float] = [False] * 4      
        ##############################################################
        # ロボット接続開始
        ##############################################################  
        self.openRobot(dev_port, baurate, dev_port, baurate)      

    def __del__(self):
        ##############################################################
        # ロボット接続解除
        ##############################################################  
        self.closeRobot()
        print("Disconnected.")    

    #############################################################
    # ロボット共通関数
    #############################################################
    def openRobot(self, dst_ip_address: str, dst_port: str, dev_port: str, baurate: str) -> None:
        """ ロボット通信を開始
        """
        # ロボットサーバに接続
        print("Start to connet robot.")
        self.ser = serial.Serial(
            port	 = dev_port,\
            baudrate = baurate,\
            parity	 = serial.PARITY_NONE,\
            stopbits = serial.STOPBITS_ONE,\
            bytesize = serial.EIGHTBITS,\
            timeout	 = 1)
        print("Finished to connet robot.")
        print("Connected to: " + self.ser.port)    
    
    def closeRobot(self) -> None:
        """ ロボット通信を解除
        """
        self.ser.close()
        print("break the connection: " + self.ser.port)  

    # 2023/1/13追加　ready用
    def readyRobot(self):
        self.setServoOn()

    def getRobotStatus(self) -> None:
        """ ロボット状態を取得
        """
        ##############################################################
        # エラー状態確認
        ##############################################################
        self.getSystemStatusBase()
        ##############################################################
        # 現在地の直交座標＆軸ステータス取得
        ##############################################################
        self.getUnitStatusBase()
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
                (diff_pos[Z] >= CHECK_MOVING_DIFF)):
                self.moving = True
            else: 
                self.moving = False
        self.pre_current_pos = self.current_pos
        ##############################################################
        # Origin確認
        ##############################################################
        axis_cnt = 0
        MAX_axis = 3
        for i in range(MAX_axis):
            if (self.origin_axis[i] == True):
                axis_cnt = axis_cnt + 1
        if (axis_cnt == MAX_axis):
            self.origin = True
        else:
            self.origin = False
        ##############################################################
        # Servo確認
        ##############################################################
        axis_cnt = 0
        MAX_axis = 3
        for i in range(MAX_axis):
            if (self.servo_axis[i] == True):
                axis_cnt = axis_cnt + 1
        if (axis_cnt == MAX_axis):
            self.servo = True
        else:
            self.servo = False
        ##############################################################
        # エラーステータス取得(エラー発生時のみ)
        ##############################################################
        if (self.error == True): self.error_id = self.getErrorBase()
        else                   : self.error_id = 0

    def setTool(self, tool_no: int) -> None:
        """ ツール座標系設定
        """
        pass
    
    def setUser(self, user_no: int) -> None:
        """ ツール座標系設定
        """
        pass

    def getCurrentPos(self) -> None:
        """ 現在地の直交座標取得
        """
        pass
        
    def getCurrentJoint(self) -> None:
        """ 現在地のジョイント座標取得
        """
        pass
    
    def getPos2Joint(self, x: float, y: float, z: float, r: float) -> None:
        """ 直交座標をジョイント座標へ変換
        """
        pass
    
    def getJoint2Pos(self, j1: float, j2: float, j3: float, j4: float) -> None:
        """ ジョイント座標を直交座標へ変換
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
        ##############################################################
        # Arrived確認 
        ###############################################################
        # 現在位置と目標位置の差分取得
        diff_pos = [abs(x - y) for (x, y) in zip(target_pos, self.current_pos)]
        # print("diff_pos",diff_pos)
        # 差分が設定値以内なら
        if ((diff_pos[X] <= width) and
            (diff_pos[Y] <= width) and
            (diff_pos[Z] <= width)):
            for i in range(3):
                if   (self.moving_axis[i] == False) : self.arrived = True
                elif (self.moving_axis[i] == True)  : self.arrived = False
        else: 
            self.arrived = False

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

    def moveAbsoluteLine(self, x: float, y: float, z: float, r: float, vel: int=100, acc: int=100, dec: int=100) -> None:
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
        # acc=0.4
        # dec=0.4
        print("Moving: ")
        print("x: ", x)
        print("y: ", y)
        print("z: ", z)
        print("v: ", vel)
        print("a: ", acc)
        print("d: ", dec)

        self.moveAbsoluteLineBase(x, y, z, vel, acc, dec)

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
        self.moveRelativeBase(x, y, z, r, vel, acc, dec)

    def moveOrigin(self) -> None:
        """ 原点復帰
        """ 
        print("################################3orign#######################")
        self.moveOriginBase()

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
        self.setServoOffBase()
        self.resetErrorBase()

    def setRightForm(self) -> None:
        """ 右手系に変換
        """
        pass

    def setLeftForm(self) -> None:
        """ 左手系に変換
        """
        pass

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

    #############################################################
    # ロボット固有関数
    #############################################################      
    def sendCommandBase(self, input_cmd):
        """ ロボットにデータ送信＆受信
        Parameters
        ----------
        input_cmd : str
            aaa
        """
        request_flag = True
        self.request_cnt = 1
        while request_flag:
            # 伝文を送信
            self.ser.write(input_cmd.encode())
            # レスポンスを読込み
            received_data_byte = self.ser.read_until()  
            received_data_byte_string = str(received_data_byte)
            
            # ロボットからの返事が無い OR ロボットからの返事がエラーなら
            if (received_data_byte_string == "b''") or ("&" in received_data_byte_string):
                print("Request retry ...(Now:%d)" % self.request_cnt)
                self.request_cnt += 1
                if(self.request_cnt == 10):
                    print("The number of the retry is MAX.")
                    break                
            # ロボットからの返事が正常なら
            else:
                # print("Success")
                break

        return (received_data_byte_string)
   
    # 指定したbit単位で取り出す
    def splitBytesBase(self, value, target, length):
        return (value >> target) & (0xFF >> (8 - length))

    # 座標を10進数で取得(16進数の文字列を10進数(符号付き32bit)に変換)
    def convStr2DecBase(self, pos_str):
        pos_val = (-(int(pos_str, 16) & 0b10000000000000000000000000000000) | (int(pos_str, 16) & 0b01111111111111111111111111111111)) / 1000.0
        return pos_val

    # 16進数文字列を指定バイト文字列(ゼロ埋めあり)に変換
    def convBytes2StrBase(self, input_data, target_byte=8):
        # 入力データが負数なら
        if (input_data < 0) :
            input_data = int(input_data) & 0b11111111111111111111111111111111
            
        zero_data_string = ['0'] * (target_byte-(len(hex(int(input_data)))-2))          
        revised_zero_data_string = ''.join(zero_data_string)
        input_data_hex_string = hex(int(input_data))
        output_data = revised_zero_data_string + input_data_hex_string[2:]
        return (output_data)
    
    # 生データを整形
    def handleRowDataBase(self, cmd_data, received_data):
        # コマンドデータの累積和算出
        cmd_data_total_val = np.array(cmd_data).cumsum()
        # 生データ整形        
        output_data = []
        for _ in range(len(cmd_data)-1):
            output_data.append(received_data[2+cmd_data_total_val[_]:2+cmd_data_total_val[_]+cmd_data[_+1]])
        
        return (output_data)

    ##############################ここからIAI動作関数################################
    # P.71:ジョグ・インチング移動
    def moveJogBase(self, dir_str, axis_str):       
        # +方向なら
        if (dir_str == '+'):
            act_cmd_str = '1'
        # -方向なら
        elif (dir_str == '-'):
            act_cmd_str = '0'
            
        # X軸移動なら
        if (axis_str == 'X'):
            axis_cmd_str = '01'
        # Y軸移動なら
        elif (axis_str == 'Y'):
            axis_cmd_str = '02'
        # Z軸移動なら
        elif (axis_str == 'Z'):
            axis_cmd_str = '04'
        # # R軸移動なら
        # elif (axis_str == 'R'):
        #     axis_cmd_str = '08'
                   
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                        # 初期化
        cmd_data_string.append(HEADER_STRING)       # ヘッダー
        cmd_data_string.append(STATION_STRING)      # 局
        cmd_data_string.append('236')               # 伝文ID
        cmd_data_string.append(axis_cmd_str)        # 軸パターン
        cmd_data_string.append('0000')              # 加速度(0.01G)
        cmd_data_string.append('0000')              # 減速度(0.01G)
        cmd_data_string.append('0000')              # 速度(mm/sec)
        cmd_data_string.append('00000000')          # インチング距離(0.001mm, 0mm=Jog)
        cmd_data_string.append(act_cmd_str)         # 動作種別(BIT0(ジョグ・インチング方向):0=座標-方向/1=座標+方向)
        cmd_data_string.append('@@')                # SC
        cmd_data_string.append('\r')                # CR
        cmd_data_string.append('\n')                # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str) 

    # P.71:ジョグ・インチング移動
    def moveInchingBase(self, axis_str, width_val):       
        # X軸移動なら
        if (axis_str == 'X'):
            axis_cmd_str = '01'
        # Y軸移動なら
        elif (axis_str == 'Y'):
            axis_cmd_str = '02'
        # Z軸移動なら
        elif (axis_str == 'Z'):
            axis_cmd_str = '04'
        # # R軸移動なら
        # elif (axis_str == 'R'):
        #     axis_cmd_str = '08'
        # インチング幅を、16進数8桁に変換
        width_cmd_str = self.convBytes2StrBase(width_val*1000, 8)
        
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                        # 初期化
        cmd_data_string.append(HEADER_STRING)       # ヘッダー
        cmd_data_string.append(STATION_STRING)      # 局
        cmd_data_string.append('2D5')               # 伝文ID
        cmd_data_string.append(axis_cmd_str)        # 軸パターン
        cmd_data_string.append('000A')              # 加速度(0.01G)
        cmd_data_string.append('000A')              # 減速度(0.01G)
        cmd_data_string.append('000A')              # 速度(mm/sec)
        cmd_data_string.append('03')                # 位置決め動作種別
        cmd_data_string.append(width_cmd_str)       # 相対座標データ
        cmd_data_string.append('@@')                # SC
        cmd_data_string.append('\r')                # CR
        cmd_data_string.append('\n')                # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str) 


    # P.42:動作停止＆キャンセル
    def stopRobotBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                        # 初期化
        cmd_data_string.append(HEADER_STRING)       # ヘッダー
        cmd_data_string.append(STATION_STRING)      # 局
        cmd_data_string.append('238')               # 伝文ID
        cmd_data_string.append('0F')                # 停止軸パターン
        cmd_data_string.append('00')                # 付加コマンドバイト
        cmd_data_string.append('@@')                # SC
        cmd_data_string.append('\r')                # CR
        cmd_data_string.append('\n')                # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str) 
  
    #   # P.42:動作停止＆キャンセル
    # def resetPauseMoveBase(self):
    #     # 伝文コマンド定義
    #     ########################### コマンド #############################
    #     cmd_data_string = []                        # 初期化
    #     cmd_data_string.append(HEADER_STRING)       # ヘッダー
    #     cmd_data_string.append(STATION_STRING)      # 局
    #     cmd_data_string.append('238')               # 伝文ID
    #     cmd_data_string.append('0F')                # 停止軸パターン
    #     cmd_data_string.append('01')                # 付加コマンドバイト
    #     cmd_data_string.append('@@')                # SC
    #     cmd_data_string.append('\r')                # CR
    #     cmd_data_string.append('\n')                # LF
    #     ##################################################################
    #     ########################## レスポンス #############################
    #     res_data_val = [0]                       # 初期化
    #     res_data_val.append(HEADER_NUM)          # ヘッダー
    #     res_data_val.append(STATION_NUM)         # 局
    #     res_data_val.append(3)                   # 伝文ID
    #     res_data_val.append(2)                   # SC
    #     res_data_val.append(1)                   # CR
    #     res_data_val.append(1)                   # LF
    #     ##################################################################
    #     # 伝文コマンド生成
    #     cmd_data_val = ''.join(cmd_data_string)
    #     # ロボットにリクエストを送信
    #     received_row_data_str = self.sendCommandBase(cmd_data_val)
    #     # 生データ整形
    #     received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str) 
  
    # P.67:絶対座標指定移動
    # pos:mm, vel:mm/s, acc,dec:G
    def moveAbsoluteLineBase(self, x_pos, y_pos, z_pos, vel, acc, dec):
        # 使用する軸の位置データ格納
        abs_pos_data = []
        abs_pos_data.append(self.convBytes2StrBase(x_pos*1000, 8))
        rest_abs_pos_data = []
        rest_abs_pos_data.append(self.convBytes2StrBase(y_pos*1000, 8))
        rest_abs_pos_data.append(self.convBytes2StrBase(z_pos*1000, 8))
                
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                              # 初期化
        cmd_data_string.append(HEADER_STRING)                             # ヘッダー
        cmd_data_string.append(STATION_STRING)                            # 局
        cmd_data_string.append('234')                                     # 伝文ID
        cmd_data_string.append('07')                                      # 軸パターン
        cmd_data_string.append(self.convBytes2StrBase(acc*100, 4))        # 加速度(0.01G)
        cmd_data_string.append(self.convBytes2StrBase(dec*100, 4))        # 減速度(0.01G)
        cmd_data_string.append(self.convBytes2StrBase(vel, 4))            # 速度(mm/sec)
        cmd_data_string.append(abs_pos_data[0])                           # 絶対座標データ(0.001mm)
        cmd_data_string.append(''.join(rest_abs_pos_data))                # 残絶対座標データ(0.001mm)
        cmd_data_string.append('@@')                                      # SC
        cmd_data_string.append('\r')                                      # CR
        cmd_data_string.append('\n')                                      # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str) 
        
    # P.89:アラームリセット
    def resetErrorBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                             # 初期化
        cmd_data_string.append(HEADER_STRING)            # ヘッダー
        cmd_data_string.append(STATION_STRING)           # 局
        cmd_data_string.append('252')                    # 伝文ID
        cmd_data_string.append('@@')                     # SC
        cmd_data_string.append('\r')                     # CR
        cmd_data_string.append('\n')                     # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str) 

    # P.66:原点復帰
    def moveOriginBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                             # 初期化
        cmd_data_string.append(HEADER_STRING)            # ヘッダー
        cmd_data_string.append(STATION_STRING)           # 局
        cmd_data_string.append('233')                    # 伝文ID
        cmd_data_string.append('07')                     # 軸パターン
        cmd_data_string.append('010')                    # 原点復帰時エンドサーチ速度(mm/sec)
        cmd_data_string.append('010')                    # 原点復帰時エンドサーチ速度(mm/sec)
        cmd_data_string.append('@@')                     # SC
        cmd_data_string.append('\r')                     # CR
        cmd_data_string.append('\n')                     # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str) 

    # P.65:サーボオン／オフ
    def setServoOnBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                             # 初期化
        cmd_data_string.append(HEADER_STRING)            # ヘッダー
        cmd_data_string.append(STATION_STRING)           # 局
        cmd_data_string.append('232')                    # 伝文ID
        cmd_data_string.append('07')                     # 軸パターン
        cmd_data_string.append('1')                      # 動作種別
        cmd_data_string.append('@@')                     # SC
        cmd_data_string.append('\r')                     # CR
        cmd_data_string.append('\n')                     # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str) 
    
    # P.65:サーボオン／オフ
    def setServoOffBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                             # 初期化
        cmd_data_string.append(HEADER_STRING)            # ヘッダー
        cmd_data_string.append(STATION_STRING)           # 局
        cmd_data_string.append('232')                    # 伝文ID
        cmd_data_string.append('07')                     # 軸パターン
        cmd_data_string.append('0')                      # 動作種別
        cmd_data_string.append('@@')                     # SC
        cmd_data_string.append('\r')                     # CR
        cmd_data_string.append('\n')                     # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str) 

    # P113:ユニット軸ステータス取得
    def getUnitStatusBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                             # 初期化
        cmd_data_string.append(HEADER_STRING)            # ヘッダー
        cmd_data_string.append(STATION_STRING)           # 局
        cmd_data_string.append('212')                    # 伝文ID
        cmd_data_string.append('07')                     # 照会軸パターン
        cmd_data_string.append('@@')                     # SC
        cmd_data_string.append('\r')                     # CR
        cmd_data_string.append('\n')                     # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(2)                   # 軸パターン
        res_data_val.append(2)                   # X軸ステータス
        res_data_val.append(1)                   # X軸センサ入力ステータス
        res_data_val.append(3)                   # X軸関連エラー
        res_data_val.append(2)                   # X軸エンコーダステータス
        res_data_val.append(8)                   # X軸現在位置
        res_data_val.append(2)                   # Y軸ステータス
        res_data_val.append(1)                   # Y軸センサ入力ステータス
        res_data_val.append(3)                   # Y軸関連エラー
        res_data_val.append(2)                   # Y軸エンコーダステータス
        res_data_val.append(8)                   # Y軸現在位置
        res_data_val.append(2)                   # Z軸ステータス
        res_data_val.append(1)                   # Z軸センサ入力ステータス
        res_data_val.append(3)                   # Z軸関連エラー
        res_data_val.append(2)                   # Z軸エンコーダステータス
        res_data_val.append(8)                   # Z軸現在位置
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str)    
        
        ##############################################################
        # 現在位置
        ##############################################################    
        self.current_pos[X] = self.convStr2DecBase(received_data_str[8])
        self.current_pos[Y] = self.convStr2DecBase(received_data_str[13])
        self.current_pos[Z] = self.convStr2DecBase(received_data_str[18])
        ##############################################################
        # 軸ステータス
        ############################################################## 
        # X
        self.moving_axis[X]     = True if self.splitBytesBase(int(received_data_str[4], 16), 0, 1) == 1 else False  # move_status 
        self.origin_axis[X]     = True if self.splitBytesBase(int(received_data_str[4], 16), 2, 1) == 1 else False  # home_high 
        self.servo_axis[X]      = True if self.splitBytesBase(int(received_data_str[4], 16), 3, 1) == 1 else False  # servo_status 
        self.cmd_result_axis[X] = True if self.splitBytesBase(int(received_data_str[4], 16), 4, 1) == 1 else False  # cmd_result       
        # Y    
        self.moving_axis[Y]     = True if self.splitBytesBase(int(received_data_str[9], 16), 0, 1) == 1 else False  # move_status 
        self.origin_axis[Y]     = True if self.splitBytesBase(int(received_data_str[9], 16), 2, 1) == 1 else False  # home_high 
        self.servo_axis[Y]      = True if self.splitBytesBase(int(received_data_str[9], 16), 3, 1) == 1 else False  # servo_status 
        self.cmd_result_axis[Y] = True if self.splitBytesBase(int(received_data_str[9], 16), 4, 1) == 1 else False  # cmd_result       
        # Z    
        self.moving_axis[Z]     = True if self.splitBytesBase(int(received_data_str[14], 16), 0, 1) == 1 else False  # move_status 
        self.origin_axis[Z]     = True if self.splitBytesBase(int(received_data_str[14], 16), 2, 1) == 1 else False  # home_high 
        self.servo_axis[Z]      = True if self.splitBytesBase(int(received_data_str[14], 16), 3, 1) == 1 else False  # servo_status 
        self.cmd_result_axis[Z] = True if self.splitBytesBase(int(received_data_str[14], 16), 4, 1) == 1 else False  # cmd_result           

    # P32:システムステータス照会
    def getSystemStatusBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                             # 初期化
        cmd_data_string.append(HEADER_STRING)            # ヘッダー
        cmd_data_string.append(STATION_STRING)           # 局
        cmd_data_string.append('215')                    # 伝文ID
        cmd_data_string.append('@@')                     # SC
        cmd_data_string.append('\r')                     # CR
        cmd_data_string.append('\n')                     # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(1)                   # システムモード
        res_data_val.append(3)                   # 最重レベルシステムエラーNo.
        res_data_val.append(3)                   # 最新システムエラーNo.
        res_data_val.append(2)                   # システムステータスバイト1
        res_data_val.append(2)                   # システムステータスバイト2
        res_data_val.append(2)                   # システムステータスバイト3
        res_data_val.append(2)                   # システムステータスバイト4
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str)   
        
        drive_status = True if self.splitBytesBase(int(received_data_str[6], 16), 0, 1) == 0 else False  # 運転モードSWステータス:0=AUTO/1=MANUAL
        tp_enable    = True if self.splitBytesBase(int(received_data_str[6], 16), 1, 1) == 0 else False  # TPイネーブルSWステータス:0=ON/1=OFF
        emg_stop     = True if self.splitBytesBase(int(received_data_str[6], 16), 3, 1) == 1 else False  # 非常停止SWステータス:0=非非常停止/1=非常停止

        if ((drive_status == False)          or
            (tp_enable == False)             or
            (emg_stop == True)               or
            (received_data_str[4] != '000')  or
            (received_data_str[5] != '000')):
            self.error = True
        else:
            self.error = False

    # P32:エラー詳細情報照会
    def getErrorBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                             # 初期化
        cmd_data_string.append(HEADER_STRING)            # ヘッダー
        cmd_data_string.append(STATION_STRING)           # 局
        cmd_data_string.append('216')                    # 伝文ID
        cmd_data_string.append('3')                      # 種別1(0=システムエラー/1=軸別エラー/2=プログラム別エラー/3=エラーリストレコード内エラー)
        cmd_data_string.append('01')                     # 種別2(0=最重レベルエラー/1=最新エラー)
        cmd_data_string.append('000')                    # レコードNo.
        cmd_data_string.append('@@')                     # SC
        cmd_data_string.append('\r')                     # CR
        cmd_data_string.append('\n')                     # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(3)                   # エラーNo.
        res_data_val.append(8)                   # 詳細情報1
        res_data_val.append(8)                   # 詳細情報2
        res_data_val.append(8)                   # 詳細情報3
        res_data_val.append(8)                   # 詳細情報4
        res_data_val.append(8)                   # 詳細情報5
        res_data_val.append(8)                   # 詳細情報6
        res_data_val.append(8)                   # 詳細情報7
        res_data_val.append(8)                   # 詳細情報8
        res_data_val.append(2)                   # システム予約
        res_data_val.append(2)                   # システム予約
        res_data_val.append(2)                   # システム予約
        res_data_val.append(1)                   # システム予約
        res_data_val.append(2)                   # システム予約
        res_data_val.append(2)                   # システム予約
        res_data_val.append(4)                   # システム予約
        res_data_val.append(2)                   # メッセージ バイト数
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str)   
        self.error_id = received_data_str[3] # エラーID
        

    # # P22:フラグ照会
    # def getFlagStatusBase(self):
    #     # 伝文コマンド定義
    #     ########################### コマンド #############################
    #     cmd_data_string = []                             # 初期化
    #     cmd_data_string.append(HEADER_STRING)            # ヘッダー
    #     cmd_data_string.append(STATION_STRING)           # 局
    #     cmd_data_string.append('20D')                    # 伝文ID
    #     cmd_data_string.append('00')                     # プログラムNo.(グローバルフラグ=00)
    #     cmd_data_string.append('0258')                   # 照会開始フラグNo.
    #     cmd_data_string.append('0008')                   # 照会フラグ数
    #     cmd_data_string.append('@@')                     # SC
    #     cmd_data_string.append('\r')                     # CR
    #     cmd_data_string.append('\n')                     # LF
    #     ##################################################################
    #     ########################## レスポンス #############################
    #     res_data_val = [0]                       # 初期化
    #     res_data_val.append(HEADER_NUM)          # ヘッダー
    #     res_data_val.append(STATION_NUM)         # 局
    #     res_data_val.append(3)                   # 伝文ID
    #     res_data_val.append(2)                   # プログラムNo.(グローバルフラグ=00)
    #     res_data_val.append(4)                   # レスポンス開始フラグNo.
    #     res_data_val.append(4)                   # レスポンスフラグ数
    #     # res_data_val.append(2)                   # フラグデータ（*1）
    #     res_data_val.append(2)                   # 残フラグデータ
    #     res_data_val.append(2)                   # SC
    #     res_data_val.append(1)                   # CR
    #     res_data_val.append(1)                   # LF
    #     ##################################################################
    #     # 伝文コマンド生成
    #     print(cmd_data_string)
    #     cmd_data_val = ''.join(cmd_data_string)
    #     # ロボットにリクエストを送信
    #     received_row_data_str = self.sendCommandBase(cmd_data_val)       
    #     # 生データ整形
    #     received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str)         
    #     return (received_data_str)   
    
    # # P47:フラグ状態変更
    # #
    # def changeFlagStatusBase(self, flag_no, on_off_flag):
        
    #     if (on_off_flag == True):
    #         on_off_flag = '1'
    #     else:
    #         on_off_flag = '0'
        
    #     # 伝文コマンド定義
    #     ########################### コマンド #############################
    #     cmd_data_string = []                                           # 初期化
    #     cmd_data_string.append(HEADER_STRING)                          # ヘッダー
    #     cmd_data_string.append(STATION_STRING)                         # 局
    #     cmd_data_string.append('24B')                                  # 伝文ID
    #     cmd_data_string.append('00')                                   # プログラムNo.(グローバルフラグ=00)
    #     cmd_data_string.append(self.convBytes2StrBase(flag_no, 4))   # 照会フラグNo.
    #     cmd_data_string.append(on_off_flag)                            # 変更種別
    #     cmd_data_string.append('@@')                                   # SC
    #     cmd_data_string.append('\r')                                   # CR
    #     cmd_data_string.append('\n')                                   # LF
    #     ##################################################################
    #     ########################## レスポンス #############################
    #     res_data_val = [0]                       # 初期化
    #     res_data_val.append(HEADER_NUM)          # ヘッダー
    #     res_data_val.append(STATION_NUM)         # 局
    #     res_data_val.append(3)                   # 伝文ID
    #     res_data_val.append(2)                   # SC
    #     res_data_val.append(1)                   # CR
    #     res_data_val.append(1)                   # LF
    #     ##################################################################
    #     # 伝文コマンド生成
    #     cmd_data_val = ''.join(cmd_data_string)
    #     # ロボットにリクエストを送信
    #     received_row_data_str = self.sendCommandBase(cmd_data_val)       
    #     # 生データ整形
    #     received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str)        
    #     return (received_data_str)     
    
    # # P47:フラグ状態変更
    # #
    # def writePointDataBase(self, pos_X_1=0.0, pos_Y_1=0.0, pos_Z_1=0.0, pos_R_1=0.0, vel_1=0.0, acc_1=0.0, dec_1=0.0, 
    #                          pos_X_2=0.0, pos_Y_2=0.0, pos_Z_2=0.0, pos_R_2=0.0, vel_2=0.0, acc_2=0.0, dec_2=0.0,
    #                          pos_X_3=0.0, pos_Y_3=0.0, pos_Z_3=0.0, pos_R_3=0.0, vel_3=0.0, acc_3=0.0, dec_3=0.0,
    #                          pos_X_4=0.0, pos_Y_4=0.0, pos_Z_4=0.0, pos_R_4=0.0, vel_4=0.0, acc_4=0.0, dec_4=0.0):
        
    #     axis_pattern_str = '0F'
    #     if (vel_1 > 0.0) and (vel_2 > 0.0) and (vel_3 > 0.0) and (vel_4 > 0.0):
    #         # ポイントデータ数
    #         target_point_val = 4
    #         # ポイントデータ1
    #         pos_XYZR_str_1 = self.convBytes2StrBase(pos_X_1*1000, 8) + self.convBytes2StrBase(pos_Y_1*1000, 8) + self.convBytes2StrBase(pos_Z_1*1000, 8) + self.convBytes2StrBase(pos_R_1*1000, 8)
    #         vel_str_1 = self.convBytes2StrBase(vel_1, 4)
    #         acc_str_1 = self.convBytes2StrBase(acc_1*100, 4)
    #         dec_str_1 = self.convBytes2StrBase(dec_1*100, 4)
    #         point_data_str_1 = axis_pattern_str + acc_str_1 + dec_str_1 + vel_str_1 + pos_XYZR_str_1
    #         # ポイントデータ2
    #         pos_XYZR_str_2 = self.convBytes2StrBase(pos_X_2*1000, 8) + self.convBytes2StrBase(pos_Y_2*1000, 8) + self.convBytes2StrBase(pos_Z_2*1000, 8) + self.convBytes2StrBase(pos_R_2*1000, 8)
    #         vel_str_2 = self.convBytes2StrBase(vel_2, 4)
    #         acc_str_2 = self.convBytes2StrBase(acc_2*100, 4)
    #         dec_str_2 = self.convBytes2StrBase(dec_2*100, 4)
    #         point_data_str_2 = axis_pattern_str + acc_str_2 + dec_str_2 + vel_str_2 + pos_XYZR_str_2
    #         # ポイントデータ3
    #         pos_XYZR_str_3 = self.convBytes2StrBase(pos_X_3*1000, 8) + self.convBytes2StrBase(pos_Y_3*1000, 8) + self.convBytes2StrBase(pos_Z_3*1000, 8) + self.convBytes2StrBase(pos_R_3*1000, 8)
    #         vel_str_3 = self.convBytes2StrBase(vel_3, 4)
    #         acc_str_3 = self.convBytes2StrBase(acc_3*100, 4)
    #         dec_str_3 = self.convBytes2StrBase(dec_3*100, 4)
    #         point_data_str_3 = axis_pattern_str + acc_str_3 + dec_str_3 + vel_str_3 + pos_XYZR_str_3   
    #         # ポイントデータ4
    #         pos_XYZR_str_4 = self.convBytes2StrBase(pos_X_4*1000, 8) + self.convBytes2StrBase(pos_Y_4*1000, 8) + self.convBytes2StrBase(pos_Z_4*1000, 8) + self.convBytes2StrBase(pos_R_4*1000, 8)
    #         vel_str_4 = self.convBytes2StrBase(vel_4, 4)
    #         acc_str_4 = self.convBytes2StrBase(acc_4*100, 4)
    #         dec_str_4 = self.convBytes2StrBase(dec_4*100, 4)
    #         point_data_str_4 = axis_pattern_str + acc_str_4 + dec_str_4 + vel_str_4 + pos_XYZR_str_4  
    #         # ポイントデータ1~4
    #         point_data_str = point_data_str_1 + point_data_str_2 + point_data_str_3 + point_data_str_4    
            
    #     elif (vel_1 > 0.0) and (vel_2 > 0.0) and (vel_3 > 0.0):
    #         # ポイントデータ数
    #         target_point_val = 3
    #         # ポイントデータ1
    #         pos_XYZR_str_1 = self.convBytes2StrBase(pos_X_1*1000, 8) + self.convBytes2StrBase(pos_Y_1*1000, 8) + self.convBytes2StrBase(pos_Z_1*1000, 8) + self.convBytes2StrBase(pos_R_1*1000, 8)
    #         vel_str_1 = self.convBytes2StrBase(vel_1, 4)
    #         acc_str_1 = self.convBytes2StrBase(acc_1*100, 4)
    #         dec_str_1 = self.convBytes2StrBase(dec_1*100, 4)
    #         point_data_str_1 = axis_pattern_str + acc_str_1 + dec_str_1 + vel_str_1 + pos_XYZR_str_1
    #         # ポイントデータ2
    #         pos_XYZR_str_2 = self.convBytes2StrBase(pos_X_2*1000, 8) + self.convBytes2StrBase(pos_Y_2*1000, 8) + self.convBytes2StrBase(pos_Z_2*1000, 8) + self.convBytes2StrBase(pos_R_2*1000, 8)
    #         vel_str_2 = self.convBytes2StrBase(vel_2, 4)
    #         acc_str_2 = self.convBytes2StrBase(acc_2*100, 4)
    #         dec_str_2 = self.convBytes2StrBase(dec_2*100, 4)
    #         point_data_str_2 = axis_pattern_str + acc_str_2 + dec_str_2 + vel_str_2 + pos_XYZR_str_2
    #         # ポイントデータ3
    #         pos_XYZR_str_3 = self.convBytes2StrBase(pos_X_3*1000, 8) + self.convBytes2StrBase(pos_Y_3*1000, 8) + self.convBytes2StrBase(pos_Z_3*1000, 8) + self.convBytes2StrBase(pos_R_3*1000, 8)
    #         vel_str_3 = self.convBytes2StrBase(vel_3, 4)
    #         acc_str_3 = self.convBytes2StrBase(acc_3*100, 4)
    #         dec_str_3 = self.convBytes2StrBase(dec_3*100, 4)
    #         point_data_str_3 = axis_pattern_str + acc_str_3 + dec_str_3 + vel_str_3 + pos_XYZR_str_3   
    #         # ポイントデータ4
    #         point_data_str_4 = ''
    #         # ポイントデータ1~4
    #         point_data_str = point_data_str_1 + point_data_str_2 + point_data_str_3 + point_data_str_4 
    #     elif (vel_1 > 0.0) and (vel_2 > 0.0):
    #         # ポイントデータ数
    #         target_point_val = 2
    #         # ポイントデータ1
    #         pos_XYZR_str_1 = self.convBytes2StrBase(pos_X_1*1000, 8) + self.convBytes2StrBase(pos_Y_1*1000, 8) + self.convBytes2StrBase(pos_Z_1*1000, 8) + self.convBytes2StrBase(pos_R_1*1000, 8)
    #         vel_str_1 = self.convBytes2StrBase(vel_1, 4)
    #         acc_str_1 = self.convBytes2StrBase(acc_1*100, 4)
    #         dec_str_1 = self.convBytes2StrBase(dec_1*100, 4)
    #         point_data_str_1 = axis_pattern_str + acc_str_1 + dec_str_1 + vel_str_1 + pos_XYZR_str_1
    #         # ポイントデータ2
    #         pos_XYZR_str_2 = self.convBytes2StrBase(pos_X_2*1000, 8) + self.convBytes2StrBase(pos_Y_2*1000, 8) + self.convBytes2StrBase(pos_Z_2*1000, 8) + self.convBytes2StrBase(pos_R_2*1000, 8)
    #         vel_str_2 = self.convBytes2StrBase(vel_2, 4)
    #         acc_str_2 = self.convBytes2StrBase(acc_2*100, 4)
    #         dec_str_2 = self.convBytes2StrBase(dec_2*100, 4)
    #         point_data_str_2 = axis_pattern_str + acc_str_2 + dec_str_2 + vel_str_2 + pos_XYZR_str_2
    #         # ポイントデータ3
    #         point_data_str_3 = '' 
    #         # ポイントデータ4
    #         point_data_str_4 = ''
    #         # ポイントデータ1~4
    #         point_data_str = point_data_str_1 + point_data_str_2 + point_data_str_3 + point_data_str_4 
    #     elif (vel_1 > 0.0):
    #         # ポイントデータ数
    #         target_point_val = 1
    #         # ポイントデータ1
    #         pos_XYZR_str_1 = self.convBytes2StrBase(pos_X_1*1000, 8) + self.convBytes2StrBase(pos_Y_1*1000, 8) + self.convBytes2StrBase(pos_Z_1*1000, 8) + self.convBytes2StrBase(pos_R_1*1000, 8)
    #         vel_str_1 = self.convBytes2StrBase(vel_1, 4)
    #         acc_str_1 = self.convBytes2StrBase(acc_1*100, 4)
    #         dec_str_1 = self.convBytes2StrBase(dec_1*100, 4)
    #         point_data_str_1 = axis_pattern_str + acc_str_1 + dec_str_1 + vel_str_1 + pos_XYZR_str_1
    #         # ポイントデータ2
    #         point_data_str_2 = ''
    #         # ポイントデータ3
    #         point_data_str_3 = '' 
    #         # ポイントデータ4
    #         point_data_str_4 = ''
    #         # ポイントデータ1~4
    #         point_data_str = point_data_str_1 + point_data_str_2 + point_data_str_3 + point_data_str_4 
        
    #     # 伝文コマンド定義
    #     ########################### コマンド #############################
    #     cmd_data_string = []                                                     # 初期化
    #     cmd_data_string.append(HEADER_STRING)                                    # ヘッダー
    #     cmd_data_string.append(STATION_STRING)                                   # 局
    #     cmd_data_string.append('244')                                            # 伝文ID
    #     cmd_data_string.append('01E')                                            # 変更開始ポイントデータNo.30
    #     cmd_data_string.append(self.convBytes2StrBase(target_point_val, 3))    # 変更ポイントデータ数
    #     cmd_data_string.append(point_data_str)                                   # ポイントデータ
    #     cmd_data_string.append('@@')                                             # SC
    #     cmd_data_string.append('\r')                                             # CR
    #     cmd_data_string.append('\n')                                             # LF
    #     ##################################################################
    #     ########################## レスポンス #############################
    #     res_data_val = [0]                       # 初期化
    #     res_data_val.append(HEADER_NUM)          # ヘッダー
    #     res_data_val.append(STATION_NUM)         # 局
    #     res_data_val.append(3)                   # 伝文ID
    #     res_data_val.append(2)                   # SC
    #     res_data_val.append(1)                   # CR
    #     res_data_val.append(1)                   # LF
    #     ##################################################################
    #     print(cmd_data_string)
    #     # 伝文コマンド生成
    #     cmd_data_val = ''.join(cmd_data_string)
    #     # ロボットにリクエストを送信
    #     received_row_data_str = self.sendCommandBase(cmd_data_val)       
    #     # 生データ整形
    #     received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str)  
    #     print(received_data_str)      
    #     return (received_data_str)      
    
    # # P20:入力ポート照会

    # def getInputPortBase(self):        
    #     # 伝文コマンド定義
    #     ########################### コマンド #############################
    #     cmd_data_string = []                                           # 初期化
    #     cmd_data_string.append(HEADER_STRING)                          # ヘッダー
    #     cmd_data_string.append(STATION_STRING)                         # 局
    #     cmd_data_string.append('20B')                                  # 伝文ID
    #     cmd_data_string.append('0010')                                 # 照会開始ポートNo.
    #     cmd_data_string.append('0010')                                 # 照会ポート数
    #     cmd_data_string.append('@@')                                   # SC
    #     cmd_data_string.append('\r')                                   # CR
    #     cmd_data_string.append('\n')                                   # LF
    #     ##################################################################
    #     ########################## レスポンス #############################
    #     res_data_val = [0]                       # 初期化
    #     res_data_val.append(HEADER_NUM)          # ヘッダー
    #     res_data_val.append(STATION_NUM)         # 局
    #     res_data_val.append(3)                   # 伝文ID
    #     res_data_val.append(4)                   # レスポンス開始ポートNo.
    #     res_data_val.append(4)                   # レスポンスポート数
    #     res_data_val.append(2)                   # 入力ポートデータ
    #     res_data_val.append(2)                   # SC
    #     res_data_val.append(1)                   # CR
    #     res_data_val.append(1)                   # LF
    #     ##################################################################
    #     # 伝文コマンド生成
    #     cmd_data_val = ''.join(cmd_data_string)
    #     # ロボットにリクエストを送信
    #     received_row_data_str = self.sendCommandBase(cmd_data_val)       
    #     # 生データ整形
    #     received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str)        
    #     return (received_data_str)  

    # # P46:出力ポート状態変更

    # def changeOutputPortBase(self):        
    #     # 伝文コマンド定義
    #     ########################### コマンド #############################
    #     cmd_data_string = []                                           # 初期化
    #     cmd_data_string.append(HEADER_STRING)                          # ヘッダー
    #     cmd_data_string.append(STATION_STRING)                         # 局
    #     cmd_data_string.append('24A')                                  # 伝文ID
    #     cmd_data_string.append('013C')                                 # 出力ポートNo.
    #     cmd_data_string.append('1')                                    # 変更種別
    #     cmd_data_string.append('@@')                                   # SC
    #     cmd_data_string.append('\r')                                   # CR
    #     cmd_data_string.append('\n')                                   # LF
    #     ##################################################################
    #     ########################## レスポンス #############################
    #     res_data_val = [0]                       # 初期化
    #     res_data_val.append(HEADER_NUM)          # ヘッダー
    #     res_data_val.append(STATION_NUM)         # 局
    #     res_data_val.append(3)                   # 伝文ID
    #     res_data_val.append(2)                   # SC
    #     res_data_val.append(1)                   # CR
    #     res_data_val.append(1)                   # LF
    #     ##################################################################
    #     # 伝文コマンド生成
    #     cmd_data_val = ''.join(cmd_data_string)
    #     # ロボットにリクエストを送信
    #     received_row_data_str = self.sendCommandBase(cmd_data_val)       
    #     # 生データ整形
    #     received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str)        
    #     return (received_data_str)  
