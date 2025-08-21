"""
Search Agent 工具层

提供搜索、内容分析、数据处理等工具
"""

import re
import asyncio
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import Counter
from loguru import logger

from ..models import SearchResult, SourceType
from ..llm_enhancer import LLMEnhancer


class SearchTools:
    """搜索工具集"""
    
    def __init__(self, search_orchestrator):
        self.search_orchestrator = search_orchestrator
    
    async def multi_source_search(self, query: str, sources: List[SourceType], 
                                max_results: int = 10) -> List[SearchResult]:
        """多源搜索"""
        from ..models import SearchRequest
        
        request = SearchRequest(
            query=query,
            max_results=max_results,
            sources=sources,
            include_content=True,
        )
        
        response = await self.search_orchestrator.search(request)
        return response.results
    
    async def parallel_query_search(self, queries: List[str], sources: List[SourceType],
                                  max_results_per_query: int = 5) -> Dict[str, List[SearchResult]]:
        """并行多查询搜索"""
        tasks = []
        for query in queries:
            task = self.multi_source_search(query, sources, max_results_per_query)
            tasks.append((query, task))
        
        results = {}
        completed_tasks = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for (query, _), result in zip(tasks, completed_tasks):
            if isinstance(result, list):
                results[query] = result
            else:
                logger.warning(f"查询失败: {query}, 错误: {result}")
                results[query] = []
        
        return results
    
    def expand_query(self, original_query: str, expansion_type: str = "synonyms") -> List[str]:
        """查询扩展"""
        expanded_queries = [original_query]
        
        if expansion_type == "synonyms":
            # 添加同义词扩展
            expanded_queries.extend(self._add_synonyms(original_query))
        elif expansion_type == "related":
            # 添加相关词扩展
            expanded_queries.extend(self._add_related_terms(original_query))
        elif expansion_type == "specific":
            # 添加具体化扩展
            expanded_queries.extend(self._add_specific_terms(original_query))
        
        return expanded_queries[:5]  # 最多返回5个扩展查询
    
    def _add_synonyms(self, query: str) -> List[str]:
        """添加同义词"""
        # 简单的同义词映射，实际应用中可以使用词典或模型
        synonym_map = {
            "人工智能": ["AI", "机器学习", "深度学习"],
            "教程": ["指南", "学习", "入门"],
            "应用": ["使用", "实践", "案例"],
            "方法": ["技巧", "策略", "方式"],
        }
        
        synonyms = []
        for word, syns in synonym_map.items():
            if word in query:
                for syn in syns:
                    synonyms.append(query.replace(word, syn))
        
        return synonyms
    
    def _add_related_terms(self, query: str) -> List[str]:
        """添加相关词"""
        related_terms = {
            "人工智能": ["神经网络", "算法", "数据科学"],
            "编程": ["开发", "代码", "软件"],
            "教育": ["学习", "培训", "课程"],
        }
        
        related = []
        for word, terms in related_terms.items():
            if word in query:
                for term in terms:
                    related.append(f"{query} {term}")
        
        return related
    
    def _add_specific_terms(self, query: str) -> List[str]:
        """添加具体化词汇"""
        specific_terms = ["详细", "实例", "案例", "教程", "指南"]
        return [f"{query} {term}" for term in specific_terms[:2]]


