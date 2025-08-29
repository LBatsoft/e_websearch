# 目录整理计划：agent vs agents

## 🎯 问题描述

当前项目中同时存在两个智能体相关的目录：
- `core/agent/` - 原有目录，包含现有工作代码
- `core/agents/` - 新建目录，作为重构目标

这种重复会导致：
1. 开发者困惑
2. 导入路径不一致
3. 代码维护困难
4. 潜在的循环依赖

## 📋 整理方案

### 方案选择：统一使用 `core/agents/`

**理由：**
1. 复数形式更符合包含多个智能体类的语义
2. 新的目录结构更清晰、更模块化
3. 便于未来扩展和维护

### 迁移步骤

#### 阶段 1: 创建完整的新目录结构
```
core/agents/
├── base/                     # 基础组件
│   ├── __init__.py
│   ├── base_agent.py         # 基础智能体类
│   ├── models.py             # 数据模型
│   └── observability.py     # 可观测性组件
├── specialists/              # 专门化智能体
│   ├── __init__.py
│   ├── search_specialist.py  # 搜索专家
│   ├── content_analyzer.py   # 内容分析师
│   ├── result_synthesizer.py # 结果综合器
│   └── quality_assessor.py   # 质量评估师
├── coordination/             # 协调管理
│   ├── __init__.py
│   ├── coordinator.py        # 多智能体协调器
│   └── task_manager.py       # 任务管理器
├── reasoning/                # 推理策略
│   ├── __init__.py
│   ├── reasoning_engine.py   # 推理引擎
│   ├── search_strategies.py  # 搜索策略
│   └── result_processor.py   # 结果处理器
├── legacy/                   # 向后兼容
│   ├── __init__.py
│   ├── search_agent.py       # 原始搜索智能体
│   └── planner.py            # 原始规划器
└── __init__.py               # 主模块导出
```

#### 阶段 2: 迁移现有代码
1. **保留关键文件**：将 `core/agent/` 中的核心文件迁移到新结构
2. **更新导入路径**：修改所有相关的导入语句
3. **向后兼容**：在 `legacy/` 目录中保留原有接口

#### 阶段 3: 更新引用
1. **API 层**：更新 `api/` 中的导入路径
2. **测试文件**：更新 `tests/` 中的导入路径
3. **示例代码**：更新 `examples/` 中的导入路径
4. **文档**：更新所有相关文档

#### 阶段 4: 清理和验证
1. **删除旧目录**：确认所有功能正常后删除 `core/agent/`
2. **运行测试**：确保所有测试通过
3. **更新文档**：完善新的目录结构文档

## 🔄 迁移映射表

| 原路径 | 新路径 | 说明 |
|--------|--------|------|
| `core/agent/models.py` | `core/agents/base/models.py` | 基础数据模型 |
| `core/agent/observability.py` | `core/agents/base/observability.py` | 可观测性组件 |
| `core/agent/multi_agent_system.py` | `core/agents/coordination/coordinator.py` | 协调器（重构） |
| `core/agent/multi_agent.py` | `core/agents/multi_agent_system.py` | 主系统接口 |
| `core/agent/reasoning_engine.py` | `core/agents/reasoning/reasoning_engine.py` | 推理引擎 |
| `core/agent/search_strategies.py` | `core/agents/reasoning/search_strategies.py` | 搜索策略 |
| `core/agent/result_processor.py` | `core/agents/reasoning/result_processor.py` | 结果处理器 |
| `core/agent/search_agent.py` | `core/agents/legacy/search_agent.py` | 向后兼容 |
| `core/agent/planner.py` | `core/agents/legacy/planner.py` | 向后兼容 |

## 📦 导入路径变更

### 旧导入方式
```python
from core.agent.models import AgentType, TaskType
from core.agent.search_agent import SearchAgent
from core.agent.multi_agent import MultiAgentSearchSystem
```

### 新导入方式
```python
from core.agents.base.models import AgentType, TaskType
from core.agents.legacy.search_agent import SearchAgent  # 向后兼容
from core.agents import MultiAgentSearchSystem  # 主接口
```

### 推荐导入方式（新代码）
```python
from core.agents import (
    MultiAgentSearchSystem,
    SearchSpecialistAgent,
    ContentAnalyzerAgent,
    AgentType, TaskType
)
```

## ⚠️ 注意事项

1. **渐进式迁移**：不要一次性删除所有旧代码，确保系统稳定运行
2. **向后兼容**：在 `legacy/` 目录中保留原有接口，避免破坏现有代码
3. **测试覆盖**：每个迁移步骤都要运行完整测试
4. **文档同步**：及时更新相关文档和示例

## 🎯 预期收益

1. **清晰的代码组织**：按功能模块清晰分类
2. **更好的可维护性**：模块化设计便于维护和扩展
3. **一致的命名规范**：统一使用复数形式
4. **向后兼容性**：不破坏现有功能
5. **更好的开发体验**：清晰的导入路径和模块结构
