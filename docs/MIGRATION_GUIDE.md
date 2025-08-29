# 智能体模块迁移指南

## 🎯 概述

E-WebSearch 项目已将智能体相关代码从 `core/agent/` 迁移到 `core/agents/`，采用更清晰的模块化架构。本指南将帮助您顺利迁移到新的架构。

## 📋 主要变更

### 目录结构变更

```
旧结构：                        新结构：
core/agent/                    core/agents/
├── search_agent.py           ├── base/                    # 基础组件
├── multi_agent.py            │   ├── base_agent.py
├── models.py                 │   ├── models.py
├── observability.py          │   └── observability.py
├── reasoning_engine.py       ├── specialists/             # 专门化智能体
├── search_strategies.py      │   ├── search_specialist.py
├── result_processor.py       │   ├── content_analyzer.py
└── ...                       │   ├── result_synthesizer.py
                              │   └── quality_assessor.py
                              ├── coordination/            # 协调管理
                              │   ├── coordinator.py
                              │   └── task_manager.py
                              ├── reasoning/               # 推理策略
                              │   ├── reasoning_engine.py
                              │   ├── search_strategies.py
                              │   └── result_processor.py
                              ├── legacy/                  # 向后兼容
                              │   ├── search_agent.py
                              │   └── multi_agent.py
                              └── multi_agent_system.py    # 主接口
```

## 🔄 导入路径迁移

### 1. 基础智能体组件

```python
# ❌ 旧的导入方式
from core.agent.models import AgentType, TaskType, AgentTask
from core.agent.observability import ExecutionTracer

# ✅ 新的导入方式
from core.agents.base.models import AgentType, TaskType, AgentTask
from core.agents.base.observability import ExecutionTracer

# 🚀 推荐的导入方式（从主模块导入）
from core.agents import AgentType, TaskType, AgentTask, ExecutionTracer
```

### 2. 搜索智能体

```python
# ❌ 旧的导入方式
from core.agent.search_agent import SearchAgent

# ✅ 新的导入方式（向后兼容）
from core.agents.legacy.search_agent import SearchAgent

# 🚀 推荐的导入方式（使用新的专门化智能体）
from core.agents import SearchSpecialistAgent
```

### 3. 多智能体系统

```python
# ❌ 旧的导入方式
from core.agent.multi_agent import MultiAgentSearchSystem

# ✅ 新的导入方式
from core.agents import MultiAgentSearchSystem

# 🚀 高级用法（直接使用协调器）
from core.agents import MultiAgentCoordinator
```

### 4. 推理和策略组件

```python
# ❌ 旧的导入方式
from core.agent.reasoning_engine import ReasoningEngine
from core.agent.search_strategies import SearchStrategyManager
from core.agent.result_processor import ResultProcessor

# ✅ 新的导入方式
from core.agents.reasoning.reasoning_engine import ReasoningEngine
from core.agents.reasoning.search_strategies import SearchStrategyManager
from core.agents.reasoning.result_processor import ResultProcessor

# 🚀 推荐的导入方式
from core.agents import ReasoningEngine, SearchStrategyManager, ResultProcessor
```

## 📝 代码迁移示例

### 示例 1: 基础搜索智能体使用

```python
# ❌ 旧代码
from core.agent.search_agent import SearchAgent
from core.agent.models import AgentSearchRequest

agent = SearchAgent(search_orchestrator)
request = AgentSearchRequest(query="测试查询")
response = await agent.search(request)

# ✅ 新代码（向后兼容）
from core.agents.legacy.search_agent import SearchAgent
from core.agents import AgentSearchRequest

agent = SearchAgent(search_orchestrator)
request = AgentSearchRequest(query="测试查询")
response = await agent.search(request)

# 🚀 推荐的新代码（使用新架构）
from core.agents import MultiAgentSearchSystem, AgentSearchRequest

system = MultiAgentSearchSystem(search_orchestrator)
request = AgentSearchRequest(query="测试查询")
response = await system.search(request)
```

