# ===============================================================================
# Name      : plc_lib.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-04-19 12:00
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================

from time import perf_counter
from typing import Tuple, Union
from pydantic import BaseModel
try:
    from .api import plc_comm
    from .api.command_checker import check_command
except Exception:
    from api import plc_comm  # type: ignore
    from api.command_checker import check_command  # type: ignore
# from vastlib.connection.old.plc.api import plc_comm
# from vastlib.connection.old.plc.api.command_checker import check_command

try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


class PLCParam(BaseModel):
    ip: str
    port: str
    manufacturer: str
    series: str
    plc_protocol: str
    transport_protocol: str
    bit: str   # NOTE: ビットデバイス
    word: str   # NOTE: ワードデバイス
    double_word: str  # NOTE: ダブルワード


def word2byte(word: str) -> str:
    byte = '{:016b}'.format(int(word))
    register = byte[::-1]
    return register


class BasePLC:
    __version__ = '1.0.0'

    def __init__(self):
        pass

    def load_param(self, data: dict) -> None:
        """
        PLCの通信設定を読込

        Args:
            data (dict): dict型のパラメータ
        """
        self.param = PLCParam(**data)
        self.plc_network = dict(ip=self.param.ip,
                                port=self.param.port)

        self.plc_protocol = dict(manufacture=self.param.manufacturer,
                                 series=self.param.series,
                                 protocol=self.param.plc_protocol,
                                 transport_layer=self.param.transport_protocol)

        # NOTE: OMRON-FINSの場合は公式サポート外なのでコマンドチェックを通す
        if self.param.manufacturer == 'omron' and self.param.plc_protocol == 'fins':
            self._omron_fins_flag = True
        else:
            self._omron_fins_flag = False

    def get_time_from_plc(self) -> dict:
        """
        PLCから時刻取得

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

    def get_device(self, d_type: str) -> str:
        """
        デバイス名を取得

        Args:
            d_type (str): レジスタのデバイスの種類

        Returns:
            str: _description_
        """
        if d_type == 'bit':
            return self.param.bit
        elif d_type == "word":
            return self.param.word
        else:
            return ""

    def write_data_to_plc(self,
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

        device = self.get_device(d_type)
        if multi:
            if isinstance(addr_min, int):
                addr_min = str(addr_min)
            if isinstance(addr_max, int):
                addr_max = str(addr_max)

            # NOTE: 複数のデータレジスタを読み込む場合
            device_data = dict(device=device,
                               min=addr_min,
                               max=addr_max)
        else:
            if isinstance(addr, int):
                addr = str(addr)
            # NOTE: 1個のデータレジスタを読み込む場合
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

    def read_data_from_plc(self,
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

        device = self.get_device(d_type)

        if multi:
            if isinstance(addr_min, int):
                addr_min = str(addr_min)
            if isinstance(addr_max, int):
                addr_max = str(addr_max)

            # NOTE: 複数のデータレジスタを読み込む場合
            device_data = dict(device=device,
                               min=addr_min,
                               max=addr_max)
        else:
            if isinstance(addr, int):
                addr = str(addr)
            # NOTE: 1個のデータレジスタを読み込む場合
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


if __name__ == "__main__":

    config = dict(
        ip='192.168.250.10',
        port='5000',
        manufacturer='keyence',
        series='KV-7500',
        plc_protocol='slmp',
        transport_protocol='udp',
        bit='R',
        word='DM',
        double_word='DM'
    )

    plc = BasePLC()
    plc.load_param(config)

    success = plc.write_data_to_plc(d_type='word',
                                    # addr='30',
                                    addr_min='0',
                                    addr_max='1',
                                    multi=True,
                                    data=[0, 0])
    print(success)

    success, data = plc.read_data_from_plc(d_type='bit',
                                           # addr='30',
                                           addr_min='10',
                                           addr_max='20',
                                           multi=True)
    #  data=[?1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]))
    # data=[1])
    print(data)
    # print(success)

    # success, data = plc.read_data_from_plc(d_type='word',
    #                                        addr='5000',
    #                                        )

    # print(data)
