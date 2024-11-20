# -*- coding : UTF-8 -*-

# from socket import *        #通信ソケット
import select  # 复数IO入力，複数イベント受け付け
from time import sleep, perf_counter, time  # 計測時間、UNIX時間を基準
from multiprocessing import Process, Value, Array  # 子プロセス関係。ValueとArray：共有メモリ
# import multiprocessing as mp    #子プロセス関係。ValueとArray：共有メモリ
from typing import Tuple, List, Union, Optional  # 对函数参数加注解

import numpy as np  # 数字计算Lib

# official api
import socket  # 通信ソケット
from threading import Timer  # 複数タスク、マルチスレッド処理、Timer：タイマー
from tkinter import Text, END  # GUIキット、Text：文字定義、カスタマイズ。End：ディフォルト値の入力（表示）
import datetime  # 日時、標準時間

# Only Fr-Robot official api
# from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove, MyType
# Only Fr-Robot official api
import frrpc
# import Robot as frrpc
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
RZ = 5  # moveRelativeBase中使用
CHECK_MOVING_DIFF = 0.1  # 未使用，yamaha_scara判断是否移动时使用，IO不能判断所以用位置差分判断

GRAVITY = 9800  ##########
XYZ_MAX_JERK = 30000  # 未使用
R_MAX_JERK = 30000  # 未使用
XYZ_MAX_ACC = 3000  # 未使用 ，yamaha_scara使用
R_MAX_ACC = 6000  # 未使用
XYZ_MAX_VEL = 250  # 未使用 ，yamaha_scara使用
R_MAX_VEL = 600  # 未使用

# Port Feedback
MyType = np.dtype([
    ('head_Fr', np.uint16,),
    ('CNT', np.uint8,),
    ('LEN', np.uint16,),
    ('program_state', np.uint8,),
    ('error_code', np.uint8,),
    ('robot_mode', np.uint8,),
    ('jt_cur_pos', (np.float64), (6,)),
    ('tl_cur_pos', (np.float64), (6,)),
    ('toolNum', np.int32,),
    # ('jt_cur_tor',    6(np.float64),),
    ('jt_cur_tor', (np.float64), (6,)),  # 156
    # ('program_name',    (np.unicode),(20)), ##NG
    # ('program_name',    (np.string_),(20)),   ##ok,长度20，  写法 (20,)不可
    ('program_name', (np.bytes_), (20)),
    ## #`np.string_` was removed in the NumPy 2.0 release. Use `np.bytes_` instead.
    # ('program_name',    (np.str),(20,)),   ##NG
    # ('program_name',    'U20',),   ## OK但长度不对20
    ('prog_total_line', np.uint8,),  # 177
    ('prog_cur_line', np.uint8,),
    ('cl_dgt_output_h', np.uint8,),
    ('cl_dgt_output_l', np.uint8,),
    ('tl_dgt_output_l', np.uint8,),
    ('cl_dgt_input_h', np.uint8,),
    ('cl_dgt_input_l', np.uint8,),
    ('tl_dgt_input_l', np.uint8,),  # 184
    ('FT_data', (np.float64), (6,)),  # 232
    ('FT_ActStatus', np.uint8,),
    ('EmergencyStop', np.uint8,),
    ('robot_motion_done', np.int32,),
    ('gripper_motion_done', np.uint8,),
    ('summ', np.uint16,),  # 241
    ('dummy', (np.uint8), (15,))  # 奇数不可，要凑成偶数。凑够256字节
])

# Port Feedback

'''  np之说明
import numpy as np
dtypes = [
    np.int8,        # 符号あり  8bit 整数 
    np.int16,       # 符号あり 16bit 整数
    np.int32,       # 符号あり 32bit 整数
    np.int64,       # 符号あり 64bit 整数
    np.uint8,       # 符号なし  8bit 整数
    np.uint16,      # 符号なし 16bit 整数
    np.uint32,      # 符号なし 32bit 整数
    np.uint64,      # 符号なし 64bit 整数
    np.float16,     # 半精度 浮動小数点数
    np.float32,     # 単精度 浮動小数点数
    np.float64,     # 倍精度 浮動小数点数
    np.float128,    # 四倍精度 浮動小数点数 
    np.complex64,   # 複素数 (実数・虚数が  float32)
    np.complex128,  # 複素数 (実数・虚数が  float64)
    np.complex256,  # 複素数 (実数・虚数が float128)
    np.bool,        # 真偽値
    np.unicode,     # Unicode文字列
    np.object       # Pythonオブジェクト（へのポインタ）
]
'''


