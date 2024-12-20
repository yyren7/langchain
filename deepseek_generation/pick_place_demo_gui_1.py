import sys
import threading
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QPushButton, QComboBox, QTextEdit, QMessageBox, QSplitter, QInputDialog, QHBoxLayout, QFileDialog
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QIcon

class StreamRedirector(QObject):
    text_written = pyqtSignal(str)
    def write(self, text):
        self.text_written.emit(str(text))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GUI for llm generation Demo")
        self.resize(1200, 800)

        # 创建QTreeWidget用于组和坐标点管理
        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderLabels(['point_group', 'x', 'y', 'z', 'r'])
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

        # 创建Prompt编辑区域
        self.promptComboBox = QComboBox()
        self.promptComboBox.addItems(['robot_prompt', 'pick_and_place_prompt', 'code_check_prompt', 'task_info_prompt','user_prompt'])
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

        # Prompt输入区域
        prompt_widget = QWidget()
        prompt_layout = QVBoxLayout()
        prompt_layout.addWidget(self.promptComboBox)
        prompt_layout.addWidget(self.promptTextEdit)
        prompt_layout.addWidget(self.submitButton)
        prompt_widget.setLayout(prompt_layout)

        # 将坐标点管理区域和Prompt输入区域添加到顶部的QSplitter
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
        button_bar_layout.addWidget(self.runButton)
        button_bar.setLayout(button_bar_layout)

        # 将输出文本框和按钮栏放在同一水平布局中
        output_layout = QVBoxLayout()
        output_layout.addWidget(self.outputTextEdit)
        output_layout.addWidget(button_bar, alignment=Qt.AlignRight)

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

        # 美化界面
        self.setStyleSheet("background-color: #f0f0f0;")
        self.treeWidget.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc;")
        self.addButton.setStyleSheet("background-color: #4CAF50; color: white;")
        self.removeButton.setStyleSheet("background-color: #f44336; color: white;")
        self.addPointButton.setStyleSheet("background-color: #4CAF50; color: white;")
        self.removePointButton.setStyleSheet("background-color: #f44336; color: white;")
        self.saveButton.setStyleSheet("background-color: #008CBA; color: white;")
        self.loadButton.setStyleSheet("background-color: #008CBA; color: white;")
        self.promptComboBox.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc;")
        self.promptTextEdit.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc;")
        self.submitButton.setStyleSheet("background-color: #4CAF50; color: white;")
        self.runButton.setStyleSheet("background-color: #4CAF50; color: white;")
        self.outputTextEdit.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc;")
        # 重定向print输出到输出框
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

    def remove_group(self, group_item):
        index = self.treeWidget.indexOfTopLevelItem(group_item)
        if index != -1:
            self.treeWidget.takeTopLevelItem(index)
            del self.groups[index]

    def add_coordinate_point_selected(self):
        selected_items = self.treeWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                if item.parent() is None:
                    self.add_coordinate_point(item)
        else:
            QMessageBox.warning(self, "warning", "please select which group to add coordinate point")

    def add_coordinate_point(self, group_item):
        coordinate_item = QTreeWidgetItem(group_item, ['coordinate_point', '0', '0', '0', '0'])
        coordinate_item.setFlags(coordinate_item.flags() | Qt.ItemIsEditable)
        group_index = self.treeWidget.indexOfTopLevelItem(group_item)
        if group_index != -1:
            self.groups[group_index]['coordinates'].append({'x': '0', 'y': '0', 'z': '0', 'r': '0'})

    def remove_coordinate_point_selected(self):
        selected_items = self.treeWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                if item.parent() is not None:
                    self.remove_coordinate_point(item)
        else:
            QMessageBox.warning(self, "warning", "please select which coordinate point to delete")

    def remove_coordinate_point(self, point_item):
        group_item = point_item.parent()
        point_index = group_item.indexOfChild(point_item)
        if point_index != -1:
            group_item.takeChild(point_index)
            group_index = self.treeWidget.indexOfTopLevelItem(group_item)
            if group_index != -1:
                del self.groups[group_index]['coordinates'][point_index]

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
            self.prompts[i] = self.promptTextEdit.toPlainText() if i == self.promptComboBox.currentIndex() else self.prompts[i]
        # 运行程序，使用多线程
        threading.Thread(target=self.execute_program, daemon=True).start()

    def execute_program(self):
        print("executing program...")
        print("current point groups and coordinate points:")
        for group in self.groups:
            print(f"group name: {group['name']}")
            print("coordinate points:")
            for coord in group['coordinates']:
                print(f"x: {coord['x']}, y: {coord['y']}, z: {coord['z']}, r: {coord['r']}")
            print()
        print("Prompts:")
        for i, prompt in enumerate(self.prompts):
            print(f"Prompt {i+1}: {prompt}")

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
                    name=point_item.text(0)
                    x = point_item.text(1)
                    y = point_item.text(2)
                    z = point_item.text(3)
                    r = point_item.text(4)
                    coordinates.append({'name': name,'x': x, 'y': y, 'z': z, 'r': r})
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())