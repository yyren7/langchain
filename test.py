from openai import OpenAI
import os
# user should set `base_url="https://api.deepseek.com/beta"` to use this feature.
client = OpenAI(
  api_key=os.environ["DEEPSEEK_API_KEY"],
  base_url="https://api.deepseek.com/beta",
)
response = client.completions.create(
  model="deepseek-chat",
  prompt="def fib(a):",
  suffix="return fib(a-1) + fib(a-2)",
  max_tokens=128)
print(response.choices[0].text)