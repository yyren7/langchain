import subprocess
import sys

from openai import OpenAI
import re
import json

'''
result = subprocess.run(['python', 'deepseek_input_parameter_format_transfer.py', position_prompt],
                                    capture_output=True,
                                    text=True, check=True)
print(result.stdout)
'''

# 示例代码

robot_prompt = "This assistant generates Python code for robot pick-and-place tasks by using the provided API and following the example program. It must understand the internal structure of the API and use the following imports: from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove and def connect_robot() with right ip and port..At the start of the task, the robot must be activated, and there should be a 2-second wait. The robot's speed should be adjusted to 50% of its maximum speed.Strict adherence to the API usage methods is required, and only the functions provided in the API should be used to generate the program. Do not use any other unspecified functions, as this will cause errors.After each motion command, a synchronization command must be used to ensure the robot reaches the specified position before unlocking the next step. Otherwise, it will result in discrepancies between the program and the robot's movement."
position_information = ("[{'name': 'pick', 'coordinates': [{'x': '295', 'y': '196', 'z': '15', 'r': '0'}, {'x': '274', "
                        "'y': '196', 'z': '15', 'r': '0'}, {'x': '253', 'y': '196', 'z': '15', 'r': '0'}, "
                        "{'x': '295', 'y': '175', 'z': '15', 'r': '0'}, {'x': '274', 'y': '175', 'z': '15', "
                        "'r': '0'}, {'x': '253', 'y': '175', 'z': '15', 'r': '0'}, {'x': '295', 'y': '154', "
                        "'z': '15', 'r': '0'}, {'x': '274', 'y': '154', 'z': '15', 'r': '0'}, {'x': '253', "
                        "'y': '154', 'z': '15', 'r': '0'}, {'x': '295', 'y': '133', 'z': '15', 'r': '0'}, "
                        "{'x': '274', 'y': '133', 'z': '15', 'r': '0'}, {'x': '253', 'y': '133', 'z': '15', "
                        "'r': '0'}]}, {'name': 'place', 'coordinates': [{'x': '242', 'y': '283', 'z': '15', "
                        "'r': '0'}, {'x': '221', 'y': '283', 'z': '15', 'r': '0'}, {'x': '200', 'y': '283', "
                        "'z': '15', 'r': '0'}, {'x': '179', 'y': '283', 'z': '15', 'r': '0'}, {'x': '242', "
                        "'y': '304', 'z': '15', 'r': '0'}, {'x': '221', 'y': '304', 'z': '15', 'r': '0'}, "
                        "{'x': '200', 'y': '304', 'z': '15', 'r': '0'}, {'x': '179', 'y': '304', 'z': '15', "
                        "'r': '0'}, {'x': '242', 'y': '325', 'z': '15', 'r': '0'}, {'x': '221', 'y': '325', "
                        "'z': '15', 'r': '0'}, {'x': '200', 'y': '325', 'z': '15', 'r': '0'}, {'x': '179', "
                        "'y': '325', 'z': '15', 'r': '0'}]}]")
code_check_prompt = " Analyze and report whether each line of code in the program uses functions from DobotApiDashboard, DobotApi, and DobotApiMove that exist in their respective function lists as documented in the API.The function names, number of parameters, and parameter types must strictly match the API documentation.If there are any errors, report the locations of the errors and provide a corrected version of the program.1.Sync() belongs to the DobotApiMove class or move, not the DobotApi class or feed. 2.SpeedFactor() belongs to the DobotApiDashboard class, not the DobotApiMove class.3.The MovL and MovJ commands must accept four individual numerical values rather than an array.4.The ip address must be correct."
task_prompt = ('Pick-and-place task: Assume there are k pick coordinates.''1.First, move to a position 40 cm directly above the starting pick coordinate, then move 40 cm downward.''2.Use the relevant function from mg400_api to activate the specified digital output.'
                                   '3.Ascend 40 cm from the current position.'
                                   '4.Move to a position 40 cm directly above the placement coordinate, then move 40 cm downward.'
                                   '5.Use the relevant function from mg400_api to deactivate the specified digital output.'
                                   '6.Ascend 40 cm from the current position.'
                                   '7.Return the string [Task k completed] for the k-th task.'
                                   '8.After completing all tasks in the loop, reset the value of k to zero and return the string [All tasks completed]. '
                                   '9.Exchange the pick positions and place locations with each other.Repeat this program from the beginning forever.')
user_prompt = "pick the objects and place them in the specified positions. Provided IP adress = 192.168.250.101. DO=1."
import subprocess

# 示例命令
command = ['python', 'deepseek_generation.py', robot_prompt, position_information, user_prompt,
           task_prompt, code_check_prompt]
result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

while True:
    output = result.stdout.readline()
    if output == '' and result.poll() is not None:
        break
    if output:
        print(output.strip())
