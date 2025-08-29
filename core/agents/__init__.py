"""
E-WebSearch 多智能体系统

这个模块包含了完整的多智能体搜索系统，包括：
- 基础智能体组件
- 专门化智能体实现
- 协调和任务管理
- 推理和策略引擎
"""

# 基础组件
from .base.base_agent import BaseAgent
from .base.models import (
    AgentType, TaskType, TaskPriority, ExecutionStatus,
    AgentTask, AgentMessage, AgentSearchRequest, AgentSearchResponse, AgentResult
)
from .base.observability import ExecutionTracer, PerformanceMonitor, ResultLogger

# 专门化智能体
from .specialists.search_specialist import SearchSpecialistAgent
# TODO: 其他专门化智能体将在后续实现
# from .specialists.content_analyzer import ContentAnalyzerAgent
# from .specialists.result_synthesizer import ResultSynthesizerAgent
# from .specialists.quality_assessor import QualityAssessorAgent

# 协调和管理
from .coordination.coordinator import MultiAgentCoordinator
from .coordination.task_manager import TaskManager

# 推理和策略
from .reasoning.reasoning_engine import ReasoningEngine
from .reasoning.search_strategies import SearchStrategyManager
from .reasoning.result_processor import ResultProcessor

# 主要系统接口
from .multi_agent_system import MultiAgentSearchSystem

# 便捷导入 - 从协调器直接导入（用于高级用法）
from .coordination.coordinator import MultiAgentCoordinator

# 向后兼容（遗留组件） - 暂时注释，需要修复导入问题
# from .legacy.search_agent import SearchAgent

__all__ = [
    # 基础组件
    'BaseAgent',
    'AgentType', 'TaskType', 'TaskPriority', 'ExecutionStatus',
    'AgentTask', 'AgentMessage', 'AgentSearchRequest', 'AgentSearchResponse', 'AgentResult',
    'ExecutionTracer', 'PerformanceMonitor', 'ResultLogger',
    
    # 专门化智能体
    'SearchSpecialistAgent',
    # 'ContentAnalyzerAgent', 
    # 'ResultSynthesizerAgent',
    # 'QualityAssessorAgent',
    
    # 协调和管理
    'MultiAgentCoordinator',
    'TaskManager',
    
    # 推理和策略
    'ReasoningEngine',
    'SearchStrategyManager',
    'ResultProcessor',
    
    # 主要接口
    'MultiAgentSearchSystem',
    'MultiAgentCoordinator',
    
    # 向后兼容 - 暂时注释
    # 'SearchAgent',
]
