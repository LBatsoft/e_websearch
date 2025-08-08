# LLM API 密钥配置指南

## 概述

E-WebSearch 支持多种 LLM（大语言模型）提供商，可以为搜索结果提供智能摘要和标签功能。本文档详细说明如何配置各种 LLM API 密钥。

## 配置步骤

### 1. 创建环境配置文件

```bash
# 复制示例配置文件
cp dotenv.example .env
```

### 2. 编辑 .env 文件

打开 `.env` 文件，配置相应的 API 密钥：

```bash
# 编辑配置文件
nano .env
# 或者使用其他编辑器
code .env
```

### 3. 配置 API 密钥

在 `.env` 文件中添加以下配置（至少配置一个）：

```bash
# ===== LLM 增强功能配置 =====

# 智谱AI (ZhipuAI) - 推荐用于中文内容
ZAI_API_KEY=your_zhipuai_api_key_here

# OpenAI - 推荐用于英文内容
OPENAI_API_KEY=your_openai_api_key_here

# Azure OpenAI - 企业级服务
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint_here

# 百度文心 - 中文理解能力强
BAIDU_API_KEY=your_baidu_api_key_here
BAIDU_SECRET_KEY=your_baidu_secret_key_here

# 阿里通义千问 - 多模态能力强
DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

## 各提供商配置详解

### 1. 智谱AI (ZhipuAI) - 推荐

**特点**: 中文优化，响应快速，成本较低

**获取步骤**:
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册账号并完成实名认证
3. 创建应用获取 API Key
4. 配置到 `.env` 文件：

```bash
ZAI_API_KEY=your_zhipuai_api_key_here
```

**推荐模型**: `glm-4`

### 2. OpenAI

**特点**: 英文效果好，功能强大，全球使用广泛

**获取步骤**:
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册账号并添加支付方式
3. 在 API Keys 页面创建密钥
4. 配置到 `.env` 文件：

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

**推荐模型**: `gpt-4`, `gpt-3.5-turbo`

### 3. Azure OpenAI

**特点**: 企业级服务，稳定可靠，支持私有部署

**获取步骤**:
1. 访问 [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/cognitive-services/openai-service)
2. 在 Azure 门户中创建 OpenAI 资源
3. 获取 API Key 和 Endpoint
4. 配置到 `.env` 文件：

```bash
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

**推荐模型**: `gpt-4`, `gpt-35-turbo`

### 4. 百度文心

**特点**: 中文理解能力强，国内服务稳定

**获取步骤**:
1. 访问 [百度智能云](https://cloud.baidu.com/product/wenxinworkshop)
2. 注册账号并开通文心一言服务
3. 创建应用获取 API Key 和 Secret Key
4. 配置到 `.env` 文件：

```bash
BAIDU_API_KEY=your_baidu_api_key_here
BAIDU_SECRET_KEY=your_baidu_secret_key_here
```

**推荐模型**: `ernie-bot-4`, `ernie-bot-turbo`

### 5. 阿里通义千问

**特点**: 多模态能力强，阿里生态集成好

**获取步骤**:
1. 访问 [阿里云 DashScope](https://dashscope.aliyun.com/)
2. 注册账号并开通服务
3. 获取 API Key
4. 配置到 `.env` 文件：

```bash
DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

**推荐模型**: `qwen-plus`, `qwen-turbo`

## 验证配置

### 1. 运行测试脚本

```bash
python test_llm_functionality.py
```

### 2. 检查服务日志

启动 API 服务后，查看日志确认 LLM 提供商初始化状态：

```bash
python run_api.py
```

正常启动时应该看到类似日志：
```
智谱AI提供商初始化成功
LLM 增强器初始化成功，可用提供商: ['zhipuai']
```

### 3. 测试 API 调用

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能发展趋势",
    "max_results": 5,
    "sources": ["zai"],
    "llm_summary": true,
    "llm_tags": true,
    "model_provider": "zhipuai",
    "model_name": "glm-4"
  }'
```

## 常见问题

### 1. API 密钥无效

**症状**: 服务启动时显示 "不可用" 或调用时返回错误

**解决方案**:
- 检查 API 密钥是否正确复制
- 确认 API 密钥是否有效（在提供商平台测试）
- 检查账户余额是否充足

### 2. 模型名称错误

**症状**: 调用时返回 "模型编码不能为空" 错误

**解决方案**:
- 确保指定了正确的模型名称
- 对于智谱AI，使用 `glm-4` 或 `glm-3-turbo`
- 对于 OpenAI，使用 `gpt-4` 或 `gpt-3.5-turbo`

### 3. 网络连接问题

**症状**: 请求超时或连接失败

**解决方案**:
- 检查网络连接
- 确认防火墙设置
- 尝试使用代理（如需要）

### 4. 配额限制

**症状**: 返回配额超限错误

**解决方案**:
- 检查 API 使用量
- 升级账户套餐
- 调整请求频率

## 最佳实践

### 1. 安全性

- 不要将 API 密钥提交到代码仓库
- 使用环境变量或配置文件管理密钥
- 定期轮换 API 密钥

### 2. 成本控制

- 选择合适的模型（功能 vs 成本）
- 设置合理的 `llm_max_items` 参数
- 监控 API 使用量

### 3. 性能优化

- 根据内容语言选择合适的提供商
- 使用缓存减少重复请求
- 合理设置超时时间

### 4. 错误处理

- 实现重试机制
- 设置降级策略
- 监控错误日志

## 配置示例

### 完整配置示例

```bash
# .env 文件示例

# 智谱AI (推荐用于中文)
ZAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI (推荐用于英文)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Azure OpenAI (企业级)
AZURE_OPENAI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# 百度文心 (中文优化)
BAIDU_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
BAIDU_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 阿里通义千问 (多模态)
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 最小配置示例

```bash
# 仅配置智谱AI (推荐)
ZAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 相关文档

- [LLM 增强功能使用指南](llm-enhancement-guide.md)
- [API 使用文档](api-readme.md)
- [项目结构说明](STRUCTURE.md)
