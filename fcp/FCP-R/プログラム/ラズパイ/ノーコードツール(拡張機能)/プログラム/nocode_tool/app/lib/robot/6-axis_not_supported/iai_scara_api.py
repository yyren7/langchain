# -*- coding : UTF-8 -*-

from socket import *
import select
import time

# To read .ini file
import configparser


class RobotApi():   
    def __init__(self, dst_ip_address, dst_port):      
        print("IAI init.")
        print(dst_ip_address)
        print(dst_port)
    
    def getRobotStatus(self):
        print("Got IAI status.")