
<div align="center">

<img src="docs/assets/logo.svg" alt="E-WebSearch Logo" height="160" />


**基于多源聚合的智能搜索框架，支持 LLM 增强功能**

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/Redis-5.0%2B-DC382D.svg?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-支持-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![ZhipuAI](https://img.shields.io/badge/ZhipuAI-GLM--4-FF6B35.svg)](https://open.bigmodel.cn/)

</div>

---

## 🚀 项目简介

E-WebSearch 是一个功能强大的多源搜索聚合系统，采用分层架构设计，集成了 Bing 搜索、ZAI 搜索和可扩展的私域搜索能力，并支持 API 服务。系统还集成了基于智谱AI GLM-4模型的 LLM 增强功能，为搜索结果提供智能摘要和标签生成。

### 🎯 核心特性

- **🔌 多源可插拔引擎**: 内置 Bing、ZAI 与私域（如微信、知乎）引擎，基于 `BaseEngine` 易于扩展
- **🧹 一体化内容抽取**: 自动化正文提取与清洗，统一标题、摘要与链接等字段
- **🧠 相关性与去重**: TF‑IDF + 向量模型的混合评分，结果去重、重排与聚合
- **🤖 LLM 智能增强**: 整体/逐条摘要与标签，优雅降级；支持智谱AI/OpenAI/Azure
- **⚡ 高并发异步**: 全链路 asyncio/aiohttp，内建超时与重试策略
- **💾 智能缓存系统**: 内存/Redis/分布式缓存，TTL、LRU、统计与健康检查，支持自动降级
- **🧪 可观测与 API**: FastAPI/OpenAPI 文档、健康检查与统计接口
- **🐳 一键部署**: Docker & Docker Compose 快速启动


## 📦 项目结构

```
e_websearch/
├── 🏗️  core/                    # 核心业务逻辑
│   ├── engines/                 # 搜索引擎实现
│   ├── search_orchestrator.py   # 搜索协调器
│   ├── models.py                # 核心数据模型
│   ├── llm_enhancer.py         # LLM 增强模块
│   └── ...
├── 🌐  api/                     # FastAPI 应用
│   ├── main.py                  # API 端点
│   └── models.py                # API 数据模型
├── 🧪  tests/                   # 测试代码
│   ├── test_llm_functionality.py
│   ├── test_zhipuai_direct.py
│   └── ...
├── 📚  examples/                # 使用示例
│   ├── llm_enhanced_example.py
│   └── ...
├── 📖  docs/                    # 文档
│   ├── llm-enhancement-guide.md
│   └── ...
├── 🐳  Dockerfile               # Docker 配置
├── 📋  requirements.txt         # 依赖列表
└── 📄  README.md               # 项目说明
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/your-username/e-websearch.git
cd e-websearch

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# 基础配置
CACHE_TYPE=memory

# ZAI Search Pro (推荐)
ZAI_API_KEY=your_zai_api_key_here

# Bing Search (可选)
BING_API_KEY=your_bing_api_key_here

# LLM 增强配置
ZAI_API_KEY=your_zhipuai_api_key_here  # 智谱AI
OPENAI_API_KEY=your_openai_api_key_here  # OpenAI (可选)
AZURE_OPENAI_API_KEY=your_azure_api_key_here  # Azure (可选)

# 私域搜索配置 (可选)
WECHAT_SEARCH_ENABLED=true
WECHAT_API_URL=http://your-wechat-api.com/search
ZHIHU_SEARCH_ENABLED=true
ZHIHU_API_URL=http://your-zhihu-api.com/search
```

### 3. 启动服务

```bash
# 启动 API 服务
python run_api.py

# 服务地址: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 4. 使用示例

#### 基础搜索

```python
import requests

response = requests.post("http://localhost:8000/search", json={
    "query": "人工智能教育应用",
    "max_results": 10,
    "sources": ["zai"]
})

print(f"找到 {response.json()['total_count']} 个结果")
```

#### 启用 LLM 增强

```python
# 带智能摘要和标签的搜索
response = requests.post("http://localhost:8000/search", json={
    "query": "人工智能教育应用",
    "max_results": 10,
    "sources": ["zai"],
    # LLM 增强选项
    "llm_summary": True,        # 生成整体摘要
    "llm_tags": True,           # 生成整体标签
    "llm_per_result": False,    # 是否逐条增强
    "llm_max_items": 5,         # 参与增强的结果数量
    "llm_language": "zh",       # 输出语言
    "model_provider": "zhipuai", # 模型提供商
    "model_name": "glm-4"       # 模型名称
})

data = response.json()
print(f"整体摘要: {data['llm_summary']}")
print(f"相关标签: {data['llm_tags']}")
```

## 🤖 LLM 增强功能

系统集成了可选的 LLM 增强功能，基于智谱AI GLM-4模型，提供：

- **📝 智能摘要**: 对所有搜索结果生成统一的摘要总结
- **🏷️ 智能标签**: 为搜索结果集合生成相关标签
- **🎯 逐条增强**: 为每个搜索结果单独生成摘要和标签
- **🔄 优雅降级**: 当 LLM 服务不可用时自动跳过增强

详细使用指南请参考：[LLM 增强功能使用指南](docs/llm-enhancement-guide.md)

## 📡 API 接口

### 搜索接口

```bash
POST /search
```

**请求参数:**
```json
{
    "query": "搜索关键词",
    "max_results": 10,
    "sources": ["zai", "wechat"],
    "include_content": true,
    "filters": {
        "time_range": "month",
        "domain": "www.sohu.com"
    },
    "llm_summary": true,
    "llm_tags": true,
    "llm_per_result": false,
    "llm_max_items": 5,
    "llm_language": "zh",
    "model_provider": "zhipuai",
    "model_name": "glm-4"
}
```

**响应格式:**
```json
{
    "success": true,
    "results": [...],
    "total_count": 10,
    "query": "搜索关键词",
    "execution_time": 2.5,
    "sources_used": ["zai"],
    "cache_hit": false,
    "llm_summary": "智能生成的摘要...",
    "llm_tags": ["标签1", "标签2"],
    "llm_per_result": {...}
}
```

### 其他接口

- `GET /health` - 健康检查
- `POST /suggestions` - 搜索建议
- `GET /statistics` - 系统统计
- `DELETE /cache` - 清空缓存

## 🐳 Docker 部署

### 快速部署

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 生产环境配置

1. 设置环境变量
2. 配置 Redis 缓存
3. 启用日志记录
4. 配置反向代理

## 🧪 测试

```bash
# 运行 LLM 功能测试
python tests/test_llm_functionality.py

# 测试智谱AI API
python tests/test_zhipuai_direct.py

# 测试 LLM 增强器
python tests/test_llm_enhancer_direct.py

# 运行所有测试
python -m pytest tests/
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [智谱AI](https://open.bigmodel.cn/) - 提供强大的 LLM 服务
- [Redis](https://redis.io/) - 高性能缓存数据库
- [Docker](https://www.docker.com/) - 容器化部署平台

---

<div align="center">

**E-WebSearch** - 让搜索更智能 🤖

[![GitHub stars](https://img.shields.io/github/stars/your-username/e-websearch?style=social)](https://github.com/your-username/e-websearch)
[![GitHub forks](https://img.shields.io/github/forks/your-username/e-websearch?style=social)](https://github.com/your-username/e-websearch)
[![GitHub issues](https://img.shields.io/github/issues/your-username/e-websearch)](https://github.com/your-username/e-websearch/issues)

</div>
