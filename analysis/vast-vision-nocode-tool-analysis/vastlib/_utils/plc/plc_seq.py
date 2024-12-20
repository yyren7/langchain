# ===============================================================================
# Name      : plc_sequence.py
# Version   : 1.0.0
# Brief     : NTSZ
# Time-stamp: 2023-05-16 17:40
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================
import copy
from typing import List, Tuple
from time import perf_counter

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

    def __init__(self, excel_path: str):
        super().__init__()
        self.load_excel(excel_path)

    def load_excel(self, path: str):
        """エクセルファイルからアドレスマップを取得"""
        # NOTE: キーと相対アドレス0-15
        header_address = get_device_map(path, 0)
        self.IN_BIT_IDX = get_device_map(path, 1)
        self.IN_WORD_IDX = get_device_map(path, 2)
        self.OUT_BIT_IDX = get_device_map(path, 3)
        self.OUT_WORD_IDX = get_device_map(path, 4)

        # NOTE: キーと絶対アドレス
        self.IN_BIT_AD = get_address_map(self.IN_BIT_IDX, header_address['IN_BIT_NO'])
        self.IN_WORD_AD = get_address_map(self.IN_WORD_IDX, header_address['IN_WORD_NO'])
        self.OUT_BIT_AD = get_address_map(self.OUT_BIT_IDX, header_address['OUT_BIT_NO'])
        self.OUT_WORD_AD = get_address_map(self.OUT_WORD_IDX, header_address['OUT_WORD_NO'])

        # NOTE: 内部保持変数 0で初期化
        # TODO: VASTから見たOUTのBITリスト 今は6Word確保
        self._pub_word_list = [[0 for i in range(16)] for j in range(6)]

        # NOTE: エクセルからPLCのパラメータ(IP,Port,Protocol)を取得&反映
        self.plc_config = g_set.getPLCParam(path, 'CONFIG')
        self.load_param(self.plc_config)

    def get_plc_config(self) -> dict:
        return self.plc_config

    def update_bit_as_word(self, tag: str, key: str, val: int) -> None:
        """内部管理しているbitを更新"""
        self._pub_word_list[self.OUT_BIT_IDX[tag]][self.OUT_BIT_IDX[key]] = val

    def read_bit_list(self, tag: str) -> Tuple[bool, list]:
        """Wordで読み取ってBitをListに変換"""
        ret, data = self.read_data_from_plc(d_type='bit',
                                            addr=self.IN_BIT_AD[tag])
        if ret:
            bit_16 = word2bit(data[0])
            return True, bit_16
        else:
            return False, [0]

    def read_bit(self, tag: str, key: str) -> int:
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

    def check_bit(self, tag: str, key: str,
                  val: int, timeout: int = 1000) -> bool:
        """PLC側のリクエスト、ステータスを確認

        Args:
            tag (str): bitの属性 request, status, complete
            key (str): bitの名前
            val (int): bitの値(0 or 1)が一致すればTrue
            timeout (int, optional): タイムアウト(ms)

        Returns:
            bool: _description_
        """
        timer_count = 0
        start_time = perf_counter()
        addr = self.IN_BIT_AD[tag]
        success = False
        while timer_count < timeout:
            # NOTE: dataはリストで返却
            ret, data = self.read_data_from_plc(d_type='bit', addr=addr, timeout=timeout)

            # NOTE: 通信失敗したらcontinue
            if not ret:
                timer_count = int((perf_counter() - start_time) * 1000)
                continue

            # NOTE: 通信に成功したら値を確認
            bit_16 = word2bit(data[0])
            s_bit = bit_16[self.IN_BIT_IDX[key]]
            if s_bit == val:
                # NOTE: 一致
                success = True
                break
            else:
                # NOTE: 不一致
                timer_count = int((perf_counter() - start_time) * 1000)
                continue
        return success

    def send_camera_status(self, capturing: bool) -> bool:
        """撮像ステータスの送信"""
        # NOTE: 撮像中はcapturing = True
        if capturing:
            self.update_bit_as_word('STATUS_COMMON', 'CAPTURING', 1)
        else:
            self.update_bit_as_word('STATUS_COMMON', 'CAPTURING', 0)

        ret = self.write_bit_as_word(self._pub_word_list, 'STATUS_COMMON')
        return ret

    def send_inspection_start(self) -> None:
        """検査中の信号を送信"""
        # NOTE: W(x_out).08 検査フラグ送信
        self.update_bit_as_word('STATUS_COMMON', 'INSPECTING', 1)
        self.write_bit_as_word(self._pub_word_list, 'STATUS_COMMON')

    def get_inspection_config(self) -> Tuple[bool, List[int]]:
        """各種検査に関する番号の取得"""
        # NOTE: DM(x_in+1,+2,+3) ワーク機種
        # NOTE: int(self.IN_WORD_AD['MODEL_NO']+1)はPOSITION_NOがない場合の配慮
        ret, data = self.read_data_from_plc(d_type='word',
                                            addr_min=self.IN_WORD_AD['PROGRAM_NO'],
                                            addr_max=int(self.IN_WORD_AD['MODEL_NO'] + 1),
                                            multi=True)
        if ret:
            return True, data
        else:
            return False, [-1, -1, -1, -1]

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
                                align_data: list,
                                b_align_data: list = [],
                                ng_code: int = 1,
                                err_code: int = 1,
                                ) -> bool:
        """結果を送信する

        Args:
            status (int): 判定結果 ok:1 ng:2 err:3
            align_data (list): 検出した座標
            b_align_data (list, optional): マスター登録した座標
            ng_code (int, optional): 画像処理のNGコード
            err_code (int, optional): 画像処理のERRORコード

        Returns:
            bool: _description_
        """
        # NOTE: 現在位置書き込み
        ret = self.send_alignment_data(align_data)
        # NOTE: 基準位置書き込み
        if b_align_data:
            ret = self.send_base_align_data(b_align_data)

        # NOTE: 判定がNGの場合NGコードを出力
        if status == 2:
            ret = self.write_data_to_plc(
                d_type='word',
                addr=self.OUT_WORD_AD['NG_CODE'],
                data=[int(ng_code)]
            )
        # NOTE: 判定がERRの場合ERRコードを出力
        elif status == 3:
            ret = self.write_data_to_plc(
                d_type='word',
                addr=self.OUT_WORD_AD['ERR_CODE'],
                data=[int(err_code)]
            )

        # NOTE: ジャッジリストを更新
        judge_list = [0, 0, 0, 0]
        judge_list[status] = 1

        # NOTE: 検査判定を書き込み
        self.update_bit_as_word('COMPLETE_COMMON', 'INSPECT_OK', judge_list[1])
        self.update_bit_as_word('COMPLETE_COMMON', 'INSPECT_NG', judge_list[2])
        self.update_bit_as_word('COMPLETE_COMMON', 'INSPECT_ERR', judge_list[3])
        self.write_bit_as_word(self._pub_word_list, 'COMPLETE_COMMON')
        # NOTE: 検査終了を伝令
        self.update_bit_as_word('STATUS_COMMON', 'INSPECTING', 0)
        self.write_bit_as_word(self._pub_word_list, 'STATUS_COMMON')

        # NOTE: PLC側で検査結果を受けとれたか確認
        ret = self.check_bit('COMPLETE_COMMON', 'INSPECT_RECV_COMP', 1, timeout=5000)
        if not ret:
            return False

        # NOTE: 検査結果を初期化
        self.update_bit_as_word('COMPLETE_COMMON', 'INSPECT_OK', 0)
        self.update_bit_as_word('COMPLETE_COMMON', 'INSPECT_NG', 0)
        self.update_bit_as_word('COMPLETE_COMMON', 'INSPECT_ERR', 0)
        self.write_bit_as_word(self._pub_word_list, 'COMPLETE_COMMON')
        return True

    def post_pc_error(self, err_code: int = 1) -> bool:
        """エラー出力"""
        # NOTE: エラーコードを出力
        self.update_bit_as_word('STATUS_COMMON', 'PC_ERR', 1)
        ret1 = self.write_bit_as_word(self._pub_word_list, 'STATUS_COMMON')
        # NOTE: エラー信号を出力
        ret2 = self.write_data_to_plc(d_type='word',
                                      addr=self.OUT_WORD_AD['PC_ERR_CODE'],
                                      data=[int(err_code)])
        if ret1 and ret2:
            return True
        return False

    def reset_pc_error(self) -> bool:
        """PCエラーをリセット"""
        # NOTE: エラーコードを初期化
        self.update_bit_as_word('STATUS_COMMON', 'PC_ERR', 0)
        ret1 = self.write_bit_as_word(self._pub_word_list, 'STATUS_COMMON')
        # NOTE: エラー信号を初期化
        ret2 = self.write_data_to_plc(d_type='word',
                                      addr=self.OUT_WORD_AD['PC_ERR_CODE'],
                                      data=[0])
        if ret1 and ret2:
            return True
        return False

    def pc_online(self, on: bool = True) -> bool:
        if on:
            self.update_bit_as_word('STATUS_COMMON', 'PC_ONLINE', 1)
        else:
            self.update_bit_as_word('STATUS_COMMON', 'PC_ONLINE', 0)
        ret = self.write_bit_as_word(self._pub_word_list, 'STATUS_COMMON')
        return ret

    def heart_beat(self, pre_beat: bool) -> bool:
        """ラズパイの生存をPLC側に通達"""
        if pre_beat:
            self.pc_online(False)
            return False
        else:
            self.pc_online(True)
            return True

    # def calibration_seq(self) -> None:
    #     # NOTE: W(x_out).00-01 <Write> プログラム起動時に初期化
    #     self.update_bit_as_word('STATUS', 'PC_ONLINE', 0)
    #     self.update_bit_as_word('STATUS', 'PC_READY', 0)
    #     self.write_bit_as_word(self._pub_word_list, 'STATUS')

    #     # NOTE: キャリブレーションスタート
    #     self.update_bit_as_word('STATUS', 'PC_ONLINE', 0)
    #     self.update_bit_as_word('STATUS', 'PC_READY', 0)
    #     self.write_bit_as_word(self._pub_word_list, 'STATUS')


