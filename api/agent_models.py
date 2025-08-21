"""
Agent API 数据模型定义
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

from core.models import SourceType


class PlanningStrategyAPI(str, Enum):
    """规划策略 API 枚举"""
    SIMPLE = "simple"
    ITERATIVE = "iterative"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


class ExecutionStatusAPI(str, Enum):
    """执行状态 API 枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepTypeAPI(str, Enum):
    """步骤类型 API 枚举"""
    SEARCH = "search"
    ANALYZE = "analyze"
    REFINE = "refine"
    SUMMARIZE = "summarize"
    VALIDATE = "validate"


class SourceTypeAPI(str, Enum):
    """搜索源类型 API 枚举"""
    BING = "bing"
    ZAI = "zai"
    WECHAT = "wechat"
    ZHIHU = "zhihu"
    BAIDU = "baidu"
    CUSTOM = "custom"


class AgentSearchRequestAPI(BaseModel):
    """Agent 搜索请求 API 模型"""
    query: str = Field(..., description="搜索查询")
    max_iterations: int = Field(3, description="最大迭代次数", ge=1, le=10)
    max_results_per_iteration: int = Field(10, description="每次迭代最大结果数", ge=1, le=50)
    total_max_results: int = Field(50, description="总最大结果数", ge=1, le=200)
    sources: List[SourceTypeAPI] = Field(default=[SourceTypeAPI.ZAI], description="搜索源列表")
    include_content: bool = Field(True, description="是否包含详细内容")
    
    # LLM 增强选项
    llm_summary: bool = Field(True, description="是否生成LLM摘要")
    llm_tags: bool = Field(True, description="是否生成LLM标签")
    llm_per_result: bool = Field(False, description="是否为每个结果生成LLM增强")
    llm_language: str = Field("zh", description="LLM输出语言")
    model_provider: str = Field("auto", description="模型提供商")
    model_name: str = Field("", description="模型名称")
    
    # Agent 特定选项
    planning_strategy: PlanningStrategyAPI = Field(PlanningStrategyAPI.ADAPTIVE, description="规划策略")
    enable_refinement: bool = Field(True, description="是否启用查询优化")
    confidence_threshold: float = Field(0.7, description="置信度阈值", ge=0.0, le=1.0)
    
    # 可观测选项
    enable_tracing: bool = Field(True, description="是否启用执行追踪")
    enable_performance_monitoring: bool = Field(True, description="是否启用性能监控")
    
    # 其他选项
    timeout: int = Field(300, description="总超时时间（秒）", ge=30, le=1800)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ExecutionStepAPI(BaseModel):
    """执行步骤 API 模型"""
    step_id: str
    step_type: StepTypeAPI
    description: str
    query: str
    sources: List[SourceTypeAPI]
    max_results: int
    status: ExecutionStatusAPI
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    results_count: int = 0
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionPlanAPI(BaseModel):
    """执行计划 API 模型"""
    plan_id: str
    original_query: str
    strategy: PlanningStrategyAPI
    steps: List[ExecutionStepAPI]
    created_at: float
    estimated_time: Optional[float] = None
    confidence_score: float = 0.0
    current_step_index: int = 0


class AgentResultAPI(BaseModel):
    """Agent 搜索结果 API 模型"""
    title: str
    url: str
    snippet: str
    source: SourceTypeAPI
    score: float
    publish_time: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    
    # Agent 增强字段
    relevance_score: float = 0.0
    confidence_score: float = 0.0
    found_in_step: Optional[str] = None
    step_type: Optional[StepTypeAPI] = None
    
    # LLM 增强字段
    llm_summary: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)
    
    # 引用和关联
    citations: List[str] = Field(default_factory=list)
    related_results: List[str] = Field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionStateAPI(BaseModel):
    """执行状态 API 模型"""
    session_id: str
    status: ExecutionStatusAPI
    start_time: float
    end_time: Optional[float] = None
    total_execution_time: Optional[float] = None
    total_searches: int = 0
    total_results_found: int = 0
    cache_hits: int = 0
    errors: List[str] = Field(default_factory=list)
    final_summary: Optional[str] = None
    final_tags: List[str] = Field(default_factory=list)


class AgentSearchResponseAPI(BaseModel):
    """Agent 搜索响应 API 模型"""
    success: bool
    session_id: str
    message: str = ""
    
    # 执行信息
    execution_state: Optional[ExecutionStateAPI] = None
    execution_plan: Optional[ExecutionPlanAPI] = None
    
    # 最终结果
    results: List[AgentResultAPI] = Field(default_factory=list)
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
    final_tags: List[str] = Field(default_factory=list)
    
    # 可观测数据
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # 引用和来源
    sources_used: List[SourceTypeAPI] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    
    # 错误信息
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchStatusResponseAPI(BaseModel):
    """搜索状态响应 API 模型"""
    success: bool
    session_id: str
    status: ExecutionStatusAPI
    progress: float = Field(0.0, description="执行进度 (0.0-1.0)")
    current_step: Optional[Dict[str, Any]] = None
    results_count: int = 0
    execution_time: float = 0.0
    errors: List[str] = Field(default_factory=list)
    message: str = ""


class CancelSearchResponseAPI(BaseModel):
    """取消搜索响应 API 模型"""
    success: bool
    session_id: str
    message: str = ""


class ExecutionTraceResponseAPI(BaseModel):
    """执行追踪响应 API 模型"""
    success: bool
    session_id: str
    trace_events: List[Dict[str, Any]] = Field(default_factory=list)
    trace_summary: Dict[str, Any] = Field(default_factory=dict)


class PerformanceMetricsResponseAPI(BaseModel):
    """性能指标响应 API 模型"""
    success: bool
    session_id: str
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponseAPI(BaseModel):
    """错误响应 API 模型"""
    success: bool = False
    error: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
