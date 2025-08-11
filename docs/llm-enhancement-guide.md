# LLM 增强功能使用指南

## 概述

E-WebSearch 提供了强大的 LLM（大语言模型）增强功能，可以为搜索结果生成智能摘要和标签，提升用户体验。

> **📢 重要更新**：v1.1.0 版本已修复 LLM 增强字段为空的问题。现在 `llm_summary` 和 `labels` 字段可以正确返回解析后的数据。

## 功能特性

### 1. 整体摘要 (Overall Summary)
- 对多个搜索结果进行智能总结
- 生成简洁、准确的中文摘要
- 支持自定义摘要长度和语言

### 2. 整体标签 (Overall Tags)
- 为搜索结果集合生成相关标签
- 提供 5-8 个中文名词短语标签
- 便于快速理解搜索结果主题

### 3. 逐条结果增强 (Per-Result Enhancement)
- 为每个搜索结果生成独立摘要
- 为每个结果生成相关标签
- 提供更细粒度的内容理解

## 支持的模型提供商

### 智谱AI (ZhipuAI)
- **API Key**: `ZAI_API_KEY`
- **默认模型**: `glm-4`
- **特点**: 中文优化，响应快速

### OpenAI
- **API Key**: `OPENAI_API_KEY`
- **默认模型**: `gpt-4`
- **特点**: 英文效果好，功能强大

### Azure OpenAI
- **API Key**: `AZURE_OPENAI_API_KEY`
- **Endpoint**: `AZURE_OPENAI_ENDPOINT`
- **特点**: 企业级服务，稳定可靠

### 百度文心
- **API Key**: `BAIDU_API_KEY`
- **Secret Key**: `BAIDU_SECRET_KEY`
- **特点**: 中文理解能力强

### 阿里通义千问
- **API Key**: `DASHSCOPE_API_KEY`
- **默认模型**: `qwen-plus`
- **特点**: 多模态能力强

### 自定义 HTTP 接口
- **Endpoint**: 自定义 URL
- **Headers**: 自定义请求头
- **特点**: 灵活集成自有模型

## API 使用方法

### 基础搜索请求

```python
import requests

# 基础搜索（无 LLM 增强）
response = requests.post("http://localhost:8000/search", json={
    "query": "人工智能最新发展",
    "max_results": 10,
    "sources": ["zai"]
})
```

### 启用 LLM 摘要

```python
# 启用整体摘要
response = requests.post("http://localhost:8000/search", json={
    "query": "人工智能最新发展",
    "max_results": 10,
    "sources": ["zai"],
    "llm_summary": True,
    "llm_max_items": 6,
    "model_provider": "zhipuai",
    "model_name": "glm-4"
})

# 解析响应
data = response.json()
if data["success"]:
    print("摘要:", data.get("llm_summary"))
    print("标签:", data.get("llm_tags", []))
```

### 启用标签生成

```python
# 启用整体标签
response = requests.post("http://localhost:8000/search", json={
    "query": "机器学习应用",
    "max_results": 8,
    "sources": ["zai"],
    "llm_tags": True,
    "llm_max_items": 5,
    "model_provider": "zhipuai"
})
```

### 启用逐条结果增强

```python
# 启用逐条结果增强
response = requests.post("http://localhost:8000/search", json={
    "query": "Python 编程教程",
    "max_results": 5,
    "sources": ["zai"],
    "llm_per_result": True,
    "llm_max_items": 4,
    "model_provider": "zhipuai"
})

# 解析逐条增强结果
data = response.json()
if data["success"]:
    # ✅ 推荐方式：直接访问每条结果的增强字段
    for result in data["results"]:
        print(f"标题: {result['title']}")
        print(f"LLM摘要: {result.get('llm_summary')}")  # 直接获取解析后的摘要
        print(f"标签: {result.get('labels', [])}")      # 直接获取解析后的标签
    
    # 🔄 兼容方式：通过 llm_per_result 映射访问
    per_result = data.get("llm_per_result", {})
    if per_result:
        for url, enhanced in per_result.items():
            print(f"URL: {url}")
            print(f"摘要: {enhanced.get('llm_summary')}")
            print(f"标签: {enhanced.get('labels', [])}")
```

### 完整功能示例

```python
# 启用所有 LLM 增强功能
response = requests.post("http://localhost:8000/search", json={
    "query": "区块链技术发展趋势",
    "max_results": 10,
    "sources": ["zai"],
    "llm_summary": True,
    "llm_tags": True,
    "llm_per_result": True,
    "llm_max_items": 8,
    "llm_language": "zh",
    "model_provider": "zhipuai",
    "model_name": "glm-4"
})
```

## 请求参数说明

### LLM 增强参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `llm_summary` | bool | false | 是否生成整体摘要 |
| `llm_tags` | bool | false | 是否生成整体标签 |
| `llm_per_result` | bool | false | 是否对每条结果生成摘要/标签 |
| `llm_max_items` | int | 5 | 参与增强的最多结果数 (1-20) |
| `llm_language` | string | "zh" | 输出语言 (zh/en) |
| `model_provider` | string | "auto" | 模型提供商 |
| `model_name` | string | "" | 具体模型名称 |

### 模型提供商选项

- `"auto"`: 自动选择（按优先级：zhipuai > openai > azure > baidu > qwen）
- `"zhipuai"`: 智谱AI
- `"openai"`: OpenAI
- `"azure"`: Azure OpenAI
- `"baidu"`: 百度文心
- `"qwen"`: 阿里通义千问
- `"custom"`: 自定义 HTTP 接口

## 响应格式

### 成功响应示例（含逐条增强字段）

