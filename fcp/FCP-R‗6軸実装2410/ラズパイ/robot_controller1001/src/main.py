# -*- coding : UTF-8 -*-

import sys
import os
import time
from typing import List
import copy
from time import sleep, perf_counter


# For multiprocess
from multiprocessing import Process, Value, Array
import ctypes

# To read setting file
import configparser

# To read api file
import importlib

# To read setting
from setting import (
    PROGRAM_VERSION_MAJOR,
    PROGRAM_VERSION_MINOR,
    PROGRAM_VERSION_PATCH,
    X, Y, Z, RX, RY, RZ,
    SETTING_PATH,
    SETTING_NAME,
    API_PATH,
    PLC_PATH,
    COMM_MODULE,
    ADDR_MODULE,
    ADDRESS_FILE
)


class RobotController:
    def __init__(self):
        #############################################################
        # カレントディレクトリパス取得＆追加
        #############################################################
        self.current_dir = os.path.dirname(
            os.path.abspath(os.path.dirname(__file__)))
        sys.path.append(self.current_dir)

        #############################################################
        # PLC 通信 APIをimport
        #############################################################
        sys.path.append(self.current_dir + PLC_PATH)
        comm_module = importlib.import_module(COMM_MODULE)
        self.plc_api = comm_module.BasePLC()

        #############################################################
        # PLC アドレス取得 APIをimport
        #############################################################
        sys.path.append(self.current_dir + PLC_PATH)
        addr_module = importlib.import_module(ADDR_MODULE)
        self.g_set = addr_module
        self.readPlcSheet()
        #############################################################
        # PLCプロセスと通信用変数定義
        #############################################################
        # self.flag = Value(ctypes.c_bool, 0)
        # self.array = Array(ctypes.c_uint16, 4)
        self.r_bin = Array("i", [0 for i in range(int(self.RANGE["IN_W"]))])
        self.r_word = Array("i", [0 for i in range(int(self.RANGE["IN_D"]))])
        self.tmp_r_bin = Array(
            "i", [0 for i in range(int(self.RANGE["IN_W"]))])
        self.tmp_r_word = Array(
            "i", [0 for i in range(int(self.RANGE["IN_D"]))])
        self.main_previous_r_bin = [0 for i in range(int(self.RANGE["IN_W"]))]
        self.main_previous_r_word = [0 for i in range(int(self.RANGE["IN_D"]))]
        self.sub_previous_r_bin = [0 for i in range(int(self.RANGE["IN_W"]))]
        self.sub_previous_r_word = [0 for i in range(int(self.RANGE["IN_D"]))]

        self.w_bin = Array("i", [0 for i in range(int(self.RANGE["OUT_W"]))])
        self.w_word = Array("i", [0 for i in range(int(self.RANGE["OUT_D"]))])
        self.tmp_w_bin = Array(
            "i", [0 for i in range(int(self.RANGE["OUT_W"]))])
        self.tmp_w_word = Array(
            "i", [0 for i in range(int(self.RANGE["OUT_D"]))])
        self.main_previous_w_bin = [0 for i in range(int(self.RANGE["OUT_W"]))]
        self.main_previous_w_word = [
            0 for i in range(int(self.RANGE["OUT_D"]))]
        self.sub_previous_w_bin = [0 for i in range(int(self.RANGE["OUT_W"]))]
        self.sub_previous_w_word = [0 for i in range(int(self.RANGE["OUT_D"]))]
        #############################################################
        # 内部パラメータリセット
        #############################################################
        self.resetParam()
        self.previous_time = 0.0
        self.tmp_time = 0.0

    # def __del__(self):
    #     self.terminate()

    #############################################################
    # 準備関連
    #############################################################
    # NOTE:割付アドレスファイルを読み込む

    def readPlcSheet(self):
        print("Start to get plc setting parameter.")
        xlsx_file = self.current_dir + SETTING_PATH + ADDRESS_FILE
        self.RANGE = self.g_set.getParamDict(
            book_name=xlsx_file, sheet_name="RANGE")
        self.IN_W = self.g_set.getWdataDict(
            book_name=xlsx_file, sheet_name="IN_W")
        self.IN_D = self.g_set.getDdataDict(
            book_name=xlsx_file, sheet_name="IN_D")
        self.OUT_W = self.g_set.getWdataDict(
            book_name=xlsx_file, sheet_name="OUT_W")
        self.OUT_D = self.g_set.getDdataDict(
            book_name=xlsx_file, sheet_name="OUT_D")
        # NOTE:アドレスを取得
        self.IN_D_AD = self.getAddressDIn()
        self.OUT_D_AD = self.getAddressDOut()
        self.IN_W_AD = self.getAddressWIn()
        self.OUT_W_AD = self.getAddressWOut()
        # print("excel_file",xlsx_file)
        # print("RANGE",self.RANGE)
        # print("IN_W",self.IN_W)
        # print("IN_D",self.IN_D)
        # print("OUT_D",self.OUT_D)
        print("Got plc setting parameter completely.")

    # NOTE:内部パラメータを初期化
    def resetParam(self):
        print("Reset internal Parameter")
        # NOTE:内部フラグ
        self.in_flag = {"STOP": False, "BUSY_CHECK": False, "INITIAL": False, "MOVE": False,
                        "MOVING": False, "OPERATING": False, "ORIGIN": False, "REQ_MOVE_UP": False, "ONLINE_CHK": False}
        # NOTE:内部フェーズ
        self.in_phase = {"MOVE": 0, "ORIGIN": 0, "ROBOT_STATUS": "INIT",
                         "BUSY_CHECK_TIME": 0.0, "DEBUG": "ABCDEFG"}
        # NOTE:前周期の内部フラグ
        self.previous_in_flag = self.in_flag.copy()
        # NOTE:前周期の内部フェーズ
        self.previous_in_phase = self.in_phase.copy()

        self.r_bin[:] = [0 for i in range(int(self.RANGE["IN_W"]))]
        self.r_word[:] = [0 for i in range(int(self.RANGE["IN_D"]))]
        self.tmp_r_bin[:] = [0 for i in range(int(self.RANGE["IN_W"]))]
        self.tmp_r_word[:] = [0 for i in range(int(self.RANGE["IN_D"]))]
        self.main_previous_r_bin = [0 for i in range(int(self.RANGE["IN_W"]))]
        self.main_previous_r_word = [0 for i in range(int(self.RANGE["IN_D"]))]
        self.sub_previous_r_bin = [0 for i in range(int(self.RANGE["IN_W"]))]
        self.sub_previous_r_word = [0 for i in range(int(self.RANGE["IN_D"]))]

        self.w_bin[:] = [0 for i in range(int(self.RANGE["OUT_W"]))]
        self.w_word[:] = [0 for i in range(int(self.RANGE["OUT_D"]))]
        self.tmp_w_bin[:] = [0 for i in range(int(self.RANGE["OUT_W"]))]
        self.tmp_w_word[:] = [0 for i in range(int(self.RANGE["OUT_D"]))]
        self.main_previous_w_bin = [0 for i in range(int(self.RANGE["OUT_W"]))]
        self.main_previous_w_word = [
            0 for i in range(int(self.RANGE["OUT_D"]))]
        self.sub_previous_w_bin = [0 for i in range(int(self.RANGE["OUT_W"]))]
        self.sub_previous_w_word = [0 for i in range(int(self.RANGE["OUT_D"]))]

    # ===============================================================================
    # NOTE: 素材関連
    # ===============================================================================

    def getAddressDIn(self) -> List[int]:
        data = {}
        for key in self.IN_D.keys():
            data[key] = self.RANGE['IN_LOWER'] + \
                self.RANGE['IN_W'] + self.IN_D[key]
        return data

    def getAddressDOut(self) -> List[int]:
        data = {}
        for key in self.OUT_D.keys():
            data[key] = self.RANGE['OUT_LOWER'] + \
                self.RANGE['OUT_W'] + self.OUT_D[key]
        return data

    def getAddressWIn(self) -> List[int]:
        data = {}
        for key in self.IN_W.keys():
            data[key] = self.RANGE['IN_LOWER'] + self.IN_W[key]
        return data

    def getAddressWOut(self) -> List[int]:
        data = {}
        for key in self.OUT_W.keys():
            data[key] = self.RANGE['OUT_LOWER'] + self.OUT_W[key]
        return data

    def bit2Word(self, bit_16: list) -> int:
        input_binary_data_buf = copy.deepcopy(bit_16)
        input_binary_data_buf.reverse()
        binary_data_str = str(input_binary_data_buf)
        revised_binary_data_str = '0b' + \
            binary_data_str[1:len(binary_data_str) - 1].replace(', ', '')
        word = eval(revised_binary_data_str)
        return word

    def word2Bit(self, word: int) -> List[int]:
        word_data_str = format(word, '016b')
        word_data_ary = list(word_data_str)
        word_data_ary.reverse()
        return list(map(int, word_data_ary))

    # ===============================================================================
    # NOTE: PLC通信メソッド関連
    # ===============================================================================
    def readInW(self, tag: str = "REQ_COM", key: str = 'SET_X_SERVO'):
        ret, data = self.plc_api.read_data_from_plc(d_type='word',
                                                    addr=self.IN_W_AD[tag])
        if ret:
            bit_16 = self.word2Bit(data[0])
            s_bit = bit_16[self.IN_W[key]]
        else:
            s_bit = -1
        return s_bit

    def writeOutW(self, data: list, tag: str) -> bool:
        bit_16 = data[self.OUT_W[tag]]
        send_data = self.bit2Word(bit_16)
        addr = self.OUT_W_AD[tag]
        ret = self.plc_api.write_data_to_plc(d_type='word',
                                             addr=addr,
                                             data=[send_data])
        return ret

    def readData(self):
        plc_status_W_val = []
        plc_status_D_val = []
        plc_status_B_val = []
        success_flag, word_data = self.plc_api.read_data_from_plc(d_type='word', addr_min=str(
            self.RANGE["IN_LOWER"]), addr_max=str(self.RANGE["IN_UPPER"]), multi=True, timeout=1000)

        plc_status_W_val = word_data[:self.RANGE["IN_W"]]
        # Word -> Bit変換
        # plc_status_B_val.append(self.word2Bit(plc_status_W_val[self.IN_W["REQ_COM"]]))
        # plc_status_B_val.append(self.word2Bit(plc_status_W_val[self.IN_W["REQ_OPT"]]))
        # plc_status_B_val.append(self.word2Bit(plc_status_W_val[self.IN_W["STATUS_COM"]]))
        # plc_status_B_val.append(self.word2Bit(plc_status_W_val[self.IN_W["STATUS_OPT"]]))
        # plc_status_B_val.append(self.word2Bit(plc_status_W_val[self.IN_W["CMP_COM"]]))
        # plc_status_B_val.append(self.word2Bit(plc_status_W_val[self.IN_W["CMP_OPT"]]))

        plc_status_D_val = word_data[self.RANGE["IN_W"]:self.RANGE["IN_SUM"]]

        return plc_status_W_val, plc_status_D_val

    def writeData(self, input_B_data, input_D_data):
        output_data = [0 for i in range(int(self.RANGE["OUT_SUM"]))]
        # Wデータ
        # output_data[0] = self.bit2Word(input_B_data[self.OUT_W["REQ_COM"]])
        # output_data[1] = self.bit2Word(input_B_data[self.OUT_W["REQ_OPT"]])
        # output_data[2] = self.bit2Word(input_B_data[self.OUT_W["STATUS_COM"]])
        # output_data[3] = self.bit2Word(input_B_data[self.OUT_W["STATUS_OPT"]])
        # output_data[4] = self.bit2Word(input_B_data[self.OUT_W["CMP_COM"]])
        # output_data[5] = self.bit2Word(input_B_data[self.OUT_W["CMP_OPT"]])
        output_data[0] = input_B_data[self.OUT_W["REQ_COM"]]
        output_data[1] = input_B_data[self.OUT_W["REQ_OPT"]]
        output_data[2] = input_B_data[self.OUT_W["STATUS_COM"]]
        output_data[3] = input_B_data[self.OUT_W["STATUS_OPT"]]
        output_data[4] = input_B_data[self.OUT_W["CMP_COM"]]
        output_data[5] = input_B_data[self.OUT_W["CMP_OPT"]]
        # Dデータ
        output_data[10] = input_D_data[self.OUT_D["PC_ERR_CODE"]]
        output_data[11] = input_D_data[self.OUT_D["ROBOT_NO"]]
        output_data[12] = input_D_data[self.OUT_D["ACK_JOB_NO"]]
        output_data[13] = input_D_data[self.OUT_D["ACK_TOOL_NO"]]

        output_data[15] = input_D_data[self.OUT_D["PROG_VER_MAJOR"]]
        output_data[16] = input_D_data[self.OUT_D["PROG_VER_MINOR"]]
        output_data[17] = input_D_data[self.OUT_D["PROG_VER_PATCH"]]

        output_data[20] = input_D_data[self.OUT_D["CR_X_LOW"]]
        output_data[21] = input_D_data[self.OUT_D["CR_X_HIGH"]]
        output_data[22] = input_D_data[self.OUT_D["CR_Y_LOW"]]
        output_data[23] = input_D_data[self.OUT_D["CR_Y_HIGH"]]
        output_data[24] = input_D_data[self.OUT_D["CR_Z_LOW"]]
        output_data[25] = input_D_data[self.OUT_D["CR_Z_HIGH"]]
        output_data[26] = input_D_data[self.OUT_D["CR_RX_LOW"]]
        output_data[27] = input_D_data[self.OUT_D["CR_RX_HIGH"]]
        output_data[28] = input_D_data[self.OUT_D["CR_RY_LOW"]]
        output_data[29] = input_D_data[self.OUT_D["CR_RY_HIGH"]]
        output_data[30] = input_D_data[self.OUT_D["CR_RZ_LOW"]]
        output_data[31] = input_D_data[self.OUT_D["CR_RZ_HIGH"]]

        # print(output_data)
        d_success = self.plc_api.write_data_to_plc(d_type='word', addr_min=str(
            self.RANGE["OUT_LOWER"]), addr_max=str(self.RANGE["OUT_UPPER"]), data=output_data, multi=True, timeout=1000)

    def transformReadWord2Bit(self, word_data):
        bin_data = []
        # Word -> Bit変換
        bin_data.append(self.word2Bit(word_data[self.IN_W["REQ_COM"]]))
        bin_data.append(self.word2Bit(word_data[self.IN_W["REQ_OPT"]]))
        bin_data.append(self.word2Bit(word_data[self.IN_W["STATUS_COM"]]))
        bin_data.append(self.word2Bit(word_data[self.IN_W["STATUS_OPT"]]))
        bin_data.append(self.word2Bit(word_data[self.IN_W["CMP_COM"]]))
        bin_data.append(self.word2Bit(word_data[self.IN_W["CMP_OPT"]]))
        # Dummy
        bin_data.append(self.word2Bit(0))
        bin_data.append(self.word2Bit(0))
        bin_data.append(self.word2Bit(0))
        bin_data.append(self.word2Bit(0))
        return bin_data

    def transformReadBit2Word(self, bin_data):
        # これは使わないはず
        word_data = []
        # Bit -> Word変換
        word_data.append(self.bit2Word(bin_data[self.IN_W["REQ_COM"]]))
        word_data.append(self.bit2Word(bin_data[self.IN_W["REQ_OPT"]]))
        word_data.append(self.bit2Word(bin_data[self.IN_W["STATUS_COM"]]))
        word_data.append(self.bit2Word(bin_data[self.IN_W["STATUS_OPT"]]))
        word_data.append(self.bit2Word(bin_data[self.IN_W["CMP_COM"]]))
        word_data.append(self.bit2Word(bin_data[self.IN_W["CMP_OPT"]]))
        # Dummy
        word_data.append(0)
        word_data.append(0)
        word_data.append(0)
        word_data.append(0)

        return word_data

    def transformWriteWord2Bit(self, word_data):
        bin_data = []
        # Word -> Bit変換
        bin_data.append(self.word2Bit(word_data[self.OUT_W["REQ_COM"]]))
        bin_data.append(self.word2Bit(word_data[self.OUT_W["REQ_OPT"]]))
        bin_data.append(self.word2Bit(word_data[self.OUT_W["STATUS_COM"]]))
        bin_data.append(self.word2Bit(word_data[self.OUT_W["STATUS_OPT"]]))
        bin_data.append(self.word2Bit(word_data[self.OUT_W["CMP_COM"]]))
        bin_data.append(self.word2Bit(word_data[self.OUT_W["CMP_OPT"]]))
        # Dummy
        bin_data.append(self.word2Bit(0))
        bin_data.append(self.word2Bit(0))
        bin_data.append(self.word2Bit(0))
        bin_data.append(self.word2Bit(0))

        return bin_data

    def transformWriteBit2Word(self, bin_data):
        word_data = []
        # Bit -> Word変換
        word_data.append(self.bit2Word(bin_data[self.OUT_W["REQ_COM"]]))
        word_data.append(self.bit2Word(bin_data[self.OUT_W["REQ_OPT"]]))
        word_data.append(self.bit2Word(bin_data[self.OUT_W["STATUS_COM"]]))
        word_data.append(self.bit2Word(bin_data[self.OUT_W["STATUS_OPT"]]))
        word_data.append(self.bit2Word(bin_data[self.OUT_W["CMP_COM"]]))
        word_data.append(self.bit2Word(bin_data[self.OUT_W["CMP_OPT"]]))
        # Dummy
        word_data.append(0)
        word_data.append(0)
        word_data.append(0)
        word_data.append(0)
        return word_data

    def updateBin(self, tag: str = "REQ_COM", key: str = "MOVE", val: int = 0) -> None:
        _w_bin = []
        # word->bit
        _w_bin = self.transformWriteWord2Bit(self.tmp_w_bin[:])
        _w_bin[self.OUT_W[tag]][self.OUT_W[key]] = val
        # bin->word
        self.tmp_w_bin[:] = self.transformWriteBit2Word(_w_bin)
        return

    def updateWord(self, tag: str, val: float) -> None:
        self.tmp_w_word[self.OUT_D[tag]] = val
        return

    def referenceWord(self, tag: str = 'PLC_X1_LOW'):
        ref_word = self.r_word[self.IN_D[tag]]
        return ref_word

    def checkBin(self, tag: str = "REQ_COM", key: str = "MOVE", val: int = 0) -> None:
        check_flag = True
        # word->bit
        tmp_r_bin = self.transformReadWord2Bit(self.tmp_r_bin[:])
        if tmp_r_bin[self.IN_W[tag]][self.IN_W[key]] == val:
            return check_flag
        else:
            check_flag = False
            return check_flag

    # NOTE:立ち上がり確認
    def triggerUp(self, tag: str = "REQ_COM", key: str = "MOVE"):
        # word->bit
        tmp_r_bin = self.transformReadWord2Bit(self.tmp_r_bin[:])
        tmp_previous_r_bin = self.transformReadWord2Bit(
            self.main_previous_r_bin)
        # try:
        up_flag = False
        current_bin = tmp_r_bin[self.IN_W[tag]][self.IN_W[key]]
        previous_bin = tmp_previous_r_bin[self.IN_W[tag]][self.IN_W[key]]
        # 現在のビットと以前のビットを比較、差が１ならば立ち上がり、0 OR -1は無視
        if current_bin-previous_bin == 1:
            up_flag = True
        # except:
        #     pass
        # except Exception as e:
        #     print(e)
        return up_flag

    # NOTE:立ち下がり確認
    def triggerDown(self, tag: str = "REQ_COM", key: str = "MOVE"):
        # word->bit
        tmp_r_bin = self.transformReadWord2Bit(self.tmp_r_bin[:])
        tmp_previous_r_bin = self.transformReadWord2Bit(
            self.main_previous_r_bin)
        try:
            down_flag = False
            current_bin = tmp_r_bin[self.IN_W[tag]][self.IN_W[key]]
            previous_bin = tmp_previous_r_bin[self.IN_W[tag]][self.IN_W[key]]
            # 現在のビットと以前のビットを比較、差が-１ならば立ち上がり、0 OR 1は無視
            if current_bin-previous_bin == -1:
                down_flag = True
        except:
            pass
        # except Exception as e:
        #     print(e)
        return down_flag

    # NOTE:ロボット番号とプログラムバージョンを書き込み
    def writeInRobotformation(self, robot_name):
        # プログラムバージョンの書き込み
        self.updateWord(tag="PROG_VER_MAJOR", val=PROGRAM_VERSION_MAJOR)
        self.updateWord(tag="PROG_VER_MINOR", val=PROGRAM_VERSION_MINOR)
        self.updateWord(tag="PROG_VER_PATCH", val=PROGRAM_VERSION_PATCH)
        # print("PROGRAM VERSION : {}.{}.{}".format(PROGRAM_VERSION_HIGH,PROGRAM_VERSION_MIDDLE,PROGRAM_VERSION_LOW))
        # ロボット番号の書き込み
        """
        iai_scara / iai_3axis_tabletop / iai_4axis_tabletop / yamaha_scara / dobot_mg400
        """
        if robot_name == "iai_scara":
            robot_no = 1
        elif robot_name == "iai_3axis_tabletop":
            robot_no = 2
        elif robot_name == "iai_4axis_tabletop":
            robot_no = 3
        elif robot_name == "yamaha_scara":
            robot_no = 4
        elif robot_name == "dobot_mg400":
            robot_no = 5
        elif 'fairino' in robot_name or 'fr' in robot_name:
            robot_no = 6
        elif 'dobot_cr'in robot_name and 'a'in robot_name:
            robot_no = 7
        elif 'hitbot'in robot_name and 'z'in robot_name and 'arm'in robot_name:
            robot_no = 8
        else:
            robot_no = 99
        self.updateWord(tag="ROBOT_NO", val=robot_no)

    # NOTE:メイン書き込みデータ更新用
    def updateWritedata(self) -> None:
        self.w_bin[:] = self.tmp_w_bin[:].copy()
        self.w_word[:] = self.tmp_w_word[:].copy()

    # NOTE:メイン読み込みデータ更新用

    def updateReaddata(self) -> None:
        self.tmp_r_bin[:] = self.r_bin[:].copy()
        self.tmp_r_word[:] = self.r_word[:].copy()

    def setPlcParam(self):
        plc_param = dict(ip=self.plc_ip_address,
                         port='5000',
                         manufacturer='keyence',
                         series='',
                         plc_protocol='slmp',
                         transport_protocol='udp',
                         bit='W',
                         word='DM',
                         double_word='')  # NOTE: ダブルワード
        self.plc_api.load_param(plc_param)

    # NOTE:PLCの通信ループ
    def runPlc(self):
        print('Run PLC')
        while True:
            self.mySleep(0.001)
            #####################################################################
            # NOTE:読み込み
            #####################################################################
            self.r_bin[:], self.r_word[:] = self.readData()
            self.mySleep(0.001)
            # 毎回書き込み
            self.writeData(self.w_bin[:], self.w_word[:])

    # NOTE:PLCマルチプロセス開始
    def startPlcProcess(self):
        # NOTE:PLCのアドレス等を定義
        self.setPlcParam()
        # PLCプロセスを作成
        self.p1 = Process(target=self.runPlc, args=())
        # PLCプロセス実行
        self.p1.daemon = True
        self.p1.start()

    # ===============================================================================
    # NOTE: 変数確認/更新メソッド
    # ===============================================================================

    # NOTE:指定フェーズのインクリメント
    def incrementPhase(self, key: str):
        self.in_phase[str(key)] += 1

    # NOTE:指定フェーズのリセット
    def resetPhase(self, key: str):
        self.in_phase[str(key)] = 0

    # NOTE:指定フェーズの確認
    def checkPhase(self, key: str, val: str):
        if self.in_phase[str(key)] == val:
            return True
        else:
            pass

    # NOTE:指定フェーズの更新
    def updateDebugPhase(self, key: str, val: any):
        self.in_phase[str(key)] = val

    # NOTE:指定ステータスの更新
    def updateRobotStatus(self, val: any):
        self.in_phase["ROBOT_STATUS"] = val

    # NOTE:指定フラグの更新
    def updateFlag(self, key: str, val: bool):
        self.in_flag[str(key)] = val

    # NOTE:指定フラグの確認
    def checkFlag(self, key: str):
        if self.in_flag[str(key)]:
            return True
        elif not self.in_flag[str(key)]:
            return False

    # NOTE:指定ステータスの確認
    def checkRobotStatus(self, val: str):
        if self.in_phase["ROBOT_STATUS"] == val:
            return True
        else:
            return False

    # ===============================================================================
    # NOTE: 計算メソッド
    # ===============================================================================
    # def calcCurrentMinArm(self):
    #     # 現在地のジョイント座標を取得
    #     current_joint = self.rb_api.getCurrentJoint()
    #     # iniファイル読み出し
    #     # min_joint = self.param_api.read_robot_ini()
    #     # current_pos_j[1] = min_joint["min_joint2"]
    #     # current_pos_j[2] = min_joint["min_joint3"]
    #     current_joint[1] = -1
    #     current_joint[2] = -1
    #     # ジョイント座標を直交座標に変換
    #     target_pos = self.rb_api.getJoint2Pos(j1=current_joint[0], j2=current_joint[1], j3=current_joint[2], j4=current_joint[3])
    #     return target_pos

    # def calcTargetMinArm(self,target_pos):
    #     # 目的地の直交座標からジョイント座標へ変換
    #     target_joint = self.rb_api.getPos2Joint(x=target_pos[0],y=target_pos[1],z=target_pos[2],r=target_pos[3])
    #     # iniファイル読み出し
    #     # min_joint = self.param_api.read_robot_ini()
    #     # target_pos_j[1] = min_joint["min_joint2"]
    #     # target_pos_j[2] = min_joint["min_joint3"]
    #     target_joint[1] = -1
    #     target_joint[2] = -1
    #     # ジョイント座標を直交座標に変換
    #     target_pos = self.rb_api.getJoint2Pos(j1=target_joint[0], j2=target_joint[1], j3=target_joint[2], j4=target_joint[3])
    #     return target_pos

    # ===============================================================================
    # NOTE: 動作メソッド
    # ===============================================================================
    # NOTE:直線動作
    def runLine(self, point_param):
        target_pos = point_param["TARGET"]
        target_param = point_param["PARAM"]
        #print("runLine point",target_pos,target_param)
        if self.checkPhase(key="MOVE", val=0):
            # ツール座標系更新
            self.rb_api.setTool(tool_no=int(target_param["TOOL"]))
            # 直線移動
            self.rb_api.moveAbsoluteLine(x=target_pos[X],
                                         y=target_pos[Y],
                                         z=target_pos[Z],
                                         rx=target_pos[RX],
                                         ry=target_pos[RY],
                                         rz=target_pos[RZ],
                                         vel=target_param["VEL"],
                                         acc=target_param["ACC"],
                                         dec=target_param["DEC"])
            # Phaseの切り替え
            self.incrementPhase("MOVE")

        elif self.checkPhase(key="MOVE", val=1):
            # 動作中確認
            if self.checkBusy(target_pos):
                # Phaseの切り替え
                self.incrementPhase("MOVE")

        elif self.checkPhase(key="MOVE", val=2):
            self.rb_api.waitArrive(target_pos=target_pos,
                                   width=target_param["DIST"])

            # 到着確認
            if self.rb_api.arrived:
                self.updateBin(tag='STATUS_COM', key='MOVING', val=0)
                # Phaseの切り替え
                self.incrementPhase("MOVE")

        elif self.checkPhase(key="MOVE", val=3):
            # with open('log_fr3api.txt', 'a') as f:
            #     t0=time.time()
            #     print('     runLine val=3',t0,file=f)
            # f.close()

            # 動作完了ON
            self.moveComp(val=1)
            # Phaseの切り替え
            self.incrementPhase("MOVE")

        elif self.checkPhase(key="MOVE", val=4):
            if self.checkBin(tag="REQ_COM", key="MOVE", val=0):
                # 動作完了OFF
                self.moveComp(val=0)
                return

    # NOTE:PTP動作
    def runPtp(self, point_param):
        target_pos = point_param["TARGET"]
        target_param = point_param["PARAM"]
        #print("runPtp point",target_pos,target_param)
        if self.checkPhase(key="MOVE", val=0):
            # ツール座標系更新
            self.rb_api.setTool(tool_no=int(target_param["TOOL"]))
            # ptp移動
            self.rb_api.moveAbsolutePtp(x=target_pos[X],
                                        y=target_pos[Y],
                                        z=target_pos[Z],
                                        rx=target_pos[RX],
                                        ry=target_pos[RY],
                                        rz=target_pos[RZ],
                                        vel=target_param["VEL"],
                                        acc=target_param["ACC"],
                                        dec=target_param["DEC"])
            # Phaseの切り替え
            self.incrementPhase("MOVE")

        elif self.checkPhase(key="MOVE", val=1):
            # 動作中確認
            if self.checkBusy(target_pos):
                # Phaseの切り替え
                self.incrementPhase("MOVE")

        elif self.checkPhase(key="MOVE", val=2):
            self.rb_api.waitArrive(target_pos=target_pos,
                                   width=target_param["DIST"])
            # 到着確認
            if self.rb_api.arrived:
                self.updateBin(tag='STATUS_COM', key='MOVING', val=0)
                # Phaseの切り替え
                self.incrementPhase("MOVE")

        elif self.checkPhase(key="MOVE", val=3):
            # 動作完了ON
            self.moveComp(val=1)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=4):
            if self.checkBin(tag="REQ_COM", key="MOVE", val=0):
                # 動作完了OFF
                self.moveComp(val=0)
                return

    '''
    # ４軸向けのためコメントアウト
    # #NOTE:腕を縮めた現在地へ動作
    # def runCurrentMinJoint(self,point_param):
    #     target_pos = point_param["TARGET"]
    #     target_param = point_param["PARAM"]
    #     if self.checkPhase(key="MOVE",val=0):
    #         # ツール座標系更新
    #         self.rb_api.setTool(tool_no=int(target_param["TOOL"]))
    #         # 現在地の腕を縮めた位置を算出
    #         current_min_pos = self.calcCurrentMinArm()
    #         # 絶対値直線移動
    #         self.rb_api.moveAbsoluteLine(x=current_min_pos[0], y=current_min_pos[1], z=current_min_pos[2], r=current_min_pos[3],vel=target_param["VEL"], acc=target_param["ACC"], dec=target_param["DEC"])
    #         #Phaseの切り替え
    #         self.incrementPhase("MOVE")

    #     elif self.checkPhase(key="MOVE",val=1):
    #         # 動作中確認
    #         if self.checkBusy(current_min_pos):
    #             #Phaseの切り替え
    #             self.incrementPhase("MOVE")

    #     elif self.checkPhase(key="MOVE",val=2):
    #         self.rb_api.waitArrive(target_pos=current_min_pos, width=target_param["DIST"])
    #         # 到着確認
    #         if self.rb_api.arrived:
    #             self.updateBin(tag='STATUS_COM', key='MOVING', val=0)
    #             #Phaseの切り替え
    #             self.incrementPhase("MOVE")

    #     elif self.checkPhase(key="MOVE",val=3):
    #         # 動作完了ON
    #         self.moveComp(val=1)
    #         #Phaseの切り替え
    #         self.incrementPhase("MOVE")
    #     elif self.checkPhase(key="MOVE",val=4):
    #         if self.checkBin(tag="REQ_COM",key="MOVE",val=0):
    #             # 動作完了OFF
    #             self.moveComp(val=0)
    #             return

    # #NOTE:腕を縮めた目的地へ動作
    # def runTargetMinJoint(self,point_param):
    #     target_pos = point_param["TARGET"]
    #     target_param = point_param["PARAM"]
    #     if self.checkPhase(key="MOVE",val=0):
    #         # ツール座標系更新
    #         self.rb_api.setTool(tool_no=int(target_param["TOOL"]))
    #         # 目的地の腕を縮めた位置を算出
    #         target_min_pos = self.calcTargetMinArm()
    #         # 絶対値ptp移動
    #         self.rb_api.moveAbsolutePtp(x=target_min_pos[0], y=target_min_pos[1], z=target_min_pos[2], r=target_min_pos[3],vel=target_param["VEL"], acc=target_param["ACC"], dec=target_param["DEC"])
    #         #Phaseの切り替え
    #         self.incrementPhase("MOVE")

    #     elif self.checkPhase(key="MOVE",val=1):
    #         # 動作中確認
    #         if self.checkBusy(target_min_pos):
    #             #Phaseの切り替え
    #             self.incrementPhase("MOVE")

    #     elif self.checkPhase(key="MOVE",val=2):
    #         self.rb_api.waitArrive(target_pos=target_min_pos, width=target_param["DIST"])
    #         # 到着確認
    #         if self.rb_api.arrived:
    #             self.updateBin(tag='STATUS_COM', key='MOVING', val=0)
    #             #Phaseの切り替え
    #             self.incrementPhase("MOVE")

    #     elif self.checkPhase(key="MOVE",val=3):
    #         # 動作完了ON
    #         self.moveComp(val=1)
    #         #Phaseの切り替え
    #         self.incrementPhase("MOVE")
    #     elif self.checkPhase(key="MOVE",val=4):
    #         if self.checkBin(tag="REQ_COM",key="MOVE",val=0):
    #             # 動作完了OFF
    #             self.moveComp(val=0)
    #             return
    '''

    # NOTE:ジョグ動作
    def runJog(self, point_param, axis, sign):
        target_pos = point_param["TARGET"]
        target_param = point_param["PARAM"]
        #print("main--runJog:in_phase", self.in_phase["MOVE"])
        #print("runJog point",target_pos,target_param)

        if self.checkPhase(key="MOVE", val=0):
            # ツール座標系更新
            self.rb_api.setTool(tool_no=int(target_param["TOOL"]))
            # ツール座標系更新
            #self.rb_api.setTool(tool_no=int(target_param["TOOL"]))   ####0507 设定tool则jog无法执行，原因不明。jog处未设codytype应该实际未使用，注释掉
                                                                    ####0517    jog处 设codytype=2，tool=0，即在0号工具坐标系运动，此句仍注释
            # print("phase0")
            self.updateBin(tag='STATUS_COM', key='MOVE', val=1)
            # JOG開始
            if (sign == '+') or (sign == '-'):
                print("target_param", target_param)
                print("target_pos", target_pos)
                #self.rb_api.moveJog(axis, sign)
                vel=target_param["VEL"]
                self.rb_api.moveJog(axis, sign,vel)      ###0901 增加速度参数 Vel
                self.incrementPhase("MOVE")

        elif self.checkPhase(key="MOVE", val=1):
            # print("phase1")
            # JOG継続
            self.rb_api.continueJog(axis, sign)
            if sign == "None":
                self.incrementPhase("MOVE")

        elif self.checkPhase(key="MOVE", val=2):
            # print("phase2")
            # JOG終了
            self.rb_api.stopJog()
            # フェイズリセット
            self.resetPhase("MOVE")
            return

    # NOTE:インチング動作
    def runInch(self, point_param):
        target_pos = point_param["TARGET"]
        target_param = point_param["PARAM"]
        # print("main--runInch")
        # print("in_phase", self.in_phase["MOVE"])
        # print("target_pos", target_pos)
        # print("target_param", target_param)
        #print("runInch point",target_pos,target_param)
        if self.checkPhase(key="MOVE", val=0):
            # ツール座標系更新
            self.rb_api.setTool(tool_no=int(target_param["TOOL"]))

            # 絶対値直線移動
            self.rb_api.moveRelative(x=target_pos[X],
                                     y=target_pos[Y],
                                     z=target_pos[Z],
                                     rx=target_pos[RX],
                                     ry=target_pos[RY],
                                     rz=target_pos[RZ],
                                     vel=target_param["VEL"],
                                     acc=target_param["ACC"],
                                     dec=target_param["DEC"])

            # Phaseの切り替え
            self.incrementPhase("MOVE")

        elif self.checkPhase(key="MOVE", val=1):
            # 動作完了ON
            self.moveComp(val=1)
            # Phaseの切り替え
            self.incrementPhase("MOVE")

        elif self.checkPhase(key="MOVE", val=2):
            if self.checkBin(tag="REQ_COM", key="MOVE", val=0):
                # 動作完了OFF
                self.moveComp(val=0)
                return

   # NOTE:Jog_no=99，Tool坐标值读入
    def getTool_coord0928(self, point_param):
        target_pos = point_param["TARGET"]
        target_param = point_param["PARAM"]
        #print(target_pos)
        # ツール座標系坐标值取得
        self.rb_api.saveTool_coord(x=target_pos[X],
                                        y=target_pos[Y],
                                        z=target_pos[Z],
                                        rx=target_pos[RX],
                                        ry=target_pos[RY],
                                        rz=target_pos[RZ],
                                        tool_no=int(target_param["TOOL"]))

    def getTool_coord(self, point_param):
        if self.rb_series=='fairino_FR' or self.rb_series=='dobot_CRA':
            target_pos = point_param["TARGET"]
            target_param = point_param["PARAM"]
            #print(target_pos)
            # ツール座標系坐标值取得
            self.rb_api.saveTool_coord(x=target_pos[X],
                                            y=target_pos[Y],
                                            z=target_pos[Z],
                                            rx=target_pos[RX],
                                            ry=target_pos[RY],
                                            rz=target_pos[RZ],
                                            tool_no=int(target_param["TOOL"]))

    # NOTE:マニュアル_ジョグ
    def manualJog(self):
        #print('manualJog',self.referenceWord(tag="JOB_NO"),self.referenceWord(tag="ENABLE_AXIS_NO") )       
        # X
        if self.referenceWord(tag="ENABLE_AXIS_NO") == 1:
            axis = "x"
        # Y
        elif self.referenceWord(tag="ENABLE_AXIS_NO") == 2:
            axis = "y"
        # Z
        elif self.referenceWord(tag="ENABLE_AXIS_NO") == 3:
            axis = "z"
        # RX
        elif self.referenceWord(tag="ENABLE_AXIS_NO") == 4:
            axis = "rx"
        # RY
        elif self.referenceWord(tag="ENABLE_AXIS_NO") == 5:
            axis = "ry"
        # RZ
        elif self.referenceWord(tag="ENABLE_AXIS_NO") == 6:
            axis = "rz"
        else:
            axis = "None"

        # 符号
        if self.checkBin(tag="REQ_COM", key='PLUS_JOG', val=1):
            sign = "+"
        elif self.checkBin(tag="REQ_COM", key='MINUS_JOG', val=1):
            sign = "-"
        else:
            sign = "None"

        self.updateDebugPhase(key="DEBUG", val="JOG")
        self.target_point = self.makePointData(p="P1")
        #print('manualJog->runJog',self.target_point )
        self.runJog(self.target_point, axis, sign)

    # NOTE:ロボットのコントローラにポイントデータを書込み
    def runJob200(self, start_no, range_no, P1, P2, P3, P4):
        if self.checkPhase(key="MOVE", val=0):
            # ポイントデータ書き込み
            self.rb_api.setPointData(start_no, range_no, P1, P2, P3, P4)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=1):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=2):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=3):
            # 動作完了ON
            self.moveComp(val=1)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=4):
            if self.checkBin(tag="REQ_COM", key="MOVE", val=0):
                # 動作完了OFF
                self.moveComp(val=0)
                return

    # NOTE:グローバルフラグON
    def runJob201(self, flag_no):
        if self.checkPhase(key="MOVE", val=0):
            # グローバルフラグON
            self.rb_api.setGlobalFlagOn(flag_no)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=1):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=2):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=3):
            # 動作完了ON
            self.moveComp(val=1)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=4):
            if self.checkBin(tag="REQ_COM", key="MOVE", val=0):
                # 動作完了OFF
                self.moveComp(val=0)
                return
            
    # NOTE:グローバルフラグOFF
    def runJob202(self, flag_no):
        if self.checkPhase(key="MOVE", val=0):
            # グローバルフラグON
            self.rb_api.setGlobalFlagOff(flag_no)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=1):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=2):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=3):
            # 動作完了ON
            self.moveComp(val=1)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=4):
            if self.checkBin(tag="REQ_COM", key="MOVE", val=0):
                # 動作完了OFF
                self.moveComp(val=0)
                return

    # NOTE:グローバル変数値書き換え
    def runJob203(self, start_no, val):
        if self.checkPhase(key="MOVE", val=0):
            # グローバル変数値書き換え
            self.rb_api.setGlobalValue(start_no, [val])
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=1):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=2):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=3):
            # 動作完了ON
            self.moveComp(val=1)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=4):
            if self.checkBin(tag="REQ_COM", key="MOVE", val=0):
                # 動作完了OFF
                self.moveComp(val=0)
                return

    # NOTE:グローバルフラグON＆グローバルフラグON完了まで待機
    def runJob204(self, write_flag_no, read_flag_no):
        if self.checkPhase(key="MOVE", val=0):
            # グローバルフラグON
            self.rb_api.setGlobalFlagOn(write_flag_no)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=1):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=2):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=3):
            flag_status = self.rb_api.getFlagStatus(read_flag_no)
            if(flag_status == True):
                # 動作完了ON
                self.moveComp(val=1)
                # Phaseの切り替え
                self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=4):
            if self.checkBin(tag="REQ_COM", key="MOVE", val=0):
                # 動作完了OFF
                self.moveComp(val=0)
                return

    # NOTE:ロボットのコントローラのプログラムを起動
    def runJob232(self, prog_no):
        if self.checkPhase(key="MOVE", val=0):
            # プログラム起動
            self.rb_api.startProgram(prog_no)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=1):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=2):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=3):
            # 動作完了ON
            self.moveComp(val=1)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=4):
            if self.checkBin(tag="REQ_COM", key="MOVE", val=0):
                # 動作完了OFF
                self.moveComp(val=0)
                return
            
    # NOTE:ロボットのコントローラのプログラムを停止
    def runJob233(self, prog_no):
        if self.checkPhase(key="MOVE", val=0):
            # プログラム起動
            self.rb_api.stopProgram(prog_no)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=1):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=2):
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=3):
            # 動作完了ON
            self.moveComp(val=1)
            # Phaseの切り替え
            self.incrementPhase("MOVE")
        elif self.checkPhase(key="MOVE", val=4):
            if self.checkBin(tag="REQ_COM", key="MOVE", val=0):
                # 動作完了OFF
                self.moveComp(val=0)
                return

    # ===============================================================================
    # NOTE: 運転モード
    # ===============================================================================
    # NOTE:自動運転モード

    def autoMode(self):
        #print('autoMode',self.referenceWord(tag="JOB_NO"),self.checkFlag(key="OPERATING"),self.referenceWord(tag="ENABLE_AXIS_NO") )       
        self.updateDebugPhase(key="DEBUG", val="RUN_MODE")
        if self.checkFlag(key="OPERATING"):
            self.updateDebugPhase(key="DEBUG", val="OPERATING_TRUE")
            # NOTE:JOB_NO_1 = 直線移動
            # if self.referenceWord(tag="JOB_NO") == 1:
            #     self.updateDebugPhase(key="DEBUG", val="1_line")
            #     self.target_point = self.makePointData(p="P1")
            #     self.runLine(self.target_point)
            if self.referenceWord(tag="JOB_NO") == 1:
                self.target_point = self.makePointData(p="P1")
                #target_param = self.target_point["PARAM"]
                #dec=target_param["DEC"]
                moveType = self.target_point["PARAM"]["DEC"]
                if moveType ==2:
                    self.updateDebugPhase(key="DEBUG", val="2_ptp")
                    self.runPtp(self.target_point)
                elif  self.rb_series=='hitbot_Z_ARM' and (moveType ==21 or moveType ==22 or moveType ==25 or moveType ==26):
                    self.updateDebugPhase(key="DEBUG", val="2_ptp")
                    self.runPtp(self.target_point)                
                else:
                    self.updateDebugPhase(key="DEBUG", val="1_line")
                    self.runLine(self.target_point)

            # NOTE:JOB_NO_2 = PTP移動
            # elif self.referenceWord(tag="JOB_NO") == 2:
            #     self.updateDebugPhase(key="DEBUG", val="2_ptp")
            #     self.target_point = self.makePointData(p="P1")
            #     self.runPtp(self.target_point)
            if self.referenceWord(tag="JOB_NO") == 2:
                self.target_point = self.makePointData(p="P1")
                #target_param = self.target_point["PARAM"]
                #dec=target_param["DEC"]
                moveType = self.target_point["PARAM"]["DEC"]
                if moveType ==1:
                    self.updateDebugPhase(key="DEBUG", val="1_line")
                    self.runLine(self.target_point)
                elif  self.rb_series=='hitbot_Z_ARM' and (moveType ==15):
                    self.updateDebugPhase(key="DEBUG", val="1_line")
                    self.runLine(self.target_point)
                else:
                    self.updateDebugPhase(key="DEBUG", val="2_ptp")
                    self.runPtp(self.target_point)

            # 4軸用のためコメントアウト
            # # NOTE:JOB_NO_3 現在地で腕を縮める位置移動
            # elif self.referenceWord(tag="JOB_NO")==3:
            #     self.updateDebugPhase(key="DEBUG",val="3_c_minj")
            #     self.target_point = self.makePointData(p="P1")
            #     self.runCurrentMinJoint(self.target_point)

            # # NOTE:JOB_NO_4 目的地の腕を縮める位置移動
            # elif self.referenceWord(tag="JOB_NO")==4:
            #     self.updateDebugPhase(key="DEBUG",val="4_t_minj")
            #     self.target_point = self.makePointData(p="P1")
            #     self.runTargetMinJoint(self.target_point)

            # NOTE:JOB_NO_20 = inch
            elif self.referenceWord(tag="JOB_NO") == 20:
                self.updateDebugPhase(key="DEBUG", val="INCH")
                self.target_point = self.makePointData(p="P1")
                # インチング時の座標計算
                self.inch_p1 = self.makeInchData(self.target_point)
                #print('autoMode Inch',self.referenceWord(tag="JOB_NO"),self.checkFlag(key="OPERATING"),self.referenceWord(tag="ENABLE_AXIS_NO") )       
                self.runInch(self.inch_p1)

            # NOTE:JOB_NO_40 = jog      ##0901 换新PLC程序后，jog运动deself.checkFlag(key="OPERATING")的值变成False所以不被调用。原因不明。保留此部分保证不管flag如何jog都能被调用
            elif self.referenceWord(tag="JOB_NO") == 40:
                self.updateDebugPhase(key="DEBUG", val="JOG")
                self.target_point = self.makePointData(p="P1")
                #print('automode->manualJog',self.target_point )
                self.manualJog()
                
            # NOTE:JOB_NO_200 = ポイントデータ書込み
            elif self.referenceWord(tag="JOB_NO") == 200:
                self.updateDebugPhase(key="DEBUG", val="SETTING")                
                # P1作成
                point_1= self.makePointData(p="P1")
                point_1['TARGET'].append(point_1['PARAM']['VEL'])
                point_1['TARGET'].append(point_1['PARAM']['ACC'])
                point_1['TARGET'].append(point_1['PARAM']['DEC'])
                # P2作成
                point_2= self.makePointData(p="P2")
                point_2['TARGET'].append(point_2['PARAM']['VEL'])
                point_2['TARGET'].append(point_2['PARAM']['ACC'])
                point_2['TARGET'].append(point_2['PARAM']['DEC'])
                # P3作成
                point_3= self.makePointData(p="P3")
                point_3['TARGET'].append(point_3['PARAM']['VEL'])
                point_3['TARGET'].append(point_3['PARAM']['ACC'])
                point_3['TARGET'].append(point_3['PARAM']['DEC'])
                # P4作成
                point_4= self.makePointData(p="P4")
                point_4['TARGET'].append(point_4['PARAM']['VEL'])
                point_4['TARGET'].append(point_4['PARAM']['ACC'])
                point_4['TARGET'].append(point_4['PARAM']['DEC'])
                #パラメータ
                ref_point_no = self.referenceWord(tag="START_NO")
                range_point_no = self.referenceWord(tag="RANGE_NO")
                self.runJob200(ref_point_no, range_point_no, point_1['TARGET'], point_2['TARGET'], point_3['TARGET'], point_4['TARGET'])

            # NOTE:JOB_NO_201 = グローバルフラグON
            elif self.referenceWord(tag="JOB_NO") == 201:
                self.updateDebugPhase(key="DEBUG", val="SETTING")
                flag_no = self.referenceWord(tag="WRITE_FLAG_NO")
                self.runJob201(flag_no)
                
            # NOTE:JOB_NO_202 = グローバルフラグOFF
            elif self.referenceWord(tag="JOB_NO") == 202:
                self.updateDebugPhase(key="DEBUG", val="SETTING")
                flag_no = self.referenceWord(tag="WRITE_FLAG_NO")
                self.runJob202(flag_no)

            # NOTE:JOB_NO_203 = グローバル変数値書き換え
            elif self.referenceWord(tag="JOB_NO") == 203:
                self.updateDebugPhase(key="DEBUG", val="SETTING")
                start_no = self.referenceWord(tag="START_NO")
                range_point_no = self.referenceWord(tag="INPUT1_NO")
                self.runJob203(start_no, range_point_no)

            # NOTE:JOB_NO_204 = グローバルフラグON＆グローバルフラグON完了まで待機
            elif self.referenceWord(tag="JOB_NO") == 204:
                self.updateDebugPhase(key="DEBUG", val="SETTING")
                write_flag_no = self.referenceWord(tag="WRITE_FLAG_NO")
                read_flag_no = self.referenceWord(tag="READ_FLAG_NO")
                self.runJob204(write_flag_no, read_flag_no)

            # NOTE:JOB_NO_232 = プログラム起動
            elif self.referenceWord(tag="JOB_NO") == 232:
                self.updateDebugPhase(key="DEBUG", val="SETTING")
                prog_no = self.referenceWord(tag="PROGRAM_NO")
                self.runJob232(prog_no)
                
            # NOTE:JOB_NO_233 = プログラム停止
            elif self.referenceWord(tag="JOB_NO") == 233:
                self.updateDebugPhase(key="DEBUG", val="SETTING")
                prog_no = self.referenceWord(tag="PROGRAM_NO")
                self.runJob233(prog_no)

        # NOTE:JOB_NO_40 = jog    ##0901 换新PLC程序后，jog运动deself.checkFlag(key="OPERATING")的值变成False所以不被调用。原因不明。所以增加此处部分保证不管flag如何jog都能被调用
        elif self.referenceWord(tag="JOB_NO") == 40:
            self.updateDebugPhase(key="DEBUG", val="JOG")
            #print('automode->manualJog',self.target_point )
            self.manualJog()
        elif self.referenceWord(tag="JOB_NO") == 99:
            self.target_point = self.makePointData(p="P1")
            #print('automode->99',self.target_point )
            self.getTool_coord(self.target_point)                          
 
    # ===============================================================================
    # NOTE: 確認メソッド
    # ===============================================================================
    # NOTE:動作中確認
    def checkBusy(self, target_pos):
        permission_time = 0.1
        permission_area = 5.0
        self.updateFlag(key='MOVING', val=False)
        if self.rb_api.moving:
            self.updateBin(tag='STATUS_COM', key='MOVING', val=1)
            self.updateFlag(key='MOVING', val=True)
            self.updateRobotStatus(val="RUN")
            return True

        elif not self.rb_api.moving:
            self.updateBin(tag='STATUS_COM', key='MOVING', val=0)
            if not self.checkFlag(key="BUSY_CHECK"):
                self.updateFlag(key="BUSY_CHECK", val=True)
                self.updateDebugPhase(
                    key="BUSY_CHECK_TIME", val=perf_counter())

            elif self.checkFlag(key="BUSY_CHECK"):
                if time.perf_counter()-self.in_phase['BUSY_CHECK_TIME'] > permission_time:
                    self.rb_api.waitArrive(
                        target_pos=target_pos, width=permission_area)
                    if self.rb_api.arrived:
                        return True
                    else:
                        return False

    # NOTE:現在地の更新
    def updateCurrentPos(self):
        # print("現在地",self.current_pos)
        if not self.rb_api.current_pos:
            print("current pos None")

        else:
            cr_x_low, cr_x_high = self.convertReal2Dword(
                self.rb_api.current_pos[X])
            cr_y_low, cr_y_high = self.convertReal2Dword(
                self.rb_api.current_pos[Y])
            cr_z_low, cr_z_high = self.convertReal2Dword(
                self.rb_api.current_pos[Z])
            cr_rx_low, cr_rx_high = self.convertReal2Dword(
                self.rb_api.current_pos[RX])
            cr_ry_low, cr_ry_high = self.convertReal2Dword(
                self.rb_api.current_pos[RY])
            cr_rz_low, cr_rz_high = self.convertReal2Dword(
                self.rb_api.current_pos[RZ])
            self.updateWord(tag='CR_X_LOW', val=cr_x_low)
            self.updateWord(tag='CR_X_HIGH', val=cr_x_high)
            self.updateWord(tag='CR_Y_LOW', val=cr_y_low)
            self.updateWord(tag='CR_Y_HIGH', val=cr_y_high)
            self.updateWord(tag='CR_Z_LOW', val=cr_z_low)
            self.updateWord(tag='CR_Z_HIGH', val=cr_z_high)
            self.updateWord(tag='CR_RX_LOW', val=cr_rx_low)
            self.updateWord(tag='CR_RX_HIGH', val=cr_rx_high)
            self.updateWord(tag='CR_RY_LOW', val=cr_ry_low)
            self.updateWord(tag='CR_RY_HIGH', val=cr_ry_high)
            self.updateWord(tag='CR_RZ_LOW', val=cr_rz_low)
            self.updateWord(tag='CR_RZ_HIGH', val=cr_rz_high)

    # NOTE:動作完了
    def moveComp(self, val):
        # ON
        if val == 1:
            self.updateBin(tag='CMP_COM', key="MOVE", val=1)
        # OFF
        elif val == 0:
            self.updateBin(tag='CMP_COM', key="MOVE", val=0)
            self.resetPhase(key="MOVE")
            self.updateFlag(key="OPERATING", val=False)
            self.updateRobotStatus(val="IDLE")

    # NOTE:原点復帰完了
    def OriginComp(self):
        self.updateBin(tag='CMP_COM', key="ORIGIN", val=1)
        self.resetPhase(key="ORIGIN")

    # NOTE:PLCへの生存通知
    def heartBeat(self):
        current_time = time.perf_counter()
        BEAT_FREQ = 1.0
        # try:
        if current_time - self.previous_time > BEAT_FREQ:
            if self.checkFlag(key="ONLINE_CHK"):
                # STATUS_ONLINEフラグをOFF
                self.updateBin(tag='STATUS_COM', key='ONLINE', val=0)
                # 内部ONLINE_CHKフラグをOFF
                self.updateFlag(key="ONLINE_CHK", val=False)

            # 内部ONLINE_CHKフラグがOFFの時
            elif not self.checkFlag(key="ONLINE_CHK"):
                # STATUS_ONLINEフラグをON
                self.updateBin(tag='STATUS_COM', key='ONLINE', val=1)
                # 内部ONLINE_CHKフラグをON
                self.updateFlag(key="ONLINE_CHK", val=True)
            # 現在時刻を前の時刻とする
            self.previous_time = current_time
        # except:
        #     self.previous_time = current_time

    # NOTE:PLCデータを保持
    def savePlcDataMain(self):
        self.main_previous_r_bin = self.tmp_r_bin[:].copy()
        self.main_previous_r_word = self.tmp_r_word[:].copy()
        self.main_previous_w_bin = self.tmp_w_bin[:].copy()
        self.main_previous_w_word = self.tmp_w_word[:].copy()

    def savePlcDataSub(self):
        self.sub_previous_r_bin = self.r_bin[:].copy()
        self.sub_previous_r_word = self.r_word[:].copy()
        self.sub_previous_w_bin = self.w_bin[:].copy()
        self.sub_previous_w_word = self.w_word[:].copy()

    # NOTE:内部データを保持

    def saveInternalData(self):
        self.previous_in_flag = self.in_flag.copy()
        self.previous_in_phase = self.in_phase.copy()

    # NOTE:ポイントデータを作成
    def makePointData(self, p="P1"):
        # ポイントによって読み込むアドレスを分岐
        if p == "P1":
            index = 1
        elif p == "P2":
            index = 2
        elif p == "P3":
            index = 3
        elif p == "P4":
            index = 4
        if index is not None:
            tool_val = self.convertDword2Real(self.referenceWord(
                "PLC_TOOL"+str(index)+"_LOW"), self.referenceWord("PLC_TOOL"+str(index)+"_HIGH"))
            x_val = self.convertDword2Real(self.referenceWord(
                "PLC_X"+str(index)+"_LOW"), self.referenceWord("PLC_X"+str(index)+"_HIGH"))
            y_val = self.convertDword2Real(self.referenceWord(
                "PLC_Y"+str(index)+"_LOW"), self.referenceWord("PLC_Y"+str(index)+"_HIGH"))
            z_val = self.convertDword2Real(self.referenceWord(
                "PLC_Z"+str(index)+"_LOW"), self.referenceWord("PLC_Z"+str(index)+"_HIGH"))
            rx_val = self.convertDword2Real(self.referenceWord(
                "PLC_RX"+str(index)+"_LOW"), self.referenceWord("PLC_RX"+str(index)+"_HIGH"))
            ry_val = self.convertDword2Real(self.referenceWord(
                "PLC_RY"+str(index)+"_LOW"), self.referenceWord("PLC_RY"+str(index)+"_HIGH"))
            rz_val = self.convertDword2Real(self.referenceWord(
                "PLC_RZ"+str(index)+"_LOW"), self.referenceWord("PLC_RZ"+str(index)+"_HIGH"))
            vel_val = self.convertDword2Real(self.referenceWord(
                "PLC_VEL"+str(index)+"_LOW"), self.referenceWord("PLC_VEL"+str(index)+"_HIGH"))
            acc_val = self.convertDword2Real(self.referenceWord(
                "PLC_ACC"+str(index)+"_LOW"), self.referenceWord("PLC_ACC"+str(index)+"_HIGH"))
            dec_val = self.convertDword2Real(self.referenceWord(
                "PLC_DEC"+str(index)+"_LOW"), self.referenceWord("PLC_DEC"+str(index)+"_HIGH"))
            area_val = self.convertDword2Real(self.referenceWord(
                "PLC_AREA"+str(index)+"_LOW"), self.referenceWord("PLC_AREA"+str(index)+"_HIGH"))
            target_pos = [x_val, y_val, z_val, rx_val, ry_val, rz_val]
            #print("raw target data ", target_pos)  # debug
            target_param = {'TOOL': tool_val, 'VEL': vel_val,
                            'ACC': acc_val, 'DEC': dec_val, 'DIST': area_val}
            # dict形式の変数を作成
            point_param = {"TARGET": target_pos, "PARAM": target_param}
            return point_param
        else:
            print("index is wrong number")

    # NOTE:インチング時のポイントデータを作成
    def makeInchData(self, point_param):
        # インチング時は固定値
        index = 1
        #tool_val = self.referenceWord("PLC_TOOL_NO")  ##旧版本  # 固定アドレス
        tool_val = self.convertDword2Real(self.referenceWord(
            "PLC_TOOL"+str(index)+"_LOW"), self.referenceWord("PLC_TOOL"+str(index)+"_HIGH"))
        x_val = self.convertDword2Real(self.referenceWord(
            "PLC_X"+str(index)+"_LOW"), self.referenceWord("PLC_X"+str(index)+"_HIGH"))
        y_val = self.convertDword2Real(self.referenceWord(
            "PLC_Y"+str(index)+"_LOW"), self.referenceWord("PLC_Y"+str(index)+"_HIGH"))
        z_val = self.convertDword2Real(self.referenceWord(
            "PLC_Z"+str(index)+"_LOW"), self.referenceWord("PLC_Z"+str(index)+"_HIGH"))
        rx_val = self.convertDword2Real(self.referenceWord(
            "PLC_RX"+str(index)+"_LOW"), self.referenceWord("PLC_RX"+str(index)+"_HIGH"))
        ry_val = self.convertDword2Real(self.referenceWord(
            "PLC_RY"+str(index)+"_LOW"), self.referenceWord("PLC_RY"+str(index)+"_HIGH"))
        rz_val = self.convertDword2Real(self.referenceWord(
            "PLC_RZ"+str(index)+"_LOW"), self.referenceWord("PLC_RZ"+str(index)+"_HIGH"))
        vel_val = self.convertDword2Real(self.referenceWord(
            "PLC_VEL"+str(index)+"_LOW"), self.referenceWord("PLC_VEL"+str(index)+"_HIGH"))
        acc_val = self.convertDword2Real(self.referenceWord(
            "PLC_ACC"+str(index)+"_LOW"), self.referenceWord("PLC_ACC"+str(index)+"_HIGH"))
        dec_val = self.convertDword2Real(self.referenceWord(
            "PLC_DEC"+str(index)+"_LOW"), self.referenceWord("PLC_DEC"+str(index)+"_HIGH"))
        area_val = self.convertDword2Real(self.referenceWord(
            "PLC_AREA"+str(index)+"_LOW"), self.referenceWord("PLC_AREA"+str(index)+"_HIGH"))
        # X
        if self.referenceWord(tag="ENABLE_AXIS_NO") == 1:
            target_pos = [x_val, 0, 0, 0, 0, 0]
        # Y
        elif self.referenceWord(tag="ENABLE_AXIS_NO") == 2:
            target_pos = [0, y_val, 0, 0, 0, 0]
        # Z
        elif self.referenceWord(tag="ENABLE_AXIS_NO") == 3:
            target_pos = [0, 0, z_val, 0, 0, 0]
        # RX
        elif self.referenceWord(tag="ENABLE_AXIS_NO") == 4:
            target_pos = [0, 0, 0, rx_val, 0, 0]
        # RY
        elif self.referenceWord(tag="ENABLE_AXIS_NO") == 5:
            target_pos = [0, 0, 0, 0, ry_val, 0]
        # RZ
        elif self.referenceWord(tag="ENABLE_AXIS_NO") == 6:
            target_pos = [0, 0, 0, 0, 0, rz_val]
        else:
            print("None data")
            target_pos = [0, 0, 0, 0, 0, 0]
        target_param = {'TOOL': tool_val, 'VEL': vel_val,
                        'ACC': acc_val, 'DEC': dec_val, 'DIST': area_val}
        # dict形式の変数を作成
        point_param = {"TARGET": target_pos, "PARAM": target_param}
        return point_param

    # NOTE:2word分のデータ(符号なし32bit整数型)を10進数(符号付き32bit実数型)に変換
    def convertDword2Real(self, low_word_data, high_word_data):
        word_data_1 = low_word_data
        word_data_2 = high_word_data << 16
        # 符号なし32bit整数型
        Dword_data = word_data_1 | word_data_2
        # 符号付き32bit整数型
        Dint_data = -(Dword_data & 0b10000000000000000000000000000000) | (
            Dword_data & 0b01111111111111111111111111111111)
        # 符号付き32bit実数型
        Real_data = Dint_data / 1000
        return (Real_data)

    # NOTE:10進数(符号付き32bit実数型)を2word分のデータ(符号なし32bit整数型)に変換
    def convertReal2Dword(self, real_data):
        Dword_data = int(real_data * 1000)
        high_word_data = (Dword_data & 0xFFFF0000) >> 16
        low_word_data = Dword_data & 0x0000FFFF
        return (low_word_data, high_word_data)

    # NOTE:BUSYタイマー
    def mySleep(self, sleep_time):
        now = time.perf_counter()
        while (time.perf_counter()-now < sleep_time):
            break

    #############################################################
    # メインプログラム
    #############################################################
    def main(self):

        try:
            print('Run Main')
            #############################################################
            # ロボット設定ファイル読込む
            #############################################################
            config = configparser.ConfigParser()
            config.read(self.current_dir + SETTING_PATH + SETTING_NAME)
            robot_name = config['settings']['robot_name']
            robot_name = robot_name.lower()    ######0802 机器人名称全小写
            robot_ip_address = config['settings']['dst_robot_ip_address']
            self.plc_ip_address = config['settings']['dst_plc_ip_address']
            robot_port = config['settings']['dst_robot_port']
            dev_port = config['settings']['dev_port']
            baudrate = config['settings']['baudrate']

            #############################################################
            # 対象のロボットAPIをimport
            #############################################################
            sys.path.append(self.current_dir + API_PATH)
            # module = importlib.import_module(robot_name+'_api')
            if 'fairino' in robot_name or 'fr' in robot_name:
                robot_series_name='fairino_FR'
            elif 'dobot_cr'in robot_name and 'a'in robot_name:
                robot_series_name='dobot_CRA'    ######0802 系列用大写，机器人名称全用小写
            elif 'hitbot'in robot_name and 'z'in robot_name and 'arm'in robot_name:
                robot_series_name='hitbot_Z_ARM'    ######0802 系列用大写，机器人名称全用小写
            else:
                robot_series_name=robot_name
            module = importlib.import_module(robot_series_name+'_api')
            self.rb_series = robot_series_name
            # self.rb_api = module.RobotApi(
            #     robot_ip_address, robot_port, dev_port, baudrate)
            if robot_series_name=='hitbot_Z_ARM':
                self.rb_api = module.RobotApi(
                    robot_ip_address, robot_port, dev_port, baudrate,robot_name)
            else:
                self.rb_api = module.RobotApi(
                    robot_ip_address, robot_port, dev_port, baudrate)

            #############################################################
            # PLC通信プロセスの動作開始
            #############################################################
            self.startPlcProcess()

            #############################################################
            # PLC初期値書き込み
            #############################################################
            # NOTE:リセットパラメータ
            self.resetParam()
            self.updateWritedata()

            #############################################################
            # メインのループ動作
            #############################################################
            cnt = 100
            self.updateRobotStatus(val="INIT")

            while True:
                ini = perf_counter()

                self.mySleep(0.001)
                #####################################################################
                # NOTE:読み込み用のデータ更新（1ループ/１回制限）
                #####################################################################
                self.updateReaddata()

                #############################################################
                # プログラムバージョンとロボット番号を書き込み
                #############################################################
                self.writeInRobotformation(robot_name)

                #####################################################################
                # NOTE:ロボットステータス取得
                #####################################################################

                self.rb_api.getRobotStatus()

                #####################################################################
                # NOTE:現在地を送信
                #####################################################################

                self.updateCurrentPos()

                #####################################################################
                # NOTE:INIT STATUS
                #####################################################################

                if self.checkRobotStatus(val="INIT"):
                    # NOTE:REQ_INITIAL確認
                    if self.checkBin(tag="REQ_COM", key="INITIAL", val=1):
                        # NOTE：運転準備
                        self.rb_api.readyRobot()
                        self.updateFlag(key="INITIAL", val=True)
                        self.updateBin(tag='CMP_COM', key="INITIAL", val=1)
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="ORIGIN")

                    # NOTE:REQ_ALARM_RESET確認
                    if self.checkBin(tag="REQ_COM", key='RESET_ALARM', val=1):
                        # NOTE:リセットパラメータ
                        self.resetParam()
                        # NOTE:停止
                        self.rb_api.stopRobot()
                        # NOTE:クリア
                        self.rb_api.resetError()
                        self.updateBin(tag='CMP_COM', key='RESET_ALARM', val=1)

                    elif self.checkBin(tag="REQ_COM", key='RESET_ALARM', val=0):
                        self.updateBin(tag='CMP_COM', key='RESET_ALARM', val=0)

                #####################################################################
                # NOTE:ORIGIN STATUS
                #####################################################################
                elif self.checkRobotStatus(val="ORIGIN"):
                    # NOTE:エラー確認
                    if self.rb_api.error:
                        self.updateBin(tag='STATUS_COM', key='ERR', val=1)
                        self.updateWord(tag='PC_ERR_CODE',
                                        val=self.rb_api.error_id)
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="ERROR")

                    elif not self.rb_api.error:
                        self.updateBin(tag='STATUS_COM', key='ERR', val=0)
                        self.updateWord(tag='PC_ERR_CODE', val=0)
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="ORIGIN")
                        
                    # NOTE:REQ_ORIGIN確認
                    if self.checkBin(tag="REQ_COM", key="ORIGIN", val=1):
                        if not self.checkFlag(key="ORIGIN"):
                            self.updateFlag(key="ORIGIN", val=True)
                            if self.checkBin(tag="STATUS_COM", key="AUTO", val=1) and not self.rb_api.origin:
                                # 　原点復帰
                                self.rb_api.moveOrigin()
                            elif self.checkBin(tag="STATUS_COM", key="AUTO", val=0):
                                # 　原点復帰
                                self.rb_api.moveOrigin()
                        elif self.checkFlag(key="ORIGIN"):
                            if self.rb_api.origin:
                                print(
                                    "#######################ORIGIN COMP#######################")
                                self.OriginComp()
                                # NOTE:ロボットステータス変更
                                self.updateRobotStatus(val="IDLE")

                    # # NOTE:REQ_ALARM_RESET確認
                    if self.checkBin(tag="REQ_COM", key='RESET_ALARM', val=1):
                        # NOTE:リセットパラメータ
                        self.resetParam()
                        # NOTE:停止
                        self.rb_api.stopRobot()
                        # NOTE:クリア
                        self.rb_api.resetError()
                        self.updateBin(tag='CMP_COM', key='RESET_ALARM', val=1)

                    # elif self.checkBin(tag="REQ_COM",key='RESET_ALARM',val=0):
                    # 立ち下がり
                    if self.triggerDown(tag="REQ_COM", key="RESET_ALARM"):
                        self.updateBin(tag='CMP_COM', key='RESET_ALARM', val=0)
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="INIT")

                    # NOTE:REQ_MOVE確認
                    self.updateFlag(key="REQ_MOVE_UP", val=self.triggerUp(
                        tag="REQ_COM", key="MOVE"))
                    if self.checkFlag(key="REQ_MOVE_UP"):
                        self.updateDebugPhase(key="DEBUG", val="REQ_MOVE_UP")
                        self.updateFlag(key="OPERATING", val=True)

                    # NOTE:REQ_STOP確認
                    if self.checkBin(tag="REQ_COM", key='STOP', val=1):
                        self.updateDebugPhase(key="DEBUG", val="REQ_STOP_TRUE")
                        # NOTE:停止
                        self.rb_api.stopRobot()
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="STOP")

                    # NOTE:自動運転モード
                    self.autoMode()

                #####################################################################
                # NOTE:ERROR STATUS
                #####################################################################
                elif self.checkRobotStatus(val="ERROR"):
                    # NOTE:REQ_ALARM_RESET確認
                    if self.checkBin(tag="REQ_COM", key='RESET_ALARM', val=1):
                        # NOTE:リセットパラメータ
                        self.resetParam()
                        # NOTE:停止
                        self.rb_api.stopRobot()
                        # NOTE:クリア
                        self.rb_api.resetError()
                        self.updateBin(tag='CMP_COM', key='RESET_ALARM', val=1)

                    elif self.checkBin(tag="REQ_COM", key='RESET_ALARM', val=0):
                        self.updateBin(tag='CMP_COM', key='RESET_ALARM', val=0)

                    # NOTE:エラー確認
                    if self.rb_api.error:
                        self.updateBin(tag='STATUS_COM', key='ERR', val=1)
                        self.updateWord(tag='PC_ERR_CODE',
                                        val=self.rb_api.error_id)
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="ERROR")

                    elif not self.rb_api.error:
                        self.updateBin(tag='STATUS_COM', key='ERR', val=0)
                        self.updateWord(tag='PC_ERR_CODE', val=0)
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="INIT")

                #####################################################################
                # NOTE:STOP STATUS
                #####################################################################
                elif self.checkRobotStatus(val="STOP"):
                    # 20230823変更 CMP_COM MOVE OFF
                    self.updateBin(tag='CMP_COM', key="MOVE", val=0)
                    self.resetPhase(key="MOVE")
                    self.updateFlag(key="REQ_MOVE_UP", val=False)
                    self.updateFlag(key="OPERATING", val=False)

                    if self.triggerDown(tag="REQ_COM", key="STOP"):
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="IDLE")

                #####################################################################
                # NOTE:IDLE STATUS
                #####################################################################
                elif self.checkRobotStatus(val="IDLE"):
                    # NOTE:エラー確認
                    if self.rb_api.error:
                        self.updateBin(tag='STATUS_COM', key='ERR', val=1)
                        self.updateWord(tag='PC_ERR_CODE',
                                        val=self.rb_api.error_id)
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="ERROR")

                    elif not self.rb_api.error:
                        self.updateBin(tag='STATUS_COM', key='ERR', val=0)
                        self.updateWord(tag='PC_ERR_CODE', val=0)
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="IDLE")

                    # NOTE:REQ_ALARM_RESET確認
                    if self.checkBin(tag="REQ_COM", key='RESET_ALARM', val=1):
                        # NOTE:リセットパラメータ
                        self.resetParam()
                        # NOTE:停止
                        self.rb_api.stopRobot()
                        # NOTE:クリア
                        self.rb_api.resetError()
                        self.updateBin(tag='CMP_COM', key='RESET_ALARM', val=1)

                    elif self.checkBin(tag="REQ_COM", key='RESET_ALARM', val=0):
                        self.updateBin(tag='CMP_COM', key='RESET_ALARM', val=0)

                    # NOTE:REQ_MOVE確認
                    self.updateFlag(key="REQ_MOVE_UP", val=self.triggerUp(
                        tag="REQ_COM", key="MOVE"))
                    if self.checkFlag(key="REQ_MOVE_UP"):
                        self.updateDebugPhase(key="DEBUG", val="REQ_MOVE_UP")
                        self.updateFlag(key="OPERATING", val=True)

                    # NOTE:REQ_STOP確認
                    if self.checkBin(tag="REQ_COM", key='STOP', val=1):
                        self.updateDebugPhase(key="DEBUG", val="REQ_STOP_TRUE")
                        # NOTE:停止
                        self.rb_api.stopRobot()
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="STOP")

                    # NOTE:自動運転モード
                    self.autoMode()

                #####################################################################
                # NOTE:RUN STATUS
                #####################################################################
                elif self.checkRobotStatus(val="RUN"):
                    # NOTE:エラー確認
                    if self.rb_api.error:
                        self.updateBin(tag='STATUS_COM', key='ERR', val=1)
                        self.updateWord(tag='PC_ERR_CODE',
                                        val=self.rb_api.error_id)
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="ERROR")

                    elif not self.rb_api.error:
                        self.updateBin(tag='STATUS_COM', key='ERR', val=0)
                        self.updateWord(tag='PC_ERR_CODE', val=0)
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="IDLE")

                    # NOTE:REQ_STOP確認
                    if self.checkBin(tag="REQ_COM", key='STOP', val=1):
                        self.updateDebugPhase(key="DEBUG", val="REQ_STOP_TRUE")
                        # NOTE:停止
                        self.rb_api.stopRobot()
                        # NOTE:ロボットステータス変更
                        self.updateRobotStatus(val="STOP")

                #####################################################################
                # NOTE:生存確認
                #####################################################################
                self.heartBeat()

                #####################################################################
                # NOTE:書き込み用のデータ更新（1ループ/１回制限）
                #####################################################################
                self.updateWritedata()

                #####################################################################
                # NOTE:前周期の値を保持
                #####################################################################
                self.saveInternalData()
                self.savePlcDataMain()

                #####################################################################
                # NOTE:ループカウント
                #####################################################################

                if cnt > 50:
                    # self.rb_api.printRobotStatus()
                    # print("#ERROR CODE:{}    #ROBBOT MODE:{}     #SEQ STATUS:{}     #MOVE PHASE:{}    #DEBUG PHASE:{}        #PROG CYCLE:{}[s]".format(self.rb_api.error_id,self.rb_api.robot_mode,self.in_phase["ROBOT_STATUS"],self.in_phase["MOVE"],self.in_phase["DEBUG"],round((perf_counter()-ini),6)))
                    # print("#ERROR CODE:{}    #ROBBOT MODE:{}     #SEQ STATUS:{}    #PROG CYCLE:{}[ms]".format(
                    #     self.rb_api.error_id, self.rb_api.robot_mode, self.in_phase["ROBOT_STATUS"], round((perf_counter()-ini)*1000, 3)))
                    # ##0901注释
                    cnt = 0

                else:
                    cnt += 1
        #except Exception as e:
        #    print(f"main program Exception {e}")

        except KeyboardInterrupt:
            self.p1.terminate()


if __name__ == "__main__":
    rb_main = RobotController()
    rb_main.main()
