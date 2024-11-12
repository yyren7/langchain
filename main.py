from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
import os

os.environ["TAVILY_API_KEY"] = "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"


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class Agent:

    def __init__(self, model, tools, system="", checkpointer=None):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_deepseek)
        """
        graph.add_node("document_llm", self.call_moonshot)
        """
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
model = ChatOpenAI(
    model="deepseek-chat",
    api_key="sk-a5fe39f6088d410784c2c31a5db4cc5f",
    base_url="https://api.deepseek.com",
    temperature=0.0
)

document_model = ChatOpenAI(
    api_key="sk-ODvoPZ9Heq4sRY34U5TwK2XCrrlbKMhosVSVm6JCxNhQhSuy",
    base_url="https://api.moonshot.cn/v1",
    temperature=0.0
)
## Tool
tool = TavilySearchResults(max_results=4)

## Agent
agent = Agent(model, [tool], system=prompt)

from IPython.display import Image

Image(agent.graph.get_graph().draw_png())

messages = [HumanMessage(content="What is the weather in sf?")]
result = agent.graph.invoke({"messages": messages})
print(result)
from IPython.display import Markdown

print(result["messages"][-1].content)

messages = [HumanMessage(content="What is the weather in SF and LA?")]
result = agent.graph.invoke({"messages": messages})
print(result["messages"][-1].content)

messages = [HumanMessage(content="Who won the super bowl in 2024? In what state is the winning team headquarters "
                                 "located? What is the GDP of that state? Answer each question.")]
result = agent.graph.invoke({"messages": messages})
print(result["messages"][-1].content)

from langgraph.checkpoint.sqlite import SqliteSaver
from IPython.display import Image
import cv2

with SqliteSaver.from_conn_string(":memory:") as memory:
    # Agent
    agent = Agent(model, [tool], system=prompt, checkpointer=memory)
    agent.graph.get_graph().draw_png("1.png")


    cv2.waitKey(0)

    cv2.destroyAllWindows()


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

