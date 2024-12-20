import os

from openai import OpenAI

client = OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello, whats the time?"},
    ],
    stream=True
)

for chunk in response:
    delta_content = chunk.choices[0].delta.content
    buffer = []
    if delta_content:
        buffer.append(delta_content)
        print(delta_content, end="", flush=True)