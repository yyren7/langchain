import redis, copy

from lib.utility.laddar_api import LaddarSeqAPI
from lib.utility.robot_api_client import RobotApiClient
from lib.plc.plc_base_class import BasePLC
import lib.utility.helper as helper
from lib.utility.local_relay_settings import local_R_setttings, local_MR_setttings, local_T_setttings
from lib.utility.constant import TEACH_FILE_PATH, NUMBER_PARAM_FILE_PATH, FLAG_PARAM_FILE_PATH, ERROR_FILE_PATH


# Laddarインスタンス生成
L = LaddarSeqAPI(max_EM_relay=60000, max_DM_relay=60000, max_R_relay=2000, max_MR_relay=2000, max_LR_relay=2000, max_T_relay=2000, max_C_relay=2000, local_R_setttings=local_R_setttings, local_MR_setttings=local_MR_setttings, local_T_setttings=local_T_setttings)

# Redisサーバーに接続
RD = redis.StrictRedis(host='localhost', port=6379, db=1)

# ロボット制御用インスタンス生成
RAC = RobotApiClient(redis_host='localhost', redis_port=6379, redis_db=2)