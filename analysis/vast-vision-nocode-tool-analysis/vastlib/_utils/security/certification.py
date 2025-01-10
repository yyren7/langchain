import hashlib


def get_cpu_serial() -> str:
    """Retrieve the Raspberry Pi's serial number"""
    cpu_serial = "0000000000000000"
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line[0:6] == 'Serial':
                    cpu_serial = line[10:26]
            f.close()
    except Exception:
        cpu_serial = "ERROR"

    return cpu_serial


def get_mac_address(interface: str) -> str:
    """Retrieve the MAC address of a Raspberry Pi interface"""
    try:
        mac = open('/sys/class/net/' + interface + '/address').readline()
    except Exception:
        mac = "ERROR"
    return mac[0:17]


def get_vast_id(serial: str, macaddr: str) -> str:
    """本体番号とMACアドレスからVASTのIDを生成"""

    # remove ":"
    macaddr = macaddr.replace(':', '')

    serial_and_mac = serial + macaddr

    # convert to decimal and add
    total = 0
    for i, char in enumerate(serial_and_mac):
        total += int(char, 16)

    # convert to hexdecimal
    vast_id = hex(total + int("0x12345678", 16))

    return vast_id


def get_vast_cipher(vast_id: str) -> str:
    """VASTのIDを暗号化"""
    # calculate two's complement
    cipher = "0x"
    for i, char in enumerate(vast_id[2:]):
        cipher += hex(15 - int(char, 16))[2:]

    cipher = hex(int(cipher, 16) + 1)

    # SHA-256 hash
    hashed = hashlib.sha256(vast_id.encode('utf-8')).hexdigest()

    return hashed


def check_hash(code: str) -> bool:
    ser = get_cpu_serial()
    mac = get_mac_address("wlan0")
    if ser == "ERROR" or mac == "ERROR":
        return False
    vast_id = get_vast_id(ser, mac)
    hash = get_vast_cipher(vast_id)
    if code == hash:
        return True
    return False


if __name__ == "__main__":

    ser = '10000000cbf98589'
    mac = 'e4:5f:01:f0:f6:87'
    hash = get_vast_cipher(get_vast_id(ser, mac))
    print(hash)

    # ser = get_cpu_serial()
    # mac = get_mac_address("wlan0")

    # if ser != "ERROR" and mac != "ERROR":
    #     vast_id = get_vast_id(ser, mac)
    #     hash = get_vast_cipher(vast_id)

    #     HASH_FILENAME = '/media/usb/hash.json'
    #     data = dict(hash=hash)
    #     ret = write_file(HASH_FILENAME, data)