def _main():
    # NOTE: トーソク用テストコード
    import time
    e_path = r'C:\Users\J100048001\Desktop\rv_vast\vision_setting.xlsx'
    plc = PlcSeq(e_path)

    param = dict(ip='192.168.250.10',
                 port='5000',
                 manufacturer='keyence',
                 series='',
                 plc_protocol='slmp',
                 transport_protocol='udp',
                 bit='DM',
                 word='DM',
                 double_word='')  # NOTE: ダブルワード

    plc.load_param(param)
    pre_bit = [False]
    pre_beat = False
    # NOTE: 周期設定
    _count = 0  # NOTE: 計測用カウンター
    WAIT_TIME = 0.1  # NOTE: ループ周期(second)
    BEAT_TIME = 1  # NOTE: ハートビート周期(second)
    COUNT_TH = int(BEAT_TIME / WAIT_TIME)
    pre_beat = plc.heart_beat(pre_beat)

    try:
        while True:
            # NOTE: PLCのメモリの値（OUTPUT）を取得
            ret, data = plc.read_bit_list(tag='REQUEST_COMMON')
            if not ret:
                # NOTE: 次にメモリを読みに行くまで所定の時間sleep
                # 負荷低減のため
                _count += 1
                time.sleep(WAIT_TIME)
                continue

            # NOTE: 検査信号のトリガー
            if data[plc.IN_BIT_IDX['CAPTURE_START']] == 1:
                # NOTE: 立ち上がりでなければ再度読み込み
                if pre_bit[0]:
                    _count += 1
                    time.sleep(WAIT_TIME)
                    continue
                # NOTE: 検査開始の電文をメインスレッドにシグナルとして送付

                r = plc.send_camera_status(True)
                time.sleep(0.5)
                r = plc.send_camera_status(False)
                r = plc.check_bit(tag='COMPLETE_COMMON', key='CAPTURE_RECV_COMP', val=1, timeout=5000)
                if not r:
                    print('errr1')
                    break
                r = plc.check_bit(tag='REQUEST_COMMON', key='INSPECT_START', val=1, timeout=5000)
                if not r:
                    print('errr2')

                plc.send_inspection_start()
                r, number_list = plc.get_inspection_config()
                print(number_list)

                plc.send_inspection_results(1, [-1111, -65000, 0, -1000])
                # NOTE: prebitを更新
                pre_bit[0] = True

            # NOTE: 不定期にON,OFFを繰り返す
            if _count > COUNT_TH:
                # print('sss')
                pre_beat = plc.heart_beat(pre_beat)
                _count = 0

            # NOTE: pre bitをオフにする
            pre_bit[0] = False

            # NOTE: カウント
            _count += 1

            # NOTE: 負荷低減のため
            time.sleep(WAIT_TIME)

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    # print(RANGE)
    _main()
