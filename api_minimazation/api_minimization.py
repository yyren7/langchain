import os

from openai import OpenAI
import numpy as np

client2 = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com/beta")

# 把它放进请求中

file_content1 = str(np.load("../fr_robot/extracted_fr_npy/1.npy"))
file_content2 = str(np.load("../fr_robot/extracted_fr_npy/2.npy"))
file_content3 = str(np.load("../fr_robot/extracted_fr_npy/3.npy"))
file_content4 = str(np.load("../fr_robot/extracted_fr_npy/4.npy"))
file_content5 = str(np.load("../fr_robot/extracted_fr_npy/5.npy"))
file_content6 = str(np.load("../moonshot/mg400_api.npy"))
content = "从上述文件提取所有python的api名称，用例代码和具体使用方式，不要其他解释内容。"
system_prompt = """The user will provided a robot manual which include its python api. Please parse the "api名称",
"使用方式" and "用例代码" and output them in JSON format.

EXAMPLE INPUT: 
1.1. 实例化机器人
原型
RPC(ip)
描述
实例化一个机器人对象
必选参数
ip：机器人的IP地址，默认出厂IP为“192.168.58.2”
默认参数
无
返回值
成功：返回一个机器人对象
失败：创建的对象会被销毁

1.1.1. 代码示例
from fairino import Robot
# 与机器人控制器建立连接，连接成功返回一个机器人对象
robot = Robot.RPC('192.168.58.2')

EXAMPLE JSON OUTPUT:
{
    "api名称": "实例化机器人",
    "使用方式": "原型："RPC(ip)"，描述："实例化一个机器人对象"，必选参数："ip：机器人的IP地址，默认出厂IP为“192.168.58.2”"，默认参数："无"，返回值："成功：返回一个机器人对象，失败：创建的对象会被销毁"",
    "用例代码": "from fairino import Robot
# 与机器人控制器建立连接，连接成功返回一个机器人对象
robot = Robot.RPC('192.168.58.2')"
}
"""
response = client2.chat.completions.create(
    model="deepseek-coder",
    messages=[
        {
            "role": "system",
            "content": api_description,
        },
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content},
    ],
    max_tokens=8192,
    temperature=0.0,
    stream=False,
    response_format={
        'type': 'json_object'
    }

)
result = response.choices[0].message.content
print(response.choices[0].message.content)
f2 = open("../dobot_robot/minimized_api.json", 'w', encoding='UTF-8')
f2.write(result)
f2.close()
