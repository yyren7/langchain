from lib.utility.constant import DM, EM, R, MR, LR, CR, T
from lib.utility.common_globals import L, RD, RAC
from lib.utility.constant import TEACH_FILE_PATH, NUMBER_PARAM_FILE_PATH, FLAG_PARAM_FILE_PATH, ERROR_FILE_PATH
# from lib.utility.globals import error_yaml, number_param_yaml, initial_number_param_yaml

import lib.utility.helper as helper


# YAMLファイルからパラメータを読み込む関数
def read_param():
  param_yaml = helper.read_yaml(NUMBER_PARAM_FILE_PATH)
  current_page_no = L.EM_relay[2001]
  offset_point_no = (current_page_no-1)*15
  for point_no in range(1, 15):
    key = param_yaml[f'D{point_no+offset_point_no}']
    L.EM_relay[1800+(point_no-1)*10:1800+len(helper.name_to_ascii16(key['name'], 20))+(point_no-1)*10] = helper.name_to_ascii16(key['name'], 20)
    L.EM_relay[4000+(point_no-1)*2:4000+len(helper.int32_to_uint16s(int(key['value']*1000)))+(point_no-1)*2] = helper.int32_to_uint16s(int(key['value']*1000))
 
# 表の書き込み
def write_param():
  L.LD(R, 2000)
  L.OUT(R, 7000)
  L.LDP(R, 2000)
  if (L.aax & L.iix):
    param_yaml = helper.read_yaml(NUMBER_PARAM_FILE_PATH)
    current_page_no = L.EM_relay[2001]
    offset_point_no = (current_page_no-1)*15
    for point_no in range(1, 15):
      key = param_yaml[f'D{point_no+offset_point_no}']
      key['name'] = helper.ascii16_to_name(L.EM_relay[1800+(point_no-1)*10:1810+(point_no-1)*10])
      key['value'] = helper.uint16s_to_int32(L.EM_relay[4000+(point_no-1)*2], L.EM_relay[4001+(point_no-1)*2]) / 1000.0
    helper.write_yaml(NUMBER_PARAM_FILE_PATH, param_yaml)

# 現在ページ更新
def update_page_no():
  # インクリメント
  L.LDP(R, 2015)
  L.ANDLDL(L.EM_relay[2001], L.EM_relay[2000])
  L.OUT(MR, 2015)
  if (L.aax & L.iix):
    L.EM_relay[2001] = L.EM_relay[2001] + 1
    L.EM_relay[2002] = L.EM_relay[2002] + L.EM_relay[2000]
  # デクリメント
  L.LDP(R, 2014)
  L.ANDLDG(L.EM_relay[2001], 1)
  L.OUT(MR, 2014)
  if (L.aax & L.iix):
    L.EM_relay[2001] = L.EM_relay[2001] - 1
    L.EM_relay[2002] = L.EM_relay[2002] - L.EM_relay[2000]
  # 表の更新
  L.LD(MR, 2014)
  L.OR(MR, 2015)
  if (L.aax & L.iix):
    read_param()

# 選択中データ番号更新
def update_data_no():
  # D1
  btn_addr = 2200
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D2
  btn_addr = 2201
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2200)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D3
  btn_addr = 2202
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2200)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D4
  btn_addr = 2203
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2200)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D5
  btn_addr = 2204
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2200)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D6
  btn_addr = 2205
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2200)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D7
  btn_addr = 2206
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2200)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D8
  btn_addr = 2207
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2200)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D9
  btn_addr = 2208
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2200)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D10
  btn_addr = 2209
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2200)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D11
  btn_addr = 2210
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2200)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D12
  btn_addr = 2211
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2200)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D13
  btn_addr = 2212
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2200)
  L.ANPB(R, 2213)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D14
  btn_addr = 2213
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2200)
  L.ANPB(R, 2214)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]
  # D15
  btn_addr = 2214
  L.LDP(R, btn_addr)
  L.LD(R, 5000 + btn_addr)
  L.ANPB(R, 2201)
  L.ANPB(R, 2202)
  L.ANPB(R, 2203)
  L.ANPB(R, 2204)
  L.ANPB(R, 2205)
  L.ANPB(R, 2206)
  L.ANPB(R, 2207)
  L.ANPB(R, 2208)
  L.ANPB(R, 2209)
  L.ANPB(R, 2210)
  L.ANPB(R, 2211)
  L.ANPB(R, 2212)
  L.ANPB(R, 2213)
  L.ANPB(R, 2200)
  L.ORL()
  L.OUT(R, 5000 + btn_addr)
  L.LDP(R, 5000 + btn_addr)
  if (L.aax & L.iix):
    L.EM_relay[2032] = btn_addr - 2200 + 1 + (L.EM_relay[2031] - 1) * L.EM_relay[2030]