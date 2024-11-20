import re
with open("result_mg400_1.txt", 'r', encoding='utf-8') as file:
    content = file.read()
# 定义正则表达式模式，使用 re.DOTALL 使 '.' 匹配包括换行符在内的所有字符
print(content)
pattern = r"```python(.*?)```"
match = re.findall(pattern, content, re.DOTALL)[0]
f2 = open("result_mg400_1.py", 'w', encoding='UTF-8')
f2.write(match)
f2.close()