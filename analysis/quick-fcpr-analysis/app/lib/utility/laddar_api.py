# -*- coding : UTF-8 -*-
import time
from lib.utility.constant import DM, EM, R, MR, LR, CR, T
# from lib.utility.globals import DM, EM, R, MR, CR, LR, T, X, Y, Z, RX, RY, RZ, VEL, ACC, DEC, DIST, WAIT

class LaddarSeqAPI():   
    def __init__(self, max_EM_relay: int, max_DM_relay: int, max_R_relay: int, max_MR_relay: int, max_LR_relay: int, max_T_relay: int, max_C_relay: int, local_R_setttings: dict, local_MR_setttings: dict, local_T_setttings: dict): 
        ##############################################################
        # クラス変数定義
        ##############################################################  
        # シーケンス作成用
        self.ldlg = 0x0  # ブロック用変数
        self.aax  = 0x0  # 回路の状態保持変数
        self.trlg = 0x0  # ＭＰＳ／ＭＲＤ／ＭＰＰ
        self.iix  = 0x01 # ＭＣ用変数の初期化 
        # プログラム起動の立ち上がり検出用
        self.loop_cnt  = 0        
        # タイマー経過時間計測用
        self.spantime = 0.0
        # 各種リレー上限値
        self.max_CR_relay   = 5500
        self.max_R_relay    = max_R_relay
        self.max_MR_relay   = max_MR_relay
        self.max_EM_relay   = max_EM_relay
        self.max_DM_relay   = max_DM_relay
        self.max_LR_relay   = max_LR_relay
        self.max_T_relay    = max_T_relay
        self.max_C_relay    = max_C_relay
        self.max_PREV_CR_relay = 5500         # 立ち上がり／下がり検出用
        self.max_PREV_MR_relay = max_MR_relay # 立ち上がり／下がり検出用
        self.max_PREV_R_relay = max_R_relay # 立ち上がり／下がり検出用
        self.max_PREV_EM_relay = max_EM_relay # 立ち上がり／下がり検出用
        self.max_PREV_DM_relay = max_DM_relay # 立ち上がり／下がり検出用
        self.max_PREV_T_relay = max_T_relay # 立ち上がり／下がり検出用
        self.max_PREV_LR_relay = max_LR_relay # 立ち上がり／下がり検出用
        # 各種リレー作成
        self.CR_relay   = [0]*self.max_CR_relay
        self.R_relay    = [0]*self.max_R_relay
        self.MR_relay   = [0]*self.max_MR_relay
        self.EM_relay   = [0]*self.max_EM_relay
        self.DM_relay   = [0]*self.max_DM_relay
        self.LR_relay   = [0]*self.max_LR_relay
        self.T_relay    = [0]*self.max_T_relay
        self.C_relay    = [0]*self.max_C_relay
        self.PREV_CR_relay = [0]*self.max_PREV_CR_relay
        self.PREV_R_relay = [0]*self.max_PREV_R_relay
        self.PREV_MR_relay = [0]*self.max_PREV_MR_relay
        self.PREV_EM_relay = [0]*self.max_PREV_EM_relay
        self.PREV_DM_relay = [0]*self.max_PREV_DM_relay
        self.PREV_T_relay = [0]*self.max_PREV_T_relay
        self.PREV_LR_relay = [0]*self.max_PREV_LR_relay
        self.local_R  = self.defineLocalRelay(local_R_setttings, max_R_relay, 'R')
        self.local_MR = self.defineLocalRelay(local_MR_setttings, max_MR_relay, 'MR')
        self.local_T  = self.defineLocalRelay(local_T_setttings, max_T_relay, 'T')
        # 各種リレー初期値
        self.CR_relay[20] = 4 #常時ON
        # 時間計測
        self.T_counter = [0]*max_T_relay*2000
        self.lasttime = 0
        # 立上がり／立下りデバイス確認用配列
        # self.UTRG =[]
        # self.DTRG =[]
        

    def __del__(self):
        ##############################################################
        # デコンストラクタ
        ##############################################################  
        print('laddar_api.py is closed.')

    # ローカルリレーを定義
    def defineLocalRelay(self, local_Relay_settings, max_relay, device_name):
        output_dict = {}
        ref_relay_no = max_relay * 100 # MR1000 → MR1000.00
        total_offset = 0

        for index, (key, value) in enumerate(local_Relay_settings.items()):
            # 'type'と'length'の値を取得
            value_type = value['type']
            length = value['length']
            
            # 新しい辞書のキーと値を生成
            for offset in range(length):
                new_key = f"{key}[{offset}]"
                word_no = int((ref_relay_no - 1) / 100) - int((offset + total_offset) / 16)
                bit_no = (15 - (ref_relay_no % 100) - ((offset + total_offset) % 16))
                output_dict[new_key] = {
                    'name': device_name,
                    'addr': word_no * 100 + bit_no
                }
            total_offset = total_offset + length
        return output_dict

    def getRealyLimit(self, relay_name: str) -> int:
        #デバイス上限確認
        if(relay_name == 'CR')     : upper_limit = self.max_CR_relay
        elif(relay_name == 'R')    : upper_limit = self.max_R_relay
        elif(relay_name == 'MR')   : upper_limit = self.max_MR_relay
        elif(relay_name == 'EM')   : upper_limit = self.max_EM_relay
        elif(relay_name == 'DM')   : upper_limit = self.max_DM_relay
        elif(relay_name == 'LR')   : upper_limit = self.max_LR_relay
        elif(relay_name == 'T')    : upper_limit = self.max_T_relay
        elif(relay_name == 'C')    : upper_limit = self.max_C_relay
        elif(relay_name == 'PREV_CR') : upper_limit = self.max_PREV_CR_relay
        elif(relay_name == 'PREV_R') : upper_limit = self.max_PREV_R_relay
        elif(relay_name == 'PREV_MR') : upper_limit = self.max_PREV_MR_relay
        elif(relay_name == 'PREV_LR') : upper_limit = self.max_PREV_LR_relay
        elif(relay_name == 'PREV_T') : upper_limit = self.max_PREV_T_relay
        else                     :raise ValueError('device name is wrong.')   
        
        return upper_limit

    def getRelay(self, relay_name: str, relay_no: int = 0, offset: int = 0):
        #ワード、ビット値計算
        word_no: int = int(relay_no / 100) + int(offset / 15)
        bit_no: int  = (relay_no % 100) + (offset % 15)

        # デバイス割付数確認
        upper_limit = self.getRealyLimit(relay_name)

        #デバイスON/OFF確認
        if((word_no <= upper_limit) and (bit_no <= 15)):
            if(relay_name == 'CR')     : flag = True if((self.CR_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'R')    : flag = True if((self.R_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'MR')   : flag = True if((self.MR_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'EM')   : flag = True if((self.EM_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'DM')   : flag = True if((self.DM_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'LR')   : flag = True if((self.LR_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'T')    : flag = True if((self.T_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'C')    : flag = True if((self.C_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'PREV_CR') : flag = True if((self.PREV_CR_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'PREV_R') : flag = True if((self.PREV_R_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'PREV_MR') : flag = True if((self.PREV_MR_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'PREV_LR') : flag = True if((self.PREV_LR_relay[word_no] & (0x01 << (bit_no))) > 0) else False
            elif(relay_name == 'PREV_T') : flag = True if((self.PREV_T_relay[word_no] & (0x01 << (bit_no))) > 0) else False

            return flag
        else:
            raise ValueError('device No. is over limit.')

    def setRelay(self, relay_name: str, relay_no: int = 0, offset: int = 0):
        #ワード、ビット値計算
        word_no: int = int(relay_no / 100) + int(offset / 15)
        bit_no: int  = (relay_no % 100) + (offset % 15)

        # デバイス割付数確認
        upper_limit = self.getRealyLimit(relay_name)

        #デバイスON処理
        if((word_no <= upper_limit) and (bit_no <= 15)):
            if(relay_name == 'R')      : self.R_relay[word_no]    = self.R_relay[word_no]    | (0x01 << (bit_no))
            elif(relay_name == 'CR')   : self.CR_relay[word_no]   = self.CR_relay[word_no]   | (0x01 << (bit_no))
            elif(relay_name == 'MR')   : self.MR_relay[word_no]   = self.MR_relay[word_no]   | (0x01 << (bit_no))
            elif(relay_name == 'EM')   : self.EM_relay[word_no]   = self.EM_relay[word_no]   | (0x01 << (bit_no))
            elif(relay_name == 'DM')   : self.DM_relay[word_no]   = self.DM_relay[word_no]   | (0x01 << (bit_no))
            elif(relay_name == 'LR')   : self.LR_relay[word_no]   = self.LR_relay[word_no]   | (0x01 << (bit_no))
            elif(relay_name == 'T')    : self.T_relay[word_no]    = self.T_relay[word_no]    | (0x01 << (bit_no))
            elif(relay_name == 'C')    : self.C_relay[word_no]    = self.C_relay[word_no]    | (0x01 << (bit_no))
            elif(relay_name == 'PREV_CR') : self.PREV_CR_relay[word_no] = self.PREV_CR_relay[word_no] | (0x01 << (bit_no))
            elif(relay_name == 'PREV_R') : self.PREV_R_relay[word_no] = self.PREV_R_relay[word_no] | (0x01 << (bit_no))
            elif(relay_name == 'PREV_MR') : self.PREV_MR_relay[word_no] = self.PREV_MR_relay[word_no] | (0x01 << (bit_no))
            elif(relay_name == 'PREV_LR') : self.PREV_LR_relay[word_no] = self.PREV_LR_relay[word_no] | (0x01 << (bit_no))
            elif(relay_name == 'PREV_T') : self.PREV_T_relay[word_no] = self.PREV_T_relay[word_no] | (0x01 << (bit_no))
        else:
            raise ValueError('device No. is over limit.')

    def resetRelay(self, relay_name: str, relay_no: int = 0, offset: int = 0):
        #ワード、ビット値計算
        word_no: int = int(relay_no / 100) + int(offset / 15)
        bit_no: int  = (relay_no % 100) + (offset % 15)

        # デバイス割付数確認
        upper_limit = self.getRealyLimit(relay_name)

        #デバイスOFF処理
        if((word_no <= upper_limit) and (bit_no <= 15)):
            if(relay_name == 'R')      : self.R_relay[word_no]    = self.R_relay[word_no]    & ~(0x01 << (bit_no))
            elif(relay_name == 'CR')   : self.CR_relay[word_no]   = self.CR_relay[word_no]   & ~(0x01 << (bit_no))
            elif(relay_name == 'MR')   : self.MR_relay[word_no]   = self.MR_relay[word_no]   & ~(0x01 << (bit_no))
            elif(relay_name == 'EM')   : self.EM_relay[word_no]   = self.EM_relay[word_no]   & ~(0x01 << (bit_no))
            elif(relay_name == 'DM')   : self.DM_relay[word_no]   = self.DM_relay[word_no]   & ~(0x01 << (bit_no))
            elif(relay_name == 'LR')   : self.LR_relay[word_no]   = self.LR_relay[word_no]   & ~(0x01 << (bit_no))
            elif(relay_name == 'T')    : self.T_relay[word_no]    = self.T_relay[word_no]    & ~(0x01 << (bit_no))
            elif(relay_name == 'C')    : self.C_relay[word_no]    = self.C_relay[word_no]    & ~(0x01 << (bit_no))
            elif(relay_name == 'PREV_CR') : self.PREV_CR_relay[word_no] = self.PREV_CR_relay[word_no] & ~(0x01 << (bit_no))
            elif(relay_name == 'PREV_R') : self.PREV_R_relay[word_no] = self.PREV_R_relay[word_no] & ~(0x01 << (bit_no))
            elif(relay_name == 'PREV_MR') : self.PREV_MR_relay[word_no] = self.PREV_MR_relay[word_no] & ~(0x01 << (bit_no))
            elif(relay_name == 'PREV_LR') : self.PREV_LR_relay[word_no] = self.PREV_LR_relay[word_no] & ~(0x01 << (bit_no))
            elif(relay_name == 'PREV_T') : self.PREV_T_relay[word_no] = self.PREV_T_relay[word_no] & ~(0x01 << (bit_no))
        else:
            raise ValueError('device No. is over limit.')

    def LD(self, relay_name: any, relay_no: int = 0, offset: int = 0):
        self.ldlg = (self.ldlg << 1) | (self.aax << 1) 
        self.aax = 0x0 
        relay_name_str = str(relay_name)
        if(relay_name_str == 'True'):
            flag = True
        elif(relay_name_str == 'False'):
            flag = False    
        else:
            flag = self.getRelay(relay_name_str, relay_no, offset)
        if (flag): self.aax |= 0x01

    def LDEQ(self, src1: int, src2 :int):
        self.ldlg = (self.ldlg << 1) | (self.aax << 1) 
        self.aax = 0x0 
        flag = True if(src1 == src2) else False
        if (flag): self.aax |= 0x01

    def LDGEQ(self, src1: int, src2 :int):
        self.ldlg = (self.ldlg << 1) | (self.aax << 1) 
        self.aax = 0x0 
        flag = True if(src1 >= src2) else False
        if (flag): self.aax |= 0x01
        
    def LDG(self, src1: int, src2 :int):
        self.ldlg = (self.ldlg << 1) | (self.aax << 1) 
        self.aax = 0x0 
        flag = True if(src1 > src2) else False
        if (flag): self.aax |= 0x01

    def LDLEQ(self, src1: int, src2 :int):
        self.ldlg = (self.ldlg << 1) | (self.aax << 1) 
        self.aax = 0x0 
        flag = True if(src1 <= src2) else False
        if (flag): self.aax |= 0x01

    def LDL(self, src1: int, src2 :int):
        self.ldlg = (self.ldlg << 1) | (self.aax << 1) 
        self.aax = 0x0 
        flag = True if(src1 < src2) else False
        if (flag): self.aax |= 0x01

    def ANDLDEQ(self, src1: int, src2 :int):
        flag = True if(src1 == src2) else False
        if (not(flag)):  self.aax &= ~0x01

    def ANDLDGEQ(self, src1: int, src2 :int):
        flag = True if(src1 >= src2) else False
        if (not(flag)):  self.aax &= ~0x01

    def ANDLDG(self, src1: int, src2 :int):
        flag = True if(src1 > src2) else False
        if (not(flag)):  self.aax &= ~0x01

    def ANDLDLEQ(self, src1: int, src2 :int):
        flag = True if(src1 <= src2) else False
        if (not(flag)):  self.aax &= ~0x01

    def ANDLDL(self, src1: int, src2 :int):
        flag = True if(src1 < src2) else False
        if (not(flag)):  self.aax &= ~0x01

    def MPS(self):
        self.trlg = (self.trlg << 1) | (self.aax) 

    def MRD(self):
        self.aax |= (self.trlg & 0x01)

    def LDB(self, relay_name: str, relay_no: int = 0, offset: int = 0):     
        self.ldlg = (self.ldlg << 1) | (self.aax << 1)
        self.aax = 0x0
        relay_name_str = str(relay_name)
        if(relay_name_str == 'True'):
            flag = True
        elif(relay_name_str == 'False'):
            flag = False    
        else:
            flag = self.getRelay(relay_name_str, relay_no, offset)
        if (not(flag)):  self.aax |= 0x01 

    def AND(self, relay_name: str, relay_no: int = 0, offset: int = 0):
        relay_name_str = str(relay_name)
        if(relay_name_str == 'True'):
            flag = True
        elif(relay_name_str == 'False'):
            flag = False    
        else:
            flag = self.getRelay(relay_name_str, relay_no, offset)
        if (not(flag)):  self.aax &= ~0x01

    def ANB(self, relay_name: str, relay_no: int = 0, offset: int = 0):
        relay_name_str = str(relay_name)
        if(relay_name_str == 'True'):
            flag = True
        elif(relay_name_str == 'False'):
            flag = False    
        else:
            flag = self.getRelay(relay_name_str, relay_no, offset)
        if (flag):  self.aax &= ~0x01 

    def OUT(self, relay_name: str, relay_no: int = 0, offset: int = 0):
        if (self.aax & self.iix):self.setRelay(relay_name, relay_no) 
        else: self.resetRelay(relay_name, relay_no, offset)    

    # def OUT(self, relay_name: str, relay_no: int = 0, offset: int = 0):
    #     if (self.aax & self.iix):
    #         # ローカルデバイスなら
    #         if (type(relay_name) == list):
    #             relay_name[relay_no] = True
    #         # グローバルデバイスなら
    #         else:
    #             self.setRelay(relay_name, relay_no) 
    #     else:
    #         # ローカルデバイスなら
    #         if (type(relay_name) == list):
    #             relay_name[relay_no] = False
    #         # グローバルデバイスなら
    #         else:
    #             self.resetRelay(relay_name, relay_no, offset)    
        
    def OUTVAR(self) -> bool:
        if (self.aax & self.iix): output_var = True
        else: output_var = False  
        return output_var

    def MPP(self):
        self.aax = 0 
        self.aax |= (self.trlg & 0x1) 
        self.trlg >>= 0x1 

    def OR(self, relay_name: str, relay_no: int = 0, offset: int = 0):
        relay_name_str = str(relay_name)
        if(relay_name_str == 'True'):
            flag = True
        elif(relay_name_str == 'False'):
            flag = False    
        else:
            flag = self.getRelay(relay_name_str, relay_no, offset)
        if (flag): self.aax |= 0x01

    def ORL(self):
        self.ldlg >>= 1; 
        self.aax |= (self.ldlg & 0x01); 

    def ORP(self, relay_name: str, relay_no: int = 0, offset: int = 0):
        if((self.getRelay(relay_name, relay_no)) and not(self.getRelay('PREV_'+relay_name, relay_no))):
            self.aax |= 0x01 

    def ANL(self):
        self.ldlg >>= 1
        self.aax &= (self.ldlg & 0x01)
        
    def ANPB(self, relay_name: str, relay_no: int = 0, offset: int = 0):
        relay_name_str = str(relay_name)
        if(relay_name_str == 'True'):
            flag = True
        elif(relay_name_str == 'False'):
            flag = False    
        else:
            flag = self.getRelay(relay_name_str, relay_no, offset)
        if (flag):
            if (self.aax & self.iix): 
                if ((self.getRelay(relay_name, relay_no)) and not(self.getRelay('PREV_'+relay_name, relay_no))): 
                    self.aax &= ~0x01 
                else: 
                    self.aax |= 0x01
        else: 
            pass
        
    def LDPB(self, relay_name: str, relay_no: int = 0, offset: int = 0):
        self.ldlg = (self.ldlg << 1) | (self.aax << 1) 
        self.aax = 0x0 
        relay_name_str = str(relay_name)
        if(relay_name_str == 'True'):
            flag = True
        elif(relay_name_str == 'False'):
            flag = False    
        else:
            flag = self.getRelay(relay_name_str, relay_no, offset)
        if (not(flag)):
            if ((self.getRelay(relay_name, relay_no)) and not(self.getRelay('PREV_'+relay_name, relay_no))):
                self.aax |= 0x01
                # print("1")
            else: 
                # print("2")
                self.aax = 0x01
        else:      
            if ((self.getRelay(relay_name, relay_no)) and not(self.getRelay('PREV_'+relay_name, relay_no))):
                # print("3")
                self.aax &= ~0x01          
            else: 
                # print("4")
                self.aax |= 0x01
     
    def LDP(self, relay_name: any, relay_no: int = 0, offset: int = 0):
        self.ldlg = (self.ldlg << 1) | (self.aax << 1) 
        self.aax = 0x0 
        if((self.getRelay(relay_name, relay_no)) and not(self.getRelay('PREV_'+relay_name, relay_no))):
            self.aax |= 0x01 
                       
    def LDF(self, relay_name: str, relay_no: int = 0, offset: int = 0):
        self.ldlg = (self.ldlg << 1) | (self.aax << 1) 
        self.aax = 0x0 
        if(not(self.getRelay(relay_name, relay_no)) and (self.getRelay('PREV_'+relay_name, relay_no))):
            self.aax |= 0x01 

    def TMS(self, relay_no :int, wait_msec: int): # wait_time:×1msec
        if (self.aax & self.iix):  
            if (not(self.getRelay(T, relay_no))):
                if(((self.T_counter[relay_no] + (self.spantime) ) >=  wait_msec * 1)): # 設定値×1msec
                    self.T_counter[relay_no] = wait_msec * 1
                    self.setRelay(T, relay_no)
                    # print('++++++++++++++++++++++++ stopped +++++++++++++++++++++++')
                else: 
                    self.T_counter[relay_no] += self.spantime
                    # print('++++++++++++++++++++++ counting +++++++++++++++++++++++++')            
        else:
            self.T_counter[relay_no] = 0
            self.resetRelay(T, relay_no)
            # print('++++++++++++++++++++++ reset +++++++++++++++++++++++++')

    def FB_setRobotParam(self, x, y, z, rx, ry, rz, vel, acc, dec, dist, wait, off_x, off_y, off_z, off_rx, off_ry, off_rz, override):
        if (self.aax & self.iix):
            x = x + off_x
            y = y + off_y
            z = z + off_z
            rx = rx + off_rx
            ry = ry + off_ry
            rz = rz + off_rz
            vel = vel * (override / 100)

        return x, y, z, rx, ry, rz, vel, acc, dec, dist, wait
        
    def FB_runRobot(self, instance,  x, y, z, rx, ry, rz, vel, acc, dec, dist, wait):
        if (self.aax & self.iix):
            instance.moveAbsoluteLine(x, y, z, rx, ry, rz, vel, acc, dec)

    def updateTime(self):
        self.nowtime = time.perf_counter() * 1000 # sec -> msec変換
        # ループの最初は経過時間0を格納
        if(self.lasttime != 0.0):self.spantime = self.nowtime - self.lasttime
        else:                    self.spantime = 0.0
        self.lasttime = self.nowtime
        # 立下り／立下り確認のため、状態更新
        self.PREV_CR_relay = self.CR_relay.copy()
        self.PREV_R_relay = self.R_relay.copy()
        self.PREV_MR_relay = self.MR_relay.copy()
        self.PREV_EM_relay = self.EM_relay.copy()
        self.PREV_DM_relay = self.DM_relay.copy()
        self.PREV_LR_relay = self.LR_relay.copy()
        self.PREV_T_relay = self.T_relay.copy()
        # 運転開始時1ｽｷｬﾝON
        if (self.loop_cnt == 0): 
            self.setRelay(CR, 2008)
            self.loop_cnt = 1
        else: 
            self.resetRelay(CR, 2008)