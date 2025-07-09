from typing import Dict, Iterator, List, Optional, Union

from qwen_agent.agents.react_chat import ReActChat
from qwen_agent.llm import BaseChatModel
from qwen_agent.llm.schema import Message


class FunctionLocatorAgent(ReActChat):

    def __init__(self,
                 llm: Optional[Union[Dict, BaseChatModel]] = None,
                 system_message: Optional[str] = None,
                 function_list: Optional[List[Union[str, Dict]]] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 **kwargs):
        super().__init__(llm=llm,
                         system_message=system_message,
                         function_list=function_list,
                         name=name,
                         description=description,
                         **kwargs) 