"""An agent implemented by assistant with qwen3"""
import os  # noqa

from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
from qwen_agent.utils.output_beautify import typewriter_print


def init_agent_service(llm_cfg):
    """
    Initializes a single, powerful CodeExpertAgent that uses tools to perform
    code analysis tasks, replacing the multi-agent GroupChat setup.
    """

    # 1. Define the tools that the CodeExpertAgent will use.
    # The functionalities of the former specialist agents are now encapsulated as tools.
    function_locator_tool = {
        'mcpServers': {
            'function_locator_by_ctag': {
                'url': 'http://127.0.0.1:1998/sse'
            }
        }
    }
    code_analyzer_tool = 'code_interpreter'

    # 2. Define the all-in-one CodeExpertAgent
    # This agent acts as the central orchestrator.
    code_expert_agent = Assistant(
        name='CodeExpertAgent',
        llm=llm_cfg,
        description='一个全能的代码专家，负责理解用户问题，自主规划并调用工具来解决代码相关问题。',
        # Provide all necessary tools to the agent
        function_list=[function_locator_tool, code_analyzer_tool],
        system_message="""你是全能的代码专家（CodeExpertAgent），是解决用户代码问题的唯一入口和总负责人。你的目标是利用你掌握的工具，自主规划并执行一系列步骤，最终为用户提供全面、准确的答案。

# 核心能力与工具

你掌握以下两大核心工具：

1.  **`function_locator_by_ctag`**: 函数定位器。
    *   **功能**: 根据一个精确的函数名和项目名，找出它在代码库中所有定义过的文件路径。
    *   **使用场景**: 当用户询问函数的**位置**、**定义**或**数量**时，这是你的第一步。
    *   **输入**: `{"project_name": "...", "function_name": "..."}`
    *   **输出**: 函数所在的文件路径列表。

2.  **`code_interpreter`**: 代码解释器与文件系统浏览器。
    *   **功能**:
        *   读取一个或多个文件的完整内容。
        *   列出一个目录的结构（例如，使用 `ls -R /path/to/dir`）。
    *   **使用场景**:
        *   在 `function_locator_by_ctag` 找到文件路径后，用它来**读取源代码**。
        *   当用户提供一个目录路径，让你分析整个目录时，用它来**探索目录结构**。
        *   在探索目录后，用它来逐一**读取感兴趣的文件**。
    *   **黄金法则**: 当你使用 `code_interpreter` 读取文件时，**必须**在脚本的最后一步使用 `print()` 函数将文件的**完整内容**输出到标准输出（stdout）。这是你获取分析所需信息的唯一途径。

# 工作流程与自主规划 (ReAct)

你将遵循一个“思考-行动-观察”的循环来解决问题。

1.  **理解与规划 (Thought)**:
    *   分析用户的请求，拆解成一个可执行的计划。
    *   **场景A：函数分析**
        *   用户问：“`Run` 函数是干什么的？”
        *   **你的计划**:
            1.  【行动】调用 `function_locator_by_ctag` 查找 `Run` 函数。
            2.  【行动】如果找到路径，调用 `code_interpreter` 读取每个文件。
            3.  【思考】综合代码内容，总结 `Run` 函数的功能、参数和返回值。
            4.  【回答】向用户提供总结。
    *   **场景B：目录分析**
        *   用户问：“分析一下 `qwen_agent/agents/` 目录。”
        *   **你的计划**:
            1.  【行动】调用 `code_interpreter` 执行 `ls -R qwen_agent/agents/` 来查看目录结构。
            2.  【思考】根据目录结构和文件名，判断哪些文件是核心文件。
            3.  【行动】调用 `code_interpreter` 逐一读取这些核心文件。
            4.  【思考】综合所有代码，总结该目录下的 Agent 的作用和关系。
            5.  【回答】向用户提供总结报告。

2.  **行动 (Action)**:
    *   根据你的计划，选择一个工具并提供格式正确的输入。
    *   `function_locator_by_ctag` 的输入**必须**是纯净的单行 JSON。
    *   `code_interpreter` 的输入是你要执行的 Python 或 Shell 代码。

3.  **观察 (Observation)**:
    *   查看工具的输出结果。这可能是文件路径、代码内容、目录列表或错误信息。

4.  **迭代与总结**:
    *   根据观察到的结果，更新你的计划。如果上一步成功，就执行计划的下一步。如果上一步失败或信息不足，就调整计划。
    *   例如，如果 `function_locator_by_ctag` 找不到函数，你可以尝试变换函数名的大小写（`Run` -> `run` -> `RUN`）然后重试。
    *   如果缺少 `project_name` 等信息，直接向用户提问。
    *   当所有信息收集完毕，进行最终的思考和总结，然后生成一个完整、清晰的答案给用户。你所有的工具调用和中间思考过程都不应直接展示给用户，用户只需要看到最终的完美答案。
""",
    )

    return code_expert_agent


def app_tui():
    """A simple text-based user interface for the agent."""
    # LLM and tool configuration
    llm_cfg = {
        'model': "qwen3-14b",
        'api_key': "sk-0c6022dc30624917ab361d33ed7084d4",
        'model_server': "https://dashscope.aliyuncs.com/compatible-mode/v1",
    }

    # Initialize the agent service
    bot = init_agent_service(llm_cfg)

    # Chat
    messages = []
    while True:
        query = input('user question: ')
        # Sanitize the input to remove invalid Unicode characters
        query = query.encode('utf-8', 'ignore').decode('utf-8')
        if not query.strip():
            continue
        messages.append({'role': 'user', 'content': query})

        response_plain_text = ''
        for response_chunk in bot.run(messages=messages):
            # The Assistant agent returns the full history, so we only need to
            # process and print the last message, which is the agent's response.
            if response_chunk:
                response_plain_text = typewriter_print(response_chunk[-1:], response_plain_text)
        
        # After the run is complete, the `bot.run` generator will have yielded the full
        # conversation history. We update our local messages to match this, so the
        # context for the next turn is correct.
        if response_chunk:
            messages = response_chunk

        print()

def app_gui():
    # LLM and tool configuration
    # It's recommended to use a powerful model like qwen-max for better planning
    # LLM and tool configuration
    llm_cfg = {
        'model': "qwen3-14b",
        'api_key': "sk-0c6022dc30624917ab361d33ed7084d4",
        'model_server': "https://dashscope.aliyuncs.com/compatible-mode/v1",
        'generate': {
            'top_p': 0.8,
            'max_retries': 10,
            'fncall_prompt_type': 'nous',
        },
    }
    # Define the agent
    bot = init_agent_service(llm_cfg)
    chatbot_config = {
        'prompt.suggestions': [
            '项目中名为 "Run" 的函数有几个？',
            '请分析一下 `qwen_agent/llm/` 这个目录是做什么的。',
            'qwen_agent/agents/assistant.py 文件中的 Assistant class 有什么用？'
        ]
    }
    WebUI(
        bot,
        chatbot_config=chatbot_config,
    ).run()


if __name__ == '__main__':
 
    app_gui()
