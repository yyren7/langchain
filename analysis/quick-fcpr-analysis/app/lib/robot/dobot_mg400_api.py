# -*- coding : UTF-8 -*-

from socket import *
import select
from time import sleep, perf_counter
from multiprocessing import Process, Value, Array
import numpy as np
from typing import Tuple, List, Union, Optional
import struct

# official api
import socket
from threading import Timer
from tkinter import Text, END
import datetime
import numpy as np


# To read .ini file
import configparser

#############################################################
# グローバル変数定義
#############################################################
X = 0
Y = 1
Z = 2
RX = 3
RY = 4
RZ = 5
CHECK_MOVING_DIFF = 0.1

GRAVITY = 9800
XYZ_MAX_JERK = 30000
R_MAX_JERK = 30000
XYZ_MAX_ACC = 3000
R_MAX_ACC = 6000
XYZ_MAX_VEL = 250
R_MAX_VEL = 600

ERROR_LIST = [
    ['none1', 1],           # 非常停止ON
    ['r6', 2],               # サーボOFF　軸使用エラー
    ['none2', 3],            # 原点復帰未完了エラー
    ['17', 4],               # 目標位置ソフトリミットオーバー
    ['23', 5],               # 目標軌跡ソフトリミットオーバーエラー
    ['18', 6],              # 実位置ソフトリミットオーバーエラー
    ['-2', 7],                # 過負荷エラー　復帰不可
    ['12294', 8],              # 衝突検知エラー　復帰可
    ["other", 32]            # その他のエラー
]


