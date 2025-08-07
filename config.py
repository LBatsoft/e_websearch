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
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Redis配置
# 当在 Docker 中运行时，host 应设置为 'redis'
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
    "decode_responses": True,
}

# 缓存配置
CACHE_CONFIG = {
    "enabled": True,
    "ttl": 3600,  # 缓存过期时间（秒）
    "max_size": 1000,  # 内存缓存最大条目数
    "cleanup_interval": 300,  # 清理间隔（秒）
    "lru_enabled": True,  # 启用LRU退出机制
    "stats_enabled": True,  # 启用缓存统计
    "max_connections": 20,  # Redis最大连接数
    "retry_on_timeout": True,  # Redis超时重试
    "health_check_interval": 30,  # Redis健康检查间隔
    "fallback_enabled": True,  # 启用本地缓存降级
    "sync_interval": 60,  # 缓存同步间隔（秒）
}

# 内容提取配置
CONTENT_EXTRACT_CONFIG = {
    "max_concurrent": 5,
    "timeout": 30,
    "max_content_length": 50000,
    "blocked_domains": ["facebook.com", "twitter.com", "instagram.com"],
}


# 私域搜索配置
def _get_bool_env(key: str, default: bool = False) -> bool:
    """获取布尔类型的环境变量"""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def _get_int_env(key: str, default: int) -> int:
    """获取整数类型的环境变量"""
    try:
        return int(os.getenv(key, default))
    except (TypeError, ValueError):
        return default


# 打印环境变量用于调试
print("环境变量配置:")
print(f"WECHAT_SEARCH_ENABLED: {os.getenv('WECHAT_SEARCH_ENABLED')}")
print(f"WECHAT_API_URL: {os.getenv('WECHAT_API_URL')}")
print(f"WECHAT_API_TIMEOUT: {os.getenv('WECHAT_API_TIMEOUT')}")

PRIVATE_DOMAIN_CONFIG = {
    "wechat": {
        "enabled": _get_bool_env("WECHAT_SEARCH_ENABLED", False),
        "api_url": os.getenv("WECHAT_API_URL", ""),
        "timeout": _get_int_env("WECHAT_API_TIMEOUT", 30),
    },
    "zhihu": {
        "enabled": _get_bool_env("ZHIHU_SEARCH_ENABLED", False),
        "api_url": os.getenv("ZHIHU_API_URL", ""),
        "timeout": _get_int_env("ZHIHU_API_TIMEOUT", 30),
    },
}
# 使用 "memory"、"redis" 或 "distributed"
CACHE_TYPE = os.getenv("CACHE_TYPE", "memory")


# 动态更新缓存配置
def get_cache_config():
    """获取缓存配置，支持环境变量覆盖"""
    config = CACHE_CONFIG.copy()
    config.update(
        {
            "ttl": _get_int_env("CACHE_TTL", config["ttl"]),
            "max_size": _get_int_env("CACHE_MAX_SIZE", config["max_size"]),
            "cleanup_interval": _get_int_env(
                "CACHE_CLEANUP_INTERVAL", config["cleanup_interval"]
            ),
            "lru_enabled": _get_bool_env("CACHE_LRU_ENABLED", config["lru_enabled"]),
            "stats_enabled": _get_bool_env(
                "CACHE_STATS_ENABLED", config["stats_enabled"]
            ),
            "max_connections": _get_int_env(
                "CACHE_MAX_CONNECTIONS", config["max_connections"]
            ),
            "retry_on_timeout": _get_bool_env(
                "CACHE_RETRY_ON_TIMEOUT", config["retry_on_timeout"]
            ),
            "health_check_interval": _get_int_env(
                "CACHE_HEALTH_CHECK_INTERVAL", config["health_check_interval"]
            ),
            "fallback_enabled": _get_bool_env(
                "CACHE_FALLBACK_ENABLED", config["fallback_enabled"]
            ),
            "sync_interval": _get_int_env(
                "CACHE_SYNC_INTERVAL", config["sync_interval"]
            ),
        }
    )
    return config
