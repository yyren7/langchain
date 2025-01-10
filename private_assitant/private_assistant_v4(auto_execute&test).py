# private_assistant_v3.py
# -*- coding: utf-8 -*-
import os
import logging
import time

from langchain.agents import Tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ===== 1) 定义 LLM =====

# 如果要使用 Google GenAI，请取消注释并配置好 GOOGLE_API_KEY
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=os.environ["GOOGLE_API_KEY"]
)

# 这里使用 langchain 的 ChatOpenAI 初始化 deepseek_llm
deepseek_llm = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.environ["DEEPSEEK_API_KEY"],
    openai_api_base='https://api.deepseek.com',
    max_tokens=8192,
    temperature=0
)

# ===== 2) 定义是否继续对话的 Tool =====
def should_continue_tool_func(user_input):
    prompt = f"""判断用户是否明确表示要结束当前对话。仅回答yes或no，不包含任何其他文字。
yes表示用户不希望结束对话，no表示用户希望结束对话。
请结合用户的实际意图来判断，而不仅仅是根据关键词。
只有当用户非常明确地表示要结束对话时，才回答‘no’，否则回答‘yes’。

User Input: {user_input}

Response:"""
    response = deepseek_llm.invoke(prompt)
    return response.content.strip().lower() == "yes"

should_continue_tool = Tool(
    name="ShouldContinue",
    func=should_continue_tool_func,
    description="Determines whether the conversation should continue based on user input."
)

# ===== 3) 定义切换模型的 Tool =====
def switch_model_tool_func(user_input, agent):
    """
    根据用户输入切换模型。
    - 如果用户输入“切换到deepseek”，则切换到 deepseek_llm。
    - 如果用户输入“切换到gemini”，则切换到 llm（Gemini）。
    """
    if "切换到deepseek" in user_input.lower():
        agent.model = deepseek_llm
        return "已切换到 DeepSeek 模型。"
    elif "切换到gemini" in user_input.lower():
        agent.model = llm
        return "已切换到 Gemini 模型。"
    else:
        return "未检测到切换模型的指令。"

switch_model_tool = Tool(
    name="SwitchModel",
    func=lambda user_input: switch_model_tool_func(user_input, agent),  # 传入当前的 agent 实例
    description="Switches between DeepSeek and Gemini models based on user input."
)

# ===== 4) 定义对话代理类 =====
class DialogueAgent:
    def __init__(self, model, system_prompt="You are a helpful assistant."):
        self.model = model
        self.system_prompt = system_prompt
        # 初始消息：SystemMessage
        self.messages = [SystemMessage(content=system_prompt)]
        self.dialogue_history = []  # 用于记录对话历史

    @retry(
        retry=retry_if_exception_type(ResourceExhausted),
        wait=wait_exponential(min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def interact_stream_generator(self, user_input):
        """
        以生成器形式流式输出的交互方法：
        - 前台 (GUI) 可以通过:
            for chunk in agent.interact_stream_generator(user_input):
                # 逐块更新UI
        - 最后一个 yield 之后，对话就完整结束
        """
        # 检查是否需要切换模型
        switch_response = switch_model_tool_func(user_input, self)
        if "已切换到" in switch_response:
            yield switch_response  # 通知用户模型已切换
            return  # 结束当前交互

        # 1) 记录用户输入
        self.messages.append(HumanMessage(content=user_input))
        self.dialogue_history.append(f"**You:** {user_input}")

        try:
            # 2) 调用模型的 stream 方法，得到一个可迭代的响应流
            response_stream = self.model.stream(self.messages)
            full_response = ""

            # 3) 逐块 yield 内容
            for chunk in response_stream:
                text_piece = chunk.content
                full_response += text_piece
                # 把当前块内容 yield 给前端
                yield text_piece

            # 4) 全部完成后，将完整响应写入对话历史
            self.messages.append(AIMessage(content=full_response))
            self.dialogue_history.append(f"**Agent:** {full_response}")

            # 5) 用 None 作为一个“结束标记”，告知前台收尾
            yield None

        except ResourceExhausted as e:
            logging.error(f"ResourceExhausted error: {e}")
            error_message = "API quota exhausted. Please try again later."
            self.dialogue_history.append(f"**Agent:** {error_message}")
            # 同样 yield 这个错误提示
            yield error_message
            yield None

        except Exception as e:
            logging.error(f"Error during interaction: {e}")
            error_message = "An error occurred during the interaction."
            self.dialogue_history.append(f"**Agent:** {error_message}")
            yield error_message
            yield None

    def save_dialogue_to_markdown(self, folder="result"):
        """
        将对话历史保存为 Markdown 文件
        """
        if not os.path.exists(folder):
            os.makedirs(folder)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(folder, f"{timestamp}.md")

        with open(filename, "w", encoding="utf-8") as file:
            file.write("# Dialogue History\n\n")
            for entry in self.dialogue_history:
                file.write(f"{entry}\n\n")

        logging.info(f"Dialogue saved to {filename}")

    # 可选：旧的非流式方法（命令行用）
    def interact(self, user_input):
        """
        不需要GUI的场景下，命令行一次性输出的简单示例。
        """
        self.messages.append(HumanMessage(content=user_input))
        self.dialogue_history.append(f"**You:** {user_input}")
        try:
            response_stream = self.model.stream(self.messages)
            print("Agent: ", end="", flush=True)
            full_response = ""
            for chunk in response_stream:
                print(chunk.content, end="", flush=True)
                full_response += chunk.content
            self.messages.append(AIMessage(content=full_response))
            self.dialogue_history.append(f"**Agent:** {full_response}")
            print()
            return full_response
        except ResourceExhausted as e:
            ...
        except Exception as e:
            ...