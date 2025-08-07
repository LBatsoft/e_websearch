"""
ZAI Search Pro搜索引擎
"""

import asyncio
from typing import List, Optional
from datetime import datetime
from loguru import logger

from .base_engine import BaseSearchEngine
from ..models import SearchResult, SearchRequest, SourceType
from ..config import ZAI_API_KEY
from ..utils import clean_text, calculate_relevance_score, parse_publish_time, RateLimiter

try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None
    logger.warning("zhipuai 模块未安装，请运行: pip install zhipuai")


class ZaiSearchEngine(BaseSearchEngine):
    """ZAI Search Pro搜索引擎"""
    
    def __init__(self):
        super().__init__("ZAI Search Pro")
        self.enabled = True
        
        self.api_key = ZAI_API_KEY
        self.rate_limiter = RateLimiter(max_requests=30, time_window=60)
        
        if not ZhipuAI:
            logger.warning("ZAI客户端不可用，请安装zhipuai包")
            self.enabled = False
        elif not self.api_key:
            logger.warning("ZAI API密钥未配置，ZAI搜索将不可用")
            self.enabled = False
        else:
            try:
                self.client = ZhipuAI(api_key=self.api_key)
                logger.info("ZAI搜索引擎初始化成功")
            except Exception as e:
                logger.error(f"初始化ZAI客户端失败: {e}")
                self.enabled = False
    
    def is_available(self) -> bool:
        """检查ZAI搜索是否可用"""
        return self.enabled and bool(self.api_key) and ZhipuAI is not None
    
    async def search(self, request) -> List[SearchResult]:
        """执行ZAI搜索"""
        if not self.is_available():
            logger.warning("ZAI搜索引擎不可用")
            return []
        
        if not self.rate_limiter.can_request():
            logger.warning("ZAI搜索达到速率限制")
            return []
        
        try:
            results = await self._perform_search(request)
            self.rate_limiter.record_request()
            logger.info(f"ZAI搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"ZAI搜索出错: {e}")
            return []
    
    async def _perform_search(self, request) -> List[SearchResult]:
        """执行实际的搜索请求"""
        # 处理请求对象（可能是字典或对象）
        if isinstance(request, dict):
            query = request.get('query', '')
            max_results = request.get('max_results', 10)
            filters = request.get('filters', {})
        else:
            query = getattr(request, 'query', '')
            max_results = getattr(request, 'max_results', 10)
            filters = getattr(request, 'filters', {})
        
        search_params = {
            "search_engine": "search_pro",
            "search_query": query,
            "count": min(max_results, 50),  # ZAI最多返回50个结果
            "content_size": "high"  # 控制网页摘要的字数
        }
        
        # 添加过滤器
        if filters:
            # 域名过滤
            if 'domain' in filters:
                search_params['search_domain_filter'] = filters['domain']
            
            # 时间范围过滤
            if 'time_range' in filters:
                time_range = filters['time_range']
                if time_range in ['day', 'week', 'month', 'year']:
                    search_params['search_recency_filter'] = time_range
                else:
                    search_params['search_recency_filter'] = 'noLimit'
        
        try:
            # 在异步上下文中调用同步API
            loop = asyncio.get_event_loop()
            
            # 创建调用函数
            def call_zai_api():
                return self.client.web_search.web_search(**search_params)
            
            response = await loop.run_in_executor(None, call_zai_api)
            
            # 处理查询字符串
            if isinstance(request, dict):
                query = request.get('query', '')
            else:
                query = getattr(request, 'query', '')
            
            return self._parse_results(response, query)
            
        except Exception as e:
            logger.error(f"ZAI API请求失败: {e}")
            return []
    
    def _parse_results(self, response: dict, query: str) -> List[SearchResult]:
        """解析ZAI搜索结果"""
        results = []
        
        # 处理 ZhipuAI 的响应对象
        search_results = None
        
        # 检查是否有 search_result 属性
        if hasattr(response, 'search_result'):
            search_results = response.search_result
        elif isinstance(response, dict):
            if 'search_result' in response:
                search_results = response['search_result']
            elif 'data' in response:
                search_results = response['data']
        
        if not search_results:
            logger.warning("无法找到搜索结果数据")
            return results
        
        if not isinstance(search_results, list):
            logger.warning(f"搜索结果不是列表格式: {type(search_results)}")
            return results
        
        for item in search_results:
            try:
                # 处理 ZhipuAI 的结果对象
                if hasattr(item, 'title'):
                    title = clean_text(item.title or '')
                    url = item.link or ''
                    snippet = clean_text(item.content or '')
                    media = item.media or ''
                    publish_date = getattr(item, 'publish_date', None)
                else:
                    # 如果是字典格式
                    title = clean_text(item.get('title', ''))
                    url = item.get('link', '') or item.get('url', '')
                    snippet = clean_text(item.get('content', '') or item.get('snippet', ''))
                    media = item.get('media', '')
                    publish_date = item.get('publish_date')
                
                if not title or not url:
                    continue
                
                # 计算相关性得分
                score = calculate_relevance_score(query, title, snippet)
                
                # 解析发布时间
                publish_time = None
                if publish_date:
                    publish_time = parse_publish_time(publish_date)
                
                # 创建结果对象
                if SearchResult:
                    result = SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source=SourceType.ZAI if SourceType else 'zai',
                        score=score,
                        publish_time=publish_time,
                        author=media,
                        metadata={
                            'media': media,
                            'publish_date': publish_date,
                            'language': 'zh',
                            'content_size': len(snippet),
                            'search_engine': 'search_pro'
                        }
                    )
                else:
                    # 如果 SearchResult 不可用，创建字典
                    result = {
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'zai',
                        'score': score,
                        'publish_time': publish_time,
                        'author': media,
                        'metadata': {
                            'media': media,
                            'publish_date': publish_date,
                            'language': 'zh',
                            'content_size': len(snippet),
                            'search_engine': 'search_pro'
                        }
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"解析ZAI搜索结果出错: {e}")
                continue
        
        # 按得分排序
        results.sort(key=lambda x: x.score if hasattr(x, 'score') else x.get('score', 0), reverse=True)
        return results
    
    async def get_suggestions(self, query: str) -> List[str]:
        """获取搜索建议（ZAI可能不支持此功能，返回空列表）"""
        # ZAI Search Pro API文档中没有提到搜索建议功能
        # 这里返回空列表，如果将来支持可以实现
        return []