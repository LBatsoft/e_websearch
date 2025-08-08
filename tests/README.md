# 测试脚本说明

本目录包含 E-WebSearch 项目的各种测试脚本。

## 测试脚本列表

### LLM 相关测试

1. **`test_llm_functionality.py`** - LLM 增强功能综合测试
   - 检查环境变量配置
   - 测试 API 健康状态
   - 测试基础搜索功能
   - 测试 LLM 增强功能

2. **`test_zhipuai_direct.py`** - 智谱AI API 直接测试
   - 直接测试智谱AI API 连接
   - 验证 API 密钥配置
   - 测试简单对话功能

3. **`test_llm_enhancer_direct.py`** - LLM 增强器直接测试
   - 直接测试 LLM 增强器功能
   - 测试整体摘要和标签生成
   - 测试逐条结果增强

### 系统测试

4. **`test_api_simple.py`** - API 简单测试
5. **`test_client.py`** - 客户端测试
6. **`test_distributed_cache.py`** - 分布式缓存测试
7. **`test_performance.py`** - 性能测试
8. **`test_system.py`** - 系统集成测试

## 运行测试

### 前提条件

1. 确保已配置 `.env` 文件中的 API 密钥
2. 确保 API 服务正在运行（`python run_api.py`）

### 运行 LLM 测试

```bash
# 测试 LLM 功能
python tests/test_llm_functionality.py

# 测试智谱AI API
python tests/test_zhipuai_direct.py

# 测试 LLM 增强器
python tests/test_llm_enhancer_direct.py
```

### 运行系统测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python tests/test_api_simple.py
python tests/test_performance.py
```

## 测试结果说明

### LLM 功能测试结果

- ✅ **环境变量检查**: 显示已配置的 API 密钥
- ✅ **API 健康检查**: 验证服务状态
- ✅ **基础搜索测试**: 测试搜索功能
- ✅ **LLM 增强测试**: 测试摘要和标签生成

### 预期输出

成功运行时应该看到：
- 智谱AI 提供商初始化成功
- LLM 增强器初始化成功
- 生成摘要和标签
- 逐条结果增强

### 故障排除

如果测试失败，请检查：
1. `.env` 文件中的 API 密钥配置
2. API 服务是否正在运行
3. 网络连接是否正常
4. 智谱AI 账户余额是否充足

## 注意事项

- 测试脚本会消耗 API 调用次数
- 建议在开发环境中运行测试
- 生产环境中请谨慎使用测试脚本
