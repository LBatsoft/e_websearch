"""
Multi Agent System 测试脚本

测试多智能体搜索系统的功能和性能
"""

import requests
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MultiAgentTester:
    """Multi Agent 测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_system_info(self) -> Dict[str, Any]:
        """测试系统信息获取"""
        try:
            response = self.session.get(f"{self.base_url}/agent/system-info")
            if response.status_code == 200:
                info = response.json()
                print("✅ 系统信息获取成功")
                print(f"   单个Agent: {'可用' if info['single_agent']['available'] else '不可用'}")
                print(f"   多智能体: {'可用' if info['multi_agent']['available'] else '不可用'}")
                print(f"   默认模式: {info['default_mode']}")
                print(f"   版本: {info['version']}")
                
                if info['multi_agent']['available']:
                    ma_info = info['multi_agent']
                    print(f"   Agent总数: {ma_info.get('total_agents', 0)}")
                    print(f"   Agent类型: {ma_info.get('agent_types', [])}")
                    print(f"   协调器ID: {ma_info.get('coordinator_id', 'N/A')}")
                
                return info
            else:
                print(f"❌ 系统信息获取失败: {response.status_code}")
                return {"success": False, "error": response.text}
        except Exception as e:
            print(f"❌ 系统信息获取出错: {e}")
            return {"success": False, "error": str(e)}
    
    def test_health_check(self) -> bool:
        """测试健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/agent/health")
            if response.status_code == 200:
                health = response.json()
                print("✅ 健康检查通过")
                print(f"   整体状态: {health['status']}")
                print(f"   服务: {health['service']}")
                print(f"   版本: {health['version']}")
                
                modes = health.get('modes', {})
                print(f"   单个Agent: {modes.get('single_agent', 'unknown')}")
                print(f"   多智能体: {modes.get('multi_agent', 'unknown')}")
                
                features = health.get('features', {})
                print(f"   并行处理: {'✓' if features.get('parallel_processing') else '✗'}")
                print(f"   专门化Agent: {'✓' if features.get('specialized_agents') else '✗'}")
                
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查出错: {e}")
            return False
    
    def test_multi_agent_search(self) -> Dict[str, Any]:
        """测试多智能体搜索"""
        print("\n🔍 测试多智能体搜索功能...")
        
        payload = {
            "query": "人工智能在医疗领域的应用",
            "max_iterations": 2,
            "max_results_per_iteration": 8,
            "total_max_results": 16,
            "sources": ["zai"],
            "include_content": True,
            "llm_summary": True,
            "llm_tags": True,
            "llm_per_result": False,
            "llm_language": "zh",
            "model_provider": "auto",
            "model_name": "",
            "planning_strategy": "parallel",  # 使用并行策略
            "enable_refinement": True,
            "confidence_threshold": 0.6,
            "enable_tracing": True,
            "enable_performance_monitoring": True,
            "timeout": 120
        }
        
        try:
            print(f"📋 搜索查询: {payload['query']}")
            print(f"📊 参数配置: 策略={payload['planning_strategy']}, 最大结果={payload['total_max_results']}")
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/agent/multi-search", json=payload)
            end_time = time.time()
            
            print(f"⏱️  请求耗时: {end_time - start_time:.2f}秒")
            
            if response.status_code == 200:
                result = response.json()
                self._print_multi_agent_results(result)
                return result
            else:
                print(f"❌ 多智能体搜索失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ 多智能体搜索过程中出错: {e}")
            return {"success": False, "error": str(e)}
    
    def test_multi_agent_with_tracing(self) -> Dict[str, Any]:
        """测试带追踪的多智能体搜索"""
        print("\n🔍 测试带追踪的多智能体搜索...")
        
        payload = {
            "query": "机器学习算法对比分析",
            "max_iterations": 2,
            "max_results_per_iteration": 6,
            "total_max_results": 12,
            "sources": ["zai"],
            "planning_strategy": "adaptive",
            "enable_tracing": True,
            "enable_performance_monitoring": True,
            "timeout": 90
        }
        
        try:
            response = self.session.post(f"{self.base_url}/agent/multi-search", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                session_id = result.get("session_id")
                
                if session_id:
                    # 获取多智能体状态
                    self._test_multi_agent_status(session_id)
                    # 获取执行追踪
                    self._test_multi_agent_trace(session_id)
                    # 获取性能指标
                    self._test_multi_agent_metrics(session_id)
                
                return result
            else:
                print(f"❌ 多智能体搜索失败: {response.status_code}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ 多智能体搜索过程中出错: {e}")
            return {"success": False, "error": str(e)}
    
    def _test_multi_agent_status(self, session_id: str):
        """测试多智能体状态"""
        try:
            response = self.session.get(f"{self.base_url}/agent/multi-search/{session_id}/status")
            if response.status_code == 200:
                status_data = response.json()
                print(f"\n📊 多智能体状态:")
                if status_data.get("success"):
                    metadata = status_data.get("metadata", {})
                    print(f"   会话状态: {status_data.get('status', 'unknown')}")
                    print(f"   执行时间: {status_data.get('execution_time', 0):.2f}秒")
                    print(f"   结果数量: {status_data.get('results_count', 0)}")
                    print(f"   活跃Agent: {metadata.get('active_agents', [])}")
                    print(f"   任务总数: {metadata.get('task_count', 0)}")
                    print(f"   完成任务: {metadata.get('completed_tasks', 0)}")
                    print(f"   失败任务: {metadata.get('failed_tasks', 0)}")
                else:
                    print("   ❌ 获取状态失败")
            else:
                print(f"   ❌ 获取状态失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 获取状态出错: {e}")
    
    def _test_multi_agent_trace(self, session_id: str):
        """测试多智能体追踪"""
        try:
            response = self.session.get(f"{self.base_url}/agent/multi-search/{session_id}/trace")
            if response.status_code == 200:
                trace_data = response.json()
                print(f"\n📊 多智能体执行追踪:")
                if trace_data.get("success"):
                    trace_summary = trace_data.get("trace_summary", {})
                    print(f"   总事件数: {trace_summary.get('total_events', 0)}")
                    print(f"   会话类型: {trace_summary.get('session_type', 'unknown')}")
                    print(f"   多智能体: {trace_summary.get('multi_agent', False)}")
                    
                    # 显示部分追踪事件
                    events = trace_data.get("trace_events", [])
                    if events:
                        print(f"   最新事件 (显示前3个):")
                        for event in events[:3]:
                            event_type = event.get("event_type", "unknown")
                            timestamp = event.get("timestamp", 0)
                            print(f"     - {event_type} @ {timestamp}")
                else:
                    print("   ❌ 获取追踪数据失败")
            else:
                print(f"   ❌ 获取追踪失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 获取追踪数据出错: {e}")
    
    def _test_multi_agent_metrics(self, session_id: str):
        """测试多智能体性能指标"""
        try:
            response = self.session.get(f"{self.base_url}/agent/multi-search/{session_id}/metrics")
            if response.status_code == 200:
                metrics_data = response.json()
                print(f"\n📈 多智能体性能指标:")
                if metrics_data.get("success"):
                    metrics = metrics_data.get("metrics", {})
                    print(f"   总时长: {metrics.get('total_duration', 0):.2f}秒")
                    print(f"   多智能体模式: {metrics.get('multi_agent', False)}")
                    print(f"   Agent总数: {metrics.get('total_agents', 0)}")
                    print(f"   活跃Agent: {metrics.get('active_agents', 0)}")
                    print(f"   任务总数: {metrics.get('total_tasks', 0)}")
                    print(f"   完成任务: {metrics.get('completed_tasks', 0)}")
                    print(f"   失败任务: {metrics.get('failed_tasks', 0)}")
                    print(f"   并行效率: {metrics.get('parallel_efficiency', 0):.2%}")
                    print(f"   性能分数: {metrics.get('performance_score', 0):.2f}")
                else:
                    print("   ❌ 获取性能指标失败")
            else:
                print(f"   ❌ 获取性能指标失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 获取性能指标出错: {e}")
    
    def _print_multi_agent_results(self, response: Dict[str, Any]):
        """打印多智能体搜索结果"""
        if not response.get("success"):
            print(f"❌ 搜索失败: {response.get('message', '未知错误')}")
            errors = response.get("errors", [])
            if errors:
                print("错误详情:")
                for error in errors:
                    print(f"   - {error}")
            return
        
        print(f"\n✅ 多智能体搜索成功完成!")
        print(f"🆔 会话ID: {response.get('session_id', 'N/A')}")
        print(f"⏱️  总耗时: {response.get('total_execution_time', 0):.2f}秒")
        print(f"🔄 总迭代数: {response.get('total_iterations', 0)}")
        print(f"🔍 总搜索次数: {response.get('total_searches', 0)}")
        print(f"💾 缓存命中: {response.get('cache_hits', 0)}")
        print(f"📊 结果总数: {response.get('total_count', 0)}")
        
        # 打印多智能体特有信息
        metadata = response.get("metadata", {})
        if metadata.get("multi_agent"):
            print(f"🤖 使用Agent: {metadata.get('agents_used', [])}")
            print(f"📋 任务数量: {metadata.get('task_count', 0)}")
            
            quality_metrics = metadata.get("quality_metrics", {})
            if quality_metrics:
                print(f"🏆 质量指标:")
                print(f"   高质量结果: {quality_metrics.get('high_quality_count', 0)}")
                print(f"   中等质量结果: {quality_metrics.get('medium_quality_count', 0)}")
                print(f"   低质量结果: {quality_metrics.get('low_quality_count', 0)}")
                print(f"   平均置信度: {quality_metrics.get('average_confidence', 0):.2f}")
        
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
                
                metadata = result.get("metadata", {})
                if metadata.get("quality_level"):
                    print(f"   ⭐ 质量等级: {metadata['quality_level']}")
                
                if result.get("llm_summary"):
                    print(f"   🤖 AI摘要: {result['llm_summary']}")
        
        # 打印引用来源
        citations = response.get("citations", [])
        if citations:
            print(f"\n📚 引用来源 ({len(citations)}个):")
            for i, citation in enumerate(citations[:5], 1):
                print(f"   {i}. {citation}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🤖 开始测试 Multi Agent 系统")
        print("=" * 60)
        
        # 1. 系统信息检查
        system_info = self.test_system_info()
        
        # 2. 健康检查
        if not self.test_health_check():
            print("❌ 服务不可用，测试终止")
            return False
        
        # 检查多智能体是否可用
        if not system_info.get("multi_agent", {}).get("available", False):
            print("❌ Multi Agent System 不可用，测试终止")
            return False
        
        # 3. 基础多智能体搜索测试
        basic_result = self.test_multi_agent_search()
        
        # 4. 带追踪的多智能体搜索测试
        trace_result = self.test_multi_agent_with_tracing()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试完成!")
        
        # 测试结果总结
        basic_success = basic_result.get("success", False)
        trace_success = trace_result.get("success", False)
        
        print(f"📊 测试结果总结:")
        print(f"   基础多智能体搜索: {'✅ 通过' if basic_success else '❌ 失败'}")
        print(f"   追踪多智能体搜索: {'✅ 通过' if trace_success else '❌ 失败'}")
        
        overall_success = basic_success and trace_success
        print(f"   整体测试结果: {'✅ 全部通过' if overall_success else '❌ 存在失败'}")
        
        return overall_success


def main():
    """主函数"""
    tester = MultiAgentTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Multi Agent System 功能测试全部通过!")
    else:
        print("\n⚠️  Multi Agent System 功能测试存在问题，请检查日志")


if __name__ == "__main__":
    main()
