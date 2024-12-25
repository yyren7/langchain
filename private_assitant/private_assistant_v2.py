import os
import logging
from langchain.agents import Tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted

# 配置日志记录
logging.basicConfig(level=logging.INFO)

# 定义 LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=os.environ["GOOGLE_API_KEY"]
)

# 定义 should_continue Tool
def should_continue_tool(user_input):
    return user_input.lower() not in ["exit", "quit", "bye", "no", "stop", "end"]

should_continue_tool = Tool(
    name="ShouldContinue",
    func=should_continue_tool,
    description="Determines whether the conversation should continue based on user input."
)

# 定义对话代理类
class DialogueAgent:
    def __init__(self, model, system_prompt="You are a helpful assistant."):
        self.model = model
        self.system_prompt = system_prompt
        self.messages = [SystemMessage(content=system_prompt)]

    @retry(
        retry=retry_if_exception_type(ResourceExhausted),
        wait=wait_exponential(min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def interact(self, user_input):
        # 将用户输入添加到对话历史中
        self.messages.append(HumanMessage(content=user_input))

        try:
            # 调用模型生成回复
            response = self.model.invoke(self.messages)
            self.messages.append(response)
            return response.content
        except ResourceExhausted as e:
            logging.error(f"ResourceExhausted error: {e}")
            return "API quota exhausted. Please try again later."
        except Exception as e:
            logging.error(f"Error during interaction: {e}")
            return "An error occurred during the interaction."

# 主函数
def main():
    # 初始化对话代理
    agent = DialogueAgent(llm)

    print("Welcome to the Dialogue Agent! Type 'exit', 'quit', 'bye', 'no', 'stop', or 'end' to end the conversation.")

    while True:
        # 获取用户输入
        user_input = input("\nYou: ")

        # 使用 should_continue Tool 判断是否退出对话
        if not should_continue_tool.func(user_input):
            print("Goodbye!")
            break

        # 与代理交互
        response = agent.interact(user_input)
        print(f"Agent: {response}")

if __name__ == "__main__":
    main()