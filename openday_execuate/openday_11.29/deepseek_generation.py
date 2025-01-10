import os
import sys

from openai import OpenAI
import re
import json
import deepseek_input_parameter_format_transfer as input_generator

client3 = OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com/beta")
# 把它放进请求中
content2 = ("该助手通过使用上方提供的api生成机器人控制python代码，开始时启动机器人并且等待两秒，结束时关闭机器人。"
            "对于抓取和放置任务，首先分别用抓取关节坐标和放置关节坐标通过正运动学API计算出其六维坐标。"
            "然后通过move_in_direction函数计算以当前朝向为基准向方向移动-10厘米后的新抓取和放置坐标。"
            "然后，先到达新抓取位置，用jog命令以工具坐标为基准向z正方向前移10cm再后退，再到达新放置位置，同样前移10cm再后退。")

content_mg400 = ("该助手通过使用上方提供的api，仿照示例程序，生成机器人抓取和放置任务python代码。"
                 "必须理解api内部构造，必须使用from dobot_api import DobotApiDashboard, DobotApi,DobotApiMove 和 def connect_robot()。"
                 "任务开始时必须启动机器人并且等待两秒，机器人速度调整到最大速度的百分之一百。"
                 "严格遵守api的使用方法，只能使用api里的函数生成程序，请确保不要使用任何其他未列出的函数，否则会导致错误。"
                 "每一次运动指令执行后，必须用同步命令保证到达指定位置后解锁下一步，否则会导致程序和机器人运动不一致。")

content_mg400_pick_and_place = ("抓取和放置任务：假设有k个抓取坐标。1，先到达抓取开始坐标正上方20cm，然后向正方向下移20cm。"
                                "2，用mg400_api里的相关函数启动指定数字输出。3，从当前位置上升20cm。4，移动到放置坐标正上方20cm，然后从当前位置向正方向下移20cm。"
                                "5，用mg400_api里的相关函数关闭指定数字输出。6，从当前位置上升20cm。7，返回字符串“第k个任务完成”。"
                                "遍历完成所有任务后，清零k的值，返回字符串“任务完成”。从头开始重复该程序。")

content_mg400_code_check = ("分析并报告该程序中每一行代码中使用的DobotApiDashboard, DobotApi,"
                            "DobotApiMove的函数，是否存在于api文档DobotApiDashboard, DobotApi,DobotApiMove各自的函数列表中，"
                            "要求调用函数名，参数的个数和类型都必须严格对应。"
                            "如果存在错误，报告出现错误的位置，并提供修改后的程序。")

content_mg400_en = ("This assistant generates Python code for robot pick-and-place tasks by using the provided API "
                    "and following the example program. It must understand the internal structure of the API and use "
                    "the following imports: from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove and "
                    "def connect_robot() with right ip and port.At the start of the task, the robot must be activated, and there should be a "
                    "2-second wait. The robot's speed should be adjusted to 50% of its maximum speed.Strict "
                    "adherence to the API usage methods is required, and only the functions provided in the API "
                    "should be used to generate the program. Do not use any other unspecified functions, as this will "
                    "cause errors.After each motion command, a synchronization command must be used to ensure the "
                    "robot reaches the specified position before unlocking the next step. Otherwise, it will result "
                    "in discrepancies between the program and the robot's movement.")

content_mg400_pick_and_place_en = ('Pick-and-place task: Assume there are k pick coordinates.'
                                   '1.First, move to a position 20 cm directly above the starting pick coordinate, then move 20 cm downward.'
                                   '2.Use the relevant function from mg400_api to activate the specified digital output.'
                                   '3.Ascend 20 cm from the current position.'
                                   '4.Move to a position 20 cm directly above the placement coordinate, then move 20 cm downward.'
                                   '5.Use the relevant function from mg400_api to deactivate the specified digital output.'
                                   '6.Ascend 20 cm from the current position.'
                                   '7.Return the string [Task k completed] for the k-th task.'
                                   'After completing all tasks in the loop, reset the value of k to zero and return the string [All tasks completed]. '
                                   'Repeat this program from the beginning.')

code_check_example_en = ("Sync() belongs to the DobotApiMove class, not the DobotApi class.SpeedFactor() belongs to "
                         "the DobotApiDashboard class, not the DobotApiMove class.  The MovL and MovJ commands"
                         "must accept four individual numerical values rather than an array.")

content_mg400_code_check_en = (" Analyze and report whether each line of code in the program uses functions from "
                               "DobotApiDashboard, DobotApi, and DobotApiMove that exist in their respective function "
                               "lists as documented in the API.The function names, number of parameters, "
                               "and parameter types must strictly match the API documentation.If there are any "
                               "errors, report the locations of the errors and provide a corrected version of the "
                               "program.For example:" + code_check_example_en)

ip = "ip=192.168.250.101"
with open("prompts_demo.json", "r", encoding="utf-8") as file:
    source_data = json.load(file)
    source_data = source_data["groups"]
