"""
缓存管理器
"""

import time
import json
import redis.async_as aio_redis
from abc import ABC, abstractmethod
from typing import List, Optional
from loguru import logger

from .models import SearchResult
from config import REDIS_CONFIG, CACHE_CONFIG


class BaseCacheManager(ABC):
    """缓存管理器基类"""
    def __init__(self, config: dict):
        self.enabled = config.get('enabled', True)
        self.ttl = config.get('ttl', 3600)

    @abstractmethod
    async def get(self, key: str) -> Optional[List[SearchResult]]:
        pass

    @abstractmethod
    async def set(self, key: str, data: List[SearchResult]):
        pass

    @abstractmethod
    async def clear(self):
        pass

    @abstractmethod
    async def close(self):
        pass


class InMemoryCacheManager(BaseCacheManager):
    """简单的内存缓存管理器"""
    def __init__(self, config: dict):
        super().__init__(config)
        self.max_size = config.get('max_size', 1000)
        self._cache = {}  # {key: (data, timestamp)}
        logger.info("使用内存缓存")

    async def get(self, key: str) -> Optional[List[SearchResult]]:
        if not self.enabled or key not in self._cache:
            return None
        
        data, timestamp = self._cache[key]
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            return None
        
        return data

    async def set(self, key: str, data: List[SearchResult]):
        if not self.enabled:
            return
        
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        self._cache[key] = (data, time.time())

    async def clear(self):
        self._cache.clear()
        logger.info("内存缓存已清空")

    async def close(self):
        pass # 内存缓存无需关闭


class RedisCacheManager(BaseCacheManager):
    """使用 Redis 的缓存管理器"""
    def __init__(self, config: dict):
        super().__init__(config)
        try:
            self.redis = aio_redis.from_url(
                f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}",
                decode_responses=True
            )
            logger.info(f"使用 Redis 缓存 (连接到 redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']})")
        except Exception as e:
            logger.error(f"无法连接到 Redis: {e}. 将禁用缓存.")
            self.enabled = False
            self.redis = None

    async def get(self, key: str) -> Optional[List[SearchResult]]:
        if not self.enabled:
            return None
        
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                # 反序列化
                results_json = json.loads(cached_data)
                return [SearchResult(**data) for data in results_json]
            return None
        except Exception as e:
            logger.error(f"从 Redis 获取缓存失败: {e}")
            return None

    async def set(self, key: str, data: List[SearchResult]):
        if not self.enabled:
            return

        try:
            # 序列化
            results_json = json.dumps([res.__dict__ for res in data])
            await self.redis.set(key, results_json, ex=self.ttl)
        except Exception as e:
            logger.error(f"向 Redis 设置缓存失败: {e}")

    async def clear(self):
        if not self.enabled:
            return
        try:
            await self.redis.flushdb()
            logger.info("Redis 缓存已清空")
        except Exception as e:
            logger.error(f"清空 Redis 缓存失败: {e}")

    async def close(self):
        if self.redis:
            await self.redis.close()
