# ===============================================================================
# Name      : plc_lib.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2022-11-15 11:58
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================

from time import perf_counter
from typing import Tuple, Union
from pydantic import BaseModel
try:
    from .api import plc_comm
except Exception:
    from lib.plc.api import plc_comm

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
    double_word: str   # NOTE: ダブルワード


def word2byte(word: str) -> str:
    byte = '{:016b}'.format(int(word))
    register = byte[::-1]
    return register


class BasePLC:
    __version__ = '1.0.0'

    def __init__(self):
        pass

    def load_param(self, data: dict) -> None:
        self.param = PLCParam(**data)
        self.plc_network = dict(ip=self.param.ip,
                                port=self.param.port)

        self.plc_protocol = dict(manufacture=self.param.manufacturer,
                                 series=self.param.series,
                                 protocol=self.param.plc_protocol,
                                 transport_layer=self.param.transport_protocol)

    def get_time_from_plc(self) -> dict:
        # NOTE: PLCから時刻取得 optionに'time'と設定する
        results = plc_comm.single_communication_to_plc(
            self.plc_network,
            self.plc_protocol,
            dict(device='D', min='0', max='0'),
            dict(cmd='read', data=[], option='time')
        )
        return results

    def get_device(self, d_type: str) -> str:
        # NOTE: データレジスタの使い方？bit or word or double word
        if d_type == 'bit':
            device = self.param.bit
        elif d_type == "word":
            device = self.param.word
        else:
            device = ""
        return device

    def write_data_to_plc(self,
                          d_type: str = 'bit',
                          addr: Union[str, int] = '0',
                          addr_min: Union[str, int] = '0',
                          addr_max: Union[str, int] = '0',
                          data: list = None,
                          multi: bool = False,
                          timeout: int = 1000) -> bool:

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
                return True, results['exists_data']

            timer_count = int((perf_counter() - start_time) * 1000)

        errMsg = '[ERR] Failed to Read plc registry...' \
            + 'Please make sure that the LAN cable is connected.'
        logger.error(errMsg)

        return False, []

    def response_check(self, d_type='bit', addr='0', ref_data=None, timeout=5000):
        timer_count = 0
        start_time = perf_counter()
        matching = False
        while timer_count < timeout:
            success, data = self.read_data_from_plc(d_type=d_type, addr=addr)
            if success:
                # NOTE: dataの中身はstr
                if data == ref_data:
                    matching = True
                    break
                timer_count = int((perf_counter() - start_time) * 1000)
            else:
                break

        return matching


if __name__ == "__main__":

    config = dict(
        ip='192.168.250.10',
        port='5000',
        manufacturer='keyence',
        series='',
        plc_protocol='slmp',
        transport_protocol='udp',
        bit='W',
        word='DM',
        double_word='W'
    )

    plc = BasePLC()
    plc.load_param(config)

    success = plc.write_data_to_plc(d_type='word',
                                    # addr='4018',
                                    addr_min='4016',
                                    addr_max='4026',
                                    multi=True,
                                    data=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    print(success)

    # success, data = plc.read_data_from_plc(d_type='word',
    #                                        addr='5000',
    #                                        )

    # print(data)
