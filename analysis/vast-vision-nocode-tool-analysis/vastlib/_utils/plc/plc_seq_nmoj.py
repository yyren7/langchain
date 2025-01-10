# ===============================================================================
# Name      : plc_sequence.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-04-19 17:16
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================
import copy
from typing import List, Tuple
from time import perf_counter, sleep
from .plc_base_class import BasePLC
from .api.plc_comm import convert_signed
from . import read_excel as g_set
try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


def word2bit(input_word_data: int) -> List[int]:
    """数値を16bitに変換"""
    word_data_str = format(input_word_data, '016b')
    word_data_ary = list(word_data_str)
    word_data_ary.reverse()
    # strのリストを数値に変換()
    return list(map(int, word_data_ary))


def bit2word(input_binary_data: list) -> int:
    """16bitのlistを数値に変換"""
    input_binary_data_buf = copy.deepcopy(input_binary_data)
    input_binary_data_buf.reverse()
    binary_data_str = str(input_binary_data_buf)
    revised_binary_data_str = '0b' + binary_data_str[1:len(binary_data_str) - 1].replace(', ', '')
    word_data = eval(revised_binary_data_str)
    return word_data


# ===============================================================================
# NOTE: エクセルのアドレス関連
# ===============================================================================
def get_device_map(xlsx_file: str, map_id: int) -> dict:
    """デバイスのINDEXを取得"""
    if map_id == 0:
        return g_set.getHeaderAddress(book_name=xlsx_file, sheet_name="CONFIG")
    elif map_id == 1:
        # NOTE: PLC->PCのBitデバイス
        return g_set.getBitData(book_name=xlsx_file, sheet_name="BIT_IN")
    elif map_id == 2:
        # NOTE: PLC->PCのWordデバイス
        return g_set.getWordData(book_name=xlsx_file, sheet_name="WORD_IN")
    elif map_id == 3:
        # NOTE: PC->PLCのBitデバイス
        return g_set.getBitData(book_name=xlsx_file, sheet_name="BIT_OUT")
    elif map_id == 4:
        # NOTE: PC->PLCのWordデバイス
        return g_set.getWordData(book_name=xlsx_file, sheet_name="WORD_OUT")
    else:
        return {}


def get_address_map(device_map: dict, header_address: int) -> dict:
    """アドレスマップを取得"""
    data = {}
    for key in device_map.keys():
        data[key] = header_address + device_map[key]
    return data


