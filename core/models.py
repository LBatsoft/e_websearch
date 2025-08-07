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


@dataclass
class SearchRequest:
    """搜索请求数据模型"""
    query: str
    max_results: int = 10
    include_content: bool = True  # 是否提取完整内容
    sources: List[SourceType] = None  # 指定搜索源
    filters: Dict[str, Any] = None
    
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