class RobotApi():
    def __init__(self, dst_ip_address: str, dst_port: str, dev_port: str, baurate: int):
        ##############################################################
        # ロボット状態通知用変数定義(数値)
        ##############################################################
        self.current_pos: List[float] = [0.0] * 6
        self.pre_current_pos: List[float] = [0.0] * 6
        self.input_signal: List[bool] = [False] * 16
        self.error_id: int = 0
        ##############################################################
        # ロボット状態通知用変数定義(フラグ)
        ##############################################################
        self.error: bool = False
        self.servo: bool = False
        self.emerge: bool = False
        self.origin: bool = False
        self.moving: bool = False
        self.dragging: bool = False
        self.arrived: bool = False

        ##############################################################
        # Dobot　固有変数定義
        ##############################################################
        # Valueオブジェクトの生成
        self._robot_mode: int = Value('i', 0)
        self.robot_mode = 0
        # 電源確認用フラグ
        self.opening = False
        # self変数
        self.dst_ip_address = dst_ip_address
        self.dst_port = dst_port
        ##############################################################
        # ロボット接続開始
        ##############################################################
        self.openRobot(self.dst_ip_address, self.dst_port)
        ##############################################################
        # エラーリスト
        ##############################################################
        self.error_list = {
            "1": "Emergency stop ON",
            "2": "Servo OFF",
            "3": "Homing incomplete error",
            "4": "Target position soft limit exceeded",
            "5": "Target trajectory soft limit exceeded",
            "6": "Actual position soft limit exceeded",
            "7": "Overload",
            "8": "Collision detection",
            "32": "Critical Error",
        }

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
        self.dst_ip_address = dst_ip_address
        # ロボットサーバに接続
        print("Start to connet robot.")
        self.connectRobotBase()
        self.resetError()
        self.setTool(tool_no=0)
        self.setUser(user_no=0)
        self.mySleepBase(0.5)
        self.startMultiFeedbackBase()
        print("Finished to connet robot.")
        print("Connected to: " + self.dst_ip_address)

        # # 初期パラメータセット
        # self.setInitialRobotParamBase()

    def closeRobot(self) -> None:
        """ ロボット通信を解除
        """
        # self.setServoOff()
        self.mySleepBase(0.5)
        self.feed.close()
        self.move.close()
        self.dashboard.close()

    # 2023/1/13追加　ready用

    def readyRobot(self):
        self.setServoOn()
        self.setInitialRobotParamBase()

    def getRobotStatus(self) -> None:
        """ ロボット状態を取得
        """
        ##############################################################
        # 電源確認
        ##############################################################
        try:
            # print(f"opening is {self.opening}")
            # robotがオープンしていないまたは各ポートでエラーの時
            if (not self.opening or
                self.dashboard._error or
                self.feed._error or
                    self.move._error):
                ########################### 設定 #############################
                timeout_in_seconds = 1.0
                self.dashboard.socket_dobot.setblocking(
                    False)  # Non-blockingモードに設定
                cmd_val = "RobotMode()"
                ########################### データ送信 #############################
                self.dashboard.socket_dobot.send(cmd_val.encode())
                # サーバーからのレスポンス格納し、タイムアウトを設定
                ready = select.select([self.dashboard.socket_dobot],
                                      [], [], timeout_in_seconds)
                # サーバーからのレスポンスがあれば
                if ready[0]:
                    print("get a socket response")
                    self.dashboard._error = False
                    self.feed._error = False
                    self.move._error = False
                    # print("close a previous socket")
                    # self.feed.close()
                    # self.move.close()
                    # self.dashboard.close()
                    ########################### 接続 ############################
                    # # ロボット接続開始
                    # print("retry a robot connecting")
                    # self.openRobot(self.dst_ip_address, self.dst_port)

                else:
                    print("wait a robot booting")
                    self.mySleepBase(1)
            else:
                ##############################################################
                # エラー状態確認
                ##############################################################
                self.checkErrorBase()
                ##############################################################
                # 現在地の直交座標取得
                ##############################################################
                self.current_pos = self.getCurrentPos()

                ##############################################################
                # ロボットモードを更新
                ##############################################################
                self.robot_mode = self._robot_mode.value

                ##############################################################
                # サーボ状態監視
                ##############################################################
                if (self.robot_mode == 4):
                    self.servo = False
                elif (self.robot_mode == 5):
                    self.servo = True

                ##############################################################
                # INPUT状態取得
                ##############################################################
                # self.input_signal[0] = self.getInput(1)
                # self.input_signal[1] = self.getInput(2)
                # self.input_signal[2] = self.getInput(3)
                # self.input_signal[3] = self.getInput(4)
                # self.input_signal[4] = self.getInput(5)
                # self.input_signal[5] = self.getInput(6)
                # self.input_signal[6] = self.getInput(7)
                # self.input_signal[7] = self.getInput(8)
                # self.input_signal[8] = self.getInput(9)
                # self.input_signal[9] = self.getInput(10)
                # self.input_signal[10] = self.getInput(11)
                # self.input_signal[11] = self.getInput(12)
                # self.input_signal[12] = self.getInput(13)
                # self.input_signal[13] = self.getInput(14)
                # self.input_signal[14] = self.getInput(15)
                # self.input_signal[15] = self.getInput(16)
                
                ##############################################################
                # Moving確認
                ##############################################################
                self.checkMovingBase()
                self.pre_current_pos = self.current_pos

                ##############################################################
                # origin確認
                ##############################################################
                self.origin = True
                ##############################################################
                # エラーステータス取得(エラー発生時のみ)
                ##############################################################
                if (self.error == True):
                    self.error_id = self.getErrorBase()
                else:
                    self.error_id = 0
        except BrokenPipeError as e:
            # Broken pipe エラーが発生した場合の処理
            print("Broken pipe エラーが発生しました\n", str(e))
            # self.feed.close()
            # self.move.close()
            # self.dashboard.close()

        except (OSError, FileNotFoundError) as e:
            # Bad file descriptor エラーが発生した場合の処理
            print("Bad file descriptor エラーが発生しました\n", str(e))
            # self.feed.close()
            # self.move.close()
            # self.dashboard.close()
            self.mySleepBase(15)
            # ロボット接続開始
            print("retry a robot connecting")
            self.openRobot(self.dst_ip_address, self.dst_port)

        except Exception as e:
            print(e)

    def setTool(self, tool_no: int) -> None:
        """ ツール座標系設定
        tool_no : int
            ツール座標番号
        """
        self.setToolBase(tool_no=tool_no)

    def setUser(self, user_no: int) -> None:
        """ ツール座標系設定
        tool_no : int
            ツール座標番号
        """
        self.setUserBase(user_no=user_no)

    def getCurrentPos(self) -> None:
        """ 現在地の直交座標取得
        """
        val = self.getCurrentPosBase()
        return val

    def getCurrentJoint(self) -> None:
        """ 現在地のジョイント座標取得
        """
        val = self.getCurrentJointBase()
        return val

    def getPos2Joint(self, x: float, y: float, z: float, r: float) -> None:
        """ 直交座標をジョイント座標へ変換
        """
        ret = self.move.InverseSolution(x, y, z, r, 0, 0, 0, 0)
        self.checkApiErrorBase()
        val = self.transformStr2Joint(ret)
        return val

    def getJoint2Pos(self, j1: float, j2: float, j3: float, j4: float) -> None:
        """ ジョイント座標を直交座標へ変換
        """
        ret = self.move.PositiveSolution(j1, j2, j3, j4, 0, 0, 0, 0)
        self.checkApiErrorBase()
        val = self.transformStr2Pos(ret)
        return val

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
        # 現在地の直交座標取得
        ##############################################################
        self.current_pos = self.getCurrentPos()
        ##############################################################
        # arrived確認
        ###############################################################
        # 現在位置と目標位置の差分取得
        diff_pos = [abs(x - y) for (x, y) in zip(target_pos, self.current_pos)]
        # print("diff_pos",diff_pos)
        # 差分が設定値以内なら
        if ((diff_pos[X] <= width)
                and (diff_pos[Y] <= width)
                and (diff_pos[Z] <= width)
                and (diff_pos[RX] <= width)
                and (diff_pos[RY] <= width)
                and (diff_pos[RZ] <= width)):
            self.arrived = True
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

        acc_line_val = (acc / XYZ_MAX_ACC) * 9800 * 100
        vel_line_val = (vel / XYZ_MAX_VEL) * 100
        acc_joint_val = (acc / XYZ_MAX_ACC) * 9800 * 100
        vel_joint_val = (vel / XYZ_MAX_VEL) * 100

        # パーセントに換算
        self.setAccLineBase(acc_line_val)
        self.setVelLineBase(vel_line_val)
        self.setAccJointBase(acc_joint_val)
        self.setVelJointBase(vel_joint_val)

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
        self.moveAbsolutePtpBase(x, y, z, rx, ry, rz, vel, acc, dec)

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
        self.moveAbsoluteLineBase(x, y, z, rx, ry, rz, vel, acc, dec)

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
        self.moveRelativeBase(x, y, z, rx, ry, rz, vel, acc, dec)

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

    def moveJog(self, axis_char_str: str, direction_char_str: str, vel: int) -> None:
        """ 手動移動：ジョグ
        Parameters
        ----------
        axis_char_str : str
            軸(ex. "x")
        direction_char_str : str
            回転方向(ex. "+")
        """
        self.moveJogBase(axis_char_str, direction_char_str)

    def stopJog() -> None:
        """ 手動移動：ジョグ停止
        Parameters
        ----------
        """
        pass

    def getInput(self, pin_no: int) -> None:
        """ ポート入力状態参照
        """
        self.input_signal[pin_no-1] = self.getInputBase(pin_no)  

    def setOutputON(self, pin_no: int) -> None:
        """ ポート出力状態変更
        """
        self.setOutputONBase(pin_no)   

    def setOutputOFF(self, pin_no: int) -> None:
        """ ポート出力状態変更
        """
        self.setOutputOFFBase(pin_no)   

    def printRobotStatus(self) -> None:
        """ 変数表示(デバッグ用)
        """
        print("##########################  Status  ##############################################")
        print('X  = {0:.3f}'.format(self.current_pos[X]))
        print('Y  = {0:.3f}'.format(self.current_pos[Y]))
        print('Z  = {0:.3f}'.format(self.current_pos[Z]))
        print('R  = {0:.3f}'.format(self.current_pos[RZ]))
        print("emerge -> " + str(self.emerge) + ", " + "error -> ", str(self.error) + ", " + "servo -> ", str(self.servo) + ", " + "moving -> " +
              str(self.moving) + ", " + "origin -> ", str(self.origin) + ", " + "arrived -> ", str(self.arrived) + ", " + "dragging -> ", str(self.dragging))
        print("error id = ", self.error_id)
        print("##################################################################################")

    #############################################################
    # ロボット固有関数
    #############################################################
    def setInitialRobotParamBase(self):
        default = 50
        self.setAccLineBase(default)
        self.setVelLineBase(default)
        self.setAccJointBase(default)
        self.setVelJointBase(default)

    # NOTE:apiのコマンドエラー確認
    def checkApiErrorBase(self, ret: str):
        api_err = False
        _ret = self.transformStr2Ret(ret)
        if _ret != 0:
            self.error = True
            # error_id = self.transformStr2Error(ret)
            if _ret == -1:
                print("Fail to get\nApi Error No.", _ret, ret)
            else:
                print("Api Error No.", _ret)
                api_err = True
        return api_err

    def mySleepBase(self, sleep_time):
        now = perf_counter()
        while (perf_counter() - now < sleep_time):
            pass

    def connectRobotBase(self):
        try:
            ip = self.dst_ip_address
            # NOTE:以下は固定値
            dashboard_p = 29999
            move_p = 30003
            feed_p = 30004
            self.dashboard = DobotApiDashboard(ip, dashboard_p)
            self.move = DobotApiMove(ip, move_p)
            self.feed = DobotApi(ip, feed_p)
            self.opening = True  # Dobot電源確認用
            # return dashboard, move, feed
        except Exception as e:
            print("Fail to connect")
            self.opening = False  # Dobot電源確認用
            raise e

    # NOTE:並列処理開始
    def startMultiFeedbackBase(self):
        self.feed_process = Process(target=self.getFeedbackBase)
        self.feed_process.daemon = True
        self.feed_process.start()
        return

    # NOTE:フィードバックループ #RB電源遮断時例外処理
    def getFeedbackBase(self):
        ########################### 設定 #############################
        buffer_size = 1440
        timeout_in_seconds = 5.0
        hasRead = 0
        sleep_t = 0.001
        self.feed.socket_dobot.setblocking(False)  # Non-blockingモードに設定
        cmd_val = ""
        ########################### データ送信 #############################
        self.feed.socket_dobot.send(cmd_val.encode())
        while True:
            try:
                data = bytes()
                while hasRead < 1440:
                    # サーバーからのレスポンス格納し、タイムアウトを設定
                    ready = select.select(
                        [self.feed.socket_dobot], [], [], timeout_in_seconds)
                    # サーバーからのレスポンスがあれば
                    if ready[0]:
                        temp = self.feed.socket_dobot.recv(
                            buffer_size - hasRead)
                        if len(temp) > 0:
                            hasRead += len(temp)
                            data += temp
                    else:
                        print("can not get robot feedback")
                        self.opening = False
                        break

            except Exception:
                print("Exception disconneted robot")
                self.opening = False

            if self.opening:  # dobot alive
                hasRead = 0
                a = np.frombuffer(data, dtype=MyType)
                if hex((a['test_value'][0])) == '0x123456789abcdef':
                    # Refresh Properties
                    # self.current_actual = a["tool_vector_actual"][0]
                    # print("ROBOTループ",int(a["robot_mode"][0]))
                    self._robot_mode.value = int(a["robot_mode"][0])
                    # print("robot_mode",self._robot_mode.value)
                self.mySleepBase(sleep_t)
            else:  # dobot dead
                print("dobot dead")
                break

    # NOTE:ret文字列を配列へ変換

    def transformStr2Ret(self, str: str):
        if not str:
            ret = 0
        else:
            # "{"" and "}" and ";"の削除
            align_str = str.replace('{', '').replace('}', '').replace(';', '')
            align_list = align_str.split(',')
            # float型にキャスト
            ret = int(align_list[0])
        return ret

    # NOTE:座標文字列を配列へ変換
    def transformStr2Pos(self, str: str):
        if not str:
            ret = 0
        else:
            # "{"" and "}" and ";"の削除
            align_str = str.replace('{', '').replace('}', '').replace(';', '')
            align_list = align_str.split(',')
            # print(align_list)
            # 0番目と後ろから4番目以降を削除
            del align_list[0]
            del align_list[-4:]
            # float型にキャスト
            ret = [float(val) for val in align_list]
        return ret

    # NOTE:座標文字列を配列へ変換
    def transformStr2Joint(self, str: str):
        # "{"" and "}" and ";"の削除
        align_str = str.replace('{', '').replace('}', '').replace(';', '')
        align_list = align_str.split(',')
        # 0番目と後ろから3番目以降を削除
        del align_list[0]
        del align_list[-3:]
        # float型にキャスト
        ret = [float(val) for val in align_list]
        return ret

    # NOTE:エラーコード文字列を数値へ変換
    def transformStr2Error(self, str: str):
        align_str = str.replace('{', '').replace('}', '').replace(';', '').replace(
            '\n', '').replace('\t', '').replace('[', '').replace(']', '')
        align_list = align_str.split(',')
        try:
            ret = int(align_list[1])
        except:
            ret = 0
        return ret

    def stopRobotBase(self) -> None:
        ret = self.dashboard.ResetRobot()
        self.checkApiErrorBase(ret)
        return

    # NOTE:Moving発生確認
    def checkMovingBase(self):
        if self.robot_mode == 7:
            self.moving = True
        else:
            self.moving = False

    # NOTE:エラー発生確認
    def checkErrorBase(self):
        if self.robot_mode == 9:
            self.error = True

    def transformCommmonErrorID(self, error_id):
        error_dict = dict(ERROR_LIST)
        # dragging mode on
        if self.robot_mode == 6:
            self.error = True
            _tmp_error_id = "r" + str(self.robot_mode)
            common_error_id = error_dict[str(_tmp_error_id)]
            return common_error_id

        # エラー未発生は無視
        # if error_id == 0 or error_id == 12294:
        if error_id == 0:
            common_error_id = 0

        # error 発生時
        else:
            try:
                common_error_id = error_dict[str(error_id)]
            except Exception:
                # other error
                common_error_id = 32

        return common_error_id

    # NOTE:エラー番号の取得
    def getErrorBase(self):
        ret = self.dashboard.GetErrorID()
        val = self.transformStr2Error(ret)
        com_err_id = self.transformCommmonErrorID(val)
        return com_err_id

    def moveAbsolutePtpBase(self,
                            x: float,
                            y: float,
                            z: float,
                            rx: float,
                            ry: float,
                            rz: float,
                            vel: float = 100,
                            acc: float = 100,
                            dec: float = 100) -> None:
        # パーセントに換算
        vel_joint_val = int(vel)
        acc_joint_val = int(acc)
        # rzを従来のハンド周りのR座標系として使う
        print(vel_joint_val)
        ret = self.move.MovJ(x, y, z, rz, (vel_joint_val, acc_joint_val))
        self.checkApiErrorBase(ret)
        return

    def moveAbsoluteLineBase(self,
                             x: float,
                             y: float,
                             z: float,
                             rx: float,
                             ry: float,
                             rz: float,
                             vel: float = 100,
                             acc: float = 100,
                             dec: float = 100) -> None:
        # パーセントに換算
        vel_line_val = int(vel)
        acc_line_val = int(acc)
        ret = self.move.MovL(x, y, z, rz, (vel_line_val, acc_line_val))
        self.checkApiErrorBase(ret)
        return

    def moveRelativeBase(self,
                         x: float,
                         y: float,
                         z: float,
                         rx: float,
                         ry: float,
                         rz: float,
                         vel: int = 100,
                         acc: int = 100,
                         dec: int = 100) -> None:
        current_list = self.getCurrentPosBase()
        offset_list = [x, y, z, rx, ry, rz]
        target_list = []
        for i in range(6):
            val = current_list[i] + offset_list[i]
            target_list.append(val)
        ret = self.moveAbsoluteLineBase(x=target_list[X],
                                        y=target_list[Y],
                                        z=target_list[Z],
                                        rx=0,
                                        ry=0,
                                        rz=target_list[RZ],  # index RX=3
                                        vel=vel,
                                        acc=acc,
                                        dec=dec)
        self.checkApiErrorBase(ret)
        return

    def moveOriginBase(self) -> None:
        pass

    def setServoOnBase(self):
        ret = self.dashboard.EnableRobot()
        self.checkApiErrorBase(ret)
        # self.servo = True
        return

    def setServoOffBase(self):
        ret = self.dashboard.DisableRobot()
        self.checkApiErrorBase(ret)
        # self.servo = False
        return

    def resetErrorBase(self):
        self.error = False
        ret = self.dashboard.ClearError()
        self.checkApiErrorBase(ret)
        if self.servo:
            self.setServoOff()
        return

    def moveInchingBase(self, width: int, axis_char_str: str, direction_char_str: str) -> None:
        pass

    def moveJogBase(self, axis_char_str: str, direction_char_str: str) -> None:
        pass

    def setToolBase(self, tool_no: int) -> None:
        self.tool_no = tool_no
        ret = self.dashboard.Tool(int(self.tool_no))
        self.checkApiErrorBase(ret)
        return

    def setUserBase(self, user_no: int) -> None:
        self.user_no = user_no
        ret = self.dashboard.User(self.user_no)
        self.checkApiErrorBase(ret)
        return

    def setAccLineBase(self, val):
        ret = self.dashboard.AccL(int(val))
        self.checkApiErrorBase(ret)
        return

    def setAccJointBase(self, val):
        ret = self.dashboard.AccJ(int(val))
        self.checkApiErrorBase(ret)
        return

    def setVelLineBase(self, val):
        ret = self.dashboard.SpeedL(int(val))
        self.checkApiErrorBase(ret)
        return

    def setVelJointBase(self, val):
        ret = self.dashboard.SpeedJ(int(val))
        self.checkApiErrorBase(ret)
        return

    def setWeightBase(self, weight: int) -> None:
        pass

    def getCurrentPosBase(self) -> List[float]:
        ret = self.dashboard.GetPoseTool(self.user_no, self.tool_no)
        self.checkApiErrorBase(ret)
        val = self.transformStr2Pos(ret)
        # not int
        if not isinstance(val, int):
            if len(val) > 0:
                val.insert(RX, 0)  # RX要素
                val.insert(RY, 0)  # RY要素
            else:
                val = [0.0] * 6
        else:
            val = [0.0] * 6
        return val

    def getCurrentJointBase(self) -> List[float]:
        ret = self.dashboard.GetAngle()
        val = self.transformStr2Joint(ret)
        self.checkApiErrorBase(ret)
        return val

    def getInputBase(self, pin_no):
        no = pin_no
        ret = self.dashboard.DI(no)
        self.checkApiErrorBase(ret)
        
        # 文字列整形
        # `{` と `}` の位置を取得
        start = ret.find('{')  # '{' の位置
        end = ret.find('}')    # '}' の位置

        # `{}` の中身を抽出
        if start != -1 and end != -1:
            content = ret[start + 1:end]  # '{' の次から '}' の直前までを抽出
        
        return (True if(int(content) == 1) else False)

    def setOutputONBase(self, pin_no):
        no = pin_no
        status = 1
        ret = self.dashboard.DOExecute(no, status)
        self.checkApiErrorBase(ret)
        return

    def setOutputOFFBase(self, pin_no):
        no = pin_no
        status = 0
        ret = self.dashboard.DOExecute(no, status)
        self.checkApiErrorBase(ret)
        return


