from lib.utility.constant import DM, EM, R, MR, LR, CR, T
from lib.utility.common_globals import L, RD, RAC
from lib.utility.constant import TEACH_FILE_PATH, NUMBER_PARAM_FILE_PATH, FLAG_PARAM_FILE_PATH, ERROR_FILE_PATH
from lib.utility.auto_globals import error_yaml, number_param_yaml, initial_number_param_yaml

import lib.utility.helper as helper

import copy

def update_status():
    # Error
    L.LD(MR, 501)
    if (L.aax & L.iix):
        auto_status = 'Error'
        L.EM_relay[0:0+len(helper.name_to_ascii16(auto_status, 40))] = helper.name_to_ascii16(auto_status, 40)

    # リセットボタン点滅
    L.LD(MR, 501)
    # L.MPS()
    L.AND(L.local_T['500msec_timer[0]']['name'], L.local_T['500msec_timer[0]']['addr'])
    L.OUT(R, 5005)
    # L.MPP()
    # L.OUT(R, 5003)

    # Pause
    L.LDP(R, 5003)
    if (L.aax & L.iix):
        auto_status = 'Pausing ...'
        L.EM_relay[0:0+len(helper.name_to_ascii16(auto_status, 40))] = helper.name_to_ascii16(auto_status, 40)

    # Error Reset
    L.LD(R, 5)
    L.AND(MR, 501)
    L.OUT(L.local_R['reset_program[0]']['name'], L.local_R['reset_program[0]']['addr'])
    if (L.aax & L.iix):
        L.EM_relay[3800:3900] = [0] * 100
        auto_status = 'Program was reset ...'

        # パラメータ初期化
        # param_yaml.clear()
        number_param_yaml.update(copy.deepcopy(initial_number_param_yaml))

        # ステータス更新
        L.EM_relay[0:0+len(helper.name_to_ascii16(auto_status, 40))] = helper.name_to_ascii16(auto_status, 40)

def check_error():
    error_val = sum(L.EM_relay[3800:3900])
    L.LDG(error_val, 0)
    L.OUT(MR, 501)

    # エラーファイル更新
    L.LDP(MR, 501)
    if (L.aax & L.iix):
        helper.write_yaml(ERROR_FILE_PATH, error_yaml)