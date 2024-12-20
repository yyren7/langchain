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
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted
import time

# 配置日志记录
logging.basicConfig(level=logging.INFO)


# 定义LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-thinking-exp-1219",
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
        self.analysis_results = {}
        self.directory_structure = self.traverse_directory('./vast-vision-nocode-tool-analysis/nodes_common')
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_gemini)
        graph.add_conditional_edges(
            "llm",
            self.result_judge,
            {True: END, False: "llm"}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile(checkpointer=checkpointer)
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def result_judge(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    read_file = Tool(
        name="read_file",
        func=result_judge,
        description="Useful for judging if user is satisfied."
    )
    def call_gemini(self, state: AgentState):
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
                content="You are a professional analyst. Please analyze the following content and provide your insights."),
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
            logging.error(f"An error occurred during analysis: {e}")
            analysis_result = "An error occurred during analysis."
        return analysis_result  # 返回累积的完整分析结果


# 设置系统提示
prompt = """
For each file, choose the most appropriate tool to analyze it.
Only use one tool per file.
"""
# 创建Agent实例
tools = [result_judge]
with SqliteSaver.from_conn_string(":memory:") as memory:
    agent = Agent(llm, tools, system=prompt, checkpointer=memory)
    agent.graph.get_graph().draw_mermaid_png(
        output_file_path="process.png",
        draw_method=MermaidDrawMethod.API
    )
    agent.process_directory(agent.directory_structure)
    # 保存分析结果到JSON文件
print("Analysis results:", agent.analysis_results)