### 示例 2: 多智能体系统使用

```python
# ❌ 旧代码
from core.agent.multi_agent import MultiAgentSearchSystem
from core.agent.models import AgentSearchRequest, PlanningStrategy

system = MultiAgentSearchSystem(search_orchestrator)
request = AgentSearchRequest(
    query="复杂查询",
    planning_strategy=PlanningStrategy.ADAPTIVE
)
response = await system.search(request)

# ✅ 新代码
from core.agents import MultiAgentSearchSystem, AgentSearchRequest, PlanningStrategy

system = MultiAgentSearchSystem(search_orchestrator)
request = AgentSearchRequest(
    query="复杂查询",
    planning_strategy=PlanningStrategy.ADAPTIVE
)
response = await system.search(request)
```

### 示例 3: 自定义智能体开发

```python
# ❌ 旧代码
from core.agent.models import BaseAgent, AgentType, TaskType

class CustomAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.CUSTOM)
        self.capabilities = {TaskType.SEARCH}

# ✅ 新代码
from core.agents.base.base_agent import BaseAgent
from core.agents import AgentType, TaskType

class CustomAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.CUSTOM)
        self.capabilities = {TaskType.SEARCH}
```

## 🔧 API 层迁移

### FastAPI 端点更新

```python
# ❌ 旧的 API 代码
from core.agent.search_agent import SearchAgent
from core.agent.multi_agent import MultiAgentSearchSystem

# ✅ 新的 API 代码
from core.agents.legacy.search_agent import SearchAgent  # 向后兼容
from core.agents import MultiAgentSearchSystem  # 推荐使用
```

## 🧪 测试代码迁移

```python
# ❌ 旧的测试代码
from core.agent.models import AgentTask, TaskType
from core.agent.search_agent import SearchAgent

def test_search_agent():
    task = AgentTask(task_type=TaskType.SEARCH, data={"query": "test"})
    agent = SearchAgent(mock_orchestrator)
    # ...

# ✅ 新的测试代码
from core.agents import AgentTask, TaskType, SearchSpecialistAgent

def test_search_specialist():
    task = AgentTask(task_type=TaskType.SEARCH, data={"query": "test"})
    agent = SearchSpecialistAgent("test_agent", mock_orchestrator)
    # ...
```

## ⚠️ 重要注意事项

### 1. 向后兼容性
- 旧的 `core.agent` 模块仍然可用，但会显示弃用警告
- 所有旧的导入路径都会重定向到新的模块
- 建议逐步迁移，不需要一次性修改所有代码

### 2. 新功能优势
- **模块化设计**: 更清晰的代码组织
- **专门化智能体**: 更强大的搜索能力
- **更好的可观测性**: 详细的思考过程记录
- **更高的性能**: 并行处理和优化策略

### 3. 迁移建议
- **渐进式迁移**: 先迁移新功能，再逐步更新现有代码
- **测试驱动**: 每次迁移后运行完整测试
- **文档同步**: 及时更新相关文档

## 🚀 迁移检查清单

- [ ] 更新导入语句
- [ ] 运行测试确保功能正常
- [ ] 更新文档和注释
- [ ] 检查是否有弃用警告
- [ ] 考虑使用新的专门化智能体
- [ ] 更新 API 端点（如果适用）
- [ ] 更新示例代码

## 📞 获取帮助

如果在迁移过程中遇到问题：

1. 查看 `docs/architecture/multi_agent_system.md` 了解新架构
2. 参考 `examples/` 目录中的示例代码
3. 检查 `tests/` 目录中的测试用例
4. 查看弃用警告信息获取具体指导

## 🎯 迁移后的收益

- **更清晰的代码结构**: 按功能模块组织
- **更好的开发体验**: 清晰的导入路径
- **更强的扩展性**: 模块化设计便于添加新功能
- **更高的性能**: 优化的多智能体协作机制
- **更好的可维护性**: 分离关注点，降低耦合度
