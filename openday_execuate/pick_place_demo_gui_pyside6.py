import re
import sys
import threading
import json
import time
from functools import reduce

from PySide6.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QPushButton, \
    QComboBox, QTextEdit, QMessageBox, QSplitter, QInputDialog, QHBoxLayout, QFileDialog
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QIcon, QFont
import subprocess


class StreamRedirector(QObject):
    text_written = Signal(str)

    def write(self, text):
        self.text_written.emit(str(text))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        font = QFont()
        font.setPointSize(15)

        app.setFont(font)
        self.setWindowTitle("GUI for llm generation Demo")
        self.resize(1600, 900)

        # 创建 QTreeWidget
        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderLabels(['groups', 'x', 'y', 'z', 'r'])
        self.treeWidget.setColumnCount(5)

        # 创建按钮
        self.addButton = QPushButton("add_group")
        self.addButton.clicked.connect(self.add_group)
        self.removeButton = QPushButton("delete_group")
        self.removeButton.clicked.connect(self.remove_group_selected)
        self.addPointButton = QPushButton("add_coordinate_point")
        self.addPointButton.clicked.connect(self.add_coordinate_point_selected)
        self.removePointButton = QPushButton("delete_coordinate_point")
        self.removePointButton.clicked.connect(self.remove_coordinate_point_selected)
        self.saveButton = QPushButton("save_data")
        self.saveButton.clicked.connect(self.save_data)
        self.loadButton = QPushButton("load_data")
        self.loadButton.clicked.connect(self.load_data)
        self.updatePointButton = QPushButton("update_point")
        self.updatePointButton.clicked.connect(self.update_points)

        # 创建 Prompt 编辑区域
        self.promptComboBox = QComboBox()
        self.promptComboBox.addItems(
            ['robot_prompt', 'pick_and_place_prompt', 'code_check_prompt', 'task_info_prompt', 'user_prompt'])
        self.promptComboBox.currentIndexChanged.connect(self.show_current_prompt)

        self.promptTextEdit = QTextEdit()
        self.promptTextEdit.setPlaceholderText("edit prompt here")

        self.submitButton = QPushButton("submit")
        self.submitButton.clicked.connect(self.submit_prompt)

        # 创建运行按钮和输出文本框
        self.runButton = QPushButton("execute")
        self.runButton.clicked.connect(self.run_code)

        self.outputTextEdit = QTextEdit()
        self.outputTextEdit.setReadOnly(True)

        # 坐标点管理区域
        coordinate_widget = QWidget()
        coordinate_layout = QVBoxLayout()
        coordinate_layout.addWidget(self.treeWidget)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.addButton)
        button_layout.addWidget(self.removeButton)
        button_layout.addWidget(self.addPointButton)
        button_layout.addWidget(self.removePointButton)
        coordinate_layout.addLayout(button_layout)

        coordinate_widget.setLayout(coordinate_layout)

        # Prompt 输入区域
        prompt_widget = QWidget()
        prompt_layout = QVBoxLayout()
        prompt_layout.addWidget(self.promptComboBox)
        prompt_layout.addWidget(self.promptTextEdit)
        prompt_layout.addWidget(self.submitButton)
        prompt_widget.setLayout(prompt_layout)

        # 将坐标点管理区域和 Prompt 输入区域添加到顶部的 QSplitter
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(coordinate_widget)
        top_splitter.addWidget(prompt_widget)
        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 2)

        # 创建按钮栏
        button_bar = QWidget()
        button_bar_layout = QHBoxLayout()
        button_bar_layout.addWidget(self.saveButton)
        button_bar_layout.addWidget(self.loadButton)
        button_bar_layout.addWidget(self.updatePointButton)
        button_bar_layout.addWidget(self.runButton)
        button_bar.setLayout(button_bar_layout)

        # 将输出文本框和按钮栏放在同一垂直布局中
        output_layout = QVBoxLayout()
        output_layout.addWidget(self.outputTextEdit)
        output_layout.addWidget(button_bar)

        output_widget = QWidget()
        output_widget.setLayout(output_layout)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(top_splitter)
        main_layout.addWidget(output_widget)

        # 创建一个中心 widget 并设置主布局
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 初始化数据
        self.prompts = [''] * 5
        self.groups = []

        # 界面美化
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QTreeWidget { background-color: #ffffff; border: 1px solid #cccccc; }
            QPushButton { padding: 5px; font-weight: bold; }
            QPushButton#addButton, QPushButton#addPointButton, QPushButton#updatePointButton, QPushButton#runButton, QPushButton#submitButton {
                background-color: #4CAF50; color: white;
            }
            QPushButton#removeButton, QPushButton#removePointButton {
                background-color: #f44336; color: white;
            }
            QPushButton#saveButton, QPushButton#loadButton {
                background-color: #008CBA; color: white;
            }
            QComboBox { background-color: #ffffff; border: 1px solid #cccccc; }
            QTextEdit { background-color: #ffffff; border: 1px solid #cccccc; }
        """)

        # 重定向 print 输出到输出框
        self.redirector = StreamRedirector()
        self.redirector.text_written.connect(self.outputTextEdit.append)
        sys.stdout = self.redirector
    def add_group(self):
        group_name, ok = QInputDialog.getText(self, "add group", "pleas input group name:")
        if ok and group_name:
            group_item = QTreeWidgetItem([group_name, '', '', '', ''])
            group_item.setFlags(group_item.flags() | Qt.ItemIsEditable)
            self.treeWidget.addTopLevelItem(group_item)
            self.groups.append({'name': group_name, 'coordinates': []})

    def remove_group_selected(self):
        selected_items = self.treeWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                if item.parent() is None:
                    self.remove_group(item)
        else:
            QMessageBox.warning(self, "warning", "please select which group to delete")

    def add_coordinate_point_selected(self):
        selected_items = self.treeWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                if item.parent() is None:
                    self.add_coordinate_point(item)
        else:
            QMessageBox.warning(self, "warning", "please select which group to add coordinate point")

    def remove_coordinate_point_selected(self):
        selected_items = self.treeWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                if item.parent() is not None:
                    self.remove_coordinate_point(item)
        else:
            QMessageBox.warning(self, "warning", "please select which coordinate point to delete")

    def update_points(self):
        # 启动新线程来运行指定程序
        threading.Thread(target=self.run_update_program, daemon=True).start()

    def remove_group(self, item):
        reply = QMessageBox.question(self, 'confirm', f'confirm to delete {item.text(0)} ?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 从树里删除项
            self.treeWidget.invisibleRootItem().removeChild(item)
            # 从 groups 列表中删除对应的组
            for group in self.groups:
                if group['name'] == item.text(0):
                    self.groups.remove(group)
                    break

    def remove_coordinate_point(self, item):
        reply = QMessageBox.question(self, 'confirm', f'confirm to delete {item.text(0)} ?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            parent = item.parent()
            if parent:
                # 从树里删除子项
                parent.takeChild(parent.indexOfChild(item))
                # 从组的 coordinates 列表中删除对应的坐标点
                group_data = parent.data(0, Qt.UserRole)
                if group_data and 'coordinates' in group_data:
                    for coord in group_data['coordinates']:
                        if coord['name'] == item.text(0):
                            group_data['coordinates'].remove(coord)
                            break


    def run_update_program(self):
        # 重定向stdout到GUI的输出文本框
        sys.stdout = self.redirector

        # 运行指定的程序，并捕获输出
        try:
            # 替换为你的指定程序的命令
            position_prompt = self.prompts[1]
            position_prompt = position_prompt.translate(str.maketrans('', '', '\n\r'))
            print("executing program...")
            command1 = ['python', 'deepseek_input_parameter_format_transfer.py', position_prompt]
            process = subprocess.Popen(command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

            # 实时读取并输出stdout
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
        finally:
            # 恢复stdout
            sys.stdout = sys.__stdout__

        # 从指定的JSON文件读取数据并更新point group
        self.load_data_from_json('prompts_demo.json')

    def load_data_from_json(self, file_path):
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                # 清空现有的数据
                self.treeWidget.clear()
                self.groups = []
                # 重新加载组和坐标点
                for group_data in data.get('groups', []):
                    group_name = group_data.get('name', 'unknown')
                    group_item = QTreeWidgetItem([group_name, '', '', '', ''])
                    group_item.setFlags(group_item.flags() | Qt.ItemIsEditable)
                    self.treeWidget.addTopLevelItem(group_item)
                    coordinates = group_data.get('coordinates', [])
                    for coord in coordinates:
                        name = coord.get('name', 'coordinate_point')
                        x = coord.get('x', '0')
                        y = coord.get('y', '0')
                        z = coord.get('z', '0')
                        r = coord.get('r', '0')
                        coordinate_item = QTreeWidgetItem(group_item, [name, x, y, z, r])
                        coordinate_item.setFlags(coordinate_item.flags() | Qt.ItemIsEditable)
                    self.groups.append({'name': group_name, 'coordinates': coordinates})
                QMessageBox.information(self, "message", "point groups updated successfully")
            except Exception as e:
                QMessageBox.warning(self, "warning", f"error occurred when loading data: {str(e)}")

    def save_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "save data", "", "JSON Files (*.json)")
        if file_path:
            groups = []
            for group_index in range(self.treeWidget.topLevelItemCount()):
                group_item = self.treeWidget.topLevelItem(group_index)
                group_name = group_item.text(0)
                coordinates = []
                for point_index in range(group_item.childCount()):
                    point_item = group_item.child(point_index)
                    name = point_item.text(0)
                    x = point_item.text(1)
                    y = point_item.text(2)
                    z = point_item.text(3)
                    r = point_item.text(4)
                    coordinates.append({'name': name, 'x': x, 'y': y, 'z': z, 'r': r})
                groups.append({'name': group_name, 'coordinates': coordinates})
            data = {
                'groups': groups,
                'prompts': self.prompts
            }
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, ensure_ascii=True, indent=4)
                QMessageBox.information(self, "message", "data saved successfully")
            except Exception as e:
                QMessageBox.warning(self, "warning", f"error occurred when saving data: {str(e)}")

    def load_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "load data", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                # 清空现有的数据
                self.treeWidget.clear()
                self.groups = []
                self.prompts = data.get('prompts', [''] * 5)
                # 重新加载组和坐标点
                for group_data in data.get('groups', []):
                    group_name = group_data.get('name', 'unknown')
                    group_item = QTreeWidgetItem([group_name, '', '', '', ''])
                    group_item.setFlags(group_item.flags() | Qt.ItemIsEditable)
                    self.treeWidget.addTopLevelItem(group_item)
                    coordinates = group_data.get('coordinates', [])
                    for coord in coordinates:
                        name = coord.get('name', '0')
                        x = coord.get('x', '0')
                        y = coord.get('y', '0')
                        z = coord.get('z', '0')
                        r = coord.get('r', '0')
                        coordinate_item = QTreeWidgetItem(group_item, [name, x, y, z, r])
                        coordinate_item.setFlags(coordinate_item.flags() | Qt.ItemIsEditable)
                    self.groups.append({'name': group_name, 'coordinates': coordinates})
                # 更新当前Prompt的文本
                current_index = self.promptComboBox.currentIndex()
                if 0 <= current_index < len(self.prompts):
                    self.promptTextEdit.setPlainText(self.prompts[current_index])
                QMessageBox.information(self, "message", "data loaded successfully")
            except Exception as e:
                QMessageBox.warning(self, "warning", f"error occurred when loading data: {str(e)}")

    def show_current_prompt(self, index):
        prompt = self.prompts[index]
        self.promptTextEdit.setPlainText(prompt)

    def submit_prompt(self):
        index = self.promptComboBox.currentIndex()
        prompt = self.promptTextEdit.toPlainText()
        self.prompts[index] = prompt
        QMessageBox.information(self, "message", "Prompt submitted")

    def run_code(self):
        # 更新groups列表中的坐标点数据
        self.groups = []
        for group_index in range(self.treeWidget.topLevelItemCount()):
            group_item = self.treeWidget.topLevelItem(group_index)
            group_name = group_item.text(0)
            coordinates = []
            for point_index in range(group_item.childCount()):
                point_item = group_item.child(point_index)
                x = point_item.text(1)
                y = point_item.text(2)
                z = point_item.text(3)
                r = point_item.text(4)
                coordinates.append({'x': x, 'y': y, 'z': z, 'r': r})
            self.groups.append({'name': group_name, 'coordinates': coordinates})
        # 收集Prompts
        for i in range(5):
            self.prompts[i] = self.promptTextEdit.toPlainText() if i == self.promptComboBox.currentIndex() else \
                self.prompts[i]
        # 运行程序，使用多线程
        threading.Thread(target=self.execute_program, daemon=True).start()

    def point_reading_program(self):
        # 获取 `groups`

        match = '"' + str(self.groups) + '"'
        print(match)
        return match

    def execute_program(self):

        sys.stdout = self.redirector

        # 运行指定的程序，并捕获输出
        try:
            # 替换为你的指定程序的命令
            robot_prompt = str(self.prompts[0])  # 使用第一个命令行参数覆盖默认坐标
            position_information = "please load the points from './generated_points.json', their format is: "+str(json.load(open('./generated_points.json', 'rb')))
            code_check_prompt = str(self.prompts[2])  # 使用第一个命令行参数覆盖默认坐标
            task_prompt = str(self.prompts[3])  # 使用第一个命令行参数覆盖默认坐标
            user_prompt = str(self.prompts[4])  # 使用第一个命令行参数覆盖默认坐标
            print("executing program...")
            command = ['python', '-u', 'deepseek_generation.py', robot_prompt, position_information, user_prompt,
                       task_prompt, code_check_prompt]
            result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            while True:
                output = result.stdout.readline()
                if output == '' and result.poll() is not None:
                    break
                if output:
                    print(output.strip())
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
        finally:
            # 恢复stdout
            sys.stdout = sys.__stdout__


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