class PlcSeq(BasePLC):
    __version__ = '1.0.0'

    def __init__(self, excel_path: str = './vision_setting.xlsx'):
        super().__init__()
        self.load_excel(excel_path)

    def load_excel(self, path: str):
        """エクセルファイルからアドレスマップを取得"""
        # NOTE: 各キー、タグのインデックス
        header_address = get_device_map(path, 0)
        self.IN_BIT_IDX = get_device_map(path, 1)
        self.IN_WORD_IDX = get_device_map(path, 2)
        self.OUT_BIT_IDX = get_device_map(path, 3)
        self.OUT_WORD_IDX = get_device_map(path, 4)

        # NOTE: 各キー、タグのアドレス
        self.IN_BIT_AD = get_address_map(self.IN_BIT_IDX, header_address['IN_BIT_NO'])
        self.IN_WORD_AD = get_address_map(self.IN_WORD_IDX, header_address['IN_WORD_NO'])
        self.OUT_BIT_AD = get_address_map(self.OUT_BIT_IDX, header_address['OUT_BIT_NO'])
        self.OUT_WORD_AD = get_address_map(self.OUT_WORD_IDX, header_address['OUT_WORD_NO'])

        # NOTE: 内部保持変数 0で初期化
        # TODO: レンジをエクセルからとってくる、今は３
        self._pub_word_list = [[0 for i in range(16)] for j in range(3)]

        self.plc_config = g_set.getPLCParam(path, 'CONFIG')
        self.load_param(self.plc_config)

    def get_plc_config(self) -> dict:
        return self.plc_config

    def update_bit_as_word(self, tag: str, key: str, val: int) -> None:
        """内部管理しているbitを更新"""
        self._pub_word_list[self.OUT_BIT_IDX[tag]][self.OUT_BIT_IDX[key]] = val

    def read_bit_list(self, tag: str = 'REQ') -> Tuple[bool, list]:
        """Wordで読み取ってBitをListに変換"""
        ret, data = self.read_data_from_plc(d_type='bit',
                                            addr=self.IN_BIT_AD[tag])
        if ret:
            bit_16 = word2bit(data[0])
            return True, bit_16
        else:
            return False, [0]

    def read_bit(self, tag: str = 'REQ', key: str = 'INSPECT_START') -> int:
        """Wordで読み取ってBitに分解"""
        ret, data = self.read_bit_list(tag)
        if ret:
            s_bit = data[self.IN_BIT_IDX[key]]
            return s_bit
        else:
            return -1

    def write_bit_as_word(self, data: list, tag: str) -> bool:
        """Bitの状態をWord単位で書き込む"""
        bit_16 = data[self.OUT_BIT_IDX[tag]]
        send_data = bit2word(bit_16)
        addr = self.OUT_BIT_AD[tag]
        ret = self.write_data_to_plc(d_type='bit',
                                     addr=addr,
                                     data=[send_data])
        return ret

    def check_bit(self, tag: str, key: str, val: int, timeout: int = 1000) -> bool:
        """Bitの状態確認"""
        timer_count = 0
        start_time = perf_counter()
        _match = False
        addr = self.IN_BIT_AD[tag]
        while timer_count < timeout:
            # NOTE: dataはリストで返却
            success, data = self.read_data_from_plc(d_type='bit', addr=addr, timeout=timeout)
            if success:
                bit_16 = word2bit(data[0])
                s_bit = bit_16[self.IN_BIT_IDX[key]]
                if s_bit == val:
                    _match = True
                    break
                else:
                    # NOTE: 不一致
                    timer_count = int((perf_counter() - start_time) * 1000)
                    continue
            # TODO: タイムアウトと通信失敗を切り分けできるように
            else:
                # NOTE: 通信失敗
                timer_count = int((perf_counter() - start_time) * 1000)
                continue
        return _match

    # ===============================================================================
    # NOTE: 通信確認
    # ===============================================================================

    def communication_confirmation(self) -> bool:
        """Ready信号に対する応答"""
        # NOTE: 初回起動時、原点復帰後に実施

        # NOTE: W(x_out).00-01 <Write> プログラム起動時に初期化
        self.update_bit_as_word('STATUS', 'PC_ONLINE', 0)
        self.update_bit_as_word('STATUS', 'PC_READY', 0)
        self.write_bit_as_word(self._pub_word_list, 'STATUS')

        # NOTE: W(x_out).08-11 <Write> プログラム起動時に初期化（検査系）
        self.update_bit_as_word('STATUS', 'INSPECTING', 0)
        self.update_bit_as_word('STATUS', 'INSPECT_OK', 0)
        self.update_bit_as_word('STATUS', 'INSPECT_NG', 0)
        self.update_bit_as_word('STATUS', 'INSPECT_ERR', 0)
        self.write_bit_as_word(self._pub_word_list, 'STATUS')

        # NOTE:  W(x_out).00 <Write> PCの電源がONであることをPLCに通達
        self.update_bit_as_word('STATUS', 'PC_ONLINE', 1)
        self.write_bit_as_word(self._pub_word_list, 'STATUS')

        # NOTE: W(x_in).01 <Read> Request Readyがオンになっていることを確認
        ret = self.check_bit('REQ', 'READY', 1, timeout=5000)
        if not ret:
            logger.debug('Timeout Request Ready [on]')
            return False

        # NOTE: W(x_out).01 <Write> PLC側のW(2).01を確認したことを通達
        self.update_bit_as_word('STATUS', 'PC_READY', 1)
        self.write_bit_as_word(self._pub_word_list, 'STATUS')

        # NOTE: W(x_in).01 <Read> PLC側が通達を確認
        ret = self.check_bit('REQ', 'READY', 0, timeout=5000)
        if not ret:
            logger.debug('Timeout Request Ready [off]')
            return False

        # NOTE: W(x_out).01 <Write> 初期通信確認終了
        self.update_bit_as_word('STATUS', 'PC_READY', 0)
        self.write_bit_as_word(self._pub_word_list, 'STATUS')

        logger.debug('Ready Sequence Complete')

        return True

    def send_camera_status(self, capturing: bool) -> bool:
        """撮像ステータスの送信"""
        # NOTE: 撮像中はcapturing = True
        if capturing:
            self.update_bit_as_word('STATUS', 'CAPTURE', 1)
        else:
            self.update_bit_as_word('STATUS', 'CAPTURE', 0)

        ret = self.write_bit_as_word(self._pub_word_list, 'STATUS')
        return ret

    def send_inspection_start(self) -> None:
        """検査中の信号を送信"""
        # NOTE: W(x_out).08 検査フラグ送信
        self.update_bit_as_word('STATUS', 'INSPECTING', 1)
        self.write_bit_as_word(self._pub_word_list, 'STATUS')

    def get_inspection_config(self) -> Tuple[bool, int, int, int]:
        """検査番号の取得"""
        # NOTE: DM(x_in+1,+2,+3) ワーク機種
        ret, data = self.read_data_from_plc(d_type='word',
                                            addr_min=self.IN_WORD_AD['PROGRAM_NO'],
                                            addr_max=int(self.IN_WORD_AD['MODEL_NO'] + 1),
                                            multi=True)
        if ret:
            return True, data[0], data[1], data[2]
        else:
            return False, -1, -1, -1

    def send_alignment_data(self, data: list) -> bool:
        """補正量を送信"""
        # NOTE: 一応intに変換
        data = [int(v) for v in data]
        # NOTE: 符号付きの形式に変換
        send_data = convert_signed(data)
        ret = self.write_data_to_plc(d_type='word',
                                     addr_min=self.OUT_WORD_AD['ALIGN_X_HIGH'],
                                     addr_max=self.OUT_WORD_AD['ALIGN_R_LOW'],
                                     multi=True,
                                     data=send_data)
        return ret

    def send_base_align_data(self, data: list) -> bool:
        """基準量を送付"""
        # NOTE: 一応intに変換
        data = [int(v) for v in data]
        # NOTE: 符号付きの形式に変換
        send_data = convert_signed(data)
        ret = self.write_data_to_plc(d_type='word',
                                     addr_min=self.OUT_WORD_AD['B_ALIGN_X_HIGH'],
                                     addr_max=self.OUT_WORD_AD['B_ALIGN_R_LOW'],
                                     multi=True,
                                     data=send_data)
        return ret

    def send_num_work(self, num: int) -> bool:
        try:
            ret = self.write_data_to_plc(
                d_type='word',
                addr=self.OUT_WORD_AD['NUM_WORK'],
                data=[int(num)]
            )
        except Exception:
            return False

        return ret

    def send_inspection_results(self,
                                status: int,
                                data: list,
                                b_data: list = [0, 0, 0, 0],
                                ngcode: int = 0
                                ) -> bool:
        """検査結果を送信"""
        # NOTE: status : ok:1 ng:2 err:3

        # NOTE: 現在位置書き込み
        ret = self.send_alignment_data(data)
        # NOTE: 基準位置書き込み
        ret = self.send_base_align_data(b_data)

        # NOTE: post NG Code
        if status == 2:
            ret = self.write_data_to_plc(
                d_type='word',
                addr=self.OUT_WORD_AD['NG_CODE'],
                data=[int(ngcode)]
            )

        judge_list = [0, 0, 0, 0]
        judge_list[status] = 1

        # NOTE: W(x_out).08-11 検査フラグ送信
        self.update_bit_as_word('STATUS', 'INSPECTING', 0)
        self.update_bit_as_word('STATUS', 'INSPECT_OK', judge_list[1])
        self.update_bit_as_word('STATUS', 'INSPECT_NG', judge_list[2])
        self.update_bit_as_word('STATUS', 'INSPECT_ERR', judge_list[3])
        self.write_bit_as_word(self._pub_word_list, 'STATUS')

        # NOTE: W(x_in).09 検査終了確認
        ret = self.check_bit('REQ', 'INSPECT_RCV', 1, timeout=5000)
        if not ret:
            logger.debug('Timeout Inspection Recv [on]')
            return False

        # NOTE: W(x_out).09-11 検査結果削除
        self.update_bit_as_word('STATUS', 'INSPECT_OK', 0)
        self.update_bit_as_word('STATUS', 'INSPECT_NG', 0)
        self.update_bit_as_word('STATUS', 'INSPECT_ERR', 0)
        self.write_bit_as_word(self._pub_word_list, 'STATUS')

        logger.debug('Inspection Sequence Complete')

        return True

    def post_error_code(self, error_code: int) -> None:
        """エラーを吐く"""
        self.success = self.write_data_to_plc(
            d_type='word',
            addr=self.OUT_WORD_AD['ERR_CODE'],
            data=[int(error_code)]
        )

        self.update_bit_as_word('STATUS', 'PC_ERR', 1)
        self.write_bit_as_word(self._pub_word_list, 'STATUS')

        # # TODO: ここは無限タイムアウトじゃないと
        # ret = self.check_bit('REQ', 'RST_PC_ERR', 1, timeout=1000)
        # if not ret:
        #     return

        # self.update_bit_as_word('STATUS', 'PC_ERR', 0)
        # self.write_bit_as_word(self._pub_word_list, 'STATUS')

    def pc_online(self, on: bool = True) -> bool:
        """PC Online"""
        if on:
            self.update_bit_as_word('STATUS', 'PC_ONLINE', 1)
        else:
            self.update_bit_as_word('STATUS', 'PC_ONLINE', 0)
        ret = self.write_bit_as_word(self._pub_word_list, 'STATUS')
        return ret

    def calibration_seq(self) -> None:
        # NOTE: W(x_out).00-01 <Write> プログラム起動時に初期化
        self.update_bit_as_word('STATUS', 'PC_ONLINE', 0)
        self.update_bit_as_word('STATUS', 'PC_READY', 0)
        self.write_bit_as_word(self._pub_word_list, 'STATUS')

        # NOTE: キャリブレーションスタート
        self.update_bit_as_word('STATUS', 'PC_ONLINE', 0)
        self.update_bit_as_word('STATUS', 'PC_READY', 0)
        self.write_bit_as_word(self._pub_word_list, 'STATUS')


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

    in_w = get_device_map('./setting_Vision_W.xlsx', 1)

    try:
        while True:
            # NOTE: 一括読取
            ret, data = plc.read_bit_list()
            if ret:
                if data[in_w['INSPECT_START']] == 1:

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

                elif data[in_w['READY']] == 1:

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
