from functools import wraps
import time
import lib.write_csv as h_csv

def stop_watch(func):
    @wraps(func)
    def wrapper(*args, **kargs):
        # 処理開始直前の時間
        start = time.perf_counter()
        # 処理実行
        result = func(*args, **kargs)
        # 処理終了直後の時間から処理時間を算出
        elapsed_time = time.perf_counter() - start
        # 処理時間を出力
        print("{} ms in {}".format(elapsed_time * 1000, func.__name__))
        # ログファイル名の指定があれば
        # if (len(args) > 1):
        h_csv.writeCsvFile(func.__name__, elapsed_time * 1000)

        return result
    return wrapper