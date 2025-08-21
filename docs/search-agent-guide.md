# Search Agent 使用指南

## 🤖 简介

Search Agent 是 E-WebSearch 的智能搜索代理功能，基于规划器+循环执行器+工具层架构，实现按计划多跳检索、阶段总结、引用输出，并提供统一结构化结果与可观测数据。

## 🏗️ 架构设计

```
Search Agent 系统
├── 🧠 规划器 (Planner)
│   ├── 查询分析器 (Query Analyzer)
│   ├── 任务分解器 (Task Decomposer) 
│   └── 策略生成器 (Strategy Generator)
├── 🔄 循环执行器 (Loop Executor)
│   ├── 执行引擎 (Execution Engine)
│   ├── 状态管理器 (State Manager)
│   └── 条件判断器 (Condition Evaluator)
├── 🛠️ 工具层 (Tool Layer)
│   ├── 搜索工具 (Search Tools)
│   ├── 内容分析工具 (Content Analysis Tools)
│   └── 数据处理工具 (Data Processing Tools)
├── 📊 可观测层 (Observability Layer)
│   ├── 执行追踪器 (Execution Tracer)
│   ├── 性能监控器 (Performance Monitor)
│   └── 结果记录器 (Result Logger)
└── 🌐 Agent API (New API Layer)
    ├── Agent 搜索接口
    ├── 执行状态查询接口
    └── 历史记录接口
```

## 🚀 核心特性

### 🧠 智能规划
- **查询分析**: 自动分析查询意图、复杂度和实体
- **任务分解**: 将复杂查询分解为多个执行步骤
- **策略生成**: 根据查询特征选择最优执行策略
- **LLM 增强**: 可选的大模型辅助分析

### 🔄 循环执行
- **多跳检索**: 支持迭代式、并行式、自适应搜索
- **状态管理**: 完整的执行状态跟踪和管理
- **条件判断**: 智能的继续/停止/优化决策
- **错误处理**: 优雅的错误处理和恢复机制

### 🛠️ 丰富工具
- **多源搜索**: 支持并行多源、查询扩展
- **内容分析**: 关键短语提取、相似度计算、质量评估
- **数据处理**: 去重、排序、过滤、聚合

### 📊 全面可观测
- **执行追踪**: 详细的执行过程记录
- **性能监控**: 实时性能指标收集
- **结果记录**: 搜索结果和分析数据记录

## 📡 API 接口

### 智能搜索接口

```bash
POST /agent/search
```

**请求参数:**
```json
{
    "query": "人工智能在医疗领域的应用",
    "max_iterations": 3,
    "max_results_per_iteration": 10,
    "total_max_results": 50,
    "sources": ["zai"],
    "include_content": true,
    "llm_summary": true,
    "llm_tags": true,
    "llm_per_result": false,
    "llm_language": "zh",
    "model_provider": "auto",
    "model_name": "",
    "planning_strategy": "adaptive",
    "enable_refinement": true,
    "confidence_threshold": 0.7,
    "enable_tracing": true,
    "enable_performance_monitoring": true,
    "timeout": 300,
    "metadata": {}
}
```

**规划策略选项:**
- `simple`: 简单单次搜索
- `iterative`: 迭代式多跳搜索
- `parallel`: 并行多路搜索  
- `adaptive`: 自适应策略（推荐）

**响应格式:**
```json
{
    "success": true,
    "session_id": "agent_abc12345",
    "message": "搜索完成",
    "execution_state": {
        "session_id": "agent_abc12345",
        "status": "completed",
        "start_time": 1703123456.789,
        "total_execution_time": 15.23,
        "total_searches": 3,
        "cache_hits": 1,
        "final_summary": "AI在医疗领域的应用主要包括...",
        "final_tags": ["人工智能", "医疗诊断", "机器学习"]
    },
    "execution_plan": {
        "plan_id": "plan_def67890",
        "strategy": "iterative",
        "steps": [
            {
                "step_id": "step_1",
                "step_type": "search",
                "description": "基础搜索: 人工智能在医疗领域的应用",
                "status": "completed",
                "execution_time": 3.45,
                "results_count": 10,
                "confidence_score": 0.85
            }
        ]
    },
    "results": [
        {
            "title": "AI医疗诊断技术突破",
            "url": "https://example.com/ai-medical",
            "snippet": "人工智能在医疗诊断中的应用...",
            "source": "zai",
            "score": 0.95,
            "relevance_score": 0.88,
            "confidence_score": 0.92,
            "found_in_step": "step_1",
            "step_type": "search",
            "llm_summary": "文章介绍了AI在医疗诊断中的最新突破",
            "labels": ["医疗AI", "诊断技术", "深度学习"],
            "key_insights": ["提高诊断准确率", "减少误诊率"],
            "citations": ["https://example.com/ai-medical"],
            "metadata": {}
        }
    ],
    "total_count": 25,
    "original_query": "人工智能在医疗领域的应用",
    "final_query": "人工智能在医疗领域的应用",
    "total_execution_time": 15.23,
    "total_iterations": 3,
    "total_searches": 3,
    "cache_hits": 1,
    "final_summary": "综合分析显示，AI在医疗领域的应用...",
    "final_tags": ["人工智能", "医疗诊断", "机器学习"],
    "execution_trace": [...],
    "performance_metrics": {...},
    "sources_used": ["zai"],
    "citations": ["https://example.com/ai-medical"],
    "errors": [],
    "warnings": []
}
```

