import sys
import platform

CONFIG_PATH = None
HEADLESS_CONFIG_PATH = None
MAIN_UI = None
ADJUSTER_UI = None
JUDGE_UI = None
KEYBOARD_UI = None
NUMPAD_UI = None
LOGO = None

if platform.system() == "Windows":
    # Windowsの場合
    CONFIG_PATH = "./config/config.json"
    HEADLESS_CONFIG_PATH = "./config/headless_config.json"
    if getattr(sys, 'frozen', False):
        # exeの場合
        MAIN_UI = "./_internal/headless/gui/mainwindow.ui"
        ADJUSTER_UI = "./_internal/headless/gui/adjuster_dialog.ui"
        JUDGE_UI = "./_internal/headless/gui/judge_widget.ui"
        KEYBOARD_UI = "./_internal/headless/gui/u_keyboard.ui"
        NUMPAD_UI = "./_internal/headless/gui/u_numpad.ui"
        LOGO = "./_internal/headless/gui/logo_mini5.svg"
    else:
        # .pyを叩く場合
        MAIN_UI = "./headless/gui/mainwindow.ui"
        ADJUSTER_UI = "./headless/gui/adjuster_dialog.ui"
        JUDGE_UI = "./headless/gui/judge_widget.ui"
        KEYBOARD_UI = "./headless/gui/u_keyboard.ui"
        NUMPAD_UI = "./headless/gui/u_numpad.ui"
        LOGO = "./headless/gui/logo_mini5.svg"
else:
    # Linuxの場合
    MAIN_UI = "./headless/gui/mainwindow.ui"
    CONFIG_PATH = "/media/usb/Nocode/config.json"
    HEADLESS_CONFIG_PATH = "/media/usb/NoCode/headless_config.json"
    ADJUSTER_UI = "./headless/gui/adjuster_dialog.ui"
    JUDGE_UI = "./headless/gui/judge_widget.ui"
    KEYBOARD_UI = "./headless/gui/u_keyboard.ui"
    NUMPAD_UI = "./headless/gui/u_numpad.ui"
    LOGO = "./headless/gui/logo_mini5.svg"