> **💡 提示**：每条搜索结果中的 `llm_summary` 和 `labels` 字段包含解析后的数据，可以直接使用。`llm_per_result` 映射提供相同的增强信息，按 URL 索引。

```json
{
  "success": true,
  "message": "搜索完成",
  "results": [
    {
      "title": "人工智能在医疗领域的应用",
      "url": "https://example.com/article1",
      "snippet": "人工智能技术正在医疗领域发挥重要作用...",
      "source": "zai",
      "score": 0.95,
      "llm_summary": "文章介绍了AI在医疗诊断中的应用",
      "labels": ["医疗AI", "诊断技术", "智能医疗"]
    }
  ],
  "total_count": 10,
  "query": "人工智能最新发展",
  "execution_time": 2.5,
  "sources_used": ["zai"],
  "cache_hit": false,
  "llm_summary": "根据搜索结果，人工智能在多个领域都有重要应用，包括医疗、教育、金融等。最新发展主要集中在深度学习、自然语言处理和计算机视觉等方面。",
  "llm_tags": ["人工智能", "深度学习", "医疗应用", "技术创新", "未来发展"],
  "llm_per_result": {
    "https://example.com/article1": {
      "llm_summary": "文章介绍了AI在医疗诊断中的应用",
      "labels": ["医疗AI", "诊断技术", "智能医疗"]
    }
  }
}
```

## 环境配置

### 1. 设置环境变量

创建 `.env` 文件并配置相应的 API 密钥：

```bash
# 智谱AI
ZAI_API_KEY=your_zhipuai_api_key

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_api_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint

# 百度文心
BAIDU_API_KEY=your_baidu_api_key
BAIDU_SECRET_KEY=your_baidu_secret_key

# 阿里通义千问
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python run_api.py
```

## 使用示例

### Python 客户端示例

```python
from examples.llm_enhanced_example import EWebSearchLLMClient

# 创建客户端
client = EWebSearchLLMClient("http://localhost:8000")

# 执行带 LLM 增强的搜索
result = client.search_with_llm(
    query="机器学习算法",
    max_results=8,
    sources=["zai"],
    llm_summary=True,
    llm_tags=True,
    llm_per_result=True,
    model_provider="zhipuai",
    model_name="glm-4"
)

# 处理结果
if result["success"]:
    print("整体摘要:", result.get("llm_summary"))
    print("整体标签:", result.get("llm_tags", []))
    
    # ✅ 推荐方式：直接访问每条结果的增强字段
    for item in result["results"]:
        print(f"标题: {item['title']}")
        print(f"LLM摘要: {item.get('llm_summary')}")  # 直接获取解析后的摘要
        print(f"标签: {item.get('labels', [])}")      # 直接获取解析后的标签
    
    # 🔄 兼容方式：通过 llm_per_result 映射访问
    for item in result["results"]:
        enhanced = result.get("llm_per_result", {}).get(item['url'], {})
        if enhanced:
            print(f"URL: {item['url']}")
            print(f"映射摘要: {enhanced.get('llm_summary')}")
            print(f"映射标签: {enhanced.get('labels', [])}")
```

### 命令行示例

```bash
# 演示摘要功能
python examples/llm_enhanced_example.py --summary

# 演示逐条增强功能
python examples/llm_enhanced_example.py --per-result
```

## 最佳实践

### 1. 性能优化

- 合理设置 `llm_max_items` 参数，避免处理过多结果
- 根据需求选择启用功能，避免不必要的计算
- 使用缓存减少重复计算

### 2. 成本控制

- 选择合适的模型提供商和模型
- 限制 `llm_max_items` 数量
- 根据需要启用功能，避免过度使用

### 3. 错误处理

```python
try:
    result = client.search_with_llm(
        query="查询词",
        llm_summary=True,
        model_provider="zhipuai"
    )
    
    if result["success"]:
        # 处理成功结果
        pass
    else:
        # 处理失败情况
        print(f"搜索失败: {result['message']}")
        
except Exception as e:
    print(f"请求异常: {e}")
```

### 4. 模型选择建议

- **中文内容**: 推荐使用智谱AI (zhipuai)
- **英文内容**: 推荐使用 OpenAI
- **企业环境**: 推荐使用 Azure OpenAI
- **成本敏感**: 推荐使用百度文心或阿里通义千问

## 故障排除

### 常见问题

1. **LLM 增强未生效**
   - 检查 API 密钥配置
   - 确认模型提供商可用
   - 查看服务日志

2. **LLM 增强字段为空**
   - ✅ **已修复**：确保使用最新版本的代码
   - 检查是否正确启用了 `llm_per_result` 参数
   - 确认 `llm_max_items` 设置合理（建议 3-8）
   - 查看服务日志确认 LLM 增强是否执行成功

3. **响应时间过长**
   - 减少 `llm_max_items` 数量
   - 选择更快的模型
   - 检查网络连接

4. **摘要质量不佳**
   - 调整 `llm_language` 参数
   - 尝试不同的模型提供商
   - 优化查询词

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查服务健康状态
health = client.health_check()
print("服务状态:", health)
```

## 更新日志

### v1.1.0 (最新)
- 🐛 **修复**：LLM 增强字段（`llm_summary` 和 `labels`）在搜索结果中为空的问题
- 🔧 **改进**：优化 JSON 解析逻辑，支持代码块格式的 LLM 响应
- 📝 **文档**：更新使用说明和故障排除指南

### v1.0.0
- 支持多种 LLM 提供商
- 实现整体摘要和标签功能
- 支持逐条结果增强
- 提供完整的 API 接口

## 技术支持

如有问题或建议，请参考：
- API 文档: `/docs`
- 示例代码: `examples/`
- 项目仓库: GitHub
