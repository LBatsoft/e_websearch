"""
内容提取器
"""

import asyncio
from typing import List

from loguru import logger

from .models import SearchResult


class ContentExtractor:
    """内容提取器"""

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self._semaphore = None

    async def __aenter__(self):
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 清理信号量
        if self._semaphore:
            # 等待所有任务完成
            await asyncio.sleep(0)
            self._semaphore = None

    async def extract_content_batch(self, results: List[SearchResult]):
        """批量提取内容"""
        if not results:
            return

        logger.info(f"开始提取 {len(results)} 个结果的内容")

        async def extract_single(result: SearchResult):
            async with self._semaphore:
                try:
                    # 这里可以实现实际的内容提取逻辑
                    # 暂时使用摘要作为内容
                    result.content = result.content
                    result.metadata = result.metadata or {}
                    result.metadata["extraction_method"] = "snippet_fallback"
                except Exception as e:
                    logger.error(f"提取内容失败 {result.url}: {e}")
                    result.metadata = result.metadata or {}
                    result.metadata["extraction_error"] = str(e)

        # 并发提取所有内容
        tasks = [extract_single(result) for result in results]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("内容提取完成")
