"""An agent implemented by assistant with qwen3"""
import os  # noqa

from qwen_agent.agents import Assistant, GroupChat, Router
from qwen_agent.agents.code_reader_agent import CodeReaderAgent
from qwen_agent.agents.code_expert_agent import CodeExpertAgent
from qwen_agent.agents.dialogue_agent import DialogueAgent
from qwen_agent.agents.function_locator_agent import FunctionLocatorAgent
from qwen_agent.gui import WebUI
from qwen_agent.utils.output_beautify import typewriter_print


def init_agent_service(llm_cfg):
    """Initializes the specialized GroupChat for autonomous code analysis."""

    # 1. Define tools for the workflow
    function_locator_tool = {
        'mcpServers': {
            'function_locator_by_ctag': {
                'url': 'http://127.0.0.1:1998/sse'
            }
        }
    }
    code_analyzer_tool = 'code_interpreter'

    # 2. Define the agents that form the autonomous workflow
    function_locator_agent = FunctionLocatorAgent(
        name='FunctionLocatorAgent',
        llm=llm_cfg,
        description='一个函数定位专家，负责根据函数名找出其定义的文件路径或统计其数量。注意：我只负责“找路”，不负责“看路上的风景”（即不读取代码内容）。',
        function_list=[function_locator_tool],
        system_message="""你是函数定位专家(FunctionLocatorAgent)。

# 核心能力
你能调用 `function_locator_by_ctag` 工具，根据一个**精确的函数名**，找出它在项目代码库中所有定义过的文件路径。

# 目标
你的首要任务是**理解用户的真实意图**，然后利用你的核心能力来回答关于函数**位置**或**数量**的问题。

# 工作流程
1.  **分析请求**: 当被`@`时，或作为第一个响应者时，分析用户的最新问题。
    *   如果问题是关于“**有多少个**”或“**统计数量**”（例如：“项目里有几个 Run 函数？”），你的任务就是调用工具，然后**直接回答路径的数量**。
    *   如果问题是关于“**在哪里**”或“**列出位置**”（例如：“Run 函数定义在哪些文件里？”），你的任务就是调用工具，然后**列出所有返回的文件路径**。
    *   如果问题是关于“**是什么**”、“**做什么**”或需要**理解代码内容**（例如：“Run 函数是干嘛的？”），在找到路径后，你的任务就完成了。在你的最终回答中，请清晰地列出找到的路径，并直接 @CodeReaderAgent 来进行下一步的源码读取和分析。例如： "我找到了 `Run` 函数，它在这里：/path/to/file.go。@CodeReaderAgent，请你来分析一下这个文件。" **这只是一个输出文本，不是工具调用。**
    *   如果执行任务缺少必要参数（如 `project_name`），直接在你的回答中 @CodeExpertAgent。

2.  **处理函数名**: 在调用工具前，如果 `function_name` 大小写可能不匹配，请按顺序尝试以下变换，直到成功或用尽次数：`原样` -> `首字母大写` -> `全大写`。

3.  **最终输出**: 根据第1步分析的意图，生成你的最终答案。要么是数量，要么是路径列表，要么是移交给其他 Agent 的指令。

# 黄金法则
*   **`Action Input` 格式**：当你决定调用工具时，为 `Action Input` 生成的内容**必须**是一个**纯净、单行、没有任何 Markdown 标记（例如 ```json）的 JSON 字符串**。

    *   **正确示例**: `{"project_name": "duration-billing", "function_name": "RunBandwidth"}`
    *   **错误示例**: ` ```json\n{\n  "project_name": "duration-billing",\n  "function_name": "RunBandwidth"\n}\n``` `

# 兜底策略
如果连续尝试后工具调用依然失败或未找到任何路径，应明确告知用户`[FAILED] 无法定位函数 <function_name>`，并直接在回答中 @CodeExpertAgent 进行分析。
""",
    )

    code_reader_agent = CodeReaderAgent(
        name='CodeReaderAgent',
        llm=llm_cfg,
        description='一个代码读取专家。当需要深入分析、阅读或引用具体源代码或者代码所在目录时，总调度员应选择我，尤其是在文件或目录路径已知或已在上下文中提及时。',
        function_list=[code_analyzer_tool],
        system_message="""你是代码读取专家(CodeReaderAgent)。

# 目标
读取指定文件或逐个读取多个文件或分析目录，并将上下文交给`CodeExpertAgent`。

# 工作流程 (ReAct)
1. 等待其他 Agent @你，并提供**单个文件路径**或**多个文件路径**或**目录路径**。
2. **行动**: 根据路径类型，使用`code_interpreter`读取文件或逐个读取多个文件或分析目录或读目录下所有的文件，如果在用户的提问以及你的运行中中渐渐发现了更多关心的文件，请继续读取其源代码。

   **黄金法则：** 当你使用 `code_interpreter` 读取文件时，**必须**在脚本的最后一步使用 `print()` 函数将文件的**完整内容**输出到标准输出（stdout）。这是你获取分析所需信息的唯一途径。**绝对禁止**只打印‘成功’、‘已读取’或任何形式的确认消息，因为这会导致你无法看到源码而产生幻觉。

3. **兜底**: 如果路径不存在或权限不足，**重试 1 次**。仍失败则输出`[FAILED] 无法访问路径 <path>。`并直接在回答中 @CodeExpertAgent。
4. **成功后**: 在你的最终回答中，附上代码内容或你的分析摘要，并 @CodeExpertAgent 来进行最终解读。
""",
    )

    code_expert_agent = CodeExpertAgent(
        name='CodeExpertAgent',
        llm=llm_cfg,
        description='一个代码解读专家，负责综合所有上下文，生成最终的、高质量的答案，并在必要时向用户请求缺失信息。',
        system_message="""你是代码解读专家(CodeExpertAgent)，是团队的最终回答生成者和对外沟通者。

# 目标
1.  **生成最终答案**: 整合所有上下文信息（用户原始问题、其他Agent的成功结果或失败信息），产出面向用户的、专业且完整的最终答案。
2.  **对外沟通**: 如果团队在执行任务的任何环节**缺少必要参数**（例如，`FunctionLocatorAgent`报告缺少`project_name`），你的职责是**直接向用户提问**，以获取这些缺失的信息。你的提问应该清晰、简短。

# 记忆与上下文
*   在生成任何回答之前，**必须**先回顾整个对话历史。
*   如果之前的步骤中已经成功获取了信息（例如，`FunctionLocatorAgent` 已返回了文件路径，`CodeReaderAgent` 已返回了代码内容），**必须**直接利用这些已知信息，而不是要求重新获取或假装不知道。
*   你的核心价值在于**整合**和**总结**，而不是重复劳动。

# 工作流程
1.  **回顾历史**: 回顾整个对话历史，理解用户原始意图以及之前步骤的上下文。
2.  **判断状态**:
    *   **任务成功**: 如果前面的Agent已成功执行并提供了所需信息（如代码内容、路径列表），请结合这些信息生成详尽的答案或分析报告。
    *   **任务失败（缺少参数）**: 如果有Agent报告因缺少参数而失败，**你的唯一任务是向用户提问**。例如：“好的，我需要知道项目的名称才能继续。请问您想在哪个项目中查找？”
    *   **任务失败（其他原因）**: 如果是其他类型的失败，请向用户解释失败原因，并提供清晰的调试建议。
3.  **生成回答**: 你的回答是直接面向用户的，必须清晰、完整、结构化。
""",
    )

    # 3. Create a GroupChat to manage the autonomous workflow
    # This GroupChat now directly serves the user.
    workflow_agent = GroupChat(
        agents=[function_locator_agent, code_reader_agent, code_expert_agent],
        llm=llm_cfg
    )
    return workflow_agent


