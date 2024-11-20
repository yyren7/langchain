# coding: utf8
from http import HTTPStatus
from dashscope import Application, Assistants, Messages, Runs, Threads
import broadscope_bailian
import json
import os


# -*- encoding: utf-8 -*-
def create_assistant():
    # create assistant with information
    assistant = Assistants.create(
        model="qwen-max",
        name='smart helper',
        description='一个智能助手，可以通过用户诉求，调用已有的插件能力帮助用户。',
        instructions='你是一个信息处理者，不会和用户进行二次交互。首先需要总结用户当前输入。然后根据已有插件补充用户的语句。'
                     '请按优先级依次查询下列情况：'
                     '1.若提及训练模型相关，必须调用获取训练模型情况插件，该调用无需询问用户具体模型情况，获取训练模型情况会返回所有结果，请都展示给用户。'
                     '2.若提及assistant-api，必须调用最佳实践查询插件，返回具体assistant-api的最佳实践代码链接，该调用无需询问用户。'
                     '3.若上述情况都没出现，还询问api-key相关，请返回他的apikey具体值。'
                     '请不要主动询问用户，任何潜在的调用请主动发起。',
        tools=[
            {
                'type': 'function',
                'function': {
                    'name': '最佳实践查询',
                    'description': '返回assistant-api相关的最佳实践代码链接',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'str',
                                'description': '用户id'
                            },
                        },
                        'required': ['user_id']},
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': '获取训练模型情况',
                    'description': '用于获取用户部署在百炼平台上用数据额外训练的模型情况。包含SFT模型的具体情况',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'str',
                                'description': '用户id'
                            },
                        },
                        'required': ['user_id']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': '应用创建情况',
                    'description': '可以查询应用相关信息。用于返回用户当前应用的具体创建情况，即用户路径下的应用创建数量和对应的id。',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'str',
                                'description': '用户id'
                            },
                        },
                        'required': ['user_id']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': '模型用量查询',
                    'description': '一个通用的超大规模语言模型用量查询接口，直接查询下所有模型（含通义千问）使用量。',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'str',
                                'description': '用户id'
                            },
                        },
                        'required': ['user_id']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'apikey查询',
                    'description': '用于apikey的具体值',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'str',
                                'description': '用户id'
                            },
                            'required': ['user_id']
                        }
                    }
                },
            },

        ],
    )

    return assistant


function_mapper = {
    "apikey查询": get_api_key,
    "获取训练模型情况": get_train_model,
    "应用创建情况": get_application,
    "最佳实践查询": get_code,
}

def send_message(assistant, message=''):
    print(f"Query: {message}")

    # create a thread.
    thread = Threads.create()
    print(thread)

    # create a message.
    message = Messages.create(thread.id, content=message)
    print(message)

    run = Runs.create(thread.id, assistant_id=assistant.id)
    print(run)

    # # get run statue
    # run_status = Runs.get(run.id, thread_id=thread.id)
    # print(run_status)

    # wait for run completed or requires_action
    run_status = Runs.wait(run.id, thread_id=thread.id)
    print('插件调用前：')
    print(run_status)
    if run_status.status == 'failed':
        print('run failed:')
        print(run_status.last_error)

    # if prompt input tool result, submit tool result.
    if run_status.required_action:

        f = run_status.required_action.submit_tool_outputs.tool_calls[0].function
        func_name = f['name']
        param = json.loads(f['arguments'])
        print(f)
        if func_name in function_mapper:
            output = function_mapper[func_name](**param)
        else:
            output = ""

        tool_outputs = [{
            'output':
                output
        }]

        run = Runs.submit_tool_outputs(run.id,
                                       thread_id=thread.id,
                                       tool_outputs=tool_outputs)

        # should wait for run completed
        run_status = Runs.wait(run.id, thread_id=thread.id)
        print(run_status)
        # verify_status_code(run_status)

    run_status = Runs.get(run.id, thread_id=thread.id)
    # print(run_status)
    # verify_status_code(run_status)

    # get the thread messages.
    msgs = Messages.list(thread.id)
    # print(msgs)
    # print(json.dumps(msgs, default=lambda o: o.__dict__, sort_keys=True, indent=4))

    print("运行结果:")
    for message in msgs['data'][::-1]:
        print("content: ", message['content'][0]['text']['value'])
    print("\n")


if __name__ == '__main__':
    assistant = create_assistant()

    # answer = call_rag_app(prompt='模型训练？') # example 1
    answer = call_rag_app(prompt='请问Assistant API如何创建？')  # example 2

    # 'assistant-api怎么使用'#output["text"]#call_rag_app(请问Assistant API如何创建？)
    user_config = os.environ["user_config"]
    send_message(assistant=assistant, message=user_config + answer)