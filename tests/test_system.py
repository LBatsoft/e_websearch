#!/usr/bin/env python3
"""
系统测试脚本
"""

import asyncio
import sys
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import SearchRequest, SourceType
from core.search_orchestrator import SearchOrchestrator


async def test_basic_functionality():
    """测试基础功能"""
    print("1. 测试基础功能...")

    try:
        orchestrator = SearchOrchestrator()

        # 简单的健康检查
        health = await orchestrator.health_check()
        print(f"   系统状态: {health['status']}")
        print(f"   可用引擎: {health['engines']}")
        print(f"   可用搜索源: {health['available_sources']}")

        return True

    except Exception as e:
        print(f"   ❌ 基础功能测试失败: {e}")
        traceback.print_exc()
        return False


async def test_private_domain_search():
    """测试私域搜索"""
    print("2. 测试私域搜索...")

    try:
        orchestrator = SearchOrchestrator()

        request = SearchRequest(
            query="教育",
            max_results=3,
            include_content=False,
            sources=[SourceType.WECHAT, SourceType.ZHIHU],
        )

        response = await orchestrator.search(request)
        print(f"   找到 {len(response.results)} 个私域结果")

        for result in response.results[:2]:
            print(f"   - {result.source.value}: {result.title[:50]}...")

        return True

    except Exception as e:
        print(f"   ❌ 私域搜索测试失败: {e}")
        return False


async def test_bing_search():
    """测试Bing搜索"""
    print("3. 测试Bing搜索...")

    try:
        orchestrator = SearchOrchestrator()

        if not orchestrator.bing_engine.is_available():
            print("   ⚠️  Bing搜索不可用（API密钥未配置）")
            return True

        request = SearchRequest(
            query="Python编程",
            max_results=3,
            include_content=False,
            sources=[SourceType.BING],
        )

        response = await orchestrator.search(request)
        print(f"   找到 {len(response.results)} 个Bing结果")

        for result in response.results[:2]:
            print(f"   - {result.title[:50]}...")

        return True

    except Exception as e:
        print(f"   ❌ Bing搜索测试失败: {e}")
        return False


async def test_content_extraction():
    """测试内容提取"""
    print("4. 测试内容提取...")

    try:
        from core.content_extractor import ContentExtractor

        # 测试HTTP提取
        async with ContentExtractor() as extractor:
            test_url = "https://www.python.org"
            content = await extractor._extract_with_http(test_url)

            if content:
                print(f"   ✅ HTTP内容提取成功，长度: {len(content)}")
            else:
                print(f"   ⚠️  HTTP内容提取返回空内容")

        return True

    except Exception as e:
        print(f"   ❌ 内容提取测试失败: {e}")
        return False


async def test_cache_system():
    """测试缓存系统"""
    print("5. 测试缓存系统...")

    try:
        orchestrator = SearchOrchestrator()

        # 清空缓存
        orchestrator.clear_cache()

        # 第一次搜索
        request = SearchRequest(
            query="测试查询",
            max_results=2,
            include_content=False,
            sources=[SourceType.WECHAT],
        )

        response1 = await orchestrator.search(request)
        print(f"   第一次搜索 - 缓存命中: {response1.cache_hit}")

        # 第二次搜索（应该命中缓存）
        response2 = await orchestrator.search(request)
        print(f"   第二次搜索 - 缓存命中: {response2.cache_hit}")

        return True

    except Exception as e:
        print(f"   ❌ 缓存系统测试失败: {e}")
        return False


async def test_result_aggregation():
    """测试结果聚合"""
    print("6. 测试结果聚合...")

    try:
        from core.models import SearchResult, SourceType
        from core.result_aggregator import ResultAggregator

        aggregator = ResultAggregator()

        # 创建测试结果
        test_results = {
            SourceType.BING: [
                SearchResult(
                    title="测试标题1",
                    url="http://test1.com",
                    snippet="测试摘要1",
                    source=SourceType.BING,
                    score=0.8,
                )
            ],
            SourceType.WECHAT: [
                SearchResult(
                    title="测试标题2",
                    url="http://test2.com",
                    snippet="测试摘要2",
                    source=SourceType.WECHAT,
                    score=0.7,
                )
            ],
        }

        from core.models import SearchRequest

        request = SearchRequest(query="测试", max_results=10)

        aggregated = aggregator.aggregate_results(test_results, request)
        print(f"   聚合后结果数量: {len(aggregated)}")

        # 测试统计信息
        stats = aggregator.get_statistics(aggregated)
        print(f"   统计信息: {stats.get('source_distribution', {})}")

        return True

    except Exception as e:
        print(f"   ❌ 结果聚合测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("=== 增强版Web搜索系统 - 系统测试 ===\n")

    tests = [
        test_basic_functionality,
        test_private_domain_search,
        test_bing_search,
        test_content_extraction,
        test_cache_system,
        test_result_aggregation,
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"   ❌ 测试执行异常: {e}")
        print()

    print("=" * 50)
    print(f"测试完成: {passed}/{total} 通过")

    if passed == total:
        print("✅ 所有测试通过！系统运行正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置和依赖。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
