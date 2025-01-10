# -*- coding: utf-8 -*-
import os
import logging
import time

from langchain.agents import Tool
from langchain_openai import ChatOpenAI  # 使用 langchain 的 ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted
# 配置日志记录
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# 定义 LLM
'''
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=os.environ["GOOGLE_API_KEY"]
)
'''
# 使用 langchain 的 ChatOpenAI 初始化 deepseek_llm
deepseek_llm = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.environ["DEEPSEEK_API_KEY"],
    openai_api_base='https://api.deepseek.com',
    max_tokens=8192
)
# 定义 should_continue Tool
def should_continue_tool(user_input):
    prompt = f"""判断用户是否明确表示要结束当前对话。仅回答yes或no，不包含任何其他文字。yes表示用户不希望结束对话，no表示用户希望结束对话。请结合用户的实际意图来判断，而不仅仅是根据关键词。只有当用户的意图非常明确地表示要结束对话时，才回答‘no’，否则回答‘yes’。例如，当用户说‘我要写一封道别的信’时，不应认为用户要结束对话；而当用户说‘好的，再见’时，应认为用户要结束对话。

    User Input: {user_input}

    Response:"""
    response = deepseek_llm.invoke(prompt)
    return response.content.strip().lower() == "yes"


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
        self.dialogue_history = []  # 用于记录对话历史

    @retry(
        retry=retry_if_exception_type(ResourceExhausted),
        wait=wait_exponential(min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def interact_stream(self, user_input, update_callback, finalize_callback):
        """
        流式交互方法，逐块更新 GUI 内容。

        :param user_input: 用户输入文本
        :param update_callback: 每次接收到块时调用的回调函数
        :param finalize_callback: 流结束时调用的回调函数
        """
        # 将用户输入添加到对话历史中
        self.messages.append(HumanMessage(content=user_input))
        self.dialogue_history.append(f"**You:** {user_input}")  # 记录用户输入

        try:
            # 调用模型生成回复，使用流式输出
            response_stream = self.model.stream(self.messages)

            full_response = ""
            for chunk in response_stream:
                full_response += chunk.content
                update_callback(chunk.content)  # 调用更新回调

            # 将完整的响应添加到对话历史中
            self.messages.append(AIMessage(content=full_response))
            self.dialogue_history.append(f"**Agent:** {full_response}")  # 记录代理回复

            finalize_callback()  # 调用完成回调
        except ResourceExhausted as e:
            logging.error(f"ResourceExhausted error: {e}")
            error_message = "API quota exhausted. Please try again later."
            self.dialogue_history.append(f"**Agent:** {error_message}")  # 记录错误信息
            update_callback(error_message)
            finalize_callback()
        except Exception as e:
            logging.error(f"Error during interaction: {e}")
            error_message = "An error occurred during the interaction."
            self.dialogue_history.append(f"**Agent:** {error_message}")  # 记录错误信息
            update_callback(error_message)
            finalize_callback()

    def interact(self, user_input):
        # 将用户输入添加到对话历史中
        self.messages.append(HumanMessage(content=user_input))
        self.dialogue_history.append(f"**You:** {user_input}")  # 记录用户输入

        try:
            # 调用模型生成回复，使用流式输出
            response_stream = self.model.stream(self.messages)

            # 逐块输出响应
            print("Agent: ", end="", flush=True)
            full_response = ""
            for chunk in response_stream:
                print(chunk.content, end="", flush=True)
                full_response += chunk.content

            # 将完整的响应添加到对话历史中
            self.messages.append(AIMessage(content=full_response))
            self.dialogue_history.append(f"**Agent:** {full_response}")  # 记录代理回复
            print()  # 换行
            return full_response
        except ResourceExhausted as e:
            logging.error(f"ResourceExhausted error: {e}")
            error_message = "API quota exhausted. Please try again later."
            self.dialogue_history.append(f"**Agent:** {error_message}")  # 记录错误信息
            return error_message
        except Exception as e:
            logging.error(f"Error during interaction: {e}")
            error_message = "An error occurred during the interaction."
            self.dialogue_history.append(f"**Agent:** {error_message}")  # 记录错误信息
            return error_message

    def save_dialogue_to_markdown(self, folder="result"):
        """将对话历史保存为 Markdown 文件，文件名使用当前时间戳，并保存到指定文件夹"""

        # 确保文件夹存在，如果不存在则创建
        if not os.path.exists(folder):
            os.makedirs(folder)

        # 生成当前时间戳作为文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(folder, f"{timestamp}.md")

        # 将对话历史保存为 Markdown 文件
        with open(filename, "w", encoding="utf-8") as file:
            file.write("# Dialogue History\n\n")
            for entry in self.dialogue_history:
                file.write(f"{entry}\n\n")

        logging.info(f"Dialogue saved to {filename}")


# 主函数
def main():
    # 初始化对话代理
    agent = DialogueAgent(deepseek_llm)

    print("Welcome to the Dialogue Agent! Type 'exit', 'quit', 'bye', 'no', 'stop', or 'end' to end the conversation.")

    while True:
        # 获取用户输入
        user_input = input("\nYou: ").strip()  # 去除输入的前后空白字符

        # 如果输入为空（用户只按了回车），则跳过处理
        if not user_input:
            continue

        # 使用 should_continue Tool 判断是否退出对话
        if not should_continue_tool.func(user_input):
            print("Goodbye!")
            agent.save_dialogue_to_markdown()  # 保存对话记录
            break

        # 与代理交互
        agent.interact(user_input)


if __name__ == "__main__":
    main()