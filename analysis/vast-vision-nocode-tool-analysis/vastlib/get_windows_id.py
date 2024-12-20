import winreg

num = "0x12345678"

def get_windows_product_id():
    """
    WindowsのプロダクトIDを取得する
    """
    try:
        # レジストリキーを開く
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")

        # プロダクトIDを取得
        product_id, _ = winreg.QueryValueEx(key, "ProductId")

        # レジストリキーを閉じる
        winreg.CloseKey(key)

        return product_id
    except WindowsError:
        return "Unable to retrieve product ID."

import os

def get_computer_name():
    return os.environ.get('COMPUTERNAME', 'Unknown')


def convert_computer_name_to_number(computer_name):
    """
    コンピューター名の文字列を数値に変換する
    """
    # 文字列をバイト列に変換
    byte_name = computer_name.encode('utf-8')

    # バイト列の各バイトを数値に変換し、合計する
    total = sum(byte_name)

    return total

def convert_to_ascii_codes(input_string):
    """
    数字とアルファベットが含まれる文字列に対して、アルファベットをアスキーコードナンバーに変換する
    """
    result = ""
    for char in input_string:
        if char.isalpha():
            result += str(ord(char))
        else:
            result += char
    return result

import re

def get_vast_id():
    pattern = r'[^a-zA-Z0-9\s]'

    pid = get_windows_product_id()
    pid = re.sub(pattern, '', pid)
    pid_ascii = convert_to_ascii_codes(pid)

    comp_name = get_computer_name()
    comp_name = re.sub(pattern, '', comp_name)
    comp_name_ascii = convert_to_ascii_codes(comp_name)

    id_num = pid_ascii + comp_name_ascii

    total = 0
    for i, char in enumerate(id_num):
        total += int(char, 16)

    # convert to hexdecimal
    vast_id = hex(total + int(num, 16))

    return vast_id

import json

import hashlib
def get_vast_cipher(vast_id):
    # calculate two's complement
    cipher = "0x"
    for i, char in enumerate(vast_id[2:]):
        cipher += hex(15 - int(char, 16))[2:]

    cipher = hex(int(cipher, 16) + 1)

    # SHA-256 hash
    hashed = hashlib.sha256(vast_id.encode('utf-8')).hexdigest()

    return hashed
def check_id_authentication():
    id_path = "./authentication/id.json"
    key_path = "./authentication/key.json"
    _dir = os.path.dirname(id_path)

    if not os.path.exists(_dir):
        os.makedirs(_dir)

    if not os.path.isfile(id_path):
        vastid = get_vast_id()
        # 初期設定値
        _config = {
            "id": vastid
        }
        with open(id_path, 'w') as f:
            json.dump(_config, f, indent=4)

    if not os.path.isfile(key_path):
        raise SystemError("ID authentication key is not found.")
    else:
        with open(key_path, "r") as fr:
            _key = json.load(fr)

        correct_key = get_vast_cipher(get_vast_id())

        if _key["HASH"] != correct_key:
            raise SystemError("ID authentication key is incorrect.")

    return