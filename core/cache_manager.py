"""
缓存管理器
"""

import time
from typing import List, Optional
from .models import SearchResult


class CacheManager:
    """简单的内存缓存管理器"""
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        self.ttl = ttl  # 生存时间（秒）
        self.max_size = max_size
        self.cache = {}  # {key: (data, timestamp)}
        self.enabled = True
    
    def get(self, key: str) -> Optional[List[SearchResult]]:
        """获取缓存"""
        if not self.enabled or key not in self.cache:
            return None
        
        data, timestamp = self.cache[key]
        
        # 检查是否过期
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None
        
        return data
    
    def set(self, key: str, data: List[SearchResult]):
        """设置缓存"""
        if not self.enabled:
            return
        
        # 如果缓存满了，删除最旧的条目
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[key] = (data, time.time())
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
    
    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]