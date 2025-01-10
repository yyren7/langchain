import sys

from openai import OpenAI
import re
import json


def format_input_parameter(
                           prompt="[298, 199, 14, 0],From this point, there are three more objects spaced 18 units apart leftward. Then, "
                                  "to the downside of this point, at 188 units and another 188 units further, "
                                  "there are two more rows of objects arranged in the same pattern. Please tell me "
                                  "these points in groups."):
    print(prompt)
    client3 = OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com/beta")
    point_output_prompt = ("""Please output groups of points in JSON format.
    EXAMPLE INPUT:
    "points_start = [[291, 10, 12, 0], [272, 12, 12, 0], [255, 13, 12, 0], [237, 14, 12, 0]],points_end =[[290, -178, 12, 0],
     [271, -177, 12, 0], [252, -177, 12, 0], [233, -177, 12, 0]]"
           EXAMPLE JSON OUTPUT:
           {
        "groups": [
            {
                "name": "start",
                "coordinates": [
                    {
                        "number": "1",
                        "x": "291",
                        "y": "10",
                        "z": "12",
                        "r": "0"
                    },
                    {
                        "number": "2",
                        "x": "272",
                        "y": "12",
                        "z": "12",
                        "r": "0"
                    },
                    {
                        "number": "3",
                        "x": "255",
                        "y": "13",
                        "z": "12",
                        "r": "0"
                    },
                    {
                        "number": "4",
                        "x": "237",
                        "y": "14",
                        "z": "12",
                        "r": "0"
                    }
                ]
            },
            {
                "name": "end",
                "coordinates": [
                    {
                        "number": "1",
                        "x": "291",
                        "y": "-177",
                        "z": "12",
                        "r": "0"
                    },
                    {
                        "number": "2",
                        "x": "272",
                        "y": "-177",
                        "z": "12",
                        "r": "0"
                    },
                    {
                        "number": "3",
                        "x": "255",
                        "y": "-177",
                        "z": "12",
                        "r": "0"
                    },
                    {
                        "number": "4",
                        "x": "237",
                        "y": "-177",
                        "z": "12",
                        "r": "0"
                    }
                ]
            }
        ]
    }
    """)
    pos_ask = client3.chat.completions.create(
        model="deepseek-coder",
        messages=[
            {
                "role": "system",
                "content": "The user will ask for groups of points.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_tokens=2048,
        temperature=0.0,
        stream=False
    )
    pos_result = pos_ask.choices[0].message.content
    print(pos_result)
    pos_format = client3.chat.completions.create(
        model="deepseek-coder",
        messages=[
            {
                "role": "system",
                "content": point_output_prompt,
            },
            {
                "role": "user",
                "content": pos_result + "Please provide "
                                        "the coordinates of all these points in JSON format.",
            },
        ],
        max_tokens=2048,
        temperature=0.0,
        stream=False,
        response_format={
            'type': 'json_object'
        }
    )
    pos_format_result = pos_format.choices[0].message.content

    f2 = open("generated_points.json", 'w', encoding='UTF-8')
    f2.write(pos_format_result)
    f2.close()


if __name__ == '__main__':
    args = sys.argv[1:]  # 获取从命令行传入的所有参数

    # 判断是否传入覆盖参数
    if len(args) >= 1:
        default_coordinates = args[0]  # 使用第一个命令行参数覆盖默认坐标


    # 调用函数并覆盖默认值
    format_input_parameter(default_coordinates)