class RobotApi():
    def __init__(self, dst_ip_address: str, dst_port: str, dev_port: str, baurate: int):
        # print(dst_ip_address, dst_port, dev_port, baurate)
        ##############################################################
        # ロボット状態通知用変数定義(数値)
        ##############################################################    
        # self.current_pos     :List[float] = [0.0] * 4
        # self.pre_current_pos :List[float] = [0.0] * 4
        self.current_pos: List[float] = [0.0] * 6  ##################0105
        self.pre_current_pos: List[float] = [0.0] * 6  ###############0105
        # self.error_id        :int = 0
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
        self.robot_mode: int = Value('i', 0)  # 内存共享， int型，值0
        self.robot_mode = 0  # 10  #0
        self.error_id: int = Value('i', 0)  # 内存共享， int型，值0
        self.error_id = 0  # 10  # 0
        # 電源確認用フラグ
        self.opening = False
        # self変数
        self.dst_ip_address = dst_ip_address
        self.dst_port = dst_port

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
    '''
    def openRobot_Dobot(self, dst_ip_address: str, dst_port: str) -> None:
        """ ロボット通信を開始
        """
        # ロボットサーバに接続
        print("Start to connet robot.")
        self.connectRobotBase()
        self.resetError()
        self.setTool(tool_no=0)
        self.setUser(user_no=0)
        self.mySleepBase(0.5)
        self.startMultiFeedbackBase()
        print("Finished to connet robot.")
        print("Connected to: " + dst_ip_address)
        
        # # 初期パラメータセット
        # self.setInitialRobotParamBase()

    '''

    def openRobot(self, dst_ip_address: str, dst_port: str) -> None:
        """ ロボット通信を開始
        """
        self.dst_ip_address = dst_ip_address
        # ロボットサーバに接続
        print("Start to connet robot.")
        # self.connectRobotBase()
        self.robot = frrpc.RPC(dst_ip_address)
        self.readyRobot()  ##########1130 执行结束关闭后，在执行程序时需要开使能
        self.FairRobotApi = FairRobotApi(dst_ip_address, dst_port)
        self.feed = FairRobotApi(dst_ip_address, dst_port)
        self.resetError()
        self.tool_no = -1
        # self.setTool(tool_no=0)
        self.setUser(user_no=0)
        # self.user_no=0
        self.mySleepBase(0.5)

        self.startMultiFeedbackBase()  #####1114  Linux可以，但Window不可，要在 if name = '__main__' 中起用 multiprocessing 才可以
        print("Finished to connet robot.")
        print("Connected to: " + dst_ip_address)

        # # 初期パラメータセット
        # self.setInitialRobotParamBase()  ##必须，否则main调用时无值  ,######1225 readyRobot中调用，此处不要

    def closeRobot(self) -> None:
        """ ロボット通信を解除
        """
        self.setServoOff()
        self.mySleepBase(0.5)
        self.feed.close()

    # 2023/1/13追加　ready用
    def readyRobot(self):
        # print('readyRobot')
        self.setServoOn()
        self.setInitialRobotParamBase()
        self.Tool_coord = [[0.0] * 6 for ii in range(10)]
        self.tool_no = -1  ##防止以前留下错误坐标系状态造成错误，一定执行一次tool设为0
        self.setTool(tool_no=0)
        # self.Tool_index = 0

    def saveTool_coord(self, x, y, z, rx, ry, rz, tool_no):
        # print('saveTool_coord',x,y,z,rx,ry,rz,tool_no)
        if tool_no < 10:
            self.Tool_coord[tool_no][:] = [x, y, z, rx, ry, rz]
            print('saveTool_coord', tool_no, self.Tool_coord[tool_no][:])
        else:
            print('saveTool_coord: Tool_index Over', tool_no)

    def getRobotStatus(self) -> None:
        """ ロボット状態を取得
        """
        ##############################################################
        # エラー状態確認
        ##############################################################
        # with open('log_Multi_fr3api.txt', 'a') as fm:        
        #     # .value不能使用。出错
        #     #print('befor getRobotStatus:robot_mode, error_id=', self.robot_mode.value,self.error_id.value, time(),file=fm)
        #     print('befor getRobotStatus:robot_mode, error_id=', self.robot_mode,self.error_id, time(),file=fm)
        # fm.close()
        # with open('log_fr3api.txt', 'a') as f2:
        #     print('     getRobotStatus checkErrorBase start',time(),file=f2)
        # f2.close()
        # print("api--getRobotStatus -- start",perf_counter())

        self.checkErrorBase()
        # print("api--getRobotStatus -- checkErrorBase--end",perf_counter())
        ##############################################################
        # 現在地の直交座標取得
        ##############################################################
        # with open('log_fr3api.txt', 'a') as f2:
        #     print('     getRobotStatus getCurrentPos start',time(),file=f2)
        # f2.close()
        self.current_pos = self.getCurrentPos()
        # print("api--getRobotStatus -- getCurrentPos--end",perf_counter())
        ##############################################################
        # Moving確認 
        ##############################################################
        # with open('log_fr3api.txt', 'a') as f2:
        #     print('     getRobotStatus checkMovingBase start',time(),file=f2)
        # f2.close()
        self.checkMovingBase()
        # print("api--getRobotStatus -- checkMovingBase--end",perf_counter())
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
        # print("api--getRobotStatus ---end",perf_counter())
        # with open('log_fr3api.txt', 'a') as f2:
        #     print('     getRobotStatus  end',time(),file=f2)
        # f2.close()
        # with open('log_Multi_fr3api.txt', 'a') as fm:        
        #     print('after getRobotStatus:robot_mode, error_id=', self.robot_mode,self.error_id, time(),file=fm)
        # fm.close()

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

    def getCurrentPos(self) -> list[float]:
        """ 現在地の直交座標取得
        """
        val = self.getCurrentPosBase()
        return val

    def getCurrentJoint(self) -> None:
        """ 現在地のジョイント座標取得
        """
        val = self.getCurrentJointBase()
        return val

    '''
    def getPos2Joint_Dobot(self, x: float, y: float, z: float, r: float) -> None:
        """ 直交座標をジョイント座標へ変換
        """
        ret = self.move.InverseSolution(x,y,z,r,0,0,0,0)
        self.checkApiErrorBase()
        val = self.transformStr2Joint(ret)
        return val

    '''

    def getPos2Joint(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, type_coor: int = 0,
                     jRef: int = -1) -> list[float]:
        """ 直交座標をジョイント座標へ変換
        #type_coor:0-绝对位姿(基坐标系)，1-相对位姿（基坐标系），2-相对位姿（工具坐标系）
        #jRef:关节配置，[-1]-参考当前关节位置求解，[0~7]-依据关节配置求解
        """
        joint_pos = self.getPos2JointBase(x, y, z, rx, ry, rz, type_coor, jRef)
        # 返回joint_pos=[j1,j2,j3,j4,j5,j6]
        return joint_pos

    def getPos2JointBase(self, x, y, z, rx, ry, rz, type_coor, jRef) -> list[float]:
        """ 直交座標をジョイント座標へ変換
        """
        # GetInverseKin(type,desc_pos,config)
        desc_pos = [x, y, z, rx, ry, rz]
        # type:0-绝对位姿(基坐标系)，1-相对位姿（基坐标系），2-相对位姿（工具坐标系）
        # config:关节配置，[-1]-参考当前关节位置求解，[0~7]-依据关节配置求解

        ret_val = self.robot.GetInverseKin(type_coor, desc_pos, jRef)
        # 成功：[0,joint_pos],joint_pos=[j1,j2,j3,j4,j5,j6], 失败：[errcode,]
        ret = ret_val[0]
        if ret == 0:
            val = ret_val[1:7]  ###输出为0-6，7个数，ret_val【1】只是x
        else:
            print('坐标变换错误')
            self.checkApiErrorBase(ret)  # 检查。非0则错误
            return ret
            # val = self.transformStr2Joint(ret) #不需要，ret为int，无{}，无需去除前后等
        return val

    '''
    def getJoint2Pos_Dobot(self, j1: float, j2: float, j3: float, j4: float) -> None:
        """ ジョイント座標を直交座標へ変換
        """
        ret = self.move.PositiveSolution(j1,j2,j3,j4,0,0,0,0)
        self.checkApiErrorBase()
        val = self.transformStr2Pos(ret)
        return val

    '''

    def getJoint2Pos(self, j1: float, j2: float, j3: float, j4: float, j5: float, j6: float) -> list[float]:
        """ ジョイント座標を直交座標へ変換
        """
        desc_pos = self.getJoint2PosBase(j1, j2, j3, j4, j5, j6)
        # 返回 desc_pos=[x,y,z,rx,ry,rz]:工具位姿，单位[mm][°]
        return desc_pos

    def getJoint2PosBase(self, j1: float, j2: float, j3: float, j4: float, j5: float, j6: float) -> list[float]:
        """ ジョイント座標を直交座標へ変換
        """
        joint_pos = [j1, j2, j3, j4, j5, j6]
        ret_val = self.robot.GetForwardKin(joint_pos)
        # 成功：[0,desc_pos],desc_pos=[x,y,z,rx,ry,rz]:工具位姿，单位[mm][°],  失败：[errcode,]
        ret = ret_val[0]
        if ret == 0:
            val = ret_val[1:7]  ###输出为0-6，7个数，ret_val【1】只是x
        else:
            print('坐标变换错误')
            self.checkApiErrorBase(ret)  # 检查。非0则错误
            return ret
            # val = self.transformStr2Pos(ret)   #不需要，ret为int，无{}，无需去除前后等
        return val

    '''
    def waitArrive_Dobot(self, target_pos: List[float], width: float) -> None:
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
        if ((diff_pos[X] <= width) and
            (diff_pos[Y] <= width) and
            (diff_pos[Z] <= width) and
            (diff_pos[R] <= width)):
            self.arrived = True
        else: 
            self.arrived = False

    '''

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
        # diff_pos = [abs(x - y) for (x, y) in zip(target_pos, self.current_pos)]
        #########0422 Rx,Ry,Rz检出位置180与-180跳跃问题解决
        target_pos_linshi = target_pos
        current_pos_linshi = self.current_pos

        for ii in range(3, 6):
            if current_pos_linshi[ii] == -180:
                current_pos_linshi[ii] = 180
            if target_pos_linshi[ii] == -180:
                target_pos_linshi[ii] = 180

        diff_pos = [abs(x - y) for (x, y) in zip(target_pos_linshi, current_pos_linshi)]
        # print("diff_pos",diff_pos)
        # width=2
        # width=0.2
        # 差分が設定値以内なら
        if ((diff_pos[X] <= width) and
                (diff_pos[Y] <= width) and
                (diff_pos[Z] <= width) and
                (diff_pos[RX] <= width) and
                (diff_pos[RY] <= width) and
                (diff_pos[RZ] <= width)):
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

    def moveAbsolutePtp(self, x: float, y: float, z: float, rx: float = 0.0, ry: float = 0.0, rz: float = 0.0,
                        vel: float = -1.0, acc: float = -1.0, dec: float = -1.0, tool_no: int = -1,
                        user_no: int = -1) -> None:
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
        if vel <= 0:
            vel = self.vel_default
        if acc <= 0:
            acc = self.acc_default
        if tool_no < 0:
            tool_no = self.tool_no
        if user_no < 0:
            user_no = self.user_no

        self.moveAbsolutePtpBase(x, y, z, rx, ry, rz, tool_no, user_no, vel)

    def moveAbsoluteLine(self, x: float, y: float, z: float, rx: float = 0.0, ry: float = 0.0, rz: float = 0.0,
                         vel: float = -1.0, acc: float = -1.0, dec: float = -1.0, tool_no: int = -1,
                         user_no: int = -1) -> None:
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
        # self.moveAbsoluteLineBase (x, y, z, r, vel, acc, dec)
        if vel <= 0:
            vel = self.vel_default
        if acc <= 0:
            acc = self.acc_default
        if tool_no < 0:
            tool_no = self.tool_no
        if user_no < 0:
            user_no = self.user_no
        self.moveAbsoluteLineBase(x, y, z, rx, ry, rz, tool_no, user_no, vel)
        # print('moveAbsoluteLine end',perf_counter())

    def moveRelative(self, x: float, y: float, z: float, rx: float = 0.0, ry: float = 0.0, rz: float = 0.0,
                     vel: float = -1.0, acc: float = -1.0, dec: float = -1.0, tool_no: int = -1,
                     user_no: int = -1) -> None:
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
        if vel <= 0:
            vel = self.vel_default
        if acc <= 0:
            acc = self.acc_default
        if tool_no < 0:
            tool_no = self.tool_no
        if user_no < 0:
            user_no = self.user_no
        # print('tool_no =',tool_no)
        self.moveRelativeBase(x, y, z, rx, ry, rz, tool_no, user_no, vel, acc)

    def moveOrigin(self) -> None:
        """ 原点復帰
        """
        # ret=self.moveOriginBase()
        self.moveOriginBase()
        # return ret

    def setServoOn(self):
        """ サーボ電源ON
        """
        self.servo = True
        self.setServoOnBase()

    def setServoOff(self):
        """ サーボ電源OFF
        """
        self.servo = False
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

    def moveJog(self, axis_char_str: str, direcCharOrCoordType, vel: float = -1.0, acc: float = -1.0,
                max_dis: float = 30.000) -> None:
        """ 手動移動：ジョグ
        Parameters
        ----------
        axis_char_str : str
            軸(ex. "x")    Or 軸と方向　x+
        direction_char_str : str
            回転方向(ex. "+")  or　座標系指定 *dynParams:
        ref：0-关节点动,2-基坐标系点动,4-工具坐标系点动,8-工件坐标系点动；但无法指定具体的坐标系编号

         coord_type: 1: User coordinate 2: tool coordinate (default value is 1)
        """
        max_dis = 3000.0
        if vel <= 0:
            vel = self.vel_default
        if acc <= 0:
            acc = self.acc_default
        # 入力パターン1
        axis_dic1 = {"x": 1, "y": 2, "z": 3, "rx": 4, "ry": 5, "rz": 6,
                     "X": 1, "Y": 2, "Z": 3, "RX": 4, "RY": 5, "RZ": 6}
        axis_dic2 = {"J1": 1, "J2": 2, "J3": 3, "J4": 4, "J5": 5, "J6": 6,
                     "j1": 1, "j2": 2, "j3": 3, "j4": 4, "j5": 5, "j6": 6, }
        dir_dic = {"+": 1, "-": 0}
        # 入力パターン2
        axis_dic3 = {"x+": 1, "y+": 2, "z+": 3, "rx+": 4, "ry+": 5, "rz+": 6,
                     "X+": 1, "Y+": 2, "Z+": 3, "RX+": 4, "RY+": 5, "RZ+": 6}
        axis_dic4 = {"x-": 1, "y-": 2, "z-": 3, "rx-": 4, "ry-": 5, "rz-": 6,
                     "X-": 1, "Y-": 2, "Z-": 3, "RX-": 4, "RY-": 5, "RZ-": 6}
        axis_dic5 = {"J1+": 1, "J2+": 2, "J3+": 3, "J4+": 4, "J5+": 5, "J6+": 6,
                     "j1+": 1, "j2+": 2, "j3+": 3, "j4+": 4, "j5+": 5, "j6+": 6, }
        axis_dic6 = {"J1-": 1, "J2-": 2, "J3-": 3, "J4-": 4, "J5-": 5, "J6-": 6,
                     "j1-": 1, "j2-": 2, "j3-": 3, "j4-": 4, "j5-": 5, "j6-": 6, }

        if axis_char_str in axis_dic1:
            RobAxis = axis_dic1[axis_char_str]
            ref: int = 2  # 基坐标系点动
            if direcCharOrCoordType in dir_dic:
                AxisDir = dir_dic[direcCharOrCoordType]
            else:
                print("direction_char_str =", direcCharOrCoordType, "is no right")
                self.checkApiErrorBase(4)  # 检查。非0则错误. 4 接口参数值异常, 检查参数值类型或范围
        elif axis_char_str in axis_dic2:
            RobAxis = axis_dic2[axis_char_str]
            ref: int = 0  # 关节点动
            if direcCharOrCoordType in dir_dic:
                AxisDir = dir_dic[direcCharOrCoordType]
            else:
                print("direction_char_str =", direcCharOrCoordType, "is no right")
                self.checkApiErrorBase(4)  # 检查。非0则错误. 4 接口参数值异常, 检查参数值类型或范围
        elif axis_char_str in axis_dic3:
            RobAxis = axis_dic3[axis_char_str]
            AxisDir = 1  # +方向
            if int(direcCharOrCoordType) == 1:
                ref: int = 8  # -工件坐标系点动
            elif int(direcCharOrCoordType) == 2:
                ref: int = 4  # -工具坐标系点动
            else:
                ref: int = 2  # 基坐标系点动
        elif axis_char_str in axis_dic4:
            RobAxis = axis_dic4[axis_char_str]
            AxisDir = 0  # -方向
            if int(direcCharOrCoordType) == 1:
                ref: int = 8  # -工件坐标系点动
            elif int(direcCharOrCoordType) == 2:
                ref: int = 4  # -工具坐标系点动
            else:
                ref: int = 2  # 基坐标系点动
        elif axis_char_str in axis_dic5:
            RobAxis = axis_dic5[axis_char_str]
            AxisDir = 1  # +方向
            ref: int = 0  # 关节点动
        elif axis_char_str in axis_dic6:
            RobAxis = axis_dic6[axis_char_str]
            AxisDir = 0  # -方向
            ref: int = 0  # 关节点动
        else:
            print("axis_char_str =", axis_char_str, "is no right")
            self.checkApiErrorBase(4)  # 检查。非0则错误. 4 接口参数值异常, 检查参数值类型或范围

        print('ref_zuobiaoxi,   RobAxis   ,AxisDir:  ', ref, RobAxis, AxisDir, vel, acc, max_dis)
        ret = self.moveJogBase(RobAxis, AxisDir, ref, max_dis, vel, acc)
        self.checkApiErrorBase(ret)  # 成功：[0],失败：[errcode]

    def continueJog(self, axis_char_str: str, direction_char_str: str) -> None:
        """ ジョグ継続
        """
        pass

    # def stopJogBase_Dobot(self) -> None:
    #     ret = self.dashboard.ResetRobot()
    #     self.checkApiErrorBase(ret)
    #     return

    def stopJog(self) -> None:
        # 原型 ImmStopJOG()
        # 描述jog 点动立即停止
        # 参数无
        # 返回值
        # • 成功：[0]
        # • 失败：[errcode]
        ret = self.robot.ImmStopJOG()
        self.checkApiErrorBase(ret)
        # ret = self.dashboard.ResetRobot()
        return

    def ResetRobot_Dobot(self):
        """  Dobot中应该是作为Stop使用。在StopRobot 和 JobStop 中调用
        停止机器人，清空已规划的指令队列。
        返回
        ErrorID,{},ResetRobot();
        """
        string = "ResetRobot()"
        self.send_data(string)
        return self.wait_reply()

    def ResetRobot(self):
        """  此函数未使用
           Dobot的Reset Robot：停止机器人，清空已规划的指令队列，应该相当Fr3的ImmStopJOG（或StopMotion）+ ProgramStop ？ 
            原型 ProgramStop()
            描述 终止当前运行的作业程序
            参数 无
            返回值
            • 成功：[0]
            • 失败：[errcode
        """
        ret = self.robot.ProgramStop()
        self.checkApiErrorBase(ret)

        return

    def printRobotStatus(self) -> None:
        """ 変数表示(デバッグ用)
        """
        print("##########################  Status  ##############################################")
        print('X  = {0:.3f}'.format(self.current_pos[X]))
        print('Y  = {0:.3f}'.format(self.current_pos[Y]))
        print('Z  = {0:.3f}'.format(self.current_pos[Z]))
        print('RX  = {0:.3f}'.format(self.current_pos[RX]))  ##########0105
        print('RY  = {0:.3f}'.format(self.current_pos[RY]))  #########0105
        print('RZ  = {0:.3f}'.format(self.current_pos[RZ]))  #########0105
        print("emerge -> " + str(self.emerge) + ", " + "error -> ", str(self.error) + ", " + "servo -> ",
              str(self.servo) + ", " + "moving -> " + str(self.moving) + ", " + "origin -> ",
              str(self.origin) + ", " + "arrived -> ", str(self.arrived) + ", " + "dragging -> ", str(self.dragging))
        print("error id = ", self.error_id)
        print("##################################################################################")

    #############################################################
    # ロボット固有関数
    #############################################################
    '''
    def setInitialRobotParamBase_Dobot(self):
        default = 50
        self.setAccLineBase(default)
        self.setVelLineBase(default)
        self.setAccJointBase(default)
        self.setVelJointBase(default)

    def setInitialRobotParamBase_old(self):
        default = 50.0000

        ret=self.robot.SetSpeed(default)  #设置全局速度, 速度百分比，范围[0~100]
        self.checkApiErrorBase(ret)  #成功：[0]，失败：[errcode]

        self.vel_default=default
        self.acc_default=default
        self.velJoint_default=default
        self.accJoint_default=default

    '''

    def setInitialRobotParamBase(self):
        # default = 100.0    ####MoveJ等处，vel百分比要为浮点数 ####1114
        default = 100.0  ####MoveJ等处，vel百分比要为浮点数 ####1114

        ret = self.robot.SetSpeed(int(default))  # 设置全局速度, 速度百分比，范围[0~100]，百分比要为整数 #####1114
        self.checkApiErrorBase(ret)  # 成功：[0]，失败：[errcode]

        self.setAccLineBase(default)
        self.setVelLineBase(default)
        self.setAccJointBase(default)
        self.setVelJointBase(default)

    # NOTE:apiのコマンドエラー確認
    '''
    def checkApiErrorBase_Dobot(self,ret:str):
        api_err = False
        _ret = self.transformStr2Ret(ret)
        if _ret != 0:
            self.error = True
            # error_id = self.transformStr2Error(ret)
            if ret==-1:
                print("Fail to get\nApi Error No.",_ret)
            else:
                print("Api Error No.",_ret)
                api_err = True
        return api_err
    
    '''

    def checkApiErrorBase(self, ret):
        self.error = False
        # api_err = False
        self.api_err = False  ##要作为self的参数，main中才可以调用，.error和.api_err同时使用（只要一个即可，为了调试方便
        # _ret = self.transformStr2Ret(ret)
        _ret = int(ret)
        if _ret != 0:
            self.error = True
            # api_err = True
            self.api_err = True
            print("Api Error No.", _ret)
            # error_id = self.transformStr2Error(ret)
            if ret == -1:
                # print("Fail to get\nApi Error No.",_ret)
                print("Please connect to the supporter for Fr-robot", "其他错误,联系售后工程师查看控制器日志")
            elif ret == 3:
                print("接口参数个数不一致,检查接口参数个数")
            elif ret == 4:
                print("接口参数值异常,检查参数值类型或范围")
            elif ret == 8:
                print("轨迹文件打开失败,检查TPD轨迹文件是否存在或轨迹名是否正确")
            elif ret == 14:
                print("接口执行失败,检查web界面是否报故障或状态反馈是否报故障")
            elif ret == 18:
                print("机器人程序正在运行，先停止程序，再进行其他操作")
            elif ret == 25:
                print("数据异常，计算失败,重新标定或辨识")
            elif ret == 28:
                print("逆运动学计算结果异常，检查位姿是否合理")
            elif ret == 30:
                print("不可复位故障，请断电重启控制箱 ，请断电重启控制箱 ")
            elif ret == 34:
                print("工件号错误 ，请检查工件号是否合理 ")
            elif ret == 36:
                print("文件名过长, 请缩减文件名长度 ")
            elif ret == 38:
                print("奇异位姿，计算失败 ，请更换位姿 ")
            elif ret == 64:
                print("未加入指令队列 ，联系售后工程师查看控制器日志 ")
            elif ret == 66:
                print("整圆,螺旋线指令中间点1错误 ，检查中间点1数据是否正确 ")
            elif ret == 67:
                print("整圆,螺旋线指令中间点2错误 ，检查中间点2数据是否正确 ")
            elif ret == 68:
                print("整圆,螺旋线指令中间点3错误 ，检查中间点3数据是否正确 ")
            elif ret == 69:
                print("圆弧指令中间点错误 ，检查中间点数据是否正确 ")
            elif ret == 70:
                print("圆弧指令目标点错误 ，检查目标点数据是否正确 ")
            elif ret == 73:
                print("夹爪运动报错 ，检查夹爪通信状态是否正常 ")
            elif ret == 74:
                print("直线指令点错误 ，检查点位数据是否正确 ")
            elif ret == 75:
                print("通道错误 ，检查IO编号是否在范围内 ")
            elif ret == 76:
                print("等待超时 ，检查IO信号是否输入或接线是否正确 ")
            elif ret == 82:
                print("TPD指令点错误 ，重新记录示教轨迹 ")
            elif ret == 83:
                print("TPD指令工具与当前工具不符 ，更改为TPD示教时所用的工具坐标系 ")
            elif ret == 94:
                print("样条指令点错误 ，检查点位数据是否正确 ")
            elif ret == 108:
                print("螺旋线指令起点错误 ，检查起点数据是否正确 ")
            elif ret == 112:
                print("给定位姿无法到达 ，检查目标位姿是否合理 ")
        return self.api_err

    def mySleepBase(self, sleep_time):
        now = perf_counter()
        while (perf_counter() - now < sleep_time):
            pass

    # Dobot，
    # NOTE:Fr3不需要
    '''
    def connectRobotBase_dobot(self):
        try:
            ip = "192.168.250.101"
            # NOTE:以下は固定値
            dashboard_p = 29999
            move_p = 30003
            feed_p = 30004
            self.dashboard = DobotApiDashboard(ip, dashboard_p)
            self.move = DobotApiMove(ip, move_p)
            self.feed = DobotApi(ip, feed_p)
            # return dashboard, move, feed
        except Exception as e:
            print("Fail to connect")
            raise e

    '''

    '''
    def worker1():
        print('start worker1')
        #time.sleep(5)
        sleep(5)
        print('end worker1')

    # プロセスで実行する関数の準備
    def worker2(x, y):
        print('start worker2')
        #time.sleep(5)
        sleep(5)
        print('end worker2', x, y)

    def run2(self):
        p1 = Process(name="p1", target=self.worker1)
        p2 = Process(name="p2", target=self.worker2, args=(10, 20))

        # プロセスの開始
        p1.start()
        p2.start()
        p1.join()
        p2.join()
    
    def startMultiFeedbackBase(self):
        self.run2()
        #feed_process = Process(target=self.getFeedbackBase)  #创建了feed_process进程，进程调用的是getFeedbackBase函数
        #ppp = Process(target=self.run2)  #创建了feed_process进程，进程调用的是getFeedbackBase函数
        #feed_process = Process(target=self.getFeedbackBase,args=())  #创建了feed_process进程，进程调用的是getFeedbackBase函数

        #feed_process = mp.Process(target=self.getFeedbackBase)  #创建了feed_process进程，进程调用的是getFeedbackBase函数
        #ppp.daemon = True   #设置子进程属性 daemon 为 True 来使主进程运行完毕后子进程强制结束
                    #每个进程修改全局变量后只能局部可见，虽然使用相同的名字，但是全局变量不共享
        #ppp.start()   #开始执行进程
        # self.mySleepBase(1)
        return 
    '''

    # NOTE:並列処理開始
    def startMultiFeedbackBase(self):
        # with open('log_Multi_fr3api.txt', 'a') as fm:    #multi 不知输出到何处
        #     print(' startMultiFeedbackBase start', time(),file=fm)
        # fm.close()
        feed_process = Process(target=self.getFeedbackBase)  # 创建了feed_process进程，进程调用的是getFeedbackBase函数
        feed_process.daemon = True  # 设置子进程属性 daemon 为 True 来使主进程运行完毕后子进程强制结束
        # 每个进程修改全局变量后只能局部可见，虽然使用相同的名字，但是全局变量不共享
        feed_process.start()  # 开始执行进程
        # self.mySleepBase(1)
        # input('multi start')  ##### for test
        # with open('log_Multi_fr3api.txt', 'a') as fm:   #multi 不知输出到何处
        #     print(' startMultiFeedbackBase end', time(),file=fm)
        # fm.close()
        return

    def getFeedbackBase(self):
        # self.getFeedbackBase_new()    #只接收一次
        self.getFeedbackBase_new01()  # 一直接收
        # self.getFeedbackBase_old()

    # NOTE:フィードバックループ
    '''
    def getFeedbackBase_Dobot(self):
        hasRead = 0
        sleep_t = 0.001
        while True:
            data = bytes()
            while hasRead < 1440:
                temp = self.feed.socket_dobot.recv(1440 - hasRead)
                if len(temp) > 0:
                    hasRead += len(temp)
                    data += temp
            hasRead = 0

            a = np.frombuffer(data, dtype=MyType)
            if hex((a['test_value'][0])) == '0x123456789abcdef':
                # Refresh Properties
                # self.current_actual = a["tool_vector_actual"][0]
                # print("ROBOTループ",int(a["robot_mode"][0]))
                self.robot_mode.value =  int(a["robot_mode"][0])
                
            self.mySleepBase(sleep_t)
    
    '''

    def getFeedbackBase_new01old(self):  # no use  #一直接收
        sleep_t = 0.001
        while True:
            rob_stat = self.FairRobotApi.wait_reply_new()
            RVV = []  #####1114  接收正确性判断改为wait_reply中进行
            for i in range(2):
                RVV.append(hex(rob_stat[i]))

            if RVV[0:2] == ['0x5A', '0x5A'] or RVV[0:2] == ['0x5a', '0x5a']:  # 人为暂停后值会有错误，需要检查
                self.robot_mode.value = int(rob_stat[5])  # 1停止；2 运行；3 暂停；4 拖动
                print(RVV, self.robot_mode.value)
            self.mySleepBase(sleep_t)

    def getFeedbackBase_new01NG(self):  # no use 一直接收
        sleep_t = 0.001
        # sleep_t = 0.5    #########1114 测试
        while True:
            with open('log_Multi_fr3api.txt', 'a') as fm:
                # print('     befor:robot_mode, error_id=', self.robot_mode.value,self.error_id.value, time(),file=fm)
                print('     befor:robot_mode, error_id=', self.robot_mode, self.error_id, time(), file=fm)
            fm.close()
            rob_stat = self.FairRobotApi.wait_reply_new()
            rob_stat = self.FairRobotApi.wait_reply_new()
            # self.robot_mode.value =  int(rob_stat[5])  #1停止；2 运行；3 暂停；4 拖动
            # print(' #1停止；2 运行；3 暂停；4 拖动',self.robot_mode.value)
            self.mySleepBase(sleep_t)
            with open('log_Multi_fr3api.txt', 'a') as fm:
                print('     after:robot_mode, error_id=', self.robot_mode, self.error_id, time(), file=fm)
            fm.close()

    def getFeedbackBase_new01(self):  # 一直接收  using
        sleep_t = 0.001
        while True:
            # with open('log_Multi_fr3api.txt', 'a') as fm:        #multi 不知输出到何处
            #     #print('     befor:robot_mode, error_id=', self.robot_mode.value,self.error_id.value, time(),file=fm)
            #     print('     befor getFeedbackBase :robot_mode, error_id=', self.robot_mode.value,self.error_id.value, time(),file=fm)
            # fm.close()
            rob_stat = self.FairRobotApi.wait_reply_new()
            # print(rob_stat)
            self.robot_mode.value = int(rob_stat[5])  # 1停止；2 运行；3 暂停；4 拖动
            self.error_id.value = int(rob_stat[6])  #
            # print(' after getFeedbackBase:robot_mode, error_id=', self.robot_mode.value,self.error_id.value, time())
            # print(' after getFeedbackBase:robot_mode, error_id=', self.robot_mode,self.error_id, time())
            # multi 不知输出到何处
            self.mySleepBase(sleep_t)
            # with open('log_Multi_fr3api.txt', 'a') as fm:             #multi 不知输出到何处
            #     print('     after getFeedbackBase:robot_mode, error_id=', self.robot_mode.value,self.error_id.value, time(),file=fm)
            #     print('     after getFeedbackBase:robot_mode, error_id=', self.robot_mode.value,self.error_id.value, file=fm)
            # fm.close()

    def getFeedbackBase_new(self):  # 只接收一次  no use
        # rob_stat=self.FairRobotApi.wait_reply_new()   #只有接收正确后才会返回
        rob_stat = self.feed.wait_reply_new()  # 只有接收正确后才会返回
        self.robot_mode.value = int(rob_stat[5])  # 1停止；2 运行；3 暂停；4 拖动
        # print(self.robot_mode.value)
        return

    def getFeedbackBase_old(self):  ######## no use
        hasRead = 0
        sleep_t = 0.001
        while True:
            data = bytes()
            # while hasRead < 1440:
            while hasRead < 256:  # Fr3的反馈字节数241
                # temp = self.feed.socket_dobot.recv(1440 - hasRead)

                # temp = self.feed.socket_FairRobot.recv(256 - hasRead)   #w
                # temp = self.FairRobotApi.socket_FairRobot.recv(256 - hasRead)  #未开 startMultiFeedbackBase 时只有self.FairRobotApi，无self.feed
                temp = self.feed.socket_FairRobot.recv(256 - hasRead)  #############1222
                if len(temp) > 0:
                    hasRead += len(temp)
                    data += temp
            hasRead = 0

            a = np.frombuffer(data, dtype=MyType)
            # val=hex((a['head_Fr'][0]))
            # self.robot_mode.value =  int(a["program_state"][0])  #1停止；2 运行；3 暂停；4 拖动
            # print(a['head_Fr'][0],hex((a['head_Fr'][0])),a["program_state"][0])
            # print(val,self.robot_mode.value)
            if hex((a['head_Fr'][0])) == '0x5A5A' or hex((a['head_Fr'][0])) == '0x5a5a':
                # Refresh Properties
                # self.current_actual = a["tool_vector_actual"][0]
                # print("ROBOTループ",int(a["robot_mode"][0]))
                # self.robot_mode.value =  int(a["robot_mode"][0])  #0-自动模式，1-手动模式；2-拖动模式
                self.robot_mode.value = int(a["program_state"][0])  # 1停止；2 运行；3 暂停；4 拖动
                print(self.robot_mode.value)
                """ #Dobot 模式很多,  
                    1 ROBOT_MODE_INIT 初始化
                    2 ROBOT_MODE_BRAKE_OPEN 有任意关节的抱闸松开
                    3 ROBOT_MODE_POWER_STATUS 本体未上电
                    4 ROBOT_MODE_DISABLED 未使能（无抱闸松开）
                    5 ROBOT_MODE_ENABLE 使能且空闲
                    6 ROBOT_MODE_BACKDRIVE 拖拽模式
                    7 ROBOT_MODE_RUNNING 运行状态，包括轨迹复现/拟合中，机器人执行运动命令中，工程运行中。
                    8 ROBOT_MODE_RECORDING 轨迹录制模式
                    9 ROBOT_MODE_ERROR 有未清除的报警。此状态优先级最高，无论机械臂处于什么状态，有报警时都返回9
                    10 ROBOT_MODE_PAUSE 暂停状态
                    11 ROBOT_MODE_JOG 点动中
                """
            self.mySleepBase(sleep_t)

    # NOTE:ret文字列を配列へ変換
    # NOTE:Fr3不需要
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
    # NOTE:Fr3不需要
    def transformStr2Pos(self, str: str):
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
    # NOTE:Fr3不需要
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
    # NOTE:Fr3不需要
    '''
    def transformStr2Error_Dobot(self,str :str):
        align_str = str.replace('{', '').replace('}', '').replace(';', '').replace('\n', '').replace('\t', '').replace('[', '').replace(']', '')
        align_list = align_str.split(',')
        try:
            ret = int(align_list[1])
        except:
            ret = 0
        return ret
    
 
    def stopRobotBase_Dobot(self) -> None:
        ret = self.dashboard.ResetRobot()
        self.checkApiErrorBase(ret)
        return
    
    '''

    def stopRobotBase(self) -> None:
        # start = time()
        print('call stop', perf_counter())
        start = time()
        while True:
            #        
            # --0 ori 处理  单纯停止
            # ret = self.robot.StopMotion()  #终止运动，使用终止运动需运动指令为非阻塞状态  #PaouseMotion 在C中有，python中无，下次更新预计会有
            # ret = self.robot.SetSpeed(20)  #再启动后变更有效
            # print('speed 20')          

            # --1 处理  用程序暂停方式，途中暂停，到目的地后TP才可控
            # ret = self.robot.ProgramPause()  #暂停程序，使用终止运动需运动指令为非阻塞状态，立刻停止
            # print('ProgramPause')   
            # ret = self.robot.SetSpeed(2)  ##速度变化在到目的地后，下一个动作开始有效
            # print('speed 2')             
            # sleep(0.2)
            # ret = self.robot.ProgramResume()  #程序再开，必须。继续运动到目的地。要在开后TP上run才能动作
            # print('ProgramResume')   

            # --2 new 处理  先程序暂再停止，最后程序再开。停止似乎更平稳一点
            ret = self.robot.ProgramPause()  # 暂停程序，使用终止运动需运动指令为非阻塞状态
            print('ProgramPause')
            sleep(0.2)
            ret = self.robot.StopMotion()  # 终止运动，使用终止运动需运动指令为非阻塞状态  #PaouseMotion 在C中有，python中无，下次更新预计会有
            # ret = self.robot.SetSpeed(20)  #再启动后变更有效
            ret = self.robot.ProgramResume()  # 程序再开，使用终止运动需运动指令为非阻塞状态，必须。
            # sleep(1)
            print('ProgramResume')

            # ret = self.robot.SetSpeed(20)  #再启动后变更有效

            if ret == 0:
                break
            else:
                t = time() - start
                if t > 2:
                    break
        self.checkApiErrorBase(ret)  # 成功：[0],失败：[errcode]
        return

    # NOTE:Moving発生確認
    '''
    def checkMovingBase_Dobot(self):
        if self.robot_mode.value == 7:
            self.moving = True
        else: 
            self.moving = False

    '''

    def checkMovingBase(self):
        ret_val = self.robot.GetRobotMotionDone()
        ret = ret_val[0]
        val = ret_val[1]
        self.checkApiErrorBase(ret)  # 成功：[0,state],state:0-未完成，1-完成
        if ret == 0:
            if val == 0:
                self.moving = True
            # else:
            elif val == 1:
                self.moving = False

    # NOTE:エラー発生確認
    '''
    def checkErrorBase_Dobot(self):
        self.error = False
        if self.robot_mode.value == 9:
            self.error = True
    
    '''

    def checkErrorBase(self):
        # self.checkErrorBase_old()
        self.checkErrorBase_new()

    def checkErrorBase_old(self):
        self.error = False
        # rob_stat=FairRobotApi.wait_reply_old()
        rob_stat = self.FairRobotApi.wait_reply_old()
        if rob_stat[0]['error_code'] != 0:
            self.error = True

    def checkErrorBase_new(self):
        if self.error_id == 0:  # set in wait_reply()
            self.error = False
        else:
            self.error = True

    def checkErrorBase_new01(self):  ####0108 no use
        self.error = False
        rob_stat = self.FairRobotApi.wait_reply_new()
        val = int(rob_stat[6])
        # val1 = str(rob_stat[6])
        # val2 = int(val1)
        # print("int,str, str->int",val,val1, val2)
        if val != 0:
            self.error = True

    # NOTE:エラー番号の取得
    '''
    def getErrorBase_Dobot(self):
        ret = self.dashboard.GetErrorID()
        # self.checkApiErrorBase(ret)
        val = self.transformStr2Error(ret)
        return val

    '''

    def getErrorBase_old(self):
        rob_stat = self.FairRobotApi.wait_reply_old()
        # self.checkApiErrorBase(ret)
        val = int(rob_stat[0]['error_code'])
        if val == 1:
            print("1:驱动器故障")
        elif val == 2:
            print("2:超出软限位故障")
        elif val == 3:
            print("3:碰撞故障")
        elif val == 4:
            print("4:奇异位姿")
        elif val == 5:
            print("5:从站错误")
        elif val == 6:
            print("6:指令点错误")
        elif val == 7:
            print("7:IO错误")
        elif val == 8:
            print("8:夹爪错误")
        elif val == 9:
            print("9:文件错误")
        elif val == 10:
            print("10:参数错误")
        elif val == 11:
            print("11:扩展轴超出软限位错误")
        elif val == 12:
            print("12:关节配置警告")
        # elif val ==0:             ##########1114 测试
        #    print("0: 无错误")  
        return val

    def getErrorBase_new(self):
        rob_stat = self.FairRobotApi.wait_reply_new()
        # self.checkApiErrorBase(ret)
        # val = int(rob_stat[0]['error_code'] )
        val = int(rob_stat[6])
        # val1 = str(rob_stat[6])
        # val2 = int(val1)
        # print("int,str, str->int",val,val1, val2)
        if val == 1:
            print("1:驱动器故障")
        elif val == 2:
            print("2:超出软限位故障")
        elif val == 3:
            print("3:碰撞故障")
        elif val == 4:
            print("4:奇异位姿")
        elif val == 5:
            print("5:从站错误")
        elif val == 6:
            print("6:指令点错误")
        elif val == 7:
            print("7:IO错误")
        elif val == 8:
            print("8:夹爪错误")
        elif val == 9:
            print("9:文件错误")
        elif val == 10:
            print("10:参数错误")
        elif val == 11:
            print("11:扩展轴超出软限位错误")
        elif val == 12:
            print("12:关节配置警告")
        # elif val ==0:             ##########1114 测试
        # print("0: 无错误")
        return val

    def getErrorBase(self):
        val = self.getErrorBase_new()
        # val=self.getErrorBase_old()
        return val

    def moveAbsolutePtpBase(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, tool_no: int,
                            user_no: int, vel: float) -> None:
        # ret = self.MovJ(self, x, y, z)
        ret = self.MovJ(x, y, z, rx, ry, rz, tool_no, user_no, vel)
        # self.checkApiErrorBase(ret)    #checkApiErrorBase改为在MovL中进行
        return

    def MovJ(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, tool_no: int, user_no: int,
             vel: float) -> int:  # 加参数时，正常的顺序
        """
        Joint motion interface (point-to-point motion mode)
        #关节空间运动#从当前位置以关节运动方式运动至笛卡尔坐标目标点。关节运动的轨迹非直线，所有关节会同时完成运动。

        x: A number in the Cartesian coordinate system x
        y: A number in the Cartesian coordinate system y
        z: A number in the Cartesian coordinate system z
        rx: Position of Rx axis in Cartesian coordinate system
        ry: Position of Ry axis in Cartesian coordinate system
        rz: Position of Rz axis in Cartesian coordinate system
        """
        P1 = [x, y, z, rx, ry, rz]  # 笛卡尔空间坐标
        print('moveJ: pos=', P1, 'Para=', vel, tool_no)
        # j1 = self.robot.GetInverseKin(0,P1,-1)       #关节位置 ,只有笛卡尔空间坐标的情况下，可用逆运动学接口求解关节位置
        ret_val = self.robot.GetInverseKin(0, P1, -1)  # 关节位置 ,只有笛卡尔空间坐标的情况下，可用逆运动学接口求解关节位置
        # [in]type 0-绝对位姿(基坐标系)，1-增量位姿(基坐标系)，2-增量位姿(工具坐标系)
        # [in] config 关节空间配置，[-1]-参考当前关节位置解算，[0~7]-,→依据特定关节空间配置求解
        ret = ret_val[0]
        if ret == 0:
            j1 = ret_val[1:7]
        else:
            print('坐标变换错误')
            self.checkApiErrorBase(ret)  # 检查。非0则错误
            return ret

        eP1 = [0.000, 0.000, 0.000, 0.000]  # 外部轴1位置~外部轴4位置
        dP1 = [0.000, 0.000, 0.000, 0.000, 0.000, 0.000]  # 位姿偏移量，单位[mm][°]

        # MoveJ(joint_pos,desc_pos,tool,user,vel,acc,ovl,exaxis_pos,blendT,offset_flag,offset_pos)
        # robot.MoveJ(J1,p1,1,0,100.0,180.0,100.0,eP1,-1.0,0,dP1)
        # ------Fr3的SDK方式，用Fr3的SDK方式？ send_data方式？

        # flag = -1.0 #[-1.0]-运动到位(阻塞)，[0~500]-平滑时间(非阻塞)，单位[ms]
        flag = 0.0  # [-1.0]-运动到位(阻塞)，[0~500]-平滑时间(非阻塞)，单位[ms]
        # with open('log_fr3api.txt', 'a') as f1:
        #     t00=time()
        #     print('         MoveJ start,,time=',t00,file=f1)
        #     #print('MoveJ start',file=f1)
        #     print("         target pos", P1,file=f1)
        #     print("         vel,acc,ovl,,blendT", vel,"180.0,100.0",flag,file=f1)
        # f1.close()
        # vel=20.0

        ret = self.robot.MoveJ(j1, P1, tool_no, user_no, vel, 180.0, 100.0, eP1, flag, 0, dP1)
        # 成功：[0],失败：[errcode]
        # with open('log_fr3api.txt', 'a') as f1:
        #     t01=time()
        #     #f.write('runPtp start,time={0}\n'.format(t0))
        #     print('         MoveJ end,,time=',t01, '   ', t01-t00,file=f1)
        # f1.close()
        self.checkApiErrorBase(ret)  # 检查。非0则错误

        # ------send_data方式， 用Fr3的SDK方式？ send_data方式？
        # string = "self.robot.MoveJ({0},{1},{2},{3},{4},180.0,100.0,{5},-1.0,0,{6})".format(j1, P1,tool_no, user_no, vel, eP1, dP1)
        # string = "MoveJ({0},{1},{2},{3},{4},180.0,100.0,{5},-1.0,0,{6})".format(j1, P1,tool_no, user_no, vel, eP1, dP1)
        # 工具坐标，工件坐标均设默认0 （想不使用，但不知道正确与否）
        # 速度百分比，[0~100]
        #:[-1.0]-运动到位(阻塞)，[0~500]-平滑时间(非阻塞)，单位[ms] #速度相关100%
        # [0]-不偏移，[1]-工件/基坐标系下偏移，[2]-工具坐标系下偏移

        # self.send_data(string)
        # return self.wait_reply()  #返回整个字符串，用途不明，只是返回？
        return ret

    def moveAbsoluteLineBase(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, tool_no: int,
                             user_no: int, vel: float) -> None:
        # ret = self.MovL(x, y, z, r)
        # with open('log_fr3api.txt', 'a') as f1:
        #     t00=time()
        #     print('     MoveL start,,time=',t00,file=f1)
        #     print("     target pos", x,y,z,rx,ry,rz,file=f1)
        #     print("     vel,", vel,file=f1)
        # f1.close()
        ret = self.MovL(x, y, z, rx, ry, rz, tool_no, user_no, vel)  #####1114   实际ret返回的是checkApiErrorBase的值=movL返回值
        # self.checkApiErrorBase(ret)    #checkApiErrorBase改为在MovL中进行
        # print('moveAbsoluteLineBase MovL ret',ret,perf_counter())

        # 成功：[0],失败：[errcode]
        # with open('log_fr3api.txt', 'a') as f1:
        #     t01=time()
        #     print('     MoveL end,,time=',t00,"  ",t01-t00,file=f1)
        # f1.close()
        # ret = self.MovL(x, y, z, rx,ry,rz,tool_no,user_no,vel)   #####1114   movL
        return  ##无返回值

    def MovL(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, tool_no: int, user_no: int,
             vel: float):  # 加参数时，正常的顺序
        """
        Coordinate system motion interface (linear motion mode) 
        #笛卡尔空间直线运动,#从当前位置以直线运动方式运动至笛卡尔坐标目标点。

        x: A number in the Cartesian coordinate system x
        y: A number in the Cartesian coordinate system y
        z: A number in the Cartesian coordinate system z
        rx: Position of Rx axis in Cartesian coordinate system
        ry: Position of Ry axis in Cartesian coordinate system
        rz: Position of Rz axis in Cartesian coordinate system
        """

        P1 = [x, y, z, rx, ry, rz]  # 笛卡尔空间坐标
        # print('target',P1)
        print('moveL: pos=', P1, 'Para=', vel, tool_no)

        ret_val = self.robot.GetInverseKin(0, P1, -1)  # 关节位置 ,只有笛卡尔空间坐标的情况下，可用逆运动学接口求解关节位置
        # [in]type 0-绝对位姿(基坐标系)，1-增量位姿(基坐标系)，2-增量位姿(工具坐标系)
        # [in] config 关节空间配置，[-1]-参考当前关节位置解算，[0~7]-,→依据特定关节空间配置求解
        ret = ret_val[0]
        if ret == 0:
            j1 = ret_val[1:7]
        else:
            print('逆运动学求解错误')
            self.checkApiErrorBase(ret)  # 检查。非0则错误
            return ret

            # j1 = [j1[1],j1[2],j1[3],j1[4],j1[5],j1[6]] #####'''' j1[0]为ret值,一定要注意
        # j1 = ret[1:7]       #####'''' j1[0]为ret值,一定要注意

        eP1 = [0.000, 0.000, 0.000, 0.000]  # 外部轴1位置~外部轴4位置
        dP1 = [0.000, 0.000, 0.000, 0.000, 0.000, 0.000]  # 位姿偏移量，单位[mm][°]

        # flag = -1.0 #[-1.0]-运动到位(阻塞)，[0~1000]-平滑半径(非阻塞)，单位[mm]
        flag = 1000.0  # [-1.0]-运动到位(阻塞)，[0~1000]-平滑半径(非阻塞)，单位[mm]
        # print('flag',flag,perf_counter())

        # print(tool_no,user_no,int(vel),flag)
        # with open('log_fr3api.txt', 'a') as f1:
        #     t00=time()
        #     print('         MoveL start,,time=',t00,file=f1)
        #     #print('MoveL start',file=f1)
        #     print("         target pos", P1,file=f1)
        #     print("         vel,acc,ovl,blendT", vel,"180.0,100.0",flag,file=f1)
        # f1.close()

        # user_no=tool_no  ###tool与基座标不同
        # tool_no =0

        ret = self.robot.MoveL(j1, P1, tool_no, user_no, vel, 180.0, 100.0, flag, eP1, 0, 0, dP1)
        # ret=self.robot.MoveL(j1,P1,2,user_no,vel,180.0,100.0,flag, eP1,0,0,dP1)
        # MoveL(joint_pos,desc_pos,tool,user,vel,acc,ovl,blendR,exaxis_pos,search,offset_flag,offset_pos)
        # 成功：[0],失败：[errcode]
        # print('robot.moveL ret',ret,perf_counter())
        self.checkApiErrorBase(ret)  # 检查。非0则错误
        # print('movL',ret,perf_counter())
        # with open('log_fr3api.txt', 'a') as f1:
        #     t01=time()
        #     #f.write('runPtp start,time={0}\n'.format(t0))
        #     print('         MoveL end,,time=',t01,"    ",t01-t00,file=f1)
        # f1.close()

        return ret

    def moveRelativeBase(self, x: float, y: float, z: float, rx: float, ry: float, rz: float, tool_no: int,
                         user_no: int, vel: float, acc: float) -> None:
        # current_list = self.getCurrentPosBase()  ###此时取得的坐标为新坐标下的值
        # print(current_list)
        current_list = self.current_pos  ## 保存的坐标为旧坐标下的值
        # print(current_list)
        offset_list = [x, y, z, rx, ry, rz]
        target_list = []
        for i in range(6):
            val = current_list[i] + offset_list[i]
            target_list.append(val)  ####目标，执行运动时，到达新坐标中指定位置
        #######1114  moveAbsoluteLineBase无返回值    
        self.moveAbsoluteLineBase(x=target_list[X], y=target_list[Y], z=target_list[Z], rx=target_list[RX],
                                  ry=target_list[RY], rz=target_list[RZ], tool_no=tool_no, user_no=user_no,
                                  vel=vel)  # 关键字参数，非位置参数
        # ret = self.moveAbsoluteLine(x=target_list[X],y=target_list[Y],z=target_list[Z],rx=target_list[RX],ry=target_list[RY],rz=target_list[RZ])
        return

    '''
    def moveOriginBase_Dobot(self) -> None:
        pass

    '''

    def moveOriginBase_old(self) -> None:
        j1 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        P1 = self.getJoint2Pos(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        eP1 = [0.000, 0.000, 0.000, 0.000]  # 外部轴1位置~外部轴4位置
        dP1 = [0.000, 0.000, 0.000, 0.000, 0.000, 0.000]  # 位姿偏移量，单位[mm][°]

        # MoveJ(joint_pos,desc_pos,tool,user,vel,acc,ovl,exaxis_pos,blendT,offset_flag,offset_pos)
        flag = -1.0  # [-1.0]-运动到位(阻塞)，[0~500]-平滑时间(非阻塞)，单位[ms]
        tool_no = 0
        user_no = 0
        vel = self.vel_default
        ret = self.robot.MoveJ(j1, P1, tool_no, user_no, vel, 180.0, 100.0, eP1, flag, 0, dP1)
        # 成功：[0],失败：[errcode]
        self.checkApiErrorBase(ret)  # 检查。非0则错误
        return ret  # 1114 追加

    def moveOriginBase(self) -> None:
        # j1 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        # P1=self.getJoint2Pos(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        j1 = [0.0, -90.0, 90.0, 0.0, 0.0, 0.0]  # 水平伸展开的位置，似乎不太好改为垂直方块型  #####1114改
        P1 = self.getJoint2Pos(0.0, 90.0, 0.0, 90.0, 0.0, 0.0)
        # P1 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        # j1=self.getPos2Joint(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        eP1 = [0.000, 0.000, 0.000, 0.000]  # 外部轴1位置~外部轴4位置
        dP1 = [0.000, 0.000, 0.000, 0.000, 0.000, 0.000]  # 位姿偏移量，单位[mm][°]

        # MoveJ(joint_pos,desc_pos,tool,user,vel,acc,ovl,exaxis_pos,blendT,offset_flag,offset_pos)
        flag = -1.0  # [-1.0]-运动到位(阻塞)，[0~500]-平滑时间(非阻塞)，单位[ms]
        tool_no = 0
        user_no = 0
        vel = self.vel_default
        ret = self.robot.MoveJ(j1, P1, tool_no, user_no, vel, 180.0, 100.0, eP1, flag, 0, dP1)
        # 成功：[0],失败：[errcode]
        self.checkApiErrorBase(ret)  # 检查。非0则错误
        # return ret   #1114 追加

    '''
    def setServoOnBase_Dobot(self):
        ret = self.dashboard.EnableRobot()
        self.checkApiErrorBase(ret)
        return 

    def EnableRobot_Dobot(self):
        """
        Enable the robot
        """
        string = "EnableRobot()"
        self.send_data(string)
        return self.wait_reply()

    '''

    def setServoOnBase(self):
        ret = self.robot.RobotEnable(1)  # 1-上使能，0-下使能,机器人上电后默认自动上使能
        self.checkApiErrorBase(ret)  # 返回 成功：[0]，失败：[errcode]
        return

    def setServoOffBase(self):
        # ret = self.dashboard.DisableRobot()
        ret = self.robot.RobotEnable(0)  # 1-上使能，0-下使能,机器人上电后默认自动上使能
        self.checkApiErrorBase(ret)
        return

    '''
    def setServoOffBase_Dobot(self):
        ret = self.dashboard.DisableRobot()
        self.checkApiErrorBase(ret)
        return 

    def resetErrorBase_Dobot(self):
        ret = self.dashboard.ClearError()
        self.checkApiErrorBase(ret)
        return 
    
    '''

    def resetErrorBase(self):
        # ret = self.robot.StopMotion()  #终止运动，使用终止运动需运动指令为非阻塞状态 ##0805有时机器人处于暂停（暂停是运动状态），需要先停止
        ret = self.robot.ResetAllError()  # 错误状态清除，只能清除可复位的错误
        self.checkApiErrorBase(ret)
        return

    def moveInchingBase(self, width: int, axis_char_str: str, direction_char_str: str) -> None:
        pass

    def moveJogBase(self, RobAxis: int, AxisDir: int, ref, max_dis, vel, acc) -> int:
        """
        #点动机械臂 的部分功能 --- jog点动      
        #StartJOG(ref,nb,dir,vel,acc,max_dis) 
                #ref：0-关节点动,2-基坐标系点动,4-工具坐标系点动,8-工件坐标系点动；
                #nb：1-1关节(x轴),2-2关节(y轴),3-3关节(z轴),4-4关节(rx),5-5关节(ry),6-6关节(rz);
                #dir：0-负方向，1-正方向;
                #vel：速度百分比，[0~100];
                #acc：加速度百分比，[0~100];
                #max_dis：单次点动最大角度/距离，单位°或mm
        """
        # self.robot.StartJOG(0,1,0,20.0,20.0,30.0)
        # print('moveJogBase',ref,RobAxis,AxisDir)    ###########1114 Joint以外容易卡死
        # ret=0
        ret = self.robot.StartJOG(ref, RobAxis, AxisDir, vel, acc, max_dis)
        self.checkApiErrorBase(ret)  # 成功：[0]，失败：[errcode]
        return ret

    '''
    def StartJOG(self, nb:int, dir:int, ref:int=0, max_dis:float=30.000,vel:float=20.0,acc:float=20.0):
        """
        Joint motion #点动机械臂 的部分功能 --- jog点动

        #StartJOG(ref,nb,dir,vel,acc,max_dis) 
                #ref：0-关节点动,2-基坐标系点动,4-工具坐标系点动,8-工件坐标系点动；
                #nb：1-1关节(x轴),2-2关节(y轴),3-3关节(z轴),4-4关节(rx),5-5关节(ry),6-6关节(rz);
                #dir：0-负方向，1-正方向;
                #vel：速度百分比，[0~100];
                #acc：加速度百分比，[0~100];
                #max_dis：单次点动最大角度/距离，单位°或mm
        """

        #robot.StartJOG(0,1,0,20.0,20.0,30.0)
        #         
        #string = f"MoveJog({axis_id}"
        string = "StartJOG({0},{1},{2},{3},{4},{5}".format(ref,nb,dir,vel,acc,max_dis)
        # print(string)
        self.send_data(string)
        return self.wait_reply()
    '''
    '''
    def setToolBase_Dobot(self, tool_no: int) -> None:
        self.tool_no = tool_no
        ret = self.dashboard.Tool(int(self.tool_no))
        self.checkApiErrorBase(ret)
        return 

    '''

    def setToolBase(self, tool_no: int) -> None:
        if self.tool_no == tool_no:  ###只有坐标系不同时才进行设置
            # print('cool setToolBase')
            return

        self.tool_no = tool_no
        ##FR的Tool=0与基座标不同，Z向下，x与y互换。在此改用工件坐标，wobj=0与基座标一致，但执行出错
        # if tool_no ==2:
        #     t_coord=[0.0,0.0,30.0,0.0,0.0,0.0]
        # elif tool_no ==1:
        #     t_coord=[10.0,10.0,10.0,0.0,0.0,0.0]
        # else:
        #     t_coord=[0.0,0.0,0.0,0.0,0.0,0.0]

        t_coord = self.Tool_coord[tool_no][:]

        print('tool =', tool_no, t_coord)
        ret = self.robot.SetToolCoord(tool_no, t_coord, 0,
                                      0)  ###0901 坐标系编号，相对末端法兰中心位姿， 0：工具坐标系 1：传感器坐标系， 安装位置 0：末端 1：外部
        # ret=self.robot.SetToolList(tool_no,t_coord,0,0)  ###0901 坐标系编号，相对末端法兰中心位姿， 0：工具坐标系 1：传感器坐标系， 安装位置 0：末端 1：外部
        self.checkApiErrorBase(ret)  # 检查。非0则错误
        '''
        ##FR的Tool=0与基座标不同，Z向下，x与y互换。在此改用工件坐标，wobj=0与基座标一致，但执行出错
        if tool_no ==2:
            w_coord=[0.0,0.0,10.0,0.0,0.0,0.0]
        elif tool_no ==0:
            w_coord=[0.0,0.0,0.0,0.0,0.0,0.0]
        else:
            w_coord=[0.0,0.0,0.0,0.0,0.0,0.0]

        print(tool_no,w_coord)
        ret=self.robot.SetWObjCoord(tool_no,w_coord)  ###0901 坐标系编号，相对末端法兰中心位姿， 
        #ret=self.robot.SetWobjList(tool_no,t_coord)  ###0901 坐标系编号，相对末端法兰中心位姿，
        self.checkApiErrorBase(ret)   #检查。非0则错误
        '''
        # ret=self.robot.GetAcutualTCPNum()  ##flag=0:阻塞，1：非阻塞(默认)
        # currTool=ret[1]
        # print (ret,currTool)

        # ret=self.robot.GetAcutualTCPPose(1)  ##flag=0:阻塞，1：非阻塞(默认)
        # currCoord=ret[1:7]
        # print (ret,currCoord)
        # ret = self.dashboard.Tool(int(self.tool_no))
        # self.checkApiErrorBase(ret)
        return

    '''
    def setUserBase_Dobot(self, user_no: int) -> None:
        self.user_no = user_no
        ret = self.dashboard.User(self.user_no)
        self.checkApiErrorBase(ret)
        return 

    '''

    def setUserBase(self, user_no: int) -> None:
        self.user_no = user_no
        # ret = self.dashboard.User(self.user_no)
        # self.checkApiErrorBase(ret)
        return

    '''    
    def setAccLineBase_Dobot(self,val):
        ret = self.dashboard.AccL(int(val)) 
        self.checkApiErrorBase(ret)
        return 
    '''

    def setAccLineBase(self, val):
        self.acc_default = val
        return

    '''
    def setAccJointBase_Dobot(self,val):  
        ret = self.dashboard.AccJ(int(val))
        self.checkApiErrorBase(ret)
        return 

    '''

    def setAccJointBase(self, val):
        self.accJoint_default = val
        return

    '''
    def setVelLineBase_Dobot(self,val):
        ret = self.dashboard.SpeedL(int(val))
        self.checkApiErrorBase(ret)
        return 

    '''

    def setVelLineBase(self, val):
        self.vel_default = val
        return

    '''
    def setVelJointBase_Dobot(self,val):  
        ret = self.dashboard.SpeedJ(int(val))
        self.checkApiErrorBase(ret)
        return 

    def SpeedJ_Dobot(self, speed):
        """
        Set joint speed ratio (Only for MovJ, MovJIO, MovJR, JointMovJ commands)
        speed : Joint velocity ratio (Value range:1~100)
        """
        string = "SpeedJ({:d})".format(speed)
        self.send_data(string)
        return self.wait_reply()

    '''

    def setVelJointBase(self, val):
        self.velJoint_default = val
        return

    def setWeightBase(self, weight: int) -> None:
        pass

    '''
    def getCurrentPosBase_Dobot(self) -> List[float]:
        ret = self.dashboard.GetPoseTool(self.user_no,self.tool_no)
        self.checkApiErrorBase(ret)
        val = self.transformStr2Pos(ret)
        return val

    def GetPoseTool_Dobot(self,user,tool):
        """
        user: index of User coordinate system
        tool: index of Tool coordinate system
        """
        string = "GetPose({:d},{:d})".format(
            user,tool)
        self.send_data(string)
        return self.wait_reply()
    
    '''

    def getCurrentPosBase(self) -> List[float]:
        flag = 1  # 0-阻塞，1-非阻塞   ####240804 阻塞时，机器人运动结束才会返回坐标，无法进行其他处理。改为非阻塞
        ret_val = self.robot.GetActualTCPNum(flag)  # 获得当前Tool坐标号
        # ret,self.tool_no_current:int = self.robot.GetActualTCPNum(flag)  #获得当前Tool坐标号
        # 成功：[0,tool_id],失败：[errcode,]
        ret = ret_val[0]
        if ret == 0:
            self.tool_no_current = ret_val[1]  # 获得当前Tool坐标号
        else:
            print('tool坐标系取得错误')
            self.checkApiErrorBase(ret)  # 检查。非0则错误
            return ret

            # ret,self.user_no_current:int = self.robot.GetActualWObjNum(flag)  #获得当前工件坐标号
        ret_val = self.robot.GetActualWObjNum(flag)  # 获得当前工件坐标号
        # 成功：[0,Wobj_id],失败：[errcode,]
        ret = ret_val[0]
        if ret == 0:
            self.user_no_current = ret_val[1]  # 获得当前Tool坐标号
        else:
            print('user坐标系取得错误')
            self.checkApiErrorBase(ret)  # 检查。非0则错误
            return ret

            # ret = self.dashboard.GetPoseTool(self.user_no,self.tool_no)
        # ret,val = self.robot.GetActualTCPPose(flag)  #获取当前工具位姿
        ret_val = self.robot.GetActualTCPPose(flag)  # 获取当前工具位姿
        # 成功：[0,tcp_pose],tcp_pose=[x,y,z,rx,ry,rz],  失败：[errcode,]
        ret = ret_val[0]
        if ret == 0:
            val = ret_val[1:7]  ###输出为0-6，7个数，ret_val【1】只是x
            # print('    currentPos=',val)
        else:
            print('TCP 位姿系取得错误')
            self.checkApiErrorBase(ret)  # 检查。非0则错误
            return ret
            # val = self.transformStr2Pos(ret)  #不需要，无{}，无需去除前后等
        return val

    '''
    def getCurrentJointBase_Dobot(self) -> List[float]:
        ret = self.dashboard.GetAngle()
        val = self.transformStr2Joint(ret)
        self.checkApiErrorBase(ret)
        return val

    def GetAngle_Dobot(self):
        """
        """
        string = "GetAngle()"
        self.send_data(string)
        return self.wait_reply()
    
    '''

    def getCurrentJointBase(self) -> List[float]:
        flag = 1  # 0 #0-阻塞，1-非阻塞
        # ret = self.dashboard.GetAngle()
        # ret,val = self.robot.GetActualJointPosDegree(flag)  #获取关节当前位置(角度)
        ret_val = self.robot.GetActualJointPosDegree(flag)  # 获取关节当前位置(角度)
        # 成功：[0,joint_pos],joint_pos=[j1,j2,j3,j4,j5,j6],  失败：[errcode,]
        ret = ret_val[0]
        if ret == 0:
            val = ret_val[1:7]  ###输出为0-6，7个数，注意ret_val【1】只是x
        else:
            print('JOG 位姿系取得错误')
            self.checkApiErrorBase(ret)  # 检查。非0则错误
            return ret
            # val = self.transformStr2Joint(ret)  #不需要，无{}，无需去除前后等
        return val

    '''
    def main2(self):   ##########1114 测试用,失败
        ######self init中多进程关闭状态，测试
        self.readyRobot()
        self.getFeedbackBase()
        ###### 第一个多进程
        feed_process = Process(target=self.getFeedbackBase)  #创建了feed_process进程，进程调用的是getFeedbackBase函数
        feed_process.daemon = True   #设置子进程属性 daemon 为 True 来使主进程运行完毕后子进程强制结束
                #每个进程修改全局变量后只能局部可见，虽然使用相同的名字，但是全局变量不共享
        feed_process.start()   #开始执行进程
        # self.mySleepBase(1)
        ###### 第二个多进程
        self.startMultiFeedbackBase()
    '''


class FairRobotApi(RobotApi):
    def __init__(self, ip, port, *args):
        self.ip = ip
        # self.port = port
        self.port = int(port)
        # self.socket_FairRobot = 0  ####1109  为何初值0，？ 整数初值可以吗？
        self.text_log: Text = None
        if args:
            self.text_log = args[0]

        if self.port == 8083:
            try:
                self.socket_FairRobot = socket.socket()
                self.socket_FairRobot.connect((self.ip, self.port))
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
        self.socket_FairRobot.send(str.encode(string, 'utf-8'))

    def wait_reply_old(self):
        """
        Read the return value
        """
        hasRead = 0

        data = bytes()
        while hasRead < 256:  # Fr3的反馈字节数241，凑为2的指数256,字节数不能为奇数
            # temp = self.feed.socket_FairRobot.recv(241 - hasRead)  ######1109 .feed 多余？  RobotApi调用时需要
            temp = self.socket_FairRobot.recv(256 - hasRead)
            if len(temp) > 0:
                hasRead += len(temp)
                data += temp
                # print(len(data))

        rob_stat = np.frombuffer(data, dtype=MyType)  # メモリのバイト列を直接読み込む,バッファーを配列(ndarray)に変換する,処理速度の高速化につながります。
        # data_str = str(data, encoding="utf-8")
        # self.log(f'Receive from 192.168.250.31:{self.port}: {data_str}')
        # return data_str
        return rob_stat

    def wait_reply_new(self):  #####1109
        sleep_t = 0.001
        # self.socket_FairRobot.connect((self.ip, self.port)) #####1114 不可重复连接。
        while True:
            rob_stat = self.socket_FairRobot.recv(256)
            RVV = []
            for i in range(2):
                RVV.append(hex(rob_stat[i]))
            if RVV[0:2] == ['0x5a', '0x5a'] or RVV[0:2] == ['0x5A', '0x5A']:  # 值可能会有错误，需要检查
                return rob_stat
            # print('值不正确',RVV)
            self.mySleepBase(sleep_t)

        # print(rob_stat)
        # self.socket_FairRobot.close()

    def wait_reply_new3(self):  #####1109  ## from 240108 no user
        sleep_t = 0.001
        # self.socket_FairRobot.connect((self.ip, self.port)) #####1114 不可重复连接。
        while True:
            rob_stat = self.socket_FairRobot.recv(256)
            RVV = []
            for i in range(2):
                RVV.append(hex(rob_stat[i]))

            if RVV[0:2] == ['0x5a', '0x5a'] or RVV[0:2] == ['0x5A', '0x5A']:  # 值可能会有错误，需要检查
                return rob_stat
            # print('值不正确',RVV)
            self.mySleepBase(sleep_t)

        # print(rob_stat)
        # self.socket_FairRobot.close()

    def wait_reply_new2(self):  #####1109  ## from 231114 no user
        self.socket_FairRobot.connect((self.ip, self.port))  #####1114 不可重复连接。--init--处连接注释掉是可以用此函数
        rob_stat = self.socket_FairRobot.recv(256)
        print(rob_stat)
        self.socket_FairRobot.close()
        return (rob_stat)

    def wait_reply(self):  #####1109 no use
        rob_stat = self.wait_reply_new()  #######1114 增加反馈
        # rob_stat=self.wait_reply_old()
        return rob_stat

    def close(self):
        """
        Close the port
        """
        if (self.socket_FairRobot != 0):
            self.socket_FairRobot.close()

    def __del__(self):
        self.close()


'''
def main(self):
    RobotApi.main2(self)
'''
if __name__ == '__main__':  ######为测试多进程。Window中只有在此中才不会出错
    # RobotApi.run2(RobotApi)    ####在此调用OK
    # RobotApi.main(RobotApi)   ####调用引数不对，不知为何
    node = RobotApi('192.168.250.121', 8083, '115200', '9011')  # 1114 8083 字符改为数值
    # main(node)   ##失败
    vel = 10.0
    # speed_g=80
    # ret=node.robot.SetSpeed(speed_g)  #再启动后变更有效
    for i in range(10):
        ret = node.MovL(467.547, 713.588, 480.0, 179.862, 0.156, -22.508, 0, 0, vel)
        ret = node.MovL(467.547, 713.588, 480.0, 179.862, 20.156, -22.508, 0, 0, vel)
        ret = node.MovL(467.547, 713.588, 480.0, 179.862, 0.156, -22.508, 0, 0, vel)
        ret = node.MovL(467.547, 613.588, 480.0, 179.862, 0.156, -22.508, 0, 0, vel)

    # def MovL(self, x: float, y: float, z: float, rx: float, ry: float, rz: float,tool_no: int,user_no: int, vel: float):   #加参数时，正常的顺序
    for ii in range(5):
        # ret=node.MovL(467.547, 713.588, 480.0, 179.862, 0.156, -22.508, 0,0,5.0)
        # sleep(1)
        # #ret=node.stopRobot()
        # sleep(2)
        print('--0-start-P1', speed_g, perf_counter())  # ,node.getCurrentPosBase())
        # print(node.robot.GetTargetTCPSpeed(1))
        # print(node.robot.GetActualTCPSpeed(1))
        ret = node.MovL(467.547, 713.588, 480.0, 179.862, 0.156, -22.508, 0, 0, vel)
        sleep(5)
        print('--1-1s-', speed_g, perf_counter())  # ,node.getCurrentPosBase())
        speed_g = int(speed_g / 2 + 2)
        speed_g = 10
        ret = node.robot.SetSpeed(speed_g)  # 再启动后变更有效
        sleep(0.1)
        print('--2-set speed -p1-', speed_g, perf_counter())  # ,node.getCurrentPosBase())
        ret = node.MovL(467.547, 713.588, 480.0, 179.862, 0.156, -25.508, 0, 0, vel)
        # print(node.robot.GetTargetTCPSpeed(1))
        # print(node.robot.GetActualTCPSpeed(1))
        sleep(1)
        print('--3-1s-', speed_g, perf_counter())  # ,node.getCurrentPosBase())

        print('--4-P2-', speed_g, perf_counter())  # ,node.getCurrentPosBase())
        ret = node.MovL(700.000, -159.000, 774.0, 180.0, 0.0, -90.0, 0, 0, vel)
        # print(node.robot.GetTargetTCPSpeed(1))
        # print(node.robot.GetActualTCPSpeed(1))
        sleep(1)
        speed_g = int(speed_g / 2 + 2)
        speed_g = 2
        ret = node.robot.SetSpeed(speed_g)  # 再启动后变更有效
        sleep(0.1)
        print('--5-1s speed P2-', speed_g, perf_counter())  # ,node.getCurrentPosBase())
        ret = node.MovL(700.000, -159.000, 774.01, 180.0, 0.0, -90.0, 0, 0, vel)
        # print(node.robot.GetTargetTCPSpeed(1))
        # print(node.robot.GetActualTCPSpeed(1))
        sleep(1)
        print('--6-1s -', speed_g, perf_counter())  # ,node.getCurrentPosBase())
        speed_g = int(speed_g / 2 + 2)
        speed_g = 20
        ret = node.robot.SetSpeed(speed_g)  # 再启动后变更有效
        sleep(0.1)
