"""
主搜索协调器 - 协调整个搜索流程
"""

import asyncio
import time
from typing import List, Dict
from loguru import logger

from core.models import SearchRequest, SearchResponse, SearchResult, SourceType
from core.engines import BingSearchEngine, ZaiSearchEngine, PrivateDomainEngine
from core.content_extractor import ContentExtractor
from core.result_aggregator import ResultAggregator
from core.cache_manager import InMemoryCacheManager, RedisCacheManager, BaseCacheManager
from core.utils import generate_cache_key, setup_logging
from core.relevance_scoring import HybridScorer
from config import CACHE_TYPE, CACHE_CONFIG


class SearchOrchestrator:
    """主搜索协调器"""
    
    def __init__(self):
        # 初始化日志
        setup_logging()
        
        # 初始化各个组件
        self.bing_engine = BingSearchEngine() if BingSearchEngine else None
        self.zai_engine = ZaiSearchEngine() if ZaiSearchEngine else None
        self.private_engine = PrivateDomainEngine() if PrivateDomainEngine else None
        self.scorer = HybridScorer()
        self.aggregator = ResultAggregator(self.scorer) if ResultAggregator else None
        self.cache_manager = self._init_cache_manager()
        
        # 引擎映射
        self.engines = {}
        if SourceType and self.bing_engine:
            self.engines[SourceType.BING] = self.bing_engine
        if SourceType and self.zai_engine:
            self.engines[SourceType.ZAI] = self.zai_engine
        if SourceType and self.private_engine:
            self.engines[SourceType.WECHAT] = self.private_engine
            self.engines[SourceType.ZHIHU] = self.private_engine
        
        logger.info("搜索协调器初始化完成")

    def _init_cache_manager(self) -> BaseCacheManager:
        """根据配置初始化缓存管理器"""
        if CACHE_TYPE.lower() == 'redis':
            return RedisCacheManager(CACHE_CONFIG)
        else:
            return InMemoryCacheManager(CACHE_CONFIG)

    async def close(self):
        """关闭并清理资源"""
        logger.info("正在关闭搜索协调器...")
        if self.cache_manager:
            await self.cache_manager.close()

    async def search(self, request: SearchRequest) -> SearchResponse:
        """执行搜索"""
        start_time = time.time()
        
        logger.info(f"开始搜索: '{request.query}', 源: {[s.value for s in request.sources]}")

        # 检查缓存
        cache_key = generate_cache_key(request.query, str(request.sources))
        cached_results = await self.cache_manager.get(cache_key)
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
        await self.cache_manager.set(cache_key, aggregated_results)
        
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
        
        tasks = []
        source_engine_map = {}
        
        for source in request.sources:
            engine = self.engines.get(source)
            if engine and engine.is_available():
                task = engine.search(request)
                tasks.append(task)
                source_engine_map[task] = source
            else:
                logger.warning(f"搜索引擎 for source '{source.value}' is not available.")
        
        if tasks:
            search_results = await asyncio.gather(*tasks, return_exceptions=True)
            for task, result in zip(tasks, search_results):
                source = source_engine_map[task]
                if isinstance(result, list):
                    results_by_source[source] = result
                    logger.info(f"{source.value} 搜索完成，返回 {len(result)} 个结果")
                elif isinstance(result, Exception):
                    logger.error(f"{source.value} 搜索失败: {result}")
                    results_by_source[source] = []
        
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
            if self.zai_engine and self.zai_engine.is_available() and hasattr(self.zai_engine, 'get_suggestions'):
                return await self.zai_engine.get_suggestions(query)
            elif self.bing_engine and self.bing_engine.is_available() and hasattr(self.bing_engine, 'get_suggestions'):
                return await self.bing_engine.get_suggestions(query)
            
            # 提供简单的模拟建议
            return [
                f"{query} 教程",
                f"{query} 原理",
                f"{query} 应用",
            ]
        except Exception as e:
            logger.error(f"获取搜索建议失败: {e}")
            return []

    def get_available_sources(self) -> list:
        """获取可用的搜索源"""
        return [source for source, engine in self.engines.items() if engine.is_available()]

    async def clear_cache(self):
        """清空缓存"""
        if self.cache_manager:
            await self.cache_manager.clear()

    async def health_check(self) -> dict:
        """健康检查"""
        engine_status = {
            source.value: engine.is_available() 
            for source, engine in self.engines.items()
        }

        cache_status = self.cache_manager.enabled if self.cache_manager else False
        status = 'healthy' if all(engine_status.values()) and cache_status else 'degraded'

        return {
            'status': status,
            'engines': engine_status,
            'available_sources': [s.value for s in self.get_available_sources()],
            'cache_enabled': cache_status,
            'cache_type': CACHE_TYPE,
        }

