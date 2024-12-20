# ===============================================================================
# Name      : capacity_checker.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2022-12-26 14:52
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================
import shutil
# import sys
import datetime
import subprocess
import os

try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


class CapacityChecker:
    def __init__(self, usb_mount_dir: str, img_dir: str):
        self.gb = 1073741824  # 1GB
        self.delete_threshold = 1073741824  # 1GB
        self.year_format = '%Y'
        self.month_format = '%Y-%m'
        self.day_format = '%Y-%m-%d'
        self.usb_mount_dir = usb_mount_dir
        self.img_dir = img_dir

    def capacity_check(self):
        # NOTE: USBマウント先のフォルダがあるか確認
        if not os.path.exists(self.usb_mount_dir):
            return False

        # NOTE: フォルダがUSBにマウントされているか確認
        mount_cmd = f"mountpoint -q {self.usb_mount_dir}; echo $?"
        mount_flag = int(
            (subprocess.Popen(mount_cmd, stdout=subprocess.PIPE, shell=True).communicate()[0]).decode("utf-8"))

        if mount_flag != 0:
            return False

        # NOTE: ストレージの情報を取得（byte）
        total, used, free = shutil.disk_usage(self.usb_mount_dir)
        logger.info(f'Free memory: {round(free/self.gb, 3)}GB')

        if free < self.delete_threshold:
            self.delete_oldfile(self.img_dir)

        return True

    def folder_check(self, target_dir: str, dateformat: str):
        date_list = []
        folder_list = os.listdir(target_dir)
        for folder in folder_list:
            try:
                date_data = datetime.datetime.strptime(folder, dateformat)
                date_list.append(date_data)
            except Exception as e:
                logger.error(str(e))
        # NOTE: there is no year folder
        if len(date_list) == 0:
            return False, None
        else:
            if date_list == []:
                return False, None
            else:
                return True, min(date_list)

    def delete_oldfile(self, target_dir: str):
        year: datetime.date
        month: datetime.date
        day: datetime.date

        if os.path.exists(target_dir):

            success, year = self.folder_check(target_dir=target_dir,
                                              dateformat=self.year_format)

            if success:
                if year is None:
                    return -1
            else:
                logger.info(f'{target_dir} is empty')
                return -1

            month_dir = f'{target_dir}{year.strftime(self.year_format)}'

            success, month = self.folder_check(target_dir=month_dir,
                                               dateformat=self.month_format)
            if success:
                if month is None:
                    return -1
            else:
                logger.info(f'{month_dir} is empty')
                shutil.rmtree(f'{target_dir}{year.strftime(self.year_format)}')
                return -1

            day_dir = f'{target_dir}{month.strftime(self.year_format)}/{month.strftime(self.month_format)}'

            success, day = self.folder_check(target_dir=day_dir,
                                             dateformat=self.day_format)

            if success:
                if day is None:
                    return -1
            else:
                logger.info(f'{day_dir} is empty')
                shutil.rmtree(f'{target_dir}{month.strftime(self.year_format)}/{month.strftime(self.month_format)}')
                return -1

            # NOTE: 最も古いフォルダを削除
            delete_folder_name = \
                f'{target_dir}{day.strftime(self.year_format)}/{day.strftime(self.month_format)}/{day.strftime(self.day_format)}'

            try:
                shutil.rmtree(delete_folder_name)
                logger.info(f'Deleted: {delete_folder_name}')
            except Exception as e:
                logger.error(str(e))

            # NOTE: 月フォルダが空になった場合削除
            success, _ = self.folder_check(target_dir=day_dir,
                                           dateformat=self.month_format)
            if success:
                pass
            else:
                shutil.rmtree(f'{target_dir}{month.strftime(self.year_format)}/{month.strftime(self.month_format)}')

            # NOTE: 年フォルダが空になった場合削除
            success, _ = self.folder_check(target_dir=month_dir,
                                           dateformat=self.year_format)
            if success:
                pass
            else:
                shutil.rmtree(f'{target_dir}{year.strftime(self.year_format)}')

        return 0


if __name__ == "__main__":
    cc = CapacityChecker()
    cc.capacity_check()
