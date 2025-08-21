"""
Search Agent 核心模块

实现基于规划器+循环执行器+工具层的智能搜索代理功能
"""

from .planner import SearchPlanner, QueryAnalyzer, TaskDecomposer, StrategyGenerator
from .executor import LoopExecutor, ExecutionEngine, StateManager, ConditionEvaluator
from .tools import SearchTools, ContentAnalysisTools, DataProcessingTools
from .observability import ExecutionTracer, PerformanceMonitor, ResultLogger
from .models import (
    AgentSearchRequest,
    AgentSearchResponse,
    ExecutionPlan,
    ExecutionStep,
    ExecutionState,
    AgentResult,
)
from .search_agent import SearchAgent

__all__ = [
    # 核心组件
    "SearchAgent",
    "SearchPlanner",
    "LoopExecutor",
    
    # 规划器组件
    "QueryAnalyzer",
    "TaskDecomposer", 
    "StrategyGenerator",
    
    # 执行器组件
    "ExecutionEngine",
    "StateManager",
    "ConditionEvaluator",
    
    # 工具层
    "SearchTools",
    "ContentAnalysisTools",
    "DataProcessingTools",
    
    # 可观测层
    "ExecutionTracer",
    "PerformanceMonitor",
    "ResultLogger",
    
    # 数据模型
    "AgentSearchRequest",
    "AgentSearchResponse",
    "ExecutionPlan",
    "ExecutionStep",
    "ExecutionState",
    "AgentResult",
]
