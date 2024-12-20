# -*- coding : UTF-8 -*-
# ===============================================================================
# Name      : node.py
# Version   : 1.0.0
# Brief     :
# Time-stamp:2024-09-18 10:44
# Copyirght 2024 Tatsuya Sugino
# ===============================================================================
from ryven.node_env import *
import sys
import os
import json
import threading
import time
from queue import Queue


sys.path.append(os.path.dirname(__file__))

script_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(os.path.dirname(script_path))
sys.path.insert(0, parent_dir)

# TCPサーバーのモジュールをインポート
from socket_lib.tcp_connection_class import TCPServerSingleton, load_settings
# VAST用フォーマットモジュールをインポート
from socket_lib.vast_tcp_format import VastInputValue, create_vast_input_value

guis = import_guis(__file__)


class NodeBase(Node):
    version = "v0.1"

    def have_gui(self):
        return hasattr(self, 'gui')


class TCP_Server_Recv_Node(NodeBase):
    title = 'Com_TCP_Server_Recv'
    init_inputs = []
    init_outputs = [
        NodeOutputType(type_="exec"),
        NodeOutputType("message")
    ]
    GUI = guis.TCPServerRecvGui

    def __init__(self, params):
        super().__init__(params)
        self.tcp_server = None
        self.start_tcp_server()

    def start_tcp_server(self):
        if self.tcp_server is None:
            settings = load_settings()
            if settings:
                self.tcp_server = TCPServerSingleton.get_instance(
                    settings["ip_address"],
                    settings["port"],
                    callback=None,
                    disconnect_callback=self.handle_disconnect
                )
                self.tcp_server._signal.connect(lambda v: self.update_event(v))
                self.tcp_server.start()
            else:
                print("Settings not found or failed to load.")

    def update_event(self, inp=-1):
        try:
            message = inp
            if message:
                self.set_output_val(1, Data(message))
                self.exec_output(0)
        except Exception as e:
            print(f"Error receiving message: {e}")


    def handle_disconnect(self):
        print("Client disconnected, restarting server...")
        self.start_tcp_server()

    def stop_tcp_server(self):
        if self.tcp_server:
            self.tcp_server.stop()

    def __del__(self):
        self.stop_tcp_server()


class TCP_Server_Send_Node(NodeBase):
    title = 'Com_TCP_Server_Send'
    init_inputs = [
        NodeInputType(type_="exec"),
        NodeInputType("message")
    ]
    init_outputs = []
    GUI = guis.TCPServerSendGui

    def __init__(self, params):
        super().__init__(params)
        self.tcp_server = None
        self.start_tcp_server()

    def start_tcp_server(self):
        if self.tcp_server is None:
            settings = load_settings()
            if settings:
                self.tcp_server = TCPServerSingleton.get_instance(
                    settings["ip_address"],
                    settings["port"],
                    callback=None,
                    disconnect_callback=self.handle_disconnect
                )
                self.tcp_server.start()
            else:
                print("Settings not found or failed to load.")

    def update_event(self, inp=-1):
        if inp == 0:
            print("SEND EXEC!!")
            try:
                message = self.input(1).payload
                print("@", message)
                if not isinstance(message, str):
                    message = str(message)
                if message:
                    for client_socket in self.tcp_server.server_thread.clients:
                        self.tcp_server.server_thread.send_to_client(client_socket, message)
            except Exception as e:
                print(f"Error sending message: {e}")
            print("SEND FINISH")
            

    def handle_disconnect(self):
        print("Client disconnected, restarting server...")
        self.start_tcp_server()

    def stop_tcp_server(self):
        if self.tcp_server:
            self.tcp_server.stop()

    def __del__(self):
        self.stop_tcp_server()


# export_nodes([
#     TCP_Server_Recv_Node,
#     TCP_Server_Send_Node,
# ])
