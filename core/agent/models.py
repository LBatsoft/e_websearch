"""
Search Agent 数据模型定义
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from ..models import SearchResult, SourceType


class ExecutionStatus(Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(Enum):
    """执行步骤类型"""
    SEARCH = "search"
    ANALYZE = "analyze"
    REFINE = "refine"
    SUMMARIZE = "summarize"
    VALIDATE = "validate"


class PlanningStrategy(Enum):
    """规划策略枚举"""
    SIMPLE = "simple"          # 简单单次搜索
    ITERATIVE = "iterative"    # 迭代式多跳搜索
    PARALLEL = "parallel"      # 并行多路搜索
    ADAPTIVE = "adaptive"      # 自适应策略


@dataclass
class AgentSearchRequest:
    """Agent 搜索请求"""
    query: str
    max_iterations: int = 3
    max_results_per_iteration: int = 10
    total_max_results: int = 50
    sources: List[SourceType] = field(default_factory=lambda: [SourceType.ZAI])
    include_content: bool = True
    
    # LLM 增强选项
    llm_summary: bool = True
    llm_tags: bool = True
    llm_per_result: bool = False
    llm_language: str = "zh"
    model_provider: str = "auto"
    model_name: str = ""
    
    # Agent 特定选项
    planning_strategy: PlanningStrategy = PlanningStrategy.ADAPTIVE
    enable_refinement: bool = True
    confidence_threshold: float = 0.7
    
    # 可观测选项
    enable_tracing: bool = True
    enable_performance_monitoring: bool = True
    
    # 其他选项
    timeout: int = 300  # 总超时时间（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: str
    step_type: StepType
    description: str
    query: str
    sources: List[SourceType]
    max_results: int
    
    # 执行状态
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    
    # 执行结果
    results: List[SearchResult] = field(default_factory=list)
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
    # 错误信息
    error: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self):
        """开始执行"""
        self.status = ExecutionStatus.RUNNING
        self.start_time = time.time()
    
    def complete(self, results: List[SearchResult] = None, summary: str = None, 
                tags: List[str] = None, confidence_score: float = 0.0):
        """完成执行"""
        self.status = ExecutionStatus.COMPLETED
        self.end_time = time.time()
        if self.start_time:
            self.execution_time = self.end_time - self.start_time
        
        if results is not None:
            self.results = results
        if summary is not None:
            self.summary = summary
        if tags is not None:
            self.tags = tags
        self.confidence_score = confidence_score
    
    def fail(self, error: str):
        """执行失败"""
        self.status = ExecutionStatus.FAILED
        self.end_time = time.time()
        if self.start_time:
            self.execution_time = self.end_time - self.start_time
        self.error = error


@dataclass
class ExecutionPlan:
    """执行计划"""
    plan_id: str
    original_query: str
    strategy: PlanningStrategy
    steps: List[ExecutionStep]
    
    # 计划元数据
    created_at: float = field(default_factory=time.time)
    estimated_time: Optional[float] = None
    confidence_score: float = 0.0
    
    # 计划状态
    current_step_index: int = 0
    
    def get_current_step(self) -> Optional[ExecutionStep]:
        """获取当前执行步骤"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def next_step(self) -> bool:
        """移动到下一步"""
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            return True
        return False
    
    def is_completed(self) -> bool:
        """检查是否完成"""
        return all(step.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED] 
                  for step in self.steps)


@dataclass
class ExecutionState:
    """执行状态"""
    session_id: str
    request: AgentSearchRequest
    plan: ExecutionPlan
    
    # 执行状态
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_execution_time: Optional[float] = None
    
    # 累积结果
    all_results: List[SearchResult] = field(default_factory=list)
    final_summary: Optional[str] = None
    final_tags: List[str] = field(default_factory=list)
    
    # 性能统计
    total_searches: int = 0
    total_results_found: int = 0
    cache_hits: int = 0
    
    # 错误信息
    errors: List[str] = field(default_factory=list)
    
    # 可观测数据
    trace_data: Dict[str, Any] = field(default_factory=dict)
    performance_data: Dict[str, Any] = field(default_factory=dict)
    
    def add_results(self, results: List[SearchResult]):
        """添加搜索结果"""
        self.all_results.extend(results)
        self.total_results_found += len(results)
    
    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)
    
    def complete(self, final_summary: str = None, final_tags: List[str] = None):
        """完成执行"""
        self.status = ExecutionStatus.COMPLETED
        self.end_time = time.time()
        self.total_execution_time = self.end_time - self.start_time
        
        if final_summary:
            self.final_summary = final_summary
        if final_tags:
            self.final_tags = final_tags
    
    def fail(self, error: str):
        """执行失败"""
        self.status = ExecutionStatus.FAILED
        self.end_time = time.time()
        self.total_execution_time = self.end_time - self.start_time
        self.add_error(error)


@dataclass
class AgentResult:
    """Agent 搜索结果（单个结果项的增强版本）"""
    # 基础搜索结果信息
    title: str
    url: str
    snippet: str
    source: SourceType
    score: float
    
    # 可选字段
    publish_time: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    images: List[str] = field(default_factory=list)
    
    # Agent 增强字段
    relevance_score: float = 0.0
    confidence_score: float = 0.0
    found_in_step: Optional[str] = None
    step_type: Optional[StepType] = None
    
    # LLM 增强字段
    llm_summary: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)
    
    # 引用和关联
    citations: List[str] = field(default_factory=list)
    related_results: List[str] = field(default_factory=list)  # URL列表
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_search_result(cls, result: SearchResult, step_id: str = None, 
                          step_type: StepType = None) -> AgentResult:
        """从 SearchResult 创建 AgentResult"""
        return cls(
            title=result.title,
            url=result.url,
            snippet=result.snippet,
            source=result.source,
            score=result.score,
            publish_time=result.publish_time,
            author=result.author,
            content=result.content,
            images=result.images or [],
            llm_summary=result.llm_summary,
            labels=result.labels or [],
            found_in_step=step_id,
            step_type=step_type,
            metadata=result.metadata or {},
        )


@dataclass
class AgentSearchResponse:
    """Agent 搜索响应"""
    success: bool
    session_id: str
    message: str = ""
    
    # 执行信息
    execution_state: Optional[ExecutionState] = None
    
    # 最终结果
    results: List[AgentResult] = field(default_factory=list)
    total_count: int = 0
    
    # 查询信息
    original_query: str = ""
    final_query: str = ""
    
    # 执行统计
    total_execution_time: float = 0.0
    total_iterations: int = 0
    total_searches: int = 0
    cache_hits: int = 0
    
    # LLM 增强结果
    final_summary: Optional[str] = None
    final_tags: List[str] = field(default_factory=list)
    
    # 可观测数据
    execution_trace: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 引用和来源
    sources_used: List[SourceType] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    
    # 错误信息
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
