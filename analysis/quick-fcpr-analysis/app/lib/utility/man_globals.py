import redis, copy

# from lib.utility.laddar_api import LaddarSeqAPI
# from lib.utility.robot_api_client import RobotApiClient
from lib.plc.plc_base_class import BasePLC
import lib.utility.helper as helper
# from lib.utility.local_relay_settings import local_R_setttings, local_T_setttings
from lib.utility.constant import TEACH_FILE_PATH, NUMBER_PARAM_FILE_PATH, FLAG_PARAM_FILE_PATH, ERROR_FILE_PATH

# 各種設定ファイル読み込み
error_yaml = helper.read_yaml(ERROR_FILE_PATH)
number_param_yaml = helper.read_yaml(NUMBER_PARAM_FILE_PATH)
initial_number_param_yaml = copy.deepcopy(number_param_yaml)