# Port Feedback
MyType = np.dtype([(
    'len',
    np.int64,
), (
    'digital_input_bits',
    np.uint64,
), (
    'digital_output_bits',
    np.uint64,
), (
    'robot_mode',
    np.uint64,
), (
    'time_stamp',
    np.uint64,
), (
    'time_stamp_reserve_bit',
    np.uint64,
), (
    'test_value',
    np.uint64,
), (
    'test_value_keep_bit',
    np.float64,
), (
    'speed_scaling',
    np.float64,
), (
    'linear_momentum_norm',
    np.float64,
), (
    'v_main',
    np.float64,
), (
    'v_robot',
    np.float64,
), (
    'i_robot',
    np.float64,
), (
    'i_robot_keep_bit1',
    np.float64,
), (
    'i_robot_keep_bit2',
    np.float64,
), ('tool_accelerometer_values', np.float64, (3, )),
    ('elbow_position', np.float64, (3, )),
    ('elbow_velocity', np.float64, (3, )),
    ('q_target', np.float64, (6, )),
    ('qd_target', np.float64, (6, )),
    ('qdd_target', np.float64, (6, )),
    ('i_target', np.float64, (6, )),
    ('m_target', np.float64, (6, )),
    ('q_actual', np.float64, (6, )),
    ('qd_actual', np.float64, (6, )),
    ('i_actual', np.float64, (6, )),
    ('actual_TCP_force', np.float64, (6, )),
    ('tool_vector_actual', np.float64, (6, )),
    ('TCP_speed_actual', np.float64, (6, )),
    ('TCP_force', np.float64, (6, )),
    ('Tool_vector_target', np.float64, (6, )),
    ('TCP_speed_target', np.float64, (6, )),
    ('motor_temperatures', np.float64, (6, )),
    ('joint_modes', np.float64, (6, )),
    ('v_actual', np.float64, (6, )),
    ('dummy', np.float64, (9, 6))])
