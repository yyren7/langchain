はい、以下に翻訳結果を示します。

# dobot_robot

## 結果

### AccJ_api.json

サポートされていないファイル形式

### AccL_api.json

サポートされていないファイル形式

### Arch_api.json

サポートされていないファイル形式

### Arc_api.json

サポートされていないファイル形式

### CalcTool_api.json

サポートされていないファイル形式

### CalcUser_api.json

サポートされていないファイル形式

### Circle_api.json

サポートされていないファイル形式

### ClearError_api.json

サポートされていないファイル形式

### ContinueScript_api.json

サポートされていないファイル形式

### Continue_api.json

サポートされていないファイル形式

### CP_api.json

サポートされていないファイル形式

### DisableRobot_api.json

サポートされていないファイル形式

### DI_api.json

サポートされていないファイル形式

### dobot_api.py

### 内容

```python
import socket
import threading
from tkinter import Text, END
import datetime
import numpy as np
import os
import json

alarmControllerFile = "files/alarm_controller.json"
alarmServoFile = "files/alarm_servo.json"

# ポートフィードバック
MyType = np.dtype([('len', np.int16,),
                   ('Reserve', np.int16, (3,)),
                   ('digital_input_bits', np.int64,),
                   ('digital_outputs', np.int64,),
                   ('robot_mode', np.int64,),
                   ('controller_timer', np.int64,),
                   ('run_time', np.int64,),
                   ('test_value', np.int64,),
                   ('safety_mode', np.float64,),
                   ('speed_scaling', np.float64,),
                   ('linear_momentum_norm', np.float64,),
                   ('v_main', np.float64,),
                   ('v_robot', np.float64,),
                   ('i_robot', np.float64,),
                   ('program_state', np.float64,),
                   ('safety_status', np.float64,),
                   ('tool_accelerometer_values', np.float64, (3,)),
                   ('elbow_position', np.float64, (3,)),
                   ('elbow_velocity', np.float64, (3,)),
                   ('q_target', np.float64, (6,)),
                   ('qd_target', np.float64, (6,)),
                   ('qdd_target', np.float64, (6,)),
                   ('i_target', np.float64, (6,)),
                   ('m_target', np.float64, (6,)),
                   ('q_actual', np.float64, (6,)),
                   ('qd_actual', np.float64, (6,)),
                   ('i_actual', np.float64, (6,)),
                   ('i_control', np.float64, (6,)),
                   ('tool_vector_actual', np.float64, (6,)),
                   ('TCP_speed_actual', np.float64, (6,)),
                   ('TCP_force', np.float64, (6,)),
                   ('Tool_vector_target', np.float64, (6,)),
                   ('TCP_speed_target', np.float64, (6,)),
                   ('motor_temperatures', np.float64, (6,)),
                   ('joint_modes', np.float64, (6,)),
                   ('v_actual', np.float64, (6,)),
                   ('handtype', np.int8, (4,)),
                   ('userCoordinate', np.int8, (1,)),
                   ('toolCoordinate', np.int8, (1,)),
                   ('isRunQueuedCmd', np.int8, (1,)),
                   ('isPauseCmdFlag', np.int8, (1,)),
                   ('velocityRatio', np.int8, (1,)),
                   ('accelerationRatio', np.int8, (1,)),
                   ('jerkRatio', np.int8, (1,)),
                   ('xyzVelocityRatio', np.int8, (1,)),
                   ('rVelocityRatio', np.int8, (1,)),
                   ('xyzAccelerationRatio', np.int8, (1,)),
                   ('rAccelerationRatio', np.int8, (1,)),
                   ('xyzJerkRatio', np.int8, (1,)),
                   ('rJerkRatio', np.int8, (1,)),
                   ('BrakeStatus', np.int8, (1,)),
                   ('EnableStatus', np.int8, (1,)),
                   ('DragStatus', np.int8, (1,)),
                   ('RunningStatus', np.int8, (1,)),
                   ('ErrorStatus', np.int8, (1,)),
                   ('JogStatus', np.int8, (1,)),
                   ('RobotType', np.int8, (1,)),
                   ('DragButtonSignal', np.int8, (1,)),
                   ('EnableButtonSignal', np.int8, (1,)),
                   ('RecordButtonSignal', np.int8, (1,)),
                   ('ReappearButtonSignal', np.int8, (1,)),
                   ('JawButtonSignal', np.int8, (1,)),
                   ('SixForceOnline', np.int8, (1,)),  # 1037
                   ('Reserve2', np.int8, (82,)),
                   ('m_actual[6]', np.float64, (6,)),
                   ('load', np.float64, (1,)),
                   ('centerX', np.float64, (1,)),
                   ('centerY', np.float64, (1,)),
                   ('centerZ', np.float64, (1,)),
                   ('user', np.float64, (6,)),
                   ('tool', np.float64, (6,)),
                   ('traceIndex', np.int64,),
                   ('SixForceValue', np.int64, (6,)),
                   ('TargetQuaternion', np.float64, (4,)),
                   ('ActualQuaternion', np.float64, (4,)),
                   ('Reserve3', np.int8, (24,)),
                   ])


# コントローラーとサーボのアラームファイルを読み込む
def alarmAlarmJsonFile():
    currrntDirectory = os.path.dirname(__file__)
    jsonContrellorPath = os.path.join(currrntDirectory, alarmControllerFile)
    jsonServoPath = os.path.join(currrntDirectory, alarmServoFile)

    with open(jsonContrellorPath, encoding='utf-8') as f:
        dataController = json.load(f)
    with open(jsonServoPath, encoding='utf-8') as f:
        dataServo = json.load(f)
    return dataController, dataServo


class DobotApi:
    def __init__(self, ip, port, *args):
        self.ip = ip
        self.port = port
        self.socket_dobot = 0
        self.__globalLock = threading.Lock()
        self.text_log: Text = None
        if args:
            self.text_log = args[0]

        if self.port == 29999 or self.port == 30003 or self.port == 30004:
            try:
                self.socket_dobot = socket.socket()
                self.socket_dobot.connect((self.ip, self.port))
            except socket.error:
                print(socket.error)
                raise Exception(
                    f"ポート {self.port} を使用してソケット接続を設定できません！", socket.error)
        else:
            raise Exception(
                f"ダッシュボードサーバーに接続するには、ポート {self.port} を使用する必要があります！")

    def log(self, text):
        if self.text_log:
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ")
            self.text_log.insert(END, date + text + "\n")
        else:
            print(text)

    def send_data(self, string):
        try:
            self.log(f"{self.ip}:{self.port} に送信: {string}")
            self.socket_dobot.send(str.encode(string, 'utf-8'))
        except Exception as e:
            print(e)

    def wait_reply(self):
        """
    戻り値を読み取る
    """
        data = ""
        try:
            data = self.socket_dobot.recv(1024)
        except Exception as e:
            print(e)

        finally:
            if len(data) == 0:
                data_str = data
            else:
                data_str = str(data, encoding="utf-8")
                self.log(f'{self.ip}:{self.port} から受信: {data_str}')
            return data_str

    def close(self):
        """
    ポートを閉じる
    """
        if (self.socket_dobot != 0):
            self.socket_dobot.close()

    def sendRecvMsg(self, string):
        """
    送受信同期
    """
        with self.__globalLock:
            self.send_data(string)
            recvData = self.wait_reply()
            return recvData

    def __del__(self):
        self.close()


class DobotApiDashboard(DobotApi):
    """
  Dobotへの接続を確立するためのクラスdobot_api_dashboardを定義します
  """

    def EnableRobot(self, *dynParams):
        """
    ロボットを有効にする
    """
        string = "EnableRobot("
        for i in range(len(dynParams)):
            if i == len(dynParams) - 1:
                string = string + str(dynParams[i])
            else:
                string = string + str(dynParams[i]) + ","
        string = string + ")"
        return self.sendRecvMsg(string)

    def DisableRobot(self):
        """
    ロボットを無効にする
    """
        string = "DisableRobot()"
        return self.sendRecvMsg(string)

    def ClearError(self):
        """
    コントローラーのアラーム情報をクリアする
    """
        string = "ClearError()"
        return self.sendRecvMsg(string)

    def ResetRobot(self):
        """
    ロボットを停止する
    """
        string = "ResetRobot()"
        return self.sendRecvMsg(string)

    def SpeedFactor(self, speed):
        """
    グローバルレートを設定する
    speed:レート値（値の範囲：1〜100）
    """
        string = "SpeedFactor({:d})".format(speed)
        return self.sendRecvMsg(string)

    def User(self, index):
        """
    キャリブレーションされたユーザー座標系を選択する
    index : キャリブレーションされたユーザー座標のインデックス
    """
        string = "User({:d})".format(index)
        return self.sendRecvMsg(string)

    def Tool(self, index):
        """
    キャリブレーションされたツール座標系を選択する
    index : キャリブレーションされたツール座標のインデックス
    """
        string = "Tool({:d})".format(index)
        return self.sendRecvMsg(string)

    def RobotMode(self):
        """
    ロボットの状態を表示する
    """
        string = "RobotMode()"
        return self.sendRecvMsg(string)

    def PayLoad(self, weight, inertia):
        """
    ロボットの負荷を設定する
    weight : 負荷重量
    inertia: 負荷慣性モーメント
    """
        string = "PayLoad({:f},{:f})".format(weight, inertia)
        return self.sendRecvMsg(string)

    def DO(self, index, status):
        """
    デジタル信号出力を設定する（キュー命令）
    index : デジタル出力インデックス（値の範囲：1〜24）
    status : デジタル信号出力ポートの状態（0：ローレベル、1：ハイレベル）
    """
        string = "DO({:d},{:d})".format(index, status)
        return self.sendRecvMsg(string)

    def AccJ(self, speed):
        """
    ジョイント加速度比を設定する（MovJ、MovJIO、MovJR、JointMovJコマンドのみ）
    speed : ジョイント加速度比（値の範囲：1〜100）
    """
        string = "AccJ({:d})".format(speed)
        return self.sendRecvMsg(string)

    def AccL(self, speed):
        """
    座標系の加速度比を設定する（MovL、MovLIO、MovLR、Jump、Arc、Circleコマンドのみ）
    speed : 直交座標加速度比（値の範囲：1〜100）
    """
        string = "AccL({:d})".format(speed)
        return self.sendRecvMsg(string)

    def SpeedJ(self, speed):
        """
    ジョイント速度比を設定する（MovJ、MovJIO、MovJR、JointMovJコマンドのみ）
    speed : ジョイント速度比（値の範囲：1〜100）
    """
        string = "SpeedJ({:d})".format(speed)
        return self.sendRecvMsg(string)

    def SpeedL(self, speed):
        """
    直交座標加速度比を設定する（MovL、MovLIO、MovLR、Jump、Arc、Circleコマンドのみ）
    speed : 直交座標加速度比（値の範囲：1〜100）
    """
        string = "SpeedL({:d})".format(speed)
        return self.sendRecvMsg(string)

    def Arch(self, index):
        """
    ジャンプゲートパラメータインデックスを設定する（このインデックスには、開始点のリフト高さ、最大リフト高さ、終了点のドロップ高さが含まれます）
    index : パラメータインデックス（値の範囲：0〜9）
    """
        string = "Arch({:d})".format(index)
        return self.sendRecvMsg(string)

    def CP(self, ratio):
        """
    スムーズな遷移比を設定する
    ratio : スムーズな遷移比（値の範囲：1〜100）
    """
        string = "CP({:d})".format(ratio)
        return self.sendRecvMsg(string)

    def LimZ(self, value):
        """
    ドアタイプのパラメータの最大リフト高さを設定する
    value : 最大リフト高さ（高度に制限されています：マニピュレーターのz軸の制限位置を超えないでください）
    """
        string = "LimZ({:d})".format(value)
        return self.sendRecvMsg(string)

    def RunScript(self, project_name):
        """
    スクリプトファイルを実行する
    project_name ：スクリプトファイル名
    """
        string = "RunScript({:s})".format(project_name)
        return self.sendRecvMsg(string)

    def StopScript(self):
        """
    スクリプトを停止する
    """
        string = "StopScript()"
        return self.sendRecvMsg(string)

    def PauseScript(self):
        """
    スクリプトを一時停止する
    """
        string = "PauseScript()"
        return self.sendRecvMsg(string)

    def ContinueScript(self):
        """
    スクリプトの実行を継続する
    """
        string = "ContinueScript()"
        return self.sendRecvMsg(string)

    def GetHoldRegs(self, id, addr, count, type=None):
        """
    保持レジスタを読み取る
    id : セカンダリデバイス番号（最大5つのデバイスをサポートできます。値の範囲は0〜4です
        コントローラーの内部スレーブにアクセスする場合は0に設定します）
    addr : レジスタの開始アドレスを保持します（値の範囲：3095〜4095）
    count : 指定された数のデータ型を読み取ります（値の範囲：1〜16）
    type : データ型
        nullの場合、デフォルトで16ビット符号なし整数（2バイト、1レジスタを占有）が読み取られます
        "U16" : 16ビット符号なし整数（2バイト、1レジスタを占有）を読み取ります
        "U32" : 32ビット符号なし整数（4バイト、2レジスタを占有）を読み取ります
        "F32" : 32ビット単精度浮動小数点数（4バイト、2レジスタを占有）を読み取ります
        "F64" : 64ビット倍精度浮動小数点数（8バイト、4レジスタを占有）を読み取ります
    """
        if type is not None:
            string = "GetHoldRegs({:d},{:d},{:d},{:s})".format(
                id, addr, count, type)
        else:
            string = "GetHoldRegs({:d},{:d},{:d})".format(
                id, addr, count)
        return self.sendRecvMsg(string)

    def SetHoldRegs(self, id, addr, count, table, type=None):
        """
    保持レジスタを書き込む
    id : セカンダリデバイス番号（最大5つのデバイスをサポートできます。値の範囲は0〜4です
        コントローラーの内部スレーブにアクセスする場合は0に設定します）
    addr : レジスタの開始アドレスを保持します（値の範囲：3095〜4095）
    count : 指定された数のデータ型を書き込みます（値の範囲：1〜16）
    type : データ型
        nullの場合、デフォルトで16ビット符号なし整数（2バイト、1レジスタを占有）が読み取られます
        "U16" : 16ビット符号なし整数（2バイト、1レジスタを占有）を読み取ります
        "U32" : 32ビット符号なし整数（4バイト、2レジスタを占有）を読み取ります
        "F32" : 32ビット単精度浮動小数点数（4バイト、2レジスタを占有）を読み取ります
        "F64" : 64ビット倍精度浮動小数点数（8バイト、4レジスタを占有）を読み取ります
    """
        if type is not None:
            string = "SetHoldRegs({:d},{:d},{:d},{:d})".format(
                id, addr, count, table)
        else:
            string = "SetHoldRegs({:d},{:d},{:d},{:d},{:s})".format(
                id, addr, count, table, type)
        return self.sendRecvMsg(string)

    def GetErrorID(self):
        """
    ロボットのエラーコードを取得する
    """
        string = "GetErrorID()"
        return self.sendRecvMsg(string)

    def DOExecute(self, offset1, offset2):
        string = "DOExecute({:d},{:d}".format(offset1, offset2) + ")"
        return self.sendRecvMsg(string)

    def ToolDO(self, offset1, offset2):
        string = "ToolDO({:d},{:d}".format(offset1, offset2) + ")"
        return self.sendRecvMsg(string)

    def ToolDOExecute(self, offset1, offset2):
        string = "ToolDOExecute({:d},{:d}".format(offset1, offset2) + ")"
        return self.sendRecvMsg(string)

    def SetArmOrientation(self, offset1):
        string = "SetArmOrientation({:d}".format(offset1) + ")"
        return self.sendRecvMsg(string)

    def SetPayload(self, offset1, *dynParams):
        string = "SetPayload({:f}".format(
            offset1)
        for params in dynParams:
            string = string + "," + str(params) + ","
        string = string + ")"
        return self.sendRecvMsg(string)

    def PositiveSolution(self, offset1, offset2, offset3, offset4, user, tool):
        string = "PositiveSolution({:f},{:f},{:f},{:f},{:d},{:d}".format(offset1, offset2, offset3, offset4, user,
                                                                         tool) + ")"
        return self.sendRecvMsg(string)

    def InverseSolution(self, offset1, offset2, offset3, offset4, user, tool, *dynParams):
        string = "InverseSolution({:f},{:f},{:f},{:f},{:d},{:d}".format(offset1, offset2, offset3, offset4, user, tool)
        for params in dynParams:
            print(type(params), params)
            string = string + repr(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def SetCollisionLevel(self, offset1):
        string = "SetCollisionLevel({:d}".format(offset1) + ")"
        return self.sendRecvMsg(string)

    def GetAngle(self):
        string = "GetAngle()"
        return self.sendRecvMsg(string)

    def GetPose(self):
        string = "GetPose()"
        return self.sendRecvMsg(string)

    def EmergencyStop(self):
        string = "EmergencyStop()"
        return self.sendRecvMsg(string)

    def ModbusCreate(self, ip, port, slave_id, isRTU):
        string = "ModbusCreate({:s},{:d},{:d},{:d}".format(ip, port, slave_id, isRTU) + ")"
        return self.sendRecvMsg(string)

    def ModbusClose(self, offset1):
        string = "ModbusClose({:d}".format(offset1) + ")"
        return self.sendRecvMsg(string)

    def GetInBits(self, offset1, offset2, offset3):
        string = "GetInBits({:d},{:d},{:d}".format(offset1, offset2, offset3) + ")"
        return self.sendRecvMsg(string)

    def GetInRegs(self, offset1, offset2, offset3, *dynParams):
        string = "GetInRegs({:d},{:d},{:d}".format(offset1, offset2, offset3)
        for params in dynParams:
            print(type(params), params)
            string = string + params[0]
        string = string + ")"
        return self.sendRecvMsg(string)

    def GetCoils(self, offset1, offset2, offset3):
        string = "GetCoils({:d},{:d},{:d}".format(offset1, offset2, offset3) + ")"
        return self.sendRecvMsg(string)

    def SetCoils(self, offset1, offset2, offset3, offset4):
        string = "SetCoils({:d},{:d},{:d}".format(offset1, offset2, offset3) + "," + repr(offset4) + ")"
        print(str(offset4))
        return self.sendRecvMsg(string)

    def DI(self, offset1):
        string = "DI({:d}".format(offset1) + ")"
        return self.sendRecvMsg(string)

    def ToolDI(self, offset1):
        string = "DI({:d}".format(offset1) + ")"
        return self.sendRecvMsg(string)

    def DOGroup(self, *dynParams):
        string = "DOGroup("
        for params in dynParams:
            string = string + str(params) + ","
        string = string + ")"
        return self.wait_reply()

    def BrakeControl(self, offset1, offset2):
        string = "BrakeControl({:d},{:d}".format(offset1, offset2) + ")"
        return self.sendRecvMsg(string)

    def StartDrag(self):
        string = "StartDrag()"
        return self.sendRecvMsg(string)

    def StopDrag(self):
        string = "StopDrag()"
        return self.sendRecvMsg(string)

    def LoadSwitch(self, offset1):
        string = "LoadSwitch({:d}".format(offset1) + ")"
        return self.sendRecvMsg(string)

    def wait(self,t):
        string = "wait({:d}".format(t)+")"
        return self.sendRecvMsg(string)

    def pause(self):
        string = "pause()"
        return self.sendRecvMsg(string)

    def Continue(self):
        string = "continue()"
        return self.sendRecvMsg(string)


class DobotApiMove(DobotApi):
    """
  Dobotへの接続を確立するためのクラスdobot_api_moveを定義します
  """

    def MovJ(self, x, y, z, r, *dynParams):
        """
    ジョイントモーションインターフェース（点対点モーションモード）
    x: 直交座標系のxの数値
    y: 直交座標系のyの数値
    z: 直交座標系のzの数値
    r: 直交座標系のRの数値
    """
        string = "MovJ({:f},{:f},{:f},{:f}".format(
            x, y, z, r)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        print(string)
        return self.sendRecvMsg(string)

    def MovL(self, x, y, z, r, *dynParams):
        """
    座標系モーションインターフェース（直線モーションモード）
    x: 直交座標系のxの数値
    y: 直交座標系のyの数値
    z: 直交座標系のzの数値
    r: 直交座標系のRの数値
    """
        string = "MovL({:f},{:f},{:f},{:f}".format(
            x, y, z, r)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        print(string)
        return self.sendRecvMsg(string)

    def JointMovJ(self, j1, j2, j3, j4, *dynParams):
        """
    ジョイントモーションインターフェース（直線モーションモード）
    j1〜j6：各ジョイントの点位置の値
    """
        string = "JointMovJ({:f},{:f},{:f},{:f}".format(
            j1, j2, j3, j4)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        print(string)
        return self.sendRecvMsg(string)

    def Jump(self):
        print("未定")

    def RelMovJ(self, x, y, z, r, *dynParams):
        """
    オフセットモーションインターフェース（点対点モーションモード）
    j1〜j6：各ジョイントの点位置の値
    """
        string = "RelMovJ({:f},{:f},{:f},{:f}".format(
            x, y, z, r)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def RelMovL(self, offsetX, offsetY, offsetZ, offsetR, *dynParams):
        """
    オフセットモーションインターフェース（点対点モーションモード）
    x: 直交座標系のxのオフセット
    y: 直交座標系のyのオフセット
    z: 直交座標系のZのオフセット
    r: 直交座標系のRのオフセット
    """
        string = "RelMovL({:f},{:f},{:f},{:f}".format(offsetX, offsetY, offsetZ, offsetR)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def MovLIO(self, x, y, z, r, *dynParams):
        """
    直線移動中にデジタル出力ポートの状態を並行して設定する
    x: 直交座標系のxの数値
    y: 直交座標系のyの数値
    z: 直交座標系のzの数値
    r: 直交座標系のrの数値
    *dynParams :パラメータ設定（Mode、Distance、Index、Status）
                Mode :距離モードを設定します（0：距離パーセンテージ、1：開始点または目標点からの距離）
                Distance :指定された距離を実行します（Modeが0の場合、値の範囲は0〜100です。Modeが1の場合、値が正の場合、
                         開始点からの距離を示します。Distanceの値が負の場合、目標点からの距離を表します）
                Index ：デジタル出力インデックス（値の範囲：1〜24）
                Status ：デジタル出力状態（値の範囲：0/1）
    """
        # 例： MovLIO(0,50,0,0,0,0,(0,50,1,0),(1,1,2,1))
        string = "MovLIO({:f},{:f},{:f},{:f}".format(
            x, y, z, r)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def MovJIO(self, x, y, z, r, *dynParams):
        """
    点対点モーション中にデジタル出力ポートの状態を並行して設定する
    x: 直交座標系のxの数値
    y: 直交座標系のyの数値
    z: 直交座標系のzの数値
    r: 直交座標系のrの数値
    *dynParams :パラメータ設定（Mode、Distance、Index、Status）
                Mode :距離モードを設定します（0：距離パーセンテージ、1：開始点または目標点からの距離）
                Distance :指定された距離を実行します（Modeが0の場合、値の範囲は0〜100です。Modeが1の場合、値が正の場合、
                         開始点からの距離を示します。Distanceの値が負の場合、目標点からの距離を表します）
                Index ：デジタル出力インデックス（値の範囲：1〜24）
                Status ：デジタル出力状態（値の範囲：0/1）
    """
        # 例： MovJIO(0,50,0,0,0,0,(0,50,1,0),(1,1,2,1))
        string = "MovJIO({:f},{:f},{:f},{:f}".format(
            x, y, z, r)
        self.log("192.168.1.6:29999 に送信:" + string)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        print(string)
        return self.sendRecvMsg(string)

    def Arc(self, x1, y1, z1, r1, x2, y2, z2, r2, *dynParams):
        """
    円弧モーション命令
    x1, y1, z1, r1 :中間点座標の点値
    x2, y2, z2, r2 :終点座標の値
    注：この命令は、他の移動命令と組み合わせて使用する必要があります
    """
        string = "Arc({:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f}".format(
            x1, y1, z1, r1, x2, y2, z2, r2)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        print(string)
        return self.sendRecvMsg(string)

    def Circle(self, x1, y1, z1, r1, x2, y2, z2, r2, count, *dynParams):
        """
    全円モーションコマンド
    count：実行ラップ数
    x1, y1, z1, r1 :中間点座標の点値
    x2, y2, z2, r2 :終点座標の値
    注：この命令は、他の移動命令と組み合わせて使用する必要があります
    """
        string = "Circle({:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:d}".format(
            x1, y1, z1, r1, x2, y2, z2, r2, count)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def MoveJog(self, axis_id=None, *dynParams):
        """
    ジョイントモーション
    axis_id: ジョイントモーション軸、オプションの文字列値：
        J1+ J2+ J3+ J4+ J5+ J6+
        J1- J2- J3- J4- J5- J6-
        X+ Y+ Z+ Rx+ Ry+ Rz+
        X- Y- Z- Rx- Ry- Rz-
    *dynParams: パラメータ設定（coord_type、user_index、tool_index）
                coord_type: 1：ユーザー座標 2：ツール座標（デフォルト値は1）
                user_index: ユーザーインデックスは0〜9です（デフォルト値は0）
                tool_index: ツールインデックスは0〜9です（デフォルト値は0）
    """
        if axis_id is not None:
            string = "MoveJog({:s}".format(axis_id)
        else:
            string = "MoveJog("
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def Sync(self):
        """
    ブロッキングプログラムはキュー命令を実行し、すべてのキュー命令が