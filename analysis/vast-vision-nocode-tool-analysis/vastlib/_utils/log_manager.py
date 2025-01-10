# ===============================================================================
# Name      : log_manager.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-07-20 17:02
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================
import shutil
import datetime
import os
from cv2 import imwrite, resize
from numpy import ndarray
from typing import Tuple

try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


class ImgLogManager:
    GB_UNIT: int = 1073741824
    ENABLE_HOUR: bool = False

    def __init__(self, mount_dir: str):
        self.capacity_th = int(1 * self.GB_UNIT)  # 1GB
        # NOTE: 各フォルダのフォーマット
        self.year_format = '%Y'
        self.month_format = '%Y-%m'
        self.day_format = '%Y-%m-%d'
        self.hour_format = '%Y-%m-%d-%H'

        # NOTE: 年フォルダの上位フォルダ
        self.mount_dir = mount_dir
        # NOTE: 時間比較用
        self.bottom_folder_name = ''
        # NOTE: 画像保存フォルダ
        self.img_dir = ''
        # NOTE: 初期化処理
        self.initialize_folders()

    def _create_datetime_strings(self) -> Tuple[str, str, str, str, str]:
        """日付データを生成"""
        now = datetime.datetime.now()
        y_str = now.strftime(self.year_format)
        m_str = now.strftime(self.month_format)
        d_str = now.strftime(self.day_format)
        h_str = now.strftime(self.hour_format)
        t_str = now.strftime('%Y_%m_%d_%H_%M_%S')
        return y_str, m_str, d_str, h_str, t_str

    def _get_bottom_folder_name(self) -> str:
        """yyyy-mm-dd-hhの文字列取得"""
        now = datetime.datetime.now()
        if self.ENABLE_HOUR:
            bf_str = now.strftime(self.hour_format)
        else:
            bf_str = now.strftime(self.day_format)
        return bf_str

    def _get_current_time(self) -> str:
        """画像の保存名を取得"""
        now = datetime.datetime.now()
        t_str = now.strftime('%Y_%m_%d_%H_%M_%S')
        return t_str

    def initialize_folders(self) -> None:
        """初期化処理"""
        y_str, m_str, d_str, h_str, _ = self._create_datetime_strings()
        if self.ENABLE_HOUR:
            self.bottom_folder_name = h_str
            self.img_dir = os.path.join(self.mount_dir, y_str, m_str, d_str, h_str)
        else:
            self.bottom_folder_name = d_str
            self.img_dir = os.path.join(self.mount_dir, y_str, m_str, d_str)

        # NOTE: フォルダが無ければ再帰的に作成
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)

    def update_date(self) -> None:
        """日付フォルダのアップデート"""
        bf_name = self._get_bottom_folder_name()
        if bf_name == self.bottom_folder_name:
            return
        # NOTE: 画像保存フォルダを更新
        self.initialize_folders()

    def check_capacity(self) -> bool:
        """容量チェック"""
        # NOTE: USBマウント先のフォルダがあるか確認
        # NOTE: なかったら確認しない
        if not os.path.exists(self.mount_dir):
            return True

        # NOTE: ストレージの情報を取得（byte）
        _, _, free = shutil.disk_usage(self.mount_dir)
        free_gb = round(free / self.GB_UNIT, 3)
        logger.debug(f'Free memory: {free_gb}GB')

        # NOTE: 残り容量が十分ある場合True
        if free > self.capacity_th:
            return True

        return False

    def get_oldest_date(self, date_list: list, date_format: str) -> Tuple[bool, str]:
        """最小の日付フォルダを返す"""
        try:
            date_list = [datetime.datetime.strptime(date_, date_format) for date_ in date_list]
        except Exception:
            # NOTE: フォーマットに沿わない名前のフォルダが存在しているとき
            # 該当フォルダが含まれる上位フォルダを削除
            return False, ''

        if len(date_list) == 0:
            # NOTE: フォルダが見つからない場合
            return False, ''

        old_date = min(date_list)
        old_date_str = old_date.strftime(date_format)
        return True, old_date_str

    def remove_folder(self, folder_path: str) -> None:
        """フォルダを再帰的に削除"""
        shutil.rmtree(folder_path)

    def perform_cleanup(self) -> None:
        """削除のプロセス"""
        # NOTE: 年フォルダを確認
        year_dir = os.listdir(self.mount_dir)
        ret, old_date = self.get_oldest_date(year_dir, self.year_format)

        # NOTE: 月フォルダを確認
        target_dir = os.path.join(self.mount_dir, old_date)
        month_dir = os.listdir(target_dir)
        ret, old_date = self.get_oldest_date(month_dir, self.month_format)
        # NOTE: 空なら削除
        if not ret:
            self.remove_folder(target_dir)
            return

        # NOTE: 日フォルダを確認
        target_dir = os.path.join(target_dir, old_date)
        day_dir = os.listdir(target_dir)
        ret, old_date = self.get_oldest_date(day_dir, self.day_format)
        # NOTE: 空なら削除
        if not ret:
            self.remove_folder(target_dir)
            return

        if self.ENABLE_HOUR:
            # NOTE: 時フォルダを確認
            target_dir = os.path.join(target_dir, old_date)
            day_dir = os.listdir(target_dir)
            ret, old_date = self.get_oldest_date(day_dir, self.hour_format)
            # NOTE: 空なら削除
            if not ret:
                self.remove_folder(target_dir)
                return

        # NOTE: フォルダを削除
        self.remove_folder(os.path.join(target_dir, old_date))

    def save_image(self, img: ndarray, tag: str = '',
                   ext: str = 'jpg', vga: bool = False) -> None:
        """画像の保存"""
        # NOTE: 別のところで行う
        # self.update_date()
        # if not self.check_capacity():
        #     self.perform_cleanup()

        t_str = self._get_current_time()
        path = os.path.join(self.img_dir, f'{t_str}{tag}.{ext}')
        if vga:
            img = resize(img, (640, 480))
        imwrite(path, img)


if __name__ == "__main__":
    # NOTE: テスト
    import numpy as np

    img_log_manager = ImgLogManager(r'C:\Users\J100048001\Desktop\rv_vast\log\img')

    # NOTE: 画像保存
    img = np.zeros(shape=(100, 100, 3), dtype=np.uint8)
    img_log_manager.save_image(img)

    # NOTE: 日付更新
    img_log_manager.update_date()

    # NOTE: 容量チェック
    if not img_log_manager.check_capacity():
        # NOTE: 削除
        img_log_manager.perform_cleanup()
