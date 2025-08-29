"""
Multi Agent 系统代码逻辑验证脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有导入"""
    print("🔍 测试模块导入...")
    
    try:
        from core.agents import (
            MultiAgentCoordinator,
            BaseAgent,
            SearchSpecialistAgent,
            AgentType,
            TaskType,
            TaskPriority,
            AgentTask,
            AgentMessage,
        )
        print("✅ agents 模块导入成功")
    except Exception as e:
        print(f"❌ agents 导入失败: {e}")
        return False
    
    try:
        from core.agents import MultiAgentSearchSystem
        print("✅ multi_agent 模块导入成功")
    except Exception as e:
        print(f"❌ multi_agent 导入失败: {e}")
        return False
    
    try:
        from core.agents import MultiAgentSearchSystem as MASFromInit
        print("✅ 从 __init__ 导入 MultiAgentSearchSystem 成功")
    except Exception as e:
        print(f"❌ 从 __init__ 导入失败: {e}")
        return False
    
    return True

def test_agent_creation():
    """测试Agent创建逻辑"""
    print("\n🔍 测试Agent创建逻辑...")
    
    try:
        from core.agents.specialists.search_specialist import SearchSpecialistAgent
        from core.agents.base.models import AgentType
        
        # 创建一个模拟的search_orchestrator用于测试
        class MockSearchOrchestrator:
            async def search(self, request):
                return type('MockResponse', (), {
                    'total_count': 5,
                    'results': [],
                    'sources_used': []
                })()
        
        # 测试SearchSpecialistAgent创建（需要search_orchestrator）
        mock_orchestrator = MockSearchOrchestrator()
        search_agent = SearchSpecialistAgent("test_search_agent", mock_orchestrator)
        print(f"✅ SearchSpecialistAgent创建成功: {search_agent.agent_id}")
        
        # 测试capabilities
        assert isinstance(search_agent.capabilities, set)
        print("✅ capabilities 初始化正确")
        
        # 测试状态
        from core.agents.base.models import ExecutionStatus
        assert search_agent.status == ExecutionStatus.IDLE
        print("✅ 初始状态正确")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent创建测试失败: {e}")
        return False

def test_task_creation():
    """测试任务创建逻辑"""
    print("\n🔍 测试任务创建逻辑...")
    
    try:
        from core.agents.base.models import AgentTask, TaskType, TaskPriority
        from core.agents.base.models import ExecutionStatus
        
        # 创建测试任务
        task = AgentTask(
            task_id="test_task_001",
            task_type=TaskType.SEARCH,
            priority=TaskPriority.HIGH,
            data={"query": "测试查询", "sources": ["zai"]},
        )
        
        print(f"✅ AgentTask创建成功: {task.task_id}")
        assert task.status == ExecutionStatus.PENDING
        print("✅ 任务初始状态正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 任务创建测试失败: {e}")
        return False

def test_data_models():
    """测试数据模型"""
    print("\n🔍 测试数据模型...")
    
    try:
        from core.agents.legacy.models import AgentSearchRequest, PlanningStrategy
        from core.models import SourceType
        
        # 创建测试请求
        request = AgentSearchRequest(
            query="测试查询",
            sources=[SourceType.ZAI],
            planning_strategy=PlanningStrategy.PARALLEL,
        )
        
        print(f"✅ AgentSearchRequest创建成功: {request.query}")
        assert request.planning_strategy == PlanningStrategy.PARALLEL
        print("✅ 规划策略设置正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False

def test_mock_coordinator():
    """测试协调器基础逻辑（不需要实际搜索）"""
    print("\n🔍 测试协调器基础逻辑...")
    
    try:
        from core.agents import MultiAgentCoordinator
        from core.search_orchestrator import SearchOrchestrator
        
        # 这里我们不能创建真实的SearchOrchestrator，因为需要API密钥
        # 但我们可以测试类的基础结构
        print("✅ MultiAgentCoordinator 类可以导入")
        
        # 测试枚举值
        from core.agents.base.models import AgentType, TaskType
        
        agent_types = [AgentType.COORDINATOR, AgentType.SEARCH_SPECIALIST, 
                      AgentType.CONTENT_ANALYZER, AgentType.RESULT_SYNTHESIZER, 
                      AgentType.QUALITY_ASSESSOR]
        print(f"✅ AgentType枚举: {[at.value for at in agent_types]}")
        
        task_types = [TaskType.SEARCH, TaskType.ANALYZE, TaskType.SYNTHESIZE, 
                     TaskType.ASSESS, TaskType.COORDINATE]
        print(f"✅ TaskType枚举: {[tt.value for tt in task_types]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 协调器测试失败: {e}")
        return False

def main():
    """主验证函数"""
    print("🤖 Multi Agent 系统代码逻辑验证")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("Agent创建", test_agent_creation),
        ("任务创建", test_task_creation),
        ("数据模型", test_data_models),
        ("协调器逻辑", test_mock_coordinator),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name} - 通过")
                passed += 1
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 验证结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有代码逻辑验证通过！")
        return True
    else:
        print("⚠️  存在代码逻辑问题，需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)