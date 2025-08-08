"""
工具函数
"""

import hashlib
import re
import time
from datetime import datetime
from typing import Optional

from loguru import logger


def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ""

    # 移除多余的空白字符
    text = re.sub(r"\s+", " ", text)

    # 移除首尾空白
    text = text.strip()

    return text


def parse_publish_time(date_str: str) -> Optional[datetime]:
    """解析发布时间"""
    if not date_str:
        return None

    # 常见的日期格式
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # 如果无法解析，返回None
    logger.warning(f"无法解析日期格式: {date_str}")
    return None


def generate_cache_key(query: str, sources: str) -> str:
    """生成缓存键"""
    key_string = f"{query}|{sources}"
    return hashlib.md5(key_string.encode()).hexdigest()


def setup_logging():
    """设置日志"""
    logger.add(
        "logs/websearch.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )


class RateLimiter:
    """速率限制器"""

    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def can_request(self) -> bool:
        """检查是否可以发起请求"""
        now = time.time()

        # 清理过期的请求记录
        self.requests = [
            req_time for req_time in self.requests if now - req_time < self.time_window
        ]

        return len(self.requests) < self.max_requests

    def record_request(self):
        """记录请求"""
        self.requests.append(time.time())
