"""
主搜索协调器 - 协调整个搜索流程
"""

import asyncio
import time
from typing import List, Dict
from loguru import logger

from .models import SearchRequest, SearchResponse, SearchResult, SourceType
from .engines import BingSearchEngine, ZaiSearchEngine, PrivateDomainEngine
from .content_extractor import ContentExtractor
from .result_aggregator import ResultAggregator
from .cache_manager import CacheManager
from .utils import generate_cache_key, setup_logging


class SearchOrchestrator:
    """主搜索协调器"""
    
    def __init__(self):
        # 初始化日志
        setup_logging()
        
        # 初始化各个组件（处理可能为 None 的情况）
        self.bing_engine = BingSearchEngine() if BingSearchEngine else None
        self.zai_engine = ZaiSearchEngine() if ZaiSearchEngine else None
        self.private_engine = PrivateDomainEngine() if PrivateDomainEngine else None
        self.aggregator = ResultAggregator() if ResultAggregator else None
        self.cache_manager = CacheManager() if CacheManager else None
        
        # 引擎映射 - 只添加可用的引擎
        self.engines = {}
        if SourceType and self.bing_engine:
            self.engines[SourceType.BING] = self.bing_engine
        if SourceType and self.zai_engine:
            self.engines[SourceType.ZAI] = self.zai_engine
        if SourceType and self.private_engine:
            self.engines[SourceType.WECHAT] = self.private_engine
            self.engines[SourceType.ZHIHU] = self.private_engine
        
        # 如果没有可用引擎，使用模拟搜索
        if not self.engines:
            logger.warning("没有可用的搜索引擎，将使用模拟搜索")
            self.use_mock_search = True
        else:
            self.use_mock_search = False
        
        logger.info("搜索协调器初始化完成")
    
    async def search(self, request) -> dict:
        """执行搜索"""
        start_time = time.time()
        
        # 处理请求对象（可能是字典或对象）
        if isinstance(request, dict):
            query = request.get('query', '')
            max_results = request.get('max_results', 10)
            sources = request.get('sources', ['zai'])
            include_content = request.get('include_content', False)
        else:
            query = getattr(request, 'query', '')
            max_results = getattr(request, 'max_results', 10)
            sources = getattr(request, 'sources', ['zai']) 
            include_content = getattr(request, 'include_content', False)
        
        logger.info(f"开始搜索: '{query}', 源: {sources}")
        
        # 检查是否有可用的真实搜索引擎
        has_real_engine = False
        if self.zai_engine and hasattr(self.zai_engine, 'is_available') and self.zai_engine.is_available():
            has_real_engine = True
        elif self.bing_engine and hasattr(self.bing_engine, 'is_available') and self.bing_engine.is_available():
            has_real_engine = True
        
        # 如果没有真实引擎可用，使用模拟搜索
        if not has_real_engine or self.use_mock_search:
            return await self._mock_search(query, max_results, sources, start_time)
        
        # 执行真实搜索
        try:
            # 创建搜索请求对象
            search_request = {
                'query': query,
                'max_results': max_results,
                'filters': {}
            }
            
            # 优先使用 ZAI 引擎
            if self.zai_engine and hasattr(self.zai_engine, 'is_available') and self.zai_engine.is_available():
                logger.info("使用 ZAI 搜索引擎")
                search_results = await self.zai_engine.search(search_request)
            elif self.bing_engine and hasattr(self.bing_engine, 'is_available') and self.bing_engine.is_available():
                logger.info("使用 Bing 搜索引擎")
                search_results = await self.bing_engine.search(search_request)
            else:
                logger.warning("没有可用的搜索引擎，使用模拟搜索")
                return await self._mock_search(query, max_results, sources, start_time)
            
            # 处理搜索结果
            if isinstance(search_results, list) and search_results:
                # 转换结果为标准格式
                results_data = []
                for result in search_results:
                    if hasattr(result, 'title'):
                        # 对象格式
                        result_dict = {
                            'title': result.title,
                            'url': result.url,
                            'snippet': result.snippet,
                            'source': result.source.value if hasattr(result.source, 'value') else str(result.source),
                            'score': result.score,
                            'publish_time': result.publish_time,
                            'author': result.author,
                            'content': result.content,
                            'images': result.images,
                            'metadata': result.metadata
                        }
                    else:
                        # 字典格式
                        result_dict = result
                    
                    results_data.append(result_dict)
                
                execution_time = time.time() - start_time
                
                return {
                    'success': True,
                    'results': results_data,
                    'total_count': len(results_data),
                    'query': query,
                    'execution_time': execution_time,
                    'sources_used': sources,
                    'cache_hit': False
                }
            else:
                logger.warning("搜索引擎返回空结果，使用模拟搜索")
                return await self._mock_search(query, max_results, sources, start_time)
                
        except Exception as e:
            logger.error(f"真实搜索失败: {e}")
            return await self._mock_search(query, max_results, sources, start_time)
        
        if cached_results:
            execution_time = time.time() - start_time
            logger.info(f"缓存命中，返回 {len(cached_results)} 个结果")
            
            return SearchResponse(
                results=cached_results[:request.max_results],
                total_count=len(cached_results),
                query=request.query,
                execution_time=execution_time,
                sources_used=request.sources,
                cache_hit=True
            )
        
        # 执行搜索
        results_by_source = await self._search_all_sources(request)
        
        # 聚合结果
        aggregated_results = self.aggregator.aggregate_results(results_by_source, request)
        
        # 提取内容
        if request.include_content and aggregated_results:
            await self._extract_content(aggregated_results)
        
        # 缓存结果
        self.cache_manager.set(cache_key, aggregated_results)
        
        execution_time = time.time() - start_time
        
        # 构建响应
        response = SearchResponse(
            results=aggregated_results,
            total_count=len(aggregated_results),
            query=request.query,
            execution_time=execution_time,
            sources_used=list(results_by_source.keys()),
            cache_hit=False
        )
        
        logger.info(f"搜索完成，耗时 {execution_time:.2f}秒，返回 {len(aggregated_results)} 个结果")
        
        return response
    
    async def _search_all_sources(self, request: SearchRequest) -> Dict[SourceType, List[SearchResult]]:
        """搜索所有源"""
        results_by_source = {}
        
        # 创建搜索任务
        tasks = []
        source_engine_map = {}
        
        for source in request.sources:
            if source == SourceType.BING:
                if self.bing_engine.is_available():
                    task = self.bing_engine.search(request)
                    tasks.append(task)
                    source_engine_map[task] = source
                else:
                    logger.warning("Bing搜索引擎不可用")
            
            elif source == SourceType.ZAI:
                if self.zai_engine.is_available():
                    task = self.zai_engine.search(request)
                    tasks.append(task)
                    source_engine_map[task] = source
                else:
                    logger.warning("ZAI搜索引擎不可用")
            
            elif source in [SourceType.WECHAT, SourceType.ZHIHU]:
                if self.private_engine.is_available():
                    # 为私域搜索创建专门的请求
                    private_request = SearchRequest(
                        query=request.query,
                        max_results=request.max_results,
                        include_content=request.include_content,
                        sources=[source],  # 单独指定源
                        filters=request.filters
                    )
                    task = self.private_engine.search(private_request)
                    tasks.append(task)
                    source_engine_map[task] = source
                else:
                    logger.warning("私域搜索引擎不可用")
        
        # 并发执行搜索
        if tasks:
            try:
                search_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, (task, result) in enumerate(zip(tasks, search_results)):
                    source = source_engine_map[task]
                    
                    if isinstance(result, list):
                        results_by_source[source] = result
                        logger.info(f"{source.value}搜索完成，返回 {len(result)} 个结果")
                    elif isinstance(result, Exception):
                        logger.error(f"{source.value}搜索失败: {result}")
                        results_by_source[source] = []
                    else:
                        results_by_source[source] = []
                        
            except Exception as e:
                logger.error(f"搜索执行出错: {e}")
        
        return results_by_source
    
    async def _extract_content(self, results: List[SearchResult]):
        """提取搜索结果的详细内容"""
        if not results:
            return
        
        logger.info("开始提取详细内容")
        
        try:
            async with ContentExtractor() as extractor:
                await extractor.extract_content_batch(results)
        except Exception as e:
            logger.error(f"内容提取失败: {e}")
    
    async def get_search_suggestions(self, query: str) -> list:
        """获取搜索建议"""
        try:
            # 优先使用 ZAI 引擎，如果不可用则使用 Bing
            if self.zai_engine and hasattr(self.zai_engine, 'is_available') and self.zai_engine.is_available():
                if hasattr(self.zai_engine, 'get_suggestions'):
                    return await self.zai_engine.get_suggestions(query)
            elif self.bing_engine and hasattr(self.bing_engine, 'is_available') and self.bing_engine.is_available():
                if hasattr(self.bing_engine, 'get_suggestions'):
                    return await self.bing_engine.get_suggestions(query)
            
            # 提供简单的模拟建议
            return [
                f"{query} 教程",
                f"{query} 原理",
                f"{query} 应用",
                f"{query} 发展",
                f"{query} 技术"
            ]
        except Exception as e:
            logger.error(f"获取搜索建议失败: {e}")
            return []
    
    def get_available_sources(self) -> list:
        """获取可用的搜索源"""
        available_sources = []
        
        if self.bing_engine and hasattr(self.bing_engine, 'is_available') and self.bing_engine.is_available():
            if SourceType and hasattr(SourceType, 'BING'):
                available_sources.append(SourceType.BING)
            else:
                available_sources.append('bing')
        
        if self.zai_engine and hasattr(self.zai_engine, 'is_available') and self.zai_engine.is_available():
            if SourceType and hasattr(SourceType, 'ZAI'):
                available_sources.append(SourceType.ZAI)
            else:
                available_sources.append('zai')
        
        if self.private_engine and hasattr(self.private_engine, 'is_available') and self.private_engine.is_available():
            if SourceType and hasattr(SourceType, 'WECHAT'):
                available_sources.extend([SourceType.WECHAT, SourceType.ZHIHU])
            else:
                available_sources.extend(['wechat', 'zhihu'])
        
        # 如果没有真实引擎可用，返回模拟源
        if not available_sources:
            available_sources = ['mock']
        
        return available_sources
    
    def get_search_statistics(self, results: list) -> dict:
        """获取搜索统计信息"""
        if self.aggregator and hasattr(self.aggregator, 'get_statistics'):
            return self.aggregator.get_statistics(results)
        return {}
    
    def clear_cache(self):
        """清空缓存"""
        if self.cache_manager and hasattr(self.cache_manager, 'clear'):
            self.cache_manager.clear()
            logger.info("缓存已清空")
        else:
            logger.info("缓存管理器不可用")
    
    def cleanup_expired_cache(self):
        """清理过期缓存"""
        if self.cache_manager and hasattr(self.cache_manager, 'cleanup_expired'):
            self.cache_manager.cleanup_expired()
            logger.info("过期缓存已清理")
        else:
            logger.info("缓存管理器不可用")
    
    async def health_check(self) -> dict:
        """健康检查"""
        health_status = {
            'status': 'healthy',
            'engines': {
                'bing': self.bing_engine.is_available() if self.bing_engine and hasattr(self.bing_engine, 'is_available') else False,
                'zai': self.zai_engine.is_available() if self.zai_engine and hasattr(self.zai_engine, 'is_available') else False,
                'private_domain': self.private_engine.is_available() if self.private_engine and hasattr(self.private_engine, 'is_available') else False
            },
            'available_sources': [str(s) for s in self.get_available_sources()],
            'cache_enabled': self.cache_manager.enabled if self.cache_manager and hasattr(self.cache_manager, 'enabled') else False
        }
        
        # 测试基本搜索功能
        try:
            # 优先使用 ZAI 引擎进行测试
            test_sources = []
            if self.zai_engine.is_available():
                test_sources = [SourceType.ZAI]
            elif self.bing_engine.is_available():
                test_sources = [SourceType.BING]
            
            test_request = SearchRequest(
                query="测试",
                max_results=1,
                include_content=False,
                sources=test_sources
            )
            
            if test_request.sources:
                test_result = await self.search(test_request)
                health_status['last_search_time'] = test_result.execution_time
            else:
                health_status['last_search_time'] = None
                
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['error'] = str(e)
        
        return health_status
    
    async def _mock_search(self, query: str, max_results: int, sources: list, start_time: float) -> dict:
        """模拟搜索（当真实引擎不可用时）"""
        import time
        from datetime import datetime
        
        logger.info(f"执行模拟搜索: '{query}'")
        
        # 生成模拟结果
        mock_results = []
        for i in range(min(max_results, 3)):
            mock_results.append({
                'title': f"关于'{query}'的搜索结果 {i+1}",
                'url': f"https://example.com/result-{i+1}",
                'snippet': f"这是关于'{query}'的第{i+1}个搜索结果的摘要内容。包含了相关信息和详细描述。",
                'source': sources[0] if sources else 'mock',
                'score': 0.9 - i * 0.1,
                'publish_time': datetime.now().isoformat() if i == 0 else None,
                'author': f"作者{i+1}" if i < 2 else None,
                'content': None,
                'images': [],
                'metadata': {
                    'type': 'mock',
                    'engine': 'mock_search'
                }
            })
        
        execution_time = time.time() - start_time
        
        return {
            'success': True,
            'results': mock_results,
            'total_count': len(mock_results),
            'query': query,
            'execution_time': execution_time,
            'sources_used': sources,
            'cache_hit': False
        } 