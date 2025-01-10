# gui_app.py
# -*- coding: utf-8 -*-
import sys
import logging
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QObject, Signal
from PySide6.QtGui import QTextCursor, QKeyEvent, QTextOption, QResizeEvent

# ========== 核心：从文件2 (private_assistant_v2.py) 中导入 ==========
from private_assistant_v2 import (
    DialogueAgent,
    deepseek_llm,
    should_continue_tool
)


logging.basicConfig(level=logging.INFO)


class StreamRedirector(QObject):
    """重定向控制台输出到 QTextEdit"""
    text_written = Signal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass


class ChatBubbleWidget(QTextEdit):
    """自定义气泡控件：高度自适应 + 拦截滚轮"""
    def __init__(self, text, is_user, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFrameShape(QTextEdit.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setSizeAdjustPolicy(QTextEdit.AdjustToContents)
        self.setWordWrapMode(QTextOption.WordWrap)

        self.setStyleSheet(self.get_bubble_style(is_user))
        self.setText(text)

        # 限制气泡宽度
        self.setFixedWidth(400)
        self.update_height()

    def get_bubble_style(self, is_user):
        if is_user:
            return """
                QTextEdit {
                    background-color: #dcf8c6;
                    border-radius: 10px;
                    padding: 8px;
                    margin: 5px;
                    color: black;
                }
            """
        else:
            return """
                QTextEdit {
                    background-color: #ffffff;
                    border-radius: 10px;
                    padding: 8px;
                    margin: 5px;
                    color: black;
                }
            """

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.update_height()

    def update_height(self):
        doc = self.document()
        doc.setTextWidth(self.viewport().width())
        height = doc.size().height() + self.frameWidth() * 2
        self.setFixedHeight(int(height))

    def wheelEvent(self, event):
        event.ignore()


class InputTextEdit(QTextEdit):
    """输入框：支持回车发送"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return and not event.modifiers():
            self.parent_window.process_input()
        else:
            super().keyPressEvent(event)


class PrivateAssistantGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Private Assistant (GUI Chunk Streaming)")
        self.setGeometry(100, 100, 600, 400)
        self.setContentsMargins(0,0,0,0)

        # ========== 核心：使用从文件2导入的 DialogueAgent ==========
        self.agent = DialogueAgent(deepseek_llm)

        # 主窗口布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0,0,0,0)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0,0,0,0)

        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        # 输入框
        self.input_text = InputTextEdit(self)
        self.input_text.setPlaceholderText("Type your message here...")
        self.input_text.setMaximumHeight(100)
        self.layout.addWidget(self.input_text)

        # 控制台输出
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFrameShape(QTextEdit.NoFrame)
        self.scroll_layout.addWidget(self.console_output)

        # 重定向 stdout
        self.redirector = StreamRedirector()
        self.redirector.text_written.connect(self.console_output.append)
        sys.stdout = self.redirector

        # 显示欢迎消息
        self.add_bubble(
            """中文向导
欢迎使用本工具！在这里，您可以即时提出问题并得到回答。本工具会调用本次会话的全部上文进行连续对话，确保对话的连贯性。如果您想退出程序，只需输入类似'我想退出'之类的指令即可。请注意，本次对话的历史记录将会被保存在`result`文件夹中，方便您随时查阅。

English Instructions
Welcome to our tool! Here, you can ask questions and receive immediate responses. This tool utilizes the entire context of the current session to ensure a continuous and coherent conversation. To exit the program, simply input a command such as 'I want to exit'. Please note that the history of this conversation will be saved in the `result` folder for your future reference.

日本語の案内
このツールへようこそ！ここでは、質問を即座に投げかけて回答を得ることができます。このツールは、現在のセッションのすべての前文を利用して、連続的で一貫性のある会話を実現します。プログラムを終了したい場合は、'終了したい'などのコマンドを入力してください。なお、この会話の履歴は`result`フォルダに保存され、いつでも参照できるようになります。\n""",
            is_user=False
        )

    def add_bubble(self, text, is_user):
        bubble = ChatBubbleWidget(text, is_user)
        alignment = Qt.AlignRight if is_user else Qt.AlignLeft
        self.scroll_layout.addWidget(bubble, alignment=alignment)
        QTimer.singleShot(0, self.scroll_to_bottom)
        return bubble

    def scroll_to_bottom(self):
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def process_input(self):
        user_input = self.input_text.toPlainText().strip()
        if not user_input:
            return

        # 清空输入框 + 显示用户气泡
        self.input_text.clear()
        self.add_bubble(user_input, True)

        # 判断是否退出
        if not should_continue_tool.func(user_input):
            self.add_bubble("Goodbye!", False)
            # 保存对话到 .md
            self.agent.save_dialogue_to_markdown()
            QTimer.singleShot(1500, self.close)
            return

        # 先放一个空白气泡，用于实时输出模型的回答
        agent_bubble = self.add_bubble("", is_user=False)

        # 逐块获取后台的响应
        def update_bubble(chunk_text):
            # 将文本插入到气泡的末尾
            agent_bubble.moveCursor(QTextCursor.End)
            agent_bubble.insertPlainText(chunk_text)
            agent_bubble.update_height()
            QTimer.singleShot(0, self.scroll_to_bottom)
            # 让界面及时刷新
            QApplication.processEvents()

        # 收尾处理
        def finalize_bubble():
            text = agent_bubble.toPlainText().strip()
            agent_bubble.setText(text)
            agent_bubble.update_height()
            QTimer.singleShot(0, self.scroll_to_bottom)

        # 调用后台的生成器
        generator = self.agent.interact_stream_generator(user_input)

        # 同步方式：循环获取 chunk
        for chunk in generator:
            if chunk is None:
                # 说明输出结束
                finalize_bubble()
                break
            else:
                # 正常文本块
                update_bubble(chunk)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PrivateAssistantGUI()
    window.show()
    sys.exit(app.exec())
