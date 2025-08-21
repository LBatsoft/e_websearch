"""
Search Agent 功能测试脚本
"""

import requests
import json
import time
from typing import Dict, Any


class SearchAgentTester:
    """Search Agent 测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health_check(self) -> bool:
        """测试服务健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/agent/health")
            if response.status_code == 200:
                print("✅ API服务健康检查通过")
                return True
            else:
                print(f"❌ API服务健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接到API服务: {e}")
            return False
    
    def test_basic_search(self) -> Dict[str, Any]:
        """测试基础搜索功能"""
        print("\n🔍 测试基础搜索功能...")
        
        payload = {
            "query": "人工智能最新发展",
            "max_iterations": 2,
            "max_results_per_iteration": 5,
            "total_max_results": 10,
            "sources": ["zai"],
            "include_content": True,
            "llm_summary": True,
            "llm_tags": True,
            "llm_language": "zh",
            "planning_strategy": "iterative",
            "enable_refinement": True,
            "confidence_threshold": 0.6,
            "enable_tracing": True,
            "enable_performance_monitoring": True,
            "timeout": 120
        }
        
        try:
            print(f"📋 搜索查询: {payload['query']}")
            print(f"📊 参数配置: 最大迭代={payload['max_iterations']}, 最大结果={payload['total_max_results']}")
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/agent/search", json=payload)
            end_time = time.time()
            
            print(f"⏱️  请求耗时: {end_time - start_time:.2f}秒")
            
            if response.status_code == 200:
                result = response.json()
                self._print_search_results(result)
                return result
            else:
                print(f"❌ 搜索失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ 搜索过程中出错: {e}")
            return {"success": False, "error": str(e)}
    
    def test_search_with_tracing(self) -> Dict[str, Any]:
        """测试带追踪的搜索"""
        print("\n🔍 测试带追踪的搜索...")
        
        payload = {
            "query": "机器学习算法比较",
            "max_iterations": 2,
            "max_results_per_iteration": 3,
            "total_max_results": 6,
            "sources": ["zai"],
            "planning_strategy": "adaptive",
            "enable_tracing": True,
            "enable_performance_monitoring": True,
            "timeout": 90
        }
        
        try:
            response = self.session.post(f"{self.base_url}/agent/search", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                session_id = result.get("session_id")
                
                if session_id:
                    # 获取执行追踪
                    self._test_execution_trace(session_id)
                    # 获取性能指标
                    self._test_performance_metrics(session_id)
                
                return result
            else:
                print(f"❌ 搜索失败: {response.status_code}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ 搜索过程中出错: {e}")
            return {"success": False, "error": str(e)}
    
    def _test_execution_trace(self, session_id: str):
        """测试执行追踪"""
        try:
            response = self.session.get(f"{self.base_url}/agent/search/{session_id}/trace")
            if response.status_code == 200:
                trace_data = response.json()
                print(f"\n📊 执行追踪数据:")
                if trace_data.get("success"):
                    trace_summary = trace_data.get("trace_summary", {})
                    print(f"   总事件数: {trace_summary.get('total_events', 0)}")
                    print(f"   执行步骤数: {trace_summary.get('steps_executed', 0)}")
                    print(f"   决策数: {trace_summary.get('decisions_count', 0)}")
                    print(f"   执行时长: {trace_summary.get('duration', 0):.2f}秒")
                else:
                    print("   ❌ 获取追踪数据失败")
            else:
                print(f"   ❌ 获取追踪失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 获取追踪数据出错: {e}")
    
    def _test_performance_metrics(self, session_id: str):
        """测试性能指标"""
        try:
            response = self.session.get(f"{self.base_url}/agent/search/{session_id}/metrics")
            if response.status_code == 200:
                metrics_data = response.json()
                print(f"\n📈 性能指标:")
                if metrics_data.get("success"):
                    metrics = metrics_data.get("metrics", {})
                    print(f"   总时长: {metrics.get('total_duration', 0):.2f}秒")
                    print(f"   API调用数: {metrics.get('total_api_calls', 0)}")
                    print(f"   缓存命中率: {metrics.get('cache_hit_rate', 0):.2%}")
                    print(f"   平均步骤时间: {metrics.get('avg_step_time', 0):.2f}秒")
                    print(f"   性能分数: {metrics.get('performance_score', 0):.2f}")
                else:
                    print("   ❌ 获取性能指标失败")
            else:
                print(f"   ❌ 获取性能指标失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 获取性能指标出错: {e}")
    
    def _print_search_results(self, response: Dict[str, Any]):
        """打印搜索结果"""
        if not response.get("success"):
            print(f"❌ 搜索失败: {response.get('message', '未知错误')}")
            errors = response.get("errors", [])
            if errors:
                print("错误详情:")
                for error in errors:
                    print(f"   - {error}")
            return
        
        print(f"\n✅ 搜索成功完成!")
        print(f"🆔 会话ID: {response.get('session_id', 'N/A')}")
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
        
        # 打印搜索结果
        results = response.get("results", [])
        if results:
            print(f"\n📋 搜索结果 (显示前3个):")
            for i, result in enumerate(results[:3], 1):
                print(f"\n{i}. {result.get('title', '无标题')}")
                print(f"   🔗 URL: {result.get('url', 'N/A')}")
                print(f"   📊 分数: {result.get('score', 0):.2f}")
                print(f"   📄 摘要: {result.get('snippet', 'N/A')[:100]}...")
                
                if result.get("relevance_score"):
                    print(f"   🎯 相关性: {result['relevance_score']:.2f}")
                
                if result.get("confidence_score"):
                    print(f"   🔒 置信度: {result['confidence_score']:.2f}")
                
                if result.get("llm_summary"):
                    print(f"   🤖 AI摘要: {result['llm_summary']}")
        
        # 打印引用来源
        citations = response.get("citations", [])
        if citations:
            print(f"\n📚 引用来源 ({len(citations)}个):")
            for i, citation in enumerate(citations[:5], 1):
                print(f"   {i}. {citation}")
        
        # 打印执行计划信息
        execution_state = response.get("execution_state")
        if execution_state and execution_state.get("plan"):
            plan = execution_state["plan"]
            print(f"\n📋 执行计划:")
            print(f"   策略: {plan.get('strategy', 'N/A')}")
            print(f"   置信度: {plan.get('confidence_score', 0):.2f}")
            print(f"   步骤数: {len(plan.get('steps', []))}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🤖 开始测试 Search Agent 功能")
        print("=" * 60)
        
        # 1. 健康检查
        if not self.test_health_check():
            print("❌ 服务不可用，测试终止")
            return False
        
        # 2. 基础搜索测试
        basic_result = self.test_basic_search()
        
        # 3. 带追踪的搜索测试
        trace_result = self.test_search_with_tracing()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试完成!")
        
        # 测试结果总结
        basic_success = basic_result.get("success", False)
        trace_success = trace_result.get("success", False)
        
        print(f"📊 测试结果总结:")
        print(f"   基础搜索测试: {'✅ 通过' if basic_success else '❌ 失败'}")
        print(f"   追踪搜索测试: {'✅ 通过' if trace_success else '❌ 失败'}")
        
        overall_success = basic_success and trace_success
        print(f"   整体测试结果: {'✅ 全部通过' if overall_success else '❌ 存在失败'}")
        
        return overall_success


def main():
    """主函数"""
    tester = SearchAgentTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Search Agent 功能测试全部通过!")
    else:
        print("\n⚠️  Search Agent 功能测试存在问题，请检查日志")


if __name__ == "__main__":
    main()
