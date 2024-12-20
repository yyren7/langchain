#! /usr/bin/python
# -*- coding: utf-8 -*-

from typing import Tuple, List, Union, Optional
import numpy as np
import time
import copy


# TabletopRobotController
import serial
import select  

#############################################################
# グローバル変数定義
#############################################################  
X  = 0
Y  = 1
Z  = 2
Rx = 3
Ry = 4
Rz = 5
XYZ_MAX_ACC = 3000
XYZ_MAX_VEL = 250
CHECK_MOVING_DIFF = 0.1 
# 伝文データ作成用
HEADER_NUM     = 1
HEADER_STRING  = '!'
STATION_NUM    = 2
STATION_STRING = '99'
# 軸切替用
MAX_AXIS = 3

if (MAX_AXIS == 3): AXIS_PATTERN = '07'
if (MAX_AXIS == 4): AXIS_PATTERN = '0F'

class RobotApi():   
    def __init__(self, dst_ip_address: str, dst_port: str, dev_port: str, baurate: int):  
        ##############################################################
        # ロボット状態通知用変数定義(数値)
        ##############################################################    
        self.current_pos     :List[float] = [0.0] * 6
        self.pre_current_pos :List[float] = [0.0] * 6
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
        self.robot_mode:int  = 5    
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
            diff_pos = [abs(a - b) for (a, b) in zip(self.pre_current_pos, self.current_pos)]
            # 差分が設定値以上なら
            axis_cnt = 0
            for i in range(MAX_AXIS):
                if (diff_pos[i] >= CHECK_MOVING_DIFF):
                    axis_cnt = axis_cnt + 1
            if (axis_cnt == MAX_AXIS):
                self.moving = True
            else:
                self.moving = False
        self.pre_current_pos = self.current_pos
        ##############################################################
        # Origin確認
        ##############################################################
        axis_cnt = 0
        for i in range(MAX_AXIS):
            if (self.origin_axis[i] == True):
                axis_cnt = axis_cnt + 1
        if (axis_cnt == MAX_AXIS):
            self.origin = True
        else:
            self.origin = False
        ##############################################################
        # Servo確認
        ##############################################################
        axis_cnt = 0
        for i in range(MAX_AXIS):
            if (self.servo_axis[i] == True):
                axis_cnt = axis_cnt + 1
        if (axis_cnt == MAX_AXIS):
            self.servo = True
        else:
            self.servo = False
        ##############################################################
        # エラーステータス取得(エラー発生時のみ)
        ##############################################################
        if (self.error == True): self.getErrorBase()
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
        diff_pos = [abs(a - b) for (a, b) in zip(target_pos, self.current_pos)]
        
        
        axis_cnt = 0
        # 現在位置と目標位置の差分が、位置決め幅以下なら
        for i in range(MAX_AXIS):
            if (diff_pos[i] <= width):
                axis_cnt = axis_cnt + 1
        if (axis_cnt == MAX_AXIS):
            self.arrived = True
        else:
            self.arrived = False  
            
        # for i in range(MAX_AXIS):
        #     if (diff_pos[i] <= width):
        #         axis_cnt = axis_cnt + 1
        # if (axis_cnt == MAX_AXIS):
        #     moved = True
        # else:
        #     moved = False    
        # # 各軸のmovingが落ちていれば
        # axis_cnt = 0
        # for i in range(MAX_AXIS):
        #     if (self.moving_axis[i] == False):
        #         axis_cnt = axis_cnt + 1
        # if (axis_cnt == MAX_AXIS) and (moved == True):
        #     self.arrived = True
        # else:
        #     self.arrived = False

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

    def moveAbsolutePtp(self,
                        x: float,
                        y: float,
                        z: float,
                        rx: float,
                        ry: float,
                        rz: float,
                        vel: int = 100,
                        acc: int = 100,
                        dec: int = 100) -> None:
        """ ロボット絶対移動(PTP)
        Parameters
        ----------
        x : float
            目標x座標[mm]
        y : float
            目標y座標[mm]
        z : float
            目標z座標[mm]
        rx : float
            目標r座標[°]
        ry : float
            目標r座標[°]
        rz : float
            目標r座標[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """
        self.moveAbsolutePtpBase(x, y, z, rz, vel, acc, dec)

    def moveAbsoluteLine(self,
                         x: float,
                         y: float,
                         z: float,
                         rx: float,
                         ry: float,
                         rz: float,
                         vel: int = 100,
                         acc: int = 100,
                         dec: int = 100) -> None:
        """ ロボット絶対移動(直線補間)
        Parameters
        ----------
        x : float
            目標x座標[mm]
        y : float
            目標y座標[mm]
        z : float
            目標z座標[mm]
        rx : float
            目標r座標[°]
        ry : float
            目標r座標[°]
        rz : float
            目標r座標[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """
        self.error_id = self.getErrorBase()
        self.moveAbsoluteLineBase(x, y, z, rz, vel, acc, dec)

    def moveRelative(self,
                     x: float,
                     y: float,
                     z: float,
                     rx: float,
                     ry: float,
                     rz: float,
                     vel: int = 100,
                     acc: int = 100,
                     dec: int = 100) -> None:
        """ ロボット相対移動
        Parameters
        ----------
        x : float
            x座標移動量[mm]
        y : float
            y座標移動量[mm]
        z : float
            z座標移動量[mm]
        rx : float
            r座標移動量[°]
        ry : float
            r座標移動量[°]
        rz : float
            r座標移動量[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """
        self.moveRelativeBase(x, y, z, rz, vel, acc, dec)

    def moveOrigin(self) -> None:
        """ 原点復帰
        """
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
                
    def continueJog(self, axis_char_str: str, direction_char_str: str) -> None:
        """ ジョグ継続
        Parameters
        ----------
        axis_char_str : str
            軸(ex. "x")
        direction_char_str : str
            回転方向(ex. "+")
        """
        pass
        
    def stopJog(self) -> None:
        """ ジョグ継続
        """
        self.stopRobot()
        
    def startProgram(self, prog_no: int) -> None:
        """ プログラム起動
        """
        self.startProgramBase(prog_no)
        
    def stopProgram(self, prog_no: int) -> None:
        """ プログラム起動
        """
        self.stopProgramBase(prog_no)

    def setPointData(self, start_no, range_no, P1=[0, 0, 0, 0, 0, 0, 0], 
                                               P2=[0, 0, 0, 0, 0, 0, 0], 
                                               P3=[0, 0, 0, 0, 0, 0, 0], 
                                               P4=[0, 0, 0, 0, 0, 0, 0]):
        """ ロボット用コントローラにポイントデータを書込み
        """
        self.setPointDataBase(start_no, range_no, P1, P2, P3, P4)
        
    def setGlobalValue(self, start_val: int, data_val_list: list) -> None:
        """ グローバル変数書き換え
        """
        self.setGlobalValueBase(start_val, data_val_list)
        
    def setGlobalFlagOn(self, flag_no: int) -> None:
        """ グローバルフラグ書き換え
        """
        self.setGlobalFlagOnBase(flag_no)
        
    def setGlobalFlagOff(self, flag_no: int) -> None:
        """ グローバルフラグ書き換え
        """
        self.setGlobalFlagOffBase(flag_no)

    def getInput(self) -> None:
        """ ポート入力状態参照
        """
        # ref_port_no = 16
        ref_port_no = 32
        return self.getInputBase(ref_port_no)  
    def setOutputON(self, pin_no: int) -> None:
        """ ポート出力状態変更
        """
        ref_port_no = 316 + (pin_no-1)
        self.setOutputONBase(ref_port_no)   

    def setOutputOFF(self, pin_no: int) -> None:
        """ ポート出力状態変更
        """
        ref_port_no = 316 + (pin_no-1)
        self.setOutputOFFBase(ref_port_no)  
        

    def printRobotStatus(self) -> None:
        """ 変数表示(デバッグ用)
        """
        print("##########################  Status  ##############################################")
        print('X  = {0:.3f}'.format(self.current_pos[X]))
        print('Y  = {0:.3f}'.format(self.current_pos[Y]))
        print('Z  = {0:.3f}'.format(self.current_pos[Z]))
        print('R  = {0:.3f}'.format(self.current_pos[Rz]))
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
        """
        request_flag = True
        self.request_cnt = 1
        while request_flag:
            # 伝文を送信
            self.ser.write(input_cmd.encode())
            timeout_in_seconds = 5.0
            # サーバーからのレスポンス格納し、タイムアウトを設定
            ready = select.select([self.ser], [], [], timeout_in_seconds)
            # サーバーからのレスポンスがあれば
            if ready[0]:
                try:
                    # レスポンスを読込み
                    received_data_byte = self.ser.read_until()  
                    received_data_str = str(received_data_byte)
                    # チェックサム確認
                    reviced_received_data_str = received_data_str[:-5].replace("b'", "")
                    received_SC_str = reviced_received_data_str[-2:]
                    calculated_high_SC_str, calculated_low_SC_str = self.calcSC(reviced_received_data_str[:-2])
                    calculated_SC_str = calculated_high_SC_str + calculated_low_SC_str   
                # 例外処理
                except serial.SerialException:
                    print("例外処理発生")
                    continue  

            # print(received_data_str)
            # 通信を安定させるためのタイマ
            # time.sleep(0.005)
            
            if(received_SC_str != calculated_SC_str):
                print("チェックサムNG")
            
            # ロボットからの返事が無い OR ロボットからの返事がエラーなら OR チェックサムに問題があれば
            if (received_data_str == "b''") or ("&" in received_data_str) or (received_SC_str != calculated_SC_str):
                print("Request retry ...(Now:%d)" % self.request_cnt)
                self.request_cnt += 1 # カウンタ加算後、ループの最初に戻る
                if(self.request_cnt == 10):
                    print("The number of the retry is MAX.")
                    break                
            # ロボットからの返事が正常なら
            else:
                # print("Success")
                break

        return (received_data_str)
    
    # SC(チェックサム)を計算する
    def calcSC(self, cmd):
        # raw_SC = [int(hex(ord(cmd[i])).replace("0x","")) for i, s in enumerate(cmd)]
        raw_SC = [int(ord(cmd[i])) for i, s in enumerate(cmd)]
        sum_SC = sum(raw_SC)
        sum_SC_str = hex(sum_SC).upper().replace("0X","")
        revised_sum_SC_str = sum_SC_str[-2:]
        SC_high_str = revised_sum_SC_str[0]
        SC_low_str = revised_sum_SC_str[1]
        return SC_high_str, SC_low_str
    
    # 指定したbit単位で取り出す
    def getBytesBase(self, value, target, length):
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
    def moveJogBase(self, axis_str, dir_str):       
        # +方向なら
        if (dir_str == '+'):
            act_cmd_str = '1'
        # -方向なら
        elif (dir_str == '-'):
            act_cmd_str = '0'
            
        # X軸移動なら
        if (axis_str == 'x'):
            axis_cmd_str = '01'
        # Y軸移動なら
        elif (axis_str == 'y'):
            axis_cmd_str = '02'
        # Z軸移動なら
        elif (axis_str == 'z'):
            axis_cmd_str = '04'
        # R軸移動なら
        elif (axis_str == 'r'):
            axis_cmd_str = '08'
                   
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                      # 初期化
        cmd_data_string.append(HEADER_STRING)                     # ヘッダー
        cmd_data_string.append(STATION_STRING)                    # 局
        cmd_data_string.append('236')                             # 伝文ID
        cmd_data_string.append(axis_cmd_str)                      # 軸パターン
        cmd_data_string.append('0000')                            # 加速度(0.01G)
        cmd_data_string.append('0000')                            # 減速度(0.01G)
        cmd_data_string.append('0000')                            # 速度(mm/sec)
        cmd_data_string.append('00000000')                        # インチング距離(0.001mm, 0mm=Jog)
        cmd_data_string.append(act_cmd_str)                       # 動作種別(BIT0(ジョグ・インチング方向):0=座標-方向/1=座標+方向)
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))   # SC計算
        cmd_data_string.append(high_SC+low_SC)                    # SC
        cmd_data_string.append('\r')                              # CR
        cmd_data_string.append('\n')                              # LF
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
        # R軸移動なら
        elif (axis_str == 'R'):
            axis_cmd_str = '08'
        # インチング幅を、16進数8桁に変換
        width_cmd_str = self.convBytes2StrBase(width_val*1000, 8)
        
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                      # 初期化
        cmd_data_string.append(HEADER_STRING)                     # ヘッダー
        cmd_data_string.append(STATION_STRING)                    # 局
        cmd_data_string.append('2D5')                             # 伝文ID
        cmd_data_string.append(axis_cmd_str)                      # 軸パターン
        cmd_data_string.append('000A')                            # 加速度(0.01G)
        cmd_data_string.append('000A')                            # 減速度(0.01G)
        cmd_data_string.append('000A')                            # 速度(mm/sec)
        cmd_data_string.append('03')                              # 位置決め動作種別
        cmd_data_string.append(width_cmd_str)                     # 相対座標データ
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))   # SC計算
        cmd_data_string.append(high_SC+low_SC)                    # SC
        cmd_data_string.append('\r')                              # CR
        cmd_data_string.append('\n')                              # LF
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
        cmd_data_string = []                                      # 初期化
        cmd_data_string.append(HEADER_STRING)                     # ヘッダー
        cmd_data_string.append(STATION_STRING)                    # 局
        cmd_data_string.append('238')                             # 伝文ID
        cmd_data_string.append('0F')                              # 停止軸パターン
        cmd_data_string.append('00')                              # 付加コマンドバイト
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))   # SC計算
        cmd_data_string.append(high_SC+low_SC)                    # SC
        cmd_data_string.append('\r')                              # CR
        cmd_data_string.append('\n')                              # LF
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
  
    # P.38:絶対座標指定移動
    # pos:mm, vel:mm/s, acc,dec:G
    def moveAbsoluteLineBase(self, x_pos, y_pos, z_pos, r_pos, vel, acc, dec):
        # 使用する軸の位置データ格納
        abs_pos_data = []
        abs_pos_data.append(self.convBytes2StrBase(x_pos*1000, 8))
        rest_abs_pos_data = []
        rest_abs_pos_data.append(self.convBytes2StrBase(y_pos*1000, 8))
        rest_abs_pos_data.append(self.convBytes2StrBase(z_pos*1000, 8))
        if (MAX_AXIS >= 4): rest_abs_pos_data.append(self.convBytes2StrBase(r_pos*1000, 8))
                
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                              # 初期化
        cmd_data_string.append(HEADER_STRING)                             # ヘッダー
        cmd_data_string.append(STATION_STRING)                            # 局
        cmd_data_string.append('234')                                     # 伝文ID
        cmd_data_string.append(AXIS_PATTERN)                              # 軸パターン
        cmd_data_string.append(self.convBytes2StrBase(acc*100, 4))        # 加速度(0.01G)
        cmd_data_string.append(self.convBytes2StrBase(dec*100, 4))        # 減速度(0.01G)
        cmd_data_string.append(self.convBytes2StrBase(vel, 4))            # 速度(mm/sec)
        cmd_data_string.append(abs_pos_data[0])                           # 絶対座標データ(0.001mm)
        cmd_data_string.append(''.join(rest_abs_pos_data))                # 残絶対座標データ(0.001mm)
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))           # SC計算
        cmd_data_string.append(high_SC+low_SC)                            # SC
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

    # P.39:相対座標指定移動
    # pos:mm, vel:mm/s, acc,dec:G   
    def moveRelativeBase(self, x_pos: float, y_pos: float, z_pos: float, r_pos: float, vel: int, acc: int, dec: int) -> None:
        # 使用する軸の位置データ格納
        abs_pos_data = []
        abs_pos_data.append(self.convBytes2StrBase(x_pos*1000, 8))
        rest_abs_pos_data = []
        rest_abs_pos_data.append(self.convBytes2StrBase(y_pos*1000, 8))
        rest_abs_pos_data.append(self.convBytes2StrBase(z_pos*1000, 8))
        if (MAX_AXIS >= 4): rest_abs_pos_data.append(self.convBytes2StrBase(r_pos*1000, 8))
    
        # # X軸移動なら
        # if (axis_str == 'X'):
        #     axis_cmd_str = '01'
        # # Y軸移動なら
        # elif (axis_str == 'Y'):
        #     axis_cmd_str = '02'
        # # Z軸移動なら
        # elif (axis_str == 'Z'):
        #     axis_cmd_str = '04'
        # # R軸移動なら
        # elif (axis_str == 'R'):
        #     axis_cmd_str = '08'
                    
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                              # 初期化
        cmd_data_string.append(HEADER_STRING)                             # ヘッダー
        cmd_data_string.append(STATION_STRING)                            # 局
        cmd_data_string.append('235')                                     # 伝文ID
        cmd_data_string.append(AXIS_PATTERN)                              # 軸パターン
        cmd_data_string.append(self.convBytes2StrBase(acc*100, 4))        # 加速度(0.01G)
        cmd_data_string.append(self.convBytes2StrBase(dec*100, 4))        # 減速度(0.01G)
        cmd_data_string.append(self.convBytes2StrBase(vel, 4))            # 速度(mm/sec)
        cmd_data_string.append(abs_pos_data[0])                           # 絶対座標データ(0.001mm)
        cmd_data_string.append(''.join(rest_abs_pos_data))                # 残絶対座標データ(0.001mm)
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))           # SC計算
        cmd_data_string.append(high_SC+low_SC)                            # SC
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
        cmd_data_string = []                                              # 初期化
        cmd_data_string.append(HEADER_STRING)                             # ヘッダー
        cmd_data_string.append(STATION_STRING)                            # 局
        cmd_data_string.append('252')                                     # 伝文ID
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))           # SC計算
        cmd_data_string.append(high_SC+low_SC)                            # SC
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

    # P.66:原点復帰
    def moveOriginBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                      # 初期化
        cmd_data_string.append(HEADER_STRING)                     # ヘッダー
        cmd_data_string.append(STATION_STRING)                    # 局
        cmd_data_string.append('233')                             # 伝文ID
        cmd_data_string.append(AXIS_PATTERN)                      # 軸パターン
        cmd_data_string.append('010')                             # 原点復帰時エンドサーチ速度(mm/sec)
        cmd_data_string.append('010')                             # 原点復帰時エンドサーチ速度(mm/sec)
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))   # SC計算
        cmd_data_string.append(high_SC+low_SC)                    # SC
        cmd_data_string.append('\r')                              # CR
        cmd_data_string.append('\n')                              # LF
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
        cmd_data_string = []                                      # 初期化
        cmd_data_string.append(HEADER_STRING)                     # ヘッダー
        cmd_data_string.append(STATION_STRING)                    # 局
        cmd_data_string.append('232')                             # 伝文ID
        cmd_data_string.append(AXIS_PATTERN)                      # 軸パターン
        cmd_data_string.append('1')                               # 動作種別
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))   # SC計算
        cmd_data_string.append(high_SC+low_SC)                    # SC
        cmd_data_string.append('\r')                              # CR
        cmd_data_string.append('\n')                              # LF
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
        cmd_data_string = []                                              # 初期化
        cmd_data_string.append(HEADER_STRING)                             # ヘッダー
        cmd_data_string.append(STATION_STRING)                            # 局
        cmd_data_string.append('232')                                     # 伝文ID
        cmd_data_string.append(AXIS_PATTERN)                              # 軸パターン
        cmd_data_string.append('0')                                       # 動作種別
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))           # SC計算
        cmd_data_string.append(high_SC+low_SC)                            # SC
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

    # P113:ユニット軸ステータス取得
    def getUnitStatusBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                              # 初期化
        cmd_data_string.append(HEADER_STRING)                             # ヘッダー
        cmd_data_string.append(STATION_STRING)                            # 局
        cmd_data_string.append('212')                                     # 伝文ID
        cmd_data_string.append(AXIS_PATTERN)                              # 軸パターン
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))           # SC計算
        cmd_data_string.append(high_SC+low_SC)                            # SC
        cmd_data_string.append('\r')                                      # CR
        cmd_data_string.append('\n')                                      # LF
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
        if (MAX_AXIS >=4):
            res_data_val.append(2)               # R軸ステータス
            res_data_val.append(1)               # R軸センサ入力ステータス
            res_data_val.append(3)               # R軸関連エラー
            res_data_val.append(2)               # R軸エンコーダステータス
            res_data_val.append(8)               # R軸現在位置
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
        if (MAX_AXIS >=4): self.current_pos[Rz] = self.convStr2DecBase(received_data_str[23]) 
        ##############################################################
        # 軸ステータス
        ############################################################## 
        # X
        # self.moving_axis[X]     = True if self.getBytesBase(int(received_data_str[4], 16), 0, 1) == 1 else False  # move_status 
        self.origin_axis[X]     = True if self.getBytesBase(int(received_data_str[4], 16), 2, 1) == 1 else False  # home_high 
        self.servo_axis[X]      = True if self.getBytesBase(int(received_data_str[4], 16), 3, 1) == 1 else False  # servo_status 
        # self.cmd_result_axis[X] = True if self.getBytesBase(int(received_data_str[4], 16), 4, 1) == 1 else False  # cmd_result       
        # Y    
        # self.moving_axis[Y]     = True if self.getBytesBase(int(received_data_str[9], 16), 0, 1) == 1 else False  # move_status 
        self.origin_axis[Y]     = True if self.getBytesBase(int(received_data_str[9], 16), 2, 1) == 1 else False  # home_high 
        self.servo_axis[Y]      = True if self.getBytesBase(int(received_data_str[9], 16), 3, 1) == 1 else False  # servo_status 
        # self.cmd_result_axis[Y] = True if self.getBytesBase(int(received_data_str[9], 16), 4, 1) == 1 else False  # cmd_result       
        # Z    
        # self.moving_axis[Z]     = True if self.getBytesBase(int(received_data_str[14], 16), 0, 1) == 1 else False  # move_status 
        self.origin_axis[Z]     = True if self.getBytesBase(int(received_data_str[14], 16), 2, 1) == 1 else False  # home_high 
        self.servo_axis[Z]      = True if self.getBytesBase(int(received_data_str[14], 16), 3, 1) == 1 else False  # servo_status 
        # self.cmd_result_axis[Z] = True if self.getBytesBase(int(received_data_str[14], 16), 4, 1) == 1 else False  # cmd_result           
        # R  
        if (MAX_AXIS >=4):  
            # self.moving_axis[Rz]     = True if self.getBytesBase(int(received_data_str[19], 16), 0, 1) == 1 else False  # move_status 
            self.origin_axis[Rz]     = True if self.getBytesBase(int(received_data_str[19], 16), 2, 1) == 1 else False  # home_high 
            self.servo_axis[Rz]      = True if self.getBytesBase(int(received_data_str[19], 16), 3, 1) == 1 else False  # servo_status 
            # self.cmd_result_axis[Rz] = True if self.getBytesBase(int(received_data_str[19], 16), 4, 1) == 1 else False  # cmd_result           


    # P32:システムステータス照会
    def getSystemStatusBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                              # 初期化
        cmd_data_string.append(HEADER_STRING)                             # ヘッダー
        cmd_data_string.append(STATION_STRING)                            # 局
        cmd_data_string.append('215')                                     # 伝文ID
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))           # SC計算
        cmd_data_string.append(high_SC+low_SC)                            # SC
        cmd_data_string.append('\r')                                      # CR
        cmd_data_string.append('\n')                                      # LF
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
        
        drive_status = True if self.getBytesBase(int(received_data_str[6], 16), 0, 1) == 0 else False  # 運転モードSWステータス:0=AUTO/1=MANUAL
        tp_enable    = True if self.getBytesBase(int(received_data_str[6], 16), 1, 1) == 0 else False  # TPイネーブルSWステータス:0=ON/1=OFF
        emg_stop     = True if self.getBytesBase(int(received_data_str[6], 16), 3, 1) == 1 else False  # 非常停止SWステータス:0=非非常停止/1=非常停止

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
        cmd_data_string = []                                              # 初期化
        cmd_data_string.append(HEADER_STRING)                             # ヘッダー
        cmd_data_string.append(STATION_STRING)                            # 局
        cmd_data_string.append('216')                                     # 伝文ID
        cmd_data_string.append('3')                                       # 種別1(0=システムエラー/1=軸別エラー/2=プログラム別エラー/3=エラーリストレコード内エラー)
        cmd_data_string.append('01')                                      # 種別2(0=最重レベルエラー/1=最新エラー)
        cmd_data_string.append('000')                                     # レコードNo.
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))           # SC計算
        cmd_data_string.append(high_SC+low_SC)                            # SC
        cmd_data_string.append('\r')                                      # CR
        cmd_data_string.append('\n')                                      # LF
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
        self.error_id = int(received_data_str[3], 16) # エラーID
        
    # P22:フラグ照会
    def getFlagStatusBase(self):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                              # 初期化
        cmd_data_string.append(HEADER_STRING)                             # ヘッダー
        cmd_data_string.append(STATION_STRING)                            # 局
        cmd_data_string.append('20D')                                     # 伝文ID
        cmd_data_string.append('00')                                      # プログラムNo.(グローバルフラグ=00)
        cmd_data_string.append('0258')                                    # 照会開始フラグNo.
        cmd_data_string.append('0008')                                    # 照会フラグ数
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))           # SC計算
        cmd_data_string.append(high_SC+low_SC)                            # SC
        cmd_data_string.append('\r')                                      # CR
        cmd_data_string.append('\n')                                      # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(2)                   # プログラムNo.(グローバルフラグ=00)
        res_data_val.append(4)                   # レスポンス開始フラグNo.
        res_data_val.append(4)                   # レスポンスフラグ数
        # res_data_val.append(2)                   # フラグデータ（*1）
        res_data_val.append(2)                   # 残フラグデータ
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        # 伝文コマンド生成
        print(cmd_data_string)
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)       
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str)         
        return (received_data_str)   
    
    # P47:フラグ状態変更(ON)
    def setGlobalFlagOnBase(self, flag_no):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                           # 初期化
        cmd_data_string.append(HEADER_STRING)                          # ヘッダー
        cmd_data_string.append(STATION_STRING)                         # 局
        cmd_data_string.append('24B')                                  # 伝文ID
        cmd_data_string.append('00')                                   # プログラムNo.(グローバルフラグ=00)
        cmd_data_string.append(self.convBytes2StrBase(flag_no, 4))     # 照会フラグNo.
        cmd_data_string.append('1')                                    # 変更種別
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))        # SC計算
        cmd_data_string.append(high_SC+low_SC)                         # SC
        cmd_data_string.append('\r')                                   # CR
        cmd_data_string.append('\n')                                   # LF
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
        return (received_data_str)     
    
    # P47:フラグ状態変更(OFF)
    def setGlobalFlagOffBase(self, flag_no):
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                           # 初期化
        cmd_data_string.append(HEADER_STRING)                          # ヘッダー
        cmd_data_string.append(STATION_STRING)                         # 局
        cmd_data_string.append('24B')                                  # 伝文ID
        cmd_data_string.append('00')                                   # プログラムNo.(グローバルフラグ=00)
        cmd_data_string.append(self.convBytes2StrBase(flag_no, 4))     # 照会フラグNo.
        cmd_data_string.append('0')                                    # 変更種別
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))        # SC計算
        cmd_data_string.append(high_SC+low_SC)                         # SC
        cmd_data_string.append('\r')                                   # CR
        cmd_data_string.append('\n')                                   # LF
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
        return (received_data_str)         
    
    def makePointDataBase(self, P):
        # 座標以外はリストの後ろから取得
        dec_str   = self.convBytes2StrBase(P.pop()*100, 4)
        acc_str   = self.convBytes2StrBase(P.pop()*100, 4)
        vel_str   = self.convBytes2StrBase(P.pop(), 4)
        # 座標はリストの前から取得
        x_pos_str = y_pos_str = z_pos_str = r_pos_str = ''
        if(len(P) > 0): x_pos_str = self.convBytes2StrBase(P.pop(0)*1000, 8)
        if(len(P) > 0): y_pos_str = self.convBytes2StrBase(P.pop(0)*1000, 8)
        if(len(P) > 0): z_pos_str = self.convBytes2StrBase(P.pop(0)*1000, 8)
        if((len(P) > 0) and (MAX_AXIS >= 4)): r_pos_str = self.convBytes2StrBase(P.pop(0)*1000, 8)
        # ポイントデータ中身合算
        point_data_str  = AXIS_PATTERN + acc_str + dec_str + vel_str + x_pos_str + y_pos_str + z_pos_str + r_pos_str
        return point_data_str

    def setPointDataBase(self, start_no, range_no, P1, P2, P3, P4):
        # ポイント開始番号
        start_no_str = self.convBytes2StrBase(start_no, 3)
        # # ポイント数確認
        # if   (sum(P1) > 0.0) and (sum(P2) > 0.0) and (sum(P3) > 0.0) and (sum(P4) > 0.0): range_point_val = 4
        # elif (sum(P1) > 0.0) and (sum(P2) > 0.0) and (sum(P3) > 0.0)                    : range_point_val = 3
        # elif (sum(P1) > 0.0) and (sum(P2) > 0.0)                                        : range_point_val = 2
        # elif (sum(P1) > 0.0)                                                            : range_point_val = 1
        # else                                                                            : raise ValueError("Not a point")
        # 送信用ポイントデータ作成
        point_data_str_list = []
        # match range_point_val: python3.10～しか使えない
        #     case 1:
        if (range_no == 1):
            point_data_str_list.append(self.makePointDataBase(P1))
            point_data_str = ''.join(point_data_str_list)
        elif (range_no == 2):
            point_data_str_list.append(self.makePointDataBase(P1))
            point_data_str_list.append(self.makePointDataBase(P2))
            point_data_str = ''.join(point_data_str_list)
        elif (range_no == 3):
            point_data_str_list.append(self.makePointDataBase(P1))
            point_data_str_list.append(self.makePointDataBase(P2))
            point_data_str_list.append(self.makePointDataBase(P3))
            point_data_str = ''.join(point_data_str_list)
        elif (range_no == 4):
            point_data_str_list.append(self.makePointDataBase(P1))
            point_data_str_list.append(self.makePointDataBase(P2))
            point_data_str_list.append(self.makePointDataBase(P3))
            point_data_str_list.append(self.makePointDataBase(P4))
            point_data_str = ''.join(point_data_str_list)
        else:
            raise ValueError("Not a point")
        
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                                     # 初期化
        cmd_data_string.append(HEADER_STRING)                                    # ヘッダー
        cmd_data_string.append(STATION_STRING)                                   # 局
        cmd_data_string.append('244')                                            # 伝文ID
        cmd_data_string.append(start_no_str)                                     # 変更開始ポイントデータNo.
        cmd_data_string.append(self.convBytes2StrBase(range_no, 3))              # 変更ポイントデータ数
        cmd_data_string.append(point_data_str)                                   # ポイントデータ
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))                  # SC計算
        cmd_data_string.append(high_SC+low_SC)                                   # SC
        cmd_data_string.append('\r')                                             # CR
        cmd_data_string.append('\n')                                             # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(3)                   # 変更開始ポイントデータNo.
        res_data_val.append(3)                   # 変更ポイントデータ数
        res_data_val.append(2)                   # SC
        res_data_val.append(1)                   # CR
        res_data_val.append(1)                   # LF
        ##################################################################
        print(cmd_data_string)
        # 伝文コマンド生成
        cmd_data_val = ''.join(cmd_data_string)
        # ロボットにリクエストを送信
        received_row_data_str = self.sendCommandBase(cmd_data_val)       
        # 生データ整形
        received_data_str = self.handleRowDataBase(res_data_val, received_row_data_str)     
        return (received_data_str)      
    
    # P20:入力ポート照会
    def getInputBase(self, port_no) -> bool:  
        port_no_str = self.convBytes2StrBase(port_no, 4)  
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                           # 初期化
        cmd_data_string.append(HEADER_STRING)                          # ヘッダー
        cmd_data_string.append(STATION_STRING)                         # 局
        cmd_data_string.append('20B')                                  # 伝文ID
        cmd_data_string.append(port_no_str)                            # 照会開始ポートNo.
        cmd_data_string.append('000F')                                 # 照会ポート数
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))        # SC計算
        cmd_data_string.append(high_SC+low_SC)                         # SC
        cmd_data_string.append('\r')                                   # CR
        cmd_data_string.append('\n')                                   # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(4)                   # レスポンス開始ポートNo.
        res_data_val.append(4)                   # レスポンスポート数
        res_data_val.append(2)                   # 入力ポートデータ
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
        return (int(received_data_str[5])) # 入力ポートデータ

    # P46:出力ポート状態変更（ON）
    def setOutputONBase(self, port_no):  
        port_no_str = self.convBytes2StrBase(port_no, 4) 
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                           # 初期化
        cmd_data_string.append(HEADER_STRING)                          # ヘッダー
        cmd_data_string.append(STATION_STRING)                         # 局
        cmd_data_string.append('24A')                                  # 伝文ID
        cmd_data_string.append(port_no_str)                            # 出力ポートNo.
        cmd_data_string.append('1')                                    # 変更種別
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))        # SC計算
        cmd_data_string.append(high_SC+low_SC)                         # SC
        cmd_data_string.append('\r')                                   # CR
        cmd_data_string.append('\n')                                   # LF
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
        return (received_data_str)  

    # P46:出力ポート状態変更（OFF）
    def setOutputOFFBase(self, port_no):  
        port_no_str = self.convBytes2StrBase(port_no, 4) 
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                           # 初期化
        cmd_data_string.append(HEADER_STRING)                          # ヘッダー
        cmd_data_string.append(STATION_STRING)                         # 局
        cmd_data_string.append('24A')                                  # 伝文ID
        cmd_data_string.append(port_no_str)                            # 出力ポートNo.
        cmd_data_string.append('0')                                    # 変更種別
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))        # SC計算
        cmd_data_string.append(high_SC+low_SC)                         # SC
        cmd_data_string.append('\r')                                   # CR
        cmd_data_string.append('\n')                                   # LF
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
        return (received_data_str)  


    # P48:グローバル変数値変更
    def setGlobalValueBase(self, start_val, data_val_list):
        start_data_str = self.convBytes2StrBase(start_val, 3)
        range_data_str = self.convBytes2StrBase(len(data_val_list), 2)
        first_data_str = ''
        rest_data_str = ''
        for i, val in enumerate(data_val_list):       
            # データ値を、16進数2桁文字列に変換
            if(i == 0): first_data_str = self.convBytes2StrBase(data_val_list[i], 8)
            else      : rest_data_str  = rest_data_str + self.convBytes2StrBase(data_val_list[i], 8)

        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                           # 初期化
        cmd_data_string.append(HEADER_STRING)                          # ヘッダー
        cmd_data_string.append(STATION_STRING)                         # 局
        cmd_data_string.append('24C')                                  # 伝文ID
        cmd_data_string.append('00')                                   # プログラムNo.(グローバルフラグ=00)
        cmd_data_string.append(start_data_str)                         # 変更開始変数No.
        cmd_data_string.append(range_data_str)                         # 変更変数データ数
        cmd_data_string.append(first_data_str)                         # 整数変数データ
        cmd_data_string.append(rest_data_str)                          # 残整数変数データ
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))        # SC計算
        cmd_data_string.append(high_SC+low_SC)                         # SC
        cmd_data_string.append('\r')                                   # CR
        cmd_data_string.append('\n')                                   # LF
        ##################################################################
        ########################## レスポンス #############################
        res_data_val = [0]                       # 初期化
        res_data_val.append(HEADER_NUM)          # ヘッダー
        res_data_val.append(STATION_NUM)         # 局
        res_data_val.append(3)                   # 伝文ID
        res_data_val.append(2)                   # プログラムNo.
        res_data_val.append(3)                   # 変更開始変数No.
        res_data_val.append(2)                   # 変更完了データ数
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
        return (received_data_str)   

    # P52:プログラム起動
    def startProgramBase(self, prog_no):
        prog_no_str = self.convBytes2StrBase(prog_no, 2)
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                           # 初期化
        cmd_data_string.append(HEADER_STRING)                          # ヘッダー
        cmd_data_string.append(STATION_STRING)                         # 局
        cmd_data_string.append('253')                                  # 伝文ID
        cmd_data_string.append(prog_no_str)                            # プログラムNo.(停止=00)
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))        # SC計算
        cmd_data_string.append(high_SC+low_SC)                         # SC
        cmd_data_string.append('\r')                                   # CR
        cmd_data_string.append('\n')                                   # LF
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
        return (received_data_str)   
    
    # P52:プログラム停止
    def stopProgramBase(self, prog_no):
        prog_no_str = self.convBytes2StrBase(prog_no, 2)
        # 伝文コマンド定義
        ########################### コマンド #############################
        cmd_data_string = []                                           # 初期化
        cmd_data_string.append(HEADER_STRING)                          # ヘッダー
        cmd_data_string.append(STATION_STRING)                         # 局
        cmd_data_string.append('254')                                  # 伝文ID
        cmd_data_string.append(prog_no_str)                            # プログラムNo.(停止=00)
        high_SC, low_SC = self.calcSC(''.join(cmd_data_string))        # SC計算
        cmd_data_string.append(high_SC+low_SC)                         # SC
        cmd_data_string.append('\r')                                   # CR
        cmd_data_string.append('\n')                                   # LF
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
        return (received_data_str)   

if __name__ == '__main__':
    node = RobotApi('192.168.250.11', 23, '/dev/ttyUSB0', 115200)
    # node.setServoOn()
    # node.moveOrigin()
    # node.startProgramBase(50)
    # node.resetError()
    # print(node.setGlobalValueBase(200, [50, 52]))
    # node.setGrobalFlagOnBase(600)
    # node.setGrobalFlagOffBase(600)
    # node.setOutputONBase(316)
    print(node.getInput(3))
    
    # P1 = [1, 2, 3, 5, 6, 7] 
    # P2 = [1, 2, 3, 5, 6, 7] 
    # P3 = [1, 2, 3, 5, 6, 7] 
    # P4 = [1, 2, 3, 5, 6, 7]     
    # P1 = [11, 22, 33, 44, 55, 0.6, 0.7] 
    # P2 = [11, 22, 33, 44, 55, 0.6, 0.7] 
    # P3 = [11, 22, 33, 44, 55, 0.6, 0.7] 
    # P4 = [11, 22, 33, 44, 55, 0.6, 0.7] 
    # print(node.setPointDataBase(50, P1, P2))    
    # node.setPointDataBase(pos_X_1=1.0, pos_Y_1=2.0, pos_Z_1=3.0, vel_1=5.0, acc_1=6.0, dec_1=7.0, 
    #                       pos_X_2=1.0, pos_Y_2=2.0, pos_Z_2=3.0, vel_2=5.0, acc_2=6.0, dec_2=7.0,
    #                       pos_X_3=1.0, pos_Y_3=2.0, pos_Z_3=3.0, vel_3=5.0, acc_3=6.0, dec_3=7.0,
    #                       pos_X_4=1.0, pos_Y_4=2.0, pos_Z_4=3.0, vel_4=5.0, acc_4=6.0, dec_4=7.0)
