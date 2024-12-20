# -*- coding : UTF-8 -*-
###########################
# Supports 6-axis control for dobot CR A series
###########################
# official api
# from mg400
from socket import *
import select
from time import sleep, perf_counter
from multiprocessing import Process, Value, Array
from typing import Tuple, List, Union, Optional
import struct

from threading import Timer
from tkinter import Text, END
import datetime

import configparser

#from dobotapi CR A
import socket
#import numpy as np
import os
import re
import json
import threading
from time import sleep

#HITBOT用
from ctypes import *

#test用
#import pdb

#############################################################
# グローバル変数定義
#############################################################
X = 0
Y = 1
Z = 2
#R = 3  ###0701 4轴也统一使用6个坐标，ry,rx实际不使用
RX = 3
RY = 4
RZ = 5 
CHECK_MOVING_DIFF = 0.1

GRAVITY = 9800
#XYZ_MAX_JERK = 30000
#R_MAX_JERK = 30000
XYZ_MAX_ACC = 220  #？？ ####0701 hitbot movej方式可设加速度 30-220%，绝对值不明
R_MAX_ACC = XYZ_MAX_ACC   ####0701 Hitbot中R的加速度与线速度同值 
XYZ_MAX_VEL = 1500    ###1220    ##TCP速度， mm/s
R_MAX_VEL = XYZ_MAX_VEL   ####0701  Hitbot中R的加速度与线速度同值 

