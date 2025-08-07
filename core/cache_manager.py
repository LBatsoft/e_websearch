"""
缓存管理器
"""

import time
import json
import asyncio
from collections import OrderedDict
import redis.asyncio as aio_redis
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from loguru import logger

from core.models import SearchResult
from config import REDIS_CONFIG, get_cache_config


class BaseCacheManager(ABC):
    """缓存管理器基类"""
    def __init__(self, config: dict):
        self.enabled = config.get('enabled', True)
        self.ttl = config.get('ttl', 3600)
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }

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

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def cleanup_expired(self):
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class InMemoryCacheManager(BaseCacheManager):
    """优化的内存缓存管理器，支持LRU退出机制"""
    def __init__(self, config: dict):
        super().__init__(config)
        self.max_size = config.get('max_size', 1000)
        self.cleanup_interval = config.get('cleanup_interval', 300)  # 5分钟清理一次
        self._cache = OrderedDict()  # 使用OrderedDict实现LRU
        self._last_cleanup = time.time()
        logger.info(f"使用内存缓存 (最大容量: {self.max_size}, TTL: {self.ttl}s)")

    async def get(self, key: str) -> Optional[List[SearchResult]]:
        if not self.enabled:
            self.stats['misses'] += 1
            return None
        
        if key not in self._cache:
            self.stats['misses'] += 1
            return None
        
        data, timestamp = self._cache[key]
        
        # 检查是否过期
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            self.stats['misses'] += 1
            return None
        
        # LRU: 移动到末尾（最近使用）
        self._cache.move_to_end(key)
        self.stats['hits'] += 1
        return data

    async def set(self, key: str, data: List[SearchResult]):
        if not self.enabled:
            return
        
        # 定期清理过期项
        await self.cleanup_expired()
        
        # 如果缓存已满，使用LRU策略移除最久未使用的项
        if len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self.stats['evictions'] += 1
            logger.debug(f"LRU缓存退出: {oldest_key}")
        
        self._cache[key] = (data, time.time())
        self.stats['sets'] += 1

    async def clear(self):
        self._cache.clear()
        self.stats = {'hits': 0, 'misses': 0, 'sets': 0, 'evictions': 0}
        logger.info("内存缓存已清空")

    async def close(self):
        await self.clear()

    async def get_stats(self) -> Dict[str, Any]:
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'type': 'memory',
            'enabled': self.enabled,
            'current_size': len(self._cache),
            'max_size': self.max_size,
            'ttl': self.ttl,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'evictions': self.stats['evictions'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }

    async def cleanup_expired(self):
        """清理过期的缓存项"""
        current_time = time.time()
        
        # 避免频繁清理，每5分钟最多清理一次
        if current_time - self._last_cleanup < self.cleanup_interval:
            return
        
        expired_keys = []
        for key, (data, timestamp) in self._cache.items():
            if current_time - timestamp > self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存项")
        
        self._last_cleanup = current_time

    async def health_check(self) -> bool:
        """内存缓存健康检查"""
        return self.enabled


