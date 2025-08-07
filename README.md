# 增强版Web搜索系统

一套功能强大的多源搜索系统，集成了Bing搜索和私域搜索能力，并支持自动化内容提取。

## 主要特性

- **多源搜索**: 支持Bing搜索、微信公众号、知乎等多个搜索源
- **智能内容提取**: 使用Playwright自动化浏览器访问详情页，提取完整内容
- **私域搜索**: 搜索本地微信公众号文章、知乎内容等私有数据
- **结果聚合**: 智能去重、相关性评分、结果排序
- **缓存系统**: 内存+文件双重缓存，提高搜索效率
- **异步处理**: 全异步架构，支持高并发搜索

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，至少设置 Bing API 密钥：

```
BING_API_KEY=your_bing_api_key_here
```

### 3. 安装浏览器（可选，用于内容提取）

```bash
playwright install chromium
```

### 4. 基础使用

```python
import asyncio
from e_websearch import SearchOrchestrator, SearchRequest, SourceType

async def main():
    # 创建搜索协调器
    orchestrator = SearchOrchestrator()
    
    # 创建搜索请求
    request = SearchRequest(
        query="人工智能教育",
        max_results=10,
        include_content=True,
        sources=[SourceType.BING, SourceType.WECHAT]
    )
    
    # 执行搜索
    response = await orchestrator.search(request)
    
    # 显示结果
    for result in response.results:
        print(f"标题: {result.title}")
        print(f"来源: {result.source.value}")
        print(f"URL: {result.url}")
        print(f"摘要: {result.snippet}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
```

## 系统架构

```
增强版WebSearch系统
├── SearchOrchestrator (主搜索协调器)
├── SearchEngines (搜索引擎模块)
│   ├── BingSearchEngine (Bing搜索)
│   └── PrivateDomainEngine (私域搜索)
├── ContentExtractor (内容提取器)
├── ResultAggregator (结果聚合器)
├── CacheManager (缓存管理)
└── Utils (工具模块)
```

## 核心组件

### 1. SearchOrchestrator (主协调器)

负责协调整个搜索流程：
- 调度多个搜索引擎
- 管理缓存
- 协调内容提取
- 聚合最终结果

### 2. SearchEngines (搜索引擎)

#### BingSearchEngine
- 基于 Bing Web Search API
- 支持搜索建议
- 自动解析搜索结果
- 包含速率限制

#### PrivateDomainEngine
- 搜索本地微信公众号文章
- 搜索本地知乎内容
- 支持扩展其他私域数据源

### 3. ContentExtractor (内容提取器)

- 使用 Playwright 自动化浏览器
- 智能识别页面主要内容
- 回退到 HTTP 请求方式
- 支持并发提取

### 4. ResultAggregator (结果聚合器)

- 智能去重（URL + 标题相似度）
- 多维度相关性评分
- 灵活的排序策略
- 详细统计信息

### 5. CacheManager (缓存管理)

- 内存 + 文件双重缓存
- 自动过期清理
- 可配置缓存策略

## API 参考

### SearchRequest

```python
SearchRequest(
    query: str,                    # 搜索关键词
    max_results: int = 10,         # 最大结果数
    include_content: bool = True,  # 是否提取完整内容
    sources: List[SourceType] = None,  # 搜索源列表
    filters: Dict[str, Any] = None     # 过滤器
)
```

### SourceType

```python
class SourceType(Enum):
    BING = "bing"
    WECHAT = "wechat"
    ZHIHU = "zhihu"
    BAIDU = "baidu"
    CUSTOM = "custom"
```

### SearchResult

```python
@dataclass
class SearchResult:
    title: str                     # 标题
    url: str                       # URL
    snippet: str                   # 摘要
    source: SourceType            # 来源
    score: float                   # 相关性得分
    publish_time: datetime         # 发布时间
    author: str                    # 作者
    content: str                   # 完整内容
    images: List[str]              # 图片列表
    metadata: Dict[str, Any]       # 元数据
```

## 配置说明

### config.py

```python
# Bing搜索配置
BING_API_KEY = os.getenv("BING_API_KEY", "")

# 浏览器配置
BROWSER_CONFIG = {
    "headless": True,
    "timeout": 30000,
    "viewport": {"width": 1920, "height": 1080}
}

# 内容提取配置
CONTENT_EXTRACT_CONFIG = {
    "max_concurrent": 5,
    "timeout": 30,
    "max_content_length": 50000,
    "blocked_domains": ["facebook.com", "twitter.com"]
}

# 缓存配置
CACHE_CONFIG = {
    "enabled": True,
    "ttl": 3600,
    "max_size": 1000
}
```

## 示例

查看 `examples/` 目录下的示例文件：

- `basic_example.py`: 基础使用示例
- `advanced_example.py`: 高级功能示例

## 私域数据配置

系统会自动搜索项目中的微信和知乎数据：

- 微信数据: `wechat/`, `wewe_rss/` 目录下的 JSON 文件
- 知乎数据: `zhihu/` 目录下的 JSON 文件

数据格式要求：

### 微信文章 JSON 格式

```json
{
    "title": "文章标题",
    "content": "文章内容",
    "url": "文章链接",
    "author": "作者",
    "account": "公众号名称",
    "publish_time": "2024-01-01 12:00:00"
}
```

### 知乎内容 JSON 格式

```json
{
    "title": "问题标题",
    "content": "回答内容",
    "url": "链接",
    "author": "作者",
    "vote_count": 100,
    "comment_count": 20
}
```

## 性能优化

1. **并发控制**: 内容提取限制并发数，避免过载
2. **缓存策略**: 智能缓存，减少重复请求
3. **速率限制**: API 调用速率限制，避免被封
4. **资源管理**: 自动关闭浏览器页面，释放资源

## 故障排除

### 1. Bing 搜索不可用

```
警告: Bing API密钥未配置，Bing搜索将不可用
```

**解决**: 在 `.env` 文件中设置 `BING_API_KEY`

### 2. Playwright 安装问题

```
警告: Playwright未安装，将仅使用HTTP方式提取内容
```

**解决**: 
```bash
pip install playwright
playwright install chromium
```

### 3. 内容提取失败

**可能原因**:
- 网站反爬虫
- 网络超时
- JavaScript 渲染问题

**解决**: 系统会自动回退到 HTTP 方式

## 扩展开发

### 添加新的搜索源

1. 继承 `BaseSearchEngine`
2. 实现 `search` 方法
3. 在 `SearchOrchestrator` 中注册

### 自定义内容提取器

1. 修改 `ContentExtractor._extract_main_content`
2. 添加特定网站的提取规则

### 自定义结果聚合

1. 修改 `ResultAggregator` 的评分算法
2. 添加新的排序策略

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！ 