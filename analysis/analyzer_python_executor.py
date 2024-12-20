import os
import json
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.agents import Tool
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_core.runnables.graph import MermaidDrawMethod
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated
import operator
import subprocess
# 配置日志记录
import logging
logging.basicConfig(level=logging.INFO)

# 定义允许的目录和文件大小限制
allowed_directory = os.path.abspath('./vastlib')
max_file_size = 1024 * 1024  # 1MB

# 工具函数：读取文本文件
def read_file_tool(file_path: str) -> str:
    abs_path = os.path.abspath(file_path)
    if not abs_path.startswith(allowed_directory):
        return "Access denied."
    if not abs_path.endswith(('.txt', '.md')):
        return "Only .txt and .md files are allowed."
    if os.path.getsize(abs_path) > max_file_size:
        return "File is too large."
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except UnicodeDecodeError:
        with open(abs_path, 'r', encoding='latin-1') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {e}"

# 工具函数：执行Python脚本
def execute_file_tool(file_path: str) -> str:
    abs_path = os.path.abspath(file_path)
    if not abs_path.startswith(allowed_directory):
        return "Access denied."
    if not abs_path.endswith('.py'):
        return "Only .py files are allowed."
    try:
        result = subprocess.run(['python', abs_path], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return f"Execution failed with code {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        else:
            return result.stdout
    except subprocess.TimeoutExpired:
        return "Execution timed out."
    except Exception as e:
        return f"Error executing file: {e}"

# 工具函数：读取PDF文件
def read_pdf_tool(file_path: str) -> str:
    abs_path = os.path.abspath(file_path)
    if not abs_path.startswith(allowed_directory):
        return "Access denied."
    if not abs_path.endswith('.pdf'):
        return "Only .pdf files are allowed."
    if os.path.getsize(abs_path) > max_file_size:
        return "File is too large."
    try:
        loader = PyPDFLoader(abs_path)
        docs = loader.load()
        return docs[0].page_content if docs else ''
    except Exception as e:
        return f"Error reading PDF file: {e}"

# 工具函数：读取Word文档
def read_word_tool(file_path: str) -> str:
    abs_path = os.path.abspath(file_path)
    if not abs_path.startswith(allowed_directory):
        return "Access denied."
    if not abs_path.endswith('.docx'):
        return "Only .docx files are allowed."
    if os.path.getsize(abs_path) > max_file_size:
        return "File is too large."
    try:
        loader = UnstructuredWordDocumentLoader(abs_path)
        docs = loader.load()
        return docs[0].page_content if docs else ''
    except Exception as e:
        return f"Error reading Word document: {e}"

# 定义工具
read_file = Tool(
    name="read_file",
    func=read_file_tool,
    description="Useful for reading the contents of text files. Provide the file path as input."
)

execute_file = Tool(
    name="execute_python_file",
    func=execute_file_tool,
    description="Useful for executing Python scripts. Provide the file path of the Python script as input."
)

read_pdf = Tool(
    name="read_pdf_file",
    func=read_pdf_tool,
    description="Useful for reading the contents of PDF files. Provide the file path as input."
)

read_word = Tool(
    name="read_word_document",
    func=read_word_tool,
    description="Useful for reading the contents of Word documents. Provide the file path as input."
)

# 定义LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-exp-1206",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=os.environ["GOOGLE_API_KEY"]
)

# 定义AgentState类型
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# 定义Agent类
class Agent:
    def __init__(self, model, tools, system="", checkpointer=None):
        self.system = system
        self.directory_structure = self.traverse_directory('./vastlib')
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile(checkpointer=checkpointer)
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def traverse_directory(self, root_dir):
        directory_structure = {}
        for root, dirs, files in os.walk(root_dir):
            current_level = directory_structure
            for dir_name in root.split('/')[1:]:  # 跳过根目录
                if dir_name not in current_level:
                    current_level[dir_name] = {}
                current_level = current_level[dir_name]
            for file in files:
                file_path = os.path.join(root, file)
                current_level[file] = file_path
        return directory_structure

    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_openai(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling tool: {t}")
            if t['name'] not in self.tools:
                print("...bad tool name...")
                result = "bad tool name, retry"
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}

    def process_directory(self, directory_struct, parent_path=""):
        for key, value in directory_struct.items():
            if isinstance(value, dict):
                self.process_directory(value, os.path.join(parent_path, key))
            else:
                file_path = value
                abs_file_path = os.path.abspath(file_path)
                if os.path.isfile(abs_file_path):
                    # 根据文件类型选择工具
                    tool_name = None
                    if abs_file_path.endswith(('.txt', '.md')):
                        tool_name = "read_file"
                    elif abs_file_path.endswith('.py'):
                        tool_name = "execute_python_file"
                    elif abs_file_path.endswith('.pdf'):
                        tool_name = "read_pdf_file"
                    elif abs_file_path.endswith('.docx'):
                        tool_name = "read_word_document"
                    if tool_name:
                        # 重置消息历史，开始新的一轮对话
                        messages = [HumanMessage(content=f"Analyze file: {abs_file_path}")]
                        thread = {"configurable": {"thread_id": "1"}}
                        for event in self.graph.stream({"messages": messages}, thread):
                            for v in event.values():
                                print("Agent Response:", v['messages'])
                                # 在这里可以添加进一步的分析或处理
                    else:
                        print(f"Unsupported file type: {abs_file_path}")

# 设置系统提示
prompt = """You are an agent with access to the ./vast-vision-nocode-tool-analysis/ directory. You can read text files, execute Python scripts, read PDFs, and Word documents."""

# 创建Agent实例
tools = [read_file, execute_file, read_pdf, read_word]
with SqliteSaver.from_conn_string(":memory:") as memory:
    agent = Agent(llm, tools, system=prompt, checkpointer=memory)
    agent.graph.get_graph().draw_mermaid_png(
        output_file_path="process.png",
        draw_method=MermaidDrawMethod.API
    )
    agent.process_directory(agent.directory_structure)