def app_tui():
    """A simple text-based user interface for the agent."""
    # LLM and tool configuration
    llm_cfg = {
        'model': "qwen3-235b-a22b",
        'api_key': "sk-0c6022dc30624917ab361d33ed7084d4",
        'model_server': "https://dashscope.aliyuncs.com/compatible-mode/v1",
        'generate': {
            'top_p': 0.8,
            'max_retries': 10,
            'fncall_prompt_type': 'nous',
        },
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
        response_chunk_all = []
        for response_chunk in bot.run(messages=messages):
            response_chunk_all.extend(response_chunk)
            # We only print the last message of the response chunk to avoid repetition
            if response_chunk:
                response_plain_text = typewriter_print(response_chunk[-1:], response_plain_text)

        # After the workflow is complete, append only the last, user-facing message to history.
        # This prevents the context from bloating with internal dialogues and source code.
        if response_chunk_all:
            messages.append(response_chunk_all[-1])

        print()

# if __name__ == '__main__':
#     app_tui()


def app_gui():
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
            'What time is it?',
            'https://github.com/orgs/QwenLM/repositories Extract markdown content of this page, then draw a bar chart to display the number of stars.'
        ]
    }
    WebUI(
        bot,
        chatbot_config=chatbot_config,
    ).run()


if __name__ == '__main__':
    # test()
    # app_tui()
    app_gui()