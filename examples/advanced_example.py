"""
高级使用示例
"""

import asyncio
import json
from datetime import datetime

from e_websearch import SearchOrchestrator, SearchRequest, SourceType


async def multi_source_search():
    """多源搜索示例"""
    
    orchestrator = SearchOrchestrator()
    
    # 测试多个查询
    queries = [
        "人工智能教育",
        "区块链技术",
        "新能源汽车",
    ]
    
    for query in queries:
        print(f"\n搜索: {query}")
        print("-" * 30)
        
        request = SearchRequest(
            query=query,
            max_results=5,
            include_content=False,  # 不提取详细内容以提高速度
            sources=[SourceType.BING, SourceType.WECHAT, SourceType.ZHIHU]
        )
        
        response = await orchestrator.search(request)
        
        print(f"找到 {len(response.results)} 个结果，耗时 {response.execution_time:.2f}秒")
        
        # 按来源分组显示
        by_source = {}
        for result in response.results:
            source = result.source.value
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(result)
        
        for source, results in by_source.items():
            print(f"  {source}: {len(results)} 个结果")
            for result in results[:2]:  # 显示前2个
                print(f"    - {result.title[:50]}...")


async def content_extraction_example():
    """内容提取示例"""
    
    orchestrator = SearchOrchestrator()
    
    request = SearchRequest(
        query="Python编程教程",
        max_results=3,
        include_content=True,  # 启用内容提取
        sources=[SourceType.BING]
    )
    
    print("执行搜索并提取详细内容...")
    response = await orchestrator.search(request)
    
    print(f"搜索完成，耗时 {response.execution_time:.2f}秒")
    
    for i, result in enumerate(response.results, 1):
        print(f"\n结果 {i}:")
        print(f"标题: {result.title}")
        print(f"URL: {result.url}")
        
        if result.content:
            print(f"内容长度: {len(result.content)} 字符")
            print(f"提取方法: {result.metadata.get('extraction_method', '未知')}")
            print(f"内容预览:")
            print(result.content[:300] + "..." if len(result.content) > 300 else result.content)
        else:
            print("未能提取到详细内容")
            
        if 'extraction_error' in result.metadata:
            print(f"提取错误: {result.metadata['extraction_error']}")


async def private_domain_search():
    """私域搜索示例"""
    
    orchestrator = SearchOrchestrator()
    
    # 搜索微信公众号内容
    request = SearchRequest(
        query="教育政策",
        max_results=10,
        include_content=False,
        sources=[SourceType.WECHAT, SourceType.ZHIHU]
    )
    
    print("搜索私域内容（微信公众号、知乎）...")
    response = await orchestrator.search(request)
    
    print(f"找到 {len(response.results)} 个私域结果")
    
    for result in response.results:
        print(f"\n来源: {result.source.value}")
        print(f"标题: {result.title}")
        print(f"作者: {result.author or '未知'}")
        print(f"摘要: {result.snippet[:100]}...")
        
        if result.metadata:
            # 显示特殊元数据
            if result.source == SourceType.WECHAT:
                account = result.metadata.get('account', '')
                if account:
                    print(f"公众号: {account}")
            elif result.source == SourceType.ZHIHU:
                vote_count = result.metadata.get('vote_count', 0)
                if vote_count:
                    print(f"点赞数: {vote_count}")


async def cache_management_example():
    """缓存管理示例"""
    
    orchestrator = SearchOrchestrator()
    
    query = "机器学习"
    
    print("第一次搜索（无缓存）...")
    request = SearchRequest(query=query, max_results=5)
    
    response1 = await orchestrator.search(request)
    print(f"耗时: {response1.execution_time:.2f}秒，缓存命中: {response1.cache_hit}")
    
    print("\n第二次搜索（应该命中缓存）...")
    response2 = await orchestrator.search(request)
    print(f"耗时: {response2.execution_time:.2f}秒，缓存命中: {response2.cache_hit}")
    
    print("\n清空缓存...")
    orchestrator.clear_cache()
    
    print("第三次搜索（缓存已清空）...")
    response3 = await orchestrator.search(request)
    print(f"耗时: {response3.execution_time:.2f}秒，缓存命中: {response3.cache_hit}")


async def export_results_example():
    """导出结果示例"""
    
    orchestrator = SearchOrchestrator()
    
    request = SearchRequest(
        query="深度学习框架",
        max_results=5,
        sources=[SourceType.BING]
    )
    
    response = await orchestrator.search(request)
    
    # 导出为JSON
    results_data = []
    for result in response.results:
        result_dict = {
            'title': result.title,
            'url': result.url,
            'snippet': result.snippet,
            'source': result.source.value,
            'score': result.score,
            'author': result.author,
            'publish_time': result.publish_time.isoformat() if result.publish_time else None,
            'metadata': result.metadata
        }
        results_data.append(result_dict)
    
    export_data = {
        'query': response.query,
        'total_count': response.total_count,
        'execution_time': response.execution_time,
        'timestamp': datetime.now().isoformat(),
        'results': results_data
    }
    
    # 保存到文件
    filename = f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"搜索结果已导出到: {filename}")


async def main():
    """主函数"""
    
    print("=== 增强版Web搜索系统 - 高级示例 ===\n")
    
    examples = [
        ("多源搜索", multi_source_search),
        ("内容提取", content_extraction_example),
        ("私域搜索", private_domain_search),
        ("缓存管理", cache_management_example),
        ("结果导出", export_results_example),
    ]
    
    for name, func in examples:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            await func()
        except Exception as e:
            print(f"示例执行失败: {e}")
        print()


if __name__ == "__main__":
    asyncio.run(main()) 