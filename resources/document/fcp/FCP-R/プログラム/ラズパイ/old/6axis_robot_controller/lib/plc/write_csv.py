#-*- using:utf-8 -*-
import csv
import os
import datetime
import time

######################### 変数定義 ########################
# ヘッダー生成
HEADER = ['date', 'func_name', 'data_1', 'data_2', 'data_3', 'data_4', 'data_5']  
# フォルダ名
FOLDER_NAME = './log'
# 日付・時刻取得（ファイル名に利用）
DATE = datetime.datetime.now()
# パス生成
EXT = '.csv'
FILE_NAME = FOLDER_NAME + '/' + '{0:%Y_%m_%d_%H_%M_%S}'.format(DATE) + EXT
##########################################################

######################### 関数定義 ########################
def initCsvFile():
     # ログ用のフォルダ作成
    os.makedirs(FOLDER_NAME, exist_ok=True)
    # ファイルパス生成
    # FILE_NAME = folder_name + '/' + FILE_NAME + EXT 
    try:
        with open(FILE_NAME, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)
    except FileNotFoundError as e:
        print(e)
    except csv.Error as e:
        print(e)

def writeCsvFile(data_1='N/A', data_2='N/A', data_3='N/A', data_4='N/A', data_5='N/A'):
    # 時間計測開始
    # time_start = time.perf_counter()    

    # 日付・時刻取得
    now_date = '{0:%Y_%m_%d_%H_%M_%S}'.format(datetime.datetime.now())
    # データ整形
    written_data_str = now_date + ',' + str(data_1) + ',' + str(data_2) + ',' + str(data_3) + ',' + str(data_4) + ',' + str(data_5)
    written_data_str_ary = written_data_str.split(',')
    try:
        # データ追記
        with open(FILE_NAME, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(written_data_str_ary)

            ############### 書き込むのにかかる時間を計測 ################
            # time_end = time.perf_counter()
            # elapsed_time = time_end - time_start
            # written_data_str = now_date + ',' + str('write_CSV_' + data_1) + ',' + str(elapsed_time*1000) + ',' + str('N/A') + ',' + str('N/A') + ',' + str('N/A')
            # written_data_str_ary = written_data_str.split(',')     
            # writer.writerow(written_data_str_ary)
            ###########################################################

            # print(f'write time: {(elapsed_time * 1000):.7}')  
    except FileNotFoundError as e:
        print(e)
    except csv.Error as e:
        print(e)

initCsvFile()