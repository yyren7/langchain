from langchain_google_genai import ChatGoogleGenerativeAI
import os
import logging
import absl.logging
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

os.environ["USER_AGENT"] = "MyCustomAgent/1.0"
# 隐藏 gRPC 日志
absl.logging.set_verbosity(absl.logging.ERROR)
logging.getLogger('grpc').setLevel(logging.ERROR)

# 设置 API 密钥
'''
# 初始化 Gemini 模型
gemini_model = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=50,  # 限制输出 token 数
    timeout=60,  # 设置超时时间
    max_retries=3  # 增加重试次数
)

messages = [
    ("system", "You are a helpful assistant that translates English to French. Translate the user sentence."),
    ("human", "I love programming."),
]

try:
    ai_msg = gemini_model.stream(messages)
    for chunk in ai_msg:
        print(chunk.content)
except Exception as e:
    print(f"Error invoking Gemini model: {e}")
'''

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class Agent:
    # langgraphを使って、multi_agentフレームワークを構築しました。
    # agentループの終了判定条件（質のいいコードを生成できた、必要の分のAPIだけを選択できた）のところは上手く設定できない現状です。
    def __init__(self, model, tools, system="", checkpointer=None):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_deepseek)
        graph.add_node("document_llm", self.call_moonshot)
        graph.add_node("selection_llm", self.call_moonshot)
        graph.add_node("code_adjustment", self.take_action)
        graph.add_conditional_edges(
            "document_llm",
            self.exists_action,
            {True: "selection_llm", False: "llm"}
        )
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "code_adjustment", False: END}
        )
        graph.add_edge("selection_llm", "document_llm")
        graph.add_edge("code_adjustment", "llm")
        graph.set_entry_point("document_llm")
        self.graph = graph.compile(checkpointer=checkpointer)
        self.tools = {t.name: t for t in tools}
        self.model =model.bind_tools(tools)
        self.document_model = document_model.bind_tools(tools)

    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_deepseek(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def call_moonshot(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.document_model.invoke(messages)
        return {'messages': [message]}

    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")
            if not t['name'] in self.tools:  # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}


prompt = """You are a smart research assistant. Use the search engine to look up information. \
    You are allowed to make multiple calls (either together or in sequence). \
    Only look up information when you are sure of what you want. \
    If you need to look up some information before asking a follow up question, you are allowed to do that!
    """
## Model
deepseek_model = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com",
    temperature=0.0
)

model = ChatGoogleGenerativeAI(
    model="gemini-exp-1121",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=os.environ["GOOGLE_API_KEY"]
)

document_model = ChatOpenAI(
    api_key=os.getenv('MOOONSHOT_API_KEY'),
    base_url="https://api.moonshot.cn/v1",
    temperature=0.0
)
## Tool
tool = TavilySearchResults(max_results=4)

from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string(":memory:") as memory:
    # Agent
    agent = Agent(model, [tool], system=prompt, checkpointer=memory)
    agent.graph.get_graph().draw_mermaid_png(curve_style=CurveStyle.LINEAR,
                                             node_colors=NodeStyles(first="#ffdfba", last="#baffc9", default="#fad7de"),
                                             wrap_label_n_words=9,
                                             output_file_path="1.png",
                                             draw_method=MermaidDrawMethod.API,
                                             background_color="white",
                                             padding=10)

    # Image(agent.graph.get_graph().draw_png)
    messages = [HumanMessage(content="What is the weather in sf?")]

    thread = {"configurable": {"thread_id": "1"}}

    for event in agent.graph.stream({"messages": messages}, thread):
        for v in event.values():
            print(v['messages'])

    messages = [HumanMessage(content="How about in LA?")]

    for event in agent.graph.stream({"messages": messages}, thread):
        for v in event.values():
            print(v['messages'])

    messages = [HumanMessage(content="Which one is warmer?")]
    for event in agent.graph.stream({"messages": messages}, thread):
        for v in event.values():
            print(v)