EthernetでPLCと通信する - python.
==============
PLCとPCをイーサネット間で接続し、ソケット通信(TCP)で疎通します。<br>
指定したPLCのデバイス(ビット群)にアクセスし、内容の読み書きを行います。<br>
通信する際は通信先PLCと通信元PCのネットワーク設定をよく確認してください。<br>

## 対応PLC
三菱　　　　：MELSEC-QL /iQ-R /iQ-Fシリーズ (MCプロトコル 1E, 3Eフレーム対応機種)<br>
キーエンス　：KV-3000 /5000 /7000 /8000シリーズ (MCプロトコル対応機種)<br>
パナソニック：FP-0 /7シリーズ (MCプロトコル対応機種)<br>
オムロン　　：CS /CJ /CP /NSJシリーズ (FINS通信対応機種)<br>

## 使い方
##### ~~~~~~ 辞書型 ~~~~~~
##### PLCのネットワーク設定
&nbsp;plc_netwok = {'com0':{'ip':'xxx.xxx.xxx.xxx', 'port':'xxxxx'},}<br>
##### PLCの機種設定
&nbsp;plc_protocol = {'com0':{'manufacture':'mitsubishi', 'series':'ql', 'protocol':'mc_3e', 'transport_layer':'tcp'},}<br>
##### アクセスするPLCのデバイスの設定<br>
&nbsp;device_parameter = {'com0':{'device':'M', 'min':'0', 'max':10},}<br>
##### 実行内容
###### 読出し
&emsp;cmd_data = {'com0':{'cmd':'read', 'data':[], 'option':''},}<br>
###### 書込み(数値)
&emsp;cmd_data = {'com0':{'cmd':'write', 'data':[0,1,2,3,4,5,6,7,8,9,10], 'option':''},}<br>
###### 書込み(文字列)
&emsp;moji = ['A','B','C','D']　⇒　ASCII(10)変換 　⇒　moji_ascii = [97,98,99,100]<br>
&emsp;cmd_data = {'com0':{'cmd':'write', 'data':[len(moji_ascii), moji_ascii[0]+moji_ascii[1]*256+moji_ascii[2]*(256**2)+moji_ascii[3]*(256**3)], 'option':'string'},}<br>
##### 実行
&nbsp;loop = asyncio.get_event_loop()<br>
&nbsp;result = loop.run_until_complete(parallel_connect(plc_network, plc_protocol, device_parameter, cmd_data))<br>
##### 結果
&nbsp;result[n]['response']    ⇒ n台目に設定したPLCからの返答電文<br>
&nbsp;result[n]['exists_data'] ⇒ 返答電文の内容 (書込みの場合は空)<br>
&nbsp;result[n]['send_binary'] ⇒ PLCに送信した電文<br>
&nbsp;result[n]['error_code']  ⇒ エラー判定。0の場合通信成功<br>
