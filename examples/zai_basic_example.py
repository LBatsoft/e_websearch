"""
ZAI Search Pro 基础使用示例
"""

import asyncio
import os
import sys

# 添加项目路径到 Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# 直接导入模块
try:
    from search_orchestrator import SearchOrchestrator
    from models import SearchRequest, SourceType
except ImportError:
    # 如果直接导入失败，尝试从上级目录导入
    sys.path.insert(0, os.path.dirname(project_root))
    from e_websearch.search_orchestrator import SearchOrchestrator
    from e_websearch.models import SearchRequest, SourceType


async def basic_zai_search():
    """基础 ZAI 搜索示例"""
    
    # 设置 API 密钥（请替换为您的实际密钥）
    # os.environ["ZAI_API_KEY"] = "your-zai-api-key-here"
    
    print("🔍 ZAI Search Pro 基础搜索示例")
    
    # 初始化搜索协调器
    orchestrator = SearchOrchestrator()
    
    # 创建搜索请求
    request = SearchRequest(
        query="2025年4月的财经新闻",
        max_results=10,
        include_content=False,  # 不提取详细内容以提高速度
        sources=[SourceType.ZAI],  # 仅使用 ZAI 搜索
        filters={
            'time_range': 'month',  # 搜索最近一个月
            'domain': 'www.sohu.com',  # 仅搜索搜狐网站（可选）
        }
    )
    
    print(f"搜索查询: {request.query}")
    print(f"搜索源: {[s.value for s in request.sources]}")
    
    try:
        # 执行搜索
        response = await orchestrator.search(request)
        
        print(f"\n✓ 搜索完成!")
        print(f"耗时: {response.execution_time:.2f}秒")
        print(f"结果数量: {len(response.results)}")
        print(f"缓存命中: {'是' if response.cache_hit else '否'}")
        
        # 显示搜索结果
        if response.results:
            print(f"\n📄 搜索结果:")
            for i, result in enumerate(response.results, 1):
                print(f"\n{i}. {result.title}")
                print(f"   URL: {result.url}")
                print(f"   摘要: {result.snippet[:150]}...")
                print(f"   得分: {result.score:.2f}")
                
                if result.author:
                    print(f"   作者: {result.author}")
                
                if result.publish_time:
                    print(f"   发布时间: {result.publish_time}")
        else:
            print("未找到搜索结果")
            
    except Exception as e:
        print(f"❌ 搜索失败: {e}")


async def multi_source_search():
    """多源搜索示例（ZAI + 其他源）"""
    
    print(f"\n{'='*50}")
    print("多源搜索示例 (ZAI + 微信公众号)")
    print('='*50)
    
    orchestrator = SearchOrchestrator()
    
    # 多源搜索请求
    request = SearchRequest(
        query="教育政策解读",
        max_results=5,
        include_content=False,
        sources=[SourceType.ZAI, SourceType.WECHAT],  # ZAI + 微信公众号
    )
    
    try:
        response = await orchestrator.search(request)
        
        print(f"总结果数量: {len(response.results)}")
        print(f"使用的搜索源: {[s.value for s in response.sources_used]}")
        
        # 按来源分组显示
        results_by_source = {}
        for result in response.results:
            source = result.source.value
            if source not in results_by_source:
                results_by_source[source] = []
            results_by_source[source].append(result)
        
        for source, results in results_by_source.items():
            print(f"\n📰 {source.upper()} 搜索结果 ({len(results)} 个):")
            for i, result in enumerate(results[:3], 1):  # 显示前3个
                print(f"  {i}. {result.title[:60]}...")
                print(f"     URL: {result.url}")
                
    except Exception as e:
        print(f"❌ 多源搜索失败: {e}")


async def search_with_filters():
    """带过滤器的搜索示例"""
    
    print(f"\n{'='*50}")
    print("带过滤器的搜索示例")
    print('='*50)
    
    orchestrator = SearchOrchestrator()
    
    # 带过滤器的搜索
    request = SearchRequest(
        query="人工智能",
        max_results=8,
        include_content=False,
        sources=[SourceType.ZAI],
        filters={
            'time_range': 'week',  # 最近一周的内容
            'domain': 'tech.sina.com.cn',  # 指定域名过滤
            'content_size': 'high'  # 高质量摘要
        }
    )
    
    print(f"搜索条件:")
    print(f"  - 查询: {request.query}")
    print(f"  - 时间范围: {request.filters.get('time_range', '无限制')}")
    print(f"  - 域名过滤: {request.filters.get('domain', '无限制')}")
    
    try:
        response = await orchestrator.search(request)
        
        print(f"\n结果: 找到 {len(response.results)} 个相关内容")
        
        for i, result in enumerate(response.results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   📊 得分: {result.score:.2f}")
            print(f"   🔗 {result.url}")
            
            # 显示元数据
            if result.metadata:
                media = result.metadata.get('media', {})
                if media and media.get('name'):
                    print(f"   📰 媒体: {media['name']}")
                    
    except Exception as e:
        print(f"❌ 过滤搜索失败: {e}")


async def main():
    """主函数"""
    
    # 检查 API 密钥
    if not os.getenv("ZAI_API_KEY"):
        print("⚠️  请设置 ZAI_API_KEY 环境变量")
        print("   例如: export ZAI_API_KEY='your-api-key'")
        print("   或在代码中设置: os.environ['ZAI_API_KEY'] = 'your-api-key'")
        return
    
    # 运行示例
    examples = [
        ("基础 ZAI 搜索", basic_zai_search),
        ("多源搜索", multi_source_search),
        ("带过滤器搜索", search_with_filters),
    ]
    
    for name, func in examples:
        print(f"\n🚀 运行示例: {name}")
        try:
            await func()
        except Exception as e:
            print(f"❌ 示例运行失败: {e}")
        
        print("\n" + "="*60)
    
    print("🎉 所有示例运行完成!")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())