show_pos = source_data
DO = "DO=1"
end_pos = "pos_end = [192, 304, 80, 0]"
user_input = "pick the objects and place them in the specified positions." + ip + DO
positions = show_pos

magic = str(open('../../langchain/magic.txt'))

api_description = str(json.load(open('../../dobot_robot/api_description.json', 'rb')))

api_code = (str(open("../../dobot_robot/TCP-IP-4Axis-Python/PythonExample.py")))
api = (str(open("../../dobot_robot/TCP-IP-4Axis-Python/dobot_api.py")))
example = (str(open("../../dobot_robot/TCP-IP-4Axis-Python/main_mg400.py")))

object_pos = ("pos_object = "
              "[[291, 10, 12, 0], [272, 12, 12, 0],"
              " [255, 13.5, 12, 0], [237, 14, 12, 0], "
              "[290, -178, 12, 0], [271, -177, 12, 0], "
              "[252, -177, 12, 0], [233, -177, 12, 0]]")

pos_new = "z=10,pos_end = [158, 234, 86, 21],DO=1"
pos_transfer = "ip=192.168.250.101 , pos_object = [291, 10, 12, 0],pos_end = [158, 234, 36, 21],DO=1"


def file_writer(f2, assistant_reply):
    f2.write(assistant_reply)
    f2.close()


def code_generator(robot_prompt=content_mg400_en, task_prompt=content_mg400_pick_and_place_en, user_prompt=user_input,
                   position_information=positions, code_check_prompt=content_mg400_code_check_en):
    system_messages = [
        {"role": "system", "content": "python example：" + api_code},
        {"role": "system", "content": "program example：" + example},
        {"role": "system", "content": robot_prompt},
    ]

    # 保存会话历史
    conversation_history = system_messages[:]

    # 模拟多轮对话
    for i in range(2):

        full_text = ""
        # 构造用户消息
        if i == 0:
            print("code generation running...")
            user_input = task_prompt + user_prompt + position_information
        elif i == 1:
            user_input = "api file:" + api + code_check_prompt
        else:
            user_input = input("input：")
        user_message = {"role": "user", "content": user_input}
        conversation_history.append(user_message)

        # 调用 API 获取回复
        response = client3.chat.completions.create(
            model="deepseek-coder",
            messages=conversation_history,
            max_tokens=8192,
            temperature=0.0,
            stream=True
        )

        # 确保正确访问返回对象的内容
        # 如果 `response` 是对象而不是字典，使用属性访问法
        for chunk in response:
            pos_result = chunk.choices[0].delta.content
            if pos_result:
                full_text += pos_result
                print(pos_result, end="", flush=True)

        assistant_reply = full_text

        if i == 0:
            print("code generation finished.")
            f2 = open("openday_execuate/generation_result.txt", 'w', encoding='UTF-8')
            file_writer(f2, assistant_reply)
            print("code check running...")
        if i == 1:
            f2 = open("openday_execuate/correction_result.txt", 'w', encoding='UTF-8')
            file_writer(f2, assistant_reply)
            print("code check finished.")
        # 将回复添加到会话历史
        conversation_history.append({"role": "assistant", "content": assistant_reply})

        if user_input.lower() in ["exit", "quit"]:
            break
    f2 = open("openday_execuate/correction_result.txt", 'r', encoding='UTF-8')
    assistant_reply = f2.read()
    f2.close()
    # 定义正则表达式模式，使用 re.DOTALL 使 '.' 匹配包括换行符在内的所有字符
    pattern = r"```python(.*?)```"
    match = re.findall(pattern, assistant_reply, re.DOTALL)[0]

    print(match)

    f2 = open("openday_execuate/result_mg400_en.py", 'w', encoding='UTF-8')
    f2.write(match)
    f2.close()

    print("program fixed successfully.")
    # import result_mg400_en1  # 导入生成的程序

    # result_mg400_en1.main()


if __name__ == '__main__':
    # print('Number of arguments:', len(sys.argv), 'arguments.')
    # print('Argument List:', str(sys.argv))
    args = sys.argv[1:]  # 获取从命令行传入的所有参数
    # 判断是否传入覆盖参数
    if args[0] != "" and args[1] != "" and args[2] != "" and args[3] != "" and args[4] != "":

        robot_prompt = args[0]  # 使用第一个命令行参数覆盖默认坐标
        position_information = args[1]  # 使用第一个命令行参数覆盖默认坐标
        user_prompt = args[2]  # 使用第一个命令行参数覆盖默认坐标
        task_prompt = args[3]  # 使用第一个命令行参数覆盖默认坐标
        code_check_prompt = args[4]  # 使用第一个命令行参数覆盖默认坐标

        code_generator(robot_prompt, position_information, user_prompt, task_prompt, code_check_prompt)
    else:
        print("prompts not enough.")
