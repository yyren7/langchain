# -*- coding : UTF-8 -*-
# ===============================================================================
# Name      : tcpserver_dialog.py
# Version   : 1.0.0
# Brief     : 
# Time-stamp:2024-09-17 14:37
# Copyirght 2024 Tatsuya Sugino
# ===============================================================================
from PySide2.QtWidgets import (QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QApplication)
import json
import os
import sys
import platform

from socket_lib.tcp_connection_class import COM_PATH

# SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "../config/communication.json")
        
class TCPDialog(QDialog):
    
    def __init__(self):
        super().__init__()

        self.setWindowTitle('TCP Settings')

        # レイアウトの設定
        layout = QVBoxLayout(self)

        # IPアドレス入力フィールド
        ip_layout = QHBoxLayout()
        ip_label = QLabel("IP Address:")
        self.ip_input = QLineEdit()
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_input)

        # ポート入力フィールド
        port_layout = QHBoxLayout()
        port_label = QLabel("Port:")
        self.port_input = QLineEdit()
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)

        # タイムアウト入力フィールド
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Timeout:")
        self.timeout_input = QLineEdit()
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_input)

        # ボタンの設定
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("SAVE")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        # レイアウトにウィジェットを追加
        layout.addLayout(ip_layout)
        layout.addLayout(port_layout)
        layout.addLayout(timeout_layout)
        layout.addLayout(button_layout)

        # 設定ファイルの読み込み
        self.load_settings()

    def load_settings(self):
        if os.path.exists(COM_PATH):
            try:
                with open(COM_PATH, "r") as f:
                    settings = json.load(f)
                    self.ip_input.setText(settings.get("ip_address", ""))
                    self.port_input.setText(str(settings.get("port", "")))
                    self.timeout_input.setText(str(settings.get("timeout", "")))
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            settings = {
                "ip_address": self.ip_input.text(),
                "port": int(self.port_input.text()),
                "timeout": float(self.timeout_input.text())
            }
            
            os.makedirs(os.path.dirname(COM_PATH), exist_ok=True)
            with open(COM_PATH, "w") as f:
                json.dump(settings, f, indent=4)
            

            self.accept()
        except ValueError as e:
            print(f"Error converting values: {e}")
            self.reject()
        except Exception as e:
            print(f"Error saving settings: {e}")
            self.reject()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = TCPDialog()
    if dialog.exec_():
        print("Settings saved")
    else:
        print("Settings not saved")
    sys.exit(app.exec_())