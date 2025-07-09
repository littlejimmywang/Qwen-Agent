from typing import Dict, Optional, Union

from qwen_agent.agents.assistant import Assistant
from qwen_agent.llm import BaseChatModel


class CodeExpertAgent(Assistant):

    def __init__(self,
                 llm: Optional[Union[Dict, BaseChatModel]] = None,
                 system_message: Optional[str] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 **kwargs):
        super().__init__(llm=llm,
                         system_message=system_message,
                         name=name,
                         description=description,
                         **kwargs) 