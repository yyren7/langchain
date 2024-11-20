from openai import OpenAI
import numpy as np

client2 = OpenAI(api_key="sk-a5fe39f6088d410784c2c31a5db4cc5f", base_url="https://api.deepseek.com")

# 把它放进请求中

file_content1 = str(np.load("../fr_robot/extracted_fr_npy/1.npy"))
file_content2 = str(np.load("../fr_robot/extracted_fr_npy/2.npy"))
file_content3 = str(np.load("../fr_robot/extracted_fr_npy/3.npy"))
file_content4 = str(np.load("../fr_robot/extracted_fr_npy/4.npy"))
file_content5 = str(np.load("../fr_robot/extracted_fr_npy/5.npy"))
content = "从上述文件查询使能机器人，MOVEL直线运动,MOVEJ直线运动,JOG直线运动，机器人点位整体偏移,运动学求解，逆运动学求解的api并返回他们的名称，使用方式和用例代码。"
system_prompt = """
The user will provided a python api manual. Please parse the "api名称"，""使用方式""，"用例代码" and output them in JSON format. 

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
    "用例代码": "from fairino import Robot # 与机器人控制器建立连接，连接成功返回一个机器人对象 robot = Robot.RPC('192.168.58.2')"
}
"""
response = client2.chat.completions.create(
    model="deepseek-coder",
    messages=[
        {
            "role": "system",
            "content": file_content1 + file_content2 + file_content3 + file_content4 + file_content5,
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
f2 = open("../fr_robot/extracted_json_fr/minimized_api_5.json", 'w', encoding='UTF-8')
f2.write(result)
f2.close()
