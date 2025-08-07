# ZAI Search Pro 集成更新日志

## 版本 1.1.0 - ZAI Search Pro 集成

### 🚀 新功能

1. **新增 ZAI Search Pro 搜索引擎**
   - 基于智谱AI的搜索引擎，支持 search_pro 模式
   - 支持高质量网页摘要和时间过滤
   - 支持域名过滤和搜索结果数量控制

2. **增强的搜索源类型**
   - 新增 `SourceType.ZAI` 搜索源类型
   - 默认搜索源更新为 ZAI + 微信公众号

3. **配置扩展**
   - 新增 `ZAI_API_KEY` 环境变量配置
   - 支持通过环境变量设置 ZAI API 密钥

### 🔧 技术实现

1. **ZaiSearchEngine 类**
   - 继承自 `BaseSearchEngine`
   - 实现异步搜索功能
   - 支持速率限制（30请求/分钟）
   - 自动处理API错误和超时

2. **搜索参数支持**
   - `count`: 返回结果数量 (1-50)
   - `search_domain_filter`: 域名过滤
   - `search_recency_filter`: 时间范围过滤
   - `content_size`: 摘要质量控制

3. **结果解析**
   - 自动解析标题、URL、摘要
   - 提取媒体信息和发布时间
   - 计算相关性得分

### 📦 依赖更新

- 新增 `zai>=1.0.0` 依赖包
- 保持其他依赖包版本不变

### 🔄 向后兼容

- 保留所有原有的 Bing 搜索功能
- 保持 API 接口完全兼容
- 用户可以选择使用 ZAI 或 Bing 搜索

### 📝 使用示例

#### 基础使用

```python
import asyncio
from e_websearch import SearchOrchestrator, SearchRequest, SourceType

async def example():
    # 设置 API 密钥
    import os
    os.environ["ZAI_API_KEY"] = "your-api-key"
    
    orchestrator = SearchOrchestrator()
    
    request = SearchRequest(
        query="2025年4月的财经新闻",
        max_results=15,
        sources=[SourceType.ZAI],
        filters={
            'time_range': 'month',
            'domain': 'www.sohu.com',
            'content_size': 'high'
        }
    )
    
    response = await orchestrator.search(request)
    print(f"找到 {len(response.results)} 个结果")

asyncio.run(example())
```

#### 多源搜索

```python
request = SearchRequest(
    query="人工智能教育",
    sources=[SourceType.ZAI, SourceType.WECHAT]
)
```

### 🧪 测试

提供了完整的测试示例：

1. **基础测试**: `examples/zai_basic_example.py`
   - 基础搜索功能
   - 多源搜索
   - 过滤器使用

2. **集成测试**: `examples/zai_test_example.py`
   - 完整功能测试
   - 健康检查
   - 性能测试

### ⚙️ 配置说明

#### 环境变量

```bash
# ZAI API 密钥
export ZAI_API_KEY="your-zhipu-ai-api-key"

# 可选：Bing API 密钥（保留向后兼容）
export BING_API_KEY="your-bing-api-key"
```

#### 搜索过滤器

- `time_range`: 时间范围过滤
  - `day`: 最近一天
  - `week`: 最近一周
  - `month`: 最近一个月
  - `year`: 最近一年
  - `noLimit`: 无限制

- `domain`: 域名过滤
  - 例如: `www.sohu.com`

- `content_size`: 摘要质量
  - `low`: 低质量摘要
  - `medium`: 中等质量摘要
  - `high`: 高质量摘要

### 🐛 错误处理

- 自动检测 zai 包是否安装
- 友好的错误消息和警告
- 优雅降级到 Bing 搜索
- 网络错误自动重试机制

### 📊 性能优化

- 异步并发搜索
- 智能缓存机制
- 速率限制保护
- 超时控制

### 🔒 安全性

- API 密钥通过环境变量配置
- 请求参数验证
- 输入清理和过滤

### 🎯 下一步计划

1. 支持更多 ZAI 搜索参数
2. 增加搜索结果缓存优化
3. 添加搜索统计和分析
4. 支持自定义搜索引擎扩展

---

## 迁移指南

### 从 Bing 搜索迁移到 ZAI

1. **安装依赖**
   ```bash
   pip install zai>=1.0.0
   ```

2. **设置 API 密钥**
   ```bash
   export ZAI_API_KEY="your-api-key"
   ```

3. **更新搜索源**
   ```python
   # 原来
   sources=[SourceType.BING]
   
   # 现在
   sources=[SourceType.ZAI]
   ```

4. **测试功能**
   ```bash
   python examples/zai_test_example.py
   ```

### 常见问题

**Q: 如何获取 ZAI API 密钥？**
A: 访问智谱AI官网注册账户并申请API密钥。

**Q: ZAI 搜索和 Bing 搜索有什么区别？**
A: ZAI 提供更好的中文搜索支持和高质量摘要，适合中文内容搜索。

**Q: 可以同时使用多个搜索引擎吗？**
A: 可以，通过 `sources=[SourceType.ZAI, SourceType.BING]` 实现多源搜索。

**Q: ZAI 搜索有速率限制吗？**
A: 是的，默认限制为 30 请求/分钟，可根据 API 计划调整。