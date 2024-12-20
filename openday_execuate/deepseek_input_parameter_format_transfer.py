import os
import sys

from openai import OpenAI
import re
import json


def format_input_parameter(
        prompt="pick_origin = [298, 194, 17, 0],From this point, there are two more objects spaced 25 units apart leftward. Then, "
               "to the downside of this point, At 26 units away, 26 units further, and another 26 units further "
               ", there are three more rows of objects arranged in the same pattern."
               "place_origin = [242, 283, 35, 0],From this point, there are three more objects spaced 25 units apart leftward. Then, "
               "to the upside of this point, at 26 units and another 26 units further, "
               "there are two more rows of objects arranged in the same pattern. Only tell me "
               "the pick & place points in groups."):
    print(prompt)
    client3 = OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com/beta")
    point_output_prompt = ("""Please output groups of points in JSON format.
    EXAMPLE INPUT:
    "points_pick = [[291, 10, 12, 0], [272, 12, 12, 0], [255, 13, 12, 0], [237, 14, 12, 0]],points_place =[[290, -178, 12, 0],
     [271, -177, 12, 0], [252, -177, 12, 0], [233, -177, 12, 0]]"
           EXAMPLE JSON OUTPUT:
           {
        "groups": [
            {
                "name": "pick",
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
                "name": "place",
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
        max_tokens=8192,
        temperature=0.0,
        stream=True
    )
    full_text = ""
    for chunk in pos_ask:
        pos_result = chunk.choices[0].delta.content
        if pos_result:
            full_text += pos_result
            print(pos_result, end="", flush=True)
    print()
    print("turning into json format...")
    pos_format = client3.chat.completions.create(
        model="deepseek-coder",
        messages=[
            {
                "role": "system",
                "content": point_output_prompt,
            },
            {
                "role": "user",
                "content": full_text + "Please provide "
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
    with open("generated_points.json", "r", encoding="utf-8") as file:
        source_data = json.load(file)
        source_data=source_data["groups"]
    with open("prompts_demo.json", "r", encoding="utf-8") as file:
        target_data = json.load(file)
    target_data["groups"] = source_data
    # 序列化时避免转义换行符
    with open("prompts_demo.json", "w", encoding="utf-8") as tgt:
        json.dump(target_data, tgt, ensure_ascii=False, indent=4)
    print()
    print("groups updated successfully!")

if __name__ == '__main__':
    args = sys.argv[1:]  # 获取从命令行传入的所有参数

    # 判断是否传入覆盖参数
    if len(args) >= 1:
        default_coordinates = args[0]  # 使用第一个命令行参数覆盖默认坐标
        format_input_parameter(default_coordinates)
    else:
        format_input_parameter()  # 调用函数，使用默认坐标
