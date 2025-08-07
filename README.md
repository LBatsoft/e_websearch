# 增强版Web搜索系统

一套功能强大的多源搜索聚合系统，采用分层架构设计，集成了Bing搜索、ZAI搜索和可扩展的私域搜索能力，并支持API服务。

## 主要特性

- **分层架构**: 核心业务逻辑 (`core`) 与API接口 (`api`) 分离，清晰、可维护、易扩展。
- **多源搜索**: 支持Bing、ZAI、微信公众号、知乎等多个可插拔的搜索源。
- **私域搜索**: 支持通过 API 接口对接外部的微信、知乎等私有数据集。
- **结果聚合**: 智能去重、相关性评分、结果排序。
- **缓存系统**: 支持内存和 Redis 两种缓存后端，可灵活配置。
- **异步处理**: 全异步架构，支持高并发搜索。
- **API服务**: 提供基于FastAPI的Web接口，方便集成。
- **Docker支持**: 提供 `docker-compose.yml`，支持一键部署 API 服务和 Redis。

## 项目结构

```
e_websearch/
├── core/                 # 核心业务逻辑
│   ├── engines/          # 搜索引擎实现
│   ├── search_orchestrator.py # 搜索协调器
│   ├── models.py         # 核心数据模型 (dataclasses)
│   └── ...
├── api/                  # FastAPI 应用
│   ├── main.py           # API 端点
│   └── models.py         # API 数据模型 (Pydantic)
├── tests/                # 所有测试代码
├── examples/             # 面向用户的示例
├── run_api.py            # 运行 API 服务的脚本
├── config.py             # 系统配置
├── Dockerfile
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `dotenv.example` 文件为 `.env` 并填入您的 API 密钥。

```bash
cp dotenv.example .env
```

编辑 `.env` 文件，按需填入您的密钥：

```
# .env

# Bing 搜索 API 密钥 (可选)
BING_API_KEY=your_bing_api_key_here

# ZAI Search Pro API 密钥 (可选)
ZAI_API_KEY=your_zai_api_key_here

# 缓存配置 (可选, 默认使用 "memory")
# 可选值: "memory" 或 "redis"
# CACHE_TYPE=redis

# 如果使用 Redis，可以指定连接信息 (可选)
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_DB=0

# 私域搜索配置 (可选)
# 启用微信搜索并指定其 API 地址
# WECHAT_SEARCH_ENABLED=true
# WECHAT_API_URL=http://your-private-data-api/wechat/search

# 启用知乎搜索并指定其 API 地址
# ZHIHU_SEARCH_ENABLED=true
# ZHIHU_API_URL=http://your-private-data-api/zhihu/search
```

**重要**: `.env` 文件已被添加到 `.gitignore`，不会被提交到版本库，请放心填写。

### 3. 配置私域搜索 (可选)

本系统可以将微信、知乎等私域数据源作为搜索结果的一部分。为此，您需要：

1.  **准备一个私域数据 API**: 您需要自行搭建一个 API 服务，该服务能够接收 `GET` 请求，并通过 `query` 参数查询您的私域数据（例如，从您自己的数据库或 Elasticsearch 集群中查询）。
2.  **配置 API 地址**: 在 `.env` 文件中，取消注释并设置 `WECHAT_SEARCH_ENABLED` 和 `WECHAT_API_URL` (或知乎对应的变量) 来启用并指定您的 API 端点。

您的 API 应返回一个 JSON 数组，其中每个对象都包含 `title`, `url`, `content` 等字段。具体格式可以参考 `core/engines/private_domain_engine.py` 中的 `parse_item` 方法。

### 4. 运行服务

我们提供了两种运行方式：直接运行和使用 Docker Compose。

#### a) 直接运行 (用于本地开发)

确保您已安装依赖，然后运行：
```bash
python run_api.py
```
服务将在 `http://localhost:8000` 启动。此模式下默认使用内存缓存。

#### b) 使用 Docker Compose (推荐)

这是最简单的启动方式，它会自动为您启动 API 服务和一个 Redis 实例。

```bash
docker-compose up --build
```

服务同样在 `http://localhost:8000` 启动，并自动连接到 Redis 容器进行缓存。

### 4. 查看 API 文档

访问 [http://localhost:8000/docs](http://localhost:8000/docs) 查看由 FastAPI 自动生成的交互式 API 文档。

## 使用示例

您可以直接通过 `api_client_example.py` 脚本与 API 服务进行交互，也可以在您自己的代码中调用核心模块。

### 通过 API 客户端

```bash
# 运行演示
python api_client_example.py --demo

# 进行交互式搜索
python api_client_example.py --interactive
```

### 在代码中直接调用

`examples/basic_example.py` 展示了如何在代码中直接使用核心模块：

```python
import asyncio
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.search_orchestrator import SearchOrchestrator
from core.models import SearchRequest, SourceType

async def main():
    # 创建搜索协调器
    orchestrator = SearchOrchestrator()
    
    # 创建搜索请求
    request = SearchRequest(
        query="人工智能教育",
        max_results=5,
        sources=[SourceType.ZAI, SourceType.WECHAT]
    )
    
    # 执行搜索
    response = await orchestrator.search(request)
    
    # 显示结果
    for result in response.results:
        print(f"标题: {result.title}")
        print(f"来源: {result.source.value}")
        print(f"URL: {result.url}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
```

更多高级用法请参考 `examples/advanced_example.py`。

## 扩展开发

### 添加新的搜索源

1.  在 `core/engines/` 目录下创建一个新的引擎文件。
2.  创建一个继承自 `core.engines.base_engine.BaseSearchEngine` 的类。
3.  实现 `search` 异步方法。
4.  在 `core.search_orchestrator.SearchOrchestrator` 的 `__init__` 方法中注册您的新引擎。

### 自定义内容提取器

1.  修改 `core.content_extractor.ContentExtractor` 类。
2.  实现 `_extract_main_content` 方法，添加针对特定网站的提取规则。

### 自定义结果聚合

1.  修改 `core.result_aggregator.ResultAggregator` 类。
2.  调整 `aggregate_results` 方法中的评分或去重算法。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
