
def getPalletOffset(pallet, pallet_no):
  # オフセット量XYZ計算準備
  vec = {'AB':{},'AC':{}, 'BD':{},'CD':{}}
  vec['AB']['x'] = pallet[pallet_no-1]['B']['x'] - pallet[pallet_no-1]['A']['x']
  vec['AB']['y'] = pallet[pallet_no-1]['B']['y'] - pallet[pallet_no-1]['A']['y']
  vec['AB']['z'] = pallet[pallet_no-1]['B']['z'] - pallet[pallet_no-1]['A']['z']
  vec['AC']['x'] = pallet[pallet_no-1]['C']['x'] - pallet[pallet_no-1]['A']['x']
  vec['AC']['y'] = pallet[pallet_no-1]['C']['y'] - pallet[pallet_no-1]['A']['y']
  vec['AC']['z'] = pallet[pallet_no-1]['C']['z'] - pallet[pallet_no-1]['A']['z']
  vec['BD']['x'] = pallet[pallet_no-1]['D']['x'] - pallet[pallet_no-1]['B']['x']
  vec['BD']['y'] = pallet[pallet_no-1]['D']['y'] - pallet[pallet_no-1]['B']['y']
  vec['BD']['z'] = pallet[pallet_no-1]['D']['z'] - pallet[pallet_no-1]['B']['z']
  vec['CD']['x'] = pallet[pallet_no-1]['D']['x'] - pallet[pallet_no-1]['C']['x']
  vec['CD']['y'] = pallet[pallet_no-1]['D']['y'] - pallet[pallet_no-1]['C']['y']
  vec['CD']['z'] = pallet[pallet_no-1]['D']['z'] - pallet[pallet_no-1]['C']['z']
  vec_N = {}
  vec_N['a']  = vec['AB']['y'] * vec['AC']['z'] - vec['AB']['z'] * vec['AC']['y']
  vec_N['b']  = vec['AB']['z'] * vec['AB']['x'] - vec['AB']['x'] * vec['AC']['z']
  vec_N['c']  = vec['AB']['x'] * vec['AC']['y'] - vec['AB']['y'] * vec['AB']['x']
  # オフセット量XY計算準備
  MAX_row = pallet[pallet_no-1]['row']
  MAX_col = pallet[pallet_no-1]['col']
  dst_pocket = pallet[pallet_no-1]['cnt']
  if ((dst_pocket <= MAX_row * MAX_col) and (dst_pocket > 0)):
    dst_row = (dst_pocket-1) % MAX_row + 1
    dst_col = int((dst_pocket-1) / MAX_row) + 1
  else:
    dst_row = 1
    dst_col = 1
  # 目標位置算出用の4点計算
  dst_row_index = dst_row - 1
  dst_col_index = dst_col - 1
  divided_row_num = MAX_row - 1
  divided_col_num = MAX_col - 1
  P = {'AB':{},'BD':{},'CD':{},'AC':{}}
  P['AB']['x'] = vec['AB']['x'] * (dst_row_index / divided_row_num) + pallet[pallet_no-1]['A']['x']
  P['AB']['y'] = vec['AB']['y'] * (dst_row_index / divided_row_num) + pallet[pallet_no-1]['A']['y']
  P['BD']['x'] = vec['AB']['x'] + vec['BD']['x'] * (dst_col_index / divided_col_num) + pallet[pallet_no-1]['A']['x']
  P['BD']['y'] = vec['AB']['y'] + vec['BD']['y'] * (dst_col_index / divided_col_num) + pallet[pallet_no-1]['A']['y']
  P['CD']['x'] = vec['AC']['x'] + vec['CD']['x'] * (dst_row_index / divided_row_num) + pallet[pallet_no-1]['A']['x']
  P['CD']['y'] = vec['AC']['y'] + vec['CD']['y'] * (dst_row_index / divided_row_num) + pallet[pallet_no-1]['A']['y']
  P['AC']['x'] = vec['AC']['x'] * (dst_col_index / divided_col_num) + pallet[pallet_no-1]['A']['x']
  P['AC']['y'] = vec['AC']['y'] * (dst_col_index / divided_col_num) + pallet[pallet_no-1]['A']['y']
  S1 = ((P['AC']['x'] - P['BD']['x']) * (P['AB']['y'] - P['BD']['y']) - (P['AC']['y'] - P['BD']['y']) * (P['AB']['x'] - P['BD']['x'])) / 2
  S2 = ((P['AC']['x'] - P['BD']['x']) * (P['BD']['y'] - P['CD']['y']) - (P['AC']['y'] - P['BD']['y']) * (P['BD']['x'] - P['CD']['x'])) / 2
  # オフセット量XYZ計算
  offset = {'x': 0.0, 'y': 0.0, 'z': 0.0}
  offset['x'] = round(P['AB']['x'] + (P['CD']['x']- P['AB']['x']) * (S1 / (S1 + S2)) - pallet[pallet_no-1]['A']['x'], 3)
  offset['y'] = round(P['AB']['y'] + (P['CD']['y']- P['AB']['y']) * (S1 / (S1 + S2)) - pallet[pallet_no-1]['A']['y'], 3)
  if (abs(vec_N['c']) > 0): offset['z'] = round((-1) * (vec_N['a'] * offset['x'] + vec_N['b'] * offset['y']) / vec_N['c'], 3)
  
  return offset