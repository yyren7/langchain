
# api_minimazation

## api_document_analysis.py
**Content:**

```python
import numpy as np
file_content1 = str(np.load("../fr_robot/extracted_fr_npy/1.npy"))
file_content2 = str(np.load("../fr_robot/extracted_fr_npy/2.npy"))
file_content3 = str(np.load("../fr_robot/extracted_fr_npy/3.npy"))
file_content4 = str(np.load("../fr_robot/extracted_fr_npy/4.npy"))
```

### analysis

The code loads four numpy array files (.npy) from the specified directory. It then converts the content of each loaded array into a string and assigns them to variables file_content1, file_content2, file_content3, and file_content4 respectively. This suggests the code is preparing to process or analyze the data stored in these numpy files, likely for further use.


## api_minimization.py
**Content:**

```python
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

```

### analysis

This Python script extracts API information from several `.npy` files, likely containing robot control data. It uses the OpenAI library (with a DeepSeek API key) to process the extracted content. The script sends a system prompt and user content to the DeepSeek model, requesting the extraction of API names, usage, and example code in JSON format. The final JSON output is then saved to a file named `minimized_api.json`. The script focuses on parsing robot API information from the provided data.


## api_minimization_2.py
**Content:**

```python
from openai import OpenAI
import numpy as np
import os
client2 = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

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

```

### analysis

This code snippet uses the OpenAI library to interact with a DeepSeek API for code completion. It loads five `.npy` files, converts their content to strings, and concatenates them. It then sends this combined content, along with a system prompt instructing the model to extract API information (name, usage, example code) in JSON format, and a user query asking for specific robot control APIs, to the DeepSeek API. The response, formatted as a JSON object, is then saved to a file.


## api_minimization_mg400.py
**Content:**

```python
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



```

### analysis

This code extracts API descriptions from a robot manual using a large language model. It iterates through a list of API names, constructs a prompt asking the model to find and extract the API details from a loaded document, and formats the output as JSON. The extracted information includes the API name, prototype, description, parameters, return values, and examples. The results are then saved into individual JSON files. The code uses the DeepSeek API for processing.

