import os


from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI

# 创建 OpenAI 模型实例
"""
如果要使用 Google GenAI，请取消注释并配置好 GOOGLE_API_KEY
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=os.environ["GOOGLE_API_KEY"]
)
"""
# 这里使用 langchain 的 ChatOpenAI 初始化 deepseek_llm
deepseek_llm = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.environ["DEEPSEEK_API_KEY"],
    openai_api_base='https://api.deepseek.com',
    max_tokens=8192,
    temperature=0
)

# 定义思维链提示模板
cot_template = """
作为一个为水果电商公司工作的AI助手，我的目标是帮助客户根据他们的喜好做出明智的决定。
我会按部就班地思考，先理解客户的需求，然后考虑各种水果的特点，最后根据这些需求，给出我的推荐。
同时，我也会向客户解释我这样推荐的原因。

人类: {question}
AI:
"""

# 创建提示模板实例
prompt = PromptTemplate(template=cot_template, input_variables=["question"])

# 创建 LLMChain 实例
chain = LLMChain(llm=deepseek_llm, prompt=prompt)

# 输入客户问题并获取模型回答
question = "我想找一种不太甜且有浪漫寓意的水果，推荐一下。"
response = chain.run(question)

print(response)
