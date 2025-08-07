"""
API 数据模型
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SourceTypeAPI(str, Enum):
    """API 搜索结果来源类型"""
    BING = "bing"
    ZAI = "zai"
    WECHAT = "wechat"
    ZHIHU = "zhihu"
    BAIDU = "baidu"
    CUSTOM = "custom"


class SearchRequestAPI(BaseModel):
    """API 搜索请求模型"""
    query: str = Field(..., description="搜索查询词", min_length=1, max_length=500)
    max_results: int = Field(10, description="最大返回结果数", ge=1, le=50)
    include_content: bool = Field(True, description="是否提取完整内容")
    sources: List[SourceTypeAPI] = Field(
        default=[SourceTypeAPI.ZAI, SourceTypeAPI.WECHAT], 
        description="指定搜索源"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="搜索过滤器"
    )

    class Config:
        schema_extra = {
            "example": {
                "query": "人工智能最新发展",
                "max_results": 10,
                "include_content": False,
                "sources": ["zai"],
                "filters": {
                    "time_range": "month",
                    "domain": "www.sohu.com",
                    "content_size": "high"
                }
            }
        }


class SearchResultAPI(BaseModel):
    """API 搜索结果模型"""
    title: str = Field(..., description="标题")
    url: str = Field(..., description="URL")
    snippet: str = Field(..., description="摘要")
    source: SourceTypeAPI = Field(..., description="来源")
    score: float = Field(0.0, description="相关性得分", ge=0.0, le=1.0)
    publish_time: Optional[datetime] = Field(None, description="发布时间")
    author: Optional[str] = Field(None, description="作者")
    content: Optional[str] = Field(None, description="完整内容")
    images: List[str] = Field(default_factory=list, description="图片URL列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class SearchResponseAPI(BaseModel):
    """API 搜索响应模型"""
    success: bool = Field(..., description="搜索是否成功")
    message: str = Field("", description="响应消息")
    results: List[SearchResultAPI] = Field(default_factory=list, description="搜索结果")
    total_count: int = Field(0, description="总结果数")
    query: str = Field("", description="搜索查询词")
    execution_time: float = Field(0.0, description="执行时间(秒)")
    sources_used: List[SourceTypeAPI] = Field(default_factory=list, description="使用的搜索源")
    cache_hit: bool = Field(False, description="是否命中缓存")


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    engines: Dict[str, bool] = Field(..., description="引擎状态")
    available_sources: List[SourceTypeAPI] = Field(..., description="可用搜索源")
    cache_enabled: bool = Field(..., description="缓存是否启用")
    last_search_time: Optional[float] = Field(None, description="最后搜索耗时")
    error: Optional[str] = Field(None, description="错误信息")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="操作是否成功")
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


class SuggestionsRequest(BaseModel):
    """搜索建议请求模型"""
    query: str = Field(..., description="查询词", min_length=1, max_length=100)

    class Config:
        schema_extra = {
            "example": {
                "query": "人工智能"
            }
        }


class SuggestionsResponse(BaseModel):
    """搜索建议响应模型"""
    success: bool = Field(..., description="请求是否成功")
    suggestions: List[str] = Field(default_factory=list, description="搜索建议列表")
    query: str = Field("", description="原始查询词")


class StatisticsResponse(BaseModel):
    """统计信息响应模型"""
    success: bool = Field(..., description="请求是否成功")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="统计信息")


class CacheOperationResponse(BaseModel):
    """缓存操作响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作消息")
    cache_size: Optional[int] = Field(None, description="缓存大小")