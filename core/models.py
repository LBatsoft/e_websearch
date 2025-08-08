"""
数据模型定义
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SourceType(Enum):
    """搜索结果来源类型"""

    BING = "bing"
    ZAI = "zai"
    WECHAT = "wechat"
    ZHIHU = "zhihu"
    BAIDU = "baidu"
    CUSTOM = "custom"


@dataclass
class SearchResult:
    """搜索结果数据模型"""

    title: str
    url: str
    snippet: str
    source: SourceType
    score: float = 0.0
    publish_time: Optional[datetime] = None
    author: Optional[str] = None
    content: Optional[str] = None  # 完整内容（通过内容提取器获取）
    images: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.metadata is None:
            self.metadata = {}

        # 确保 source 是 SourceType 枚举
        if isinstance(self.source, str):
            try:
                self.source = SourceType(self.source)
            except ValueError:
                self.source = SourceType.CUSTOM

        # 确保 publish_time 是 datetime 对象
        if isinstance(self.publish_time, str):
            try:
                # 尝试解析 ISO 格式的日期时间字符串
                self.publish_time = datetime.fromisoformat(
                    self.publish_time.replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                self.publish_time = None


@dataclass
class SearchRequest:
    """搜索请求数据模型"""

    query: str
    max_results: int = 10
    include_content: bool = True  # 是否提取完整内容
    sources: List[SourceType] = None  # 指定搜索源
    filters: Dict[str, Any] = None
    # LLM 增强选项（可选）
    llm_summary: bool = False
    llm_tags: bool = False
    llm_per_result: bool = False
    llm_max_items: int = 5
    llm_language: str = "zh"
    model_provider: str = "auto"  # 模型提供商：auto, zhipuai, openai, azure, baidu, qwen, custom
    model_name: str = ""  # 模型名称：glm-4, gpt-4, qwen-plus 等

    def __post_init__(self):
        if self.sources is None:
            self.sources = [SourceType.ZAI, SourceType.WECHAT]
        if self.filters is None:
            self.filters = {}


@dataclass
class SearchResponse:
    """搜索响应数据模型"""

    results: List[SearchResult]
    total_count: int
    query: str
    execution_time: float
    sources_used: List[SourceType]
    cache_hit: bool = False
    # LLM 增强输出（可选）
    llm_summary: str | None = None
    llm_tags: List[str] | None = None
    llm_per_result: Dict[str, Dict[str, Any]] | None = None