# ('hand_type', np.char, (4, )),
# ('user', np.char,),
# ('tool', np.char,),
# ('run_queued_cmd', np.char,),
# ('pause_cmd_flag', np.char,),
# ('velocity_ratio', np.char,),
# ('acceleration_ratio', np.char,),
# ('jerk_ratio', np.char,),
# ('xyz_velocity_ratio', np.char,),
# ('r_velocity_ratio', np.char,),
# ('xyz_acceleration_ratio', np.char,),
# ('r_acceleration_ratio', np.char,),
# ('xyz_jerk_ratio', np.char,),
# ('r_jerk_ratio', np.char,),
# ('brake_status', np.char,),
# ('enable_status', np.char,),
# ('drag_status', np.char,),
# ('running_status', np.char,),
# ('error_status', np.char,),
# ('jog_status', np.char,),
# ('robot_type', np.char,),
# ('drag_button_signal', np.char,),
# ('enable_button_signal', np.char,),
# ('record_button_signal', np.char,),
# ('reappear_button_signal', np.char,),
# ('jaw_button_signal', np.char,),
# ('six_force_online', np.char,),
# ('reserve2', np.char, (82, )),
# ('m_actual', np.float64, (6, )),
# ('load', np.float64,),
# ('center_x', np.float64,),
# ('center_y', np.float64,),
# ('center_z', np.float64,),
# ('user[6]', np.float64, (6, )),
# ('tool[6]', np.float64, (6, )),
# ('trace_index', np.float64,),
# ('six_force_value', np.float64, (6, )),
# ('target_quaternion', np.float64, (4, )),
# ('actual_quaternion', np.float64, (4, )),
# ('reserve3', np.char, (24, ))])


