"""
私域搜索引擎
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
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
    
    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """执行私域搜索"""
        results = []
        
        # 并发执行各个私域搜索
        tasks = []
        
        if SourceType.WECHAT in request.sources:
            tasks.append(self.wechat_searcher.search(request))
        
        if SourceType.ZHIHU in request.sources:
            tasks.append(self.zhihu_searcher.search(request))
        
        if tasks:
            search_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in search_results:
                if isinstance(result, list):
                    results.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"私域搜索出错: {result}")
        
        # 按得分排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:request.max_results]


class WeChatSearcher:
    """微信公众号搜索器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', False)
        self.api_url = config.get('api_url', '')
        self.timeout = config.get('timeout', 10)
    
    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """搜索微信公众号文章"""
        if not self.enabled or not self.api_url:
            return []
        
        try:
            # 这里可以接入您已有的微信公众号搜索API
            # 或者搜索本地的微信文章数据库
            results = await self._search_local_wechat_data(request)
            logger.info(f"微信搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"微信搜索出错: {e}")
            return []
    
    async def _search_local_wechat_data(self, request: SearchRequest) -> List[SearchResult]:
        """搜索本地微信数据"""
        results = []
        
        # 这里可以接入您已有的微信数据
        # 例如从数据库或JSON文件中搜索
        try:
            # 示例：从项目中的微信数据搜索
            from pathlib import Path
            import os
            
            # 搜索微信相关的JSON文件
            base_dir = Path(__file__).parent.parent.parent
            wechat_dirs = ['wechat', 'wewe_rss']
            
            for wechat_dir in wechat_dirs:
                wechat_path = base_dir / wechat_dir
                if wechat_path.exists():
                    results.extend(await self._search_wechat_files(wechat_path, request))
            
        except Exception as e:
            logger.error(f"搜索本地微信数据出错: {e}")
        
        return results
    
    async def _search_we3chat_files(self, path: Path, request: SearchRequest) -> List[SearchResult]:
        """搜索微信文件"""
        results = []
        
        try:
            # 搜索JSON文件
            for json_file in path.rglob("*.json"):
                if json_file.stat().st_size > 1024 * 1024:  # 跳过大于1MB的文件
                    continue
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 如果是列表，搜索每个项目
                    if isinstance(data, list):
                        for item in data:
                            result = self._parse_wechat_item(item, request.query)
                            if result:
                                results.append(result)
                    elif isinstance(data, dict):
                        result = self._parse_wechat_item(data, request.query)
                        if result:
                            results.append(result)
                            
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                    
        except Exception as e:
            logger.error(f"搜索微信文件出错: {e}")
        
        return results
    
    def _parse_wechat_item(self, item: Dict[str, Any], query: str) -> Optional[SearchResult]:
        """解析微信文章项目"""
        try:
            title = item.get('title', '')
            content = item.get('content', '') or item.get('digest', '') or item.get('desc', '')
            url = item.get('url', '') or item.get('link', '')
            
            if not title or not any(keyword.lower() in title.lower() or 
                                  keyword.lower() in content.lower() 
                                  for keyword in query.split()):
                return None
            
            title = clean_text(title)
            content = clean_text(content)
            
            if not title:
                return None
            
            score = calculate_relevance_score(query, title, content)
            if score < 0.1:  # 相关性太低
                return None
            
            # 解析发布时间
            publish_time = None
            for time_field in ['publish_time', 'create_time', 'datetime', 'time']:
                if time_field in item:
                    publish_time = parse_publish_time(str(item[time_field]))
                    if publish_time:
                        break
            
            return SearchResult(
                title=title,
                url=url,
                snippet=content[:200] + "..." if len(content) > 200 else content,
                source=SourceType.WECHAT,
                score=score,
                publish_time=publish_time,
                author=item.get('author', '') or item.get('nickname', ''),
                content=content,
                metadata={
                    'account': item.get('account', ''),
                    'biz': item.get('biz', ''),
                    'idx': item.get('idx', ''),
                    'sn': item.get('sn', '')
                }
            )
            
        except Exception as e:
            logger.error(f"解析微信文章出错: {e}")
            return None


class ZhihuSearcher:
    """知乎搜索器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('enabled', False)
        self.api_url = config.get('api_url', '')
        self.timeout = config.get('timeout', 10)
    
    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """搜索知乎内容"""
        if not self.enabled:
            return []
        
        try:
            # 搜索本地知乎数据
            results = await self._search_local_zhihu_data(request)
            logger.info(f"知乎搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"知乎搜索出错: {e}")
            return []
    
    async def _search_local_zhihu_data(self, request: SearchRequest) -> List[SearchResult]:
        """搜索本地知乎数据"""
        results = []
        
        try:
            # 从项目中的知乎数据搜索
            from pathlib import Path
            
            base_dir = Path(__file__).parent.parent.parent
            zhihu_path = base_dir / 'zhihu'
            
            if zhihu_path.exists():
                results.extend(await self._search_zhihu_files(zhihu_path, request))
                
        except Exception as e:
            logger.error(f"搜索本地知乎数据出错: {e}")
        
        return results
    
    async def _search_zhihu_files(self, path: Path, request: SearchRequest) -> List[SearchResult]:
        """搜索知乎文件"""
        results = []
        
        try:
            for json_file in path.glob("*.json"):
                if json_file.stat().st_size > 1024 * 1024:  # 跳过大文件
                    continue
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        for item in data:
                            result = self._parse_zhihu_item(item, request.query)
                            if result:
                                results.append(result)
                    elif isinstance(data, dict):
                        result = self._parse_zhihu_item(data, request.query)
                        if result:
                            results.append(result)
                            
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                    
        except Exception as e:
            logger.error(f"搜索知乎文件出错: {e}")
        
        return results
    
    def _parse_zhihu_item(self, item: Dict[str, Any], query: str) -> Optional[SearchResult]:
        """解析知乎内容项目"""
        try:
            title = item.get('title', '') or item.get('question', '')
            content = item.get('content', '') or item.get('answer', '') or item.get('excerpt', '')
            url = item.get('url', '') or item.get('link', '')
            
            if not title or not any(keyword.lower() in title.lower() or 
                                  keyword.lower() in content.lower() 
                                  for keyword in query.split()):
                return None
            
            title = clean_text(title)
            content = clean_text(content)
            
            if not title:
                return None
            
            score = calculate_relevance_score(query, title, content)
            if score < 0.1:
                return None
            
            return SearchResult(
                title=title,
                url=url,
                snippet=content[:200] + "..." if len(content) > 200 else content,
                source=SourceType.ZHIHU,
                score=score,
                author=item.get('author', '') or item.get('author_name', ''),
                content=content,
                metadata={
                    'answer_id': item.get('answer_id', ''),
                    'question_id': item.get('question_id', ''),
                    'vote_count': item.get('vote_count', 0),
                    'comment_count': item.get('comment_count', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"解析知乎内容出错: {e}")
            return None 