class ContentAnalysisTools:
    """内容分析工具集"""
    
    def __init__(self, llm_enhancer: Optional[LLMEnhancer] = None):
        self.llm_enhancer = llm_enhancer
    
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """提取关键短语"""
        # 简单的关键短语提取
        # 移除标点符号，分割成词
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 过滤停用词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '了', '也', '就', '都', '要', '可以', '这', '那', '一个', '一些'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 统计词频
        word_freq = Counter(filtered_words)
        
        # 返回最频繁的词作为关键短语
        return [word for word, _ in word_freq.most_common(max_phrases)]
    
    def calculate_content_similarity(self, text1: str, text2: str) -> float:
        """计算内容相似度"""
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """提取实体（简单版本）"""
        entities = {
            "organizations": [],
            "locations": [],
            "persons": [],
            "technologies": [],
        }
        
        # 简单的实体识别模式
        patterns = {
            "organizations": [r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:公司|集团|企业|组织))\b'],
            "locations": [r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:市|省|国|区|县))\b'],
            "technologies": [r'\b(?:AI|人工智能|机器学习|深度学习|Python|Java|JavaScript|React|Vue)\b'],
        }
        
        for entity_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, text)
                entities[entity_type].extend(matches)
        
        return entities
    
    async def analyze_content_quality(self, results: List[SearchResult]) -> Dict[str, Any]:
        """分析内容质量"""
        if not results:
            return {"quality_score": 0.0, "analysis": "无内容可分析"}
        
        quality_metrics = {
            "total_results": len(results),
            "avg_content_length": 0,
            "has_content_ratio": 0,
            "unique_sources": 0,
            "quality_score": 0.0,
        }
        
        # 计算基础指标
        content_lengths = []
        has_content_count = 0
        sources = set()
        
        for result in results:
            if result.content:
                content_lengths.append(len(result.content))
                has_content_count += 1
            sources.add(result.source.value if hasattr(result.source, 'value') else str(result.source))
        
        if content_lengths:
            quality_metrics["avg_content_length"] = sum(content_lengths) / len(content_lengths)
        
        quality_metrics["has_content_ratio"] = has_content_count / len(results)
        quality_metrics["unique_sources"] = len(sources)
        
        # 计算综合质量分数
        quality_score = 0.0
        quality_score += min(quality_metrics["has_content_ratio"], 1.0) * 0.4  # 内容完整性
        quality_score += min(quality_metrics["avg_content_length"] / 1000, 1.0) * 0.3  # 内容丰富度
        quality_score += min(quality_metrics["unique_sources"] / 3, 1.0) * 0.3  # 来源多样性
        
        quality_metrics["quality_score"] = quality_score
        
        # 生成分析报告
        if quality_score >= 0.8:
            analysis = "内容质量优秀，信息丰富且来源多样"
        elif quality_score >= 0.6:
            analysis = "内容质量良好，信息较为完整"
        elif quality_score >= 0.4:
            analysis = "内容质量一般，可能需要补充信息"
        else:
            analysis = "内容质量较差，建议优化搜索策略"
        
        quality_metrics["analysis"] = analysis
        
        return quality_metrics
    
    async def generate_content_summary(self, results: List[SearchResult], 
                                     query: str) -> Optional[str]:
        """生成内容摘要"""
        if not results or not self.llm_enhancer or not self.llm_enhancer.is_available():
            return None
        
        try:
            summary, _, _ = await self.llm_enhancer.enhance(
                results[:10],  # 最多分析10个结果
                query,
                {
                    "llm_summary": True,
                    "llm_tags": False,
                    "llm_per_result": False,
                    "language": "zh",
                }
            )
            return summary
        except Exception as e:
            logger.warning(f"生成内容摘要失败: {e}")
            return None


