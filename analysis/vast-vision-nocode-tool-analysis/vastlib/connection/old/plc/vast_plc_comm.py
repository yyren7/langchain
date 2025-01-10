# ===============================================================================
# Name      : plc_sequence.py
# Version   : 1.0.0
# Brief     : NTSZ
# Time-stamp: 2024-01-06 15:36
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================
import copy
from typing import List, Tuple, Union
from time import perf_counter
from pydantic import BaseModel

try:
    from .api import plc_comm
    from .api.command_checker import check_command
    from .api.plc_comm import convert_signed
    from . import read_excel as g_set
except Exception:
    from api import plc_comm  # type: ignore
    from api.command_checker import check_command  # type: ignore
    from api.plc_comm import convert_signed  # type: ignore
    import read_excel as g_set  # type: ignore

try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


class PLCConfiguration(BaseModel):
    ip: str = ''
    port: str = ''
    manufacturer: str = ''
    series: str = ''
    plc_protocol: str = ''
    transport_protocol: str = ''
    bit: str = ''   # NOTE: ビットデバイス
    word: str = ''   # NOTE: ワードデバイス
    double_word: str = ''  # NOTE: ダブルワード


def word2bit(input_word_data: int) -> List[int]:
    """数値を16bitに変換"""
    word_data_str = format(input_word_data, '016b')
    word_data_ary = list(word_data_str)
    word_data_ary.reverse()
    return list(map(int, word_data_ary))


def bit2word(input_binary_data: list) -> int:
    """16bitのlistを数値に変換"""
    input_binary_data_buf = copy.deepcopy(input_binary_data)
    input_binary_data_buf.reverse()
    binary_data_str = str(input_binary_data_buf)
    revised_binary_data_str = '0b' + binary_data_str[1:len(binary_data_str) - 1].replace(', ', '')
    word_data = eval(revised_binary_data_str)
    return word_data


def bool2int(bool_val: bool) -> int:
    if bool_val:
        return 1
    else:
        return 0


