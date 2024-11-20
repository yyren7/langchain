from pathlib import Path
from openai import OpenAI
import numpy as np

client1 = OpenAI(
    api_key="sk-ODvoPZ9Heq4sRY34U5TwK2XCrrlbKMhosVSVm6JCxNhQhSuy",
    base_url="https://api.moonshot.cn/v1",
)

'''
file_basic = client1.files.create(file=Path("fr_basic.pdf"), purpose="file-extract")
file_move = client1.files.create(file=Path("fr_move.pdf"), purpose="file-extract")

file_robot_config = client1.files.create(file=Path("resources/document/fr_robot_config.pdf"), purpose="file-extract")
file_kinetic_control = client1.files.create(file=Path("resources/document/fr_kinetic_control.pdf"), purpose="file-extract")
'''
file_robot_status = client1.files.delete(file_id="cstdjkb5cfusk9hnferg", purpose="file-extract")
'''
file_content1 = client1.files.content(file_id=file_basic.id).text
file_content2 = client1.files.content(file_id=file_move.id).text
'''

file_content6 = client1.files.content(file_id=file_robot_status.id).text
print(file_content6)
np.save("6", file_content6)

