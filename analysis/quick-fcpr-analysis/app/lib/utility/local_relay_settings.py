# ローカル変数の定義
local_R_setttings = {
    'start_program'    : {'type': bool, 'length': 1},
    'reset_program'    : {'type': bool, 'length': 1},
    'show_sidebar'    : {'type': bool, 'length': 200},
    'teach_page'      : {'type': bool, 'length': 2},
    'inch_seq'        : {'type': bool, 'length': 4},
}

local_MR_setttings = {
    'seq_step'    : {'type': bool, 'length': 10000},
}

local_T_setttings = {
    '1000msec_timer' : {'type': bool, 'length': 2},
    '500msec_timer'  : {'type': bool, 'length': 2},
    'block_timeout'  : {'type': bool, 'length': 1000},
    'block_timer1'   : {'type': bool, 'length': 1000},
    'block_timer2'   : {'type': bool, 'length': 1000},
    'block_timer3'   : {'type': bool, 'length': 1000},
    'move_static_timer'   : {'type': bool, 'length': 1000},
}