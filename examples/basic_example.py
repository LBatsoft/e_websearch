"""
基础使用示例
"""

import asyncio
import os

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from core.models import SearchRequest, SourceType
from core.search_orchestrator import SearchOrchestrator


async def basic_search_example():
    """基础搜索示例"""

    # 创建搜索协调器
    orchestrator = SearchOrchestrator()

    # 创建搜索请求
    request = SearchRequest(
        query="北京小学入学政策",
        max_results=10,
        include_content=True,
        sources=[SourceType.BING, SourceType.WECHAT],
        filters={"sort": "relevance", "time_range": "Month"},  # 最近一个月
    )

    print(f"开始搜索: {request.query}")
    print(f"搜索源: {[s.value for s in request.sources]}")
    print("-" * 50)

    # 执行搜索
    try:
        response = await orchestrator.search(request)

        print(f"搜索完成！")
        print(f"总结果数: {response.total_count}")
        print(f"执行时间: {response.execution_time:.2f}秒")
        print(f"使用的源: {[s.value for s in response.sources_used]}")
        print(f"缓存命中: {response.cache_hit}")
        print("-" * 50)

        # 显示搜索结果
        for i, result in enumerate(response.results[:5], 1):
            print(f"\n{i}. {result.title}")
            print(f"   来源: {result.source.value}")
            print(f"   URL: {result.url}")
            print(f"   得分: {result.score:.3f}")
            print(f"   摘要: {result.snippet[:100]}...")

            if result.content:
                print(f"   内容长度: {len(result.content)}字符")
                print(f"   内容预览: {result.content[:150]}...")

            if result.author:
                print(f"   作者: {result.author}")

            if result.publish_time:
                print(f"   发布时间: {result.publish_time}")

        # 获取统计信息
        print(f"\n统计信息:")
        if response.results:
            scores = [
                result.score for result in response.results if hasattr(result, "score")
            ]
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"平均得分: {avg_score:.3f}")

            has_content_count = sum(1 for result in response.results if result.content)
            print(f"有完整内容的结果: {has_content_count}")

            source_distribution = {}
            for result in response.results:
                source = result.source.value
                source_distribution[source] = source_distribution.get(source, 0) + 1
            print(f"来源分布: {source_distribution}")
        else:
            print("无搜索结果")

    except Exception as e:
        print(f"搜索失败: {e}")


async def health_check_example():
    """健康检查示例"""

    orchestrator = SearchOrchestrator()

    print("检查系统健康状态...")
    health = await orchestrator.health_check()

    print(f"系统状态: {health['status']}")
    print(f"可用引擎: {health['engines']}")
    print(f"可用搜索源: {health['available_sources']}")
    print(f"缓存启用: {health['cache_enabled']}")

    if "last_search_time" in health:
        print(f"上次搜索耗时: {health['last_search_time']:.2f}秒")


async def suggestions_example():
    """搜索建议示例"""

    orchestrator = SearchOrchestrator()

    query = "北京教育"
    print(f"获取'{query}'的搜索建议...")

    suggestions = await orchestrator.get_search_suggestions(query)

    if suggestions:
        print("搜索建议:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
    else:
        print("未获取到搜索建议")


async def main():
    """主函数"""

    print("=== 增强版Web搜索系统示例 ===\n")

    # 健康检查
    await health_check_example()
    print("\n" + "=" * 50 + "\n")

    # 基础搜索
    await basic_search_example()
    print("\n" + "=" * 50 + "\n")

    # 搜索建议
    await suggestions_example()


if __name__ == "__main__":
    # 设置Bing API密钥（如果有的话）
    if not os.getenv("BING_API_KEY"):
        print("注意: 未设置BING_API_KEY环境变量，Bing搜索将不可用")
        print("可以在.env文件中设置: BING_API_KEY=your_api_key")
        print()

    asyncio.run(main())