class BasePLCCommunication:
    """
    PLCとの通信に使う基本関数
    """
    __version__ = '1.0.0'

    # def __init__(self):
    #     self._vis_address: bool = False

    # def enableAddress(self, enabled: bool) -> None:
    #     self._vis_address = enabled

    def loadPLCConfiguration(self, data: Union[dict, PLCConfiguration]) -> bool:
        """
        PLCとの通信設定の読込

        Args:
            data (Union[dict, PLCConfiguration]): 通信設定のパラメータ

        Returns:
            bool: 入力フォーマットが間違っていた場合False
        """
        if isinstance(data, dict):
            self.param = PLCConfiguration(**data)
        elif isinstance(data, PLCConfiguration):
            self.param = data
        else:
            return False

        self.plc_network = dict(ip=self.param.ip,
                                port=self.param.port)

        self.plc_protocol = dict(manufacture=self.param.manufacturer,
                                 series=self.param.series,
                                 protocol=self.param.plc_protocol,
                                 transport_layer=self.param.transport_protocol)

        # NOTE: OMRON-FINSの場合は公式サポート外なのでコマンドチェックを適用
        if self.param.manufacturer == 'omron' and self.param.plc_protocol == 'fins':
            self._omron_fins_flag = True
        else:
            self._omron_fins_flag = False

        return True

    def getTimeFromPLC(self) -> dict:
        """
        PLCから時刻取得(Omronのみ対応?)

        Returns:
            dict: _description_
        """
        results = plc_comm.single_communication_to_plc(
            self.plc_network,
            self.plc_protocol,
            dict(device='D', min='0', max='0'),
            dict(cmd='read', data=[], option='time')
        )
        return results

    def getPLCDeviceName(self, d_type: str) -> str:
        """
        デバイス名を取得

        Args:
            d_type (str): レジスタのデバイスの種類

        Returns:
            str: デバイス名
        """
        if d_type == 'bit':
            return self.param.bit
        elif d_type == "word":
            return self.param.word
        else:
            return ""

    def writeDataToPLCDevice(self,
                             d_type: str = 'bit',
                             addr: Union[str, int] = '0',
                             addr_min: Union[str, int] = '0',
                             addr_max: Union[str, int] = '0',
                             data: list = None,
                             multi: bool = False,
                             timeout: int = 1000) -> bool:
        """
        PLCのレジスタに値を書き込む関数

        Args:
            d_type (str, optional): レジスタのデバイスの種類
            addr (Union[str, int], optional): 1word分書き込むときのアドレス.
            addr_min (Union[str, int], optional): 連番で書き込むときの最初のアドレス.
            addr_max (Union[str, int], optional): 連番で書き込むときの最後のアドレス.
            data (list, optional): 書き込むデータ(list形式).
            multi (bool, optional): 連番で書き込むときはTrue.
            timeout (int, optional): 通信のタイムアウト設定(ms).

        Returns:
            bool: 通信成功ならTrue.
        """

        device = self.getPLCDeviceName(d_type)
        if multi:
            # NOTE: 複数のデータレジスタを書き込む場合
            if isinstance(addr_min, int):
                addr_min = str(addr_min)
            if isinstance(addr_max, int):
                addr_max = str(addr_max)

            device_data = dict(device=device,
                               min=addr_min,
                               max=addr_max)
        else:
            # NOTE: 1個のデータレジスタを書き込む場合
            if isinstance(addr, int):
                addr = str(addr)

            device_data = dict(device=device,
                               min=addr,
                               max=addr)

        timer_count = 0
        start_time = perf_counter()

        # NOTE: タイムアウトまで通信トライ
        while timer_count < timeout:
            results = plc_comm.single_communication_to_plc(
                self.plc_network,
                self.plc_protocol,
                device_data,
                dict(cmd='write', data=data, option='')
            )

            # NOTE: error_code=0で通信成功
            if results['error_code'] == 0:
                if self._omron_fins_flag:
                    if check_command(results['send_binary'], results['response']):
                        return True
                else:
                    return True

            timer_count = int((perf_counter() - start_time) * 1000)

        errMsg = '[ERR] Failed to Write to plc registry...' \
            + 'Please make sure that the LAN cable is connected.'
        logger.error(errMsg)

        return False

    def readDataFromPLCDevice(self,
                              d_type: str = 'bit',
                              addr: Union[str, int] = '0',
                              addr_min: Union[str, int] = '0',
                              addr_max: Union[str, int] = '0',
                              multi: bool = False,
                              timeout: int = 1000) -> Tuple[bool, list]:
        """
        PLCのレジスタを読み込む関数


        Args:
            d_type (str, optional): レジスタのデバイスの種類.
            addr (Union[str, int], optional): 1word分読み込む時ののアドレス.
            addr_min (Union[str, int], optional): 連番で読み込む時の最初のアドレス.
            addr_max (Union[str, int], optional): 連番で読み込む時の最後のアドレス.
            multi (bool, optional): 連番で書き込むときはTrue.
            timeout (int, optional): 通信のタイムアウト設定(ms)

        Returns:
            Tuple[bool, list]: 通信成功ならTrue, data.
        """

        device = self.getPLCDeviceName(d_type)

        if multi:
            # NOTE: 複数のデータレジスタを読み込む場合
            if isinstance(addr_min, int):
                addr_min = str(addr_min)
            if isinstance(addr_max, int):
                addr_max = str(addr_max)

            device_data = dict(device=device,
                               min=addr_min,
                               max=addr_max)
        else:
            # NOTE: 1個のデータレジスタを読み込む場合
            if isinstance(addr, int):
                addr = str(addr)

            device_data = dict(device=device,
                               min=addr,
                               max=addr)

        timer_count = 0
        start_time = perf_counter()

        while timer_count < timeout:
            results = plc_comm.single_communication_to_plc(
                self.plc_network,
                self.plc_protocol,
                device_data,
                dict(cmd='read', data=[], option='')
            )

            # NOTE: error_code=0で通信成功
            if results['error_code'] == 0:
                if self._omron_fins_flag:
                    if check_command(results['send_binary'], results['response']):
                        return True, results['exists_data']
                else:
                    return True, results['exists_data']

            timer_count = int((perf_counter() - start_time) * 1000)

        errMsg = '[ERR] Failed to Read plc registry...' \
            + 'Please make sure that the LAN cable is connected.'
        logger.error(errMsg)

        return False, []


