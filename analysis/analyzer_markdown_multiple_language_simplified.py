import os
import json
from langchain.tools.base import StructuredTool
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
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted
import time
from pydantic import BaseModel

# 配置日志记录
logging.basicConfig(level=logging.INFO)

# 定义允许的目录和文件大小限制
allowed_directory = os.path.abspath('C:/')
max_file_size = 1024 * 1024  # 1MB

# 工具函数：检测文件编码
def detect_encoding_with_bom(file_path):
    with open(file_path, 'rb') as f:
        bom = f.read(4)
        if bom.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'  # UTF-8 with BOM
        elif bom.startswith(b'\xff\xfe') or bom.startswith(b'\xfe\xff'):
            return 'utf-16'  # UTF-16 LE or BE
        else:
            return 'utf-8'  # Assume UTF-8 without BOM

# 工具函数：读取文本文件
@retry(
    retry=retry_if_exception_type((PermissionError, OSError, UnicodeDecodeError)),
    wait=wait_exponential(min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)
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
        with open(abs_path, 'r', encoding='gbk') as f:
            content = f.read()
        return content
    except Exception as e:
        logging.error(f"Error reading file {abs_path}: {e}")
        return f"Error reading file: {e}"

# 工具函数：读取Python文件
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

# 定义 Pydantic 模型
class TranslateTextArgs(BaseModel):
    text: str
    target_language: str

# 工具函数：翻译文本
def translate_text(text: str, target_language: str) -> str:
    if target_language not in ['ja', 'zh']:
        return "Unsupported target language."
    prompt = f"Translate the following text to {target_language}:\n\n{text}"
    messages = [
        SystemMessage(content="You are a professional translator."),
        HumanMessage(content=prompt)
    ]
    try:
        # 使用 stream 方法进行流式输出
        analysis_result = ""  # 用于累积完整的分析结果
        for chunk in llm.stream(messages):  # 逐块处理响应
            part = chunk.content  # 假设每个 chunk 包含部分响应内容
            print(part, end='', flush=True)  # 实时输出到控制台
            analysis_result += part  # 累积完整的分析结果
    except ResourceExhausted as e:
        logging.error(f"ResourceExhausted error: {e}")
        analysis_result = "API quota exhausted. Please try again later."
    except Exception as e:
        logging.error(f"Translation error: {e}")
        analysis_result = "Translation failed."
    return analysis_result  # 返回累积的完整分析结果

# 定义翻译工具
translate_tool = StructuredTool(
    name="translate_text",
    func=translate_text,
    description="Useful for translating text to the target language. Provide the text and target language ('ja' for Japanese, 'zh' for Chinese).",
    args_schema=TranslateTextArgs
)

# 定义 LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=os.environ["GOOGLE_API_KEY"]
)

# 定义 AgentState 类型
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# 定义 Agent 类
class Agent:
    def __init__(self, model, tools, system="", checkpointer=None):
        self.system = system
        self.analysis_results = {}
        self.directory_structure = self.traverse_directory('../dobot_robot/result')
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
            t = tool_calls[0]
            logging.info(f"Calling tool: {t}")
            if t['name'] in self.tools:
                result = self.tools[t['name']].invoke(t['args'])
            else:
                result = "bad tool name, retry"
            results = [ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result))]
        else:
            results = []
        logging.info("Back to the model!")
        return {'messages': results}

    def analyze_content(self, content):
        messages = [
            SystemMessage(
                content="Please provide a concise analysis of the following content in no more than 100 words, focusing on key insights without including any source code."),
            HumanMessage(content=content)
        ]
        try:
            # 使用 stream 方法进行流式输出
            analysis_result = ""  # 用于累积完整的分析结果
            for chunk in self.model.stream(messages):  # 逐块处理响应
                part = chunk.content  # 假设每个 chunk 包含部分响应内容
                print(part, end='', flush=True)  # 实时输出到控制台
                analysis_result += part  # 累积完整的分析结果
        except ResourceExhausted as e:
            logging.error(f"ResourceExhausted error: {e}")
            analysis_result = "API quota exhausted. Please try again later."
        except Exception as e:
            logging.error(f"Translation error: {e}")
            analysis_result = "Translation failed."
        return analysis_result  # 返回累积的完整分析结果

    def process_directory(self, directory_struct, parent_path="", current_dict=None):
        if current_dict is None:
            current_dict = self.analysis_results
        for key, value in directory_struct.items():
            current_path = os.path.join(parent_path, key)
            if isinstance(value, dict):
                current_dict[key] = {}
                self.process_directory(value, current_path, current_dict[key])
            else:
                file_path = value
                abs_file_path = os.path.abspath(file_path)
                logging.info(f"Processing file: {file_path}")
                if os.path.isfile(abs_file_path):
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
                        tool = self.tools[tool_name]
                        tool_result = tool.invoke({'arg1': abs_file_path})
                        analysis_result = self.analyze_content(tool_result)
                        current_dict[key] = {
                            'content': tool_result,
                            'analysis': analysis_result
                        }
                    else:
                        current_dict[key] = "Unsupported file type"
                else:
                    current_dict[key] = "File not found"

    # 新增方法：翻译并保存Markdown文件
    def translate_and_save(self, file_path, target_language, output_file):
        # 读取Markdown文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 调用翻译工具进行翻译
        translated_content = self.tools['translate_text'].invoke({
            'text': content,
            'target_language': target_language
        })

        # 保存翻译后的Markdown文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(translated_content)

# 新增函数：递归生成Markdown文本
def dict_to_markdown(data, level=0):
    markdown = ""
    for key, value in data.items():
        if isinstance(value, dict):
            if level == 0:
                markdown += f"\n# {key}\n"
            elif level == 1:
                markdown += f"\n## {key}\n"
            else:
                markdown += f"\n{'#' * (level + 1)} {key}\n"
            markdown += dict_to_markdown(value, level + 1)
        else:
            if 'analysis' in value:
                markdown += f"\n### {key}\n"
                markdown += f"**Analysis:**\n\n{value['analysis']}\n"
            else:
                markdown += f"\n### {key}\n\n{value}\n"
    return markdown

# 设置系统提示
prompt = """
For each file, choose the most appropriate tool to analyze it.
Only use one tool per file.
"""
# 创建 Agent 实例
tools = [read_file, read_python_file, read_pdf, read_word, translate_tool]
with SqliteSaver.from_conn_string(":memory:") as memory:
    agent = Agent(llm, tools, system=prompt, checkpointer=memory)
    agent.graph.get_graph().draw_mermaid_png(
        output_file_path="process.png",
        draw_method=MermaidDrawMethod.API
    )
    agent.process_directory(agent.directory_structure)
    # 生成Markdown文本
    markdown_content = dict_to_markdown(agent.analysis_results)
    # 保存分析结果到Markdown文件
    with open('analysis_insights_en.md', 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    # 翻译并保存为日语和中文版
    agent.translate_and_save('analysis_insights_en.md', 'ja', 'analysis_insights_ja.md')
    agent.translate_and_save('analysis_insights_en.md', 'zh', 'analysis_insights_zh.md')