"""
基础搜索引擎抽象类
"""

from abc import ABC, abstractmethod
from typing import List

from ..models import SearchRequest, SearchResult


class BaseSearchEngine(ABC):
    """搜索引擎基类"""

    def __init__(self, name: str):
        self.name = name
        self.enabled = True

    @abstractmethod
    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """执行搜索"""
        pass

    def is_available(self) -> bool:
        """检查引擎是否可用"""
        return self.enabled

    def get_name(self) -> str:
        """获取引擎名称"""
        return self.name