class PLCCommunication(BasePLCCommunication):
    __version__ = '1.0.0'
    """
    PLC通信@NPSZ&メカトロチームラダー
    """

    def __init__(self, excel_path: str):
        super().__init__()
        self.updateAddressMapFromExcel(excel_path)
        self.bit_eq_word: bool = True

    # ===============================================================================
    # NOTE: Excelからパラメータを取得する関数
    # ===============================================================================

    def getPLCDeviceMapFromExcel(self, xlsx_file: str, map_id: int) -> dict:
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

    def convertDeviceMapToAddressMap(self, device_map: dict, header_address: int) -> dict:
        """アドレスマップを取得"""
        data = {}
        for key in device_map.keys():
            data[key] = header_address + device_map[key]
        return data

    def updateAddressMapFromExcel(self, path: str) -> None:
        """エクセルファイルからアドレスマップを取得"""
        # NOTE: キーと相対アドレス0-15
        header_address = self.getPLCDeviceMapFromExcel(path, 0)
        self.IN_BIT_IDX = self.getPLCDeviceMapFromExcel(path, 1)
        self.IN_WORD_IDX = self.getPLCDeviceMapFromExcel(path, 2)
        self.OUT_BIT_IDX = self.getPLCDeviceMapFromExcel(path, 3)
        self.OUT_WORD_IDX = self.getPLCDeviceMapFromExcel(path, 4)

        # NOTE: キーと絶対アドレス
        self.IN_BIT_AD = self.convertDeviceMapToAddressMap(self.IN_BIT_IDX,
                                                           header_address['IN_BIT_NO'])
        self.IN_WORD_AD = self.convertDeviceMapToAddressMap(self.IN_WORD_IDX,
                                                            header_address['IN_WORD_NO'])
        self.OUT_BIT_AD = self.convertDeviceMapToAddressMap(self.OUT_BIT_IDX,
                                                            header_address['OUT_BIT_NO'])
        self.OUT_WORD_AD = self.convertDeviceMapToAddressMap(self.OUT_WORD_IDX,
                                                             header_address['OUT_WORD_NO'])

        # NOTE: 内部保持変数 0で初期化
        # TODO: VASTから見たOUTのBITリスト 今は6Word確保
        self._pub_word_list = [[0 for i in range(16)] for j in range(6)]

        # NOTE: エクセルからPLCのパラメータ(IP,Port,Protocol)を取得&反映
        self.plc_config = g_set.getPLCParam(path, 'CONFIG')
        self.loadPLCConfiguration(self.plc_config)

    def getPLCConfiguration(self) -> dict:
        return self.plc_config

    # ===============================================================================
    # NOTE: ステータス管理の関数（内部ではBit管理、出力はWord出力）
    # ===============================================================================

    def setBitInWord(self, tag: str, key: str, val: int) -> None:
        """内部管理しているbitを更新"""
        self._pub_word_list[self.OUT_BIT_IDX[tag]][self.OUT_BIT_IDX[key]] = val

    def readBitList(self, tag: str) -> Tuple[bool, list]:
        """Wordで読み取ってBitをListに変換"""
        ret, data = self.readDataFromPLCDevice(d_type='word',
                                               addr=self.IN_BIT_AD[tag])
        if not ret:
            return False, [0]

        bit_16 = word2bit(data[0])
        return True, bit_16

    def readBitState(self, tag: str, key: str) -> int:
        """Wordで読み取ってBitに分解"""
        ret, data = self.readBitList(tag)
        if ret:
            s_bit = data[self.IN_BIT_IDX[key]]
            return s_bit
        else:
            return -1

    def writeBitsStateToWord(self, data: list, tag: str) -> bool:
        """Bitの状態をWord単位で書き込む"""
        bit_16 = data[self.OUT_BIT_IDX[tag]]
        send_data = bit2word(bit_16)
        addr = self.OUT_BIT_AD[tag]
        ret = self.writeDataToPLCDevice(d_type='word',
                                        addr=addr,
                                        data=[send_data])
        return ret

    # ===============================================================================
    # NOTE: 外部用のメソッド
    # ===============================================================================

    def setPcOnline(self, bit_on: bool) -> bool:
        self.setBitInWord('STATUS_COMMON', 'PC_ONLINE', bool2int(bit_on))
        return self.writeBitsStateToWord(self._pub_word_list, 'STATUS_COMMON')

    def setInspectionNGCode(self, ng_code: int) -> bool:
        return self.writeDataToPLCDevice(d_type='word',
                                         addr=self.OUT_WORD_AD['NG_CODE'],
                                         data=[ng_code])

    def setInspectionErrorCode(self, error_code: int) -> bool:
        return self.writeDataToPLCDevice(d_type='word',
                                         addr=self.OUT_WORD_AD['ERR_CODE'],
                                         data=[error_code])

    def setPcErrorCode(self, error_code: int) -> bool:
        return self.writeDataToPLCDevice(d_type='word',
                                                addr=self.OUT_WORD_AD['PC_ERR_CODE'],
                                                data=[error_code])

    def setPcError(self, bit_on: bool) -> bool:
        self.setBitInWord('STATUS_COMMON', 'PC_ERR', bool2int(bit_on))
        return self.writeBitsStateToWord(self._pub_word_list, 'STATUS_COMMON')

    def sendCaptureInProgressSignalToPLC(self, in_progress: bool) -> bool:
        """撮像ステータスの送信"""
        # NOTE: 撮像中はcapturing = True
        self.setBitInWord('STATUS_COMMON', 'CAPTURING', bool2int(in_progress))
        ret = self.writeBitsStateToWord(self._pub_word_list, 'STATUS_COMMON')
        return ret

    def sendInspectionInProgressSignalToPLC(self, in_progress: bool) -> bool:
        """検査中の信号を送信"""
        # NOTE: W(x_out).08 検査フラグ送信
        self.setBitInWord('STATUS_COMMON', 'INSPECTING', bool2int(in_progress))
        ret = self.writeBitsStateToWord(self._pub_word_list, 'STATUS_COMMON')
        return ret

    def initializeStatus(self) -> None:
        """値の初期化"""
        self.sendCaptureInProgressSignalToPLC(in_progress=False)
        self.sendInspectionInProgressSignalToPLC(in_progress=False)
        self.setInspectionNGCode(ng_code=0)
        self.setInspectionErrorCode(error_code=0)
        self.setPcErrorCode(error_code=0)
        self.setPcError(bit_on=False)

    def checkPLCAcknowledgement(self, tag: str, key: str,
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
            ret, data = self.readDataFromPLCDevice(d_type='word', addr=addr, timeout=timeout)

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

    def getInspectionDataFromPLC(self) -> Tuple[bool, List[int]]:
        """各種検査に関する番号の取得"""
        # NOTE: DM(x_in+1,+2,+3) ワーク機種
        # NOTE: int(self.IN_WORD_AD['MODEL_NO']+1)はPOSITION_NOがない場合の配慮
        ret, data = self.readDataFromPLCDevice(d_type='word',
                                               addr_min=self.IN_WORD_AD['PROGRAM_NO'],
                                               addr_max=int(self.IN_WORD_AD['MODEL_NO'] + 1),
                                               multi=True)
        if ret:
            return True, data
        else:
            return False, [-1, -1, -1, -1]

    def sendAlignmentDataToPLC(self, data: list) -> bool:
        """補正量を送信"""
        # NOTE: 一応intに変換
        data = [int(v) for v in data]
        # NOTE: 符号付きの形式に変換
        send_data = convert_signed(data)
        ret = self.writeDataToPLCDevice(d_type='word',
                                        addr_min=self.OUT_WORD_AD['ALIGN_X_HIGH'],
                                        addr_max=self.OUT_WORD_AD['ALIGN_R_LOW'],
                                        multi=True,
                                        data=send_data)
        return ret

    def sendBasePositionDataToPLC(self, data: list) -> bool:
        """基準量を送付"""
        # NOTE: 一応intに変換
        data = [int(v) for v in data]
        # NOTE: 符号付きの形式に変換
        send_data = convert_signed(data)
        ret = self.writeDataToPLCDevice(d_type='word',
                                        addr_min=self.OUT_WORD_AD['B_ALIGN_X_HIGH'],
                                        addr_max=self.OUT_WORD_AD['B_ALIGN_R_LOW'],
                                        multi=True,
                                        data=send_data)
        return ret

    def sendInspectionResultToPLC(self,
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
        ret = self.sendAlignmentDataToPLC(align_data)
        # NOTE: 基準位置書き込み
        if b_align_data:
            ret = self.sendBasePositionDataToPLC(b_align_data)

        # NOTE: 判定がNGの場合NGコードを出力
        if status == 2:
            ret = self.setInspectionNGCode(ng_code=ng_code)
        # NOTE: 判定がERRの場合ERRコードを出力
        elif status == 3:
            ret = self.setInspectionErrorCode(error_code=err_code)

        # NOTE: ジャッジリストを更新
        judge_list = [0, 0, 0, 0]
        judge_list[status] = 1

        # NOTE: 検査判定を書き込み
        self.setBitInWord('COMPLETE_COMMON', 'INSPECT_OK', judge_list[1])
        self.setBitInWord('COMPLETE_COMMON', 'INSPECT_NG', judge_list[2])
        self.setBitInWord('COMPLETE_COMMON', 'INSPECT_ERR', judge_list[3])
        self.writeBitsStateToWord(self._pub_word_list, 'COMPLETE_COMMON')
        # NOTE: 検査終了を伝令
        self.sendInspectionInProgressSignalToPLC(in_progress=False)

        # NOTE: PLC側で検査結果を受けとれたか確認
        ret = self.checkPLCAcknowledgement('COMPLETE_COMMON', 'INSPECT_RECV_COMP', 1, timeout=5000)

        # NOTE: Timeoutすることがたまにある、ラダー側の問題？
        if not ret:
            return False

        # NOTE: 検査結果を初期化
        self.setBitInWord('COMPLETE_COMMON', 'INSPECT_OK', 0)
        self.setBitInWord('COMPLETE_COMMON', 'INSPECT_NG', 0)
        self.setBitInWord('COMPLETE_COMMON', 'INSPECT_ERR', 0)
        self.writeBitsStateToWord(self._pub_word_list, 'COMPLETE_COMMON')

        return True

    def sendPcErrorSignalToPLC(self, error_code: int = 1) -> bool:
        """エラー出力"""
        # NOTE: エラーコードを出力
        ret1 = self.setPcErrorCode(error_code=error_code)
        # NOTE: PCエラーステータスをON
        ret2 = self.setPcError(bit_on=True)

        if ret1 and ret2:
            return True
        return False

    def sendPcErrorResetSignalToPLC(self) -> bool:
        """PCエラーをリセット"""
        # NOTE: ステータス初期化
        self.initializeStatus()
        return True

    def sendHeartbeatSignalToPLC(self, pre_beat: bool) -> bool:
        """ラズパイの生存をPLC側に通達"""
        if pre_beat:
            self.setPcOnline(bit_on=False)
            return False
        else:
            self.setPcOnline(bit_on=True)
            return True

    def sendCustomDataToPLC(self, data: list) -> bool:
        """カスタムデータ(int)を送信 9x2 = 18"""
        # NOTE: 一応intに変換
        try:
            data = [int(v) for v in data]
            # NOTE: 符号付きの形式に変換
            send_data = convert_signed(list_negative=data, word_count=2)
            ret = self.writeDataToPLCDevice(d_type='word',
                                            addr_min=self.OUT_WORD_AD['ALIGN_X_HIGH'] + 18,
                                            addr_max=self.OUT_WORD_AD['ALIGN_R_LOW'] + 35,
                                            multi=True,
                                            data=send_data)
            return ret
        except Exception as e:
            print(e)
            return False


# class PLCCommunicationForNMOJ(BasePLCCommunication):
#     __version__ = '1.0.0'
#     """
#     PLC通信@NMOJ&昔のラダー
#     サッサとラダーを更新して捨て去りたい
#     """

#     def __init__(self, excel_path: str):
#         super().__init__()
#         self.updateAddressMapFromExcel(excel_path)

#     # ===============================================================================
#     # NOTE: Excelからパラメータを取得する関数
#     # ===============================================================================

#     def getPLCDeviceMapFromExcel(self, xlsx_file: str, map_id: int) -> dict:
#         """デバイスのINDEXを取得"""
#         if map_id == 0:
#             return g_set.getHeaderAddress(book_name=xlsx_file, sheet_name="CONFIG")
#         elif map_id == 1:
#             # NOTE: PLC->PCのBitデバイス
#             return g_set.getBitData(book_name=xlsx_file, sheet_name="BIT_IN")
#         elif map_id == 2:
#             # NOTE: PLC->PCのWordデバイス
#             return g_set.getWordData(book_name=xlsx_file, sheet_name="WORD_IN")
#         elif map_id == 3:
#             # NOTE: PC->PLCのBitデバイス
#             return g_set.getBitData(book_name=xlsx_file, sheet_name="BIT_OUT")
#         elif map_id == 4:
#             # NOTE: PC->PLCのWordデバイス
#             return g_set.getWordData(book_name=xlsx_file, sheet_name="WORD_OUT")
#         else:
#             return {}

#     def convertDeviceMapToAddressMap(self, device_map: dict, header_address: int) -> dict:
#         """アドレスマップを取得"""
#         data = {}
#         for key in device_map.keys():
#             data[key] = header_address + device_map[key]
#         return data

#     def updateAddressMapFromExcel(self, path: str) -> None:
#         """エクセルファイルからアドレスマップを取得"""
#         # NOTE: キーと相対アドレス0-15
#         header_address = self.getPLCDeviceMapFromExcel(path, 0)
#         self.IN_BIT_IDX = self.getPLCDeviceMapFromExcel(path, 1)
#         self.IN_WORD_IDX = self.getPLCDeviceMapFromExcel(path, 2)
#         self.OUT_BIT_IDX = self.getPLCDeviceMapFromExcel(path, 3)
#         self.OUT_WORD_IDX = self.getPLCDeviceMapFromExcel(path, 4)

#         # NOTE: キーと絶対アドレス
#         self.IN_BIT_AD = self.convertDeviceMapToAddressMap(self.IN_BIT_IDX,
#                                                            header_address['IN_BIT_NO'])
#         self.IN_WORD_AD = self.convertDeviceMapToAddressMap(self.IN_WORD_IDX,
#                                                             header_address['IN_WORD_NO'])
#         self.OUT_BIT_AD = self.convertDeviceMapToAddressMap(self.OUT_BIT_IDX,
#                                                             header_address['OUT_BIT_NO'])
#         self.OUT_WORD_AD = self.convertDeviceMapToAddressMap(self.OUT_WORD_IDX,
#                                                              header_address['OUT_WORD_NO'])

#         # NOTE: 内部保持変数 0で初期化
#         # TODO: VASTから見たOUTのBITリスト 今は6Word確保
#         self._pub_word_list = [[0 for i in range(16)] for j in range(6)]

#         # NOTE: エクセルからPLCのパラメータ(IP,Port,Protocol)を取得&反映
#         self.plc_config = g_set.getPLCParam(path, 'CONFIG')
#         self.loadPLCConfiguration(self.plc_config)

#     def getPLCConfiguration(self) -> dict:
#         return self.plc_config

#     # ===============================================================================
#     # NOTE: ステータス管理の関数（内部ではBit管理、出力はWord出力）
#     # ===============================================================================

#     def setBitInWord(self, tag: str, key: str, val: int) -> None:
#         """内部管理しているbitを更新"""
#         self._pub_word_list[self.OUT_BIT_IDX[tag]][self.OUT_BIT_IDX[key]] = val

#     def readBitList(self, tag: str) -> Tuple[bool, list]:
#         """Wordで読み取ってBitをListに変換"""
#         # NOTE: NMOJのラダーはbitデバイスで読取
#         ret, data = self.readDataFromPLCDevice(d_type='bit',
#                                                addr=self.IN_BIT_AD[tag])
#         if not ret:
#             return False, [0]

#         bit_16 = word2bit(data[0])
#         return True, bit_16

#     def readBitState(self, tag: str, key: str) -> int:
#         """Wordで読み取ってBitに分解"""
#         ret, data = self.readBitList(tag)
#         if ret:
#             s_bit = data[self.IN_BIT_IDX[key]]
#             return s_bit
#         else:
#             return -1

#     def writeBitsStateToWord(self, data: list, tag: str) -> bool:
#         """Bitの状態をWord単位で書き込む"""
#         bit_16 = data[self.OUT_BIT_IDX[tag]]
#         send_data = bit2word(bit_16)
#         addr = self.OUT_BIT_AD[tag]
#         # NOTE: NMOJのラダーはbitデバイスに書き込み
#         ret = self.writeDataToPLCDevice(d_type='bit',
#                                         addr=addr,
#                                         data=[send_data])
#         return ret

#     # ===============================================================================
#     # NOTE: 外部用のメソッド
#     # ===============================================================================

#     def setPcOnline(self, bit_on: bool) -> bool:
#         self.setBitInWord('STATUS', 'PC_ONLINE', bool2int(bit_on))
#         return self.writeBitsStateToWord(self._pub_word_list, 'STATUS')

#     def setInspectionNGCode(self, ng_code: int) -> bool:
#         return self.writeDataToPLCDevice(d_type='word',
#                                          addr=self.OUT_WORD_AD['NG_CODE'],
#                                          data=[ng_code])

#     def setInspectionErrorCode(self, error_code: int) -> bool:
#         return self.writeDataToPLCDevice(d_type='word',
#                                          addr=self.OUT_WORD_AD['ERR_CODE'],
#                                          data=[error_code])

#     def setPcErrorCode(self, error_code: int) -> bool:
#         return self.writeDataToPLCDevice(d_type='word',
#                                                 addr=self.OUT_WORD_AD['PC_ERR_CODE'],
#                                                 data=[error_code])

#     def setPcError(self, bit_on: bool) -> bool:
#         self.setBitInWord('STATUS', 'PC_ERR', bool2int(bit_on))
#         return self.writeBitsStateToWord(self._pub_word_list, 'STATUS_COMMON')

#     def sendCaptureInProgressSignalToPLC(self, in_progress: bool) -> bool:
#         """撮像ステータスの送信"""
#         # NOTE: 撮像中はcapturing = True
#         self.setBitInWord('STATUS', 'CAPTURE', bool2int(in_progress))
#         ret = self.writeBitsStateToWord(self._pub_word_list, 'STATUS')
#         return ret

#     def sendInspectionInProgressSignalToPLC(self, in_progress: bool) -> bool:
#         """検査中の信号を送信"""
#         # NOTE: W(x_out).08 検査フラグ送信
#         self.setBitInWord('STATUS', 'INSPECTING', bool2int(in_progress))
#         ret = self.writeBitsStateToWord(self._pub_word_list, 'STATUS')
#         return ret

#     def initializeStatus(self) -> None:
#         """値の初期化"""
#         self.sendCaptureInProgressSignalToPLC(in_progress=False)
#         self.sendInspectionInProgressSignalToPLC(in_progress=False)
#         self.setInspectionNGCode(ng_code=0)
#         self.setInspectionErrorCode(error_code=0)
#         self.setPcErrorCode(error_code=0)
#         self.setPcError(bit_on=False)

#     def checkPLCAcknowledgement(self, tag: str, key: str,
#                                 val: int, timeout: int = 1000) -> bool:
#         """PLC側のリクエスト、ステータスを確認

#         Args:
#             tag (str): bitの属性 request, status, complete
#             key (str): bitの名前
#             val (int): bitの値(0 or 1)が一致すればTrue
#             timeout (int, optional): タイムアウト(ms)

#         Returns:
#             bool: _description_
#         """
#         timer_count = 0
#         start_time = perf_counter()
#         addr = self.IN_BIT_AD[tag]
#         success = False
#         while timer_count < timeout:
#             # NOTE: dataはリストで返却
#             ret, data = self.readDataFromPLCDevice(d_type='bit', addr=addr, timeout=timeout)

#             # NOTE: 通信失敗したらcontinue
#             if not ret:
#                 timer_count = int((perf_counter() - start_time) * 1000)
#                 continue

#             # NOTE: 通信に成功したら値を確認
#             bit_16 = word2bit(data[0])
#             s_bit = bit_16[self.IN_BIT_IDX[key]]
#             if s_bit == val:
#                 # NOTE: 一致
#                 success = True
#                 break
#             else:
#                 # NOTE: 不一致
#                 timer_count = int((perf_counter() - start_time) * 1000)
#                 continue
#         return success

#     def checkCommunicationWithPLC(self) -> Tuple[bool, str]:
#         """Ready信号に対する応答"""
#         # NOTE: 初回起動時、原点復帰後に実施

#         # NOTE: W(x_out).00-01 <Write> プログラム起動時に初期化
#         self.setBitInWord('STATUS', 'PC_ONLINE', 0)
#         self.setBitInWord('STATUS', 'PC_READY', 0)
#         self.writeBitsStateToWord(self._pub_word_list, 'STATUS')

#         # NOTE: W(x_out).08-11 <Write> プログラム起動時に初期化（検査系）
#         self.setBitInWord('STATUS', 'INSPECTING', 0)
#         self.setBitInWord('STATUS', 'INSPECT_OK', 0)
#         self.setBitInWord('STATUS', 'INSPECT_NG', 0)
#         self.setBitInWord('STATUS', 'INSPECT_ERR', 0)
#         self.writeBitsStateToWord(self._pub_word_list, 'STATUS')

#         # NOTE:  W(x_out).00 <Write> PCの電源がONであることをPLCに通達
#         self.setBitInWord('STATUS', 'PC_ONLINE', 1)
#         self.writeBitsStateToWord(self._pub_word_list, 'STATUS')

#         # NOTE: W(x_in).01 <Read> Request Readyがオンになっていることを確認
#         ret = self.checkPLCAcknowledgement('REQ', 'READY', 1, timeout=5000)
#         if not ret:
#             logger.debug('Timeout Request Ready [on]')
#             return False, 'Timeout Request Ready [on]'

#         # NOTE: W(x_out).01 <Write> PLC側のW(2).01を確認したことを通達
#         self.setBitInWord('STATUS', 'PC_READY', 1)
#         self.writeBitsStateToWord(self._pub_word_list, 'STATUS')

#         # NOTE: W(x_in).01 <Read> PLC側が通達を確認
#         ret = self.checkPLCAcknowledgement('REQ', 'READY', 0, timeout=5000)
#         if not ret:
#             logger.debug('Timeout Request Ready [off]')
#             return False, 'Timeout Request Ready [off]'

#         # NOTE: W(x_out).01 <Write> 初期通信確認終了
#         self.setBitInWord('STATUS', 'PC_READY', 0)
#         self.writeBitsStateToWord(self._pub_word_list, 'STATUS')

#         logger.debug('Ready Sequence Complete')
#         return True, ''

#     def getInspectionDataFromPLC(self) -> Tuple[bool, List[int]]:
#         """各種検査に関する番号の取得"""
#         # NOTE: DM(x_in+1,+2,+3) ワーク機種
#         # NOTE: int(self.IN_WORD_AD['MODEL_NO']+1)はPOSITION_NOがない場合の配慮
#         ret, data = self.readDataFromPLCDevice(d_type='word',
#                                                addr_min=self.IN_WORD_AD['PROGRAM_NO'],
#                                                addr_max=int(self.IN_WORD_AD['MODEL_NO'] + 1),
#                                                multi=True)
#         if ret:
#             return True, data
#         else:
#             return False, [-1, -1, -1, -1]

#     def sendCustomDataToPLC(self, data: list) -> bool:
#         """カスタムデータを送信 9x2 = 18"""
#         # NOTE: 一応intに変換
#         data = [int(v) for v in data]
#         # NOTE: 符号付きの形式に変換
#         send_data = convert_signed(data)
#         ret = self.writeDataToPLCDevice(d_type='word',
#                                         addr_min=self.OUT_WORD_AD['ALIGN_X_HIGH'] + 18,
#                                         addr_max=self.OUT_WORD_AD['ALIGN_R_LOW'] + 35,
#                                         multi=True,
#                                         data=send_data)
#         return ret

#     def sendAlignmentDataToPLC(self, data: list) -> bool:
#         """補正量を送信"""
#         # NOTE: 一応intに変換
#         data = [int(v) for v in data]
#         # NOTE: 符号付きの形式に変換
#         send_data = convert_signed(data)
#         ret = self.writeDataToPLCDevice(d_type='word',
#                                         addr_min=self.OUT_WORD_AD['ALIGN_X_HIGH'],
#                                         addr_max=self.OUT_WORD_AD['ALIGN_R_LOW'],
#                                         multi=True,
#                                         data=send_data)
#         return ret

#     def sendBasePositionDataToPLC(self, data: list) -> bool:
#         """基準量を送付"""
#         # NOTE: 一応intに変換
#         data = [int(v) for v in data]
#         # NOTE: 符号付きの形式に変換
#         send_data = convert_signed(data)
#         ret = self.writeDataToPLCDevice(d_type='word',
#                                         addr_min=self.OUT_WORD_AD['B_ALIGN_X_HIGH'],
#                                         addr_max=self.OUT_WORD_AD['B_ALIGN_R_LOW'],
#                                         multi=True,
#                                         data=send_data)
#         return ret

#     def sendNumOfWorkPiece(self, num_work: int) -> bool:
#         ret = self.writeDataToPLCDevice(d_type='word',
#                                         addr=self.OUT_WORD_AD['NUM_WORK'],
#                                         data=[int(num_work)])
#         return ret

#     def sendInspectionResultToPLC(self,
#                                   status: int,
#                                   align_data: list,
#                                   b_align_data: list = [],
#                                   ng_code: int = 1,
#                                   err_code: int = 1,
#                                   ) -> bool:
#         """結果を送信する

#         Args:
#             status (int): 判定結果 ok:1 ng:2 err:3
#             align_data (list): 検出した座標
#             b_align_data (list, optional): マスター登録した座標
#             ng_code (int, optional): 画像処理のNGコード
#             err_code (int, optional): 画像処理のERRORコード

#         Returns:
#             bool: _description_
#         """
#         # NOTE: 現在位置書き込み
#         ret = self.sendAlignmentDataToPLC(align_data)
#         # NOTE: 基準位置書き込み
#         if b_align_data:
#             ret = self.sendBasePositionDataToPLC(b_align_data)

#         # NOTE: 判定がNGの場合NGコードを出力
#         if status == 2:
#             ret = self.setInspectionNGCode(ng_code=ng_code)
#         # NOTE: 判定がERRの場合ERRコードを出力
#         elif status == 3:
#             ret = self.setInspectionErrorCode(error_code=err_code)

#         # NOTE: ジャッジリストを更新
#         judge_list = [0, 0, 0, 0]
#         judge_list[status] = 1

#         # NOTE: 検査判定を書き込み
#         self.setBitInWord('STATUS', 'INSPECT_OK', judge_list[1])
#         self.setBitInWord('STATUS', 'INSPECT_NG', judge_list[2])
#         self.setBitInWord('STATUS', 'INSPECT_ERR', judge_list[3])
#         self.writeBitsStateToWord(self._pub_word_list, 'STATUS')
#         # NOTE: 検査終了を伝令
#         self.sendInspectionInProgressSignalToPLC(in_progress=False)

#         # NOTE: PLC側で検査結果を受けとれたか確認
#         ret = self.checkPLCAcknowledgement('REQ', 'INSPECT_RCV', 1, timeout=5000)
#         if not ret:
#             return False

#         # NOTE: 検査結果を初期化
#         self.setBitInWord('STATUS', 'INSPECT_OK', 0)
#         self.setBitInWord('STATUS', 'INSPECT_NG', 0)
#         self.setBitInWord('STATUS', 'INSPECT_ERR', 0)
#         self.writeBitsStateToWord(self._pub_word_list, 'STATUS')
#         return True

#     def sendPcErrorSignalToPLC(self, error_code: int = 1) -> bool:
#         """エラー出力"""
#         # NOTE: エラーコードを出力
#         ret1 = self.setPcErrorCode(error_code=error_code)
#         # NOTE: PCエラーステータスをON
#         ret2 = self.setPcError(bit_on=True)

#         if ret1 and ret2:
#             return True
#         return False

#     def sendPcErrorResetSignalToPLC(self) -> bool:
#         """PCエラーをリセット"""
#         # NOTE: ステータス初期化
#         self.initializeStatus()
#         return True

#     def sendHeartbeatSignalToPLC(self, pre_beat: bool) -> bool:
#         """ラズパイの生存をPLC側に通達"""
#         if pre_beat:
#             self.setPcOnline(bit_on=False)
#             return False
#         else:
#             self.setPcOnline(bit_on=True)
#             return True


if __name__ == "__main__":
    def set_time_from_plc(time_data: dict) -> None:
        import subprocess

        # NOTE: ERROR_CODEが-1の時, 通信失敗
        if time_data.get('error_code') == -1:
            return

        # NOTE: 一応仮でデータが入るようにしておく
        [year_, month_, day_, hour_, minutes_, second_, micro_second_] \
            = time_data.get('exists_data', [2023, 7, 7, 12, 12, 12, 12])

        subprocess.run([
            "sudo",
            "date",
            "-s",
            "{:02}/{:02} {:02}:{:02} 20{:02}".format(
                month_,
                day_,
                hour_,
                minutes_,
                year_
            )
        ])

    plc = BasePLCCommunication()

    conf = PLCConfiguration(ip='192.168.1.11',
                            port='9600',
                            manufacturer='omron',
                            series='',
                            plc_protocol='fins',
                            transport_protocol='udp',
                            bit='W',
                            word='DM',
                            double_word='',)

    plc.loadPLCConfiguration(conf)

    plc.getTimeFromPLC()
