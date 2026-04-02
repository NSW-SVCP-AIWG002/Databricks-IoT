import operator

from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class AgentState(TypedDict, total=False):
    arrived_count: int
    next_api_index:int
    prompt: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
    genie_conversation_info: List[str]
    genie_download_url: str
    sql_query: str
    dataframe: Optional[str]
    space: str
    fig_data: Optional[str]
    need_LLM: bool
    selected_apis: List[Dict[str, Any]]
    current_prompt: str
    Error: bool
    need_new_genie_data: bool