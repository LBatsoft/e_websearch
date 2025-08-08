"""
E-WebSearch API 模块
提供基于 FastAPI 的 Web 搜索 REST API 服务
"""

from .main import app
from .models import (
    ErrorResponse,
    HealthCheckResponse,
    SearchRequestAPI,
    SearchResponseAPI,
    SearchResultAPI,
    SourceTypeAPI,
)

__version__ = "1.0.0"
__all__ = [
    "app",
    "SearchRequestAPI",
    "SearchResponseAPI",
    "SearchResultAPI",
    "SourceTypeAPI",
    "HealthCheckResponse",
    "ErrorResponse",
]
