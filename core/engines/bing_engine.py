"""
Bing搜索引擎
"""

import asyncio
import aiohttp
from typing import List, Optional
from datetime import datetime
from loguru import logger

from .base_engine import BaseSearchEngine
from config import BING_SEARCH_URL, BING_API_KEY
from core.models import SearchResult, SearchRequest, SourceType
from core.utils import clean_text, calculate_relevance_score, parse_publish_time, RateLimiter


class BingSearchEngine(BaseSearchEngine):
    """Bing搜索引擎"""
    
    def __init__(self):
        super().__init__("Bing")
        self.api_key = BING_API_KEY
        self.search_url = BING_SEARCH_URL
        self.rate_limiter = RateLimiter(max_requests=50, time_window=60)
        
        if not self.api_key:
            logger.warning("Bing API密钥未配置，Bing搜索将不可用")
            self.enabled = False
    
    def is_available(self) -> bool:
        """检查Bing搜索是否可用"""
        return self.enabled and bool(self.api_key)
    
    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """执行Bing搜索"""
        if not self.is_available():
            logger.warning("Bing搜索引擎不可用")
            return []
        
        if not self.rate_limiter.can_request():
            logger.warning("Bing搜索达到速率限制")
            return []
        
        try:
            results = await self._perform_search(request)
            self.rate_limiter.record_request()
            logger.info(f"Bing搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"Bing搜索出错: {e}")
            return []
    
    async def _perform_search(self, request: SearchRequest) -> List[SearchResult]:
        """执行实际的搜索请求"""
        headers = {
            'Ocp-Apim-Subscription-Key': self.api_key,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        params = {
            'q': request.query,
            'count': min(request.max_results, 50),  # Bing最多返回50个结果
            'mkt': 'zh-CN',
            'safesearch': 'Moderate',
            'responseFilter': 'Webpages'
        }
        
        # 添加时间过滤器
        if request.filters.get('time_range'):
            params['freshness'] = request.filters['time_range']
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.search_url,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    logger.error(f"Bing API请求失败: {response.status}")
                    return []
                
                data = await response.json()
                return self._parse_results(data, request.query)
    
    def _parse_results(self, data: dict, query: str) -> List[SearchResult]:
        """解析Bing搜索结果"""
        results = []
        
        webpages = data.get('webPages', {})
        if not webpages:
            return results
        
        for item in webpages.get('value', []):
            try:
                title = clean_text(item.get('name', ''))
                url = item.get('url', '')
                snippet = clean_text(item.get('snippet', ''))
                
                if not title or not url:
                    continue
                
                # 计算相关性得分
                score = calculate_relevance_score(query, title, snippet)
                
                # 解析发布时间
                publish_time = None
                date_published = item.get('datePublished')
                if date_published:
                    publish_time = parse_publish_time(date_published)
                
                # 提取深度链接
                deep_links = []
                if 'deepLinks' in item:
                    for deep_link in item['deepLinks']:
                        deep_links.append({
                            'name': deep_link.get('name', ''),
                            'url': deep_link.get('url', '')
                        })
                
                result = SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source=SourceType.BING,
                    score=score,
                    publish_time=publish_time,
                    metadata={
                        'display_url': item.get('displayUrl', ''),
                        'deep_links': deep_links,
                        'language': item.get('language', 'zh'),
                        'is_navigational': item.get('isNavigational', False)
                    }
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"解析Bing搜索结果出错: {e}")
                continue
        
        # 按得分排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    async def get_suggestions(self, query: str) -> List[str]:
        """获取搜索建议"""
        if not self.is_available():
            return []
        
        try:
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key
            }
            
            params = {
                'q': query,
                'mkt': 'zh-CN'
            }
            
            suggestion_url = "https://api.bing.microsoft.com/v7.0/suggestions"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    suggestion_url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        suggestions = []
                        
                        for group in data.get('suggestionGroups', []):
                            for suggestion in group.get('searchSuggestions', []):
                                suggestions.append(suggestion.get('query', ''))
                        
                        return suggestions[:10]
            
        except Exception as e:
            logger.error(f"获取Bing搜索建议出错: {e}")
        
        return [] 