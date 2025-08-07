#!/usr/bin/env python3
"""
分布式缓存功能测试脚本
"""

import asyncio
import time
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from core.cache_manager import CacheManagerFactory
from config import get_cache_config


async def test_distributed_cache():
    """测试分布式缓存功能"""
    print("🧪 测试分布式缓存功能...")
    
    # 创建分布式缓存管理器
    config = get_cache_config()
    cache = CacheManagerFactory.create_cache_manager("distributed", config)
    
    # 测试基本功能
    test_key = "distributed_test_1"
    test_data = [{"title": "分布式测试结果", "url": "http://example.com", "score": 0.9}]
    
    # 设置缓存
    await cache.set(test_key, test_data)
    print("✅ 分布式缓存设置成功")
    
    # 获取缓存
    cached_data = await cache.get(test_key)
    if cached_data:
        print("✅ 分布式缓存获取成功")
    else:
        print("❌ 分布式缓存获取失败")
    
    # 获取统计信息
    stats = await cache.get_stats()
    print(f"📊 分布式缓存统计: {stats}")
    
    # 健康检查
    health = await cache.health_check()
    print(f"🏥 缓存健康状态: {health}")
    
    # 清理
    await cache.clear()
    await cache.close()
    print("✅ 分布式缓存测试完成\n")


async def test_fallback_mechanism():
    """测试降级机制"""
    print("🧪 测试缓存降级机制...")
    
    config = get_cache_config()
    cache = CacheManagerFactory.create_cache_manager("distributed", config)
    
    # 模拟Redis不可用的情况
    if hasattr(cache, 'redis_cache'):
        cache.redis_cache._connection_healthy = False
        print("🔴 模拟Redis不可用")
    
    # 设置缓存（应该只写入本地缓存）
    test_key = "fallback_test"
    test_data = [{"title": "降级测试", "url": "http://example.com", "score": 0.8}]
    
    await cache.set(test_key, test_data)
    print("✅ 降级缓存设置成功")
    
    # 获取缓存（应该从本地缓存获取）
    cached_data = await cache.get(test_key)
    if cached_data:
        print("✅ 降级缓存获取成功")
    else:
        print("❌ 降级缓存获取失败")
    
    # 获取统计信息
    stats = await cache.get_stats()
    print(f"📊 降级缓存统计: {stats}")
    
    await cache.clear()
    await cache.close()
    print("✅ 降级机制测试完成\n")


async def test_cache_sync():
    """测试缓存同步功能"""
    print("🧪 测试缓存同步功能...")
    
    config = get_cache_config()
    cache = CacheManagerFactory.create_cache_manager("distributed", config)
    
    # 测试同步功能
    if hasattr(cache, 'sync_caches'):
        await cache.sync_caches()
        print("✅ 缓存同步功能正常")
    
    await cache.close()
    print("✅ 缓存同步测试完成\n")


async def test_different_cache_types():
    """测试不同缓存类型"""
    print("🧪 测试不同缓存类型...")
    
    config = get_cache_config()
    
    # 测试内存缓存
    memory_cache = CacheManagerFactory.create_cache_manager("memory", config)
    await memory_cache.set("memory_test", [{"title": "内存缓存测试"}])
    result = await memory_cache.get("memory_test")
    print(f"✅ 内存缓存: {'成功' if result else '失败'}")
    await memory_cache.close()
    
    # 测试Redis缓存
    redis_cache = CacheManagerFactory.create_cache_manager("redis", config)
    await redis_cache.set("redis_test", [{"title": "Redis缓存测试"}])
    result = await redis_cache.get("redis_test")
    print(f"✅ Redis缓存: {'成功' if result else '失败'}")
    await redis_cache.close()
    
    # 测试分布式缓存
    distributed_cache = CacheManagerFactory.create_cache_manager("distributed", config)
    await distributed_cache.set("distributed_test", [{"title": "分布式缓存测试"}])
    result = await distributed_cache.get("distributed_test")
    print(f"✅ 分布式缓存: {'成功' if result else '失败'}")
    await distributed_cache.close()
    
    print("✅ 不同缓存类型测试完成\n")


async def main():
    """主测试函数"""
    print("🚀 开始分布式缓存功能测试\n")
    
    try:
        await test_distributed_cache()
        await test_fallback_mechanism()
        await test_cache_sync()
        await test_different_cache_types()
        
        print("🎉 所有分布式缓存功能测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
