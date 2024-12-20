# ===============================================================================
# Name      : status_recoder.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-12-20 09:41
# Copyirght 2022 Hiroya Aoyama
# ===============================================================================
import os
import psutil
import subprocess
import csv
import time
from threading import Thread
from datetime import datetime
from pydantic import BaseModel
from typing import List, Tuple

FIELDNAMES: List[str] = [
    'timestamp',
    'cpu_usage',
    'cpu_temp',
    'mem_usage',
    'mem_used',
    'mem_free',
    'clock',
    'volts',
]


class LabelList(BaseModel):
    """データフレームにアクセスする時に使うラベルリスト"""
    timestamp: str = FIELDNAMES[0]
    cpu_usage: str = FIELDNAMES[1]
    cpu_temp: str = FIELDNAMES[2]
    mem_usage: str = FIELDNAMES[3]
    mem_used: str = FIELDNAMES[4]
    mem_free: str = FIELDNAMES[5]
    clock: str = FIELDNAMES[6]
    volts: str = FIELDNAMES[7]


class SystemInfo(BaseModel):
    timestamp: str = ''
    cpu_usage: float = 0.0
    cpu_temp: float = 0.0
    mem_usage: float = 0.0
    mem_used: float = 0.0
    mem_free: float = 0.0
    clock: float = 0.0
    volts: float = 0.0


def run_shell_command(command_str: str) -> str:
    # unit_list = ['\'C', 'V', 'M']
    if os.name == 'nt':
        return '0'

    try:
        proc = subprocess.run(command_str, shell=True, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, text=True)
        result = proc.stdout.split("=")
        # volts = result.decode("utf-8").split("=")[1].strip()
        return result[1].replace('\n', '')
    except subprocess.CalledProcessError:
        return '0'


def get_cpu_temp() -> float:
    try:
        res = run_shell_command("vcgencmd measure_temp")
        res = res.replace('\'C', '')
        cpu_temp = round(float(res), 1)
        return cpu_temp
    except Exception:
        return 0.0


def get_cpu_volts() -> float:
    try:
        res = run_shell_command("vcgencmd measure_volts")
        res = res.replace('V', '')
        volts = round(float(res), 1)
        return volts
    except Exception:
        return 0.0


def get_cpu_clocks() -> float:
    try:
        res = run_shell_command("vcgencmd measure_clock arm")
        clocks = round(float(res), 1)
        return clocks
    except Exception:
        return 0.0


def convert_bytes_unit(byte_size: float, mem_unit: str = 'B') -> float:
    """
    Converts a byte size to the specified memory unit.
    """
    mem_unit_list = ['B', 'K', 'M', 'G', 'T']
    try:
        index = mem_unit_list.index(mem_unit)
    except Exception:
        return byte_size

    mem_size = byte_size
    for _ in range(index):
        mem_size = mem_size / 1024
    return round(mem_size, 2)


def get_system_info(mem_unit: str = 'M') -> SystemInfo:
    """
    システム情報を取得
    """
    # NOTE: CPU使用率を取得
    cpu_usage = psutil.cpu_percent(interval=1)
    # NOTE: メモリ使用量を取得
    mem_info = psutil.virtual_memory()

    # NOTE: CPU温度
    cpu_temp = get_cpu_temp()
    clocks = get_cpu_clocks()
    volts = get_cpu_volts()

    return SystemInfo(
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        cpu_usage=cpu_usage,
        cpu_temp=cpu_temp,
        mem_used=convert_bytes_unit(byte_size=mem_info.used,
                                    mem_unit=mem_unit),
        mem_free=convert_bytes_unit(byte_size=mem_info.available,
                                    mem_unit=mem_unit),
        mem_usage=round(number=mem_info.used / mem_info.total * 100,
                        ndigits=2),
        clock=clocks,
        volts=volts
    )


class CSVHandler:
    """Inspection ResultsをCSVファイルに書き込むクラス"""
    Labels = LabelList()

    @staticmethod
    def create_new_csv(filename: str) -> None:
        """Inspection ResultsをCSVファイルに書き込む"""
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()

    @staticmethod
    def add_data_to_csv(result: SystemInfo, filename: str) -> None:
        """Inspection ResultsをCSVファイルに書き込む"""
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(f=csvfile, fieldnames=FIELDNAMES)
            writer.writerow({
                CSVHandler.Labels.timestamp: result.timestamp,
                CSVHandler.Labels.cpu_usage: result.cpu_usage,
                CSVHandler.Labels.cpu_temp: result.cpu_temp,
                CSVHandler.Labels.mem_usage: result.mem_usage,
                CSVHandler.Labels.mem_used: result.mem_used,
                CSVHandler.Labels.mem_free: result.mem_free,
                CSVHandler.Labels.clock: result.clock,
                CSVHandler.Labels.volts: result.volts,
            })


