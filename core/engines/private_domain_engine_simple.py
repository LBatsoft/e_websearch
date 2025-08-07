"""
简化版私域搜索引擎
"""

from typing import List
from .base_engine import BaseSearchEngine
from ..models import SearchResult, SearchRequest, SourceType


class PrivateDomainEngine(BaseSearchEngine):
    """简化版私域搜索引擎"""
    
    def __init__(self):
        super().__init__("PrivateDomain")
        # 简化版本，默认不可用
        self.enabled = False
    
    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """执行私域搜索"""
        # 简化版本，返回空结果
        return []
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        return False  # 简化版本暂不可用