class DobotApi:
    def __init__(self, ip, port, *args):
        self.ip = ip
        self.port = port
        self.socket_dobot = 0
        self.text_log: Text = None
        self._error = False  # 電源遮断用追加
        if args:
            self.text_log = args[0]

        if self.port == 29999 or self.port == 30003 or self.port == 30004:
            try:
                self.socket_dobot = socket.socket()
                self.socket_dobot.connect((self.ip, self.port))
                l_onoff = 1
                l_linger = 0
                self.socket_dobot.setsockopt(
                    socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', l_onoff, l_linger))
            except socket.error:
                print(socket.error)
                raise Exception(
                    f"Unable to set socket connection use port {self.port} !", socket.error)
        else:
            raise Exception(
                f"Connect to dashboard server need use port {self.port} !")

    def log(self, text):
        if self.text_log:
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ")
            self.text_log.insert(END, date + text + "\n")
        else:
            print(text)

    def send_data(self, string):
        # self.log(f"Send to 192.168.250.31:{self.port}: {string}")
        self.socket_dobot.send(str.encode(string, 'utf-8'))

    def wait_reply(self):  # working
        """
        Read the return value
        """
        data = self.socket_dobot.recv(1024)
        # print(data)
        data_str = str(data, encoding="utf-8")
        # self.log(f'Receive from 192.168.250.31:{self.port}: {data_str}')
        return data_str
    
    """
    def wait_reply(self):  # not working

        Read the return value

        if self.port == 29999:  # dashboardのみタイムアウト設ける
            ########################### 設定 #############################
            buffer_size = 1024
            timeout_in_seconds = 0.1
            self.socket_dobot.setblocking(False)  # Non-blockingモードに設定
            cmd_val = ""
            ########################### データ送信 #############################
            self.socket_dobot.send(cmd_val.encode())
            # サーバーからのレスポンス格納し、タイムアウトを設定
            ready = select.select([self.socket_dobot],
                                  [], [], timeout_in_seconds)
            # サーバーからのレスポンスがあれば
            if ready[0]:
                data = self.socket_dobot.recv(buffer_size)
                data_str = str(data, encoding="utf-8")
                self._error = False
                # self.log(f'Receive from 192.168.250.31:{self.port}: {data_str}')
                return data_str
            else:
                self._error = True
                print(f"not reply error is {self._error}")
                return

        else:  # move feedはタイムアウト設けない
            data = self.socket_dobot.recv(1024)
            # print(data)
            data_str = str(data, encoding="utf-8")
            # self.log(f'Receive from 192.168.250.31:{self.port}: {data_str}')
            return data_str
    """

    def close(self):
        """
        Close the port
        """
        if (self.socket_dobot != 0):
            self.socket_dobot.close()

    def __del__(self):
        self.close()


class DobotApiDashboard(DobotApi):
    """
    Define class dobot_api_dashboard to establish a connection to Dobot
    """

    def EnableRobot(self):
        """
        Enable the robot
        """
        string = "EnableRobot()"
        self.send_data(string)
        return self.wait_reply()

    def DisableRobot(self):
        """
        Disabled the robot
        """
        string = "DisableRobot()"
        self.send_data(string)
        return self.wait_reply()

    def ClearError(self):
        """
        Clear controller alarm information
        """
        string = "ClearError()"
        self.send_data(string)
        return self.wait_reply()

    def ResetRobot(self):
        """
        Robot stop
        """
        string = "ResetRobot()"
        self.send_data(string)
        return self.wait_reply()

    def SpeedFactor(self, speed):
        """
        Setting the Global rate   
        speed:Rate value(Value range:1~100)
        """
        string = "SpeedFactor({:d})".format(speed)
        self.send_data(string)
        return self.wait_reply()

    def User(self, index):
        """
        Select the calibrated user coordinate system
        index : Calibrated index of user coordinates
        """
        string = "User({:d})".format(index)
        self.send_data(string)
        return self.wait_reply()

    def Tool(self, index):
        """
        Select the calibrated tool coordinate system
        index : Calibrated index of tool coordinates
        """
        string = "Tool({:d})".format(index)
        self.send_data(string)
        return self.wait_reply()

    def RobotMode(self):
        """
        View the robot status
        """
        string = "RobotMode()"
        self.send_data(string)
        return self.wait_reply()

    def PayLoad(self, weight, inertia):
        """
        Setting robot load
        weight : The load weight
        inertia: The load moment of inertia
        """
        string = "PayLoad({:f},{:f})".format(weight, inertia)
        self.send_data(string)
        return self.wait_reply()

    def DI(self, index):
        """
        Set digital signal output (Queue instruction)
        index : Digital output index (Value range:1~24)
        status : Status of digital signal output port(0:Low level，1:High level
        """
        string = "DI({:d})".format(index)
        self.send_data(string)
        return self.wait_reply()


    def DOExecute(self, index, status):
        """
        Set digital signal output (Queue instruction)
        index : Digital output index (Value range:1~24)
        status : Status of digital signal output port(0:Low level，1:High level
        """
        string = "DOExecute({:d},{:d})".format(index, status)
        self.send_data(string)
        return self.wait_reply()

    def AccJ(self, speed):
        """
        Set joint acceleration ratio (Only for MovJ, MovJIO, MovJR, JointMovJ commands)
        speed : Joint acceleration ratio (Value range:1~100)
        """
        string = "AccJ({:d})".format(speed)
        self.send_data(string)
        return self.wait_reply()

    def AccL(self, speed):
        """
        Set the coordinate system acceleration ratio (Only for MovL, MovLIO, MovLR, Jump, Arc, Circle commands)
        speed : Cartesian acceleration ratio (Value range:1~100)
        """
        string = "AccL({:d})".format(speed)
        self.send_data(string)
        return self.wait_reply()

    def SpeedJ(self, speed):
        """
        Set joint speed ratio (Only for MovJ, MovJIO, MovJR, JointMovJ commands)
        speed : Joint velocity ratio (Value range:1~100)
        """
        string = "SpeedJ({:d})".format(speed)
        self.send_data(string)
        return self.wait_reply()

    def SpeedL(self, speed):
        """
        Set the cartesian acceleration ratio (Only for MovL, MovLIO, MovLR, Jump, Arc, Circle commands)
        speed : Cartesian acceleration ratio (Value range:1~100)
        """
        string = "SpeedL({:d})".format(speed)
        self.send_data(string)
        return self.wait_reply()

    def Arch(self, index):
        """
        Set the Jump gate parameter index (This index contains: start point lift height, maximum lift height, end point drop height)
        index : Parameter index (Value range:0~9)
        """
        string = "Arch({:d})".format(index)
        self.send_data(string)
        return self.wait_reply()

    def CP(self, ratio):
        """
        Set smooth transition ratio
        ratio : Smooth transition ratio (Value range:1~100)
        """
        string = "CP({:d})".format(ratio)
        self.send_data(string)
        return self.wait_reply()

    def LimZ(self, value):
        """
        Set the maximum lifting height of door type parameters
        value : Maximum lifting height (Highly restricted:Do not exceed the limit position of the z-axis of the manipulator)
        """
        string = "LimZ({:d})".format(value)
        self.send_data(string)
        return self.wait_reply()

    def RunScript(self, project_name):
        """
        Run the script file
        project_name ：Script file name
        """
        string = "RunScript({:s})".format(project_name)
        self.send_data(string)
        return self.wait_reply()

    def StopScript(self):
        """
        Stop scripts
        """
        string = "StopScript()"
        self.send_data(string)
        return self.wait_reply()

    def PauseScript(self):
        """
        Pause the script
        """
        string = "PauseScript()"
        self.send_data(string)
        return self.wait_reply()

    def ContinueScript(self):
        """
        Continue running the script
        """
        string = "ContinueScript()"
        self.send_data(string)
        return self.wait_reply()

    def GetHoldRegs(self, id, addr, count, type):
        """
        Read hold register
        id :Secondary device NUMBER (A maximum of five devices can be supported. The value ranges from 0 to 4
            Set to 0 when accessing the internal slave of the controller)
        addr :Hold the starting address of the register (Value range:3095~4095)
        count :Reads the specified number of types of data (Value range:1~16)
        type :The data type
            If null, the 16-bit unsigned integer (2 bytes, occupying 1 register) is read by default
            "U16" : reads 16-bit unsigned integers (2 bytes, occupying 1 register)
            "U32" : reads 32-bit unsigned integers (4 bytes, occupying 2 registers)
            "F32" : reads 32-bit single-precision floating-point number (4 bytes, occupying 2 registers)
            "F64" : reads 64-bit double precision floating point number (8 bytes, occupying 4 registers)
        """
        string = "GetHoldRegs({:d},{:d},{:d},{:s})".format(
            id, addr, count, type)
        self.send_data(string)
        return self.wait_reply()

    def SetHoldRegs(self, id, addr, count, table, type):
        """
        Write hold register
        id :Secondary device NUMBER (A maximum of five devices can be supported. The value ranges from 0 to 4
            Set to 0 when accessing the internal slave of the controller)
        addr :Hold the starting address of the register (Value range:3095~4095)
        count :Writes the specified number of types of data (Value range:1~16)
        type :The data type
            If null, the 16-bit unsigned integer (2 bytes, occupying 1 register) is read by default
            "U16" : reads 16-bit unsigned integers (2 bytes, occupying 1 register)
            "U32" : reads 32-bit unsigned integers (4 bytes, occupying 2 registers)
            "F32" : reads 32-bit single-precision floating-point number (4 bytes, occupying 2 registers)
            "F64" : reads 64-bit double precision floating point number (8 bytes, occupying 4 registers)
        """
        string = "SetHoldRegs({:d},{:d},{:d},{:d},{:s})".format(
            id, addr, count, table, type)
        self.send_data(string)
        return self.wait_reply()

    def GetErrorID(self):
        """
        Get robot error code
        """
        string = "GetErrorID()"
        self.send_data(string)
        return self.wait_reply()

    def GetPose(self):
        """

        """
        string = "GetPose()"
        self.send_data(string)
        return self.wait_reply()

    def GetAngle(self):
        """

        """
        string = "GetAngle()"
        self.send_data(string)
        return self.wait_reply()

    def GetPoseTool(self, user, tool):
        """
        user: index of User coordinate system
        tool: index of Tool coordinate system
        """
        string = "GetPose({:d},{:d})".format(
            user, tool)
        self.send_data(string)
        return self.wait_reply()

    def ResetRobot(self):
        """

        """
        string = "ResetRobot()"
        self.send_data(string)
        return self.wait_reply()

    def ClearError(self):
        """

        """
        string = "ClearError()"
        self.send_data(string)
        return self.wait_reply()


class DobotApiMove(DobotApi):
    """
    Define class dobot_api_move to establish a connection to Dobot
    """

    def MovJ(self, x, y, z, r, *dynParams):
        # (X,Y,Z,Rx,Ry,Rz,User=index,Tool=index,SpeedL=R,AccL=R)
        """
        Coordinate system motion interface (linear motion mode)
        x: A number in the Cartesian coordinate system x
        y: A number in the Cartesian coordinate system y
        z: A number in the Cartesian coordinate system z
        rx: Position of Rx axis in Cartesian coordinate system
        ry: Position of Ry axis in Cartesian coordinate system
        rz: Position of Rz axis in Cartesian coordinate system
        """
        # string = "MovL({:f},{:f},{:f},{:f})".format(
        #     x, y, z, r)
        string = "MovJ({:f},{:f},{:f},{:f},{:f},{:f}".format(
            x, y, z, r, 0, 0)

        for params in dynParams:
            #print(type(params), params)
            string = string + ", SpeedL={:d}, AccL={:d}".format(
                params[0], params[1])
        string = string + ")"

        self.send_data(string)
        return self.wait_reply()

    def MovL(self, x, y, z, r, *dynParams):
        # (X,Y,Z,Rx,Ry,Rz,User=index,Tool=index,SpeedL=R,AccL=R)
        """
        Coordinate system motion interface (linear motion mode)
        x: A number in the Cartesian coordinate system x
        y: A number in the Cartesian coordinate system y
        z: A number in the Cartesian coordinate system z
        rx: Position of Rx axis in Cartesian coordinate system
        ry: Position of Ry axis in Cartesian coordinate system
        rz: Position of Rz axis in Cartesian coordinate system
        """
        # string = "MovL({:f},{:f},{:f},{:f})".format(
        #     x, y, z, r)
        string = "MovL({:f},{:f},{:f},{:f},{:f},{:f}".format(
            x, y, z, r, 0, 0)

        for params in dynParams:
            #print(type(params), params)
            string = string + ", SpeedL={:d}, AccL={:d}".format(
                params[0], params[1])
        string = string + ")"

        self.send_data(string)
        return self.wait_reply()

    def JointMovJ(self, j1, j2, j3, j4):
        """
        Joint motion interface (linear motion mode)
        j1~j6:Point position values on each joint
        """
        string = "JointMovJ({:f},{:f},{:f},{:f})".format(
            j1, j2, j3, j4)
        self.send_data(string)
        return self.wait_reply()

    def Jump(self):
        print("待定")

    def RelMovJ(self, offset1, offset2, offset3, offset4, offset5, offset6):
        """
        Offset motion interface (point-to-point motion mode)
        j1~j6:Point position values on each joint
        """
        string = "RelMovJ({:f},{:f},{:f},{:f},{:f},{:f})".format(
            offset1, offset2, offset3, offset4, offset5, offset6)
        self.send_data(string)
        return self.wait_reply()

    def RelMovL(self, offsetX, offsetY, offsetZ):
        """
        Offset motion interface (point-to-point motion mode)
        x: Offset in the Cartesian coordinate system x
        y: offset in the Cartesian coordinate system y
        z: Offset in the Cartesian coordinate system Z
        """
        string = "RelMovL({:f},{:f},{:f})".format(offsetX, offsetY, offsetZ)
        self.send_data(string)
        return self.wait_reply()

    def MovLIO(self, x, y, z, a, b, c, *dynParams):
        """
        Set the digital output port state in parallel while moving in a straight line
        x: A number in the Cartesian coordinate system x
        y: A number in the Cartesian coordinate system y
        z: A number in the Cartesian coordinate system z
        a: A number in the Cartesian coordinate system a
        b: A number in the Cartesian coordinate system b
        c: a number in the Cartesian coordinate system c
        *dynParams :Parameter Settings（Mode、Distance、Index、Status）
                    Mode :Set Distance mode (0: Distance percentage; 1: distance from starting point or target point)
                    Distance :Runs the specified distance（If Mode is 0, the value ranges from 0 to 100；When Mode is 1, if the value is positive,
                             it indicates the distance from the starting point. If the value of Distance is negative, it represents the Distance from the target point）
                    Index ：Digital output index （Value range：1~24）
                    Status ：Digital output state（Value range：0/1）
        """
        # example： MovLIO(0,50,0,0,0,0,(0,50,1,0),(1,1,2,1))
        string = "MovLIO({:f},{:f},{:f},{:f},{:f},{:f}".format(
            x, y, z, a, b, c)
        print(type(dynParams), dynParams)
        for params in dynParams:
            print(type(params), params)
            string = string + ",{{{:d},{:d},{:d},{:d}}}".format(
                params[0], params[1], params[2], params[3])
        string = string + ")"
        self.send_data(string)
        return self.wait_reply()

    def MovJIO(self, x, y, z, a, b, c, *dynParams):
        """
        Set the digital output port state in parallel during point-to-point motion
        x: A number in the Cartesian coordinate system x
        y: A number in the Cartesian coordinate system y
        z: A number in the Cartesian coordinate system z
        a: A number in the Cartesian coordinate system a
        b: A number in the Cartesian coordinate system b
        c: a number in the Cartesian coordinate system c
        *dynParams :Parameter Settings（Mode、Distance、Index、Status）
                    Mode :Set Distance mode (0: Distance percentage; 1: distance from starting point or target point)
                    Distance :Runs the specified distance（If Mode is 0, the value ranges from 0 to 100；When Mode is 1, if the value is positive,
                             it indicates the distance from the starting point. If the value of Distance is negative, it represents the Distance from the target point）
                    Index ：Digital output index （Value range：1~24）
                    Status ：Digital output state（Value range：0/1）
        """
        # example： MovJIO(0,50,0,0,0,0,(0,50,1,0),(1,1,2,1))
        string = "MovJIO({:f},{:f},{:f},{:f},{:f},{:f}".format(
            x, y, z, a, b, c)
        self.log("Send to 192.168.1.31:29999:" + string)
        print(type(dynParams), dynParams)
        for params in dynParams:
            print(type(params), params)
            string = string + ",{{{:d},{:d},{:d},{:d}}}".format(
                params[0], params[1], params[2], params[3])
        string = string + ")"
        self.send_data(string)
        return self.wait_reply()

    def Arc(self, x1, y1, z1, a1, b1, c1, x2, y2, z2, a2, b2, c2):
        """
        Circular motion instruction
        x1, y1, z1, a1, b1, c1 :Is the point value of intermediate point coordinates
        x2, y2, z2, a2, b2, c2 :Is the value of the end point coordinates
        Note: This instruction should be used together with other movement instructions
        """
        string = "Arc({:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f})".format(
            x1, y1, z1, a1, b1, c1, x2, y2, z2, a2, b2, c2)
        self.send_data(string)
        return self.wait_reply()

    def Circle(self, count, x1, y1, z1, a1, b1, c1, x2, y2, z2, a2, b2, c2):
        """
        Full circle motion command
        count：Run laps
        x1, y1, z1, a1, b1, c1 :Is the point value of intermediate point coordinates
        x2, y2, z2, a2, b2, c2 :Is the value of the end point coordinates
        Note: This instruction should be used together with other movement instructions
        """
        string = "Circle({:d},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f})".format(
            count, x1, y1, z1, a1, b1, c1, x2, y2, z2, a2, b2, c2)
        self.send_data(string)
        return self.wait_reply()

    def ServoJ(self, j1, j2, j3, j4, j5, j6):
        """
        Dynamic follow command based on joint space
        j1~j6:Point position values on each joint
        """
        string = "ServoJ({:f},{:f},{:f},{:f},{:f},{:f})".format(
            j1, j2, j3, j4, j5, j6)
        self.send_data(string)
        return self.wait_reply()

    def ServoP(self, x, y, z, a, b, c):
        """
        Dynamic following command based on Cartesian space
        x, y, z, a, b, c :Cartesian coordinate point value
        """
        string = "ServoP({:f},{:f},{:f},{:f},{:f},{:f})".format(
            x, y, z, a, b, c)
        self.send_data(string)
        return self.wait_reply()

    def MoveJog(self, axis_id, *dynParams):
        """
        Joint motion
        axis_id: Joint motion axis, optional string value:
            J1+ J2+ J3+ J4+ J5+ J6+
            J1- J2- J3- J4- J5- J6- 
            X+ Y+ Z+ Rx+ Ry+ Rz+ 
            X- Y- Z- Rx- Ry- Rz-
        *dynParams: Parameter Settings（coord_type, user_index, tool_index）
                    coord_type: 1: User coordinate 2: tool coordinate (default value is 1)
                    user_index: user index is 0 ~ 9 (default value is 0)
                    tool_index: tool index is 0 ~ 9 (default value is 0)
        """
        string = f"MoveJog({axis_id}"
        for params in dynParams:
            # print(type(params), params)
            string = string + ", CoordType={:d}, User={:d}, Tool={:d}".format(
                params[0], params[1], params[2])
        string = string + ")"
        # print(string)
        self.send_data(string)
        return self.wait_reply()

    def StartTrace(self, trace_name):
        """
        Trajectory fitting (track file Cartesian points)
        trace_name: track file name (including suffix)
        (The track path is stored in /dobot/userdata/project/process/trajectory/)

        It needs to be used together with `GetTraceStartPose(recv_string.json)` interface
        """
        string = f"StartTrace({trace_name})"
        self.send_data(string)
        return self.wait_reply()

    def StartPath(self, trace_name, const, cart):
        """
        Track reproduction. (track file joint points)
        trace_name: track file name (including suffix)
        (The track path is stored in /dobot/userdata/project/process/trajectory/)
        const: When const = 1, it repeats at a constant speed, and the pause and dead zone in the track will be removed;
               When const = 0, reproduce according to the original speed;
        cart: When cart = 1, reproduce according to Cartesian path;
              When cart = 0, reproduce according to the joint path;

        It needs to be used together with `GetTraceStartPose(recv_string.json)` interface
        """
        string = f"StartPath({trace_name}, {const}, {cart})"
        self.send_data(string)
        return self.wait_reply()

    def StartFCTrace(self, trace_name):
        """
        Trajectory fitting with force control. (track file Cartesian points)
        trace_name: track file name (including suffix)
        (The track path is stored in /dobot/userdata/project/process/trajectory/)

        It needs to be used together with `GetTraceStartPose(recv_string.json)` interface
        """
        string = f"StartFCTrace({trace_name})"
        self.send_data(string)
        return self.wait_reply()

    def Sync(self):
        """
        The blocking program executes the queue instruction and returns after all the queue instructions are executed
        """
        string = "Sync()"
        self.send_data(string)
        return self.wait_reply()

    def RelMovJTool(self, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, tool, *dynParams):
        """
        The relative motion command is carried out along the tool coordinate system, and the end motion mode is joint motion
        offset_x: X-axis direction offset
        offset_y: Y-axis direction offset
        offset_z: Z-axis direction offset
        offset_rx: Rx axis position
        offset_ry: Ry axis position
        offset_rz: Rz axis position
        tool: Select the calibrated tool coordinate system, value range: 0 ~ 9
        *dynParams: parameter Settings（speed_j, acc_j, user）
                    speed_j: Set joint speed scale, value range: 1 ~ 100
                    acc_j: Set acceleration scale value, value range: 1 ~ 100
                    user: Set user coordinate system index
        """
        string = "RelMovJTool({:f},{:f},{:f},{:f},{:f},{:f}, {:d}".format(
            offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, tool)
        for params in dynParams:
            print(type(params), params)
            string = string + ", SpeedJ={:d}, AccJ={:d}, User={:d}".format(
                params[0], params[1], params[2])
        string = string + ")"
        self.send_data(string)
        return self.wait_reply()

    def RelMovLTool(self, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, tool, *dynParams):
        """
        Carry out relative motion command along the tool coordinate system, and the end motion mode is linear motion
        offset_x: X-axis direction offset
        offset_y: Y-axis direction offset
        offset_z: Z-axis direction offset
        offset_rx: Rx axis position
        offset_ry: Ry axis position
        offset_rz: Rz axis position
        tool: Select the calibrated tool coordinate system, value range: 0 ~ 9
        *dynParams: parameter Settings（speed_l, acc_l, user）
                    speed_l: Set Cartesian speed scale, value range: 1 ~ 100
                    acc_l: Set acceleration scale value, value range: 1 ~ 100
                    user: Set user coordinate system index
        """
        string = "RelMovLTool({:f},{:f},{:f},{:f},{:f},{:f}, {:d}".format(
            offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, tool)
        for params in dynParams:
            print(type(params), params)
            string = string + ", SpeedJ={:d}, AccJ={:d}, User={:d}".format(
                params[0], params[1], params[2])
        string = string + ")"
        print(string)
        self.send_data(string)
        return self.wait_reply()

    def RelMovJUser(self, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, user, *dynParams):
        """
        The relative motion command is carried out along the user coordinate system, and the end motion mode is joint motion
        offset_x: X-axis direction offset
        offset_y: Y-axis direction offset
        offset_z: Z-axis direction offset
        offset_rx: Rx axis position
        offset_ry: Ry axis position
        offset_rz: Rz axis position
        user: Select the calibrated user coordinate system, value range: 0 ~ 9
        *dynParams: parameter Settings（speed_j, acc_j, tool）
                    speed_j: Set joint speed scale, value range: 1 ~ 100
                    acc_j: Set acceleration scale value, value range: 1 ~ 100
                    tool: Set tool coordinate system index
        """
        string = "RelMovJUser({:f},{:f},{:f},{:f},{:f},{:f}, {:d}".format(
            offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, user)
        for params in dynParams:
            print(type(params), params)
            string = string + ", SpeedJ={:d}, AccJ={:d}, Tool={:d}".format(
                params[0], params[1], params[2])
        string = string + ")"
        self.send_data(string)
        return self.wait_reply()

    def RelMovLUser(self, offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, user, *dynParams):
        """
        The relative motion command is carried out along the user coordinate system, and the end motion mode is linear motion
        offset_x: X-axis direction offset
        offset_y: Y-axis direction offset
        offset_z: Z-axis direction offset
        offset_rx: Rx axis position
        offset_ry: Ry axis position
        offset_rz: Rz axis position
        user: Select the calibrated user coordinate system, value range: 0 ~ 9
        *dynParams: parameter Settings（speed_l, acc_l, tool）
                    speed_l: Set Cartesian speed scale, value range: 1 ~ 100
                    acc_l: Set acceleration scale value, value range: 1 ~ 100
                    tool: Set tool coordinate system index
        """
        string = "RelMovLUser({:f},{:f},{:f},{:f},{:f},{:f}, {:d}".format(
            offset_x, offset_y, offset_z, offset_rx, offset_ry, offset_rz, user)
        for params in dynParams:
            print(type(params), params)
            string = string + ", SpeedL={:d}, AccL={:d}, Tool={:d}".format(
                params[0], params[1], params[2])
        string = string + ")"
        self.send_data(string)
        return self.wait_reply()

    def RelJointMovJ(self, offset1, offset2, offset3, offset4, offset5, offset6, *dynParams):
        """
        The relative motion command is carried out along the joint coordinate system of each axis, and the end motion mode is joint motion
        Offset motion interface (point-to-point motion mode)
        j1~j6:Point position values on each joint
        *dynParams: parameter Settings（speed_j, acc_j, user）
                    speed_j: Set Cartesian speed scale, value range: 1 ~ 100
                    acc_j: Set acceleration scale value, value range: 1 ~ 100
        """
        string = "RelJointMovJ({:f},{:f},{:f},{:f},{:f},{:f}".format(
            offset1, offset2, offset3, offset4, offset5, offset6)
        for params in dynParams:
            print(type(params), params)
            string = string + ", SpeedJ={:d}, AccJ={:d}".format(
                params[0], params[1])
        string = string + ")"
        self.send_data(string)
        return self.wait_reply()

    def InverseSolution(self, x, y, z, rx, ry, rz, user, tool):
        """
        Coordinate system motion interface (linear motion mode)
        x: A number in the Cartesian coordinate system x
        y: A number in the Cartesian coordinate system y
        z: A number in the Cartesian coordinate system z
        rx: Position of Rx axis in Cartesian coordinate system
        ry: Position of Ry axis in Cartesian coordinate system
        rz: Position of Rz axis in Cartesian coordinate system
        user: index of User coordinate system
        tool: index of Tool coordinate system
        """
        string = "InverseSolution({:f},{:f},{:f},{:f},{:f},{:f},{:d},{:d})".format(
            x, y, z, rx, ry, rz, user, tool)
        self.send_data(string)
        return self.wait_reply()

    def PositiveSolution(self, j1, j2, j3, j4, j5, j6, user, tool):
        """
        Joint motion interface (linear motion mode)
        j1~j6:Point position values on each joint
        user: index of User coordinate system
        tool: index of Tool coordinate system
        """
        string = "PositiveSolution({:f},{:f},{:f},{:f},{:f},{:f},{:d},{:d})".format(
            j1, j2, j3, j4, j5, j6, user, tool)
        self.send_data(string)
        return self.wait_reply()


if __name__ == '__main__':
    node = RobotApi()
