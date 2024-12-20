# Manufacturer
MANUFACTURER_MITSUBISHI = ["mitsubishi", "mitubisi", "melsec"]
MANUFACTURER_KEYENCE = ["keyence"]
MANUFACTURER_PANASONIC = ["panasonic", "matsushita", "matusita"]
MANUFACTURER_OMRON = ["omron"]
# MANUFACTURER_YASKAWA = ["yaskawa", "yasukawa"]
# MANUFACTURER_YOKOGAWA = ["yokogawa", "yokokawa"]
# MANUFACTURER_JTEKT = ["jtekt"]
# MANUFACTURER_HITACHI = ["hitachi", "hitati"]
# MANUFACTURER_TOSHIBA = ["toshiba", "tosiba"]
# MANUFACTURER_SIEMENS = ["siemens"]
# MANUFACTURER_SCHNEIDER = [
#     "schneider", "schneiderelectric", "schneider_electric", "schneider electric"]
# MANUFACTURER_ROCKWELL = ["rockwell"]
MANUFACTURER_FANUC = ["fanuc"]
MANUFACTURER_BROTHER = ["brother"]
# MANUFACTURER_SHIBAURA = ["shibaura"]
# MANUFACTURER_SUMITOMOHEAVY = [
#     "sumitomoheavy", "sumitomo_heavy", "sumitomo heavy"]

# Series
SERIES_MITSUBISHI_IQR = ["iqr"]
SERIES_MITSUBISHI_QL = ["ql", "q61p"]
# SERIES_MITSUBISHI_QNA = ["qna", "qa"]
# SERIES_MITSUBISHI_A = ["a"]
# SERIES_KEYENCE_KV8XXX = ["8000"]
SERIES_KEYENCE_KV7XXX = ["7000", "7300", "7500"]
SERIES_KEYENCE_KV5XXX = ["5000", "5500", "3000"]
SERIES_KEYENCE_KVNANO = ["nano"]
SERIES_PANASONIC_FP0 = ["fp0"]
SERIES_PANASONIC_FP7 = ["fp7"]

# Protocol
PROTOCOL_SLMP = ["slmp", "mcprotocol3e",
                 "mcprotocol_3e", "mcprotocol 3e", "mcprotocol", "3e"]
PROTOCOL_MC4E = ["mcprotocol4e", "4e", "mcprotocol_4e", "mcprotocol 4e"]
PROTOCOL_MC1E = ["mcprotocol1e", "1e", "mcprotocol_1e", "mcprotocol 1e"]
PROTOCOL_FINS = ["fins"]
# PROTOCOL_CIP = ["cip"]
# PROTOCOL_HOSTLINK = ["hostlink", "host link"]
PROTOCOL_MODBUSTCP = ["modbus_tcp", "modbustcp", "modbus tcp"]
# PROTOCOL_FOCAS2 = ["focas2"]
# PROTOCOL_MTLINKI = ["mtlinki", "mt_linki", "mt linki"]
# PROTOCOL_OPCUA = ["opcua"]
# PROTOCOL_MTCONNECT = ["mtconnect", "mt_connect", "mt connect"]

# Device Identify
BIT_DEVICE = ["bit", "b"]
WORD_DEVICE = ["word", "w"]
DOUBLE_DEVICE = ["double", "double word", "double_word", "dw"]

# Endian
ENDIAN_LITTLE = ["little", "l"]
ENDIAN_BIG = ["big", "b"]

# Transport identify
TRANSPORT_TCP = ["tcp", "tcpip", "t"]
TRANSPORT_UDP = ["udp", "udpip", "u"]
TRANSPORT_RS232C = ["rs232c", "232c"]
TRANSPORT_RS485 = ["rs485", "485"]
TRANSPORT_RS422 = ["rs422", "422"]
TRANSPORT_ETHERCAT = ["ethercat"]

# Timeout
TRANSPORT_TIMEOUT = 0.1
# Retry count
RETRY_COUNT = 3

# Command
READ_COMMAND = ["read", "r"]
WRITE_COMMAND = ["write", "w"]

# Options
STRING_DATA = ["string", "str", "s"]
TIME_DATA = ["time"]
ASCII_DATA_CODE = ["ascii"]
