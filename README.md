# 增强版Web搜索系统

一套功能强大的多源搜索聚合系统，采用分层架构设计，集成了Bing搜索、ZAI搜索和可扩展的私域搜索能力，并支持API服务。

## 主要特性

- **分层架构**: 核心业务逻辑 (`core`) 与API接口 (`api`) 分离，清晰、可维护、易扩展。
- **多源搜索**: 支持Bing、ZAI、微信公众号、知乎等多个可插拔的搜索源。
- **私域搜索**: 支持通过 API 接口对接外部的微信、知乎等私有数据集。
- **智能评分**: 采用混合评分系统（TF-IDF + 向量模型），支持语义相似度匹配。
- **灵活搜索**: 移除基础关键词匹配限制，提供更智能的相关性评分。
- **智能预览**: 优化snippet和content字段，避免内容重复，提供更好的预览体验。
- **结果聚合**: 智能去重、多维度评分、结果排序。
- **智能缓存系统**: 支持内存和 Redis 两种缓存后端，具备LRU退出机制、自动清理、详细统计等功能。
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

**注意**：首次运行时，系统会自动下载预训练的语言模型（约 100MB）用于语义相关性评分。如果您不需要向量模型评分功能，可以修改 `core/result_aggregator.py` 中的评分器配置。

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

# 缓存高级配置 (可选)
# CACHE_TTL=3600                    # 缓存过期时间（秒）
# CACHE_MAX_SIZE=1000               # 内存缓存最大条目数
# CACHE_CLEANUP_INTERVAL=300        # 清理间隔（秒）
# CACHE_LRU_ENABLED=true            # 启用LRU退出机制
# CACHE_STATS_ENABLED=true          # 启用缓存统计
# CACHE_MAX_CONNECTIONS=20          # Redis最大连接数
# CACHE_RETRY_ON_TIMEOUT=true       # Redis超时重试
# CACHE_HEALTH_CHECK_INTERVAL=30    # Redis健康检查间隔

# 私域搜索配置 (可选)
# 启用微信搜索并指定其 API 地址
# WECHAT_SEARCH_ENABLED=true
# WECHAT_API_URL=http://your-private-data-api/wechat/search
# WECHAT_API_TIMEOUT=30

# 启用知乎搜索并指定其 API 地址
# ZHIHU_SEARCH_ENABLED=true
# ZHIHU_API_URL=http://your-private-data-api/zhihu/search
# ZHIHU_API_TIMEOUT=30
```

**重要**: `.env` 文件已被添加到 `.gitignore`，不会被提交到版本库，请放心填写。

### 3. 配置私域搜索 (可选)

本系统可以将微信、知乎等私域数据源作为搜索结果的一部分。为此，您需要：

1.  **准备一个私域数据 API**: 您需要自行搭建一个 API 服务，该服务能够接收 `POST` 请求，并通过 JSON body 中的 `query` 参数查询您的私域数据（例如，从您自己的数据库或 Elasticsearch 集群中查询）。
2.  **配置 API 地址**: 在 `.env` 文件中，取消注释并设置 `WECHAT_SEARCH_ENABLED` 和 `WECHAT_API_URL` (或知乎对应的变量) 来启用并指定您的 API 端点。

#### 微信私域搜索API格式

您的微信API应返回以下格式的JSON响应：

```json
{
    "articles": [
        {
            "title": "文章标题",
            "link": "https://mp.weixin.qq.com/s?...",
            "account": "公众号名称",
            "publish_time": "2023-12-08 12:15",
            "summary": "文章摘要内容...",
            "content_markdown": "完整的文章内容..."
        }
    ]
}
```

系统会自动适配不同的API响应格式，优先使用 `articles` 键，备选 `data` 或 `results` 键。

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

### 自定义相关性评分

系统提供了一个强大的混合评分系统，结合了 TF-IDF 和向量模型的优势：

1. **TF-IDF 评分器** (`TfidfScorer`)
   - 基于词频-逆文档频率
   - 支持单词和双词组合（n-gram）
   - 适合精确匹配场景

2. **向量模型评分器** (`VectorScorer`)
   - 使用预训练的多语言模型
   - 支持跨语言语义匹配
   - 更好地理解同义词和相关概念

3. **混合评分器** (`HybridScorer`)
   - 智能结合 TF-IDF 和向量模型
   - 可调节的权重配置
   - 标题和摘要的差异化权重 

要自定义评分系统，您可以：

1. 继承 `core.relevance_scoring.BaseScorer` 创建新的评分器
2. 修改 `core.result_aggregator.ResultAggregator` 中的评分权重
3. 在 `SearchOrchestrator` 中使用自定义评分器

示例：创建自定义评分器

```python
from core.relevance_scoring import BaseScorer

class MyCustomScorer(BaseScorer):
    def calculate_score(self, query: str, title: str, snippet: str) -> float:
        # 实现您的评分逻辑
        score = 0.0
        # ...
        return score

# 在 SearchOrchestrator 中使用
orchestrator = SearchOrchestrator(scorer=MyCustomScorer())

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 最新更新

### v1.2.0 - 搜索优化和私域搜索适配

#### 🚀 新功能
- **移除关键词匹配限制**: 所有搜索引擎不再要求搜索结果必须包含查询关键词
- **智能预览优化**: 优化 `snippet` 和 `content` 字段，避免内容重复
- **微信私域搜索适配**: 完全适配微信API的实际返回格式
- **灵活API解析**: 支持多种API响应格式的自动适配

#### 🔧 技术改进
- **snippet长度优化**: 统一所有搜索引擎的snippet截取长度为50字符
- **字段映射优化**: 正确提取微信API的 `title`、`link`、`account`、`summary` 等字段
- **智能内容选择**: 优先使用API提供的摘要字段，备选截取内容
- **错误处理增强**: 改进API响应解析的错误处理和日志记录
- **缓存策略优化**: 实现LRU退出机制、自动清理、详细统计功能

#### 📝 文档更新
- 更新了微信私域搜索的API格式说明
- 添加了搜索优化特性的详细说明
- 完善了环境变量配置示例
- 添加了缓存高级配置选项说明
- 新增了缓存统计API端点文档
