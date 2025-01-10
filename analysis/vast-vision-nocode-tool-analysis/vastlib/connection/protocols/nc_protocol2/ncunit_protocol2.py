import struct
import socket


class Connect():
    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port

    def header_adjustment(self, il, c, f, s, r):
        """
        ヘッダーの作成
        """
        il = (il + " " * 1)[:1]
        c = (c + " " * 3)[:3]
        f = (f + " " * 4)[:4]
        s = (s + " " * 8)[:8]
        r = (r + " " * 2)[:2]
        header = il + c + f + s + r

        return header

    def cal_check_sum(self, header, data):
        """
        チェックサムの作成
        """
        # チェックサムの作成
        check_sum = ""
        d = 0
        for i in header:
            d = d + ord(i)
        if data != "":
            # brotherの場合のLFはASCIIでCR(13)+LF(10)
            d = d + 23
            for i in data:
                d = d + ord(i)
        _check_sum = str(d % 16)
        check_sum = (" " * 2 + _check_sum)[-2:]

        return check_sum

    def generate_telegram(self, il, c, f, s, r):
        """
        電文生成

        Header = % il c1 c2 c3 f1 f2 f3 f4 s1 s2 s3 s4 s5 s6 s7 s8 r1 r2
                %:  開始マーク
                il: 識別子 1byte
                    C:  コマンド
                    R:  レスポンス
                c1: コマンド種別 3byte
                f1: 機能 4byte
                s1: 伝文 8byte
                r1: 完了コード 2byte
                    00: 正常終了
                    以外: 以上終了
                ※コマンドヘッダ表内の空白はスペースを意味する
            Data
                LFで始まり, FotterのLFまでの間
            Footer = LF ss %
                ss: チェックサム, 10進数2桁の数字
                    1. Headerの%以降～FooterのLFの前の文字までをすべて10進数表現で加算
                    2. 1.を10進数16で除算したときの余りがss
            ※%はISO/ASCII:%、EIA:ER
            ※LFはISO: LF、EIA: EOB、ASCII: CR+LF
        """
        # 電文生成
        error_code = 0
        telegram = ""

        try:
            header = self.header_adjustment(il, c, f, s, r)

            data = ""
            check_sum = self.cal_check_sum(header, data)
            footer = str(check_sum)

            if data == "":
                _telegram = (
                    "%" + header + "\r\n" + footer + "%"
                )
            else:
                _telegram = (
                    "%" + header + "\r\n" + data + "\r\n" + footer + "%"
                )
            telegram = b"".join([struct.pack("B", ord(x)) for x in _telegram])

        except Exception:
            error_code = 10000

        return telegram, error_code

    def define_socket(self):
        """
        socket定義
        """
        error_code = 0
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(0.1)
        except Exception:
            error_code = 10001  # エラー発生
        finally:
            return error_code

    def send_telegram(self, telegram):
        """
        電文送受信

        [in]
        telegram: 送信電文

        [out]
        recv: 受信電文
        error_code: 0以外の場合はエラー発生
        """
        error_code = 0
        recv = ""
        try:
            self.sock.connect((self.ip_address, self.port))
        except Exception:
            error_code = 10002
            return recv, error_code

        try:
            self.sock.send(bytes(telegram))
            recv = self.sock.recv(1024)
            self.sock.close()
        except Exception:
            error_code = 10003
        else:
            error_code = int(recv[17:19])

        return recv, error_code

    def divide_received(self, recv, res_structure):
        """
        受信電文の分割

        [in]
        recv: 受信電文
        res_structure: 抽出するシンボル部の項目リスト

        [out]
        divided_data: 分割後のデータ <- {シンボル部(str): 項目部(dic)}
        error_code: 0以外の場合はエラー発生
        """
        # b'%RREDPRGN        00\r\n72337233              \r\n06%'
        recv_data = {}
        error_code = 0

        # 取得データを辞書型にする <- {シンボル部(str): 項目部(str)}
        recv_list = recv.split(b'\r\n')
        recv_list.pop(0)  # レスポンスデータのヘッダ部分を削除
        for _sym_data in recv_list:
            if b',' in _sym_data:
                sym_data = _sym_data.split(b',', 1)
                recv_symbol = sym_data[0]  # シンボル部
                recv_symdata = sym_data[1]  # 項目部
                recv_data[recv_symbol.decode("utf8")] = recv_symdata.decode("utf8")

        # res_structureに従い取得データからデータ抽出
        divided_data = {}
        for symbol, list in res_structure.items():  # 各シンボルごとの処理
            _data = {}
            if symbol in recv_data:
                _recv_symdata = recv_data[symbol]
                _recv_symdatalist = _recv_symdata.split(",")
                for key, value in zip(list, _recv_symdatalist):
                    _data[key] = value
            divided_data[symbol] = _data

        return divided_data, error_code

    def read_plcd(self, device_name, device_num):
        """
        PLC信号データを取得する

        [in]
        device_name: 信号種類
        device_num: 番号
        """

        result = {}

        # 設定
        c = f = s = r = ""
        il = "C"
        c = "RED"
        f = "PLCD"

        k = (device_name + " " * 4)[:4]
        n = (str(device_num) + " " * 4)[:4]
        s = k + n

        # 電文生成
        telegram, error_code = self.generate_telegram(il, c, f, s, r)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(telegram)

        # Socket定義
        error_code = self.define_socket()
        if error_code != 0:
            result["result"] = error_code
            return result

        # 電文送受信
        recv, error_code = self.send_telegram(telegram)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(recv)

        # 受信電文の分割
        try:
            recv_list = recv.split(b'\r\n')
            divided_data = recv_list[1].decode("utf8")
            result["data"] = divided_data
        except Exception:
            error_code = 104

        result["result"] = error_code
        return result

    def load_toln(self, unit, num):
        """
        TOLNun: 工具データ（タイプ1）

        [in]
        unit: 単位系（M: メトリック, I: インチ）
        num: データバンク番号（0~9: 10は0を使用）

        [data]
        <T01>
        lenoffset: 工具長オフセット
        lenwearcomp: 工具長摩耗補正
        diacomp: 工具径補正
        diawewarcomp: 工具径摩耗補正
        lifeunit: 寿命単位
        initlife: 初期寿命/終了寿命
        noticelife: 予告寿命
        life: 寿命
        name: 工具名
        speed: 周速
        rfeed: 回転送り
        scommand: S指令値
        fcommand: F指令値
        maxrspeed: 最高回転数
        clean: ツール洗浄
        cts: CTS
        typenum: 工具種類番号
        posoffsetx: 工具位置オフセット(X)
        poswearcompx: 工具位置摩耗補正(X)
        posoffsety: 工具位置オフセット(Y)
        poswearcompy: 工具位置摩耗補正(Y)
        virtcutedgedirection: 仮想刃先方向
        """

        result = {}

        # 設定
        c = f = s = r = ""
        il = "C"
        c = "LOD"
        s = f"TOLN{unit}{num}"

        # 電文生成
        telegram, error_code = self.generate_telegram(il, c, f, s, r)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(telegram)

        # Socket定義
        error_code = self.define_socket()
        if error_code != 0:
            result["result"] = error_code
            return result

        # 電文送受信
        recv, error_code = self.send_telegram(telegram)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(recv)
        # recv = b"%RLOD    TOLNM2  00\r\nT01,120.000,0.000,0.000,0.000,,0,0,0,'              ',,,,,,0,0,,0.000,0.000,0.000,0.000,\r\nT02,0.000,0.000,0.000,0.000,,0,0,0,'              ',,,,,,0,0,,0.000,0.000,0.000,0.000,\r\nT03,0.000,0.000,0.000,0.000,,0,0,0,'              ',,,,,,0,0,,0.000,0.000,0.000,0.000,\r\nT04,0.000,0.000,0.000,0.000,,0,0,0,'              ',,,,,,0,0,,0.000,0.000,0.000,0.000,\r\nT05,0.000,0.000,0.000,0.000,,0,0,0,'              ',,,,,,0,0,,0.000,0.000,0.000,0.000,\r\nT06,0.000,0.000,0.000,0.000,,0,0,0,'              ',,,,,,0,0,,0.000,0.000,0.000,0.000,\r\nT07,0.000,0.000,0.000,0.000,,0,0,0,'              ',,,,,,0,0,,0.000,0.000,0.000,0.000,\r\nT08,0.000,0.000,0.000,0.000,,0,0,0,'              ',,,,,,0,0,,0.000,0.000,0.000,0.000,\r\nT09,0.000,0.000,0.000,0.000,,0,0,0,'              ',,,,,,0,0,,0.000,0.000,0.000,0.000,\r\nT10,0.000,0.000,0.000,0.000,,0,0,0,'              ',,,,,,0,0,,0.000,0.000,0.000,0.000,\r\nT11,0.000,0.000,0.000,0.000,,0,0,0,'              ',,,,,,0,0,,0.000,0.000,0.000,0.000,\r\nT12,0.000,0.000,0.000,0.000,,0,0,"

        # 受信電文の分割設定
        res_structure = {
            "T01": [
                "lenoffset", "lenwearcomp", "diacomp", "diawewarcomp", "lifeunit",
                "initlife", "noticelife", "life", "name", "speed",
                "rfeed", "scommand", "fcommand", "maxrspeed", "clean",
                "cts", "typenum", "posoffsetx", "poswearcompx", "posoffsety",
                "poswearcompy", "virtcutedgedirection"
            ]
        }
        # 受信電文の分割
        divided_data, error_code = self.divide_received(recv, res_structure)

        if error_code != 0:
            result["result"] = error_code
            return result

        result.update(divided_data)
        result["result"] = error_code
        return result

    def load_prd3(self):
        """
        PRD3: 生産データ3（状態履歴）

        [data]
        <C01>
        currtime: 現在（開始日時）
        currstatus: 現在（状態）
        currlang: 現在状態（言語）
        currstatinfo: 現在状態（プログラム番号/エラー番号）
        currfolder: 現在状態（フォルダ名）
        memstatus: メモリ運転種別
        """

        result = {}

        # 設定
        c = f = s = r = ""
        il = "C"
        c = "LOD"
        s = "PRD3"

        # 電文生成
        telegram, error_code = self.generate_telegram(il, c, f, s, r)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(telegram)

        # Socket定義
        error_code = self.define_socket()
        if error_code != 0:
            result["result"] = error_code
            return result

        # 電文送受信
        recv, error_code = self.send_telegram(telegram)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(recv)
        # recv = b"%RLOD    PRD3    00\r\nA01,2148,2148,2\r\nC01,20230731104231,5,0,050518,'        ',0\r\nB0001,20230731104231,2,0,007233,'/       ',0\r\nB0002,20230728191907,1,0,007233,'/       ',0\r\nB0003,20230728163042,2,0,007233,'/       ',0\r\nB0004,20230728162925,3,0,007233,'/       ',0\r\nB0005,20230728162735,2,0,007233,'/       ',0\r\nB0006,20230728162617,3,0,007233,'/       ',0\r\nB0007,20230728162023,2,0,007233,'/       ',0\r\nB0008,20230728161905,3,0,007233,'/       ',0\r\nB0009,20230728161722,2,0,007233,'/       ',0\r\nB0010,20230728161604,3,0,007233,'/       ',0\r\nB0011,20230728160637,2,0,007233,'/       ',0\r\nB0012,20230728160519,3,0,007233,'/       ',0\r\nB0013,20230728160442,2,0,007233,'/       ',0\r\nB0014,20230728160326,3,0,007233,'/       ',0\r\nB0015,20230728160303,4,0,007233,'/       ',0\r\nB0016,20230728160303,3,0,007233,'/       ',0\r\nB0017,20230728160301,4,0,007233,'/       ',0\r\nB0018,20230728160300,3,0,007233,'/       ',0\r\nB0019,20230728160251,4,0,007233,'/       ',0\r\nB0020,20230728160250,3,0,007233,'/       ',0\r\nB0021,20230728160250,4"

        # 受信電文の分割設定
        res_structure = {
            "C01": [
                "currtime", "currstatus", "currlang", "currstatinfo", "currfolder", "memstatus"
            ]
        }
        # 受信電文の分割
        divided_data, error_code = self.divide_received(recv, res_structure)

        if error_code != 0:
            result["result"] = error_code
            return result

        result.update(divided_data)
        result["result"] = error_code
        return result

    def load_prdc2(self, flag):
        """
        PRDC2: 生産データ2（時間表示）

        [in]
        flag: Trueのとき、N01~N20シンボルデータは最新の日付データのみ分割後データとして追加（N00シンボル）

        [data]
        <L01>
        cycletime1: サイクルタイム(1) （時間/分/0.1秒）
        cuttingtime1: 切削時間(1) （時間/分/0.1秒）
        cycletime2: サイクルタイム(2) （時間/分/0.1秒）
        cuttingtime2: 切削時間(2) （時間/分/0.1秒）
        prg1: プログラム番号(1)
        prg2: プログラム番号(2)
        prgfolder1: プログラムフォルダ(1)
        prgfolder2: プログラムフォルダ(2)
        memstatus1: メモリ運転種別(1)
        memstatus2: メモリ運転種別(2)

        <N01>
        date1: 稼働時間記録1 (年月日)
        time1: 稼働時間記録1 (時分秒)
        count1: 稼働時間記録1 (運転回数)
        energization1: 稼働時間記録1 (通電時間)

        <N02-20>
        N01と同一構造
        """

        result = {}

        # 設定
        c = f = s = r = ""
        il = "C"
        c = "LOD"
        s = "PRDC2"

        # 電文生成
        telegram, error_code = self.generate_telegram(il, c, f, s, r)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(telegram)

        # Socket定義
        error_code = self.define_socket()
        if error_code != 0:
            result["result"] = error_code
            return result

        # 電文送受信
        recv, error_code = self.send_telegram(telegram)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(recv)
        # recv = b"%RLOD    PRDC2   00\r\nL01,000000256,000000173,000000000,000000000,5000,0000,'/       ','        ',0,0\r\nM01,2,16\r\nN01,20230630,000000,    0,  1513\r\nN02,20230703,000000,    0,  3313\r\nN03,20230704,000000,    0,  2714\r\nN04,20230705,002655,   18, 71559\r\nN05,20230706,010035,   40, 44320\r\nN06,20230707,004249,   42, 40517\r\nN07,20230711,060503,   18,131854\r\nN08,20230712,031142,    3,230309\r\nN09,20230713,012627,   17, 50030\r\nN10,20230714,003732,    6, 23544\r\nN11,20230718,020959,    2, 95834\r\nN12,20230719,014247,    1, 14514\r\nN13,20230725,001218,    6,  4836\r\nN14,20230726,000000,    0, 71531\r\nN15,20230727,002032,   10, 85750\r\nN16,20230728,004538,   34,103857\r\nN17,20230731,000107,    2, 65849\r\nN18,20230627,082920,    4,240000\r\nN19,20230628,083058,    4,240001\r\nN20,20230629,000000,    0,101521\r\nO01,0,0,1,0\r\nP01,   35.4807,   16.5640,  -45.0600,    0.0000,    0.0000,    0.0000,    0.0000,    0.0000,        0,        0,        0,        0\r\n\r\n03%"

        # 受信電文の分割設定
        res_structure = {
            "L01": ["cycletime1", "cuttingtime1", "cycletime2", "cuttingtime2", "prg1", "prg2", "prgfolder1", "prgfolder2", "memstaus1", "memstaus2"],
            "N01": ["date", "time", "count", "energization"],
            "N02": ["date", "time", "count", "energization"],
            "N03": ["date", "time", "count", "energization"],
            "N04": ["date", "time", "count", "energization"],
            "N05": ["date", "time", "count", "energization"],
            "N06": ["date", "time", "count", "energization"],
            "N07": ["date", "time", "count", "energization"],
            "N08": ["date", "time", "count", "energization"],
            "N09": ["date", "time", "count", "energization"],
            "N10": ["date", "time", "count", "energization"],
            "N11": ["date", "time", "count", "energization"],
            "N12": ["date", "time", "count", "energization"],
            "N13": ["date", "time", "count", "energization"],
            "N14": ["date", "time", "count", "energization"],
            "N15": ["date", "time", "count", "energization"],
            "N16": ["date", "time", "count", "energization"],
            "N17": ["date", "time", "count", "energization"],
            "N18": ["date", "time", "count", "energization"],
            "N19": ["date", "time", "count", "energization"],
            "N20": ["date", "time", "count", "energization"]
        }
        # 受信電文の分割
        divided_data, error_code = self.divide_received(recv, res_structure)
        if error_code != 0:
            result["result"] = error_code
            return result

        if flag:  # flag==Trueのとき、N01~N20シンボルデータは最新の日付データのみ分割後データとして追加（N00シンボル）
            try:
                latest_divided_data = {}
                _latest_date = 0
                _latest_symbol = ""
                for symbol, dic in divided_data.items():
                    if "N" in symbol:
                        for key in dic:
                            if key.startswith("date"):
                                _date = int(dic[key])
                                _latest_symnum = key.replace("date", "")
                                if _date > _latest_date:
                                    _latest_date = _date
                                    _latest_symbol = symbol
                    else:
                        latest_divided_data[symbol] = dic
                # N00シンボル項目部のkeyは数字なしで作成["date", "time", "count", "energization"]
                latest_symbol_data = {}
                for key in divided_data[_latest_symbol]:
                    latest_symbol_data[key.replace(_latest_symnum, "")] = divided_data[_latest_symbol][key]
                latest_divided_data["N00"] = latest_symbol_data
                result.update(latest_divided_data)
            except Exception:
                error_code = 10004
        else:
            result.update(divided_data)

        result["result"] = error_code
        return result

    def load_prdd3(self):
        """
        PRDD3: 生産データ3（状態履歴）

        [data]
        <C01>
        currtime: 現在（開始日時）
        currstatus: 現在（状態）
        currlang: 現在状態（言語）
        currstatinfo: 現在状態（プログラム番号/エラー番号）
        currfolder: 現在状態（フォルダ名）
        memstatus: メモリ運転種別
        """

        result = {}

        # 設定
        c = f = s = r = ""
        il = "C"
        c = "LOD"
        s = "PRDD3"

        # 電文生成
        telegram, error_code = self.generate_telegram(il, c, f, s, r)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(telegram)

        # Socket定義
        error_code = self.define_socket()
        if error_code != 0:
            result["result"] = error_code
            return result

        # 電文送受信
        recv, error_code = self.send_telegram(telegram)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(recv)

        # 受信電文の分割設定
        res_structure = {
                         "C01": ["currtime", "currstatus", "currlang", "currstatinfo", "currfolder", "memstatus"]
                         }
        # 受信電文の分割
        divided_data, error_code = self.divide_received(recv, res_structure)

        if error_code != 0:
            result["result"] = error_code
            return result

        result.update(divided_data)
        result["result"] = error_code
        return result

    def load_prdd2(self):
        """
        PRDD2: 生産データ2（時間表示）

        [data]
        <L01>
        cycletime1: サイクルタイム(1) （時間/分/0.1秒）
        cuttingtime1: 切削時間(1) （時間/分/0.1秒）
        othertime1: その他(1) （0.1秒）
        cycletime2: サイクルタイム(2) （時間/分/0.1秒）
        cuttingtime2: 切削時間(2) （時間/分/0.1秒）
        othertime2: その他(2) （0.1秒）
        prg1: プログラム(1)
        prg2: プログラム(2)
        prgfolder1: プログラムフォルダ(1)
        prgfolder2: プログラムフォルダ(2)
        prgstatus1: プログラム再開/途中終了フラグ(1)
        prgstatus2: プログラム再開/途中終了フラグ(2)
        memstatus1: メモリ運転種別(1)
        memstatus2: メモリ運転種別(2)
        count: 運転終了カウンタ
        """

        result = {}

        # 設定
        c = f = s = r = ""
        il = "C"
        c = "LOD"
        s = "PRDD2"

        # 電文生成
        telegram, error_code = self.generate_telegram(il, c, f, s, r)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(telegram)

        # Socket定義
        error_code = self.define_socket()
        if error_code != 0:
            result["result"] = error_code
            return result

        # 電文送受信
        recv, error_code = self.send_telegram(telegram)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(recv)

        # 受信電文の分割設定
        res_structure = {
                         "L01": ["cycletime1", "cuttingtime1", "othertime1", "cycletime2", "cuttingtime2", "othertime2", "prg1", "prg2", "prgfolder1", "prgfolder2", "prgstatus1", "prgstatus2", "memstatus1", "memstatus2", "count"]
                         }
        # 受信電文の分割
        divided_data, error_code = self.divide_received(recv, res_structure)

        if error_code != 0:
            result["result"] = error_code
            return result

        result.update(divided_data)
        result["result"] = error_code
        return result

    def load_montr(self):
        """
        MONTR: 機械モニタ用データ（生産データ4）

        [data]
        <T01>
        actualtime: 運転時間
        energization: 通電時間
        operating: 稼働時間
        """

        result = {}

        # 設定
        c = f = s = r = ""
        il = "C"
        c = "LOD"
        s = "MONTR"

        # 電文生成
        telegram, error_code = self.generate_telegram(il, c, f, s, r)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(telegram)

        # Socket定義
        error_code = self.define_socket()
        if error_code != 0:
            result["result"] = error_code
            return result

        # 電文送受信
        recv, error_code = self.send_telegram(telegram)
        if error_code != 0:
            result["result"] = error_code
            return result
        print(recv)

        # 受信電文の分割設定
        res_structure = {
                         "T01": ["actualtime", "energization", "operating"]
                         }
        # 受信電文の分割
        divided_data, error_code = self.divide_received(recv, res_structure)

        if error_code != 0:
            result["result"] = error_code
            return result

        result.update(divided_data)
        result["result"] = error_code
        return result


if __name__ == "__main__":
    ip_address = ""
    port = ""
    connect = Connect(ip_address, port)

    result = connect.load_prdc2(flag=True)
    # result = connect.load_prd3()
    # result = connect.load_toln(unit="M", num=2)
    # result = connect.read_plcd(device_name="DL", device_num=40)

    # res_structure: レスポンスデータ中で必要なシンボル名称とシンボル別のデータ長を順に作成
    # シンボル部は必要なもののみ記載でOK、各シンボルの項目部は過不足なく順番通りに記載すること
    print(result)
