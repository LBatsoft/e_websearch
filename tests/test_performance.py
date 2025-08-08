#!/usr/bin/env python3
"""
性能测试脚本
测试搜索系统的缓存性能、并发性能和响应时间
"""

import asyncio
import json
from pathlib import Path
import statistics
import sys
import time
from typing import Dict, List

import aiohttp

# 将项目根目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from config import get_cache_config
from core.cache_manager import CacheManagerFactory
from core.models import SearchRequest, SourceType
from core.search_orchestrator import SearchOrchestrator


class PerformanceTester:
    """性能测试器"""

    def __init__(self):
        self.orchestrator = SearchOrchestrator()
        self.test_queries = [
            "Python 教程",
            "机器学习算法",
            "深度学习框架",
            "数据科学工具",
            "人工智能应用",
            "自然语言处理",
            "计算机视觉",
            "推荐系统",
            "区块链技术",
            "云计算服务",
        ]

    async def test_cache_performance(self):
        """测试缓存性能"""
        print("🧪 测试缓存性能...")

        query = "缓存性能测试"
        request = SearchRequest(query=query, max_results=5)

        # 第一次搜索（无缓存）
        start_time = time.time()
        response1 = await self.orchestrator.search(request)
        first_search_time = time.time() - start_time

        # 第二次搜索（缓存命中）
        start_time = time.time()
        response2 = await self.orchestrator.search(request)
        cached_search_time = time.time() - start_time

        print(f"✅ 首次搜索耗时: {first_search_time:.3f}秒")
        print(f"✅ 缓存搜索耗时: {cached_search_time:.3f}秒")
        print(
            f"✅ 性能提升: {((first_search_time - cached_search_time) / first_search_time * 100):.1f}%"
        )

        return {
            "first_search_time": first_search_time,
            "cached_search_time": cached_search_time,
            "performance_improvement": (
                (first_search_time - cached_search_time) / first_search_time * 100
            ),
        }

    async def test_concurrent_performance(self, concurrency: int = 5):
        """测试并发性能"""
        print(f"🧪 测试并发性能 (并发数: {concurrency})...")

        async def single_search(query: str):
            request = SearchRequest(query=query, max_results=3)
            start_time = time.time()
            response = await self.orchestrator.search(request)
            search_time = time.time() - start_time
            return {
                "query": query,
                "time": search_time,
                "results_count": len(response.results),
                "cache_hit": response.cache_hit,
            }

        # 并发执行搜索
        start_time = time.time()
        tasks = [single_search(query) for query in self.test_queries[:concurrency]]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # 统计结果
        search_times = [r["time"] for r in results]
        cache_hits = sum(1 for r in results if r["cache_hit"])

        print(f"✅ 总耗时: {total_time:.3f}秒")
        print(f"✅ 平均搜索时间: {statistics.mean(search_times):.3f}秒")
        print(f"✅ 最快搜索时间: {min(search_times):.3f}秒")
        print(f"✅ 最慢搜索时间: {max(search_times):.3f}秒")
        print(
            f"✅ 缓存命中率: {cache_hits}/{len(results)} ({cache_hits/len(results)*100:.1f}%)"
        )

        return {
            "total_time": total_time,
            "avg_search_time": statistics.mean(search_times),
            "min_search_time": min(search_times),
            "max_search_time": max(search_times),
            "cache_hit_rate": cache_hits / len(results),
        }

    async def test_cache_stats(self):
        """测试缓存统计"""
        print("🧪 测试缓存统计...")

        # 执行一些搜索来生成缓存数据
        for query in self.test_queries[:5]:
            request = SearchRequest(query=query, max_results=3)
            await self.orchestrator.search(request)

        # 获取缓存统计
        cache_stats = await self.orchestrator.cache_manager.get_stats()

        print(f"✅ 缓存类型: {cache_stats.get('type', 'unknown')}")
        print(f"✅ 缓存启用: {cache_stats.get('enabled', False)}")

        if cache_stats.get("type") == "distributed":
            redis_stats = cache_stats.get("redis_stats", {})
            local_stats = cache_stats.get("local_stats", {})

            print(f"✅ Redis连接状态: {redis_stats.get('connection_healthy', False)}")
            print(
                f"✅ 本地缓存大小: {local_stats.get('current_size', 0)}/{local_stats.get('max_size', 0)}"
            )
            print(f"✅ 总体命中率: {cache_stats.get('hit_rate', 0):.1f}%")

        return cache_stats

    async def test_api_performance(self, base_url: str = "http://localhost:8000"):
        """测试API性能"""
        print(f"🧪 测试API性能 ({base_url})...")

        async def api_search(session: aiohttp.ClientSession, query: str):
            payload = {"query": query, "max_results": 3, "sources": ["bing"]}

            start_time = time.time()
            async with session.post(f"{base_url}/search", json=payload) as response:
                result = await response.json()
                search_time = time.time() - start_time

                return {
                    "query": query,
                    "time": search_time,
                    "status": response.status,
                    "results_count": len(result.get("results", [])),
                    "cache_hit": result.get("cache_hit", False),
                }

        # 测试API连接
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/health") as response:
                    if response.status == 200:
                        print("✅ API服务正常运行")
                    else:
                        print(f"⚠️ API服务状态异常: {response.status}")
                        return None

                # 执行API搜索测试
                start_time = time.time()
                tasks = [api_search(session, query) for query in self.test_queries[:5]]
                results = await asyncio.gather(*tasks)
                total_time = time.time() - start_time

                # 统计结果
                search_times = [r["time"] for r in results if r["status"] == 200]
                cache_hits = sum(1 for r in results if r.get("cache_hit", False))

                if search_times:
                    print(f"✅ API总耗时: {total_time:.3f}秒")
                    print(f"✅ API平均响应时间: {statistics.mean(search_times):.3f}秒")
                    print(
                        f"✅ API缓存命中率: {cache_hits}/{len(results)} ({cache_hits/len(results)*100:.1f}%)"
                    )

                return {
                    "total_time": total_time,
                    "avg_response_time": (
                        statistics.mean(search_times) if search_times else 0
                    ),
                    "cache_hit_rate": cache_hits / len(results) if results else 0,
                }

        except Exception as e:
            print(f"❌ API测试失败: {e}")
            return None

    async def run_all_tests(self):
        """运行所有性能测试"""
        print("🚀 开始性能测试\n")

        results = {}

        # 测试缓存性能
        try:
            results["cache_performance"] = await self.test_cache_performance()
            print()
        except Exception as e:
            print(f"❌ 缓存性能测试失败: {e}")

        # 测试并发性能
        try:
            results["concurrent_performance"] = await self.test_concurrent_performance(
                5
            )
            print()
        except Exception as e:
            print(f"❌ 并发性能测试失败: {e}")

        # 测试缓存统计
        try:
            results["cache_stats"] = await self.test_cache_stats()
            print()
        except Exception as e:
            print(f"❌ 缓存统计测试失败: {e}")

        # 测试API性能（如果API服务运行中）
        try:
            api_results = await self.test_api_performance()
            if api_results:
                results["api_performance"] = api_results
            print()
        except Exception as e:
            print(f"❌ API性能测试失败: {e}")

        # 生成测试报告
        self._generate_report(results)

        return results

    def _generate_report(self, results: Dict):
        """生成性能测试报告"""
        print("📊 性能测试报告")
        print("=" * 50)

        if "cache_performance" in results:
            cp = results["cache_performance"]
            print(f"缓存性能:")
            print(f"  - 首次搜索: {cp['first_search_time']:.3f}秒")
            print(f"  - 缓存搜索: {cp['cached_search_time']:.3f}秒")
            print(f"  - 性能提升: {cp['performance_improvement']:.1f}%")

        if "concurrent_performance" in results:
            cp = results["concurrent_performance"]
            print(f"并发性能:")
            print(f"  - 总耗时: {cp['total_time']:.3f}秒")
            print(f"  - 平均搜索时间: {cp['avg_search_time']:.3f}秒")
            print(f"  - 缓存命中率: {cp['cache_hit_rate']*100:.1f}%")

        if "cache_stats" in results:
            cs = results["cache_stats"]
            print(f"缓存统计:")
            print(f"  - 缓存类型: {cs.get('type', 'unknown')}")
            print(f"  - 缓存启用: {cs.get('enabled', False)}")
            if cs.get("type") == "distributed":
                print(f"  - 总体命中率: {cs.get('hit_rate', 0):.1f}%")

        if "api_performance" in results:
            ap = results["api_performance"]
            print(f"API性能:")
            print(f"  - 总耗时: {ap['total_time']:.3f}秒")
            print(f"  - 平均响应时间: {ap['avg_response_time']:.3f}秒")
            print(f"  - 缓存命中率: {ap['cache_hit_rate']*100:.1f}%")

        print("=" * 50)

    async def close(self):
        """关闭测试器"""
        if self.orchestrator:
            await self.orchestrator.close()


async def main():
    """主测试函数"""
    tester = PerformanceTester()

    try:
        await tester.run_all_tests()
    except Exception as e:
        print(f"❌ 性能测试过程中出现错误: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
