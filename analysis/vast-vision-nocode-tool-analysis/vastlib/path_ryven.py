import sys
import platform

CONFIG_PATH = None
NODES_COMMON = None
NODES_UNCOMMON = None

if platform.system() == "Windows":
    # Windowsの場合
    CONFIG_PATH = "./config/config.json"
    if getattr(sys, 'frozen', False):
        # exeの場合
        NODES_COMMON = "./_internal/nodes_common"
        NODES_UNCOMMON = "./_internal/nodes_uncommon"
    else:
        # .pyを叩く場合
        NODES_COMMON = "./nodes_common"
        NODES_UNCOMMON = "./nodes_uncommon"
else:
    # Linuxの場合
    CONFIG_PATH = "/media/usb/Nocode/config.json"
    NODES_COMMON = "./nodes_common"
    NODES_UNCOMMON = "./nodes_uncommon"

