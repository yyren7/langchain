# To read yaml data
import yaml
from collections import OrderedDict

# YAMLファイルを順序通り読み込む関数
def read_yaml(file_path):
    with open(file_path, 'r') as file:
      # `yaml.Loader` を指定してロードします
      data = yaml.load(file, Loader=yaml.SafeLoader)
      return OrderedDict(data)

# YAMLファイルに書き込む関数
def write_yaml(file_path, data):
    with open(file_path, 'w') as file:
      dict_data = dict(data)
      yaml.dump(dict_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)

# INT32を2つのUINT16に変換する関数
def int32_to_uint16s(value):
    upper = (value >> 16) & 0xFFFF
    lower = value & 0xFFFF
    return lower, upper

# "name"をASCIIコードに変換する関数
def name_to_ascii16(name, char_len):
    ascii16 = []
    for i in range(0, len(name), 2):
        if i + 1 < len(name):
            combined = (ord(name[i]) << 8) | ord(name[i + 1])
        else:
            combined = (ord(name[i]) << 8)
        ascii16.append(combined)
    # 残りの要素を0で埋める
    while len(ascii16) < char_len // 2:
        ascii16.append(0)
    return ascii16

# ASCIIコードを"name"に変換する関数
def ascii16_to_name(ascii16):
    name = ''
    for value in ascii16:
        # 高位バイトと低位バイトを取り出す
        high_byte = (value >> 8) & 0xFF
        low_byte = value & 0xFF
        # バイトから文字に変換
        if high_byte > 0:
            name += chr(high_byte)
        if low_byte > 0:
            name += chr(low_byte)
    return name

# 2つのUINT16をINT32に変換する関数
def uint16s_to_int32(lower, upper):
    # UINT16 から符号付き INT32 に変換する
    result = (upper << 16) | lower
    # もし結果が 2^31 以上なら符号付き INT32 としてマイナスに変換
    if result >= 0x80000000:
        result -= 0x100000000
    return result