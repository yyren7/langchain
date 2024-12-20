import subprocess
position_prompt = ("The original position is[298, 199, 14, 0],From this point, there are three more objects spaced 20 "
                   "units apart leftward. Then, to the downside of this point, at 20 units and another 20 units "
                   "further, there are two more rows of objects arranged in the same pattern. Please tell me these "
                   "points in groups.To determine the groups of points based on the given description, we can break "
                   "down the problem step by step.")
result = subprocess.run(['python', 'deepseek_input_parameter_format_transfer.py', position_prompt],
                                    capture_output=True,
                                    text=True, check=True)
print(result.stdout)




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
response = client3.chat.completions.create(
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
            "content": "api内部构造：" + api,
        },
        {
            "role": "system",
            "content": "接口代码："+api_code,
        },
"""

content_mg400_chatgpt = ("该助手通过使用上方提供的api生成机器人抓取和放置任务python代码。"
                         "严格遵守api的使用方法，使用api的相关函数。任务开始时启动机器人并且等待两秒。速度调整到最大速度的百分之八十，每一步之间间隔100ms。"
                         "对于抓取和放置任务：假设有k个抓取坐标。1，计算抓取和放置坐标的开始位置，该位置为实际抓取和放置坐标的上方20cm。"
                         "2，先到达抓取开始坐标，然后向正方向下移20cm。"
                         "3，用mg400_api里的相关函数启动指定数字输出。4，从当前位置上升20cm。5，移动到放置坐标，然后向正方向下移20cm。"
                         "6，用mg400_api里的相关函数关闭指定数字输出。7，返回字符串“第“+k+“个任务完成”。根据用户要求无限重复上述任务。")
