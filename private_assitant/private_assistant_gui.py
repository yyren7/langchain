import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QScrollArea
from PySide6.QtCore import Qt, QTimer, QObject, Signal
from PySide6.QtGui import QTextCursor, QKeyEvent
from private_assistant_v1 import DialogueAgent, should_continue_tool, llm  # 导入 llm

class StreamRedirector(QObject):
    """重定向控制台输出到 QTextEdit"""
    text_written = Signal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass


class ChatBubbleWidget(QTextEdit):
    """自定义气泡控件"""
    def __init__(self, text, is_user, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFrameShape(QTextEdit.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet(self.get_bubble_style(is_user))
        self.setText(text)
        self.adjustSize()

    def get_bubble_style(self, is_user):
        """根据用户或代理设置气泡样式"""
        if is_user:
            return """
                QTextEdit {
                    background-color: #dcf8c6;
                    border-radius: 10px;
                    padding: 8px;
                    margin: 5px;
                    color: black;  /* 字体颜色为黑色 */
                    align-self: flex-end;
                }
            """
        else:
            return """
                QTextEdit {
                    background-color: #ffffff;
                    border-radius: 10px;
                    padding: 8px;
                    margin: 5px;
                    color: black;  /* 字体颜色为黑色 */
                    align-self: flex-start;
                }
            """


class InputTextEdit(QTextEdit):
    """自定义输入框，支持回车键发送消息"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def keyPressEvent(self, event: QKeyEvent):
        """重写 keyPressEvent 方法，监听回车键"""
        if event.key() == Qt.Key_Return and not event.modifiers():
            # 按下回车键（无修饰键，如 Shift）
            self.parent.process_input()
        else:
            # 其他按键正常处理
            super().keyPressEvent(event)


class PrivateAssistantGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Private Assistant")
        self.setGeometry(100, 100, 600, 400)

        # 初始化对话代理
        self.agent = DialogueAgent(llm)

        # 创建主窗口的布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        # 创建输入区域
        self.input_text = InputTextEdit(self)  # 使用自定义输入框
        self.input_text.setPlaceholderText("Type your message here...")
        self.input_text.setMaximumHeight(100)
        self.layout.addWidget(self.input_text)

        # 重定向控制台输出
        self.console_output = QTextEdit()  # 创建一个 QTextEdit 用于控制台输出
        self.console_output.setReadOnly(True)
        self.scroll_layout.addWidget(self.console_output)

        # 创建 StreamRedirector 并连接信号
        self.redirector = StreamRedirector()
        self.redirector.text_written.connect(self.console_output.append)
        sys.stdout = self.redirector

        # 显示欢迎信息
        self.add_bubble("Welcome to the Private Assistant! Type 'exit', 'quit', 'bye', 'no', 'stop', or 'end' to end the conversation.\n", False)

    def add_bubble(self, text, is_user):
        """添加气泡到对话区域"""
        bubble = ChatBubbleWidget(text, is_user)
        self.scroll_layout.addWidget(bubble, alignment=Qt.AlignRight if is_user else Qt.AlignLeft)
        QTimer.singleShot(0, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """滚动到对话区域底部"""
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def process_input(self):
        # 获取用户输入
        user_input = self.input_text.toPlainText().strip()

        # 如果输入为空，则跳过处理
        if not user_input:
            return

        # 清空输入框
        self.input_text.clear()

        # 显示用户输入气泡
        self.add_bubble(user_input, True)

        # 使用 should_continue Tool 判断是否退出对话
        if not should_continue_tool.func(user_input):
            self.add_bubble("Goodbye!", False)
            self.agent.save_dialogue_to_markdown()  # 保存对话记录
            QTimer.singleShot(2000, self.close)  # 2秒后关闭窗口
            return

        # 创建代理回复气泡（空内容，稍后填充）
        agent_bubble = ChatBubbleWidget("", False)
        self.scroll_layout.addWidget(agent_bubble, alignment=Qt.AlignLeft)
        QTimer.singleShot(0, self.scroll_to_bottom)

        # 与代理交互（流式输出）
        def update_bubble(chunk):
            """更新代理气泡内容"""
            agent_bubble.setText(agent_bubble.toPlainText() + chunk)
            QTimer.singleShot(0, self.scroll_to_bottom)

        def finalize_bubble():
            """完成气泡显示"""
            agent_bubble.setText(agent_bubble.toPlainText().strip())

        # 调用 interact_stream 方法
        self.agent.interact_stream(user_input, update_bubble, finalize_bubble)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PrivateAssistantGUI()
    window.show()
    sys.exit(app.exec())