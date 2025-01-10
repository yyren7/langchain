import os

from openai import OpenAI


def send_messages(messages):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools
    )
    return response.choices[0].message


client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com",
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "move_in_direction",
            "description": "Get new 6d position after vertical movement, the user should supply a 6d position first",
            "parameters": {
                "type": "object",
                "properties": {
                    "original_position": {
                        "type": "List[float]",
                        "description": "The original robot position",
                    }
                },
                "required": ["original_position"]
            },
        }
    },
]

messages = [{"role": "user", "content": "What is the position after move 10cm backward?"}]
message = send_messages(messages)
print(f"User>\t {messages[0]['content']}")

tool = message.tool_calls[0]
messages.append(message)

messages.append({"role": "tool", "tool_call_id": tool.id, "content": "24℃"})
message = send_messages(messages)
print(f"Model>\t {message.content}")

