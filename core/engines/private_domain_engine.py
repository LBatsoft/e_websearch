"""
私域搜索引擎
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from loguru import logger

from core.engines.base_engine import BaseSearchEngine
from abc import ABC, abstractmethod
from config import PRIVATE_DOMAIN_CONFIG
from core.models import SearchResult, SearchRequest, SourceType
from core.utils import clean_text, calculate_relevance_score, parse_publish_time


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
                data = {'query': request.query}
                headers = {'Content-Type': 'application/json'}
                
                logger.info(f"发送请求到 {self.api_url}, 数据: {data}")
                async with session.post(self.api_url, json=data, headers=headers, timeout=self.timeout) as response:
                    response_text = await response.text()
                    logger.info(f"收到响应: {response.status} - {response_text[:200]}")
                    
                    if response.status >= 400:
                        logger.error(f"API 错误响应: {response.status} - {response_text}")
                        return []
                    
                    try:
                        api_results = await response.json()
                        logger.info(f"解析的 JSON 响应: {str(api_results)[:200]}")
                    except Exception as e:
                        logger.error(f"JSON 解析失败: {e}, 原始响应: {response_text[:200]}")
                        return []
                    
                    # 处理不同的响应格式
                    items = []
                    if isinstance(api_results, dict):
                        # 适配微信API的实际返回结构，优先查找articles键
                        items = api_results.get('articles', []) or api_results.get('data', []) or api_results.get('results', [])
                        logger.info(f"从字典响应中提取到 {len(items)} 个结果")
                    elif isinstance(api_results, list):
                        items = api_results
                        logger.info(f"从列表响应中提取到 {len(items)} 个结果")
                    
                    parsed_results = [
                        self.parse_item(item, request.query)
                        for item in items
                    ]
                    # 过滤掉解析失败的结果 (None)
                    valid_results = [res for res in parsed_results if res]
                    logger.info(f"成功解析 {len(valid_results)}/{len(items)} 个结果")
                    return valid_results

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
            logger.debug(f"开始解析条目: {str(item)[:200]}")
            
            # 适配微信API的实际返回格式
            title = clean_text(item.get('title', ''))
            # 优先使用summary，如果没有则使用content_markdown
            content = clean_text(item.get('summary', '') or item.get('content_markdown', '') or item.get('content', '') or item.get('digest', '') or item.get('description', ''))
            url = item.get('link', '') or item.get('url', '')
            
            logger.debug(f"提取的字段 - 标题: {title[:50]}, URL: {url}, 内容长度: {len(content)}")
            
            if not title or not url:
                logger.warning(f"跳过条目：标题或URL为空 - 标题: {title[:30]}, URL: {url[:50]}")
                return None
            
            # 移除基础关键词匹配，让搜索更加灵活
            logger.debug(f"跳过基础关键词匹配检查，直接进行相关性评分")

            score = calculate_relevance_score(query, title, content)
            logger.debug(f"计算得分: {score:.2f} - 标题: {title[:50]}")
            if score < 0.1:
                logger.debug(f"跳过条目：得分过低 ({score:.2f}) - 标题: {title[:50]}")
                return None
            
            # 处理发布时间
            publish_time_str = (
                item.get('publish_time') or 
                item.get('create_time') or 
                item.get('publishTime') or 
                item.get('createTime')
            )
            publish_time = parse_publish_time(str(publish_time_str)) if publish_time_str else None

            # 处理作者信息 - 适配微信API的account字段
            author = (
                item.get('account', '') or  # 直接使用account字段
                item.get('author') or 
                item.get('nickname') or 
                item.get('authorName') or 
                item.get('account', {}).get('name')
            )

            # 处理元数据 - 适配微信API的account字段
            metadata = {
                'account': item.get('account', ''),  # 直接使用account字段
                'platform': item.get('platform', 'wechat'),
                'likes': item.get('likes', 0),
                'reads': item.get('reads', 0)
            }

            # 为snippet创建更合适的预览内容
            # 优先使用summary作为snippet，如果没有则截取content的前200字符
            snippet_content = item.get('summary', '') or content[:50]
            
            return SearchResult(
                title=title,
                url=url,
                snippet=snippet_content,
                source=self.source_type,
                score=score,
                publish_time=publish_time,
                author=author,
                content=content,
                metadata=metadata
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
                
            # 移除基础关键词匹配，让搜索更加灵活

            score = calculate_relevance_score(query, title, content)
            if score < 0.1:
                return None

            # 为知乎内容创建合适的snippet
            # 优先使用摘要字段，如果没有则截取content的前50字符
            snippet_content = item.get('excerpt', '') or item.get('summary', '') or content[:50]
            
            return SearchResult(
                title=title,
                url=url,
                snippet=snippet_content,
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