class RedisCacheManager(BaseCacheManager):
    """优化的Redis缓存管理器，支持缓存统计和自动清理"""
    def __init__(self, config: dict):
        super().__init__(config)
        self.cleanup_interval = config.get('cleanup_interval', 600)  # 10分钟清理一次
        self._last_cleanup = time.time()
        self.redis = None
        self._connection_healthy = False
        
        try:
            self.redis = aio_redis.from_url(
                f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}",
                decode_responses=True,
                max_connections=config.get('max_connections', 20),
                retry_on_timeout=config.get('retry_on_timeout', True),
                health_check_interval=config.get('health_check_interval', 30)
            )
            logger.info(f"使用 Redis 缓存 (连接到 redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']})")
            self._connection_healthy = True
        except Exception as e:
            logger.error(f"无法连接到 Redis: {e}. 将禁用缓存.")
            self.enabled = False
            self.redis = None

    async def get(self, key: str) -> Optional[List[SearchResult]]:
        if not self.enabled or not self._connection_healthy:
            self.stats['misses'] += 1
            return None
        
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                # 反序列化 - 处理SearchResult对象和字典两种情况
                results_json = json.loads(cached_data)
                results = []
                for data in results_json:
                    if isinstance(data, dict):
                        # 尝试创建SearchResult对象，如果失败则返回字典
                        try:
                            results.append(SearchResult(**data))
                        except Exception:
                            # 如果无法创建SearchResult，直接返回字典
                            results.append(data)
                    else:
                        # 其他类型，直接返回
                        results.append(data)
                
                self.stats['hits'] += 1
                return results
            else:
                self.stats['misses'] += 1
                return None
        except Exception as e:
            logger.error(f"从 Redis 获取缓存失败: {e}")
            self.stats['misses'] += 1
            self._connection_healthy = False
            return None

    async def set(self, key: str, data: List[SearchResult]):
        if not self.enabled or not self._connection_healthy:
            return

        try:
            # 定期清理过期项
            await self.cleanup_expired()
            
            # 序列化 - 处理SearchResult对象和字典两种情况
            serialized_data = []
            for res in data:
                if hasattr(res, '__dict__'):
                    # SearchResult对象
                    serialized_data.append(res.__dict__)
                elif isinstance(res, dict):
                    # 字典对象
                    serialized_data.append(res)
                else:
                    # 其他类型，尝试转换为字典
                    serialized_data.append(str(res))
            
            results_json = json.dumps(serialized_data)
            await self.redis.set(key, results_json, ex=self.ttl)
            self.stats['sets'] += 1
        except Exception as e:
            logger.error(f"向 Redis 设置缓存失败: {e}")
            self._connection_healthy = False

    async def clear(self):
        if not self.enabled or not self._connection_healthy:
            return
        try:
            await self.redis.flushdb()
            self.stats = {'hits': 0, 'misses': 0, 'sets': 0, 'evictions': 0}
            logger.info("Redis 缓存已清空")
        except Exception as e:
            logger.error(f"清空 Redis 缓存失败: {e}")
            self._connection_healthy = False

    async def close(self):
        if self.redis:
            await self.redis.close()

    async def get_stats(self) -> Dict[str, Any]:
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # 获取Redis内存使用情况
        memory_info = {}
        try:
            if self.redis and self._connection_healthy:
                info = await self.redis.info('memory')
                memory_info = {
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'used_memory_peak': info.get('used_memory_peak_human', 'N/A'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
        except Exception as e:
            logger.warning(f"获取Redis内存信息失败: {e}")
        
        return {
            'type': 'redis',
            'enabled': self.enabled,
            'connection_healthy': self._connection_healthy,
            'ttl': self.ttl,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'evictions': self.stats['evictions'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'memory_info': memory_info
        }

    async def cleanup_expired(self):
        """Redis会自动清理过期项，这里主要用于统计"""
        current_time = time.time()
        
        # 避免频繁检查，每10分钟最多检查一次
        if current_time - self._last_cleanup < self.cleanup_interval:
            return
        
        try:
            if self.redis and self._connection_healthy:
                # 获取数据库大小
                db_size = await self.redis.dbsize()
                logger.debug(f"Redis数据库大小: {db_size} 个键")
        except Exception as e:
            logger.warning(f"获取Redis数据库大小失败: {e}")
            self._connection_healthy = False
        
        self._last_cleanup = current_time

    async def health_check(self) -> bool:
        """Redis健康检查"""
        if not self.enabled or not self.redis:
            return False
        
        try:
            await self.redis.ping()
            self._connection_healthy = True
            return True
        except Exception as e:
            logger.warning(f"Redis健康检查失败: {e}")
            self._connection_healthy = False
            return False


class DistributedCacheManager(BaseCacheManager):
    """分布式缓存管理器，支持Redis + 本地缓存降级"""
    def __init__(self, config: dict):
        super().__init__(config)
        self.redis_cache = RedisCacheManager(config)
        self.local_cache = InMemoryCacheManager(config)
        self.fallback_enabled = config.get('fallback_enabled', True)
        self.sync_interval = config.get('sync_interval', 60)  # 同步间隔（秒）
        self._last_sync = time.time()
        
        logger.info("使用分布式缓存 (Redis + 本地缓存降级)")

    async def get(self, key: str) -> Optional[List[SearchResult]]:
        if not self.enabled:
            self.stats['misses'] += 1
            return None
        
        # 首先尝试从Redis获取
        result = await self.redis_cache.get(key)
        if result:
            # Redis命中，同步到本地缓存
            if self.fallback_enabled:
                await self.local_cache.set(key, result)
            self.stats['hits'] += 1
            return result
        
        # Redis未命中，尝试本地缓存
        if self.fallback_enabled:
            result = await self.local_cache.get(key)
            if result:
                self.stats['hits'] += 1
                return result
        
        self.stats['misses'] += 1
        return None

    async def set(self, key: str, data: List[SearchResult]):
        if not self.enabled:
            return
        
        # 同时写入Redis和本地缓存
        await asyncio.gather(
            self.redis_cache.set(key, data),
            self.local_cache.set(key, data) if self.fallback_enabled else asyncio.sleep(0)
        )
        self.stats['sets'] += 1

    async def clear(self):
        """清空所有缓存"""
        await asyncio.gather(
            self.redis_cache.clear(),
            self.local_cache.clear()
        )
        self.stats = {'hits': 0, 'misses': 0, 'sets': 0, 'evictions': 0}
        logger.info("分布式缓存已清空")

    async def close(self):
        """关闭缓存管理器"""
        await asyncio.gather(
            self.redis_cache.close(),
            self.local_cache.close()
        )

    async def get_stats(self) -> Dict[str, Any]:
        """获取分布式缓存统计信息"""
        redis_stats = await self.redis_cache.get_stats()
        local_stats = await self.local_cache.get_stats()
        
        # 合并统计信息
        combined_stats = {
            'type': 'distributed',
            'enabled': self.enabled,
            'fallback_enabled': self.fallback_enabled,
            'redis_healthy': redis_stats.get('connection_healthy', False),
            'redis_stats': redis_stats,
            'local_stats': local_stats,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'evictions': self.stats['evictions']
        }
        
        # 计算总体命中率
        total_requests = self.stats['hits'] + self.stats['misses']
        if total_requests > 0:
            combined_stats['hit_rate'] = round((self.stats['hits'] / total_requests) * 100, 2)
        else:
            combined_stats['hit_rate'] = 0.0
        
        return combined_stats

    async def cleanup_expired(self):
        """清理过期缓存"""
        await asyncio.gather(
            self.redis_cache.cleanup_expired(),
            self.local_cache.cleanup_expired()
        )

    async def health_check(self) -> bool:
        """分布式缓存健康检查"""
        redis_healthy = await self.redis_cache.health_check()
        local_healthy = await self.local_cache.health_check()
        
        # 只要有一个缓存可用就认为健康
        return redis_healthy or local_healthy

    async def sync_caches(self):
        """同步Redis和本地缓存（可选功能）"""
        current_time = time.time()
        if current_time - self._last_sync < self.sync_interval:
            return
        
        try:
            # 这里可以实现更复杂的同步逻辑
            # 例如：将本地缓存的热点数据同步到Redis
            logger.debug("执行缓存同步...")
            self._last_sync = current_time
        except Exception as e:
            logger.error(f"缓存同步失败: {e}")


class CacheManagerFactory:
    """缓存管理器工厂"""
    @staticmethod
    def create_cache_manager(cache_type: str, config: dict) -> BaseCacheManager:
        """创建缓存管理器实例"""
        if cache_type == "distributed":
            return DistributedCacheManager(config)
        elif cache_type == "redis":
            return RedisCacheManager(config)
        else:
            return InMemoryCacheManager(config)
