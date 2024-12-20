

# アドレス毎に指定された進数表現を元に、入力されたアドレスの文字列を10進数数値に変換
def decimal_convert(decimal: str, str_address: str) -> int:
    """
    # "10": "99999" => 99999
    # "16": "FFFF" => 65535
    # "1016": "10015" => 100*16 + 15 = 1615
    # "108": "1007" => 100*8 + 7 = 807
    # "10F": "100F" => 100*16 + 15 = 1615
    # "10.7": "100.7" => 100[7] =  107
    # "10.9": "100.9" => 100[9] =  109
    # "10.15": "100.15" => 100[15] = 115
    # "10.F": "100.F" => 100[15] = 115
    """
    if decimal == "10":
        int_address = int(float(str_address))
    elif decimal == "16":
        int_address = int(str_address, 16)
    elif decimal == "1016":
        # 下2桁だけ分割し、それより上を*16 + 下2桁
        try:
            int_address = int(
                str_address[:-2]) * 16 + int(str_address[-2:])
        except Exception:
            int_address = int(str_address[-2:]) * 16
    elif decimal == "108":
        # 下1桁だけ分割し、それより上を*8*2 + 下1桁
        try:
            int_address = int(
                str_address[:-1]) * 16 + int(str_address[-1:])
        except Exception:
            int_address = int(str_address[-1:]) * 16
    elif decimal == "10F":
        # 下1桁だけ分割し、それより上を*16 + 下1桁を10進数変換
        try:
            int_address = int(
                str_address[:-1]) * 16 + int(str_address[-1:], 16)
        except Exception:
            int_address = int(str_address[-1:]) * 16
    elif (decimal == "10.7" or decimal == "10.8") or (decimal == "10.15" or decimal == "10.16"):
        # 整数と少数に分けて、整数を8*2倍 + 少数
        # 整数と少数に分けて、整数を16倍 + 少数
        try:
            i, d = str_address.split(".")
            int_address = int(i) * 16 + int(d)
        except Exception:
            int_address = int(str_address) * 16
    elif decimal == "10.9" or decimal == "10.10":
        # 整数と少数に分けて、整数を10倍 + 少数 = 少数化*100(2桁)
        int_address = float(str_address) * 100
    elif decimal == "10.F":
        # 整数と少数に分けて、整数を16倍 + 少数を10進数変換
        try:
            i, d = str_address.split(".")
            int_address = int(i) * 16 + int(d, 16)
        except Exception:
            int_address = int(str_address) * 16
    else:
        int_address = None
    return int_address


# 10進数数値からアドレス毎に指定された進数表現の文字列に変換
def each_convert(decimal: str, int_address: int):
    """
    # "10": 99999 => "99999"
    # "16": 65535 => "FFFF"
    # "1016": 1615 = 100*16 + 15 => "10015"
    # "108": 807 = 100*8 + 7 => "1007"
    # "10F": 1615 = 100*16 + 15 => "100F"
    # "10.7": 107 = 100[7] => "100.7"
    # "10.9": 109 = 100[9] => "100.9"
    # "10.15": 115 = 100[15] => "100.15"
    # "10.F": 115 = 100[15] => "100.F"
    """
    if decimal == "10":
        str_address = format(int_address, "d")
        quotient = str_address
        remainder = "00"

    elif decimal == "16":
        str_address = format(int_address, "x")
        quotient = str_address
        remainder = "00"

    elif decimal == "1016":
        # 16で割り、"商余(02d)"
        x, y = divmod(int_address, 16)
        str_address = format(x, "d") + format(y, "02d")
        quotient = format(x, "d")
        remainder = format(y, "02d")

    elif decimal == "108":
        # 8で割り、"商余(01d)"
        x, y = divmod(int_address, 8)
        str_address = format(x, "d") + format(y, "01d")
        quotient = format(x, "d")
        remainder = format(y, "01d")

    elif decimal == "10F":
        # 16で割り、"商余(01x)"
        x, y = divmod(int_address, 8)
        str_address = format(x, "d") + format(y, "01x")
        quotient = format(x, "d")
        remainder = format(y, "01x")

    elif (decimal == "10.7" or decimal == "10.8"):
        # 8で割り、"商.余(01d)"
        x, y = divmod(int_address, 8)
        str_address = format(x, "d") + "." + format(y, "01d")
        quotient = format(x, "d")
        remainder = format(y, "01d")

    elif (decimal == "10.15" or decimal == "10.16"):
        # 16で割り、"商.余(02d)"
        x, y = divmod(int_address, 16)
        str_address = format(x, "d") + "." + format(y, "02d")
        quotient = format(x, "d")
        remainder = format(y, "02d")

    elif decimal == "10.9" or decimal == "10.10":
        # 10で割り、"商.余(01d)"
        x, y = divmod(int_address, 10)
        str_address = format(x, "d") + "." + format(y, "01d")
        quotient = format(x, "d")
        remainder = format(y, "01d")

    elif decimal == "10.F":
        # 10で割り、"商.余(01x)"
        x, y = divmod(int_address, 10)
        str_address = format(x, "d") + "." + format(y, "01x")
        quotient = format(x, "d")
        remainder = format(y, "01x")

    else:
        str_address = None
        quotient = None
        remainder = None

    return str_address, quotient, remainder


if __name__ == "__main__":
    converted = decimal_convert("10.10", "100")
