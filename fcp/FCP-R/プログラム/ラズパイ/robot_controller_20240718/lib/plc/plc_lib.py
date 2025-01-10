# ===============================================================================
# Name      : plc_sequence.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2022-11-09 10:58
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================

# -*- coding: utf-8 -*-
import copy
from .plc_base_class import BasePLC
from .api.plc_comm import convert_signed
from . import load_excel as g_set
from typing import List, Tuple
from time import perf_counter, sleep

xlsx_file = 'setting_Vision_W.xlsx'

# NOTE: エクセルから変換したアドレスマップ
RANGE: dict = g_set.getParamDict(book_name=xlsx_file, sheet_name="RANGE")
IN_W: dict = g_set.getWdataDict(book_name=xlsx_file, sheet_name="IN_W")
IN_D: dict = g_set.getDdataDict(book_name=xlsx_file, sheet_name="IN_D")
OUT_W: dict = g_set.getWdataDict(book_name=xlsx_file, sheet_name="OUT_W")
OUT_D: dict = g_set.getDdataDict(book_name=xlsx_file, sheet_name="OUT_D")


def word2bit(input_word_data: int) -> List[int]:
    # データがあれば
    # if (len(input_word_data) > 1):
    word_data_str = format(input_word_data, '016b')
    word_data_ary = list(word_data_str)
    word_data_ary.reverse()
    # strのリストを数値に変換()
    return list(map(int, word_data_ary))


def bit2word(input_binary_data: list) -> int:
    input_binary_data_buf = copy.deepcopy(input_binary_data)
    input_binary_data_buf.reverse()
    binary_data_str = str(input_binary_data_buf)
    revised_binary_data_str = '0b' + binary_data_str[1:len(binary_data_str) - 1].replace(', ', '')
    word_data = eval(revised_binary_data_str)
    return word_data


