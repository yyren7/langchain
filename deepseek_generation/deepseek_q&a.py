# sk-ODvoPZ9Heq4sRY34U5TwK2XCrrlbKMhosVSVm6JCxNhQhSuy


from pathlib import Path
from openai import OpenAI
import numpy as np
import json
import os
client2 = OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

# 把它放进请求中
content2 = ("该助手通过使用上方提供的api生成机器人控制python代码，开始时启动机器人并且等待两秒，结束时关闭机器人。"
            "对于抓取和放置任务，首先分别用抓取关节坐标和放置关节坐标通过正运动学API计算出其六维坐标。"
            "然后通过矩阵变换计算以当前朝向为基准向负方向移动10厘米后的新抓取和放置坐标。"
            "然后，先到达新抓取位置，用jog命令以工具坐标为基准向z正方向前移10cm再后退，再到达新放置位置，同样前移10cm再后退。")

file_content1 = str(np.load("../resources/api_fr_minimization/extracted_fr_npy/1.npy"))
file_content2 = str(np.load("../resources/api_fr_minimization/extracted_fr_npy/2.npy"))
file_content3 = str(np.load("../resources/api_fr_minimization/extracted_fr_npy/3.npy"))
file_content4 = str(np.load("../resources/api_fr_minimization/extracted_fr_npy/4.npy"))
file_content5 = str(np.load("../resources/api_fr_minimization/extracted_fr_npy/5.npy"))
with open('../resources/api_fr_minimization/extracted_json_fr/minimized_api_5.json', 'rb') as minimized_api_file:
    file_content6 = str(json.load(minimized_api_file))


content1 = ("This GPT assists in developing robot control programs by analyzing  API details. It generates executable "
            "python code. Make sure wait for two seconds after the robot is enabled at first and unable the robot at "
            "last. For pick and place task, calculate the pick Point position from the provided pick Joint position, "
            "then calculate the start Point position which is 10 cm away from the tool coordinate system in z "
            "direction. Reach the new start pick and place position, insert 10 cm and then go back for 10 cm use jog "
            "move command with tool coordinate system for them both. This robot use cm as its insert unit.")


pos = "pos J1 = [-89.662, -95.327, -81.219, -209.943, -120.115, -102.395]"
response = client2.chat.completions.create(
    model="deepseek-coder",
    messages=[
        {"role": "system", "content": "六维坐标的格式P=[x, y, z, rx, ry, rz],其中x,y,z指的是机器臂位置坐标，rx,ry,rz指的是当前的机器臂旋转角度。"},
        {
            "role": "user",
            "content": "写一个python程序，输入六维坐标P1，通过旋转矩阵获得从当前机器臂坐标位置向面朝方向的负方向移动10cm的新坐标,返回移动后的六维坐标P2。x,y,z的单位是mm。"
            ,
        },
    ],
    max_tokens=1024,
    temperature=0.0,
    stream=False
)
result = response.choices[0].message.content
print(response.choices[0].message.content)
f2 = open("result.txt", 'w', encoding='UTF-8')
f2.write(result)
f2.close()
