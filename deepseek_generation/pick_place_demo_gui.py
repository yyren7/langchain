import sys
import threading
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QPushButton, QComboBox, QTextEdit, QMessageBox, QSplitter, QInputDialog, QHBoxLayout, QFileDialog, QDialog, QDialogButtonBox
from PyQt5.QtCore import QObject, pyqtSignal, Qt

class StreamRedirector(QObject):
    text_written = pyqtSignal(str)
    def write(self, text):
        self.text_written.emit(str(text))

class GroupTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Group Type")
        layout = QVBoxLayout()
        self.typeComboBox = QComboBox()
        self.typeComboBox.addItems(['coordinate_group', 'ip_group', 'io_group'])
        layout.addWidget(self.typeComboBox)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

    def get_group_type(self):
        return self.typeComboBox.currentText()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GUI for llm generation Demo")
        self.resize(1200, 800)

        # 创建QTreeWidget用于组和成员管理
        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderLabels(['Group Type', 'Group Name'])
        self.treeWidget.setColumnCount(2)

        # 创建按钮
        self.addButton = QPushButton("Add Group")
        self.addButton.clicked.connect(self.add_group)
        self.removeButton = QPushButton("Delete Group")
        self.removeButton.clicked.connect(self.remove_group_selected)
        self.addMemberButton = QPushButton("Add Member")
        self.addMemberButton.clicked.connect(self.add_member_selected)
        self.removeMemberButton = QPushButton("Delete Member")
        self.removeMemberButton.clicked.connect(self.remove_member_selected)
        self.saveButton = QPushButton("Save Data")
        self.saveButton.clicked.connect(self.save_data)
        self.loadButton = QPushButton("Load Data")
        self.loadButton.clicked.connect(self.load_data)

        # 创建Prompt编辑区域
        self.promptComboBox = QComboBox()
        self.promptComboBox.addItems(['robot_prompt', 'pick_and_place_prompt', 'code_check_prompt', 'task_info_prompt','user_prompt'])
        self.promptComboBox.currentIndexChanged.connect(self.show_current_prompt)

        self.promptTextEdit = QTextEdit()
        self.promptTextEdit.setPlaceholderText("Edit prompt here")

        self.submitButton = QPushButton("Submit")
        self.submitButton.clicked.connect(self.submit_prompt)

        # 创建运行按钮和输出文本框
        self.runButton = QPushButton("Execute")
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
        button_layout.addWidget(self.addMemberButton)
        button_layout.addWidget(self.removeMemberButton)
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

        # 将输出文本框和按钮栏放在同一垂直布局中
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
        self.addMemberButton.setStyleSheet("background-color: #4CAF50; color: white;")
        self.removeMemberButton.setStyleSheet("background-color: #f44336; color: white;")
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
        dialog = GroupTypeDialog()
        if dialog.exec_() == QDialog.Accepted:
            group_type = dialog.get_group_type()
            group_name, ok = QInputDialog.getText(self, "Add Group", "Please input group name:")
            if ok and group_name:
                group_item = QTreeWidgetItem([group_type, group_name])
                group_item.setFlags(group_item.flags() | Qt.ItemIsEditable)
                self.treeWidget.addTopLevelItem(group_item)
                self.groups.append({'type': group_type, 'name': group_name, 'members': []})

    def remove_group_selected(self):
        selected_items = self.treeWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                if item.parent() is None:
                    self.remove_group(item)
        else:
            QMessageBox.warning(self, "Warning", "Please select which group to delete")

    def remove_group(self, group_item):
        index = self.treeWidget.indexOfTopLevelItem(group_item)
        if index != -1:
            self.treeWidget.takeTopLevelItem(index)
            del self.groups[index]

    def add_member_selected(self):
        selected_items = self.treeWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                if item.parent() is None:
                    self.add_member(item)
        else:
            QMessageBox.warning(self, "Warning", "Please select which group to add member")

    def add_member(self, group_item):
        group_type = group_item.text(0)
        if group_type == 'coordinate_group':
            x, ok = QInputDialog.getText(self, "Add Member", "Please input X:")
            if ok:
                y, ok = QInputDialog.getText(self, "Add Member", "Please input Y:")
                if ok:
                    z, ok = QInputDialog.getText(self, "Add Member", "Please input Z:")
                    if ok:
                        r, ok = QInputDialog.getText(self, "Add Member", "Please input R:")
                        if ok:
                            member_item = QTreeWidgetItem([x, y, z, r])
                            member_item.setFlags(member_item.flags() | Qt.ItemIsEditable)
                            group_item.addChild(member_item)
                            self.groups[self.treeWidget.indexOfTopLevelItem(group_item)]['members'].append({'x': x, 'y': y, 'z': z, 'r': r})
        elif group_type == 'ip_group':
            ip, ok = QInputDialog.getText(self, "Add Member", "Please input IP:")
            if ok:
                port, ok = QInputDialog.getText(self, "Add Member", "Please input Port:")
                if ok:
                    member_item = QTreeWidgetItem([ip, port])
                    member_item.setFlags(member_item.flags() | Qt.ItemIsEditable)
                    group_item.addChild(member_item)
                    self.groups[self.treeWidget.indexOfTopLevelItem(group_item)]['members'].append({'ip': ip, 'port': port})
        elif group_type == 'io_group':
            device, ok = QInputDialog.getText(self, "Add Member", "Please input Device Name:")
            if ok:
                interface, ok = QInputDialog.getText(self, "Add Member", "Please input Interface Number:")
                if ok:
                    member_item = QTreeWidgetItem([device, interface])
                    member_item.setFlags(member_item.flags() | Qt.ItemIsEditable)
                    group_item.addChild(member_item)
                    self.groups[self.treeWidget.indexOfTopLevelItem(group_item)]['members'].append({'device': device, 'interface': interface})

    def remove_member_selected(self):
        selected_items = self.treeWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                if item.parent() is not None:
                    self.remove_member(item)
        else:
            QMessageBox.warning(self, "Warning", "Please select which member to delete")

    def remove_member(self, member_item):
        group_item = member_item.parent()
        member_index = group_item.indexOfChild(member_item)
        if member_index != -1:
            group_item.takeChild(member_index)
            group_index = self.treeWidget.indexOfTopLevelItem(group_item)
            if group_index != -1:
                del self.groups[group_index]['members'][member_index]

    def show_current_prompt(self, index):
        prompt = self.prompts[index]
        self.promptTextEdit.setPlainText(prompt)

    def submit_prompt(self):
        index = self.promptComboBox.currentIndex()
        prompt = self.promptTextEdit.toPlainText()
        self.prompts[index] = prompt
        QMessageBox.information(self, "Message", "Prompt submitted")

    def run_code(self):
        # 更新groups列表中的成员数据
        self.groups = []
        for group_index in range(self.treeWidget.topLevelItemCount()):
            group_item = self.treeWidget.topLevelItem(group_index)
            group_type = group_item.text(0)
            group_name = group_item.text(1)
            members = []
            for member_index in range(group_item.childCount()):
                member_item = group_item.child(member_index)
                if group_type == 'coordinate_group':
                    x = member_item.text(0)
                    y = member_item.text(1)
                    z = member_item.text(2)
                    r = member_item.text(3)
                    members.append({'x': x, 'y': y, 'z': z, 'r': r})
                elif group_type == 'ip_group':
                    ip = member_item.text(0)
                    port = member_item.text(1)
                    members.append({'ip': ip, 'port': port})
                elif group_type == 'io_group':
                    device = member_item.text(0)
                    interface = member_item.text(1)
                    members.append({'device': device, 'interface': interface})
            self.groups.append({'type': group_type, 'name': group_name, 'members': members})
        # 收集Prompts
        for i in range(5):
            self.prompts[i] = self.promptTextEdit.toPlainText() if i == self.promptComboBox.currentIndex() else self.prompts[i]
        # 运行程序，使用多线程
        threading.Thread(target=self.execute_program, daemon=True).start()

    def execute_program(self):
        print("Executing program...")
        print("Current groups and members:")
        for group in self.groups:
            print(f"Group Type: {group['type']}, Group Name: {group['name']}")
            print("Members:")
            for member in group['members']:
                print(f"  {member}")
            print()
        print("Prompts:")
        for i, prompt in enumerate(self.prompts):
            print(f"Prompt {i+1}: {prompt}")

    def save_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "JSON Files (*.json)")
        if file_path:
            data = {
                'groups': self.groups,
                'prompts': self.prompts
            }
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "Message", "Data saved successfully")
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Error occurred when saving data: {str(e)}")

    def load_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Data", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                # 清空现有的数据
                self.treeWidget.clear()
                self.groups = data.get('groups', [])
                self.prompts = data.get('prompts', [''] * 5)
                # 重新加载组和成员
                for group_data in self.groups:
                    group_type = group_data.get('type', 'unknown')
                    group_name = group_data.get('name', 'unknown')
                    group_item = QTreeWidgetItem([group_type, group_name])
                    group_item.setFlags(group_item.flags() | Qt.ItemIsEditable)
                    self.treeWidget.addTopLevelItem(group_item)
                    members = group_data.get('members', [])
                    for member in members:
                        if group_type == 'coordinate_group':
                            x = member.get('x', '0')
                            y = member.get('y', '0')
                            z = member.get('z', '0')
                            r = member.get('r', '0')
                            member_item = QTreeWidgetItem([x, y, z, r])
                            member_item.setFlags(member_item.flags() | Qt.ItemIsEditable)
                            group_item.addChild(member_item)
                        elif group_type == 'ip_group':
                            ip = member.get('ip', '0.0.0.0')
                            port = member.get('port', '0')
                            member_item = QTreeWidgetItem([ip, port])
                            member_item.setFlags(member_item.flags() | Qt.ItemIsEditable)
                            group_item.addChild(member_item)
                        elif group_type == 'io_group':
                            device = member.get('device', 'unknown')
                            interface = member.get('interface', 'unknown')
                            member_item = QTreeWidgetItem([device, interface])
                            member_item.setFlags(member_item.flags() | Qt.ItemIsEditable)
                            group_item.addChild(member_item)
                # 更新当前Prompt的文本
                current_index = self.promptComboBox.currentIndex()
                if 0 <= current_index < len(self.prompts):
                    self.promptTextEdit.setPlainText(self.prompts[current_index])
                QMessageBox.information(self, "Message", "Data loaded successfully")
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Error occurred when loading data: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())