from openai import OpenAI
import numpy as np
import json
import os
client2 = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/beta")

# 把它放进请求中

file_content1 = str(np.load("../fr_robot/extracted_fr_npy/1.npy"))
file_content2 = str(np.load("../fr_robot/extracted_fr_npy/2.npy"))
file_content3 = str(np.load("../fr_robot/extracted_fr_npy/3.npy"))
file_content4 = str(np.load("../fr_robot/extracted_fr_npy/4.npy"))
file_content5 = str(np.load("../fr_robot/extracted_fr_npy/5.npy"))
system_prompt = """The user will provided a robot manual which include a python api name and its description.

EXAMPLE INPUT: 
EnableRobot（立即指令）

原型

EnableRobot(load,centerX,centerY,centerZ)

描述

使能机械臂。执行队列指令（机械臂运动、队列IO等）前必须先使能机械臂。

参数
参数名 类型 说明

load double 设置负载重量，取值范围不能超过各个型号机器人的负载范围。单
位：kg
centerX double X方向偏心距离。取值范围：-500 ~ 500，单位：mm
centerY double Y方向偏心距离。取值范围：-500 ~ 500，单位：mm
centerZ double Z方向偏心距离。取值范围：-500 ~ 500，单位：mm

均为可选参数，可携带的参数数量如下：
0：不携带参数，表示使能时不设置负载重量和偏心参数。
1：携带一个参数，该参数表示负载重量。
4：携带四个参数，分别表示负载重量和偏心参数。

返回

ErrorID,{},EnableRobot(load,centerX,centerY,centerZ);

示例

EnableRobot()

使能机器人，不设置负载重量和偏心参数。

EnableRobot(0.5)

使能机器人并设置负载重量0.5kg。
EnableRobot(0.5,0,0,5.5)

使能机器人并设置负载重量1.5kg，Z方向偏心5.5mm。

EXAMPLE JSON OUTPUT:
{
    "api名称": "EnableRobot（立即指令）",
    "原型": "EnableRobot(load,centerX,centerY,centerZ)",
    "描述": "使能机械臂。执行队列指令（机械臂运动、队列IO等）前必须先使能机械臂。",
    "参数": "[{"参数名":centerX,"类型":double,"说明":X方向偏心距离。取值范围：-500 ~ 500，单位：mm}, {"参数名":centerY,"类型":double,"说明":X方向偏心距离。取值范围：-500 ~ 500，单位：mm},{"参数名":centerZ,"类型":double,"说明":X方向偏心距离。取值范围：-500 ~ 500，单位：mm}],
    均为可选参数，可携带的参数数量如下：
0：不携带参数，表示使能时不设置负载重量和偏心参数。
1：携带一个参数，该参数表示负载重量。
4：携带四个参数，分别表示负载重量和偏心参数。",
    "返回": "ErrorID,{},EnableRobot(load,centerX,centerY,centerZ);",
    "示例":"EnableRobot()
# 使能机器人，不设置负载重量和偏心参数。
EnableRobot(0.5)
# 使能机器人并设置负载重量0.5kg。
EnableRobot(0.5,0,0,5.5)
# 使能机器人并设置负载重量1.5kg，Z方向偏心5.5mm。"
}
"""
with open('../dobot_robot/api_description.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
names=data['api名称']
file_content = str(np.load("../moonshot/mg400_api.npy"))
for name in names:
    content = "在文档中寻找名称为" + name + "的api，读取该api的内容，以固定格式输出。"
    response = client2.chat.completions.create(
        model="deepseek-coder",
        messages=[
            {
                "role": "system",
                "content": file_content,
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
    f2 = open("../dobot/result/"+name+"_api.json", 'w', encoding='UTF-8')
    f2.write(result)
    f2.close()


