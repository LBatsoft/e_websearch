# E-WebSearch 项目结构

## 📁 目录结构概览

```
e_websearch/
├── 📦 core/                          # 核心功能模块
│   ├── 🤖 agents/                    # 多智能体系统
│   │   ├── base/                     # 基础智能体组件
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py         # 基础智能体类
│   │   │   ├── models.py             # 智能体数据模型
│   │   │   └── observability.py     # 可观测性组件
│   │   ├── specialists/              # 专门化智能体
│   │   │   ├── __init__.py
│   │   │   ├── search_specialist.py  # 搜索专家
│   │   │   ├── content_analyzer.py   # 内容分析师
│   │   │   ├── result_synthesizer.py # 结果综合器
│   │   │   └── quality_assessor.py   # 质量评估师
│   │   ├── coordination/             # 协调和管理
│   │   │   ├── __init__.py
│   │   │   ├── coordinator.py        # 多智能体协调器
│   │   │   └── task_manager.py       # 任务管理器
│   │   ├── reasoning/                # 推理和策略
│   │   │   ├── __init__.py
│   │   │   ├── reasoning_engine.py   # 推理引擎
│   │   │   ├── search_strategies.py  # 搜索策略
│   │   │   └── result_processor.py   # 结果处理器
│   │   └── legacy/                   # 遗留组件（向后兼容）
│   │       ├── __init__.py
│   │       ├── search_agent.py       # 原始搜索智能体
│   │       └── planner.py            # 原始规划器
│   ├── 🔍 search/                    # 搜索引擎模块
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # 搜索编排器
│   │   ├── engines/                  # 搜索引擎
│   │   │   ├── __init__.py
│   │   │   ├── base_engine.py
│   │   │   ├── bing_engine.py
│   │   │   ├── zai_engine.py
│   │   │   └── private_domain_engine.py
│   │   └── models.py                 # 搜索相关数据模型
│   ├── 🧠 llm/                       # LLM 增强模块
│   │   ├── __init__.py
│   │   ├── enhancer.py               # LLM 增强器
│   │   └── models.py                 # LLM 相关模型
│   ├── 📄 content/                   # 内容处理模块
│   │   ├── __init__.py
│   │   ├── extractor.py              # 内容提取器
│   │   ├── aggregator.py             # 结果聚合器
│   │   └── scoring.py                # 相关性评分
│   ├── 💾 storage/                   # 存储模块
│   │   ├── __init__.py
│   │   ├── cache_manager.py          # 缓存管理器
│   │   └── models.py                 # 存储相关模型
│   ├── 🔧 utils/                     # 工具模块
│   │   ├── __init__.py
│   │   ├── common.py                 # 通用工具
│   │   └── config.py                 # 配置管理
│   └── models.py                     # 核心数据模型
├── 🌐 api/                           # API 接口模块
│   ├── __init__.py
│   ├── main.py                       # FastAPI 主应用
│   ├── v1/                           # API v1 版本
│   │   ├── __init__.py
│   │   ├── endpoints/                # API 端点
│   │   │   ├── __init__.py
│   │   │   ├── search.py             # 搜索相关端点
│   │   │   ├── agents.py             # 智能体相关端点
│   │   │   └── health.py             # 健康检查端点
│   │   └── models.py                 # API 数据模型
│   └── middleware/                   # 中间件
│       ├── __init__.py
│       ├── auth.py                   # 认证中间件
│       └── logging.py                # 日志中间件
├── 📚 examples/                      # 示例代码
│   ├── basic/                        # 基础示例
│   │   ├── __init__.py
│   │   ├── simple_search.py          # 简单搜索示例
│   │   └── basic_usage.py            # 基础用法示例
│   ├── advanced/                     # 高级示例
│   │   ├── __init__.py
│   │   ├── multi_agent_demo.py       # 多智能体演示
│   │   ├── llm_enhanced_demo.py      # LLM 增强演示
│   │   └── custom_agent_demo.py      # 自定义智能体演示
│   ├── integration/                  # 集成示例
│   │   ├── __init__.py
│   │   ├── api_client_demo.py        # API 客户端演示
│   │   └── batch_processing_demo.py  # 批量处理演示
│   └── run_examples.py               # 示例运行器
├── 🧪 tests/                         # 测试模块
│   ├── unit/                         # 单元测试
│   │   ├── __init__.py
│   │   ├── test_agents/              # 智能体测试
│   │   ├── test_search/              # 搜索测试
│   │   └── test_llm/                 # LLM 测试
│   ├── integration/                  # 集成测试
│   │   ├── __init__.py
│   │   ├── test_api.py               # API 测试
│   │   └── test_system.py            # 系统测试
│   ├── performance/                  # 性能测试
│   │   ├── __init__.py
│   │   └── test_performance.py       # 性能测试
│   ├── conftest.py                   # pytest 配置
│   └── README.md                     # 测试说明
├── 📖 docs/                          # 文档目录
│   ├── architecture/                 # 架构文档
│   │   ├── overview.md               # 架构概览
│   │   ├── multi_agent_system.md     # 多智能体系统
│   │   └── search_engine.md          # 搜索引擎架构
│   ├── api/                          # API 文档
│   │   ├── reference.md              # API 参考
│   │   ├── authentication.md         # 认证说明
│   │   └── examples.md               # API 示例
│   ├── guides/                       # 使用指南
│   │   ├── quick_start.md            # 快速开始
│   │   ├── configuration.md          # 配置指南
│   │   ├── deployment.md             # 部署指南
│   │   └── troubleshooting.md        # 故障排除
│   ├── development/                  # 开发文档
│   │   ├── contributing.md           # 贡献指南
│   │   ├── testing.md                # 测试指南
│   │   └── release_notes.md          # 发布说明
│   └── assets/                       # 文档资源
│       ├── images/                   # 图片资源
│       └── diagrams/                 # 架构图
├── 🐳 deployment/                    # 部署配置
│   ├── docker/                       # Docker 配置
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── docker-compose.prod.yml
│   ├── kubernetes/                   # K8s 配置
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   └── scripts/                      # 部署脚本
│       ├── deploy.sh
│       └── health_check.sh
├── 📊 monitoring/                    # 监控配置
│   ├── prometheus/                   # Prometheus 配置
│   ├── grafana/                      # Grafana 仪表板
│   └── alerts/                       # 告警规则
├── 🔧 config/                        # 配置文件
│   ├── development.yaml              # 开发环境配置
│   ├── production.yaml               # 生产环境配置
│   └── testing.yaml                  # 测试环境配置
├── 📝 logs/                          # 日志目录
├── 💾 cache/                         # 缓存目录
├── 📦 requirements/                  # 依赖管理
│   ├── base.txt                      # 基础依赖
│   ├── development.txt               # 开发依赖
│   └── production.txt                # 生产依赖
├── 🔐 .env.example                   # 环境变量示例
├── 📋 pyproject.toml                 # 项目配置
├── 📄 README.md                      # 项目说明
├── 📜 LICENSE                        # 许可证
└── 🚀 run_api.py                     # API 启动脚本
```

