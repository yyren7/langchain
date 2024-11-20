# sk-ODvoPZ9Heq4sRY34U5TwK2XCrrlbKMhosVSVm6JCxNhQhSuy


from pathlib import Path
from openai import OpenAI
import numpy as np
import re
import json
from function_generation.pos_calculation_2 import move_in_direction

client2 = OpenAI(api_key="sk-a5fe39f6088d410784c2c31a5db4cc5f", base_url="https://api.deepseek.com")

# 把它放进请求中
content2 = ("该助手通过使用上方提供的api生成机器人控制python代码，开始时启动机器人并且等待两秒，结束时关闭机器人。"
            "对于抓取和放置任务，首先分别用抓取关节坐标和放置关节坐标通过正运动学API计算出其六维坐标。"
            "然后通过move_in_direction函数计算以当前朝向为基准向方向移动-10厘米后的新抓取和放置坐标。"
            "然后，先到达新抓取位置，用jog命令以工具坐标为基准向z正方向前移10cm再后退，再到达新放置位置，同样前移10cm再后退。")

content3 = ("该助手仿照代码样例，生成机器人控制任务python代码。任务开始时启动机器人并且等待两秒，结束时关闭机器人。"
            "对于抓取和放置任务，首先计算以当前工具朝向为基准向反方向移动10厘米后的新抓取和放置坐标。"
            "然后，先到达新抓取位置，用jog命令以工具坐标为基准向正方向前移10cm再后退回来。再到达新放置位置，同样前移10cm再后退回来。"
            "无限重复上述动作。")

magic = str(open('../magic.txt'))

api_description = str(json.load(open('../dobot/api_description.json', 'rb')))

content0 = "根据api名称和使用方式寻找上方任务需要用到的api，并返回他们的api名称。"
system_prompt = """
该用户会提供某机器人python api的名称和使用方式。而你只需要根据需求输出"api名称"。

EXAMPLE INPUT: 
{
    "api名称": [
        "EnableRobot",
        "DisableRobot"
    ],
    "使用方式": [
        "原型：EnableRobot(load,centerX,centerY,centerZ)，描述：使能机械臂",
        "原型：DisableRobot()，描述：下使能机器人"
    ]
}

EXAMPLE JSON OUTPUT:
{
    "api名称": [
        {"name":"EnableRobot"},
        {"name":"DisableRobot"}
    ]
}
"""
"""
response = client2.chat.completions.create(
    model="deepseek-coder",
    messages=[
        {
            "role": "system",
            "content": api_description,
        },
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content0},
    ],
    max_tokens=2048,
    temperature=0.0,
    stream=False,
    response_format={
        'type': 'json_object'
    }

)
results = response.choices[0].message.content
data = json.loads(results)
print(response.choices[0].message.content)
file_content = ""
for result in data["api名称"]:
    # print(result['name'])
    file_content += str(json.load(open('../dobot/result/' + result['name'] + '_api.json', 'rb')))

content1 = ("This GPT assists in developing robot control programs by analyzing  API details. It generates executable "
            "python code. Make sure wait for two seconds after the robot is enabled at first and unable the robot at "
            "last. For pick and place task, calculate the pick Point position from the provided pick Joint position, "
            "then calculate the start Point position which is 10 cm away from the tool coordinate system in z "
            "direction. Reach the new start pick and place position, insert 10 cm and then go back for 10 cm use jog "
            "move command with tool coordinate system for them both. This robot use cm as its insert unit.")


{
            "role": "system",
            "content": magic,
        },
                {
            "role": "system",
            "content": "会用到的api"+file_content,
        },
        {
            "role": "system",
            "content": "接口代码："+api_code,
        },
"""

api_code = (str(open("../dobot/TCP-IP-4Axis-Python/PythonExample.py")))
example=(str(open("../dobot/TCP-IP-4Axis-Python/main_mg400.py")))
pos = "ip=192.168.250.101 ,pos_start = [284, 4, 90, -43],pos_end = [280, 104, 80, -23]"

response = client2.chat.completions.create(
    model="deepseek-coder",
    messages=[
        {
            "role": "system",
            "content": "编程样例："+example,
        },
        {
            "role": "system",
            "content": content3,
        },
        {
            "role": "user",
            "content": "从起始位置抓取物件放置到结束位置" + pos,
        },
    ],
    max_tokens=2048,
    temperature=0.0,
    stream=False
)
result = response.choices[0].message.content
# 定义正则表达式模式，使用 re.DOTALL 使 '.' 匹配包括换行符在内的所有字符
pattern = r"```python(.*?)```"
match = re.findall(pattern, result, re.DOTALL)[0]

print(match)
f2 = open("result_mg400_1.py", 'w', encoding='UTF-8')
f2.write(match)
f2.close()
