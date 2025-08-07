"""
工具函数
"""

import re
import hashlib
import time
from datetime import datetime
from typing import Optional
from loguru import logger


def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    
    # 移除首尾空白
    text = text.strip()
    
    return text


def calculate_relevance_score(query: str, title: str, snippet: str) -> float:
    """计算相关性得分"""
    score = 0.0
    
    query_lower = query.lower()
    title_lower = title.lower()
    snippet_lower = snippet.lower()
    
    # 标题匹配权重更高
    if query_lower in title_lower:
        score += 0.6
    
    # 摘要匹配
    if query_lower in snippet_lower:
        score += 0.3
    
    # 计算查询词在文本中的密度
    query_words = query_lower.split()
    title_words = title_lower.split()
    snippet_words = snippet_lower.split()
    
    title_match_count = sum(1 for word in query_words if word in title_words)
    snippet_match_count = sum(1 for word in query_words if word in snippet_words)
    
    if query_words:
        title_density = title_match_count / len(query_words)
        snippet_density = snippet_match_count / len(query_words)
        score += title_density * 0.3 + snippet_density * 0.2
    
    return min(score, 1.0)


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
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
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
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        return len(self.requests) < self.max_requests
    
    def record_request(self):
        """记录请求"""
        self.requests.append(time.time())