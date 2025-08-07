"""
系统配置
"""

import os
from pathlib import Path

# 基础配置
BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "cache"
LOGS_DIR = BASE_DIR / "logs"

# 创建必要目录
CACHE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Bing搜索配置
BING_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search"
BING_API_KEY = os.getenv("BING_API_KEY", "")

# ZAI Search Pro配置
ZAI_API_KEY = os.getenv("ZAI_API_KEY", "")

# 浏览器配置
BROWSER_CONFIG = {
    "headless": True,
    "timeout": 30000,
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Redis配置
# 当在 Docker 中运行时，host 应设置为 'redis'
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
    "decode_responses": True
}

# 缓存配置
CACHE_CONFIG = {
    "enabled": True,
    "ttl": 3600,  # 1小时
    "max_size": 1000
}

# 内容提取配置
CONTENT_EXTRACT_CONFIG = {
    "max_concurrent": 5,
    "timeout": 30,
    "max_content_length": 50000,
    "blocked_domains": [
        "facebook.com",
        "twitter.com", 
        "instagram.com"
    ]
}

# 私域搜索配置
PRIVATE_DOMAIN_CONFIG = {
    "wechat": {
        "enabled": os.getenv("WECHAT_SEARCH_ENABLED", "false").lower() == "true",
        "api_url": os.getenv("WECHAT_API_URL", ""),
        "timeout": int(os.getenv("WECHAT_API_TIMEOUT", 10))
    },
    "zhihu": {
        "enabled": os.getenv("ZHIHU_SEARCH_ENABLED", "false").lower() == "true",
        "api_url": os.getenv("ZHIHU_API_URL", ""),
        "timeout": int(os.getenv("ZHIHU_API_TIMEOUT", 10))
    }
} 
# 使用 "memory" 或 "redis"
CACHE_TYPE = os.getenv("CACHE_TYPE", "memory")
