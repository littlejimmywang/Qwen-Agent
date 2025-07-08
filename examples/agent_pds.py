"""An agent implemented by assistant with qwen3"""
import os  # noqa

from qwen_agent.agents import Assistant, ReActChat
#from qwen_agent.gui import WebUI
from qwen_agent.utils.output_beautify import typewriter_print


def init_agent_service():
    llm_cfg = {
            'model': 'qwen3',
        'api_key': 'vllm',
        'model_server': 'http://127.0.0.1:8000/v1',
        'generate': {
            'top_p': 0.8,
            'max_retries': 10,
            'fncall_prompt_type': 'nous',   
            },
    }
    # llm_cfg = {
    #     # Use the OpenAI-compatible model service provided by DashScope:
    #     'model': 'qwen3-235b-a22b',
    #     'model_server': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    #     'api_key': os.getenv('DASHSCOPE_API_KEY'),
    #
    #     # 'generate_cfg': {
    #     #     # When using Dash Scope OAI API, pass the parameter of whether to enable thinking mode in this way
    #     #     'extra_body': {
    #     #         'enable_thinking': False
    #     #     },
    #     # },
    # }
    # llm_cfg = {
    #     # Use your own model service compatible with OpenAI API by vLLM/SGLang:
    #     'model': 'Qwen/Qwen3-32B',
    #     'model_server': 'http://localhost:8000/v1',  # api_base
    #     'api_key': 'EMPTY',
    #
    #     'generate_cfg': {
    #         # When using vLLM/SGLang OAI API, pass the parameter of whether to enable thinking mode in this way
    #         'extra_body': {
    #             'chat_template_kwargs': {'enable_thinking': False}
    #         },
    #
    #         # Add: When the content is `<think>this is the thought</think>this is the answer`
    #         # Do not add: When the response has been separated by reasoning_content and content
    #         # This parameter will affect the parsing strategy of tool call
    #         # 'thought_in_content': True,
    #     },
    # }
    # tools = [
    #     {
    #         'mcpServers': {  # You can specify the MCP configuration file
    #             'time': {
    #                 'command': 'uvx',
    #                 'args': ['mcp-server-time', '--local-timezone=Asia/Shanghai']
    #             },
    #             'fetch': {
    #                 'command': 'uvx',
    #                 'args': ['mcp-server-fetch']
    #             },
    #             'PsdMcpServer': {
    #                'url': 'http://127.0.0.1:1998/sse'
    #             }
    #         }
    #     },
    #     'code_interpreter',  # Built-in tools
    # ]
    tools = [
		{
            'mcpServers': {  # You can specify the MCP configuration file
                # 'time': {
                #     'command': 'uvx',
                #     'args': ['mcp-server-time', '--local-timezone=Asia/Shanghai']
                # },
                # 'fetch': {
                #     'command': 'uvx',
                #     'args': ['mcp-server-fetch']
                # },
                'BugLocator': {
                   'url': 'http://127.0.0.1:1998/sse'
                }
            }
        },
        'code_interpreter',
    ]
    bot = ReActChat(llm=llm_cfg,
                    function_list=tools,
                    name='PDS Agent',
                    system_message="""你是pds agent,中文名字是火眼云瞻智能体, 一个全能AI助手, 旨在解决用户提出的任何任务. 你可以调用各种工具来高效完成复杂的请求. 无论是编程, 信息检索, 文件处理还是代码评审, 你都能处理. 

关于你的code_interpreter工具能力说明：
- 你可以通过编写Python脚本来读取、分析和处理各种文件，包括项目源代码文件(不限定语言)
- 你可以使用Python的os、pathlib、glob等库来遍历目录结构，查找特定文件
- 你可以使用open()函数或其他文件处理库来读取文本文件、代码文件等
- 你可以对读取的源代码进行分析、统计、搜索、格式化等各种处理
- 你具备完整的文件系统访问能力，可以处理任何可读的文件格式
- 当用户需要分析项目代码、读取配置文件、处理数据文件时，你应该主动使用Python脚本来完成
- 如果对任务感到困惑的时候,可以先列举出目标目录的结构,然后层层推进,直到读取到源文件

当用户询问关于特定函数的问题时，你应该遵循以下步骤：
1.  首先，使用 `function_locator_by_ctag` 工具，并提供 `project_name` 和 `function_name` 来查找该函数的具体文件路径。
2.  获取到文件路径后，使用 `code_interpreter` 工具通过完整路径读取该源文件的内容,不要局限于我问的函数,而是要拿到整个源文件的内容。
3.  最后，将完整的读取到的文件内加入上下文，据此回答用户关于该函数的问题。


请始终使用中文回答用户的问题.""",                    
                    description="pioneer deep scanner agent (火眼云瞻智能体). A versatile agent that can solve various tasks using multiple tools")

    return bot


def test(query: str = '你都有什么工具可以调用?'):
    # Define the agent
    bot = init_agent_service()

    # Chat
    messages = [{'role': 'user', 'content': query}]
    response_plain_text = ''
    for response in bot.run(messages=messages):
        response_plain_text = typewriter_print(response, response_plain_text)


#def app_tui():
#    # Define the agent
#    bot = init_agent_service()
#
#    # Chat
#    messages = []
#    while True:
#        query = input('user question: ')
#        messages.append({'role': 'user', 'content': query})
#        response = []
#        response_plain_text = ''
#        for response in bot.run(messages=messages):
#            response_plain_text = typewriter_print(response, response_plain_text)
#        messages.extend(response)

def app_tui():
    # Define the agent
    bot = init_agent_service()

    # Chat
    messages = []
    while True:
        query = input('user question: ')
        # Sanitize the input to remove invalid Unicode characters
        query = query.encode('utf-8', 'ignore').decode('utf-8')
        messages.append({'role': 'user', 'content': query})
        response = []
        response_plain_text = ''
        for response in bot.run(messages=messages):
            response_plain_text = typewriter_print(response, response_plain_text)
        # Add a newline after the assistant's response is fully printed
        print()
        messages.extend(response)

# def app_gui():
#     # Define the agent
#     bot = init_agent_service()
#     chatbot_config = {
#         'prompt.suggestions': [
#             'What time is it?',
#             'https://github.com/orgs/QwenLM/repositories Extract markdown content of this page, then draw a bar chart to display the number of stars.'
#         ]
#     }
#     WebUI(
#         bot,
#         chatbot_config=chatbot_config,
#     ).run()


if __name__ == '__main__':
    #test()
    app_tui()
    #app_gui()
