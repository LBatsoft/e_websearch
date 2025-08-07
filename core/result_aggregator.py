"""
结果聚合器
"""

from typing import List, Dict
from .models import SearchResult, SearchRequest, SourceType


class ResultAggregator:
    """结果聚合器"""
    
    def aggregate_results(self, results_by_source: Dict[SourceType, List[SearchResult]], 
                         request: SearchRequest) -> List[SearchResult]:
        """聚合搜索结果"""
        
        all_results = []
        
        # 合并所有来源的结果
        for source, results in results_by_source.items():
            all_results.extend(results)
        
        # 去重（基于URL）
        seen_urls = set()
        unique_results = []
        
        for result in all_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        # 按得分排序
        unique_results.sort(key=lambda x: x.score, reverse=True)
        
        # 限制结果数量
        return unique_results[:request.max_results]
    
    def get_statistics(self, results: List[SearchResult]) -> Dict:
        """获取统计信息"""
        if not results:
            return {'total': 0, 'by_source': {}}
        
        stats = {
            'total': len(results),
            'by_source': {},
            'avg_score': sum(r.score for r in results) / len(results),
            'max_score': max(r.score for r in results),
            'min_score': min(r.score for r in results)
        }
        
        # 按来源统计
        for result in results:
            source = result.source.value
            if source not in stats['by_source']:
                stats['by_source'][source] = 0
            stats['by_source'][source] += 1
        
        return stats