## 🏗️ 架构设计原则

### 1. 模块化设计
- **单一职责**: 每个模块专注于特定功能
- **松耦合**: 模块间依赖最小化
- **高内聚**: 相关功能集中在同一模块

### 2. 分层架构
```
┌─────────────────┐
│   API Layer     │  # 接口层
├─────────────────┤
│  Service Layer  │  # 服务层（智能体系统）
├─────────────────┤
│  Core Layer     │  # 核心层（搜索、LLM、内容处理）
├─────────────────┤
│ Storage Layer   │  # 存储层（缓存、数据库）
└─────────────────┘
```

### 3. 智能体系统架构
```
┌─────────────────────────────────────────────────────────┐
│                 Multi-Agent Coordinator                 │
├─────────────────┬─────────────────┬─────────────────────┤
│ Search          │ Content         │ Result              │
│ Specialists     │ Analyzer        │ Synthesizer         │
├─────────────────┼─────────────────┼─────────────────────┤
│ Quality         │ Task            │ Observability       │
│ Assessor        │ Manager         │ Monitor             │
└─────────────────┴─────────────────┴─────────────────────┘
```

## 🔄 重构计划

### 阶段 1: 核心模块重构
1. 重新组织 `core/agent/` 目录
2. 分离智能体基础组件和专门化组件
3. 创建清晰的模块接口

### 阶段 2: API 模块优化
1. 按版本组织 API 端点
2. 分离业务逻辑和接口逻辑
3. 添加中间件支持

### 阶段 3: 示例和测试重构
1. 按功能分类示例代码
2. 完善测试覆盖率
3. 添加性能测试

### 阶段 4: 文档和部署
1. 更新架构文档
2. 完善部署配置
3. 添加监控支持

## 📈 迁移指南

### 向后兼容性
- 保留原有 API 接口
- 提供迁移工具和指南
- 逐步废弃旧接口

### 迁移步骤
1. 备份现有代码
2. 按模块逐步迁移
3. 更新导入路径
4. 运行测试验证
5. 更新文档

## 🎯 预期收益

### 开发体验
- 更清晰的代码组织
- 更容易的功能扩展
- 更好的测试覆盖

### 运维体验
- 更简单的部署流程
- 更完善的监控体系
- 更高效的故障排除

### 用户体验
- 更稳定的 API 接口
- 更丰富的功能特性
- 更详细的文档支持
