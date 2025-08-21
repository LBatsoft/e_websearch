"""
Search Agent 使用示例

演示如何使用智能搜索代理进行多跳检索、阶段总结和引用输出
"""

import asyncio
import json
import requests
import time
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SearchAgentClient:
    """Search Agent 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def agent_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """执行 Agent 搜索"""
        url = f"{self.base_url}/agent/search"
        
        # 默认参数
        payload = {
            "query": query,
            "max_iterations": 3,
            "max_results_per_iteration": 10,
            "total_max_results": 30,
            "sources": ["zai"],
            "include_content": True,
            "llm_summary": True,
            "llm_tags": True,
            "llm_per_result": False,
            "llm_language": "zh",
            "model_provider": "auto",
            "model_name": "",
            "planning_strategy": "adaptive",
            "enable_refinement": True,
            "confidence_threshold": 0.7,
            "enable_tracing": True,
            "enable_performance_monitoring": True,
            "timeout": 300,
            "metadata": {}
        }
        
        # 更新参数
        payload.update(kwargs)
        
        print(f"🔍 开始 Agent 搜索: {query}")
        print(f"📋 搜索参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = self.session.post(url, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 搜索失败: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
    
    def get_search_status(self, session_id: str) -> Dict[str, Any]:
        """获取搜索状态"""
        url = f"{self.base_url}/agent/search/{session_id}/status"
        response = self.session.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": response.text}
    
    def cancel_search(self, session_id: str) -> Dict[str, Any]:
        """取消搜索"""
        url = f"{self.base_url}/agent/search/{session_id}/cancel"
        response = self.session.post(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": response.text}
    
    def get_execution_trace(self, session_id: str) -> Dict[str, Any]:
        """获取执行追踪"""
        url = f"{self.base_url}/agent/search/{session_id}/trace"
        response = self.session.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": response.text}
    
    def get_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """获取性能指标"""
        url = f"{self.base_url}/agent/search/{session_id}/metrics"
        response = self.session.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": response.text}


def print_search_results(response: Dict[str, Any]):
    """打印搜索结果"""
    if not response.get("success"):
        print(f"❌ 搜索失败: {response.get('message', '未知错误')}")
        return
    
    print(f"\n✅ 搜索完成!")
    print(f"🆔 会话ID: {response.get('session_id')}")
    print(f"⏱️  总耗时: {response.get('total_execution_time', 0):.2f}秒")
    print(f"🔄 总迭代数: {response.get('total_iterations', 0)}")
    print(f"🔍 总搜索次数: {response.get('total_searches', 0)}")
    print(f"💾 缓存命中: {response.get('cache_hits', 0)}")
    print(f"📊 结果总数: {response.get('total_count', 0)}")
    
    # 打印最终摘要
    if response.get("final_summary"):
        print(f"\n📝 最终摘要:")
        print(f"   {response['final_summary']}")
    
    # 打印最终标签
    if response.get("final_tags"):
        print(f"\n🏷️  相关标签: {', '.join(response['final_tags'])}")
    
    # 打印前几个结果
    results = response.get("results", [])
    if results:
        print(f"\n📋 搜索结果 (显示前5个):")
        for i, result in enumerate(results[:5], 1):
            print(f"\n{i}. {result.get('title', '无标题')}")
            print(f"   🔗 {result.get('url', '')}")
            print(f"   📊 分数: {result.get('score', 0):.2f} | 相关性: {result.get('relevance_score', 0):.2f} | 置信度: {result.get('confidence_score', 0):.2f}")
            print(f"   📄 摘要: {result.get('snippet', '')[:100]}...")
            
            if result.get("llm_summary"):
                print(f"   🤖 AI摘要: {result['llm_summary']}")
            
            if result.get("labels"):
                print(f"   🏷️  标签: {', '.join(result['labels'])}")
            
            if result.get("found_in_step"):
                print(f"   🔍 发现于步骤: {result['found_in_step']} ({result.get('step_type', '')})")
    
    # 打印引用
    citations = response.get("citations", [])
    if citations:
        print(f"\n📚 引用来源 ({len(citations)}个):")
        for i, citation in enumerate(citations[:10], 1):
            print(f"   {i}. {citation}")
    
    # 打印错误和警告
    errors = response.get("errors", [])
    if errors:
        print(f"\n⚠️  错误信息:")
        for error in errors:
            print(f"   - {error}")
    
    warnings = response.get("warnings", [])
    if warnings:
        print(f"\n⚠️  警告信息:")
        for warning in warnings:
            print(f"   - {warning}")


def print_execution_plan(response: Dict[str, Any]):
    """打印执行计划"""
    execution_plan = response.get("execution_plan")
    if not execution_plan:
        return
    
    print(f"\n📋 执行计划:")
    print(f"   计划ID: {execution_plan.get('plan_id')}")
    print(f"   策略: {execution_plan.get('strategy')}")
    print(f"   置信度: {execution_plan.get('confidence_score', 0):.2f}")
    print(f"   步骤数: {len(execution_plan.get('steps', []))}")
    
    steps = execution_plan.get("steps", [])
    for i, step in enumerate(steps, 1):
        print(f"\n   步骤 {i}: {step.get('description')}")
        print(f"      类型: {step.get('step_type')}")
        print(f"      状态: {step.get('status')}")
        print(f"      查询: {step.get('query')}")
        print(f"      结果数: {step.get('results_count', 0)}")
        if step.get("execution_time"):
            print(f"      耗时: {step['execution_time']:.2f}秒")
        if step.get("confidence_score"):
            print(f"      置信度: {step['confidence_score']:.2f}")


def print_performance_metrics(metrics: Dict[str, Any]):
    """打印性能指标"""
    if not metrics.get("success"):
        return
    
    data = metrics.get("metrics", {})
    if not data:
        return
    
    print(f"\n📊 性能指标:")
    print(f"   总时长: {data.get('total_duration', 0):.2f}秒")
    print(f"   API调用数: {data.get('total_api_calls', 0)}")
    print(f"   缓存命中率: {data.get('cache_hit_rate', 0):.2%}")
    print(f"   平均步骤时间: {data.get('avg_step_time', 0):.2f}秒")
    print(f"   平均搜索时间: {data.get('avg_search_time', 0):.2f}秒")
    print(f"   平均LLM时间: {data.get('avg_llm_time', 0):.2f}秒")
    print(f"   性能分数: {data.get('performance_score', 0):.2f}")


def example_basic_search():
    """基础搜索示例"""
    print("=" * 60)
    print("🔍 基础 Agent 搜索示例")
    print("=" * 60)
    
    client = SearchAgentClient()
    
    # 执行搜索
    response = client.agent_search(
        query="人工智能在医疗领域的应用",
        max_iterations=2,
        total_max_results=20,
        planning_strategy="iterative"
    )
    
    # 打印结果
    print_search_results(response)
    print_execution_plan(response)
    
    # 获取性能指标
    if response.get("success") and response.get("session_id"):
        session_id = response["session_id"]
        metrics = client.get_performance_metrics(session_id)
        print_performance_metrics(metrics)


def example_comparison_search():
    """对比搜索示例"""
    print("\n" + "=" * 60)
    print("🔍 对比搜索示例")
    print("=" * 60)
    
    client = SearchAgentClient()
    
    # 执行对比搜索
    response = client.agent_search(
        query="ChatGPT vs Claude 对比分析",
        max_iterations=3,
        total_max_results=25,
        planning_strategy="iterative",
        confidence_threshold=0.6
    )
    
    # 打印结果
    print_search_results(response)
    print_execution_plan(response)


def example_deep_dive_search():
    """深度搜索示例"""
    print("\n" + "=" * 60)
    print("🔍 深度搜索示例")
    print("=" * 60)
    
    client = SearchAgentClient()
    
    # 执行深度搜索
    response = client.agent_search(
        query="区块链技术详细介绍",
        max_iterations=4,
        total_max_results=30,
        planning_strategy="adaptive",
        llm_per_result=True,  # 为每个结果生成LLM增强
        confidence_threshold=0.8
    )
    
    # 打印结果
    print_search_results(response)
    print_execution_plan(response)


def example_parallel_search():
    """并行搜索示例"""
    print("\n" + "=" * 60)
    print("🔍 并行搜索示例")
    print("=" * 60)
    
    client = SearchAgentClient()
    
    # 执行并行搜索
    response = client.agent_search(
        query="量子计算 机器学习 应用前景",
        max_iterations=3,
        total_max_results=40,
        planning_strategy="parallel",
        sources=["zai", "bing"],  # 使用多个搜索源
        enable_refinement=True
    )
    
    # 打印结果
    print_search_results(response)
    print_execution_plan(response)


def example_trace_analysis():
    """执行追踪分析示例"""
    print("\n" + "=" * 60)
    print("🔍 执行追踪分析示例")
    print("=" * 60)
    
    client = SearchAgentClient()
    
    # 执行搜索
    response = client.agent_search(
        query="自然语言处理最新进展",
        max_iterations=2,
        enable_tracing=True,
        enable_performance_monitoring=True
    )
    
    if response.get("success") and response.get("session_id"):
        session_id = response["session_id"]
        
        # 获取执行追踪
        trace = client.get_execution_trace(session_id)
        if trace.get("success"):
            print(f"\n📊 执行追踪分析:")
            trace_summary = trace.get("trace_summary", {})
            print(f"   总事件数: {trace_summary.get('total_events', 0)}")
            print(f"   执行步骤数: {trace_summary.get('steps_executed', 0)}")
            print(f"   错误数: {trace_summary.get('errors_count', 0)}")
            print(f"   决策数: {trace_summary.get('decisions_count', 0)}")
            print(f"   执行时长: {trace_summary.get('duration', 0):.2f}秒")
            
            # 显示关键事件
            events = trace.get("trace_events", [])
            key_events = [e for e in events if e.get("event_type") in ["session_start", "step_start", "step_complete", "decision", "session_end"]]
            
            print(f"\n📋 关键执行事件:")
            for event in key_events[:10]:  # 显示前10个事件
                event_type = event.get("event_type", "unknown")
                timestamp = event.get("timestamp", 0)
                data = event.get("data", {})
                
                if event_type == "session_start":
                    print(f"   🚀 会话开始: {data.get('start_time', '')}")
                elif event_type == "step_start":
                    print(f"   ▶️  步骤开始: {data.get('description', '')} ({data.get('step_type', '')})")
                elif event_type == "step_complete":
                    print(f"   ✅ 步骤完成: 状态={data.get('status', '')}, 结果数={data.get('results_count', 0)}, 耗时={data.get('execution_time', 0):.2f}s")
                elif event_type == "decision":
                    print(f"   🤔 决策: {data.get('decision_type', '')} - {data}")
                elif event_type == "session_end":
                    print(f"   🏁 会话结束: 状态={data.get('final_status', '')}, 总结果数={data.get('total_results', 0)}")


def main():
    """主函数"""
    print("🤖 Search Agent 使用示例")
    print("=" * 60)
    
    try:
        # 检查服务是否可用
        client = SearchAgentClient()
        health_response = client.session.get(f"{client.base_url}/agent/health")
        
        if health_response.status_code != 200:
            print("❌ Search Agent 服务不可用，请确保服务已启动")
            print("   启动命令: python run_api.py")
            return
        
        print("✅ Search Agent 服务可用")
        
        # 运行示例
        example_basic_search()
        example_comparison_search()
        example_deep_dive_search()
        example_parallel_search()
        example_trace_analysis()
        
        print("\n" + "=" * 60)
        print("🎉 所有示例执行完成!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 Search Agent 服务")
        print("   请确保服务已启动: python run_api.py")
    except Exception as e:
        print(f"❌ 执行示例时出错: {e}")


if __name__ == "__main__":
    main()
