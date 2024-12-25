
# dobot_robot

## result

### AccJ_api.json

Unsupported file type

### AccL_api.json

Unsupported file type

### Arch_api.json

Unsupported file type

### Arc_api.json

Unsupported file type

### CalcTool_api.json

Unsupported file type

### CalcUser_api.json

Unsupported file type

### Circle_api.json

Unsupported file type

### ClearError_api.json

Unsupported file type

### ContinueScript_api.json

Unsupported file type

### Continue_api.json

Unsupported file type

### CP_api.json

Unsupported file type

### DisableRobot_api.json

Unsupported file type

### DI_api.json

Unsupported file type

### dobot_api.py

### content

import socket
import threading
from tkinter import Text, END
import datetime
import numpy as np
import os
import json

alarmControllerFile = "files/alarm_controller.json"
alarmServoFile = "files/alarm_servo.json"

# Port Feedback
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


# 读取控制器和伺服告警文件
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
        try:
            self.log(f"Send to {self.ip}:{self.port}: {string}")
            self.socket_dobot.send(str.encode(string, 'utf-8'))
        except Exception as e:
            print(e)

    def wait_reply(self):
        """
    Read the return value
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
                self.log(f'Receive from {self.ip}:{self.port}: {data_str}')
            return data_str

    def close(self):
        """
    Close the port
    """
        if (self.socket_dobot != 0):
            self.socket_dobot.close()

    def sendRecvMsg(self, string):
        """
    send-recv Sync
    """
        with self.__globalLock:
            self.send_data(string)
            recvData = self.wait_reply()
            return recvData

    def __del__(self):
        self.close()


class DobotApiDashboard(DobotApi):
    """
  Define class dobot_api_dashboard to establish a connection to Dobot
  """

    def EnableRobot(self, *dynParams):
        """
    Enable the robot
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
    Disabled the robot
    """
        string = "DisableRobot()"
        return self.sendRecvMsg(string)

    def ClearError(self):
        """
    Clear controller alarm information
    """
        string = "ClearError()"
        return self.sendRecvMsg(string)

    def ResetRobot(self):
        """
    Robot stop
    """
        string = "ResetRobot()"
        return self.sendRecvMsg(string)

    def SpeedFactor(self, speed):
        """
    Setting the Global rate
    speed:Rate value(Value range:1~100)
    """
        string = "SpeedFactor({:d})".format(speed)
        return self.sendRecvMsg(string)

    def User(self, index):
        """
    Select the calibrated user coordinate system
    index : Calibrated index of user coordinates
    """
        string = "User({:d})".format(index)
        return self.sendRecvMsg(string)

    def Tool(self, index):
        """
    Select the calibrated tool coordinate system
    index : Calibrated index of tool coordinates
    """
        string = "Tool({:d})".format(index)
        return self.sendRecvMsg(string)

    def RobotMode(self):
        """
    View the robot status
    """
        string = "RobotMode()"
        return self.sendRecvMsg(string)

    def PayLoad(self, weight, inertia):
        """
    Setting robot load
    weight : The load weight
    inertia: The load moment of inertia
    """
        string = "PayLoad({:f},{:f})".format(weight, inertia)
        return self.sendRecvMsg(string)

    def DO(self, index, status):
        """
    Set digital signal output (Queue instruction)
    index : Digital output index (Value range:1~24)
    status : Status of digital signal output port(0:Low level，1:High level
    """
        string = "DO({:d},{:d})".format(index, status)
        return self.sendRecvMsg(string)

    def AccJ(self, speed):
        """
    Set joint acceleration ratio (Only for MovJ, MovJIO, MovJR, JointMovJ commands)
    speed : Joint acceleration ratio (Value range:1~100)
    """
        string = "AccJ({:d})".format(speed)
        return self.sendRecvMsg(string)

    def AccL(self, speed):
        """
    Set the coordinate system acceleration ratio (Only for MovL, MovLIO, MovLR, Jump, Arc, Circle commands)
    speed : Cartesian acceleration ratio (Value range:1~100)
    """
        string = "AccL({:d})".format(speed)
        return self.sendRecvMsg(string)

    def SpeedJ(self, speed):
        """
    Set joint speed ratio (Only for MovJ, MovJIO, MovJR, JointMovJ commands)
    speed : Joint velocity ratio (Value range:1~100)
    """
        string = "SpeedJ({:d})".format(speed)
        return self.sendRecvMsg(string)

    def SpeedL(self, speed):
        """
    Set the cartesian acceleration ratio (Only for MovL, MovLIO, MovLR, Jump, Arc, Circle commands)
    speed : Cartesian acceleration ratio (Value range:1~100)
    """
        string = "SpeedL({:d})".format(speed)
        return self.sendRecvMsg(string)

    def Arch(self, index):
        """
    Set the Jump gate parameter index (This index contains: start point lift height, maximum lift height, end point drop height)
    index : Parameter index (Value range:0~9)
    """
        string = "Arch({:d})".format(index)
        return self.sendRecvMsg(string)

    def CP(self, ratio):
        """
    Set smooth transition ratio
    ratio : Smooth transition ratio (Value range:1~100)
    """
        string = "CP({:d})".format(ratio)
        return self.sendRecvMsg(string)

    def LimZ(self, value):
        """
    Set the maximum lifting height of door type parameters
    value : Maximum lifting height (Highly restricted:Do not exceed the limit position of the z-axis of the manipulator)
    """
        string = "LimZ({:d})".format(value)
        return self.sendRecvMsg(string)

    def RunScript(self, project_name):
        """
    Run the script file
    project_name ：Script file name
    """
        string = "RunScript({:s})".format(project_name)
        return self.sendRecvMsg(string)

    def StopScript(self):
        """
    Stop scripts
    """
        string = "StopScript()"
        return self.sendRecvMsg(string)

    def PauseScript(self):
        """
    Pause the script
    """
        string = "PauseScript()"
        return self.sendRecvMsg(string)

    def ContinueScript(self):
        """
    Continue running the script
    """
        string = "ContinueScript()"
        return self.sendRecvMsg(string)

    def GetHoldRegs(self, id, addr, count, type=None):
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
        if type is not None:
            string = "GetHoldRegs({:d},{:d},{:d},{:s})".format(
                id, addr, count, type)
        else:
            string = "GetHoldRegs({:d},{:d},{:d})".format(
                id, addr, count)
        return self.sendRecvMsg(string)

    def SetHoldRegs(self, id, addr, count, table, type=None):
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
        if type is not None:
            string = "SetHoldRegs({:d},{:d},{:d},{:d})".format(
                id, addr, count, table)
        else:
            string = "SetHoldRegs({:d},{:d},{:d},{:d},{:s})".format(
                id, addr, count, table, type)
        return self.sendRecvMsg(string)

    def GetErrorID(self):
        """
    Get robot error code
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
  Define class dobot_api_move to establish a connection to Dobot
  """

    def MovJ(self, x, y, z, r, *dynParams):
        """
    Joint motion interface (point-to-point motion mode)
    x: A number in the Cartesian coordinate system x
    y: A number in the Cartesian coordinate system y
    z: A number in the Cartesian coordinate system z
    r: A number in the Cartesian coordinate system R
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
    Coordinate system motion interface (linear motion mode)
    x: A number in the Cartesian coordinate system x
    y: A number in the Cartesian coordinate system y
    z: A number in the Cartesian coordinate system z
    r: A number in the Cartesian coordinate system R
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
    Joint motion interface (linear motion mode)
    j1~j6:Point position values on each joint
    """
        string = "JointMovJ({:f},{:f},{:f},{:f}".format(
            j1, j2, j3, j4)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        print(string)
        return self.sendRecvMsg(string)

    def Jump(self):
        print("待定")

    def RelMovJ(self, x, y, z, r, *dynParams):
        """
    Offset motion interface (point-to-point motion mode)
    j1~j6:Point position values on each joint
    """
        string = "RelMovJ({:f},{:f},{:f},{:f}".format(
            x, y, z, r)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def RelMovL(self, offsetX, offsetY, offsetZ, offsetR, *dynParams):
        """
    Offset motion interface (point-to-point motion mode)
    x: Offset in the Cartesian coordinate system x
    y: offset in the Cartesian coordinate system y
    z: Offset in the Cartesian coordinate system Z
    r: Offset in the Cartesian coordinate system R
    """
        string = "RelMovL({:f},{:f},{:f},{:f}".format(offsetX, offsetY, offsetZ, offsetR)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def MovLIO(self, x, y, z, r, *dynParams):
        """
    Set the digital output port state in parallel while moving in a straight line
    x: A number in the Cartesian coordinate system x
    y: A number in the Cartesian coordinate system y
    z: A number in the Cartesian coordinate system z
    r: A number in the Cartesian coordinate system r
    *dynParams :Parameter Settings（Mode、Distance、Index、Status）
                Mode :Set Distance mode (0: Distance percentage; 1: distance from starting point or target point)
                Distance :Runs the specified distance（If Mode is 0, the value ranges from 0 to 100；When Mode is 1, if the value is positive,
                         it indicates the distance from the starting point. If the value of Distance is negative, it represents the Distance from the target point）
                Index ：Digital output index （Value range：1~24）
                Status ：Digital output state（Value range：0/1）
    """
        # example： MovLIO(0,50,0,0,0,0,(0,50,1,0),(1,1,2,1))
        string = "MovLIO({:f},{:f},{:f},{:f}".format(
            x, y, z, r)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def MovJIO(self, x, y, z, r, *dynParams):
        """
    Set the digital output port state in parallel during point-to-point motion
    x: A number in the Cartesian coordinate system x
    y: A number in the Cartesian coordinate system y
    z: A number in the Cartesian coordinate system z
    r: A number in the Cartesian coordinate system r
    *dynParams :Parameter Settings（Mode、Distance、Index、Status）
                Mode :Set Distance mode (0: Distance percentage; 1: distance from starting point or target point)
                Distance :Runs the specified distance（If Mode is 0, the value ranges from 0 to 100；When Mode is 1, if the value is positive,
                         it indicates the distance from the starting point. If the value of Distance is negative, it represents the Distance from the target point）
                Index ：Digital output index （Value range：1~24）
                Status ：Digital output state（Value range：0/1）
    """
        # example： MovJIO(0,50,0,0,0,0,(0,50,1,0),(1,1,2,1))
        string = "MovJIO({:f},{:f},{:f},{:f}".format(
            x, y, z, r)
        self.log("Send to 192.168.1.6:29999:" + string)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        print(string)
        return self.sendRecvMsg(string)

    def Arc(self, x1, y1, z1, r1, x2, y2, z2, r2, *dynParams):
        """
    Circular motion instruction
    x1, y1, z1, r1 :Is the point value of intermediate point coordinates
    x2, y2, z2, r2 :Is the value of the end point coordinates
    Note: This instruction should be used together with other movement instructions
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
    Full circle motion command
    count：Run laps
    x1, y1, z1, r1 :Is the point value of intermediate point coordinates
    x2, y2, z2, r2 :Is the value of the end point coordinates
    Note: This instruction should be used together with other movement instructions
    """
        string = "Circle({:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:d}".format(
            x1, y1, z1, r1, x2, y2, z2, r2, count)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def MoveJog(self, axis_id=None, *dynParams):
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
    The blocking program executes the queue instruction and returns after all the queue instructions are executed
    """
        string = "Sync()"
        return self.sendRecvMsg(string)

    def RelMovJUser(self, offset_x, offset_y, offset_z, offset_r, user, *dynParams):
        """
    The relative motion command is carried out along the user coordinate system, and the end motion mode is joint motion
    offset_x: X-axis direction offset
    offset_y: Y-axis direction offset
    offset_z: Z-axis direction offset
    offset_r: R-axis direction offset

    user: Select the calibrated user coordinate system, value range: 0 ~ 9
    *dynParams: parameter Settings（speed_j, acc_j, tool）
                speed_j: Set joint speed scale, value range: 1 ~ 100
                acc_j: Set acceleration scale value, value range: 1 ~ 100
                tool: Set tool coordinate system index
    """
        string = "RelMovJUser({:f},{:f},{:f},{:f}, {:d}".format(
            offset_x, offset_y, offset_z, offset_r, user)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def RelMovLUser(self, offset_x, offset_y, offset_z, offset_r, user, *dynParams):
        """
    The relative motion command is carried out along the user coordinate system, and the end motion mode is linear motion
    offset_x: X-axis direction offset
    offset_y: Y-axis direction offset
    offset_z: Z-axis direction offset
    offset_r: R-axis direction offset
    user: Select the calibrated user coordinate system, value range: 0 ~ 9
    *dynParams: parameter Settings（speed_l, acc_l, tool）
                speed_l: Set Cartesian speed scale, value range: 1 ~ 100
                acc_l: Set acceleration scale value, value range: 1 ~ 100
                tool: Set tool coordinate system index
    """
        string = "RelMovLUser({:f},{:f},{:f},{:f}, {:d}".format(
            offset_x, offset_y, offset_z, offset_r, user)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def RelJointMovJ(self, offset1, offset2, offset3, offset4, *dynParams):
        """
    The relative motion command is carried out along the joint coordinate system of each axis, and the end motion mode is joint motion
    Offset motion interface (point-to-point motion mode)
    j1~j6:Point position values on each joint
    *dynParams: parameter Settings（speed_j, acc_j, user）
                speed_j: Set Cartesian speed scale, value range: 1 ~ 100
                acc_j: Set acceleration scale value, value range: 1 ~ 100
    """
        string = "RelJointMovJ({:f},{:f},{:f},{:f}".format(
            offset1, offset2, offset3, offset4)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def MovJExt(self, offset1, *dynParams):
        string = "MovJExt({:f}".format(
            offset1)
        for params in dynParams:
            string = string + "," + str(params)
        string = string + ")"
        return self.sendRecvMsg(string)

    def SyncAll(self):
        string = "SyncAll()"
        return self.sendRecvMsg(string)



### analysis

This code defines a Python API for controlling a Dobot robot, encompassing both dashboard and motion functionalities. It uses socket communication to send commands and receive responses. The API includes classes for managing connections, sending commands, and handling data. It also defines data structures for robot feedback and includes functions for reading alarm configurations from JSON files. The API supports various robot control commands, including enabling/disabling, motion control (joint and linear), I/O manipulation, and more.


### DOExecute_api.json

Unsupported file type

### DOGroup_api.json

Unsupported file type

### DO_api.json

Unsupported file type

### EmergencyStop_api.json

Unsupported file type

### EnableRobot_api.json

Unsupported file type

### GetAngle_api.json

Unsupported file type

### GetCoils_api.json

Unsupported file type

### GetErrorID_api.json

Unsupported file type

### GetHoldRegs_api.json

Unsupported file type

### GetInBits_api.json

Unsupported file type

### GetInRegs_api.json

Unsupported file type

### GetPalletPose_api.json

Unsupported file type

### GetPose_api.json

Unsupported file type

### InverseSolution_api.json

Unsupported file type

### JointMovJ_api.json

Unsupported file type

### ModbusClose_api.json

Unsupported file type

### ModbusCreate_api.json

Unsupported file type

### MoveJog_api.json

Unsupported file type

### MovJExt_api.json

Unsupported file type

### MovJIO_api.json

Unsupported file type

### MovJ_api.json

Unsupported file type

### MovLIO_api.json

Unsupported file type

### MovL_api.json

Unsupported file type

### PalletCreate_api.json

Unsupported file type

### PauseScript_api.json

Unsupported file type

### Pause_api.json

Unsupported file type

### PositiveSolution_api.json

Unsupported file type

### RelJointMovJ_api.json

Unsupported file type

### RelMovJUser_api.json

Unsupported file type

### RelMovLUser_api.json

Unsupported file type

### ResetRobot_api.json

Unsupported file type

### result_mg400_2.py

### content


from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot(ip):
    dashboard_p = DobotApiDashboard(ip, 29999)
    move_p = DobotApiMove(ip, 30003)
    feed_p = DobotApi(ip, 30004)
    return dashboard_p, move_p, feed_p

def move_to_position(move_p, position):
    move_p.MovJ(position[0], position[1], position[2], position[3])

def move_down_and_back(move_p, position, offset):
    move_p.MovL(position[0], position[1], position[2] - offset, position[3])
    time.sleep(1)  # Wait for the robot to move down
    move_p.MovL(position[0], position[1], position[2], position[3])
    time.sleep(1)  # Wait for the robot to move back

def main():
    ip = "192.168.250.101"
    pos_start = [284, 4, 90, -43]
    pos_end = [280, 104, 80, -23]
    offset = 10  # Offset in cm for the gripper movement

    dashboard_p, move_p, feed_p = connect_robot(ip)

    try:
        # Start the robot
        dashboard_p.EnableRobot()
        time.sleep(2)  # Wait for the robot to start

        while True:
            # Move to the start position
            move_to_position(move_p, pos_start)
            time.sleep(2)  # Wait for the robot to reach the start position

            # Move down to catch the object and then move back
            move_down_and_back(move_p, pos_start, offset)
            print("catch_ok")

            # Move to the end position
            move_to_position(move_p, pos_end)
            time.sleep(2)  # Wait for the robot to reach the end position

            # Move down to place the object and then move back
            move_down_and_back(move_p, pos_end, offset)
            print("place_ok")

    finally:
        # Stop the robot
        dashboard_p.DisableRobot()
        time.sleep(2)  # Wait for the robot to stop

if __name__ == "__main__":
    main()


### analysis

This Python script controls a Dobot robot arm. It establishes a connection, then moves the arm between two defined positions (`pos_start` and `pos_end`). At each position, the arm moves down by a specified offset, pauses, and then returns to the original height, simulating a pick-and-place action. The script includes error handling to ensure the robot is disabled upon completion or interruption. The robot continuously repeats this pick-and-place cycle.


### result_mg400_3.py

### content


from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot():
    ip = "192.168.250.101"
    dashboard_p = DobotApiDashboard(ip, 29999)
    move_p = DobotApiMove(ip, 30003)
    feed_p = DobotApi(ip, 30004)
    return dashboard_p, move_p, feed_p

def move_to_position(move_p, position):
    move_p.MovJ(position[0], position[1], position[2], position[3])

def main():
    dashboard_p, move_p, feed_p = connect_robot()
    
    # 启动机器人
    dashboard_p.EnableRobot()
    time.sleep(2)

    pos_start = [284, 4, 90, -43]
    pos_end = [280, 104, 80, -23]
    DO = 1

    while True:
        # 移动到抓取开始位置（实际抓取位置上方10cm）
        move_to_position(move_p, [pos_start[0], pos_start[1], pos_start[2] + 10, pos_start[3]])
        
        # 向下移动10cm并启动数字输出
        move_to_position(move_p, pos_start)
        dashboard_p.DO(DO, 1)
        
        # 后退
        move_to_position(move_p, [pos_start[0], pos_start[1], pos_start[2] + 10, pos_start[3]])
        
        # 移动到放置位置
        move_to_position(move_p, pos_end)
        
        # 关闭数字输出
        dashboard_p.DO(DO, 0)
        
        # 返回字符串“任务完成”
        print("任务完成")

    # 关闭机器人
    dashboard_p.DisableRobot()

if __name__ == "__main__":
    main()


### analysis

This Python script controls a Dobot robot arm. It establishes a connection, enables the robot, and then enters a loop to perform a pick-and-place operation. The robot moves to a start position, activates a digital output, moves to an end position, deactivates the output, and repeats. The script includes functions for connecting to the robot and moving to specified positions. It also prints "任务完成" after each cycle. Finally, it disables the robot after the loop.


### result_mg400_4.py

### content


from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove
import time

def connect_robot():
    dashboard_p = DobotApiDashboard('192.168.250.101', 29999)
    move_p = DobotApiMove('192.168.250.101', 30003)
    feed_p = DobotApi('192.168.250.101', 30004)
    return dashboard_p, move_p, feed_p

def move_to_position(move_p, position):
    move_p.MovJ(position[0], position[1], position[2], position[3])

def main():
    dashboard_p, move_p, feed_p = connect_robot()
    
    # 启动机器人
    dashboard_p.EnableRobot()
    time.sleep(2)

    pos_start = [284, 4, 0, -43]
    pos_end = [158, 234, 86, 21]
    DO = 1

    for _ in range(10):
        # 计算抓取的开始坐标（实际抓取坐标的上方20cm）
        pick_start = pos_start.copy()
        pick_start[2] += 20

        # 先到达抓取开始坐标
        move_to_position(move_p, pick_start)
        time.sleep(1)

        # 向正方向下移10cm
        pick_start[2] -= 10
        move_to_position(move_p, pick_start)
        time.sleep(1)

        # 启动指定数字输出
        dashboard_p.DO(DO, 1)
        time.sleep(1)

        # 再上升20cm
        pick_start[2] += 20
        move_to_position(move_p, pick_start)
        time.sleep(1)

        # 移动到放置坐标
        move_to_position(move_p, pos_end)
        time.sleep(1)

        # 关闭指定数字输出
        dashboard_p.DO(DO, 0)
        time.sleep(1)

    # 关闭机器人
    dashboard_p.DisableRobot()

    return "任务完成"

if __name__ == "__main__":
    result = main()
    print(result)


### analysis

This script controls a Dobot robot to perform a pick-and-place task. It connects to the robot, enables it, and then executes a loop 10 times. In each loop, the robot moves to a pick position, activates a digital output to simulate gripping, moves to a place position, and deactivates the output. Finally, the robot is disabled. The script uses `DobotApiDashboard`, `DobotApiMove`, and `DobotApi` for control and includes delays for smooth operation.


### RobotMode_api.json

Unsupported file type

### RunScript_api.json

Unsupported file type

### SetArmOrientation_api.json

Unsupported file type

### SetCoils_api.json

Unsupported file type

### SetCollisionLevel_api.json

Unsupported file type

### SetHoldRegs_api.json

Unsupported file type

### SetPayLoad_api.json

Unsupported file type

### SetTool_api.json

Unsupported file type

### SetUser_api.json

Unsupported file type

### SpeedFactor_api.json

Unsupported file type

### SpeedJ_api.json

Unsupported file type

### SpeedL_api.json

Unsupported file type

### StartDrag_api.json

Unsupported file type

### StopDrag_api.json

Unsupported file type

### StopScript_api.json

Unsupported file type

### SyncAll_api.json

Unsupported file type

### Sync_api.json

Unsupported file type

### ToolDI_api.json

Unsupported file type

### ToolDOExecute_api.json

Unsupported file type

### ToolDO_api.json

Unsupported file type

### Tool_api.json

Unsupported file type

### User_api.json

Unsupported file type

### Wait_api.json

Unsupported file type

## result\__pycache__

### dobot_api.cpython-39.pyc

Unsupported file type

### result_mg400_2.cpython-39.pyc

Unsupported file type
