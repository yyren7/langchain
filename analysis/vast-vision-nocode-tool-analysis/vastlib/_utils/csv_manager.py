# ===============================================================================
# Name      : csv_managerpy
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-07-27 14:16
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================
import datetime
import os
import csv

from pydantic import BaseModel
from typing import Tuple, List


FIELDNAMES: List[str] = [
    'timestamp',
    'judgement',
    #'resolution',
    'pixels',
    'processing_time',
    'x',
    'y',
    'z',
    'r',
    #'num_pieces',
    'distance',
    #'error_message'
    'unit'
]


class LabelList(BaseModel):
    """データフレームにアクセスする時に使うラベルリスト"""
    timestamp: str = FIELDNAMES[0]
    judgement: str = FIELDNAMES[1]
    resolution: str = FIELDNAMES[2]
    processing_time: str = FIELDNAMES[3]
    x: str = FIELDNAMES[4]
    y: str = FIELDNAMES[5]
    z: str = FIELDNAMES[6]
    r: str = FIELDNAMES[7]
    num_pieces: str = FIELDNAMES[8]
    error_message: str = FIELDNAMES[9]


class PositionData(BaseModel):
    """ワークの位置情報"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    r: float = 0.0


class InspectionResults(BaseModel):
    """検査結果の情報"""
    timestamp: str = '2000-01-01 12:00:00'  # NOTE: 検査時刻 YYYY-MM-DD HH:mm:SS
    judgement: int = 1  # NOTE: 処理結果 OK:1, NG:2, ERR:3
    resolution: str = '-'  # NOTE: 解像度
    processing_time: float = 0.0  # NOTE: 処理時間
    position: PositionData = PositionData()  # NOTE: ワークの位置
    num_pieces: float = 0  # NOTE: ワークの数
    message: str = ''  # NOTE: エラーメッセージ


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
    def add_data_to_csv(result: InspectionResults, filename: str) -> None:
        """Inspection ResultsをCSVファイルに書き込む"""
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(f=csvfile, fieldnames=FIELDNAMES)
            writer.writerow({
                CSVHandler.Labels.timestamp: result.timestamp,
                CSVHandler.Labels.judgement: result.judgement,
                CSVHandler.Labels.resolution: result.resolution,
                CSVHandler.Labels.processing_time: result.processing_time,
                CSVHandler.Labels.x: result.position.x,
                CSVHandler.Labels.y: result.position.y,
                CSVHandler.Labels.z: result.position.z,
                CSVHandler.Labels.r: result.position.r,
                CSVHandler.Labels.num_pieces: result.num_pieces,
                CSVHandler.Labels.error_message: result.message
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
        now = datetime.datetime.now()
        y_str = now.strftime(self.year_format)
        m_str = now.strftime(self.month_format)
        d_str = now.strftime(self.day_format)
        return y_str, m_str, d_str

    def _get_bottom_folder_name(self) -> str:
        """yyyy-mm-ddの文字列取得"""
        now = datetime.datetime.now()
        bf_str = now.strftime(self.month_format)
        return bf_str

    def _get_csv_name(self) -> str:
        """画像の保存名を取得"""
        now = datetime.datetime.now()
        t_str = now.strftime('%Y_%m_%d')
        return t_str

    def get_timestamp(self) -> str:
        now = datetime.datetime.now()
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

    def save_csv(self, data: InspectionResults) -> None:
        """画像の保存"""
        csvname = self._get_csv_name()
        path = os.path.join(self.csv_dir, f'{csvname}.csv')
        CSVHandler.add_data_to_csv(data, path)


if __name__ == "__main__":
    # NOTE: テスト

    # NOTE: インスタンス生成
    csv_log_manager = CsvLogManager(r'C:\Users\J100048001\Desktop\log\csv')

    # NOTE: データ格納

    now_time = csv_log_manager.get_timestamp()
    data = InspectionResults(timestamp=now_time,
                             judgement=1,
                             processing_time=0.0,
                             position=PositionData(x=0,
                                                   y=0,
                                                   r=0),
                             num_pieces=1,
                             error_message=''
                             )

    # NOTE: 書き込み
    csv_log_manager.save_csv(data)

    # NOTE: 日付更新
    csv_log_manager.update_date()
