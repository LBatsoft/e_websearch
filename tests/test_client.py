#!/usr/bin/env python3
"""
E-WebSearch API 客户端测试脚本
"""

import requests
import json
import time

def test_api_service(base_url="http://localhost:8001"):
    """测试 API 服务"""
    
    print("🧪 E-WebSearch API 测试")
    print("=" * 50)
    print(f"📍 API 地址: {base_url}")
    
    # 1. 测试根路径
    print("\n1. 📋 测试根路径")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务名称: {data['name']}")
            print(f"✅ 版本: {data['version']}")
            print(f"✅ 状态: {data['status']}")
        else:
            print(f"❌ 错误: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        return
    
    # 2. 测试健康检查
    print("\n2. 🏥 测试健康检查")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康状态: {data['status']}")
            print(f"✅ 消息: {data['message']}")
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查错误: {e}")
    
    # 3. 测试搜索功能
    print("\n3. 🔍 测试搜索功能")
    test_queries = [
        {"query": "Python编程", "max_results": 3},
        {"query": "人工智能", "max_results": 5},
        {"query": "机器学习", "max_results": 2}
    ]
    
    for i, search_data in enumerate(test_queries, 1):
        print(f"\n  测试 {i}: {search_data['query']}")
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/search",
                json=search_data,
                headers={"Content-Type": "application/json"}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ 成功: 找到 {data['total_count']} 个结果")
                print(f"  ⏱️ 响应时间: {duration:.3f}秒")
                print(f"  📊 执行时间: {data['execution_time']:.6f}秒")
                
                # 显示前2个结果
                for j, result in enumerate(data['results'][:2], 1):
                    print(f"    {j}. {result['title']}")
                    print(f"       🔗 {result['url']}")
                    print(f"       📄 {result['snippet'][:50]}...")
                    print(f"       📊 得分: {result['score']}")
            else:
                print(f"  ❌ 搜索失败: HTTP {response.status_code}")
                print(f"  📄 响应: {response.text}")
                
        except Exception as e:
            print(f"  ❌ 搜索错误: {e}")
    
    # 4. 性能测试
    print("\n4. ⚡ 性能测试")
    performance_queries = ["AI", "编程", "技术", "开发", "算法"]
    total_time = 0
    successful_requests = 0
    
    for query in performance_queries:
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/search",
                json={"query": query, "max_results": 5},
                headers={"Content-Type": "application/json"}
            )
            duration = time.time() - start_time
            total_time += duration
            
            if response.status_code == 200:
                successful_requests += 1
                print(f"  ✅ {query}: {duration:.3f}秒")
            else:
                print(f"  ❌ {query}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ {query}: {e}")
    
    print(f"\n📊 性能统计:")
    print(f"  成功请求: {successful_requests}/{len(performance_queries)}")
    print(f"  总耗时: {total_time:.3f}秒")
    if successful_requests > 0:
        print(f"  平均响应时间: {total_time/successful_requests:.3f}秒")
    
    # 5. 错误处理测试
    print("\n5. 🚨 错误处理测试")
    
    # 测试无效请求
    print("  测试无效JSON:")
    try:
        response = requests.post(
            f"{base_url}/search",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        print(f"  状态码: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    
    # 测试缺失参数
    print("  测试缺失参数:")
    try:
        response = requests.post(
            f"{base_url}/search",
            json={},
            headers={"Content-Type": "application/json"}
        )
        print(f"  状态码: {response.status_code}")
        if response.status_code == 422:
            print("  ✅ 正确返回验证错误")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API 测试完成!")


def interactive_test():
    """交互式测试"""
    
    base_url = "http://localhost:8001"
    
    print("🔍 E-WebSearch API 交互式测试")
    print(f"📍 API 地址: {base_url}")
    print("输入 'quit' 退出")
    print("=" * 50)
    
    while True:
        try:
            query = input("\n请输入搜索词: ").strip()
            
            if query.lower() == 'quit':
                print("👋 再见!")
                break
            
            if not query:
                print("请输入有效的搜索词")
                continue
            
            try:
                response = requests.post(
                    f"{base_url}/search",
                    json={"query": query, "max_results": 5},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"\n✅ 找到 {data['total_count']} 个结果:")
                    
                    for i, result in enumerate(data['results'], 1):
                        print(f"\n{i}. {result['title']}")
                        print(f"   🔗 {result['url']}")
                        print(f"   📄 {result['snippet']}")
                        print(f"   📊 得分: {result['score']}")
                else:
                    print(f"❌ 搜索失败: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 请求错误: {e}")
                
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break


def main():
    """主函数"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="E-WebSearch API 客户端测试")
    parser.add_argument("--test", action="store_true", help="运行完整测试")
    parser.add_argument("--interactive", action="store_true", help="交互式测试")
    parser.add_argument("--url", default="http://localhost:8001", help="API 服务地址")
    
    args = parser.parse_args()
    
    if args.test:
        test_api_service(args.url)
    elif args.interactive:
        interactive_test()
    else:
        print("请选择操作:")
        print("  --test       运行完整测试")
        print("  --interactive 交互式测试")
        parser.print_help()


if __name__ == "__main__":
    main()