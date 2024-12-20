import binascii
import os

# NOTE: command
SA1_INDEX = 14
SA2_INDEX = 16
# NOTE: response
DA1_INDEX = 8
DA2_INDEX = 10
# NOTE: identification
SID_INDEX = 18
CODE_INDEX = 20


def get_random_sid_str(bytes: int = 1) -> str:
    """SIDをランダムに設定"""
    return str(binascii.b2a_hex(os.urandom(bytes)), 'ascii')


def get_random_sid(bytes: int = 1) -> bytes:
    """SIDをランダムに設定"""
    return os.urandom(bytes)


def check_command(send_cmd: list, recv_cmd: list) -> bool:
    """送った指令に対する結果であるか、
    レスポンスの文字列を見て確認する(Omron限定)
    response
    0: recv command
    2: send command [command]
    3: error command

    Args:
        response (list): _description_

    Returns:
        bool: _description_
    """
    # print(send_cmd, recv_cmd)

    # check DA1 == SA1
    if send_cmd[SA1_INDEX:SA1_INDEX + 2] != recv_cmd[DA1_INDEX:DA1_INDEX + 2]:
        return False

    # check SA2 == DA2
    if send_cmd[SA2_INDEX:SA2_INDEX + 2] != recv_cmd[DA2_INDEX:DA2_INDEX + 2]:
        return False

    # check sid
    if send_cmd[SID_INDEX:SID_INDEX + 2] != recv_cmd[SID_INDEX:SID_INDEX + 2]:
        return False

    # check command
    if send_cmd[CODE_INDEX:CODE_INDEX + 4] != recv_cmd[CODE_INDEX:CODE_INDEX + 4]:
        return False

    return True


if __name__ == "__main__":
    print(get_random_sid(1))
