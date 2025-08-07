# E-WebSearch API 服务

基于 ZAI Search Pro 的增强版 Web 搜索 REST API 服务，提供高质量的中文搜索功能。

## 🚀 快速开始

### 本地启动

```bash
# 1. 进入项目目录
cd e_websearch

# 2. 启动 API 服务
python run_api.py

# 3. 访问服务
# API 文档: http://localhost:8000/docs
# ReDoc 文档: http://localhost:8000/redoc
```

### Docker 启动

```bash
# 1. 构建镜像
docker build -t e-websearch-api .

# 2. 运行容器
docker run -p 8000:8000 \
  -e ZAI_API_KEY="your-api-key" \
  e-websearch-api

# 3. 使用 Docker Compose
docker-compose up -d
```

## 📋 API 接口

### 1. 基础信息

#### GET `/`
获取 API 基础信息

```bash
curl http://localhost:8000/
```

### 2. 搜索接口

#### POST `/search`
执行搜索请求

**请求体:**
```json
{
  "query": "人工智能最新发展",
  "max_results": 10,
  "include_content": false,
  "sources": ["zai"],
  "filters": {
    "time_range": "month",
    "domain": "www.sohu.com",
    "content_size": "high"
  }
}
```

**响应:**
```json
{
  "success": true,
  "message": "搜索完成",
  "results": [
    {
      "title": "人工智能的最新突破",
      "url": "https://example.com/ai-news",
      "snippet": "最新的人工智能技术发展...",
      "source": "zai",
      "score": 0.95,
      "publish_time": "2025-01-01T12:00:00",
      "author": "AI专家",
      "content": null,
      "images": [],
      "metadata": {
        "media": "科技日报",
        "language": "zh"
      }
    }
  ],
  "total_count": 1,
  "query": "人工智能最新发展",
  "execution_time": 1.23,
  "sources_used": ["zai"],
  "cache_hit": false
}
```

**cURL 示例:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python编程教程",
    "max_results": 5,
    "sources": ["zai"]
  }'
```

### 3. 健康检查

#### GET `/health`
检查服务健康状态

```bash
curl http://localhost:8000/health
```

**响应:**
```json
{
  "status": "healthy",
  "engines": {
    "bing": false,
    "zai": true,
    "private_domain": false
  },
  "available_sources": ["zai"],
  "cache_enabled": true,
  "last_search_time": 1.23,
  "error": null
}
```

### 4. 搜索建议

#### POST `/suggestions`
获取搜索建议

**请求体:**
```json
{
  "query": "人工智能"
}
```

**响应:**
```json
{
  "success": true,
  "suggestions": [
    "人工智能发展趋势",
    "人工智能应用场景",
    "人工智能技术原理"
  ],
  "query": "人工智能"
}
```

### 5. 系统统计

#### GET `/statistics`
获取系统统计信息

```bash
curl http://localhost:8000/statistics
```

### 6. 缓存管理

#### DELETE `/cache`
清空缓存

```bash
curl -X DELETE http://localhost:8000/cache
```

#### POST `/cache/cleanup`
清理过期缓存

```bash
curl -X POST http://localhost:8000/cache/cleanup
```

## 🔧 配置参数

### 搜索源 (sources)

- `zai`: ZAI Search Pro (推荐)
- `bing`: Bing 搜索
- `wechat`: 微信公众号
- `zhihu`: 知乎
- `baidu`: 百度搜索
- `custom`: 自定义源

### 过滤器 (filters)

#### 时间范围 (time_range)
- `day`: 最近一天
- `week`: 最近一周
- `month`: 最近一个月
- `year`: 最近一年
- `noLimit`: 无限制

#### 域名过滤 (domain)
```json
{
  "domain": "www.sohu.com"
}
```

#### 内容质量 (content_size)
- `low`: 低质量摘要
- `medium`: 中等质量摘要
- `high`: 高质量摘要

## 🌟 使用示例

### Python 客户端

```python
import requests
import json

# API 基础 URL
API_BASE = "http://localhost:8000"

