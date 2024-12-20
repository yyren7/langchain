from openai import OpenAI
import os
import sys
import numpy as np
import json

# 设置 API 密钥
client2 = OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")
client1 = OpenAI(
    api_key=os.getenv('MOONSHOT_API_KEY'),
    base_url="https://api.moonshot.cn/v1",
)

folder_path = '/hik_vision/Python'  # 请替换为您的文件夹路径

# 遍历文件夹中的所有文件
for root, dirs, files in os.walk(folder_path):
    for d in dirs:
        for filename in files:
            file_path = os.path.join(root, filename)
            print(d)
            print(filename)
        '''
        # 打开并读取文件内容
        with open(file_path, 'rb') as file:
            file_content = file.read()
            # 上传文件到 Kimi 平台
            response = client1.files.create(
                file=file_content,
                purpose='file-extract'
            )
        
        file_content = client1.files.content(file_id=response.id).text
        # 获取文件 ID
        file_id = response['id']
        with open(filename+'.json', 'w', encoding='utf-8') as file:
            json.dump(file_content, file, ensure_ascii=False, indent=4)
        print(f"文件 {filename} 上传成功，文件 ID：{file_id}")
        # 在此处添加对文件的进一步处理逻辑'''
