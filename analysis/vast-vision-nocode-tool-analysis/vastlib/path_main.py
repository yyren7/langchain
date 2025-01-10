import platform
import sys
import os

FUNCTION_DIRECTORIES = None
USER_FUNCTION_DIRECTORY = None
UI_PATH = None

if platform.system() == "Windows":
    # Windowsの場合
    pass
    if getattr(sys, 'frozen', False):
        # exeの場合
        FUNCTION_DIRECTORIES = ['./_internal/function_blocks', './user_functions']
        USER_FUNCTION_DIRECTORY = None
        UI_PATH = './_internal/pyside/main_window.ui'
        sys.path.append(os.getcwd())
    else:
        # .pyを叩く場合
        FUNCTION_DIRECTORIES = ['./function_blocks', './user_functions']
        USER_FUNCTION_DIRECTORY = None
        UI_PATH = './pyside/main_window.ui'
else:
    # Linuxの場合
    FUNCTION_DIRECTORIES = ['./function_blocks', './_function_blocks']
    USER_FUNCTION_DIRECTORY = '/media/usb/function_blocks'
    UI_PATH = './pyside/main_window.ui'
    pass
