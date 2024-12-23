import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)
import json

def load_document(file_path):
    if file_path.endswith('.pdf'):
        return PyPDFLoader(file_path)
    elif file_path.endswith('.txt'):
        return TextLoader(file_path)
    elif file_path.endswith('.docx'):
        return UnstructuredWordDocumentLoader(file_path)
    else:
        return None

def traverse_directory(root_dir):
    directory_structure = {}
    for root, dirs, files in os.walk(root_dir):
        relative_root = os.path.relpath(root, root_dir)
        current_level = directory_structure
        if relative_root != '.':
            parts = relative_root.split(os.path.sep)
            for part in parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
        for file in files:
            file_path = os.path.join(root, file)
            loader = load_document(file_path)
            if loader:
                try:
                    docs = loader.load()
                    current_level[file] = {
                        'path': file_path,
                        'content': docs[0].page_content if docs else ''
                    }
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
            else:
                current_level[file] = {
                    'path': file_path,
                    'content': 'Unsupported file type'
                }
    return directory_structure

# 获取当前脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 构建 root_dir 的绝对路径
root_dir = os.path.join(script_dir, 'vast-vision-nocode-tool-analysis/vastlib')

# 确认 root_dir 的路径
print("Root directory:", root_dir)

# 遍历目录并生成目录结构
directory_structure = traverse_directory(root_dir)

# 保存目录结构到 JSON 文件
with open('output.json', 'w') as f:
    json.dump(directory_structure, f, indent=4)

import os
import json
import logging
import subprocess
from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.agents import Tool

logging.basicConfig(level=logging.INFO)
os.environ["USER_AGENT"] = "agent"

allowed_directory = os.path.abspath('./vastlib')
max_file_size = 1024 * 1024  # 1MB

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

def execute_file_tool(file_path: str) -> str:
    abs_path = os.path.abspath(file_path)
    if not abs_path.startswith(allowed_directory):
        return "Access denied."
    if not abs_path.endswith('.py'):
        return "Only .py files are allowed."
    if os.path.getsize(abs_path) > max_file_size:
        return "File is too large."
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

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=os.environ["GOOGLE_API_KEY"]
)

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class Agent:
    def __init__(self, model, tools, system="", checkpointer=None):
        self.system = system
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
                tool = self.tools[t['name']]
                if t['name'] == 'read_file':
                    args = t['args']['file_path']
                elif t['name'] == 'execute_python_file':
                    args = t['args']['file_path']
                else:
                    args = t['args']
                result = tool.invoke(args)
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}

prompt = """You are a python programmer agent that can read files or execute python scripts on demand. 
If the user requests to read a text file or execute a python script from the allowed directory, use the tools accordingly.
"""
tools = [read_file, execute_file]

with SqliteSaver.from_conn_string(":memory:") as memory:
    agent = Agent(llm, tools, system=prompt, checkpointer=memory)

    with open('output.json', 'r') as f:
        data = json.load(f)

    def get_files_from_json(json_data, parent_path=''):
        files = []
        for key, value in json_data.items():
            if isinstance(value, dict):
                if 'path' in value and 'content' in value:
                    file_info = {
                        'path': value['path'],
                        'size': value['size'],
                        'modified_time': value['modified_time'],
                        'content': value['content']
                    }
                    files.append(file_info)
                else:
                    files.extend(get_files_from_json(value, os.path.join(parent_path, key)))
        return files

    files = get_files_from_json(data)

    report = []

    for file_info in files:
        if file_info['path'].endswith('.py'):
            messages = [HumanMessage(content=f"Please execute the python file {file_info['path']}")]
        elif file_info['path'].endswith(('.txt', '.md')):
            messages = [HumanMessage(content=f"Please read the file {file_info['path']}")]
        else:
            continue
        try:
            thread = {"configurable": {"thread_id": "1"}}
            for event in agent.graph.stream({"messages": messages}, thread):
                for v in event.values():
                    response = v['messages']
                    report.append(f"File: {file_info['path']}\nResponse: {response}\n")
        except Exception as e:
            report.append(f"File: {file_info['path']}\nError: {e}\n")

    with open('report.txt', 'w') as f:
        f.write('\n'.join(report))