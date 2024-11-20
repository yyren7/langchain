#########################################
ロボット共通制御プログラム
#########################################

# ファイル構成
-robot_controller
    -config
        -setting_robot.xlsx     #通信用の割付アドレスマップ
        -settings.ini           #パラメータiniファイル

    -lib
        -plc                    #PLCとの通信用モジュール
        -robot                  #ロボットAPI

    -src
        -main.py                #メインプログラム
        -process_controller.py  #プログラムの自動立ち上げなどの管理等
        -setting.py             #バージョン、各種PATHの設定等
    
