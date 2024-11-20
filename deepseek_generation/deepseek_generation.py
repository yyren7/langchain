# sk-ODvoPZ9Heq4sRY34U5TwK2XCrrlbKMhosVSVm6JCxNhQhSuy


from openai import OpenAI
import re
import json

client2 = OpenAI(api_key="sk-a5fe39f6088d410784c2c31a5db4cc5f", base_url="https://api.deepseek.com")

# 把它放进请求中
content2 = ("该助手通过使用上方提供的api生成机器人控制python代码，开始时启动机器人并且等待两秒，结束时关闭机器人。"
            "对于抓取和放置任务，首先分别用抓取关节坐标和放置关节坐标通过正运动学API计算出其六维坐标。"
            "然后通过move_in_direction函数计算以当前朝向为基准向方向移动-10厘米后的新抓取和放置坐标。"
            "然后，先到达新抓取位置，用jog命令以工具坐标为基准向z正方向前移10cm再后退，再到达新放置位置，同样前移10cm再后退。")

content_mg400 = ("该助手通过使用上方提供的mg400_api生成机器人抓取和放置任务python代码。"
                 "在理解api内部构造的基础上，必须使用from dobot_api import DobotApiDashboard, "
                 "DobotApi,DobotApiMove。必须使用def connect_robot()。任务开始时启动机器人并且等待两秒。"
                 "严格遵守mg400_api的使用方法，使用mg400_api的相关函数，速度调整到最大速度的百分之八十，每一步之间间隔100ms。"
                 "对于抓取和放置任务：1，计算抓取的开始坐标，该坐标为实际物体位置的上方20cm。2，先到达抓取开始坐标，然后从开始坐标向正方向下移20cm。"
                 "3，启动指定数字输出。4，再从当前位置上升20cm，然后移动到放置坐标。5，用mg400_api里的相关函数关闭指定数字输出。"
                 "最后返回字符串“任务完成”。根据用户要求重复上述任务。")

magic = str(open('../magic.txt'))

api_description = str(json.load(open('../dobot_robot/api_description.json', 'rb')))

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

api_code = (str(open("../dobot_robot/TCP-IP-4Axis-Python/PythonExample.py")))
api = (str(open("../dobot_robot/TCP-IP-4Axis-Python/dobot_api.py")))
example = (str(open("../dobot_robot/TCP-IP-4Axis-Python/main_mg400.py")))
pos = ("ip=192.168.250.101 , "
       "pos_object = [[291, 10, 10, 0], [272, 12, 10, 0],[255, 13.5, 10, 0], [237, 14, 10, 0],"
       " [290, -178, 10, 0], [271, -177, 10, 0], [252, -177, 10, 0], [233, -177, 10, 0]]"
       ",pos_end = [158, 234, 86, 21],DO=1")
pos_new = "z=10,pos_end = [158, 234, 86, 21],DO=1"
response = client2.chat.completions.create(
    model="deepseek-coder",
    messages=[
        {
            "role": "system",
            "content": "mg400_api：" + api_code,
        },
        {
            "role": "system",
            "content": "mg400api内部构造：" + api,
        },
        {
            "role": "system",
            "content": content_mg400,
        },
        {
            "role": "user",
            "content": "抓取物件放置到结束位置" + pos,
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
f2 = open("result_mg400_6.py", 'w', encoding='UTF-8')
f2.write(match)
f2.close()
import result_mg400_6
result_mg400_6.main()
