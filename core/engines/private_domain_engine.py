"""
私域搜索引擎
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from loguru import logger

from .base_engine import BaseSearchEngine
from ..models import SearchResult, SearchRequest, SourceType
from ..config import PRIVATE_DOMAIN_CONFIG
from ..utils import clean_text, calculate_relevance_score, parse_publish_time


class PrivateDomainEngine(BaseSearchEngine):
    """私域搜索引擎"""
    
    def __init__(self):
        super().__init__("PrivateDomain")
        self.config = PRIVATE_DOMAIN_CONFIG
        self.wechat_searcher = WeChatSearcher(self.config.get('wechat', {}))
        self.zhihu_searcher = ZhihuSearcher(self.config.get('zhihu', {}))
    
    def is_available(self) -> bool:
        """检查是否有任何私域引擎是启用的"""
        return self.wechat_searcher.enabled or self.zhihu_searcher.enabled

    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """执行私域搜索"""
        tasks = []
        if SourceType.WECHAT in request.sources and self.wechat_searcher.enabled:
            tasks.append(self.wechat_searcher.search(request))
        
        if SourceType.ZHIHU in request.sources and self.zhihu_searcher.enabled:
            tasks.append(self.zhihu_searcher.search(request))
        
        if not tasks:
            return []

        results = []
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in search_results:
            if isinstance(result, list):
                results.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"私域搜索出错: {result}")
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:request.max_results]


class BasePrivateSearcher(ABC):
    """私域搜索器基类"""
    def __init__(self, config: Dict[str, Any], source_type: SourceType):
        self.enabled = config.get('enabled', False)
        self.api_url = config.get('api_url', '')
        self.timeout = config.get('timeout', 10)
        self.source_type = source_type
        if self.enabled and not self.api_url:
            logger.warning(f"{source_type.value} 搜索器已启用，但 API URL 未配置。")
            self.enabled = False

    async def search(self, request: SearchRequest) -> List[SearchResult]:
        if not self.enabled:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {'query': request.query, 'max_results': request.max_results}
                async with session.get(self.api_url, params=params, timeout=self.timeout) as response:
                    response.raise_for_status()
                    api_results = await response.json()
                    
                    parsed_results = [
                        self.parse_item(item, request.query)
                        for item in api_results
                    ]
                    # 过滤掉解析失败的结果 (None)
                    return [res for res in parsed_results if res]

        except aiohttp.ClientError as e:
            logger.error(f"{self.source_type.value} API 请求失败: {e}")
        except Exception as e:
            logger.error(f"{self.source_type.value} 搜索出错: {e}")
        return []
    
    @abstractmethod
    def parse_item(self, item: Dict[str, Any], query: str) -> Optional[SearchResult]:
        pass


class WeChatSearcher(BasePrivateSearcher):
    """微信公众号搜索器"""
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, SourceType.WECHAT)

    def parse_item(self, item: Dict[str, Any], query: str) -> Optional[SearchResult]:
        try:
            title = clean_text(item.get('title', ''))
            content = clean_text(item.get('content', '') or item.get('digest', ''))
            url = item.get('url', '')
            
            if not title or not url:
                return None
            
            # 基础关键词匹配
            if not any(keyword.lower() in title.lower() or keyword.lower() in content.lower() for keyword in query.split()):
                return None

            score = calculate_relevance_score(query, title, content)
            if score < 0.1:
                return None
            
            publish_time_str = item.get('publish_time') or item.get('create_time')
            publish_time = parse_publish_time(str(publish_time_str)) if publish_time_str else None

            return SearchResult(
                title=title,
                url=url,
                snippet=content[:200],
                source=self.source_type,
                score=score,
                publish_time=publish_time,
                author=item.get('author') or item.get('nickname'),
                content=content,
                metadata={'account': item.get('account', '')}
            )
        except Exception as e:
            logger.error(f"解析微信文章出错: {item.get('title', '')} - {e}")
            return None


class ZhihuSearcher(BasePrivateSearcher):
    """知乎搜索器"""
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, SourceType.ZHIHU)

    def parse_item(self, item: Dict[str, Any], query: str) -> Optional[SearchResult]:
        try:
            title = clean_text(item.get('title', '') or item.get('question', ''))
            content = clean_text(item.get('content', '') or item.get('answer', ''))
            url = item.get('url', '')

            if not title or not url:
                return None
                
            if not any(keyword.lower() in title.lower() or keyword.lower() in content.lower() for keyword in query.split()):
                return None

            score = calculate_relevance_score(query, title, content)
            if score < 0.1:
                return None

            return SearchResult(
                title=title,
                url=url,
                snippet=content[:200],
                source=self.source_type,
                score=score,
                author=item.get('author'),
                content=content,
                metadata={
                    'vote_count': item.get('vote_count', 0),
                    'comment_count': item.get('comment_count', 0)
                }
            )
        except Exception as e:
            logger.error(f"解析知乎内容出错: {item.get('title', '')} - {e}")
            return None
