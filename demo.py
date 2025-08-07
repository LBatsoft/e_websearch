#!/usr/bin/env python3
"""
增强版Web搜索系统演示
"""

import asyncio
import os
from models import SearchRequest, SourceType
from search_orchestrator import SearchOrchestrator


async def demo_search():
    """演示搜索功能"""
    
    print("=== 增强版Web搜索系统演示 ===\n")
    
    # 创建搜索协调器
    orchestrator = SearchOrchestrator()
    
    # 系统健康检查
    print("1. 系统健康检查")
    print("-" * 30)
    health = await orchestrator.health_check()
    print(f"系统状态: {health['status']}")
    print(f"可用引擎: {health['engines']}")
    print(f"可用搜索源: {health['available_sources']}")
    print(f"缓存启用: {health['cache_enabled']}")
    
    print("\n2. 执行搜索测试")
    print("-" * 30)
    
    # 创建搜索请求 - 尝试搜索存在的数据
    request = SearchRequest(
        query="学区",  # 更改为可能存在的关键词
        max_results=5,
        include_content=False,  # 暂时不提取内容以提高速度
        sources=[SourceType.WECHAT, SourceType.ZHIHU]
    )
    
    print(f"搜索关键词: {request.query}")
    print(f"搜索源: {[s.value for s in request.sources]}")
    print(f"最大结果数: {request.max_results}")
    
    # 执行搜索
    try:
        response = await orchestrator.search(request)
        
        print(f"\n搜索结果:")
        print(f"- 总结果数: {response.total_count}")
        print(f"- 执行时间: {response.execution_time:.3f}秒")
        print(f"- 使用的源: {[s.value for s in response.sources_used]}")
        print(f"- 缓存命中: {response.cache_hit}")
        
        if response.results:
            print(f"\n找到 {len(response.results)} 个结果:")
            for i, result in enumerate(response.results[:3], 1):
                print(f"\n{i}. {result.title}")
                print(f"   来源: {result.source.value}")
                print(f"   得分: {result.score:.3f}")
                print(f"   摘要: {result.snippet[:100]}...")
                
                if result.author:
                    print(f"   作者: {result.author}")
                
                if result.url:
                    print(f"   链接: {result.url}")
        else:
            print("\n未找到匹配的结果")
            print("提示: 这可能是因为:")
            print("  1. 项目中没有相关的微信或知乎数据")
            print("  2. 搜索关键词与现有数据不匹配")
            print("  3. 私域数据文件格式不匹配")
        
        # 统计信息
        if response.results:
            stats = orchestrator.get_search_statistics(response.results)
            print(f"\n3. 统计信息")
            print("-" * 30)
            print(f"平均得分: {stats.get('avg_score', 0):.3f}")
            print(f"来源分布: {stats.get('source_distribution', {})}")
        
    except Exception as e:
        print(f"搜索失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 演示缓存功能
    print(f"\n4. 缓存功能演示")
    print("-" * 30)
    
    print("执行相同搜索（测试缓存）...")
    response2 = await orchestrator.search(request)
    print(f"第二次搜索耗时: {response2.execution_time:.3f}秒")
    print(f"缓存命中: {response2.cache_hit}")
    
    print(f"\n=== 演示完成 ===")
    print("\n功能说明:")
    print("✅ 多源搜索：支持Bing、微信公众号、知乎等多个搜索源")
    print("✅ 私域搜索：自动搜索项目中的微信、知乎JSON数据文件")
    print("✅ 内容提取：使用Playwright自动化浏览器提取详情页内容")
    print("✅ 智能聚合：去重、相关性评分、结果排序")
    print("✅ 缓存系统：内存+文件双重缓存，提高搜索效率")
    print("✅ 异步处理：全异步架构，支持高并发搜索")


if __name__ == "__main__":
    # 提示信息
    if not os.getenv("BING_API_KEY"):
        print("注意: 未设置BING_API_KEY环境变量")
        print("本演示将使用私域搜索功能（微信公众号、知乎数据）")
        print()
    
    asyncio.run(demo_search()) 