class DataProcessingTools:
    """数据处理工具集"""
    
    def __init__(self):
        pass
    
    def deduplicate_results(self, results: List[SearchResult], 
                          method: str = "url") -> List[SearchResult]:
        """结果去重"""
        if method == "url":
            return self._deduplicate_by_url(results)
        elif method == "content":
            return self._deduplicate_by_content(results)
        elif method == "title":
            return self._deduplicate_by_title(results)
        else:
            return results
    
    def _deduplicate_by_url(self, results: List[SearchResult]) -> List[SearchResult]:
        """基于URL去重"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results
    
    def _deduplicate_by_content(self, results: List[SearchResult]) -> List[SearchResult]:
        """基于内容相似度去重"""
        unique_results = []
        
        for result in results:
            is_duplicate = False
            result_content = result.content or result.snippet or ""
            
            for existing in unique_results:
                existing_content = existing.content or existing.snippet or ""
                similarity = self._calculate_text_similarity(result_content, existing_content)
                
                if similarity > 0.8:  # 相似度阈值
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(result)
        
        return unique_results
    
    def _deduplicate_by_title(self, results: List[SearchResult]) -> List[SearchResult]:
        """基于标题去重"""
        seen_titles = set()
        unique_results = []
        
        for result in results:
            title_normalized = result.title.lower().strip()
            if title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique_results.append(result)
        
        return unique_results
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def rank_results(self, results: List[SearchResult], query: str, 
                    ranking_method: str = "hybrid") -> List[SearchResult]:
        """结果排序"""
        if ranking_method == "score":
            return sorted(results, key=lambda x: x.score, reverse=True)
        elif ranking_method == "relevance":
            return self._rank_by_relevance(results, query)
        elif ranking_method == "freshness":
            return self._rank_by_freshness(results)
        elif ranking_method == "hybrid":
            return self._rank_by_hybrid(results, query)
        else:
            return results
    
    def _rank_by_relevance(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """基于相关性排序"""
        query_words = set(query.lower().split())
        
        def relevance_score(result):
            text = f"{result.title} {result.snippet}".lower()
            text_words = set(text.split())
            
            if not query_words or not text_words:
                return 0.0
            
            intersection = query_words.intersection(text_words)
            return len(intersection) / len(query_words)
        
        return sorted(results, key=relevance_score, reverse=True)
    
    def _rank_by_freshness(self, results: List[SearchResult]) -> List[SearchResult]:
        """基于时效性排序"""
        # 简单实现：有发布时间的排在前面
        def freshness_score(result):
            if result.publish_time:
                return 1.0
            return 0.0
        
        return sorted(results, key=freshness_score, reverse=True)
    
    def _rank_by_hybrid(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """混合排序"""
        query_words = set(query.lower().split())
        
        def hybrid_score(result):
            # 基础分数
            base_score = result.score
            
            # 相关性分数
            text = f"{result.title} {result.snippet}".lower()
            text_words = set(text.split())
            relevance = 0.0
            if query_words and text_words:
                intersection = query_words.intersection(text_words)
                relevance = len(intersection) / len(query_words)
            
            # 内容完整性分数
            content_score = 1.0 if result.content else 0.5
            
            # 时效性分数
            freshness_score = 1.0 if result.publish_time else 0.8
            
            # 综合分数
            return (base_score * 0.4 + relevance * 0.3 + 
                   content_score * 0.2 + freshness_score * 0.1)
        
        return sorted(results, key=hybrid_score, reverse=True)
    
    def filter_results(self, results: List[SearchResult], 
                      filters: Dict[str, Any]) -> List[SearchResult]:
        """结果过滤"""
        filtered_results = results
        
        # 按来源过滤
        if "sources" in filters:
            allowed_sources = filters["sources"]
            filtered_results = [r for r in filtered_results 
                              if r.source in allowed_sources]
        
        # 按分数过滤
        if "min_score" in filters:
            min_score = filters["min_score"]
            filtered_results = [r for r in filtered_results 
                              if r.score >= min_score]
        
        # 按内容长度过滤
        if "min_content_length" in filters:
            min_length = filters["min_content_length"]
            filtered_results = [r for r in filtered_results 
                              if r.content and len(r.content) >= min_length]
        
        # 按关键词过滤
        if "required_keywords" in filters:
            keywords = filters["required_keywords"]
            filtered_results = [r for r in filtered_results 
                              if self._contains_keywords(r, keywords)]
        
        return filtered_results
    
    def _contains_keywords(self, result: SearchResult, keywords: List[str]) -> bool:
        """检查结果是否包含关键词"""
        text = f"{result.title} {result.snippet} {result.content or ''}".lower()
        return any(keyword.lower() in text for keyword in keywords)
    
    def aggregate_results(self, results_by_source: Dict[str, List[SearchResult]],
                         aggregation_method: str = "merge") -> List[SearchResult]:
        """聚合多源结果"""
        if aggregation_method == "merge":
            # 简单合并
            all_results = []
            for results in results_by_source.values():
                all_results.extend(results)
            return all_results
        
        elif aggregation_method == "weighted":
            # 加权合并（不同来源有不同权重）
            source_weights = {
                "zai": 1.0,
                "bing": 0.8,
                "wechat": 0.9,
                "zhihu": 0.7,
            }
            
            all_results = []
            for source, results in results_by_source.items():
                weight = source_weights.get(source, 0.5)
                for result in results:
                    result.score *= weight
                    all_results.append(result)
            
            return all_results
        
        else:
            return []
