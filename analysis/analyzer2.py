import os
import json
import chardet
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.agents import Tool
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.runnables.graph import MermaidDrawMethod
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated
import operator
import subprocess
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted
import time

# 配置日志记录
logging.basicConfig(level=logging.INFO)

# 定义允许的目录和文件大小限制
allowed_directory = os.path.abspath('C:/')
max_file_size = 1024 * 1024  # 1MB

# 工具函数：读取文本文件
@retry(
    retry=retry_if_exception_type((PermissionError, OSError, UnicodeDecodeError)),
    wait=wait_exponential(min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        print(f"Detected encoding: {result['encoding']} with confidence {result['confidence']}")
        return result['encoding']

def detect_encoding_with_bom(file_path):
    with open(file_path, 'rb') as f:
        bom = f.read(4)
        if bom.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'  # UTF-8 with BOM
        elif bom.startswith(b'\xff\xfe') or bom.startswith(b'\xfe\xff'):
            return 'utf-16'  # UTF-16 LE or BE
        else:
            return 'utf-8'  # Assume UTF-8 without BOM


def read_file_tool(file_path: str) -> str:
    abs_path = os.path.abspath(file_path)
    if not abs_path.startswith(allowed_directory):
        return "Access denied."
    if not abs_path.endswith(('.txt', '.md')):
        return "Only .txt and .md files are allowed."
    if os.path.getsize(abs_path) > max_file_size:
        return "File is too large."

    encoding = detect_encoding_with_bom(abs_path)

    try:
        with open(abs_path, 'r', encoding=encoding) as f:
            content = f.read()
        return content
    except UnicodeDecodeError as e:
        logging.warning(f"UnicodeDecodeError reading {abs_path}: {e}")
        # 尝试用gbk编码读取
        with open(abs_path, 'r', encoding='gbk') as f:
            content = f.read()
        return content
    except Exception as e:
        logging.error(f"Error reading file {abs_path}: {e}")
        return f"Error reading file: {e}"

# 工具函数：读取Python文件的代码内容
@retry(
    retry=retry_if_exception_type((PermissionError, OSError, UnicodeDecodeError)),
    wait=wait_exponential(min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)
def read_python_file_tool(file_path: str) -> str:
    abs_path = os.path.abspath(file_path)
    if not abs_path.startswith(allowed_directory):
        return "Access denied."
    if not abs_path.endswith('.py'):
        return "Only .py files are allowed."
    if os.path.getsize(abs_path) > max_file_size:
        return "File is too large."

    encoding = detect_encoding_with_bom(abs_path)

    try:
        with open(abs_path, 'r', encoding=encoding) as f:
            content = f.read()
        return content
    except UnicodeDecodeError as e:
        logging.warning(f"UnicodeDecodeError reading {abs_path}: {e}")
        # 尝试用gbk编码读取
        with open(abs_path, 'r', encoding='gbk') as f:
            content = f.read()
        return content
    except Exception as e:
        logging.error(f"Error reading Python file {abs_path}: {e}")
        return f"Error reading Python file: {e}"

# 工具函数：读取PDF文件
@retry(
    retry=retry_if_exception_type((PermissionError, OSError)),
    wait=wait_exponential(min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)
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
        logging.error(f"Error reading PDF file {abs_path}: {e}")
        return f"Error reading PDF file: {e}"

# 工具函数：读取Word文档
@retry(
    retry=retry_if_exception_type((PermissionError, OSError)),
    wait=wait_exponential(min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)
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
        logging.error(f"Error reading Word document {abs_path}: {e}")
        return f"Error reading Word document: {e}"

# 定义工具
read_file = Tool(
    name="read_file",
    func=read_file_tool,
    description="Useful for reading the contents of text files. Provide the file path as input."
)

read_python_file = Tool(
    name="read_python_file",
    func=read_python_file_tool,
    description="Useful for reading the contents of Python files. Provide the file path as input."
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

class Agent:
    def __init__(self, model, tools, system="", checkpointer=None):
        self.system = system
        self.analysis_results = {}
        self.directory_structure = self.traverse_directory('./vast-vision-nocode-tool-analysis')
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

    def get_file_type(self, file_path):
        if file_path.endswith('.py'):
            return 'python'
        elif file_path.endswith(('.txt', '.md')):
            return 'text'
        elif file_path.endswith('.pdf'):
            return 'pdf'
        elif file_path.endswith('.docx'):
            return 'docx'
        else:
            return 'unknown'

    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    @retry(
        retry=retry_if_exception_type(ResourceExhausted),
        wait=wait_exponential(min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def call_openai(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        try:
            message = self.model.invoke(messages)
        except ResourceExhausted as e:
            logging.error(f"ResourceExhausted error: {e}")
            return {'messages': [AIMessage(content="API quota exhausted. Please try again later.")]}
        return {'messages': [message]}

    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        if tool_calls:
            t = tool_calls[0]  # 仅使用第一个工具调用
            print(f"Calling tool: {t}")
            if t['name'] in self.tools:
                result = self.tools[t['name']].invoke(t['args'])
            else:
                result = "bad tool name, retry"
            results = [ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result))]
        else:
            results = []
        print("Back to the model!")
        return {'messages': results}

    def analyze_content(self, content: str, file_type: str) -> str:
        # 根据文件类型设置不同的系统提示
        if file_type == 'python':
            prompt = "You are analyzing Python code. Please summarize the functionality of the code."
        elif file_type == 'text':
            prompt = "You are analyzing a text file. Please summarize the content of the file."
        elif file_type == 'pdf':
            prompt = "You are analyzing a PDF file. Please summarize the content of the file."
        elif file_type == 'docx':
            prompt = "You are analyzing a Word document. Please summarize the content of the document."
        else:
            prompt = "Please summarize the content of the file."

        # 组装消息
        messages = [
            SystemMessage(content=self.system + "\n" + prompt),
            HumanMessage(content=content)
        ]

        # 调用LLM进行分析
        try:
            response = self.model.invoke(messages)
        except Exception as e:
            logging.error(f"Error analyzing content: {e}")
            return f"Error analyzing content: {e}"

        return response.content

    def process_directory(self, directory_struct, parent_path="", current_dict=None):
        if current_dict is None:
            current_dict = self.analysis_results
        for key, value in directory_struct.items():
            current_path = os.path.join(parent_path, key)
            if isinstance(value, dict):
                # 是目录
                current_dict[key] = {}
                self.process_directory(value, current_path, current_dict[key])
            else:
                # 是文件
                file_path = value
                abs_file_path = os.path.abspath(file_path)
                if os.path.isfile(abs_file_path):
                    # 获取文件类型
                    file_type = self.get_file_type(file_path)
                    # 根据文件类型选择工具
                    tool_name = None
                    if abs_file_path.endswith(('.txt', '.md')):
                        tool_name = "read_file"
                    elif abs_file_path.endswith('.py'):
                        tool_name = "read_python_file"
                    elif abs_file_path.endswith('.pdf'):
                        tool_name = "read_pdf_file"
                    elif abs_file_path.endswith('.docx'):
                        tool_name = "read_word_document"
                    if tool_name:
                        # 调用指定的工具
                        tool = self.tools[tool_name]
                        result = tool.invoke({'arg1': abs_file_path})
                        # 分析内容
                        analysis = self.analyze_content(result, file_type)
                        # 存储结果
                        current_dict[key] = {'content': result, 'analysis': analysis}
                    else:
                        current_dict[key] = "Unsupported file type"
                else:
                    current_dict[key] = "File not found"

prompt = """
You are an agent with access to the ./vast-vision-nocode-tool-analysis/ directory.
For each file, choose the most appropriate tool to analyze it.
Only use one tool per file.
"""
# 创建Agent实例
tools = [read_file, read_python_file, read_pdf, read_word]
with SqliteSaver.from_conn_string(":memory:") as memory:
    agent = Agent(llm, tools, system=prompt, checkpointer=memory)
    agent.graph.get_graph().draw_mermaid_png(
        output_file_path="process.png",
        draw_method=MermaidDrawMethod.API
    )
    agent.process_directory(agent.directory_structure)
    # 保存分析结果到JSON文件
    with open('analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(agent.analysis_results, f, ensure_ascii=False, indent=4)