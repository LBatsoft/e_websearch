"""
ZAI Search Pro 集成测试示例
"""

import asyncio
from datetime import datetime
import os

# 添加项目路径到 Python path
import sys

project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from core.models import SearchRequest, SourceType

# 导入模块
from core.search_orchestrator import SearchOrchestrator


async def test_zai_search():
    """测试 ZAI Search Pro 搜索功能"""

    # 检查API密钥
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        print("❌ 请设置 ZAI_API_KEY 环境变量")
        return False

    print("🚀 开始测试 ZAI Search Pro 集成")
    print(f"✓ ZAI API Key: {'*' * 8}{api_key[-4:] if len(api_key) > 4 else api_key}")

    orchestrator = SearchOrchestrator()

    # 检查引擎可用性
    available_sources = orchestrator.get_available_sources()
    print(f"\n📋 可用搜索源: {[s.value for s in available_sources]}")

    if SourceType.ZAI not in available_sources:
        print("❌ ZAI搜索引擎不可用")
        return False

    print("✓ ZAI搜索引擎已就绪")

    # 测试搜索功能
    test_queries = ["人工智能最新发展", "Python编程教程", "2025年科技趋势"]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"测试 {i}: {query}")
        print("=" * 50)

        request = SearchRequest(
            query=query,
            max_results=5,
            include_content=False,
            sources=[SourceType.ZAI],
            filters={
                "time_range": "month",  # 搜索最近一个月的内容
                "content_size": "high",
            },
        )

        try:
            start_time = datetime.now()
            response = await orchestrator.search(request)
            end_time = datetime.now()

            duration = (end_time - start_time).total_seconds()

            print(f"⏱️  搜索耗时: {duration:.2f}秒")
            print(f"📊 结果数量: {len(response.results)}")
            print(f"🎯 缓存命中: {'是' if response.cache_hit else '否'}")

            if response.results:
                print(f"\n📄 搜索结果:")
                for j, result in enumerate(response.results, 1):
                    print(f"\n{j}. {result.title}")
                    print(f"   🔗 URL: {result.url}")
                    print(f"   📝 摘要: {result.snippet[:100]}...")
                    print(f"   📊 得分: {result.score:.2f}")

                    if result.author:
                        print(f"   👤 作者: {result.author}")

                    if result.publish_time:
                        print(f"   📅 发布时间: {result.publish_time}")

                    if result.metadata:
                        media = result.metadata.get("media", {})
                        if media:
                            print(f"   📰 媒体: {media.get('name', '未知')}")
            else:
                print("❌ 未找到搜索结果")

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return False

    return True


async def test_health_check():
    """测试健康检查"""
    print(f"\n{'='*50}")
    print("健康检查测试")
    print("=" * 50)

    orchestrator = SearchOrchestrator()

    try:
        health = await orchestrator.health_check()

        print(f"系统状态: {health['status']}")
        print(f"引擎状态:")
        for engine, status in health["engines"].items():
            print(f"  - {engine}: {'✓' if status else '❌'}")

        print(f"可用搜索源: {health['available_sources']}")
        print(f"缓存已启用: {'是' if health['cache_enabled'] else '否'}")

        if "last_search_time" in health and health["last_search_time"]:
            print(f"最后搜索耗时: {health['last_search_time']:.2f}秒")

        if "error" in health:
            print(f"❌ 错误: {health['error']}")
            return False

        return health["status"] == "healthy"

    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


async def test_search_suggestions():
    """测试搜索建议"""
    print(f"\n{'='*50}")
    print("搜索建议测试")
    print("=" * 50)

    orchestrator = SearchOrchestrator()

    try:
        suggestions = await orchestrator.get_search_suggestions("人工智能")

        if suggestions:
            print(f"✓ 获得 {len(suggestions)} 个搜索建议:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
        else:
            print("ℹ️  ZAI Search Pro 暂不支持搜索建议功能")

        return True

    except Exception as e:
        print(f"❌ 搜索建议测试失败: {e}")
        return False


async def main():
    """主测试函数"""

    print("🔍 ZAI Search Pro 集成测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("基础搜索功能", test_zai_search),
        ("健康检查", test_health_check),
        ("搜索建议", test_search_suggestions),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🧪 开始测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            print(f"✓ 测试完成: {test_name} - {'通过' if result else '失败'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ 测试异常: {test_name} - {e}")

    print(f"\n{'='*60}")
    print("📋 测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    print(f"\n🎯 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！ZAI Search Pro 集成成功！")
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