class PlcSeq(BasePLC):
    __version__ = '1.0.0'

    def __init__(self):
        super().__init__()

        self.IN_D_AD = self.get_address_d_in()
        self.OUT_D_AD = self.get_address_d_out()
        self.IN_W_AD = self.get_address_w_in()
        self.OUT_W_AD = self.get_address_w_out()

        # NOTE: 内部保持変数
        self._out_word_list = [[0 for i in range(16)] for j in range(int(RANGE['OUT_W']))]

    # ===============================================================================
    # NOTE: 素材
    # ===============================================================================

    def get_address_d_in(self) -> dict:
        data = {}
        for key in IN_D.keys():
            # print(key)
            data[key] = RANGE['IN_D_NO'] + IN_D[key]
        return data

    def get_address_d_out(self) -> dict:
        data = {}
        for key in OUT_D.keys():
            data[key] = RANGE['OUT_D_NO'] + OUT_D[key]
        return data

    def get_address_w_in(self) -> dict:
        data = {}
        for key in IN_W.keys():
            # print(key)
            data[key] = RANGE['IN_W_NO'] + IN_W[key]
        return data

    def get_address_w_out(self) -> dict:
        data = {}
        for key in OUT_W.keys():
            data[key] = RANGE['OUT_W_NO'] + OUT_W[key]
        return data

    def update_word(self, tag: str, key: str, val: int) -> None:
        self._out_word_list[OUT_W[tag]][OUT_W[key]] = val

    def bit2word(self, bit_16: list) -> int:
        word = bit2word(bit_16)
        return word

    # ===============================================================================
    # NOTE: メソッド
    # ===============================================================================

    def read_in_w(self, tag: str = 'REQ') -> Tuple[bool, list]:
        # NOTE: 新ラダーは'word' 旧ラダーは'bit'
        ret, data = self.read_data_from_plc(d_type='bit',
                                            addr=self.IN_W_AD[tag])
        if ret:
            bit_16 = word2bit(data[0])
            return True, bit_16
        else:
            return False, [0]

    def read_in_w_bit(self, tag: str = 'REQ',
                      key: str = 'INSPECT_START') -> int:
        ret, data = self.read_in_w(tag)
        if ret:
            s_bit = data[IN_W[key]]
            return s_bit
        else:
            return -1

    def write_out_w(self, data: list, tag: str) -> bool:
        bit_16 = data[OUT_W[tag]]
        send_data = self.bit2word(bit_16)
        addr = self.OUT_W_AD[tag]
        # print(send_data)
        # NOTE: 新ラダーは'word' 旧ラダーは'bit'
        ret = self.write_data_to_plc(d_type='bit',
                                     addr=addr,
                                     data=[send_data])
        return ret

    def check_bit(self, tag: str, key: str, val: int, timeout: int = 1000) -> bool:
        timer_count = 0
        start_time = perf_counter()
        _match = False
        addr = self.IN_W_AD[tag]
        while timer_count < timeout:
            # NOTE: dataはリストで返却
            # NOTE: 新ラダーは'word' 旧ラダーは'bit'
            success, data = self.read_data_from_plc(d_type='bit', addr=addr, timeout=timeout)
            if success:
                bit_16 = word2bit(data[0])
                s_bit = bit_16[IN_W[key]]
                if s_bit == val:
                    _match = True
                    break
                else:
                    timer_count = int((perf_counter() - start_time) * 1000)
                    continue
            # TODO: タイムアウトと通信失敗を切り分けできるように
            else:
                timer_count = int((perf_counter() - start_time) * 1000)
                continue
        return _match

    # ===============================================================================
    # NOTE: 通信確認
    # ===============================================================================

    def communication_confirmation(self) -> bool:
        # NOTE: 初回起動時、原点復帰後に実施

        # NOTE: W(x_out).00-01 <Write> プログラム起動時に初期化
        self.update_word('STATUS', 'PC_ONLINE', 0)
        self.update_word('STATUS', 'PC_READY', 0)
        self.write_out_w(self._out_word_list, 'STATUS')

        # NOTE: W(x_out).08-11 <Write> プログラム起動時に初期化（検査系）
        self.update_word('STATUS', 'INSPECTING', 0)
        self.update_word('STATUS', 'INSPECT_OK', 0)
        self.update_word('STATUS', 'INSPECT_NG', 0)
        self.update_word('STATUS', 'INSPECT_ERR', 0)
        self.write_out_w(self._out_word_list, 'STATUS')

        # NOTE:  W(x_out).00 <Write> PCの電源がONであることをPLCに通達
        self.update_word('STATUS', 'PC_ONLINE', 1)
        self.write_out_w(self._out_word_list, 'STATUS')

        # NOTE: W(x_in).01 <Read> Request Readyがオンになっていることを確認
        ret = self.check_bit('REQ', 'READY', 1, timeout=5000)
        if not ret:
            print('request ready 1 false')
            return False

        # NOTE: W(x_out).01 <Write> PLC側のW(2).01を確認したことを通達
        self.update_word('STATUS', 'PC_READY', 1)
        self.write_out_w(self._out_word_list, 'STATUS')

        # NOTE: W(x_in).01 <Read> PLC側が通達を確認
        ret = self.check_bit('REQ', 'READY', 0, timeout=5000)
        if not ret:
            print('request ready 0 false')
            return False

        # NOTE: W(x_out).01 <Write> 初期通信確認終了
        self.update_word('STATUS', 'PC_READY', 0)
        self.write_out_w(self._out_word_list, 'STATUS')

        return True

    # ===============================================================================
    # NOTE: 撮像状況の送信
    # ===============================================================================

    def send_camera_status(self, capturing: bool) -> bool:
        # NOTE: 撮像中はcapturing = True
        if capturing:
            self.update_word('STATUS', 'CAPTURE', 1)
        else:
            self.update_word('STATUS', 'CAPTURE', 0)

        ret = self.write_out_w(self._out_word_list, 'STATUS')
        return ret

    # ===============================================================================
    # NOTE: 補正量送信
    # ===============================================================================

    def send_alignment_data(self, data: list) -> bool:
        # NOTE: 一応intに変換
        data = [int(v) for v in data]
        send_data = convert_signed(data)
        ret = self.write_data_to_plc(d_type='word',
                                     addr_min=self.OUT_D_AD['ALIGN_X_HIGH'],
                                     addr_max=self.OUT_D_AD['ALIGN_R_LOW'],
                                     multi=True,
                                     data=send_data)
        return ret

    # ===============================================================================
    # NOTE: 基準量送信
    # ===============================================================================

    def send_base_align_data(self, data: list) -> bool:
        # NOTE: 一応intに変換
        data = [int(v) for v in data]
        send_data = convert_signed(data)
        ret = self.write_data_to_plc(d_type='word',
                                     addr_min=self.OUT_D_AD['B_ALIGN_X_HIGH'],
                                     addr_max=self.OUT_D_AD['B_ALIGN_R_LOW'],
                                     multi=True,
                                     data=send_data)
        return ret

    # ===============================================================================
    # NOTE: 検査内容の取得
    # ===============================================================================

    def get_inspection_config(self) -> Tuple[bool, int, int, int]:
        # NOTE: DM(x_in+1,+2,+3) ワーク機種
        ret, data = self.read_data_from_plc(d_type='word',
                                            addr_min=self.IN_D_AD['PROGRAM_NO'],
                                            addr_max=self.IN_D_AD['MODEL_NO'],
                                            multi=True)
        # [program_no, config_no, model_no]
        if ret:
            return True, data[0], data[1], data[2]
        else:
            return False, -1, -1, -1

    # ===============================================================================
    # NOTE: 検査の開始
    # ===============================================================================

    def send_inspection_start(self) -> None:
        # NOTE: W(x_out).08 検査フラグ送信
        self.update_word('STATUS', 'INSPECTING', 1)
        self.write_out_w(self._out_word_list, 'STATUS')

    # ===============================================================================
    # NOTE: 検査結果の送信
    # ===============================================================================

    def send_inspection_results(self,
                                status: int,
                                data: list,
                                b_data: list = [0, 0, 0, 0],
                                ngcode: int = 0
                                ) -> bool:

        # NOTE: status : ok:1 ng:2 err:3

        # NOTE: 現在位置書き込み
        ret = self.send_alignment_data(data)
        # NOTE: 基準位置書き込み
        ret = self.send_base_align_data(b_data)

        # NOTE: post NG Code
        if status == 2:
            ret = self.write_data_to_plc(
                d_type='word',
                addr=self.OUT_D_AD['NG_CODE'],
                data=[int(ngcode)]
            )

        # NOTE: W(x_out).08-11 検査フラグ送信
        self.update_word('STATUS', 'INSPECTING', 0)
        self.update_word('STATUS', 'INSPECT_OK', 1)
        self.update_word('STATUS', 'INSPECT_NG', 0)
        self.update_word('STATUS', 'INSPECT_ERR', 0)
        self.write_out_w(self._out_word_list, 'STATUS')

        # NOTE: W(x_in).09 検査終了確認
        ret = self.check_bit('REQ', 'INSPECT_RCV', 1, timeout=5000)
        if not ret:
            print('inspect_rcv 1 false')
            return False

        # NOTE: W(x_out).09-11 検査結果削除
        self.update_word('STATUS', 'INSPECT_OK', 0)
        self.update_word('STATUS', 'INSPECT_NG', 0)
        self.update_word('STATUS', 'INSPECT_ERR', 0)
        self.write_out_w(self._out_word_list, 'STATUS')

        return True

    # ===============================================================================
    # NOTE: エラーのポスト
    # ===============================================================================

    def post_error_code(self, error_code: int) -> None:

        self.success = self.write_data_to_plc(
            d_type='word',
            addr=self.OUT_D_AD['ERR_CODE'],
            data=[int(error_code)]
        )

        self.update_word('STATUS', 'PC_ERR', 1)
        self.write_out_w(self._out_word_list, 'STATUS')

        # TODO: ここは無限タイムアウトじゃないと
        ret = self.check_bit('REQ', 'RST_PC_ERR', 1, timeout=1000)
        if not ret:
            return

        self.update_word('STATUS', 'PC_ERR', 0)
        self.write_out_w(self._out_word_list, 'STATUS')

    def pc_online(self) -> bool:
        self.update_word('STATUS', 'PC_ONLINE', 1)
        ret = self.write_out_w(self._out_word_list, 'STATUS')
        return ret

    # ===============================================================================
    # NOTE: キャリブレーション関連
    # ===============================================================================

    def calibration_seq(self) -> None:
        # NOTE: W(x_out).00-01 <Write> プログラム起動時に初期化
        self.update_word('STATUS', 'PC_ONLINE', 0)
        self.update_word('STATUS', 'PC_READY', 0)
        self.write_out_w(self._out_word_list, 'STATUS')

        # NOTE: キャリブレーションスタート
        self.update_word('STATUS', 'PC_ONLINE', 0)
        self.update_word('STATUS', 'PC_READY', 0)
        self.write_out_w(self._out_word_list, 'STATUS')


def _main():
    plc = PlcSeq()

    param = dict(ip='192.168.14.1',
                 port='9600',
                 manufacturer='omron',
                 series='',
                 plc_protocol='fins',
                 transport_protocol='udp',
                 bit='W',
                 word='DM',
                 double_word='')  # NOTE: ダブルワード

    plc.load_param(param)
    try:
        while True:
            # NOTE: 一括読取
            ret, data = plc.read_in_w()
            if ret:
                if data[IN_W['INSPECT_START']] == 1:

                    print('inspection_start')
                    plc.send_camera_status(True)
                    sleep(1)
                    plc.send_camera_status(False)
                    plc.get_inspection_config()
                    # NOTE: 単位はum
                    ret = plc.send_inspection_results(1, [-1, 2, 3, -4])
                    if ret:
                        print('inspection success')
                    else:
                        print('inspection failed')

                elif data[IN_W['READY']] == 1:

                    print('Communication Confirmation')
                    ret = plc.communication_confirmation()
                    if ret:
                        print('commconfirm success')
                    else:
                        print('commconfirm failed')

            plc.pc_online()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    # print(RANGE)
    _main()