def search_web(query, max_results=10):
    """搜索网页"""
    url = f"{API_BASE}/search"
    data = {
        "query": query,
        "max_results": max_results,
        "sources": ["zai"],
        "filters": {
            "time_range": "month",
            "content_size": "high"
        }
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 使用示例
result = search_web("Python教程")
print(f"找到 {result['total_count']} 个结果")
for item in result['results']:
    print(f"- {item['title']}")
    print(f"  {item['url']}")
```

### JavaScript 客户端

```javascript
// 搜索函数
async function searchWeb(query, maxResults = 10) {
  const response = await fetch('http://localhost:8000/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      max_results: maxResults,
      sources: ['zai'],
      filters: {
        time_range: 'month',
        content_size: 'high'
      }
    })
  });
  
  return await response.json();
}

// 使用示例
searchWeb('人工智能')
  .then(result => {
    console.log(`找到 ${result.total_count} 个结果`);
    result.results.forEach(item => {
      console.log(`- ${item.title}`);
      console.log(`  ${item.url}`);
    });
  });
```

### cURL 批量测试

```bash
#!/bin/bash

# 测试搜索
echo "测试搜索..."
curl -s -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"AI技术","max_results":3}' | jq '.results[] | .title'

# 测试健康检查
echo "测试健康检查..."
curl -s "http://localhost:8000/health" | jq '.status'

# 测试搜索建议
echo "测试搜索建议..."
curl -s -X POST "http://localhost:8000/suggestions" \
  -H "Content-Type: application/json" \
  -d '{"query":"机器学习"}' | jq '.suggestions'
```

## 🛠️ 部署配置

### 环境变量

```bash
# ZAI API 密钥 (必需)
export ZAI_API_KEY="your-zhipuai-api-key"

# Bing API 密钥 (可选)
export BING_API_KEY="your-bing-api-key"

# 服务配置
export API_HOST="0.0.0.0"
export API_PORT="8000"
export LOG_LEVEL="info"
```

### 生产环境部署

```bash
# 使用 Gunicorn
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 使用 Docker Compose (推荐)
docker-compose -f docker-compose.yml up -d

# 使用 Nginx 反向代理
# 配置文件示例见下方
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 性能优化

### 缓存配置

```python
# 在 config.py 中调整缓存设置
CACHE_CONFIG = {
    "enabled": True,
    "ttl": 3600,  # 1小时
    "max_size": 1000
}
```

### 并发控制

```python
# 启动时配置工作进程数
python run_api.py --workers 4
```

### 限流配置

可以添加 slowapi 中间件进行 API 限流：

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/search")
@limiter.limit("10/minute")
async def search(request: Request, ...):
    # 搜索逻辑
```

## 🔍 监控和日志

### 日志配置

日志文件位置：
- API 日志: `logs/api.log`
- 搜索日志: `logs/websearch.log`
- 错误日志: `logs/error.log`

### 健康监控

```bash
# 定期健康检查
*/5 * * * * curl -f http://localhost:8000/health || echo "API服务异常"
```

### 性能监控

```python
# 添加 Prometheus 监控
from prometheus_client import Counter, Histogram, generate_latest

search_counter = Counter('searches_total', 'Total searches')
search_duration = Histogram('search_duration_seconds', 'Search duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🐛 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查找占用端口的进程
   lsof -i :8000
   # 或更换端口
   python run_api.py --port 8001
   ```

2. **ZAI API 密钥错误**
   ```bash
   # 检查环境变量
   echo $ZAI_API_KEY
   # 或在启动时设置
   ZAI_API_KEY="your-key" python run_api.py
   ```

3. **模块导入错误**
   ```bash
   # 确保在正确目录
   cd e_websearch
   # 检查 Python 路径
   export PYTHONPATH=/path/to/e_websearch
   ```

### 日志分析

```bash
# 查看最新日志
tail -f logs/api.log

# 搜索错误日志
grep -i error logs/api.log

# 分析搜索性能
grep "execution_time" logs/api.log | awk '{print $NF}'
```

## 📞 技术支持

如果遇到问题，请：

1. 查看 API 文档: `http://localhost:8000/docs`
2. 检查健康状态: `http://localhost:8000/health`
3. 查看日志文件: `logs/api.log`
4. 提交 Issue 或联系技术支持

---

🎉 现在您可以使用强大的 E-WebSearch API 服务了！