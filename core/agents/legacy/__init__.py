"""
遗留智能体组件 - 向后兼容

这个模块包含原有的智能体实现，主要用于向后兼容。
新项目建议使用新的模块化智能体架构。
"""

# 向后兼容的导入
from .search_agent import SearchAgent
from .multi_agent import MultiAgentSearchSystem as LegacyMultiAgentSearchSystem
from ..base.models import (
    AgentType, TaskType, TaskPriority, ExecutionStatus,
    AgentTask, AgentMessage
)
from .models import (
    AgentSearchRequest, AgentSearchResponse, AgentResult, ExecutionStatus
)

# 警告：这些是遗留组件
import warnings

def _legacy_warning():
    warnings.warn(
        "您正在使用遗留的智能体组件。建议迁移到新的模块化架构：\n"
        "from core.agents import MultiAgentSearchSystem, SearchSpecialistAgent",
        DeprecationWarning,
        stacklevel=3
    )

# 包装遗留类以添加警告
class SearchAgentWrapper(SearchAgent):
    def __init__(self, *args, **kwargs):
        _legacy_warning()
        super().__init__(*args, **kwargs)

# 导出包装后的类
SearchAgent = SearchAgentWrapper

__all__ = [
    'SearchAgent',
    'LegacyMultiAgentSearchSystem',
    'AgentType', 'TaskType', 'TaskPriority', 'ExecutionStatus',
    'AgentTask', 'AgentMessage', 'AgentSearchRequest', 'AgentSearchResponse', 'AgentResult',
]