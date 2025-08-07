#!/usr/bin/env python3
"""
E-WebSearch API 客户端示例
"""

import requests
import json
import time
from typing import Dict, List, Any


class EWebSearchClient:
    """E-WebSearch API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'EWebSearch-Client/1.0'
        })
    
    def search(self, 
               query: str, 
               max_results: int = 10,
               sources: List[str] = None,
               filters: Dict[str, Any] = None,
               include_content: bool = False) -> Dict[str, Any]:
        """执行搜索"""
        
        if sources is None:
            sources = ["zai"]
        
        if filters is None:
            filters = {}
        
        data = {
            "query": query,
            "max_results": max_results,
            "include_content": include_content,
            "sources": sources,
            "filters": filters
        }
        
        try:
            response = self.session.post(f"{self.base_url}/search", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"请求失败: {e}",
                "results": [],
                "total_count": 0
            }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_suggestions(self, query: str) -> Dict[str, Any]:
        """获取搜索建议"""
        try:
            response = self.session.post(
                f"{self.base_url}/suggestions", 
                json={"query": query}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "suggestions": [],
                "query": query
            }
    
    def clear_cache(self) -> Dict[str, Any]:
        """清空缓存"""
        try:
            response = self.session.delete(f"{self.base_url}/cache")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"清空缓存失败: {e}"
            }


def demo_search_examples():
    """演示搜索示例"""
    
    client = EWebSearchClient()
    
    print("🔍 E-WebSearch API 客户端演示")
    print("=" * 50)
    
    # 1. 健康检查
    print("\n1. 📊 健康检查")
    health = client.health_check()
    print(f"状态: {health.get('status', '未知')}")
    print(f"可用搜索源: {health.get('available_sources', [])}")
    
    if health.get('status') != 'healthy':
        print("❌ 服务不可用，请检查 API 服务是否正常运行")
        return
    
    # 2. 基础搜索
    print("\n2. 🔍 基础搜索")
    result = client.search(
        query="Python编程教程",
        max_results=3,
        sources=["zai"]
    )
    
    if result['success']:
        print(f"✅ 搜索成功，找到 {result['total_count']} 个结果")
        print(f"⏱️ 执行时间: {result['execution_time']:.2f}秒")
        print(f"🎯 缓存命中: {'是' if result['cache_hit'] else '否'}")
        
        for i, item in enumerate(result['results'], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   📄 {item['snippet'][:100]}...")
            print(f"   🔗 {item['url']}")
            print(f"   📊 得分: {item['score']:.2f}")
    else:
        print(f"❌ 搜索失败: {result['message']}")
    
    # 3. 带过滤器的搜索
    print("\n3. 🎯 带过滤器的搜索")
    result = client.search(
        query="人工智能最新发展",
        max_results=5,
        sources=["zai"],
        filters={
            "time_range": "month",
            "content_size": "high"
        }
    )
    
    if result['success']:
        print(f"✅ 过滤搜索成功，找到 {result['total_count']} 个结果")
        for i, item in enumerate(result['results'][:2], 1):
            print(f"{i}. {item['title'][:60]}...")
    
    # 4. 搜索建议
    print("\n4. 💡 搜索建议")
    suggestions = client.get_suggestions("机器学习")
    
    if suggestions['success'] and suggestions['suggestions']:
        print("建议词:")
        for suggestion in suggestions['suggestions'][:5]:
            print(f"  - {suggestion}")
    else:
        print("暂无搜索建议")
    
    # 5. 性能测试
    print("\n5. ⚡ 性能测试")
    start_time = time.time()
    
    queries = ["AI技术", "区块链", "云计算"]
    for query in queries:
        result = client.search(query, max_results=3)
        status = "✅" if result['success'] else "❌"
        print(f"{status} {query}: {result.get('total_count', 0)} 个结果")
    
    total_time = time.time() - start_time
    print(f"🏃 总耗时: {total_time:.2f}秒")
    
    print("\n" + "=" * 50)
    print("🎉 演示完成!")


def interactive_search():
    """交互式搜索"""
    
    client = EWebSearchClient()
    
    print("🔍 E-WebSearch 交互式搜索")
    print("输入 'quit' 退出，'health' 检查健康状态")
    print("=" * 50)
    
    while True:
        try:
            query = input("\n请输入搜索词: ").strip()
            
            if query.lower() == 'quit':
                print("👋 再见!")
                break
            
            if query.lower() == 'health':
                health = client.health_check()
                print(f"状态: {health.get('status', '未知')}")
                continue
            
            if not query:
                print("请输入有效的搜索词")
                continue
            
            print(f"🔍 搜索: {query}")
            result = client.search(query, max_results=5)
            
            if result['success']:
                print(f"✅ 找到 {result['total_count']} 个结果 (耗时: {result['execution_time']:.2f}秒)")
                
                for i, item in enumerate(result['results'], 1):
                    print(f"\n{i}. {item['title']}")
                    print(f"   {item['snippet'][:150]}...")
                    print(f"   🔗 {item['url']}")
            else:
                print(f"❌ 搜索失败: {result['message']}")
                
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


def benchmark_test():
    """性能基准测试"""
    
    client = EWebSearchClient()
    
    print("⚡ E-WebSearch API 性能基准测试")
    print("=" * 50)
    
    test_queries = [
        "Python编程",
        "人工智能",
        "机器学习",
        "数据科学",
        "Web开发"
    ]
    
    total_time = 0
    total_results = 0
    successful_queries = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 测试查询: {query}")
        
        start_time = time.time()
        result = client.search(query, max_results=10)
        end_time = time.time()
        
        duration = end_time - start_time
        total_time += duration
        
        if result['success']:
            successful_queries += 1
            total_results += result['total_count']
            cache_status = "缓存命中" if result['cache_hit'] else "无缓存"
            
            print(f"   ✅ 成功 - {result['total_count']} 个结果")
            print(f"   ⏱️ 耗时: {duration:.2f}秒 ({cache_status})")
        else:
            print(f"   ❌ 失败: {result['message']}")
    
    print(f"\n📊 基准测试结果:")
    print(f"   成功查询: {successful_queries}/{len(test_queries)}")
    print(f"   总结果数: {total_results}")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   平均耗时: {total_time/len(test_queries):.2f}秒/查询")
    print(f"   查询成功率: {successful_queries/len(test_queries)*100:.1f}%")


def main():
    """主函数"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="E-WebSearch API 客户端")
    parser.add_argument("--demo", action="store_true", help="运行演示")
    parser.add_argument("--interactive", action="store_true", help="交互式搜索")
    parser.add_argument("--benchmark", action="store_true", help="性能基准测试")
    parser.add_argument("--query", help="执行单次搜索")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API 服务地址")
    
    args = parser.parse_args()
    
    # 更新客户端 API 地址
    global client
    client = EWebSearchClient(args.api_url)
    
    if args.demo:
        demo_search_examples()
    elif args.interactive:
        interactive_search()
    elif args.benchmark:
        benchmark_test()
    elif args.query:
        client = EWebSearchClient(args.api_url)
        result = client.search(args.query)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("请指定操作: --demo, --interactive, --benchmark, 或 --query")
        parser.print_help()


if __name__ == "__main__":
    main()