### 其他接口

- `GET /agent/search/{session_id}/status` - 获取搜索状态
- `POST /agent/search/{session_id}/cancel` - 取消搜索
- `GET /agent/search/{session_id}/trace` - 获取执行追踪
- `GET /agent/search/{session_id}/metrics` - 获取性能指标
- `GET /agent/health` - Agent 健康检查

## 🎯 使用场景

### 1. 对比分析搜索
```python
response = client.agent_search(
    query="ChatGPT vs Claude 对比分析",
    planning_strategy="iterative",
    max_iterations=3
)
```

### 2. 深度研究搜索
```python
response = client.agent_search(
    query="区块链技术详细介绍",
    planning_strategy="adaptive",
    max_iterations=4,
    llm_per_result=True
)
```

### 3. 并行多主题搜索
```python
response = client.agent_search(
    query="量子计算 机器学习 应用前景",
    planning_strategy="parallel",
    sources=["zai", "bing"]
)
```

### 4. 教程类搜索
```python
response = client.agent_search(
    query="Python机器学习入门教程",
    planning_strategy="iterative",
    confidence_threshold=0.8
)
```

## 📊 执行流程

### 1. 查询分析阶段
- 分析查询类型（对比、教程、定义等）
- 评估查询复杂度
- 提取关键实体
- 推断用户意图

### 2. 计划生成阶段
- 选择执行策略
- 分解执行步骤
- 估算执行时间
- 计算计划置信度

### 3. 循环执行阶段
- 按步骤执行搜索
- 实时状态管理
- 条件判断决策
- 结果累积处理

### 4. 结果处理阶段
- 去重和排序
- 质量评估
- LLM 增强
- 引用提取

## 🔧 配置选项

### 执行控制
- `max_iterations`: 最大迭代次数 (1-10)
- `max_results_per_iteration`: 每次迭代最大结果数 (1-50)
- `total_max_results`: 总最大结果数 (1-200)
- `timeout`: 总超时时间（秒）(30-1800)

### 搜索配置
- `sources`: 搜索源列表
- `include_content`: 是否包含详细内容
- `enable_refinement`: 是否启用查询优化
- `confidence_threshold`: 置信度阈值 (0.0-1.0)

### LLM 增强
- `llm_summary`: 是否生成整体摘要
- `llm_tags`: 是否生成标签
- `llm_per_result`: 是否为每个结果生成增强
- `llm_language`: 输出语言
- `model_provider`: 模型提供商
- `model_name`: 模型名称

### 可观测性
- `enable_tracing`: 是否启用执行追踪
- `enable_performance_monitoring`: 是否启用性能监控

## 📈 性能优化

### 缓存策略
- 自动缓存搜索结果
- 智能缓存键生成
- 支持分布式缓存

### 并发控制
- 异步并发执行
- 资源池管理
- 限流和熔断

### 内存管理
- 流式结果处理
- 及时资源清理
- 内存使用监控

## 🛠️ 开发指南

### 扩展搜索引擎
```python
from core.engines.base_engine import BaseSearchEngine

class CustomEngine(BaseSearchEngine):
    async def search(self, request):
        # 实现自定义搜索逻辑
        pass
```

### 扩展分析工具
```python
from core.agent.tools import ContentAnalysisTools

class CustomAnalysisTools(ContentAnalysisTools):
    def custom_analysis(self, content):
        # 实现自定义分析逻辑
        pass
```

### 自定义规划策略
```python
from core.agent.planner import StrategyGenerator

class CustomStrategy(StrategyGenerator):
    def generate_strategy(self, request, analysis):
        # 实现自定义策略逻辑
        pass
```

## 🔍 监控和调试

### 执行追踪
```python
# 获取详细执行追踪
trace = client.get_execution_trace(session_id)
for event in trace["trace_events"]:
    print(f"{event['event_type']}: {event['data']}")
```

### 性能监控
```python
# 获取性能指标
metrics = client.get_performance_metrics(session_id)
print(f"缓存命中率: {metrics['cache_hit_rate']:.2%}")
print(f"平均响应时间: {metrics['avg_step_time']:.2f}s")
```

### 日志分析
- 使用 loguru 进行结构化日志
- 支持日志级别配置
- 提供详细的错误堆栈

## 🚨 错误处理

### 常见错误类型
- 网络连接错误
- API 限流错误
- LLM 服务不可用
- 查询解析错误

### 错误恢复策略
- 自动重试机制
- 优雅降级
- 部分结果返回
- 错误状态记录

## 📝 最佳实践

### 查询设计
- 使用具体明确的查询词
- 避免过于宽泛的查询
- 合理设置迭代次数
- 选择合适的规划策略

### 性能优化
- 启用缓存机制
- 合理设置超时时间
- 监控内存使用
- 定期清理会话数据

### 可观测性
- 启用执行追踪
- 监控性能指标
- 分析错误模式
- 优化搜索策略

## 🔗 相关文档

- [API 文档](api-readme.md)
- [LLM 增强指南](llm-enhancement-guide.md)
- [系统架构](STRUCTURE.md)
- [更新日志](changelog-zai.md)