class CsvLogManager:
    def __init__(self, mount_dir: str):
        # NOTE: 各フォルダのフォーマット
        self.year_format = '%Y'
        self.month_format = '%Y-%m'
        self.day_format = '%Y-%m-%d'

        # NOTE: 年フォルダの上位フォルダ
        self.mount_dir = mount_dir
        # NOTE: 時間比較用
        self.bottom_folder_name = ''
        # NOTE: CSV保存フォルダ(YYYY/YYYY-MM/yyyy-mm-dd.csv)
        self.csv_dir = ''
        # NOTE: 初期化処理
        self.initialize_folders()

    def _create_datetime_strings(self) -> Tuple[str, str, str]:
        """日付データを生成"""
        now = datetime.now()
        y_str = now.strftime(self.year_format)
        m_str = now.strftime(self.month_format)
        d_str = now.strftime(self.day_format)
        return y_str, m_str, d_str

    def _get_bottom_folder_name(self) -> str:
        """yyyy-mm-ddの文字列取得"""
        now = datetime.now()
        bf_str = now.strftime(self.month_format)
        return bf_str

    def _get_csv_name(self) -> str:
        """画像の保存名を取得"""
        now = datetime.now()
        t_str = now.strftime('%Y_%m_%d')
        return t_str

    def get_timestamp(self) -> str:
        now = datetime.now()
        t_str = now.strftime('%Y-%m-%d %H:%M:%S')
        return t_str

    def initialize_folders(self) -> None:
        """初期化処理"""
        y_str, m_str, _ = self._create_datetime_strings()
        self.bottom_folder_name = m_str
        self.csv_dir = os.path.join(self.mount_dir, y_str, m_str)

        # NOTE: フォルダが無ければ再帰的に作成
        if not os.path.exists(self.csv_dir):
            os.makedirs(self.csv_dir)

        # NOTE: CSVのパスを取得
        csvname = self._get_csv_name()
        csv_path = os.path.join(self.mount_dir, y_str, m_str, f'{csvname}.csv')

        # NOTE: CSVが存在しない場合、ヘッダーをつけて作成
        if not os.path.exists(csv_path):
            CSVHandler.create_new_csv(csv_path)

    def update_date(self) -> None:
        """日付フォルダのアップデート"""

        # NOTE: 最下層のフォーマット形式で時刻を比較
        bf_name = self._get_bottom_folder_name()
        if bf_name == self.bottom_folder_name:
            return
        # NOTE: 画像保存フォルダを更新
        self.initialize_folders()

    def save_csv(self, data: SystemInfo) -> None:
        """画像の保存"""
        csvname = self._get_csv_name()
        path = os.path.join(self.csv_dir, f'{csvname}.csv')
        CSVHandler.add_data_to_csv(data, path)


class StatusRecoder(Thread):
    def __init__(self, csv_dir: str, period: int = 10):
        super(StatusRecoder, self).__init__()
        self.stop_trigger = False
        self.period = period
        self.sleep_time = 0.5
        self.csv_lm = CsvLogManager(csv_dir)

    def stop(self) -> None:
        self.stop_trigger = True

    def run(self) -> None:
        counter: int = 0
        counter_th: int = int(self.period / self.sleep_time)
        while not self.stop_trigger:
            counter += 1
            if counter > counter_th:
                # NOTE: データ取得
                data = get_system_info()
                # NOTE: 書き込み
                self.csv_lm.save_csv(data)
                # NOTE: 日付更新
                self.csv_lm.update_date()
                # NOTE: カウントを初期化
                counter = 0
            # NOTE: スリープ
            time.sleep(0.5)


if __name__ == "__main__":
    # NOTE: テスト
    thread = StatusRecoder(csv_dir=os.path.join(os.path.expanduser('~/Desktop'), 'csv_dir'),
                           period=10)
    thread.start()
    try:
        while True:
            print('something to process')
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram has been finished")

    thread.stop()
    thread.join()
