import os
import json
# from dotenv import load_dotenv
import dotenv
dotenv.load_dotenv()

# Manifacture
g_MITSUBISHI = [
    'mitsubishi',
    'mitubisi',
    'melco',
    'melsec'
]
g_KEYENCE = [
    'keyence'
]
g_PANASONIC = [
    'panasonic',
    'matsushita',
    'matusita'
]
g_OMRON = [
    'omron'
]
g_ROCKWELL = [
    'rockwell'
]
g_SIEMENS = [
    'siemens'
]
g_SCHNEIDERELECTRIC = [
    'schneiderelectric',
    'schneider electric',
    'schneider_electric'
]
g_XINJE = [
    'xinje'
]  # ikeike

# Protocol.
g_MCPROTOCOL1E = [
    'mc_1e',
    'mc1e',
    'mcprotocol_1e',
    'mcprotocol_1e_frame'
]
g_MCPROTOCOL2E = [
    'mc_2e',
    'mc2e',
    'mcprotocol_2e',
    'mcprotocol_2e_frame'
]
g_MCPROTOCOL3E = [
    'mc_3e',
    'mc3e',
    'mcprotocol_3e',
    'mcprotocol_3e_frame',
    'slmp'
]
g_MCPROTOCOL4E = [
    'mc_4e',
    'mc4e',
    'mcprotocol_4e',
    'mcprotocol_4e_frame'
]
g_HOSTLINK = [
    'hostlink',
    'upperlink',
    'host_link',
    'upper_link'
]
g_MEWTOCOL = [
    'mewtocol'
]
g_FINS = [
    'fins'
]
g_CIP = [
    'cip'
]
g_MODBUSTCP = [
    'modbustcp',
    'modbus_tcp'
]
g_ETHERNETIP = [
    'ethernetip',
    'ethernet_ip,'
]

g_MODBUSRTU = [
    'modbusrtu',
    'modbus_rtu'
]  # ikeike
g_COMPUTERLINK = [
    'computerlink',
    'computer_link',
    'keisankilink',
    'keisanki_link'
]  # ikeikeike

# PLC Series.
g_SERIES_QR = ['qr', 'q', 'qna']
g_SERIES_IQR = ['iqr', 'iq']
g_SERIES_FX = ['fx']  # ikeikeike

# Ethernet Connection.
g_TCPIP = [
    'tcp',
    'tcpip',
    'tcp_ip',
    't'
]
g_UDPIP = [
    'udp',
    'udpip',
    'udp_ip',
    'u'
]
g_RC232C = [
    'rc232c',
    'rc232',
    '232'
]

# Commands.
g_WRITE_COMMAND = [
    'write',
    'w'
]
g_READ_COMMAND = [
    'read',
    'r'
]

# Command options.
g_STRING_OPTION = [
    'string',
    's'
]
g_TIME_OPTION = [
    'time',
    't'
]


# Identify device.
g_IFY_BIT_DEVICE = [
    'b',
    'bit',
    'bits',
    'byte',
    'bytes'
]
g_IFY_WORD_DEVICE = [
    'w',
    'word',
    'words'
]
g_IFY_D_WORD_DEVICE = [
    'dw',
    'd_word',
    'd_words',
    'double_word',
    'double_words'
]

PLC_TIMEOUT_SECONDS = 0.5  # ikeike0.1

# Error Code.
g_ERROR_CODE = {
    'SUCCESSFLLY_CODE': 0,
    'FUNCTIONAL_ERRORCODE': -1,
    'CONNECTION_ERRORCODE': -10,
    'SKIP_PROCESS_ERRORCODE': -100,
    'HARDWARE_ERRORCODE': -150,
    'PLC_SEQUENCE_ERRORCODE': -200,
}
g_SUCCESSFLLY_CODE = 0
g_FUNCTIONAL_ERRORCODE = -1
g_CONNECTION_ERRORCODE = -10
g_SKIP_PROCESS_ERRORCODE = -100
g_HARDWARE_ERRORCODE = -150
g_PLC_SEQUENCE_ERRORCODE = -200

# MASTER DATA TYPE
try:
    TYPE_ERRORDATA = json.loads(os.environ['TYPE_ERRORDATA'])
    TYPE_WARNINGDATA = json.loads(os.environ['TYPE_WARNINGDATA'])
    TYPE_PRODUCTIONDATA = json.loads(os.environ['TYPE_PRODUCTIONDATA'])
    TYPE_PROGRESSDATA = json.loads(os.environ['TYPE_PROGRESSDATA'])
    TYPE_INSPECTIONDATA = json.loads(os.environ['TYPE_INSPECTIONDATA'])
except:
    TYPE_ERRORDATA = ['error', 'run']
    TYPE_WARNINGDATA = ['warning', 'lift']
    TYPE_PRODUCTIONDATA = [
        'input', 'output', 'plantime',
        'actualtime', 'standardcycle', 'outputtarget']
    TYPE_PROGRESSDATA = ['status', 'currentstatus']
    TYPE_INSPECTIONDATA = ['inspect']

# INTERVAL TIME
ACQUISITION_INTERVAL = {
    'log': 1,
    'error': 1,
    'warning': 1,
    'production': 10,
    'progress': 10,
}

CONNECTION_ERROR_THRESHOLD = 5
NOT_CONNECTION_PARAMETER = 0
BEFORE_DATA_COUNT = 5

# Grobal constants.
g_ENABLE_OPTION = {
    'ENABLE_MANUFACTURE': {
        'mitsubishi': {
            'slmp': {'device': [], 'connection_type': ['tcp', 'udp']},
            'mcprotocol_1e': {'device': [], 'connection_type': ['tcp', 'udp']},
            'computer_link': {'device': [], 'connection_type': ['rc232c']}
        },
        'keyence': {
            'slmp': {'device': [], 'connection_type': ['tcp', 'udp']},
        },
        'panasonic': {
            'slmp': {'device': [], 'connection_type': ['tcp', 'udp']},
        },
        'omron': {
            'fins': {'device': [], 'connection_type': ['tcp', 'udp']},
        },
        'xinje': {
            'modbus_rtu': {'device': [], 'connection_type': ['rc232c']},
        },
    },
    'ENABLE_MASTER_TYPE': TYPE_ERRORDATA + TYPE_PRODUCTIONDATA + TYPE_PROGRESSDATA + TYPE_INSPECTIONDATA
}