class RobotApi():
    #def __init__(self, dst_ip_address: str, dst_port: str, dev_port: str, baurate: int, arm_id : int = 101):
        ####0701 Hitbot用增加 arm_id  ，连接Z ARM时必须使用，config文件亦要加此项，默认值101。IP address，port可不用  --->arm_ID= ip的第4位，不需要输入，config也不需要改
    def __init__(self, dst_ip_address: str, dst_port: str, dev_port: str, baurate: int,robot_name:str):
        ####0701 Hitbot用增加 arm_id  ，连接Z ARM时必须使用。IP address，port可不用
        ### arm_id = ip的第4位，不需要输入，config也不需要改
        arm_id=int(dst_ip_address.split(".")[3])
        self.robot_name = robot_name
        ##############################################################
        # ロボット状態通知用変数定義(数値)
        ##############################################################
        self.current_pos: List[float] = [0.0] * 6          ####0701 4轴也统一使用6个坐标，ry,rx实际不使用
        self.pre_current_pos: List[float] = [0.0] * 6        ####0701 4轴也统一使用6个坐标，ry,rx实际不使用
        self.error_id: int = 0
        ##############################################################
        # ロボット状態通知用変数定義(フラグ)
        ##############################################################
        self.connection: bool = False
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
        #self._robot_mode: int = Value('i', 0)    ####0701 Hitbot中无实时反馈
        self.robot_mode = 0      # mode 值范围 1-11
        # 電源確認用フラグ
        self.opening = False
        # self変数
        self.dst_ip_address = dst_ip_address
        self.dst_port = dst_port
        self.arm_id = arm_id  ####0701 Hitbot用增加 arm_id
        ##############################################################
        # ロボット接続開始
        ##############################################################
        #self.openRobot(self.dst_ip_address, self.dst_port)
        self.openRobot(self.dst_ip_address, self.dst_port, self.arm_id)   ###0701

    def __del__(self):
        ##############################################################
        # ロボット接続解除
        ##############################################################
        self.closeRobot()
        print("Disconnected.")

    #############################################################
    # ロボット共通関数
    #############################################################
    ''' # openRobot old
    def openRobot_mg400(self, dst_ip_address: str, dst_port: str) -> None:
        """ ロボット通信を開始
        """
        self.dst_ip_address = dst_ip_address
        # ロボットサーバに接続
        print("Start to connect robot.")
        self.connectRobotBase()
        self.resetError()
        self.setTool(tool_no=0)
        self.setUser(user_no=0)
        self.mySleepBase(0.5)
        self.startMultiFeedbackBase()
        print("Finished to connect robot.")
        print("Connected to: " + self.dst_ip_address)
        
    def openRobot_cra(self, dst_ip_address: str, dst_port: str) -> None:
        """ ロボット通信を開始
        """
        self.dst_ip_address = dst_ip_address
        # ロボットサーバに接続
        print("Start to connect robot.")
        self.connectRobotBase()    ##0405 此函数中 DobotApiFeedBack class的 init 中建立了反馈用多线程
        #self.setServoOn()  ###0422 for test 无此命令时要在main中加入ServoOn，或者预先ServoOn否则无法运行。无此命令时下面的setTool无法正确执行，有报错但程序不停止
        self.resetError()
        #self.setTool(tool_no=0)   ###0422 ServoOff时无法运行。出错但不停止程序。改到readyRobot中执行
        #self.setUser(user_no=0)   ###0422 ServoOff时无法运行。出错但不停止程序。改到readyRobot中执行
        self.tool_no=0
        self.user_no=0
        self.mySleepBase(0.5)
        #self.startMultiFeedbackBase()   ##0405
        print("Finished to connect robot.")
        print("Connected to: " + self.dst_ip_address)
    '''

    #def openRobot(self, dst_ip_address: str, dst_port: str) -> None:  
    def openRobot(self, dst_ip_address: str, dst_port: str, arm_id: int) -> None:  
        """ ロボット通信を開始
        """
        #self.dst_ip_address = dst_ip_address
        # ロボットサーバに接続
        print("开始连接。Start to connect robot.")
        #pdb.set_trace()   ##b 1
        self.connectRobotBase()   
        if self.connection ==True:
            print("连接成功。Finished to connect robot.")
            print("Connected to Hitbot Z-Arm2442: Card_Num: " , self.arm_id)
        else:
            print("Fialed to connect robot.")
            
        self.resetError()
        
        # ret = self.dashboard.set_cooperation_fun_state(True)  ####设定协作功能是否开启，True 开启，False 关闭。开启后机械臂遇到障碍物会停止运动，并上报此状态
        # if ret == True:            #####False：失败  True： 成功
        #     print("设定协作功能开启成功")
        # else:
        #     print("设定协作功能开启失败")
        ret = self.dashboard.set_cooperation_fun_state(False)  ####设定协作功能是否开启，True 开启，False 关闭。开启后机械臂遇到障碍物会停止运动，并上报此状态
        if ret == True:            #####False：失败  True： 成功
            print("设定协作功能关闭成功")
        else:
            print("设定协作功能关闭失败")
        #self.setTool(tool_no=0)   #####0701 #hitbot 无tool，user坐标
        #self.setUser(user_no=0)   ###0701 #hitbot 无tool，user坐标
        # self.tool_no=0 ###0701 #hitbot 无坐标切换功能
        # self.user_no=0 ###0701 #hitbot 无坐标切换功能
        self.mySleepBase(0.5)
        #self.startMultiFeedbackBase()   ###0701 hitbot 无实时反馈

    def closeRobot(self) -> None:
        """ ロボット通信を解除
        """
        # self.setServoOff()
        self.mySleepBase(0.5)
        #self.dst_ip_address.dll.set_tool_fun1()
        #self.feed.close()       ###0701 hitbot 无实时反馈
        #self.move.close()        ###0701 hitbot 无实时反馈 只用一个端口
        #self.dashboard.close()
        self.dashboard.close_server()  #Linux无此函数 ###0701关闭网络服务器(server.exe 程序）调用后，手臂和pc 的通讯将会断开

    def readyRobot(self):
        self.setServoOn()
        #self.setTool(tool_no=0)   ###0701 hitbot不能选坐标系。  0422增加 ServoOff时无法运行。出错但不停止程序。从OpenRobot中改到readyRobot中执行
        #self.setUser(user_no=0)   #####0701 hitbot不能选坐标系。0422增加 ServoOff时无法运行。出错但不停止程序。从OpenRobot中改到readyRobot中执行
        self.setInitialRobotParamBase()

    def saveTool_coord(self,x,y,z,rx,ry,rz,tool_no):  
        pass           ##FR设Tool坐标用函数，hitbot不作处理       

    def getRobotStatus(self) -> None:
        """ ロボット状態を取得
        """
        ##############################################################
        # 現在地の直交座標取得
        ##############################################################
        self.current_pos = self.getCurrentPos()   #### 此函数中执行 get_scara_param()
        ##############################################################
        # サーボ状態監視
        ##############################################################
        #self.servo = not self.dashboard.communicate_success  ###0701 true：不在线 false：在线 pos中已经执行了get_scara_param()   
        #if self.dashboard.initial_finish and not self.dashboard.communicate_success : ###0701 初始化成功且在线 文档错误。两个都是True为成功
        if self.dashboard.initial_finish and self.dashboard.communicate_success : ###0701 初始化成功且在线
            self.servo = True

        ##############################################################
        # エラー状態確認
        ##############################################################
        self.checkErrorBase()    
        ##############################################################
        # エラーステータス取得(エラー発生時のみ)
        ##############################################################
        if (self.error == True):
            self.error_id = self.getErrorBase()            ##com_err_id #第一个错误的类型重新编号，PLC处理用
        else:
            self.error_id = 0

        ##############################################################
        # Moving確認
        ##############################################################
        self.checkMovingBase()
        self.pre_current_pos = self.current_pos
        
        ##############################################################
        # origin確認
        ##############################################################
        self.origin = True

    def getRobotStatus_dobot(self) -> None:
        """ ロボット状態を取得
        """
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
        #self.robot_mode = self._robot_mode.value
        self.robot_mode = self.feed._robot_mode.value   ####0422 feed中接受反馈
        #print('robot_mode=',self.robot_mode)            ####0507  test
        ##############################################################
        # サーボ状態監視
        ##############################################################
        if (self.robot_mode == 4):   ##ROBOT_MODE_DISABLED 未使能（无抱闸松开）##0405  ？？2有任意关节的抱闸松开 3机械臂下电状态 不要处理？？
            self.servo = False
        elif (self.robot_mode == 5):
            self.servo = True

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

    def setCollisionLevel(self, level: int):
        """ 衝突検知設定
        tool_no : int
            ツール座標番号
        """
        self.setCollisionLevelBase(level)

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

    '''    ###hitbot不需要
    #def getPos2Joint(self, x: float, y: float, z: float, Rx: float, Ry: float, Rz: float) -> None:   ###0422 与main中一致，Rx ->rx
    def getPos2Joint(self, x: float, y: float, z: float, rx: float, ry: float, rz: float) -> None:   ###0422 与main中一致，Rx ->rx
        """ 直交座標をジョイント座標へ変換
        #InverseKin(self, X, Y, Z, Rx, Ry, Rz, user=-1, tool=-1, useJointNear=-1, JointNear=''):
        """
        #ret = self.dashboard.InverseKin(x, y, z, Rx, Ry, Rz, 0, 0, 0, 0)   ##0405 CRA系列使用TCP-IP V4，move class 废止，功能在Dashboard中实现
        ret = self.dashboard.InverseKin(x, y, z, rx, ry, rz, 0, 0, 0, 0)   ##0405 CRA系列使用TCP-IP V4，move class 废止，功能在Dashboard中实现
        self.checkApiErrorBase()   ##函数返回值 api_error =0 or 1, 未使用
        val = self.transformStr2Joint(ret)
        return val

    def getJoint2Pos(self, j1: float, j2: float, j3: float, j4: float, j5: float, j6: float) -> None:
        """ ジョイント座標を直交座標へ変換
        #def PositiveKin(self, J1, J2, J3, J4, J5, J6, user=-1, tool=-1):
        """
        ret = self.dashboard.PositiveKin(j1, j2, j3, j4, j5, j6, 0, 0)
        self.checkApiErrorBase()
        val = self.transformStr2Pos(ret)
        return val
    '''

    def waitArrive_dobot(self, target_pos: List[float], width: float) -> None:
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
        #diff_pos = [abs(x - y) for (x, y) in zip(target_pos, self.current_pos)]
        #########0422 Rx,Ry,Rz检出位置180与-180跳跃问题解决
        target_pos_linshi=target_pos
        current_pos_linshi=self.current_pos

        for ii in range(3,6):
            if current_pos_linshi[ii] ==-180:
                current_pos_linshi[ii] =180 
            if target_pos_linshi[ii] ==-180:
                target_pos_linshi[ii] =180
                
        diff_pos = [abs(x - y) for (x, y) in zip(target_pos_linshi, current_pos_linshi)]
        # print("diff_pos",diff_pos)
        # 差分が設定値以内なら
        if ((diff_pos[X] <= width)
            and (diff_pos[Y] <= width)
            and (diff_pos[Z] <= width)
            #and (diff_pos[R] <= width)):  ##0405
            and (diff_pos[RX] <= width)
            and (diff_pos[RY] <= width)
            and (diff_pos[RZ] <= width)):
            self.arrived = True
        else:
            self.arrived = False

    def waitArrive(self, target_pos: List[float], width: float) -> None:
        """ hitbot ロボットの到着まで待機
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
            #and (diff_pos[R] <= width)):  
            # and (diff_pos[RX] <= width)
            # and (diff_pos[RY] <= width)
            and (diff_pos[RZ] <= width)):
            self.arrived = True
        else:
            self.arrived = False

    def setRobotParam_dobot(self, vel: float, acc: float, dec: float) -> None:
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

    def setRobotParam(self, vel: float, acc: float, dec: float) -> None:
        """ hitbot ロボットのパラメータ変更 acc:% only,vel:mm/s
            Parameters
            ----------
            vel : float
                変更後速度[mm/s]
            acc : float
                変更後加速度[mm/s^2]
            dec : float
                変更後加速度[mm/s^2]
        """

        #acc_line_val = (acc / XYZ_MAX_ACC) * 9800 * 100
        acc_line_val = acc ### input must is %
        vel_line_val = (vel / XYZ_MAX_VEL) * 100
        #acc_joint_val = (acc / XYZ_MAX_ACC) * 9800 * 100
        acc_joint_val = acc  ### input must is %
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
    
    def moveAbsolutePtp(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, vel: int = 100, acc: int = 100, dec: int = 100) -> None:     ###0422 与main中一致，Rx ->rx
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
            目標rx座標[°]
        ry : float
            目標ry座標[°]
        rz : float
            目標rz座標[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """
        #self.error_id = self.getErrorBase()   ##0701 追加 ####0507 直线运动前检查状态，可减少很多rasipy错误但PLC无反馈问题
        self.moveAbsolutePtpBase(x, y, z, rx, ry, rz, vel, acc, dec)   ###0422 Rx->rx

    def moveAbsoluteLine(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, vel: int = 100, acc: int = 100, dec: int = 100) -> None:
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
            目標rx座標[°]
        ry : float
            目標ry座標[°]
        rz : float
            目標rz座標[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """
        #self.error_id = self.getErrorBase()   ##0405 为何调用此函数？？ 应不需要 ####0507 直线运动前检查状态，可减少很多rasipy错误但PLC无反馈问题
        self.moveAbsoluteLineBase(x, y, z, rx, ry, rz, vel, acc, dec)    ###0422 Rx->rx

    def moveRelative(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, vel: int = 100, acc: int = 100, dec: int = 100) -> None:
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
            目標rx座標[°]
        ry : float
            目標ry座標[°]
        rz : float
            目標rz座標[°]
        vel : int
            設定速度[%]
        acc : int
            設定加速度[%]
        dec : int
            設定減速度[%]
        """
        #self.error_id = self.getErrorBase()   ##0701 追加 ####0507 直线运动前检查状态，可减少很多rasipy错误但PLC无反馈问题
        self.moveRelativeBase(x, y, z, rx, ry, rz, vel, acc, dec)   ###0422 Rx->rx

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
        """ 手動移動：インチング 实际未使用此函数，而是main中直接调用moveRelative
        Parameters dobot,Fr
        ----------
        width : int
            インチング幅[mm]　最大=10.000mm
        axis_char_str : str
            軸(ex. "x")
        direction_char_str : str
            回転方向(ex. "+")
        """
        #self.error_id = self.getErrorBase()   ##0701 追加 ####0507 直线运动前检查状态，可减少很多rasipy错误但PLC无反馈问题
        self.moveInchingBase(width, axis_char_str, direction_char_str)

    def moveJog_old(self, axis_char_str: str, direction_char_str: str) -> None:
        """ 手動移動：ジョグ  dobot,fr
        Parameters
        ----------
        axis_char_str : str
            軸(ex. "x")
            軸(ex. "j1")   ####0422 新增J1-6的点动
        direction_char_str : str
            回転方向(ex. "+")
        """
        ####0507 test
        #with open('log_err_cra_api.txt', 'a') as fe:
        #   print("CAR_api--moveJog: axis, sign", axis_char_str, direction_char_str,file=fe)
        #fe.close()   ####0507 test
        
        #self.error_id = self.getErrorBase()   ##0701 追加 ####0507 直线运动前检查状态，可减少很多rasipy错误但PLC无反馈问题
        self.moveJogBase(axis_char_str, direction_char_str)
        self.waiting_end = True
        self.arrived = False

    def moveJog(self, axis_char_str: str, direction_char_str: str, vel:float=-1) -> None:
        """ 手動移動：ジョグ
        hitbot无Jog运动，类似的xyz-move需要指定距离，速度、实际是Inching运动
        Parameters   TP中有速度指定，但未使用。若今后使用则直接用其值单位mm/s。若不指定则默认-1,在jogBase中改为50%
        ----------
        axis_char_str : str
            軸(ex. "x")
            軸(ex. "j1")   ####0422 新增J1-6的点动
        direction_char_str : str
            回転方向(ex. "+")
        """
        ####0507 test
        #with open('log_err_cra_api.txt', 'a') as fe:
        #   print("CAR_api--moveJog: axis, sign", axis_char_str, direction_char_str,file=fe)
        #fe.close()   ####0507 test
        
        #self.error_id = self.getErrorBase()   ##0701 追加 ####0507 直线运动前检查状态，可减少很多rasipy错误但PLC无反馈问题
        self.moveJogBase(axis_char_str, direction_char_str,vel)
        self.waiting_end = True
        self.arrived = False
        
    def continueJog(self, axis, sign) -> None:
        pass

    def stopJog(self) -> None:
        self.stopJogBase()
        #sleep(0.5)      ######0516  0.1-0.4没效果

        return

    def printRobotStatus(self) -> None:
        """ 変数表示(デバッグ用)
        """
        print("##########################  Status  ##############################################")
        print('X  = {0:.3f}'.format(self.current_pos[X]))
        print('Y  = {0:.3f}'.format(self.current_pos[Y]))
        print('Z  = {0:.3f}'.format(self.current_pos[Z]))
        #print('R  = {0:.3f}'.format(self.current_pos[R]))  ##0405
        #print('Rx  = {0:.3f}'.format(self.current_pos[RX]))
        #print('Ry  = {0:.3f}'.format(self.current_pos[RY]))
        print('Rz  = {0:.3f}'.format(self.current_pos[RZ]))
        print("emerge -> " + str(self.emerge) + ", " + "error -> ", str(self.error) + ", " + "servo -> ", str(self.servo) + ", " + "moving -> "
              + str(self.moving) + ", " + "origin -> ", str(self.origin) + ", " + "arrived -> ", str(self.arrived) + ", " + "dragging -> ", str(self.dragging))
        print("error id = ", self.error_id)
        print("##################################################################################")

    #############################################################
    # ロボット固有関数
    #############################################################
    def setInitialRobotParamBase(self):
        default = 50
        self.setAccLineBase(default)     #### hitbot     直线acc不能设，moveJ方式30-220%
        self.setVelLineBase(default)
        self.setAccJointBase(default)   #### hitbot     直线acc不能设，moveJ方式30-220%
        self.setVelJointBase(default)

    def mySleepBase(self, sleep_time):
        now = perf_counter()
        while (perf_counter() - now < sleep_time):
            pass

    def connectRobotBase_11(self):  ##使用pdb版本
        try:
            #ip = self.dst_ip_address
            # NOTE:以下は固定値
            #dashboard_p = 40000  ###0701 Hitbot未明示使用端口，大概可以任意指定。但说明书中推测默认使用40000号端口
            #feed_p = 30004     ###0701 Hitbot无反馈
            pdb.set_trace()    ##b2
            self.dashboard = HitbotInterface(self.arm_id)  ####传入机械臂id 号，接口实例化.  Hitbot 只要Arm编号=IP地址第4节的值
            ret = self.dashboard.net_port_initial()      ####申请内存和初始化网络服务器
            if ret == 1:
                print("网络初始化成功")
            else:
                print("网络初始化失败")    #### 0 失败，一般是40000 端口号被占用   
                self.error = True
                self.error_id =2    ####サーボOFF　軸使用エラー 机械臂不在线　PLC用
                self.connection = False                
                return        
            sleep(3)   ####函数返回后，建议延迟3s
            pdb.set_trace()    ##b6
            
            ret = self.dashboard.is_connect()   ####查询机械臂是否在线  True：机械臂在线 False：机械臂不在线
            if ret == True:
                print("机械臂在线")
            else:
                print("机械臂不在线")
                self.error = True
                self.error_id =2    ####サーボOFF　軸使用エラー 机械臂不在线　PLC用
                return
            pdb.set_trace()    ##b7
            
            ret = self.dashboard.initial(1, 240)  ####0701 def initial(self, generation, z_trail)  
                #### generation：400mm 臂展系列传入1，320mm 臂展系列及其他臂展手臂传入5， float z_travel：上下关节有效行程（mm）
                #### 返回值  0：机械臂不在线,  1：初始化成功 2：generation 参数错误  3：机械臂当前位置不在限定范围，可以使用joint_home使关节强制回零
                #### 12：z_travel 传参错误   101：传入参数NOT A NUMBER   105：存在某一个关节失效   >= 10000，pid 自检异常
            if ret == 1:
                print("robot initial successful")
                self.connection = True                
            else:
                self.error_id =2    ####サーボOFF　軸使用エラー 初始化失敗　PLC用
                self.error = True
                print("robot initial failed", ret)
                self.showInitialErrorMessage(ret)
                return

            #self.feed = DobotApiFeedBack(ip, feed_p)        ###0701 Hitbot无反馈
            self.opening = True  # Dobot電源確認用
            # return dashboard, move, feed
        except Exception as e:
            print("Fail to connect")
            self.opening = False  # Dobot電源確認用
            raise e

    def connectRobotBase(self):
            #pdb.set_trace()    ##b2
            self.dashboard = HitbotInterface_new(self.arm_id)  ####传入机械臂id 号，接口实例化.  Hitbot 只要Arm编号=IP地址第4节的值
            ret = self.dashboard.net_port_initial()      ####申请内存和初始化网络服务器
            if ret == 1:
                print("网络初始化成功")
            else:
                print("网络初始化失败")    #### 0 失败，一般是40000 端口号被占用   
                self.error = True
                self.error_id =2    ####サーボOFF　軸使用エラー 机械臂不在线　PLC用
                self.connection = False                
                self.opening = False  # Dobot電源確認用
                return        
            sleep(3)   ####函数返回后，建议延迟3s
            #pdb.set_trace()    ##b6
            
            ret = self.dashboard.is_connect()   ####查询机械臂是否在线  True：机械臂在线 False：机械臂不在线
            if ret == True:
                print("机械臂在线")
            else:
                print("机械臂不在线")
                self.error = True
                self.error_id =2    ####サーボOFF　軸使用エラー 机械臂不在线　PLC用
                print("Fail to connect")
                self.opening = False  # Dobot電源確認用
                return
            #pdb.set_trace()    ##b7
            
            #ret = self.dashboard.initial(1, 240)  ####0701 def initial(self, generation, z_trail)  
                #### generation：400mm 臂展系列传入1，320mm 臂展系列及其他臂展手臂传入5， float z_travel：上下关节有效行程（mm）
                #### 返回值  0：机械臂不在线,  1：初始化成功 2：generation 参数错误  3：机械臂当前位置不在限定范围，可以使用joint_home使关节强制回零
                #### 12：z_travel 传参错误   101：传入参数NOT A NUMBER   105：存在某一个关节失效   >= 10000，pid 自检异常
            if int(self.robot_name[-2:])>40:
                generation=1
            else:
                generation=5
            z_trail = int(self.robot_name[-4:-2])*10
            ret = self.dashboard.initial(generation, z_trail)

            if ret == 1:
                print("初始化成功。robot initial successful")
                self.connection = True                
            else:
                self.error_id =2    ####サーボOFF　軸使用エラー 初始化失敗　PLC用
                self.error = True
                print("Fail to connect")
                self.opening = False  # Dobot電源確認用
                print("robot initial failed", ret)
                self.showInitialErrorMessage(ret)
                return

            #self.feed = DobotApiFeedBack(ip, feed_p)        ###0701 Hitbot无反馈
            self.opening = True  # Dobot電源確認用

    ''' ##def connectRobotBase_old
    def connectRobotBase_mg400(self):
        try:
            ip = self.dst_ip_address
            # NOTE:以下は固定値
            dashboard_p = 29999
            move_p = 30003
            feed_p = 30004
            self.dashboard = DobotApiDashboard_mg400(ip, dashboard_p)
            self.move = DobotApiMove_mg400(ip, move_p)
            self.feed = DobotApi_mg400(ip, feed_p)
            self.opening = True  # Dobot電源確認用
            # return dashboard, move, feed
        except Exception as e:
            print("Fail to connect")
            self.opening = False  # Dobot電源確認用
            raise e

    def connectRobotBase_cra(self):
        try:
            ip = self.dst_ip_address
            # NOTE:以下は固定値
            dashboard_p = 29999
            #move_p = 30003     ##0405 CRA系列使用TCP-IP V4，move class 废止，功能在Dashboard中实现
            feed_p = 30004
            self.dashboard = DobotApiDashboard(ip, dashboard_p)
            #self.move = DobotApiMove_mg400(ip, move_p)        ##0405 CRA系列使用TCP-IP V4，move class 废止，功能在Dashboard中实现
            self.feed = DobotApiFeedBack(ip, feed_p)         ##0405 DobotApiFeedBack class的 init 中建立了反馈用多线程
            self.opening = True  # Dobot電源確認用
            # return dashboard, move, feed
        except Exception as e:
            print("Fail to connect")
            self.opening = False  # Dobot電源確認用
            raise e
    '''
            
    ''' #並列処理，フィードバック hitbot この機能なし
    # NOTE:並列処理開始
    def startMultiFeedbackBase(self):
        self.feed_process = Process(target=self.getFeedbackBase)
        self.feed_process.daemon = True
        self.feed_process.start()
        return
    
    # NOTE:フィードバックループ #RB電源遮断時例外処理
    def getFeedbackBase_mg400(self):
        hasRead = 0
        sleep_t = 0.001
        while True:
            try:
                data = bytes()
                while hasRead < 1440:
                    temp = self.feed.socket_dobot.recv(1440 - hasRead)
                    if len(temp) > 0:
                        hasRead += len(temp)
                        data += temp
                hasRead = 0

                a = np.frombuffer(data, dtype=MyType_mg400)
                if hex((a['test_value'][0])) == '0x123456789abcdef':
                    # Refresh Properties
                    # self.current_actual = a["tool_vector_actual"][0]
                    # print("ROBOTループ",int(a["robot_mode"][0]))
                    self._robot_mode.value = int(a["robot_mode"][0])
                    # print("robot_mode",self._robot_mode.value)
                self.mySleepBase(sleep_t)
            except Exception:
                print("disconnected robot")
                self.opening = False
                self.feed_process.terminate()
                self.feed_process.join()
                self.mySleepBase(sleep_t)

    # NOTE:フィードバックループ #RB電源遮断時例外処理
    def getFeedbackBase(self):
        hasRead = 0
        sleep_t = 0.001
        while True:
            try:
                data = bytes()
                while hasRead < 1440:
                    temp = self.feed.socket_dobot.recv(1440 - hasRead)
                    if len(temp) > 0:
                        hasRead += len(temp)
                        data += temp
                hasRead = 0

                a = np.frombuffer(data, dtype=MyType)  
                if hex((a['test_value'][0])) == '0x123456789abcdef':
                    self._robot_mode.value = int(a["robot_mode"][0])
                    # print("robot_mode",self._robot_mode.value)
                self.mySleepBase(sleep_t)
            except Exception:
                print("disconnected robot")
                self.opening = False
                self.feed_process.terminate()
                self.feed_process.join()
                self.mySleepBase(sleep_t)
    '''

    ''' #ret 処理 hitbot 不要
    # NOTE:ret文字列を配列へ変換
    def transformStr2Ret(self, str: str):    ##0405  checkApiErrorBase中使用
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
        # "{"" and "}" and ";"の削除  ##0405 GetPose(user,tool)返回：ErrorID,{X,Y,Z,Rx,Ry,Rz},GetPose(User,Tool);
        align_str = str.replace('{', '').replace('}', '').replace(';', '')
        align_list = align_str.split(',')
        # print(align_list)     ##0405  ErrorID,X,Y,Z,Rx,Ry,Rz,GetPose(User,Tool)
        # 0番目を削除
        del align_list[0]      ##0405 X,Y,Z,Rx,Ry,Rz,GetPose(User,Tool)
        # 後ろから4番目以降を削除
        #del align_list[-4:]     ##0405 X,Y,Z,Rx
        # 6番目以降を削除
        del align_list[6:]     ##0405 X,Y,Z,Rx,Ry,Rz
        # float型にキャスト
        ret = [float(val) for val in align_list]
        return ret

    # NOTE:座標文字列を配列へ変換
    def transformStr2Joint(self, str: str):
        # "{"" and "}" and ";"の削除    ##0405 GetAngle() 返回：ErrorID,{J1,J2,J3,J4,J5,J6},GetAngle();
        align_str = str.replace('{', '').replace('}', '').replace(';', '')
        align_list = align_str.split(',')
        # 0番目を削除
        del align_list[0]
        # 後ろから3番目以降を削除
        #del align_list[-3:]    
        #6番目以降を削除
        del align_list[6:]     ##0405 X,Y,Z,Rx,Ry,Rz
        # float型にキャスト
        ret = [float(val) for val in align_list]
        return ret

    # NOTE:エラーコード文字列を数値へ変換，
    def transformStr2Error(self, str: str):
        ##0405 GetErrorID()   返回 ErrorID,{[[id,...,id], [id], [id], [id], [id], [id], [id]]},GetErrorID();
        align_str = str.replace('{', '').replace('}', '').replace(';', '').replace(
            '\n', '').replace('\t', '').replace('[', '').replace(']', '')
        align_list = align_str.split(',')
        try:
            ret = int(align_list[1])     ##0405 为空时表示无错误。ErrorID为表示GetErrorID命令自身的执行是否有错
        except:
            ret = 0
        return ret    ##0405 返回有无，有时的第一个
    '''
    
    def stopRobotBase(self) -> None:
        #ret = self.dashboard.ResetRobot()  #####0422 V40无此函数，改用stop
        #ret = self.dashboard.Stop()
        ret = self.dashboard.new_stop_move()  ##立即结束当前正在执行的指令
        #self.checkApiErrorBase(ret)   ###hitbot 不使用
        return

    # NOTE:Moving発生確認 
    '''old
    def checkMovingBase_mg400(self):
        if self.robot_mode == 7:
            self.moving = True
        else:
            self.moving = False

    def checkMovingBase_cra(self):
        if self.robot_mode == 7 or self.robot_mode == 8:   ##0405   7:运行状态(工程，TCP队列运动等),8:单次运动状态（点动、RunTo等）
            self.moving = True
        else:
            self.moving = False
    '''
    
    def checkMovingBase(self):
        ##############################################################
        # 運動状態取得 hitbot  self.moving=1　運動
        ##############################################################
        #### 方法１
        self.dashboard.get_scara_param()  ####0701 hitbot状态取得 , checkMovingBase单独调用时需要，若只是getRobotStatus中调用则不需要
        self.moving = self.dashboard.move_flag  #### =0 the robot arm is in standby state, =1 in motion state
        ####　方法２
        #self.moving = not self.dashboard.is_stop()  #### is_stop =0：运动   =1：停止
        
    # NOTE:エラー発生確認
    '''dobot 
    def checkErrorBase_dobot(self):
        if self.robot_mode == 9:
            self.error = True
    '''
            
    def checkErrorBase(self):
        ### hitbot   
        # get_joint_state(self, joint_num)  joint_num：轴号1-4 , 1：关节正常
        for ii in range(1,5):
            if self.dashboard.get_joint_state(ii) != 1:
                self.error = True
                return
        self.error = False

    '''  #transformCommmonErrorID old
    def transformCommmonErrorID_mg400(self, error_id):
        error_dict = dict(ERROR_LIST_mg400)
        # dragging mode on
        if self.robot_mode == 6:     #拖拽模式
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

    def transformCommmonErrorID_cra(self, error_id):
        ERROR_LIST = [
            ['none1', 1],           # 非常停止ON
            ['-3', 1],           # 非常停止状態、机器人处于急停状态
            ['116', 1],           # 硬件急停按钮被拍下、ハードの非常停止ボタンが押されている、The emergency stop button is captured
            ['132', 1],           # 软件急停信号被触发、ソフト非常停止信号がトリガされる、The software emergency stop signal is triggered
            ['133', 1],           # 用户急停信号被触发、ユーザ非常停止信号がトリガされる、The user emergency stop signal is triggered   

            ['r6', 2],               # サーボOFF　軸使用エラー、ROBOT_MODE　6： ROBOT_MODE_BACKDRIVE 拖拽模式
            ['-4', 2],         #"The robot is in power down state""机械臂处于下电状态。机械臂下电状态下无法执行指令，需要先给机械臂上电。"
 
            ['none2', 3],            # 原点復帰未完了エラー
            ['114', 3],            # ??? "机器人标定零点失败",The robot failed to calibrate zero
            ['1441', 3],            # ??? "零点标定失败",Zero calibration failure

            ['17', 4],               # 目標位置ソフトリミットオーバー??    mg400:逆解算无解,"Inverse kinematics error with no solution
            ['17', 4],               # 逆解算无解,"Inverse kinematics error with no solution
            ['30', 4],               # 全参逆解求解失败,"The full parameter inverse solution fails to be solved
            ['1395', 4],               # 逆解执行失败,"The inverse solution failed to execute
            #####0507 追加
            ['-40001', 4],         #第一个参数的参数范围错误。-40000表示必选参数范围错误。最后一位1表示下发第1个必选参数的参数范围错误。"
            ['-40002', 4],         #第二个参数的参数范围错误。-40000表示必选参数范围错误。最后一位2表示下发第2个必选参数的参数范围错误。"
            ['-60001', 4],         #当可选参数中有带名称的参数时，表示任意带名称的可选参数范围错误。否则表示第一个可选参数的参数范围错误。-60000表示可选参数范围错误。有带名称的可选参数时，表示带名称的可选参数错误，如a=200。最后一位1表示下发第1个可选参数的参数范围错误。"
            ['-60002', 4],         #第二个可选参数的参数范围错误,-60000表示可选参数范围错误。最后一位2表示下发第2个可选参数的参数类型错误。"
            ['-1', 4],             #"Command execution failed","命令执行失败。已收到命令，但执行失败了"
   
            ['23', 5],               # ??目標軌跡ソフトリミットオーバーエラー,  mg400:直线运动过程中规划点超出工作空间,"Plan point during linear motion out of working area"
            ['224', 5],               # ??机器人接近安全工作区域","Robot approaching safe working area,"ロボットが安全作業エリアに接近しています"

            #['18', 6],              # 実位置ソフトリミットオーバーエラー ??, mg400:目标位置触发关节限位
            ['18', 6],              # ?? "逆解结果限位,"Inverse kinematics error with result out of working area","逆計算の結果は位置制限",

           
            #['-2', 7],                # ？？？過負荷エラー　復帰不可  mg400:-2　なし
            ['-2', 7],                 #CRA：-2 机器人处于报警状态      "The robot is in an error state"    机器人报警状态下无法执行指令，需要清除报警后重新下发指令。
                                        #0422  报警状态,復帰不可を　PLCへ７番
            ['1440', 7],                # ？温度过高，或温控系统无法有效控制温度,"The temperature is too high, or the temperature control system cannot effectively control the temperature"

            ['12294', 8],              # 衝突検知エラー　復帰可
            ['117', 8],              # 衝突検知エラー　復帰可  。GetErrorID()其中碰撞检测值为117
            ['r11', 8],              # 衝突検知エラー　復帰可  11 ROBOT_MODE_COLLISION 碰撞检测触发状态

            ["other", 32]            # その他のエラー
        ]

        error_dict = dict(ERROR_LIST)
        # dragging mode on
        if self.robot_mode == 6:     #拖拽模式
            self.error = True
            _tmp_error_id = "r" + str(self.robot_mode)
            common_error_id = error_dict[str(_tmp_error_id)]
            return common_error_id

        if self.robot_mode == 11:     #碰撞检测触发状态
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
                ####0507 test
                #with open('log_err_cra_api.txt', 'a') as fe:
                #    print("CRA-api--transformCommmonErrorID: iD=", common_error_id,file=fe)
                #fe.close()   ####0507 test

            except Exception:
                # other error
                common_error_id = 32

        return common_error_id
    '''

    def transformCommmonErrorID(self, error_id):
        #### hitbot
        ERROR_LIST = [
            ['-1', 1],           # 非常停止ON
            ['5', 8],              # 衝突検知エラー　復帰可
            ####  2 サーボOFF　軸使用エラー
            ['6', 2],               ##拖拽模式
            ['7', 2],               ##：关节缺轴/失效  
            ['0', 2],               ##：轴发生复位，需要重新初始化 
            ['3', 2],               ##3：未初始化  
            ['4', 2],               ##：4：轴状态获取失败 
            ####  7 過負荷エラー　復帰不可
            ['9', 7],                # 电机堵转/过电流保护
            ['10', 7],                # 10：过压保护
            ['25', 7],                #MOS ntc 温度过高
            ['27', 7],                #27：电机ntc 温度过高
            ["other", 32]            # その他のエラー                     
                    ]
        '''
            此处无对应项目，在运动指令中可判断，另做函数
            ['none2', 3],            # 原点復帰未完了エラー
            ['17', 4],               # 目標位置ソフトリミットオーバー
            ['23', 5],               # 目標軌跡ソフトリミットオーバーエラー
            ['18', 6],              # 実位置ソフトリミットオーバーエラー
        '''

        error_dict = dict(ERROR_LIST)
        common_error_id = 0
        for ii in range(5): 
            if error_id[ii] != 1:  # error 発生時
                try:
                    common_error_id = error_dict[str(error_id[ii])]
                except Exception:  # other error                    
                    common_error_id = 32  
                return common_error_id
        return common_error_id    
    
    # NOTE:エラー番号の取得
    def getErrorBase(self):     
        #### hitbot
        error_id =[1,1,1,1,1]   ### 1 正常
        ret= self.dashboard.get_hard_emergency_stop_state()  ####获取急停状态 -1：该机型不支持；0：未处于急停状态；1：处于急停状态；3：未连接；4：没有急停功能；
        if ret == 1:
            error_id[0] = -1    ###急停状态，存于error_id[0]。各个轴状态存于error_id[1:4]
            
        for ii in range(1,5):
            ret= self.dashboard.get_joint_state(ii) 
            if ret != 1:
                error_id[ii]=ret
                print('error: joint_num ',ii)
                self.ShowErrorMessage(ret)                
                self.error = True
                
        com_err_id = self.transformCommmonErrorID(error_id)    ##第一个错误的类型重新编号，PLC处理用
        return com_err_id

    '''Dobot　cra エラー処理
    def getErrorBase_cra(self):
        ret = self.dashboard.GetErrorID()   ##0405返回 ErrorID,{[[id,...,id], [id], [id], [id], [id], [id], [id]]},GetErrorID();
        val = self.transformStr2Error(ret)        ##0405 返回有无，有时[[id,...,id]中的第一个
        com_err_id = self.transformCommmonErrorID(val)    ##0405  第一个错误的类型重新编号，PLC处理用？
        self.ShowErrorMessage(val)    ##0405 增加显示错误信息，在调试时使用，所有错误均显示
        return com_err_id

    def ShowErrorMessage_cra(self,ErroID):
        ##0405用V4的标准示例程序改造
        #详细报警信息读入
        alarmControllerFile = "files/alarmController.json"
        alarmServoFile = "files/alarmServo.json"
        currrntDirectory = os.path.dirname(__file__)
        jsonContrellorPath = os.path.join(currrntDirectory, alarmControllerFile)
        jsonServoPath = os.path.join(currrntDirectory, alarmServoFile)

        with open(jsonContrellorPath, encoding='utf-8') as f:
            dataController = json.load(f)
        with open(jsonServoPath, encoding='utf-8') as f:
            dataServo = json.load(f)        

        #0405 报警内容显示。用示例程序DobotApidashboard自带的GetErrorID，ParseResultId处理        
        geterrorID = self.dashboard.ParseResultId(self.dashboard.GetErrorID())   ##ErrorID,{[[id,...,id],  的ErrorID部分，命令自身的错误
        if geterrorID[0] == 0:      ##ErrorID,{[[id,...,id], [id], [id], [id], [id], [id], [id]]},GetErrorID(); 的{}中的id部分
            for i in range(1, len(geterrorID)):
                alarmState = False
                for item in dataController:
                    if geterrorID[i] == item["id"]:
                        print("机器告警 Controller GetErrorID", i, item["zh_CN"]["description"])
                        print("alarm Controller GetErrorID",i, item["en"]["description"])
                        alarmState = True
                        with open('log_err_cra_api.txt', 'a') as fe:
                            print("机器告警 Controller GetErrorID", i, item["zh_CN"]["description"],file=fe)
                            #print("alarm Controller GetErrorID",i, item["en"]["description"],file=fe)
                        fe.close()    
                        break
                if alarmState:
                    continue

                for item in dataServo:
                    if geterrorID[i] == item["id"]:
                        print("机器告警 Servo GetErrorID", i, item["zh_CN"]["description"])
                        print("alarm Servo GetErrorID", i, item["en"]["description"])
                        with open('log_err_cra_api.txt', 'a') as fe:
                            print("机器告警 Servo GetErrorID", i, item["zh_CN"]["description"],file=fe)
                            print("alarm Servo GetErrorID", i, item["en"]["description"],file=fe)
                        fe.close()    
                        break
    '''

    def ShowErrorMessage(self,ErroID):
        ###hitbot   error for get_joint_state()
        if ErroID ==0:
            print('error number 0:  轴发生复位，需要重新初始化')
        if ErroID ==2:
            print('error number 2:  传入参数超范围')
        if ErroID ==3:
            print('error number 3:  未初始化')
        if ErroID ==4:
            print('error number 4:  轴状态获取失败')
        if ErroID ==5:
            print('error number 5:  发生碰撞')
        if ErroID ==6:
            print('error number 6:  处于拖动模式')
        if ErroID ==7:
            print('error number 7:  关节缺轴/失效')
        if ErroID ==8:
            print('error number 8:  编码器错误')
        if ErroID ==9:
            print('error number 9:  电机堵转/过电流保护')
        if ErroID ==10:
            print('error number 10:  过压保护')
        if ErroID ==11:
            print('error number 11:  手臂收到PC 发送的错误数据')
        if ErroID ==12:
            print('error number 12:  手臂主控与驱动通讯异常')
        if ErroID ==21:
            print('error number 21:  MOS ntc 开路')
        if ErroID ==22:
            print('error number 22:  MOS ntc 短路')
        if ErroID ==23:
            print('error number 23:  电机ntc 开路')
        if ErroID ==24:
            print('error number 24:  电机ntc 短路')
        if ErroID ==25:
            print('error number 25:  MOS ntc 温度过高')
        if ErroID ==26:
            print('error number 26:  MOS ntc 温度过低')
        if ErroID ==27:
            print('error number 27:  电机ntc 温度过高')

    # NOTE:apiのコマンドエラー確認
    ''' ##def checkApiErrorBase_old
    def checkApiErrorBase_mg400(self, ret: str):
        api_err = False
        _ret = self.transformStr2Ret(ret)
        if _ret != 0:
            self.error = True
            # error_id = self.transformStr2Error(ret)
            if _ret == -1:
                print("Fail to get\nApi Error No.", _ret)
            else:
                print("Api Error No.", _ret)
                api_err = True
        return api_err

    def checkApiErrorBase_cra(self, ret: str):      ##0405  函数返回值 api_error =0 or 1, 未使用
        api_err = False
        _ret = self.transformStr2Ret(ret)
        if _ret != 0:
            self.error = True
            #self.error_id = self.transformStr2Error(ret)   ####0507 _ret=-40001, error_id=0
            self.error_id = _ret
            com_err_id = self.transformCommmonErrorID(_ret)    ####0507 新增。因为以前checkApiError只显示，未向PLC反馈所以Raspi停止或报错PLC却无处理
            print("Api Error No.", _ret)
            print("Error ret:", ret)            
            if _ret == -1:
                print("Command execution failed","命令执行失败。已收到命令，但执行失败了")
            if _ret == -2:
                print("The robot is in an error state","机器人处于报警状态。机器人报警状态下无法执行指令，需要清除报警后重新下发指令。")
            if _ret == -3:
                print("The robot is in emergency stop state","机器人处于急停状态。机器人急停状态下无法执行指令，需要松开急停并清除报警后重新下发指令。。")
            if _ret == -4:
                print("The robot is in power down state","机械臂处于下电状态。机械臂下电状态下无法执行指令，需要先给机械臂上电。")

            if _ret == -10000:
                print("","命令错误。下发的命令不存在。")
            if _ret == -20000:
                print("","参数数量错误。下发命令中的参数数量错误。")
            if _ret == -30001:
                print("","当必选参数中有带名称的参数时，表示任意带名称的必选参数格式错误,否则表示第一个参数的参数类型错误。-30000表示必选参数类型错误,有带名称的必选参数时，表示带名称的必选参数错误，如join={1,2,3,4,5,6}。否则最后一位1表示下发第1个必选参数的参数类型错误。")
            if _ret == -30002:
                print("","第二个参数的参数类型错误。-30000表示必选参数类型错误。最后一位2表示下发第2个必选参数的参数类型错误")
            if _ret == -40001:
                print(""," 第一个参数的参数范围错误。-40000表示必选参数范围错误。最后一位1表示下发第1个必选参数的参数范围错误。")
            if _ret == -40002:
                print("","第二个参数的参数范围错误。-40000表示必选参数范围错误。最后一位2表示下发第2个必选参数的参数范围错误。")
            if _ret == -50001:
                print("","当可选参数中有带名称的参数时，表示任意带名称的可选参数格式错误。否则表示第一个可选参数的参数类型错误。-50000表示可选参数类型错误。有带名称的可选参数时，表示带名称的可选参数错误，如use=1。否则最后一位1表示下发第1个可选参数的参数类型错误。")
            if _ret == -50002:
                print("","-50000表示可选参数类型错误。最后一位2表示下发第2个可选参数的参数类型错误。")
            if _ret == -60001:
                print("","当可选参数中有带名称的参数时，表示任意带名称的可选参数范围错误。否则表示第一个可选参数的参数范围错误。-60000表示可选参数范围错误。有带名称的可选参数时，表示带名称的可选参数错误，如a=200。最后一位1表示下发第1个可选参数的参数范围错误。")
            if _ret == -60002:
                print("","第二个可选参数的参数范围错误,-60000表示可选参数范围错误。最后一位2表示下发第2个可选参数的参数类型错误。")
            else:
                #print("Api Error No.", _ret)
                api_err = True
                
            with open('log_err_cra_api.txt', 'a') as fe:
                print("Api Error No.", _ret,file=fe)
                print("Error ret:", ret,file=fe)            
                print("Error id,com_err_id:", self.error_id,com_err_id,file=fe)            
                if _ret == -1:
                    #print("Fail to get\nApi Error No.", _ret)
                    print("Command execution failed","命令执行失败。已收到命令，但执行失败了",file=fe)
                if _ret == -2:
                    print("The robot is in an error state","机器人处于报警状态。机器人报警状态下无法执行指令，需要清除报警后重新下发指令。",file=fe)
                if _ret == -3:
                    print("The robot is in emergency stop state","机器人处于急停状态。机器人急停状态下无法执行指令，需要松开急停并清除报警后重新下发指令。",file=fe)
                if _ret == -4:
                    print("The robot is in power down state","机械臂处于下电状态。机械臂下电状态下无法执行指令，需要先给机械臂上电。",file=fe)

                if _ret == -10000:
                    print("","命令错误。下发的命令不存在。",file=fe)
                if _ret == -20000:
                    print("","参数数量错误。下发命令中的参数数量错误。",file=fe)
                if _ret == -30001:
                    print("","当必选参数中有带名称的参数时，表示任意带名称的必选参数格式错误,否则表示第一个参数的参数类型错误。-30000表示必选参数类型错误,有带名称的必选参数时，表示带名称的必选参数错误，如join={1,2,3,4,5,6}。否则最后一位1表示下发第1个必选参数的参数类型错误。",file=fe)
                if _ret == -30002:
                    print("","第二个参数的参数类型错误。-30000表示必选参数类型错误。最后一位2表示下发第2个必选参数的参数类型错误",file=fe)
                if _ret == -40001:
                    print(""," 第一个参数的参数范围错误。-40000表示必选参数范围错误。最后一位1表示下发第1个必选参数的参数范围错误。",file=fe)
                if _ret == -40002:
                    print("","第二个参数的参数范围错误。-40000表示必选参数范围错误。最后一位2表示下发第2个必选参数的参数范围错误。",file=fe)
                if _ret == -50001:
                    print("","当可选参数中有带名称的参数时，表示任意带名称的可选参数格式错误。否则表示第一个可选参数的参数类型错误。-50000表示可选参数类型错误。有带名称的可选参数时，表示带名称的可选参数错误，如use=1。否则最后一位1表示下发第1个可选参数的参数类型错误。",file=fe)
                if _ret == -50002:
                    print("","-50000表示可选参数类型错误。最后一位2表示下发第2个可选参数的参数类型错误。",file=fe)
                if _ret == -60001:
                    print("","当可选参数中有带名称的参数时，表示任意带名称的可选参数范围错误。否则表示第一个可选参数的参数范围错误。-60000表示可选参数范围错误。有带名称的可选参数时，表示带名称的可选参数错误，如a=200。最后一位1表示下发第1个可选参数的参数范围错误。",file=fe)
                if _ret == -60002:
                    print("","第二个可选参数的参数范围错误,-60000表示可选参数范围错误。最后一位2表示下发第2个可选参数的参数类型错误。",file=fe)
            fe.close()
  
            #self.getErrorBase()

        return api_err

    '''

    #hitbot因各函数返回值定义不同一，不使用同一的checkApiErrorBase（），在各命令后处理
            
    def showInitialErrorMessage(self,ErroID):
        ###hitbot   error for initial()
        if ErroID ==0:
            print('error number 0:  机械臂不在线')
        if ErroID ==2:
            print('error number 2:  generation 参数错误')
        if ErroID ==3:
            print('error number 3:  机械臂当前位置不在限定范围，可以使用joint_home使关节强制回零')
        if ErroID ==12:
            print('error number 12:  z_travel 传参错误')
        if ErroID ==101:
            print('error number 101: 传入参数NOT A NUMBER')
        if ErroID ==105:
            print('error number 105:  存在某一个关节失效')
        if ErroID >=10000:
            print('error number: ', ErroID, '  pid 自检异常')

    def checkMoveErrorBase(self, ErroID):
        ###hitbot   error for moveAbsolutePtp()-> new_movej_xyz_lr
        if ErroID ==0:
            print('error number 0:  正在执行其他指令，本次指令无效')
        elif ErroID ==2:
            print('error number 2:  设置速度小于等于零')
        elif ErroID ==3:
            print('error number 3:  未初始化')
        elif ErroID ==4:
            print('error number 4:  moveJ:目标点无法到达, moveL,xyz_move:过程点无法到达 ')
        elif ErroID ==5:
            print('error number 5:  xyz_move:方向参数错误')
        elif ErroID ==6:
            print('error number 6:  伺服未开启')
        elif ErroID ==7:
            print('error number 7:  moveJ:无法以设定手系到达目标点位, moveL:存在中间过程点无法以机械臂当前姿态（手系）达到,xyz_move:该姿态无法完成直线运动')
        elif ErroID ==11:
            print('error number 11:  手机端在控制')
        elif ErroID ==99:
            print('error number 99:  急停中')
        elif ErroID ==101:
            print('error number 101: 传入参数NOT A NUMBER')
        elif ErroID ==102:
            print('error number 102: 发生碰撞，本次指令无效')
        elif ErroID ==103:
            print('error number 103: 轴发生复位，需要重新初始化，本次指令无效')

        ERROR_LIST_move = [
            ['99', 1],           # 急停中: 非常停止ON
            ['3', 2],               ##：未初始化 :サーボOFF　軸使用エラー
            ['6', 2],               ##：伺服未开启 :サーボOFF　軸使用エラー
            ['103', 2],               ##轴发生复位，需要重新初始化，本次指令无效  :サーボOFF　軸使用エラー            
            ['4', 4],               # 目标点无法到达 : 目標位置ソフトリミットオーバー
            ['7', 4],               # 无法以设定手系到达目标点位 : 目標位置ソフトリミットオーバー
            ['102', 8],              # 发生碰撞，本次指令无效 : 衝突検知エラー　復帰可
                            ]
        '''
            ['none1', 1],           # 非常停止ON
            ['r6', 2],               # サーボOFF　軸使用エラー
            ['none2', 3],            # 原点復帰未完了エラー
            ['17', 4],               # 目標位置ソフトリミットオーバー
            ['23', 5],               # 目標軌跡ソフトリミットオーバーエラー
            ['18', 6],              # 実位置ソフトリミットオーバーエラー
            ['-2', 7],                # 過負荷エラー　復帰不可
            ['12294', 8],              # 衝突検知エラー　復帰可
            ["other", 32]            # その他のエラー
        '''

        error_dict = dict(ERROR_LIST_move)
        common_error_id = 0
        try:
            common_error_id = error_dict[str(ErroID)]
        except Exception:  # other error                    
            common_error_id = 32  
        return common_error_id           
                
    def moveAbsolutePtpBase(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, vel: float = 100, acc: float = 100, dec: float = 100) -> None:
        #hitbot  
        j_acc = int(acc) #### int j1_max_acc ~ int j4_max_acc：关节1~4 加速度百分比 范围>=30,<=220
        ret = self.dashboard.new_set_acc(j_acc,j_acc,j_acc,j_acc)   ####设定new_movej_xyz_lr 运动模型的关节加速度百分比,范围>=30,<=220

        speed = XYZ_MAX_VEL * vel /100   ### PLC输入速度为百分比，

        # if dec ==22 :   ###22 左手， 2,21 右手
        #     lr =-1
        # else:
        #     lr =1
        if dec ==22 or dec ==26:   ##2 维持上一个动作的手系，失败换手。21：右手，失败换手。22：左手，失败换手。25：右手，不换手。26：左手，不换手
            self.lr =-1
        if dec ==21 or dec ==25:
            self.lr =1
        else:
            if self.lr != 1 and self.lr != -1:
                self.lr =1
        lr =  self.lr 
        print('new_movej_xyz_lr',x, y, z, rz, speed,lr)

        #ret = self.dashboard.new_movej_xyz_lr(x, y, z, rz, speed,0.5,1)   ##以movej 的运动方式，并以指定手系达目标点 
        ret = self.dashboard.new_movej_xyz_lr(x, y, z, rz, speed,0.5,lr)   ##以movej 的运动方式，并以指定手系达目标点 
            ####new_movej_xyz_lr(self,goal_x,goal_y,goal_z,goal_r,speed,roughly,lr)  ###lr以外全为float。
            ### 用左手系 int lr：1 右手系，-1 左手系，angle2>0 右手系，否则为左手系
            ###float roughly：使用中间值0.5，0 先运动到前目标点，并且在当前目标点的速度等于0，而后在去往新的目标点，1 在有新目标点时，将在当前目标点附近以最大速度通过，此参数取值范围0 到1，越大通过速度越快，但是通过点距离当前目标点越远。
        if ret == 1:  ###成功
            print("moveAbsolutePtpBase : robot move start ")
        elif ret ==0:  ##失败，正在执行其他指令, 直线和旋转运动切换时经常出现，一般需等待0.5s左右
            jj =0
            while ret ==0 and jj<40:
                sleep(0.05)
                ret = self.dashboard.new_movej_xyz_lr(x, y, z, rz, speed,0.5,lr)   ##以movej 的运动方式，并以指定手系达目标点 
                jj +=1    
            print('等待时间0.05s*',jj)
            if  ret == 1:  ###成功
                print("moveAbsolutePtpBase : robot move start ")          
            #elif ret ==7 :   ## 无法以设定手系到达
            elif ret ==7 and dec !=25 and dec !=26:   ## 无法以设定手系到达,且可变手（25,26以外）
                lr = lr*-1
                ret = self.dashboard.new_movej_xyz_lr(x, y, z, rz, speed,0.5,lr)   ##以movej 的运动方式，并以指定手系达目标点 
                # if  ret == 1:  ###成功
                #     print("moveAbsolutePtpBase : robot move start ")          
                if  ret == 1:  ###成功
                    self.lr=lr
                    print("moveAbsolutePtpBase : robot move start ")          
                else:
                    print("moveAbsolutePtpBase : robot move failed ")
                    self.error = True
                    self.error_id = self.checkMoveErrorBase(ret)   
            else:
                print("moveAbsolutePtpBase : robot move failed ")
                self.error = True
                self.error_id = self.checkMoveErrorBase(ret)   
        #elif ret ==7:   ## 无法以设定手系到达
        elif ret ==7 and dec !=25 and dec !=26:   ## 无法以设定手系到达,且可变手（25,26以外）
            print('切换手系')
            lr = lr*-1
            ret = self.dashboard.new_movej_xyz_lr(x, y, z, rz, speed,0.5,lr)   ##以movej 的运动方式，并以指定手系达目标点 
            # if  ret == 1:  ###成功
            #     print("moveAbsolutePtpBase : robot move start ")          
            if  ret == 1:  ###成功
                self.lr=lr
                print("moveAbsolutePtpBase : robot move start ")          
            else: 
                print("moveAbsolutePtpBase : robot move failed ")
                self.error = True
                self.error_id = self.checkMoveErrorBase(ret)   
        else:    
            print("moveAbsolutePtpBase : robot move failed ")
            self.error = True
            self.error_id = self.checkMoveErrorBase(ret)
        return

    def moveAbsoluteLineBase(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, vel: float = 100, acc: float = 100, dec: float = 100) -> None:   ###0422 与main中一致，与main中一致，Rx ->rx
        # パーセントに換算
        speed = XYZ_MAX_VEL * vel /100 ### PLC输入速度为百分比，
        print('movel_xyz',x, y, z, rz, speed)
        ret = self.dashboard.movel_xyz(x, y, z, rz, speed)    ##以movel 的运动方式到达目标点 movel_xyz(self, goal_x, goal_y, goal_z, goal_r, speed)float speed：xyz 点的线速度（mm/s）或轴4 的旋转角速度（deg/s）
        if ret == 1:  ###成功
            print("moveAbsolutePtpBase : robot move start ")
        elif ret ==0:  ##失败，正在执行其他指令, 直线和旋转运动切换时经常出现，一般需等待0.5s左右
            jj =0
            while ret ==0 and jj<40:
                sleep(0.05)
                ret = self.dashboard.movel_xyz(x, y, z, rz, speed)  ##以movel 的运动方式到达目标点
                jj +=1    
            print('等待时间0.05s*',jj)
            if  ret == 1:  ###成功
                print("moveAbsolutePtpBase : robot move start ")          
            #elif ret ==7 :   ## 无法以设定手系到达
            elif ret ==7 and dec !=15:   ## 无法以设定手系到达,且允许换手（15以外）
                print('切换手系')
                ret = self.dashboard.change_attitude(speed)     ###切换手系
                ret = self.dashboard.movel_xyz(x, y, z, rz, speed)  ##以movel 的运动方式到达目标点
                # if  ret == 1:  ###成功
                #     print("moveAbsolutePtpBase : robot move start ")          
                if  ret == 1:  ###成功
                    self.lr=self.lr*-1  ##更新手系flag
                    print("moveAbsolutePtpBase : robot move start ")          
                else:
                    print("moveAbsolutePtpBase : robot move failed ")
                    self.error = True
                    self.error_id = self.checkMoveErrorBase(ret)   
            else:
                print("moveAbsolutePtpBase : robot move failed ")
                self.error = True
                self.error_id = self.checkMoveErrorBase(ret)   
        #elif ret ==7:   ## 无法以设定手系到达
        elif ret ==7 and dec !=15:   ## 无法以设定手系到达,且允许换手（15以外）
            print('切换手系')
            ret = self.dashboard.change_attitude(speed)     ###切换手系
            #sleep(0.05)
            ret = self.dashboard.movel_xyz(x, y, z, rz, speed)  ##以movel 的运动方式到达目标点
            # if  ret == 1:  ###成功
            #     print("moveAbsolutePtpBase : robot move start ")          
            if  ret == 1:  ###成功
                self.lr=self.lr*-1  ##更新手系flag
                print("moveAbsolutePtpBase : robot move start ")          
            else: 
                print("moveAbsolutePtpBase : robot move failed ")
                self.error = True
                self.error_id = self.checkMoveErrorBase(ret)   
        else:    
            print("moveAbsolutePtpBase : robot move failed ")
            self.error = True
            self.error_id = self.checkMoveErrorBase(ret)
        return
        # if ret == 1:
        #     print("moveAbsoluteLineBase : robot move start ")
        # else:
        #     print("moveAbsoluteLineBase : robot move failed ")
        #     self.error = True
        #     self.error_id = self.checkMoveErrorBase(ret)
        # return

    def moveRelativeBase(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, vel: int = 100, acc: int = 100, dec: int = 100) -> None:      ###0422 与main中一致，Rx ->rx
        current_list = self.current_pos
        offset_list = [x, y, z,  rx, ry, rz]
        target_list = []
        for i in range(6):
            val = current_list[i] + offset_list[i]
            target_list.append(val)
        ret = self.moveAbsoluteLineBase(
            x=target_list[X], y=target_list[Y], z=target_list[Z], rx=target_list[RX], ry=target_list[RY], rz=target_list[RZ], vel=vel, acc=acc, dec=dec)
        return

    '''### move dobot cra
    def moveAbsolutePtpBase_cra(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, vel: float = 100, acc: float = 100, dec: float = 100) -> None:
        # パーセントに換算
        vel_joint_val = int(vel)
        acc_joint_val = int(acc)
        #ret = self.move.MovJ(x, y, z,  Rx, Ry, Rz, (vel_joint_val, acc_joint_val))
        #def MovJ(self, a1, b1, c1, d1, e1, f1, coordinateMode, user=-1, tool=-1, a=-1, v=-1, cp=-1):
        #ret = self.dashboard.MovJ(x, y, z, Rx, Ry, Rz, 0, a=acc_joint_val, v=vel_joint_val)  ##0405 coordinateMode int  目标点的坐标值模式    0为pose方式  1为joint
        ret = self.dashboard.MovJ(x, y, z, rx, ry, rz, 0, a=acc_joint_val, v=vel_joint_val)  ##0405 coordinateMode int  目标点的坐标值模式    0为pose方式  1为joint, ###0422 与main中一致，Rx ->rx
        self.checkApiErrorBase(ret)
        return

    #def moveAbsoluteLineBase(self, x: float, y: float, z: float, Rx: float, Ry: float, Rz: float, vel: float = 100, acc: float = 100, dec: float = 100) -> None: 
    def moveAbsoluteLineBase_cra(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, vel: float = 100, acc: float = 100, dec: float = 100) -> None:   ###0422 与main中一致，与main中一致，Rx ->rx
        # パーセントに換算
        vel_line_val = int(vel)
        acc_line_val = int(acc)
        #ret = self.move.MovL(x, y, z, r, (vel_line_val, acc_line_val))
        #def MovL(self, a1, b1, c1, d1, e1, f1, coordinateMode, user=-1, tool=-1, a=-1, v=-1, speed=-1, cp=-1, r=-1):
            #coordinateMode int  目标点的坐标值模式    0为pose方式  1为joint
            #speed int 执⾏该条指令时的机械臂运动⽬标速度，与v互斥，若同时存在以speed为准。
        #ret = self.dashboard.MovL(x, y, z, Rx, Ry, Rz, 0, a=acc_line_val, v=vel_line_val)    ##0405   ###0422 与main中一致，Rx ->rx
        ret = self.dashboard.MovL(x, y, z, rx, ry, rz, 0, a=acc_line_val, v=vel_line_val)    ##0405   ###0422 与main中一致，Rx ->rx
        self.checkApiErrorBase(ret)    
        return

    #def moveRelativeBase(self, x: float, y: float, z: float, Rx: float, Ry: float, Rz: float, vel: int = 100, acc: int = 100, dec: int = 100) -> None:
    def moveRelativeBase_cra(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, vel: int = 100, acc: int = 100, dec: int = 100) -> None:      ###0422 与main中一致，Rx ->rx
        current_list = self.current_pos
        #offset_list = [x, y, z,  Rx, Ry, Rz]
        offset_list = [x, y, z,  rx, ry, rz]
        target_list = []
        #for i in range(4):       ##0405
        for i in range(6):
            val = current_list[i] + offset_list[i]
            target_list.append(val)
        #ret = self.moveAbsoluteLineBase(
        #    x=target_list[X], y=target_list[Y], z=target_list[Z], Rx=target_list[Rx], Ry=target_list[Ry], Rz=target_list[Rz], vel=vel, acc=acc, dec=dec)
        ret = self.moveAbsoluteLineBase(
            x=target_list[X], y=target_list[Y], z=target_list[Z], rx=target_list[RX], ry=target_list[RY], rz=target_list[RZ], vel=vel, acc=acc, dec=dec)
        self.checkApiErrorBase(ret)
        return

    def moveOriginBase_dobot(self) -> None:
        pass 
    '''

    def moveOriginBase(self) -> None:
        #### hitbot 各个轴依次回零点
        for joint_num in range(1,5):
            ret = self.dashboard.joint_home(joint_num)  ####使轴回到零位
            if ret == 1:
                print(joint_num," 号轴回零成功")
            else:
                print(joint_num," 号轴回零失败")

    def setServoOnBase_dobot(self):
        ret = self.dashboard.EnableRobot()
        self.checkApiErrorBase(ret)
        # self.servo = True
        return

    def setServoOnBase(self):
        ###hitbot
        ret = self.dashboard.unlock_position() 
            ####解锁机械臂，使机械臂可以接受运动指令,一般初始化成功后立刻调用.(相当上使能？)
        if ret == 1:                   
            print("解锁成功")
        else:
            print("机械臂不在线")
            self.error = True
        return

    def setServoOffBase_old(self):
        ret = self.dashboard.DisableRobot()
        self.checkApiErrorBase(ret)
        # self.servo = False
        return

    def setServoOffBase(self):
        pass     ####hitbot SDK 无上下使能，只能开关电源

    def resetErrorBase_old(self):
        self.error = False
        ret = self.dashboard.ClearError()
        self.checkApiErrorBase(ret)
        if self.servo:
            # ONしてからOFFにしないとサーボ切れない
            # self.setServoOn()
            # self.mySleepBase(0.3)
            self.setServoOff()
        return
        
    def resetErrorBase(self):
        print('reset')
        self.ClearError()   ####hitbot 库中无ClearError，新规做成
        self.error = False
        sleep(1)     ######0822 sleep重要。因无serverONOFF功能，reset后ready失败占多数，反复reset和ready运气好可以成功
                        ### 加sleep后则可ready成功。估计是PLC极短间隔反复尝试造成。加sleep后可以正常处理指令
        return

    def ClearError(self):
        if self.error == True:
            self.dashboard.close_server()   ####关闭网络服务器(server.exe 程序）调用后，手臂和pc 的通讯将会断开
            print('close')
            sleep(1)   ####函数返回后，建议延迟3s
            print('initial')
            ret = self.dashboard.net_port_initial()      ####申请内存和初始化网络服务器

        for kk in range(2):   ####错误处理的顺序可能影响清除的结果，重复两次
            if self.error == True:
                # if self.error_id ==8:   #  衝突検知エラー　復帰可            
                #     self.dashboard.emergency_stop()  ###立刻停止机械臂运动，然后释放除上下以外关节的转矩
                # if self.error_id ==1:   # 非常停止ON
                #     self.dashboard.clear_hard_emergency_stop()   ###急停按钮复位后，发送清除急停状态，进入正常模式
                if self.error_id ==3:   # 原点復帰未完了エラー
                    print('原点復帰未完了エラー')
                    for joint_num in range(1,5):
                        ret=self.dashboard.joint_home(joint_num)  ####使轴回到零位
                        if ret ==1 :
                            self.error == False
                if self.error_id ==2:   # # サーボOFF　軸使用エラー
                    print('サーボOFF　軸使用エラー')
                    ret = self.dashboard.initial(1, 240)  ####0701 def initial(self, generation, z_trail)  
                    if ret ==1 :
                        self.error == False

            self.dashboard.get_scara_param()
            #print('communicate,is_connect,initial',self.dashboard.communicate_success,self.dashboard.is_connect(),self.dashboard.initial_finish)
            if self.dashboard.is_connect() == False or self.dashboard.communicate_success == False:  ###communicate_success:True：在线• False：不在线
                print('is_connect() == False')
                self.dashboard.close_server()   ####关闭网络服务器(server.exe 程序）调用后，手臂和pc 的通讯将会断开
                sleep(1)
                print('initial')
                ret = self.dashboard.net_port_initial()      ####申请内存和初始化网络服务器
                if ret != 1:
                    self.error_id =2    ####サーボOFF　軸使用エラー 初始化失敗　PLC用
                sleep(3)   ####函数返回后，建议延迟3s

                ret=self.dashboard.initial(1, 240)  ####初始化  
                if ret ==3:
                    for joint_num in range(1,5):
                        self.dashboard.joint_home(joint_num)  ####使轴回到零位
                    sleep(1)
                    ret=self.dashboard.initial(1, 240)  ####初始化  
                if ret != 1:   
                    self.error_id =2    ####サーボOFF　軸使用エラー 初始化失敗　PLC用
                
            elif self.dashboard.initial_finish ==False : #### True：已初始化• False：未初始化
                print('is_connect() == 未初始化')
                ret=self.dashboard.initial(1, 240)  ####初始化  
                if ret ==3:
                    for joint_num in range(1,5):
                        self.dashboard.joint_home(joint_num)  ####使轴回到零位
                    sleep(1)
                    ret=self.dashboard.initial(1, 240)  ####初始化  
                if ret != 1:   
                    self.error_id =2    ####サーボOFF　軸使用エラー 初始化失敗　PLC用
            else:
                return

    def moveInchingBase(self, width: int, axis_char_str: str, direction_char_str: str) -> None:
        pass
    
    '''  ##def moveJogBase_mg400
    def moveJogBase_mg400(self, axis_char_str: str, direction_char_str: str) -> None:
        # J1+ J2+ J3+ J4+ J5+ J6+
        # J1- J2- J3- J4- J5- J6-
        # X+ Y+ Z+ Rx+ Ry+ Rz+
        # X- Y- Z- Rx- Ry- Rz-
        if axis_char_str == "x" and direction_char_str == "+":
            axis_id = "X+"
        elif axis_char_str == "x" and direction_char_str == "-":
            axis_id = "X-"
        elif axis_char_str == "y" and direction_char_str == "+":
            axis_id = "Y+"
        elif axis_char_str == "y" and direction_char_str == "-":
            axis_id = "Y-"
        elif axis_char_str == "z" and direction_char_str == "+":
            axis_id = "Z+"
        elif axis_char_str == "z" and direction_char_str == "-":
            axis_id = "Z-"
        elif axis_char_str == "rx" and direction_char_str == "+":
            axis_id = "Rx+"
        elif axis_char_str == "rx" and direction_char_str == "-":
            axis_id = "Rx-"
        elif axis_char_str == "ry" and direction_char_str == "+":
            axis_id = "Ry+"
        elif axis_char_str == "ry" and direction_char_str == "-":
            axis_id = "Ry-"
        elif axis_char_str == "rz" and direction_char_str == "+":
            axis_id = "R+"
        elif axis_char_str == "rz" and direction_char_str == "-":
            axis_id = "R-"
        else:
            axis_id = None

        ret = self.move.runjog(axis_id=axis_id)
        self.checkApiErrorBase(ret)
        return

    def moveJogBase_cra(self, axis_char_str: str, direction_char_str: str) -> None:
        """ Dobot FR用
        def MoveJog(self, axis_id='', coordtype=-1, user=-1, tool=-1):
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
        axis_char_str=str.lower(axis_char_str)        ##0405 安全起见，字母变小写
        if axis_char_str == "x" and direction_char_str == "+":
            axis_id = "X+"
        elif axis_char_str == "x" and direction_char_str == "-":
            axis_id = "X-"
        elif axis_char_str == "y" and direction_char_str == "+":
            axis_id = "Y+"
        elif axis_char_str == "y" and direction_char_str == "-":
            axis_id = "Y-"
        elif axis_char_str == "z" and direction_char_str == "+":
            axis_id = "Z+"
        elif axis_char_str == "z" and direction_char_str == "-":
            axis_id = "Z-"
        elif axis_char_str == "rx" and direction_char_str == "+":
            axis_id = "Rx+"
        elif axis_char_str == "rx" and direction_char_str == "-":
            axis_id = "Rx-"
        elif axis_char_str == "ry" and direction_char_str == "+":
            axis_id = "Ry+"
        elif axis_char_str == "ry" and direction_char_str == "-":
            axis_id = "Ry-"
        elif axis_char_str == "rz" and direction_char_str == "+":
            axis_id = "Rz+"
        elif axis_char_str == "rz" and direction_char_str == "-":
            axis_id = "Rz-"
        elif axis_char_str == "j1" and direction_char_str == "-":   ###0422 新增J1-6
            axis_id = "J1-"
        elif axis_char_str == "j2" and direction_char_str == "-":
            axis_id = "J2-"
        elif axis_char_str == "j3" and direction_char_str == "-":
            axis_id = "J3-"
        elif axis_char_str == "j4" and direction_char_str == "-":
            axis_id = "J4-"
        elif axis_char_str == "j5" and direction_char_str == "-":
            axis_id = "J5-"
        elif axis_char_str == "j6" and direction_char_str == "-":
            axis_id = "J6-"
        elif axis_char_str == "j1" and direction_char_str == "+":   ###0422 新增J1 J1-6
            axis_id = "J1+"
        elif axis_char_str == "j2" and direction_char_str == "+":
            axis_id = "J2+"
        elif axis_char_str == "j3" and direction_char_str == "+":
            axis_id = "J3+"
        elif axis_char_str == "j4" and direction_char_str == "+":
            axis_id = "J4+"
        elif axis_char_str == "j5" and direction_char_str == "+":
            axis_id = "J5+"
        elif axis_char_str == "j6" and direction_char_str == "+":
            axis_id = "J6+"
        else:
            axis_id = None

        #ret = self.move.runjog(axis_id=axis_id)
        ####0507 test
        # with open('log_err_cra_api.txt', 'a') as fe:
            # print("CAR_api--moveJogBase: axis_id", axis_id,file=fe)
        # fe.close()   ####0507 test
 
        #ret = self.dashboard.MoveJog(axis_id=axis_id)     ##0405　MG400
        #ret = self.dashboard.MoveJog(axis_id=axis_id,coordtype=1)     ##0507 coordtype仅当axisID指定笛卡尔坐标系的轴时生效，
                                #指定运动轴所属的坐标系。0表示关节点动，1表示用户坐标系，2表示工具坐标系。默认值为0,此处应该使用1.
        ret = self.dashboard.MoveJog(axis_id=axis_id,coordtype=2,tool=0)     ##0516 use tool=0，
        self.checkApiErrorBase(ret)
        return
    '''
    def moveJogBase(self, axis_char_str: str, direction_char_str: str,vel:float):
        #self.moveJogBase_win(axis_char_str, direction_char_str,vel) 
        self.moveJogBase_linux(axis_char_str, direction_char_str,vel)
        #self.moveJogBase_linux_old(axis_char_str, direction_char_str,vel)

    def moveJogBase_win(self, axis_char_str: str, direction_char_str: str,vel:float) -> None:
        ### hitbot无Jog运动，类似的xyz-move需要指定距离，速度、实际是Inching运动. 
        # ###距离设为尽可能大的的距离，不可则距离半减
        ### TP中有速度指定，但未使用。若不指定则默认-1,在jogBase中改为5%  ###0821 已经修改，使用速度指定

        ###xyz_move(self,direction,distance,speed) 驱动机械臂沿某一方向运动指定距离，运动轨迹为直线，move_flag 等于false 时调用有效
        #int direction：1 x 轴正方向，2 y 轴正方向，3 z 轴正方向. float distance：移动距离（mm） float speed：移动速度（mm/s）

        # if vel >0:
        #     speed= vel/100
        # else:
        #     speed=0.5*XYZ_MAX_VEL 
        if vel >0:
            speed= vel*XYZ_MAX_VEL/100
        else:
            speed=0.05*XYZ_MAX_VEL 

        axis_char_str=str.lower(axis_char_str)        ##0405 安全起见，字母变小写
        if axis_char_str == "x":
            direction = int(1)
        elif axis_char_str == "y" :
            direction = int(2)
        elif axis_char_str == "z" :
            direction = int(3)
        
        #self.dashboard.get_scara_param()  ####0701 hitbot状态取得
        #current_pos = [self.dashboard.x,self.dashboard.y,self.dashboard.z,self.dashboard.r]
        current_pos = self.getCurrentPos()
        new_pos = current_pos[:]
        
        juli=800.0   ### 先付给较大的值   距离设为尽可能大的的距离
        if direction_char_str == "-":
            juli = -juli
        
        while abs(juli) > 0.1:    ###不可则距离半减，最小0.1mm
            new_pos[direction-1] = current_pos[direction-1]  + juli
            if self.dashboard.judge_in_range_xyzr(new_pos[0],new_pos[1],new_pos[2],new_pos[3]):  
                    ###def judge_in_range_xyzr(self,x,y,z,r)false：超出范围无法到达；true：可以到达
                distance=juli
                break
            else:
                juli = juli/2

        if abs(juli) <= 0.1:
            print('moveJogBase can not move in direction',axis_char_str, direction_char_str)
            return
        else:
            print('移动距离max',juli)
        self.dashboard.get_scara_param()  ####0701 hitbot状态取得
        if self.dashboard.move_flag == False:   ####True：正在运动• False：静止状态
            ret = self.dashboard.xyz_move(direction,distance,speed) 
            if ret == 1:
                print("moveJogBase : robot move start ")
            else:
                print("moveJogBase : robot move failed ")
                self.error = True
                self.error_id = self.checkMoveErrorBase(ret)
        else:
            print('moveJogBase: failed because robot is moving (move_flag = True)')

    def moveJogBase_linux(self, axis_char_str: str, direction_char_str: str,vel:float) -> None:
        ### hitbot无Jog运动，类似的xyz-move需要指定距离，速度、实际是Inching运动. 
        # ###距离设为尽可能大的的距离，不可则距离半减
        ### TP中有速度指定，但未使用。若不指定则默认-1,在jogBase中改为5%  ###0821 已经修改，使用速度指定

        ###xyz_move(self,direction,distance,speed) 驱动机械臂沿某一方向运动指定距离，运动轨迹为直线，move_flag 等于false 时调用有效
        #int direction：1 x 轴正方向，2 y 轴正方向，3 z 轴正方向. float distance：移动距离（mm） float speed：移动速度（mm/s）

        # if vel >0:
        #     speed= vel/100
        # else:
        #     speed=0.5*XYZ_MAX_VEL 
        if vel >0:
            speed= vel*XYZ_MAX_VEL/100
        else:
            speed=0.05*XYZ_MAX_VEL 

        axis_char_str=str.lower(axis_char_str)        ##0405 安全起见，字母变小写
        if axis_char_str == "x":
            direction = int(1)
        elif axis_char_str == "y" :
            direction = int(2)
        elif axis_char_str == "z" :
            direction = int(3)
        
        #self.dashboard.get_scara_param()  ####0701 hitbot状态取得
        #current_pos = [self.dashboard.x,self.dashboard.y,self.dashboard.z,self.dashboard.r]
        current_pos = self.getCurrentPos()
        new_pos = current_pos[:]
        
        juli=800.0   ### 先付给较大的值   距离设为尽可能大的的距离
        if direction_char_str == "-":
            juli = -juli
        
        while abs(juli) > 0.1:    ###不可则距离半减，最小0.1mm
            new_pos[direction-1] = current_pos[direction-1]  + juli
            #if self.dashboard.judge_in_range_xyzr(new_pos[0],new_pos[1],new_pos[2],new_pos[3]):  ###win 名称
            if self.dashboard.judge_in_range(new_pos[0],new_pos[1],new_pos[2],new_pos[3]):  
                    ###def judge_in_range_xyzr(self,x,y,z,r)false：超出范围无法到达；true：可以到达
                distance=juli
                break
            else:
                juli = juli/2

        if abs(juli) <= 0.1:
            print('moveJogBase can not move in direction',axis_char_str, direction_char_str)
            return
        else:
            print('移动距离max',juli)
        self.dashboard.get_scara_param()  ####0701 hitbot状态取得
        if self.dashboard.move_flag == False:   ####True：正在运动• False：静止状态
            ret = self.dashboard.xyz_move(direction,distance,speed) 
            if ret == 1:
                print("moveJogBase : robot move start ")
            else:
                print("moveJogBase : robot move failed ")
                self.error = True
                self.error_id = self.checkMoveErrorBase(ret)
        else:
            print('moveJogBase: failed because robot is moving (move_flag = True)')


    def moveJogBase_linux_old(self, axis_char_str: str, direction_char_str: str,vel:float) -> None:
        ### hitbot无Jog运动，类似的xyz-move需要指定距离，速度、实际是Inching运动. 
        # ###距离设为尽可能大的的距离，不可则距离半减
        ### TP中有速度指定，但未使用。若今后使用则直接用其值单位mm/s。若不指定则默认-1,在jogBase中改为5%

        ###xyz_move(self,direction,distance,speed) 驱动机械臂沿某一方向运动指定距离，运动轨迹为直线，move_flag 等于false 时调用有效
        #int direction：1 x 轴正方向，2 y 轴正方向，3 z 轴正方向. float distance：移动距离（mm） float speed：移动速度（mm/s）

        if vel >0:
            speed= vel*XYZ_MAX_VEL/100
        else:
            speed=0.05*XYZ_MAX_VEL 

        axis_char_str=str.lower(axis_char_str)        ##0405 安全起见，字母变小写
        if axis_char_str == "x":
            direction = int(1)
        elif axis_char_str == "y" :
            direction = int(2)
        elif axis_char_str == "z" :
            direction = int(3)
        elif axis_char_str == "r" or axis_char_str == "rz" :
            direction = int(6)
        else:
            print('error for axis:  ',axis_char_str)
            sleep(10)
            return
        
        #self.dashboard.get_scara_param()  ####0701 hitbot状态取得
        #current_pos = [self.dashboard.x,self.dashboard.y,self.dashboard.z,self.dashboard.r]
        current_pos = self.getCurrentPos()
        new_pos = current_pos[:]
        print('current_pos:',current_pos)
        print('move falg:',self.dashboard.move_flag)

        juli=400.0   ### 先付给较大的值   距离设为尽可能大的的距离
        if direction_char_str == "-":
            juli = -juli

        self.dashboard.get_scara_param()  ####0701 hitbot状态取得
        print('move falg:',self.dashboard.move_flag)
        if self.dashboard.move_flag == True:   ####True：正在运动• False：静止状态
            print('moveJogBase: failed because robot is moving (move_flag = True)')
            return
        
        while abs(juli) > 0.1:    ###不可则距离半减，最小0.1mm
            new_pos[direction-1] = current_pos[direction-1]  + juli
            ret=self.dashboard.movel_xyz(new_pos[0],new_pos[1],new_pos[2],new_pos[5],speed) 
            if ret ==1:
                print('new_pos:',new_pos)
                print("moveJogBase : robot move start ")
                sleep(1)
                self.dashboard.move_flag=True
                break
            else:
                juli = juli/2
                print('juli:',juli)

        if abs(juli) <= 0.1:
            print('moveJogBase can not move in direction',axis_char_str, direction_char_str)
            return
 
        ###不应该等待，否则无法停止
        # while self.dashboard.move_flag:    ####True：正在运动• False：静止状态
        #     sleep(0.1)
        #     self.dashboard.get_scara_param()  ####0701 hitbot状态取得                
        # print("moveJogBase : robot move end ")
 

    def continueJogBase(self, axis, sign) -> None:
        pass   
        
    def stopJogBase_dobot(self) -> None:
        ret = self.dashboard.MoveJog() #####0422 增加，否则无法停止，会一直运动下去
        #ret = self.dashboard.ResetRobot()  ####0422 不能停止，不知为何用此命令  #####0422 V40无此函数，改用stop
        self.checkApiErrorBase(ret)
        return

    def stopJogBase(self) -> None:    
        self.dashboard.new_stop_move()  ####立即结束当前正在执行的指令
        
    '''old hitbot不支持，应不需要，只保留全局变量，没有全局变量的新增
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

    def setCollisionLevelBase(self, level: int) -> None:
        if not level == -1:
            ret = self.dashboard.SetCollisionLevel(level)
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
        #ret = self.dashboard.SpeedL(int(val))   ##0405 V3-》V4名称改变
        ret = self.dashboard.VelL(int(val))
        self.checkApiErrorBase(ret)
        return

    def setVelJointBase(self, val):
        #ret = self.dashboard.SpeedJ(int(val))    ##0405 V3-》V4名称改变
        ret = self.dashboard.VelJ(int(val))
        self.checkApiErrorBase(ret)
        return
    '''

    def setToolBase(self, tool_no: int) -> None:
        self.tool_no = tool_no
        return

    def setUserBase(self, user_no: int) -> None:
        self.user_no = user_no
        return

    def setAccLineBase(self, val):
        self.acc=int(val)
        self.dashboard.new_set_acc(self.acc,self.acc,self.acc,self.acc)
        return

    def setAccJointBase(self, val):
        self.acc=val
        return

    def setVelLineBase(self, val):
        self.vel=val
        return

    def setVelJointBase(self, val):
        self.vel=val
        return
    
    # def setCollisionLevelBase(self, level: int) -> None:
    #     ###hitbot 设定不可
    #     if not level == -1:
    #         ret = self.dashboard.SetCollisionLevel(level)
    #         self.checkApiErrorBase(ret)
    #     return

    def setWeightBase(self, weight: int) -> None:
        pass

    def getCurrentPosBase_old(self) -> List[float]:
        #ret = self.dashboard.GetPoseTool(self.user_no, self.tool_no)
        ret = self.dashboard.GetPose(self.user_no, self.tool_no)
        self.checkApiErrorBase(ret)
        val = self.transformStr2Pos(ret)
        return val

    def getCurrentJointBase_old(self) -> List[float]:
        ret = self.dashboard.GetAngle()
        val = self.transformStr2Joint(ret)
        self.checkApiErrorBase(ret)
        return val

    def getCurrentPosBase(self) -> List[float]:
        self.dashboard.get_scara_param()  ####0701 hitbot状态取得
        #pos = [self.dashboard.x,self.dashboard.y,self.dashboard.z,self.dashboard.r]
        pos = [self.dashboard.x,self.dashboard.y,self.dashboard.z,0,0,self.dashboard.r]  ####hitbot 4轴亦使用6轴方式，rx，ry为dummy。
        return pos

    def getCurrentJointBase(self) -> List[float]:
        self.dashboard.get_scara_param()  ####0701 hitbot状态取得
        jog = [self.dashboard.angle1,self.dashboard.angle2,self.dashboard.z,self.dashboard.r]
        return jog

# Hitbot Z-Armプログラム
# do not edit this python file
class HitbotInterface_old:
    card_number = 0
    x = 0.0
    y = 0.0
    z = 0.0
    r = 0.0
    angle1 = 0.0
    angle2 = 0.0
    communicate_success = False
    initial_finish = False
    move_flag = False
    efg_distance = 0.0
    efg_type = 0.0
    encoder_x = 0.0
    encoder_y = 0.0
    encoder_z = 0.0
    encoder_r = 0.0
    encoder_angle1 = 0.0
    encoder_angle2 = 0.0

    def __init__(self, card_number):
        self.card_number = card_number
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.r = 0.0
        self.angle1 = 0.0
        self.angle2 = 0.0
        self.efg_dis = 0.0
        self.efg_type = 0.0

    def net_port_initial(self):
        #self.dll=CDLL('./libsmall_scara_interface.so')
        self.dll=CDLL('/home/ncpt-am/robot_controller/lib/robot/libsmall_scara_interface.so')
        return self.dll.net_port_initial()

    def initial(self, generation, z_trail):
        return self.dll.initial(c_int(self.card_number), c_int(generation), c_float(z_trail))

    def get_scara_param(self):
        c_angle1 = c_float(0)
        c_angle2 = c_float(0)
        c_z = c_float(0)
        c_r = c_float(0)
        c_x = c_float(0)
        c_y = c_float(0)
        c_communicate_success = c_bool(False)
        c_initial_finish = c_bool(False)
        c_move_flag = c_bool(False)
        self.dll.get_scara_param(c_int(self.card_number), byref(c_x), byref(c_y), byref(c_z), byref(c_angle1),
                                       byref(c_angle2), byref(c_r), byref(c_communicate_success),
                                       byref(c_initial_finish),
                                       byref(c_move_flag))

        self.x = c_x.value
        self.y = c_y.value
        self.z = c_z.value
        self.angle1 = c_angle1.value
        self.angle2 = c_angle2.value
        self.r = c_r.value
        self.communicate_success = c_communicate_success.value
        self.initial_finish = c_initial_finish.value
        self.move_flag = c_move_flag.value


    def unlock_position(self):
        return self.dll.unlock_position(c_int(self.card_number))

    def is_connect(self):
        return self.dll.is_connected(c_int(self.card_number))

    def get_joint_state(self, joint_num):
        return self.dll.get_joint_state(c_int(self.card_number), c_int(joint_num))

    def set_drag_teach(self, enable):
        return self.dll.set_drag_teach(c_int(self.card_number), c_bool(enable))

    def get_drag_teach(self):
        return self.dll.get_drag_teach(c_int(self.card_number))

    def set_cooperation_fun_state(self, enable):
        return self.dll.set_cooperation_fun_state(c_int(self.card_number), c_bool(enable))

    def get_cooperation_fun_state(self):
        return self.dll.get_cooperation_fun_state(c_int(self.card_number))

    def is_collision(self):
        return self.dll.is_collision(c_int(self.card_number))

    def stop_move(self):
        return self.dll.stop_move(c_int(self.card_number))

    def joint_home(self,joint_num):
        return self.dll.joint_home(c_int(self.card_number),c_int(joint_num))

    def movel_xyz(self, goal_x, goal_y, goal_z, goal_r, speed):
        return self.dll.movel_xyz(c_int(self.card_number), c_float(goal_x), c_float(goal_y), c_float(goal_z), c_float(goal_r),
                                        c_float(speed))

    def movej_xyz(self, goal_x, goal_y, goal_z, goal_r, speed, roughly):
        return self.dll.movej_xyz(c_int(self.card_number), c_float(goal_x), c_float(goal_y), c_float(goal_z), c_float(goal_r),
                                        c_float(speed), c_float(roughly))   

    def movej_angle(self, goal_angle1, goal_angle2, goal_z, goal_r, speed, roughly):
        return self.dll.movej_angle(c_int(self.card_number), c_float(goal_angle1), c_float(goal_angle2), c_float(goal_z),
                                          c_float(goal_r),
                                          c_float(speed), c_float(roughly))

    def change_attitude(self, speed):
        return self.dll.change_attitude(c_int(self.card_number), c_float(speed))

    def wait_stop(self):
        return self.dll.wait_stop(c_int(self.card_number))

    def pause_move(self):
        return self.dll.pause_move(c_int(self.card_number))

    def resume_move(self):
        return self.dll.resume_move(c_int(self.card_number))

    def set_digital_out(self, io_number, io_value):
        return self.dll.set_digital_out(c_int(self.card_number), c_int(io_number), c_int(io_value))    

    def get_digital_out(self, io_number):
        return self.dll.get_digital_out(c_int(self.card_number), c_int(io_number))

    def get_digital_in(self, io_number):
        return self.dll.get_digital_in(c_int(self.card_number), c_int(io_number))

    def set_efg_state(self, efg_type, efg_distance):
        return self.dll.set_efg_state(c_int(self.card_number), c_int(efg_type), c_float(efg_distance))

    def get_efg_state(self):
        c_efg_type = c_int(0)
        c_efg_distance = c_float(0)
        ret = self.dll.get_efg_state(c_int(self.card_number), byref(c_efg_type), byref(c_efg_distance))
        self.efg_type = c_efg_type
        self.efg_distance = c_efg_distance
        return ret

    def movej_xyz_lr(self, goal_x, goal_y, goal_z, goal_r, speed, roughly, lr):
        return self.dll.movej_xyz_lr(c_int(self.card_number), c_float(goal_x), c_float(goal_y), c_float(goal_z), c_float(goal_r),
                                        c_float(speed), c_float(roughly), c_int(lr))

    def new_movej_xyz_lr(self, goal_x, goal_y, goal_z, goal_r, speed, roughly, lr):
        return self.dll.new_movej_xyz_lr(c_int(self.card_number), c_float(goal_x), c_float(goal_y), c_float(goal_z), c_float(goal_r), c_float(speed), c_float(roughly), c_int(lr))

    def new_set_acc(self, j1_max_acc, j2_max_acc, j3_max_acc, j4_max_acc):
        return self.dll.new_set_acc(c_int(self.card_number), c_float(j1_max_acc), c_float(j2_max_acc), c_float(j3_max_acc), c_float(j4_max_acc))

    def j5_motor_zero(self):
        return self.dll.j5_motor_zero(c_int(self.card_number))

    def set_j5_motor_pos(self, deg, speed):
        return self.dll.set_j5_motor_pos(c_int(self.card_number), c_float(deg), c_float(speed))

    def get_j5_parameter(self):
        self.dll.get_j5_parameter.restype = c_float
        return self.dll.get_j5_parameter(c_int(self.card_number))

    def movej_j5(self, deg, speed):
        return self.dll.movej_j5(c_int(self.card_number), c_float(deg), c_float(speed))

    def get_efg_state_dji(self):
        c_efg_type = c_int(0)
        c_efg_distance = c_float(0)
        ret = self.dll.get_efg_state_dji(c_int(self.card_number), byref(c_efg_type), byref(c_efg_distance))
        self.efg_type = c_efg_type
        self.efg_distance = c_efg_distance
        return ret

    def set_efg_state_dji(self, efg_type, efg_distance):
        return self.dll.set_efg_state_dji(c_int(self.card_number), c_int(efg_type), c_float(efg_distance))

    def new_stop_move(self):
        return self.dll.new_stop_move(c_int(self.card_number))

    def get_encoder_coor(self):
        c_x = c_float(0)
        c_y = c_float(0)
        c_z = c_float(0)
        c_angle1 = c_float(0)
        c_angle2 = c_float(0)
        c_r = c_float(0)
        self.dll.get_encoder_coor(c_int(self.card_number), byref(c_x), byref(c_y), byref(c_z), byref(c_angle1), byref(c_angle2), byref(c_r))
        self.encoder_x = c_x.value
        self.encoder_y = c_y.value
        self.encoder_z = c_z.value
        self.encoder_angle1 = c_angle1.value
        self.encoder_angle2 = c_angle2.value
        self.encoder_r = c_r.value

    def new_movej_angle(self, goal_angle1, goal_angle2, goal_z, goal_r, speed, roughly):
        return self.dll.new_movej_angle(c_int(self.card_number), c_float(goal_angle1), c_float(goal_angle2), c_float(goal_z), c_float(goal_r), c_float(speed), c_float(roughly))

    def com485_initial(self, baudRate):
        return self.dll.com485_initial(c_int(self.card_number), c_int(baudRate))


    def com485_send(self, data,len):
        return self.dll.com485_send(c_int(self.card_number), c_char_p(data), c_char(len))

    def com485_recv(self, data):
        return self.dll.com485_recv(c_int(self.card_number), c_char_p(data))

    def get_hard_emergency_stop_state(self):
        return self.dll.get_hard_emergency_stop_state(c_int(self.card_number))

    def check_joint(self, joint_num, state):
        return self.dll.check_joint(c_int(self.card_number), c_int(joint_num), c_bool(state))

    def is_robot_goto_target(self):
        return self.dll.is_robot_goto_target(c_int(self.card_number))

    def set_allow_distance_at_target_position(self, x_distance, y_distance, z_distance, r_distance):
        self.dll.set_allow_distance_at_target_position(c_int(self.card_number), c_float(x_distance), c_float(y_distance), c_float(z_distance), c_float(r_distance))

class HitbotInterface_new:
    card_number = 0
    x = 0.0
    y = 0.0
    z = 0.0
    r = 0.0
    angle1 = 0.0
    angle2 = 0.0
    communicate_success = False
    initial_finish = False
    move_flag = False
    efg_distance = 0.0
    efg_type = 0.0
    encoder_x = 0.0
    encoder_y = 0.0
    encoder_z = 0.0
    encoder_r = 0.0
    encoder_angle1 = 0.0
    encoder_angle2 = 0.0
    erg_distance = 0.0
    erg_angle = 0.0

    def __init__(self, card_number):
        self.card_number = card_number
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.r = 0.0
        self.angle1 = 0.0
        self.angle2 = 0.0
        self.efg_dis = 0.0
        self.efg_type = 0.0

    def net_port_initial(self):
        #self.dll=CDLL('./libsmall_scara_interface.so')
        self.dll=CDLL('/home/ncpt-am/robot_controller/lib/robot/libsmall_scara_interface.so')
        return self.dll.net_port_initial()
    def close_server(self):
        self.dll.close_tcpserver()

    def initial(self, generation, z_trail):
        return self.dll.initial(c_int(self.card_number), c_int(generation), c_float(z_trail))

    def get_scara_param(self):
        c_angle1 = c_float(0)
        c_angle2 = c_float(0)
        c_z = c_float(0)
        c_r = c_float(0)
        c_x = c_float(0)
        c_y = c_float(0)
        c_communicate_success = c_bool(False)
        c_initial_finish = c_bool(False)
        c_move_flag = c_bool(False)
        self.dll.get_scara_param(c_int(self.card_number), byref(c_x), byref(c_y), byref(c_z), byref(c_angle1),
                                       byref(c_angle2), byref(c_r), byref(c_communicate_success),
                                       byref(c_initial_finish),
                                       byref(c_move_flag))

        self.x = c_x.value
        self.y = c_y.value
        self.z = c_z.value
        self.angle1 = c_angle1.value
        self.angle2 = c_angle2.value
        self.r = c_r.value
        self.communicate_success = c_communicate_success.value
        self.initial_finish = c_initial_finish.value
        self.move_flag = c_move_flag.value


    def unlock_position(self):
        return self.dll.unlock_position(c_int(self.card_number))

    def is_connect(self):
        return self.dll.is_connected(c_int(self.card_number))

    def get_joint_state(self, joint_num):
        return self.dll.get_joint_state(c_int(self.card_number), c_int(joint_num))

    def set_drag_teach(self, enable):
        return self.dll.set_drag_teach(c_int(self.card_number), c_bool(enable))

    def get_drag_teach(self):
        return self.dll.get_drag_teach(c_int(self.card_number))

    def set_cooperation_fun_state(self, enable):
        return self.dll.set_cooperation_fun_state(c_int(self.card_number), c_bool(enable))

    def get_cooperation_fun_state(self):
        return self.dll.get_cooperation_fun_state(c_int(self.card_number))
        
    def xyz_move(self, direction, distance, speed):
        return self.dll.xyz_move(c_int(self.card_number), c_int(direction), c_float(distance), c_float(speed))
        
    def judge_in_range(self, x, y, z, ratation):
        return self.dll.judge_in_range(c_int(self.card_number), c_float(x), c_float(y), c_float(z), c_float(ratation))



    def is_collision(self):
        return self.dll.is_collision(c_int(self.card_number))

    def stop_move(self):
        return self.dll.stop_move(c_int(self.card_number))

    def joint_home(self,joint_num):
        return self.dll.joint_home(c_int(self.card_number),c_int(joint_num))

    def movel_xyz(self, goal_x, goal_y, goal_z, goal_r, speed):
        return self.dll.movel_xyz(c_int(self.card_number), c_float(goal_x), c_float(goal_y), c_float(goal_z), c_float(goal_r),
                                        c_float(speed))

    def movej_xyz(self, goal_x, goal_y, goal_z, goal_r, speed, roughly):
        return self.dll.movej_xyz(c_int(self.card_number), c_float(goal_x), c_float(goal_y), c_float(goal_z), c_float(goal_r),
                                        c_float(speed), c_float(roughly))   

    def movej_angle(self, goal_angle1, goal_angle2, goal_z, goal_r, speed, roughly):
        return self.dll.movej_angle(c_int(self.card_number), c_float(goal_angle1), c_float(goal_angle2), c_float(goal_z),
                                          c_float(goal_r),
                                          c_float(speed), c_float(roughly))

    def change_attitude(self, speed):
        return self.dll.change_attitude(c_int(self.card_number), c_float(speed))

    def wait_stop(self):
        return self.dll.wait_stop(c_int(self.card_number))

    def pause_move(self):
        return self.dll.pause_move(c_int(self.card_number))

    def resume_move(self):
        return self.dll.resume_move(c_int(self.card_number))

    def set_digital_out(self, io_number, io_value):
        return self.dll.set_digital_out(c_int(self.card_number), c_int(io_number), c_int(io_value))    

    def get_digital_out(self, io_number):
        return self.dll.get_digital_out(c_int(self.card_number), c_int(io_number))

    def get_digital_in(self, io_number):
        return self.dll.get_digital_in(c_int(self.card_number), c_int(io_number))

    def set_efg_state(self, efg_type, efg_distance):
        return self.dll.set_efg_state(c_int(self.card_number), c_int(efg_type), c_float(efg_distance))

    def get_efg_state(self):
        c_efg_type = c_int(0)
        c_efg_distance = c_float(0)
        ret = self.dll.get_efg_state(c_int(self.card_number), byref(c_efg_type), byref(c_efg_distance))
        self.efg_type = c_efg_type
        self.efg_distance = c_efg_distance
        return ret

    def movej_xyz_lr(self, goal_x, goal_y, goal_z, goal_r, speed, roughly, lr):
        return self.dll.movej_xyz_lr(c_int(self.card_number), c_float(goal_x), c_float(goal_y), c_float(goal_z), c_float(goal_r),
                                        c_float(speed), c_float(roughly), c_int(lr))

    def new_movej_xyz_lr(self, goal_x, goal_y, goal_z, goal_r, speed, roughly, lr):
        return self.dll.new_movej_xyz_lr(c_int(self.card_number), c_float(goal_x), c_float(goal_y), c_float(goal_z), c_float(goal_r), c_float(speed), c_float(roughly), c_int(lr))

    def new_set_acc(self, j1_max_acc, j2_max_acc, j3_max_acc, j4_max_acc):
        return self.dll.new_set_acc(c_int(self.card_number), c_float(j1_max_acc), c_float(j2_max_acc), c_float(j3_max_acc), c_float(j4_max_acc))

    def j5_motor_zero(self):
        return self.dll.j5_motor_zero(c_int(self.card_number))

    def set_j5_motor_pos(self, deg, speed):
        return self.dll.set_j5_motor_pos(c_int(self.card_number), c_float(deg), c_float(speed))

    def get_j5_parameter(self):
        self.dll.get_j5_parameter.restype = c_float
        return self.dll.get_j5_parameter(c_int(self.card_number))

    def movej_j5(self, deg, speed):
        return self.dll.movej_j5(c_int(self.card_number), c_float(deg), c_float(speed))

    def get_efg_state_dji(self):
        c_efg_type = c_int(0)
        c_efg_distance = c_float(0)
        ret = self.dll.get_efg_state_dji(c_int(self.card_number), byref(c_efg_type), byref(c_efg_distance))
        self.efg_type = c_efg_type
        self.efg_distance = c_efg_distance
        return ret

    def set_efg_state_dji(self, efg_type, efg_distance):
        return self.dll.set_efg_state_dji(c_int(self.card_number), c_int(efg_type), c_float(efg_distance))

    def new_stop_move(self):
        return self.dll.new_stop_move(c_int(self.card_number))

    def get_encoder_coor(self):
        c_x = c_float(0)
        c_y = c_float(0)
        c_z = c_float(0)
        c_angle1 = c_float(0)
        c_angle2 = c_float(0)
        c_r = c_float(0)
        self.dll.get_encoder_coor(c_int(self.card_number), byref(c_x), byref(c_y), byref(c_z), byref(c_angle1), byref(c_angle2), byref(c_r))
        self.encoder_x = c_x.value
        self.encoder_y = c_y.value
        self.encoder_z = c_z.value
        self.encoder_angle1 = c_angle1.value
        self.encoder_angle2 = c_angle2.value
        self.encoder_r = c_r.value

    def new_movej_angle(self, goal_angle1, goal_angle2, goal_z, goal_r, speed, roughly):
        return self.dll.new_movej_angle(c_int(self.card_number), c_float(goal_angle1), c_float(goal_angle2), c_float(goal_z), c_float(goal_r), c_float(speed), c_float(roughly))

    def com485_initial(self, baudRate):
        return self.dll.com485_initial(c_int(self.card_number), c_int(baudRate))


    def com485_send(self, data,len):
        return self.dll.com485_send(c_int(self.card_number), c_char_p(data), c_char(len))

    def com485_recv(self, data):
        return self.dll.com485_recv(c_int(self.card_number), c_char_p(data))

    def get_hard_emergency_stop_state(self):
        return self.dll.get_hard_emergency_stop_state(c_int(self.card_number))

    def check_joint(self, joint_num, state):
        return self.dll.check_joint(c_int(self.card_number), c_int(joint_num), c_bool(state))

    def is_robot_goto_target(self):
        return self.dll.is_robot_goto_target(c_int(self.card_number))

    def set_allow_distance_at_target_position(self, x_distance, y_distance, z_distance, r_distance):
        self.dll.set_allow_distance_at_target_position(c_int(self.card_number), c_float(x_distance), c_float(y_distance), c_float(z_distance), c_float(r_distance))
    #485旋转夹爪功能
    #手动初始化
    def com485_init(self):
        return self.dll.com485_init(c_int(self.card_number))
    #设置旋转速度
    def com485_set_rotation_speed(self, speed):
        return self.dll.com485_set_rotation_speed(c_int(self.card_number), c_float(speed))
    #设置旋转速度
    def com485_set_clamping_speed(self, speed):
        return self.dll.com485_set_clamping_speed(c_int(self.card_number), c_float(speed))
    #设置夹持距离
    def com485_set_clamping_distance(self, distance):
        return self.dll.com485_set_clamping_distance(c_int(self.card_number), c_float(distance))
    #获取夹持距离
    def com485_get_clamping_distance(self):
        c_erg_distance = c_float(0)
        ret = self.dll.com485_get_clamping_distance(c_int(self.card_number), byref(c_erg_distance))
        self.erg_distance = c_erg_distance
        return ret
    #设置绝对旋转角度
    def com485_set_rotation_angle(self, angle):
        return self.dll.com485_set_rotation_angle(c_int(self.card_number), c_float(angle))
    #设置相对旋转角度
    def com485_set_relative_rotation_angle(self, angle):
        return self.dll.com485_set_relative_rotation_angle(c_int(self.card_number), c_float(angle))
    #获取旋转角度
    def com485_get_rotation_angle(self):
        c_erg_angle = c_float(0)
        ret = self.dll.com485_get_rotation_angle(c_int(self.card_number), byref(c_erg_angle))
        self.erg_angle = c_erg_angle
        return ret
    #获取夹持状态
    def com485_get_clamping_state(self):
        return self.dll.com485_get_clamping_state(c_int(self.card_number))
    #获取旋转状态
    def com485_get_rotation_state(self):
        return self.dll.com485_get_rotation_state(c_int(self.card_number))
    #设置夹持电流
    def com485_set_clamping_current(self, current):
        return self.dll.com485_set_clamping_current(c_int(self.card_number), c_float(current))
    #设置旋转电流
    def com485_set_rotation_current(self, current):
        return self.dll.com485_set_rotation_current(c_int(self.card_number), c_float(current))


if __name__ == '__main__':
    #node = RobotApi_mg400()
    #node = RobotApi("192.168.250.101","29999","","")   
    #node = RobotApi("192.168.250.101","40000","","",arm_id=101)   
    node = RobotApi("192.168.250.111","40000","","","hitbot_z_arm2442")   
    #pdb.set_trace()    ##b3
    #node.setServoOn() 
    #pdb.set_trace()    ##b4

    vel=25
    acc=50
    #node.getRobotStatus()
    new_pos=[0,0,0,0,0,0]
    #node.dashboard.joint_home(1)
    #node.dashboard.joint_home(2)

    node.error_id=node.getErrorBase()
    if node.error_id != 0:
        print(node.error_id)
        node.resetError()
        node.setServoOn()
    
    #node.dashboard.set_drag_teach(True)   ##拖动模式    ### def set_drag_teach(self, enable)
    #input('enter key to end drag')
    #node.dashboard.set_drag_teach(False)   ##拖动模式    ### def set_drag_teach(self, enable)
    #pdb.set_trace()    ##b5
    
    axiss='r'
    direc='-'     
    for jogNum in range(2) :   
        node.error_id=node.getErrorBase()
        if node.error_id != 0:
            print(node.error_id)
            node.resetError()
            node.setServoOn()
        ##jog    
        #print('jog: x+ start')
        node.dashboard.get_scara_param()
        while node.dashboard.move_flag == True:
            sleep(0.05)
            node.dashboard.get_scara_param()
            
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        #axis=input("axis_str  ")
        #direc=input(' direction_str')
        ret=node.moveJog(axiss,direc,vel)
        sleep(2)
        node.stopJog()


        ''' 
        ret=node.moveJog("x","+",vel)
        input ('press enter to stop jog')
        node.stopJog()
        
        print('jog: x+ end')
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        #########   X-
        sleep(1)
        print('jog: x- start')
        node.dashboard.get_scara_param()
        while node.dashboard.move_flag == True:
            sleep(0.05)
            node.dashboard.get_scara_param()
            
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        ret=node.moveJog("x","-",vel)
        input ('input any to stop jog')
        node.stopJog()
        
        print('jog: x- end')
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        sleep(1)
        print('jog: y- start')
        node.dashboard.get_scara_param()
        while node.dashboard.move_flag == True:
            sleep(0.05)
            node.dashboard.get_scara_param()
            
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        ret=node.moveJog("y","-",vel)
        input ('input any to stop jog')
        node.stopJog()
        
        print('jog: y- end')
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        sleep(1)
        print('jog: y+ start')
        node.dashboard.get_scara_param()
        while node.dashboard.move_flag == True:
            sleep(0.05)
            node.dashboard.get_scara_param()
            
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        ret=node.moveJog("y","+",vel)
        input ('input any to stop jog')
        node.stopJog()
        
        print('jog: y+ end')
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        sleep(1)
        print('jog: z+ start')
        node.dashboard.get_scara_param()
        while node.dashboard.move_flag == True:
            sleep(0.05)
            node.dashboard.get_scara_param()
            
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        ret=node.moveJog("Z","+",vel)
        input ('input any to stop jog')
        node.stopJog()
        
        print('jog: z+ end')
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        sleep(1)
        print('jog: z- start')
        node.dashboard.get_scara_param()
        while node.dashboard.move_flag == True:
            sleep(0.05)
            node.dashboard.get_scara_param()
            
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        input ('input any to stop jog')
        node.stopJog()
        
        print('jog: z- end')
        node.current_pos = node.getCurrentPos()  
        print('current_pos',node.current_pos)
        
        sleep(1)             
        '''

    '''
    ## 1   moveAbsolutePtp
    for kk in range(20):  
        kk+=1
        node.dashboard.get_scara_param()
        while node.dashboard.move_flag == True:
            sleep(0.05)
            node.dashboard.get_scara_param()
                
        node.current_pos = node.getCurrentPos()  ### hitbot rz 为第6个参数，getCurrentPos中加了两个dummy参数
        print('current:',node.current_pos,perf_counter())  ###cra
        new_pos = node.current_pos[:]  ##直接赋值new_pos = node.current_pos二者为同一数组，分片操作new_pos = node.current_pos[:]为不同数组
        print(id(new_pos),id(node.current_pos))   ###如果两个id值一样，则表明列表是使用的同一地址同一份数据
        
        new_pos[0]= new_pos[0]+30
        # if not node.dashboard.judge_in_range_xyzr(new_pos[0],new_pos[1],new_pos[2],new_pos[5]):  
        #     new_pos[0]= new_pos[0]-200
        #     while not node.dashboard.judge_in_range_xyzr(new_pos[0],new_pos[1],new_pos[2],new_pos[5]):  
        #         new_pos[0]= new_pos[0]+10
            
        print('new1:',new_pos)
            
        node.arrived=False  
        
        print('move start:',node.current_pos,perf_counter())
        node.moveAbsolutePtp(new_pos[0],new_pos[1],new_pos[2],new_pos[3],new_pos[4],new_pos[5],vel,acc)  ###cra
            ## def moveAbsolutePtp(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, vel: int = 100, acc: int = 100, dec: int = 100) -> None:     ###0422 与main中一致，Rx ->rx
        print('move comment end:',perf_counter())

        while node.arrived==False:
            node.getRobotStatus()
            #node.current_pos = node.getCurrentPos()
            #print('moveFlag,current,time:',node.moving,node.current_pos,perf_counter())
            node.waitArrive( new_pos, width=0.01)
            sleep(0.005)
        print('move arrive:',node.current_pos,perf_counter())

        node.dashboard.get_scara_param()
        while node.dashboard.move_flag==True:    
            node.checkMovingBase()
            #print('moveFlag,node.moving,current,time:',node.dashboard.move_flag,node.moving,node.current_pos,perf_counter())
            sleep(0.001)
            node.dashboard.get_scara_param()
        print('move end:',perf_counter())
            
        node.error_id=node.getErrorBase()
        if node.error_id != 0:
            print(node.error_id)
            node.resetError()
            node.setServoOn()

        ## 2   moveAbsoluteLine
        while node.dashboard.move_flag != False:
            sleep(0.05)
            node.dashboard.get_scara_param()

        node.current_pos = node.getCurrentPos()
        print('current:',node.current_pos,perf_counter())
        new_pos = node.current_pos[:]
        new_pos[1]= new_pos[1]-30
        # if not node.dashboard.judge_in_range_xyzr(new_pos[0],new_pos[1],new_pos[2],new_pos[5]):  
        #     new_pos[1]= new_pos[1]+200
        #     while not node.dashboard.judge_in_range_xyzr(new_pos[0],new_pos[1],new_pos[2],new_pos[5]):  
        #         new_pos[1]= new_pos[1]-10
        print('new2:',new_pos)
        
        node.arrived=False

        print('move start:',node.current_pos,perf_counter())
        node.moveAbsoluteLine(new_pos[0],new_pos[1],new_pos[2],new_pos[3],new_pos[4],new_pos[5],vel,acc)  ###　cra
        print('move comment end:',perf_counter())

        while node.arrived==False:
            sleep(0.001)
            node.waitArrive( new_pos, width=0.01)
        print('move arrive:',node.current_pos,perf_counter())
            
        node.dashboard.get_scara_param()
        while node.dashboard.move_flag==True:    
            sleep(0.001)
            node.dashboard.get_scara_param()
        print('move end:',perf_counter())
    
        node.error_id=node.getErrorBase()
        if node.error_id != 0:
            print(node.error_id)
            node.resetError()
            node.setServoOn()

        ## 3   moveRelative
        while node.dashboard.move_flag == True:
            sleep(0.05)
            node.dashboard.get_scara_param()

        node.current_pos = node.getCurrentPos()
        print('current:',node.current_pos,perf_counter())
        new_pos = node.current_pos[:]
        diff=[0,0,-15,0,0,0]
        for ii in range(6):
            new_pos[ii]= new_pos[ii]+diff[ii] 
        # print(node.dashboard.judge_in_range_xyzr(new_pos[0],new_pos[1],new_pos[2],new_pos[5]))
        # while not node.dashboard.judge_in_range_xyzr(new_pos[0],new_pos[1],new_pos[2],new_pos[5]):  
        #     new_pos[2]= new_pos[2]-10
        #     #new_pos[5]= new_pos[5]-10
            
        print('new3:',new_pos)
        node.arrived=False

        print('move start:',node.current_pos,perf_counter())
        node.moveRelative(diff[0],diff[1],diff[2],diff[3],diff[4],diff[5],vel,acc)    ###　cra
        print('move comment end:',perf_counter())

        while node.arrived==False:
            sleep(0.001)
            node.waitArrive( new_pos, width=0.01)
        print('move arrive:',node.current_pos,perf_counter())
            
        node.dashboard.get_scara_param()
        while node.dashboard.move_flag==True:    
            sleep(0.001)
            node.dashboard.get_scara_param()
        print('move end:',perf_counter())
        
        node.error_id=node.getErrorBase()
        if node.error_id != 0:
            print(node.error_id)
            node.resetError()
            node.setServoOn()

    '''  


