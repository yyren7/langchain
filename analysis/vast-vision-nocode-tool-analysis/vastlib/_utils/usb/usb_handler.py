# ===============================================================================
# Name      : usb_handler.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-02-21 14:28
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================
import os
import subprocess
import time
import glob
from typing import Tuple

HOST_NAME = os.getlogin()

# NOTE: usbmountがinstall済み
# USB_MOUNT_DIR = '/media/usb/'
# NOTE: 違う場合
# USB_MOUNT_DIR = os.path.join('/media', HOST_NAME)
USB_MOUNT_DIR = '/media/'

# NOTE: ラズパイ以外で使用する場合はここを変えてください（linux限定）
PLATFORM_CODE = 'platform-fd500000.pcie-pci-0000:01:00.0-usb-'
MEMORY_HEADER = '/dev/disk/by-path/'
MEMORY_FOOTER = '-scsi-0:0:0:0-part1'
CAMERA_HEADER = '/dev/v4l/by-path/'
CAMERA_FOOTER = '-video-index0'

# NOTE: 参照URL
# https://access.redhat.com/documentation/ja-jp/red_hat_enterprise_linux/7/html/storage_administration_guide/persistent_naming-udev
# https://www.express.nec.co.jp/linux/distributions/confirm/hba/udev/udev_rules_details_rh.html


# NOTE: udevパスを取得
def get_udev_path() -> Tuple[bool, str]:
    path_key = MEMORY_HEADER + PLATFORM_CODE + '*'
    files = glob.glob(path_key)

    if len(files) == 0:
        return False, ''

    # NOTE: footerが一致するpathを探索
    filepath = [s for s in files if s.endswith(MEMORY_FOOTER)]
    if len(filepath) == 0:
        return False, ''

    # NOTE: 最初に見つかったudevを返す
    return True, filepath[0]


# NOTE: 指定のusbポートか確認
def check_usb_port(udev_path: str, port: int) -> bool:
    if udev_path == '':
        return False

    # NOTE: port番号以外を除去
    s = str(udev_path)
    s = s.replace(MEMORY_HEADER, '')
    s = s.replace(MEMORY_FOOTER, '')
    s = s.replace(PLATFORM_CODE, '')
    s_list = s.split(':')

    # NOTE: ポート番号が残っていれば
    try:
        port_id = s_list[2][0]
    except Exception:
        return False

    # NOTE: ポート番号が一致していればTrue
    if int(port_id) == port:
        return True

    return False


# NOTE: udevの情報からdevice名を取得
def extract_udev_info(src: str, *, dataname: str = "DEVNAME") -> Tuple[bool, str]:
    if src == '':
        return False, ''

    # NOTE: DEVNAMEの行を抽出
    data_list = src.split("\n")
    data = ''.join([s for s in data_list if dataname in s])
    if data == '':
        return False, ''

    # NOTE: DEVNAMEを抽出
    device_path = data.split("=")[1]
    return True, device_path


# NOTE: udevの情報からdevice名を取得
def get_device_path(udev_path: str) -> Tuple[bool, str]:
    result = subprocess.run(
        ["udevadm", "info", udev_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    ret, device_path = extract_udev_info(
        src=result.stdout.decode(),
        dataname="DEVNAME"
    )
    return ret, device_path


# NOTE: udevとdeviceのpathを取得
def get_usb_info() -> Tuple[bool, str, str]:
    ret, udev_path = get_udev_path()
    if not ret:
        return False, 'udev path is not found', ''

    ret, device_path = get_device_path(udev_path)

    if not ret:
        return False, 'device path is not found', ''

    return True, udev_path, device_path


# NOTE: usbがマウントされているか確認
def check_usb_mount() -> bool:
    mount_cmd = f"mountpoint -q {USB_MOUNT_DIR}; echo $?"
    mount_flag = int((
        subprocess.Popen(mount_cmd, stdout=subprocess.PIPE, shell=True).communicate()[0]).decode("utf-8"))
    # NOTE: 1であればUSBが挿入されていない
    if mount_flag == 1:
        return False
    return True


# NOTE: usbをマウント
def mount_usb(device_path: str, target_m_point: str = USB_MOUNT_DIR,
              timeout=500) -> bool:

    inserted = check_usb_mount()
    if inserted:
        return True

    # NOTE: 一旦アンマウント
    command = ['sudo', 'umount', device_path]
    _ = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # NOTE: マウントコマンド
    command = ['sudo', 'mount', device_path, target_m_point]

    # NOTE: timeout 計測
    time_s = time.perf_counter()
    time_counter = 0.0
    success = False
    while time_counter < timeout:
        ret = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if ret.returncode == 0:
            success = True
            break
        time_counter = int((time.perf_counter() - time_s) * 1000)

    return success


# NOTE: usbをアンマウント
def umount_usb(udev_path: str, timeout=500) -> bool:
    inserted = check_usb_mount()
    if not inserted:
        return True

    success = False
    time_s = time.perf_counter()
    time_counter = 0.0
    while time_counter < timeout:
        command = ['sudo', 'umount', udev_path]
        ret = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if ret.returncode == 0:
            success = True
            break
        time_counter = int((time.perf_counter() - time_s) * 1000)

    return success


def do_sync() -> None:
    if os.name == 'nt':
        command = 'sync'
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        os.sync()  # type: ignore


class USBHandler:
    def __init__(self):
        pass

    def check_insert(self) -> bool:
        ret, udev, dev = get_usb_info()
        if not ret:
            return False
        self.udev_path = udev
        self.device_path = dev
        return True

    def check_mount(self) -> bool:
        return check_usb_mount()

    def mount(self) -> bool:
        return mount_usb(device_path=self.device_path,
                         target_m_point=USB_MOUNT_DIR,
                         timeout=500)

    def umount(self) -> bool:
        return umount_usb(udev_path=self.udev_path,
                          timeout=500)

    def sync(self) -> None:
        do_sync()


if __name__ == '__main__':
    ret, udev_path, device_path = get_usb_info()
    if not ret:
        print(udev_path)

    ret = mount_usb(device_path, USB_MOUNT_DIR, 500)

    path = os.path.join(USB_MOUNT_DIR, 'test/uesr.txt')
    f = open(path, 'w')
    f.write('')
    f.close()
    # ret = umount_usb(udev_path, 500)
    do_sync()
