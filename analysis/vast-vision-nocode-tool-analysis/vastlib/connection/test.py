from main import communication
import time

if __name__=="__main__":
    hoge = {
        "network": {
            "ip_address": "192.168.250.10",
            "port": 5000,
        },
        "controller": {
            "type": "PLC",
            "manufacturer": "KEYENCE",
            "series": "KV",
            "protocol": "SLMP/TCP",
            "attributes": {}
        },
        "data":
        [
            {
                "execute": "read",
                "machine_id": 1,
                "group": "",
                "datatype": "",
                "device": "MR",
                "address": "10",
                "data_unit": "integer",
                "trigger": None,
                "item": None,
            },
        ],
    }
    s = time.time()
    for i in range(100):
        res = communication(hoge)
        print(res)
    print(time.time() - s)