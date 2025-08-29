"""
搜索结果处理器

实现高级的结果处理功能，包括：
- 智能去重
- 多维度排序
- 质量评估
- 结果聚合
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import time
import re
from urllib.parse import urlparse
from difflib import SequenceMatcher
from loguru import logger

from ...models import SearchResult, SourceType


class DuplicateDetectionMethod(Enum):
    """去重方法"""
    URL = "url"                 # 基于URL
    CONTENT = "content"         # 基于内容
    SEMANTIC = "semantic"       # 基于语义
    HYBRID = "hybrid"          # 混合方法


class RankingMethod(Enum):
    """排序方法"""
    RELEVANCE = "relevance"    # 相关性优先
    FRESHNESS = "freshness"    # 新鲜度优先
    QUALITY = "quality"        # 质量优先
    AUTHORITY = "authority"    # 权威性优先
    HYBRID = "hybrid"         # 混合排序


@dataclass
class ResultQualityMetrics:
    """结果质量指标"""
    content_quality: float = 0.0    # 内容质量分数
    source_authority: float = 0.0   # 来源权威分数
    freshness: float = 0.0          # 新鲜度分数
    relevance: float = 0.0          # 相关性分数
    completeness: float = 0.0       # 完整性分数
    
    def get_overall_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """计算综合得分"""
        if weights is None:
            weights = {
                "content_quality": 0.3,
                "source_authority": 0.2,
                "freshness": 0.1,
                "relevance": 0.3,
                "completeness": 0.1
            }
        
        score = (
            self.content_quality * weights.get("content_quality", 0.0) +
            self.source_authority * weights.get("source_authority", 0.0) +
            self.freshness * weights.get("freshness", 0.0) +
            self.relevance * weights.get("relevance", 0.0) +
            self.completeness * weights.get("completeness", 0.0)
        )
        
        return min(1.0, max(0.0, score))


class ResultProcessor:
    """搜索结果处理器"""
    
    def __init__(self):
        # 源权威性配置
        self.source_authority_scores = {
            "zai": 0.9,      # 专业知识库
            "bing": 0.8,     # 主流搜索引擎
            "wechat": 0.7,   # 社交媒体
            "zhihu": 0.6,    # 问答平台
        }
        
        # 内容质量评估配置
        self.content_quality_weights = {
            "length": 0.3,           # 内容长度权重
            "structure": 0.2,        # 结构完整性权重
            "readability": 0.2,      # 可读性权重
            "information_density": 0.3  # 信息密度权重
        }
        
        # 相似度阈值配置
        self.similarity_thresholds = {
            "url": 0.9,              # URL相似度阈值
            "content": 0.8,          # 内容相似度阈值
            "title": 0.85            # 标题相似度阈值
        }
    
    def process_results(self, results: List[SearchResult], query: str,
                       dedup_method: DuplicateDetectionMethod = DuplicateDetectionMethod.HYBRID,
                       ranking_method: RankingMethod = RankingMethod.HYBRID,
                       ranking_weights: Optional[Dict[str, float]] = None) -> List[SearchResult]:
        """处理搜索结果"""
        if not results:
            return []
        
        # 1. 质量评估
        results_with_metrics = self._evaluate_results_quality(results, query)
        
        # 2. 去重
        unique_results = self._deduplicate_results(
            results_with_metrics, dedup_method
        )
        
        # 3. 排序
        sorted_results = self._rank_results(
            unique_results, ranking_method, ranking_weights
        )
        
        return sorted_results
    
    def _evaluate_results_quality(self, results: List[SearchResult], 
                                query: str) -> List[SearchResult]:
        """评估结果质量"""
        for result in results:
            if not hasattr(result, 'quality_metrics'):
                result.quality_metrics = ResultQualityMetrics()
            
            # 1. 评估内容质量
            result.quality_metrics.content_quality = self._evaluate_content_quality(result)
            
            # 2. 评估来源权威性
            result.quality_metrics.source_authority = self._evaluate_source_authority(result)
            
            # 3. 评估新鲜度
            result.quality_metrics.freshness = self._evaluate_freshness(result)
            
            # 4. 评估相关性
            result.quality_metrics.relevance = self._evaluate_relevance(result, query)
            
            # 5. 评估完整性
            result.quality_metrics.completeness = self._evaluate_completeness(result)
        
        return results
    
    def _evaluate_content_quality(self, result: SearchResult) -> float:
        """评估内容质量"""
        if not result.content:
            return 0.0
        
        scores = {}
        
        # 1. 内容长度评分
        content_length = len(result.content)
        scores["length"] = min(1.0, content_length / 2000)  # 假设2000字为理想长度
        
        # 2. 结构完整性评分
        structure_score = 0.0
        if result.title:
            structure_score += 0.3
        if result.snippet:
            structure_score += 0.3
        if result.content:
            structure_score += 0.4
        scores["structure"] = structure_score
        
        # 3. 可读性评分
        readability_score = self._calculate_readability_score(result.content)
        scores["readability"] = readability_score
        
        # 4. 信息密度评分
        density_score = self._calculate_information_density(result.content)
        scores["information_density"] = density_score
        
        # 计算加权平均分
        final_score = sum(
            score * self.content_quality_weights[metric]
            for metric, score in scores.items()
        )
        
        return min(1.0, max(0.0, final_score))
    
    def _evaluate_source_authority(self, result: SearchResult) -> float:
        """评估来源权威性"""
        source_name = result.source.value if hasattr(result.source, 'value') else str(result.source)
        source_name = source_name.lower()
        
        # 基础权威分数
        base_score = self.source_authority_scores.get(source_name, 0.5)
        
        # URL权威性加成
        url_authority_bonus = self._calculate_url_authority(result.url)
        
        # 综合评分
        final_score = base_score * 0.7 + url_authority_bonus * 0.3
        return min(1.0, max(0.0, final_score))
    
    def _evaluate_freshness(self, result: SearchResult) -> float:
        """评估内容新鲜度"""
        if not hasattr(result, 'publish_time') or not result.publish_time:
            return 0.5  # 默认中等新鲜度
        
        # 计算内容年龄（天）
        content_age_days = (time.time() - result.publish_time) / (24 * 3600)
        
        # 基于内容年龄计算新鲜度分数
        if content_age_days <= 1:  # 1天内
            return 1.0
        elif content_age_days <= 7:  # 1周内
            return 0.9
        elif content_age_days <= 30:  # 1月内
            return 0.8
        elif content_age_days <= 90:  # 3月内
            return 0.6
        elif content_age_days <= 365:  # 1年内
            return 0.4
        else:
            return 0.2
    
    def _evaluate_relevance(self, result: SearchResult, query: str) -> float:
        """评估相关性"""
        if not query:
            return 0.0
        
        scores = []
        
        # 1. 标题相关性
        if result.title:
            title_relevance = self._calculate_text_similarity(query, result.title)
            scores.append(title_relevance * 0.4)  # 标题权重0.4
        
        # 2. 摘要相关性
        if result.snippet:
            snippet_relevance = self._calculate_text_similarity(query, result.snippet)
            scores.append(snippet_relevance * 0.3)  # 摘要权重0.3
        
        # 3. 内容相关性
        if result.content:
            # 取内容前500字计算相关性
            content_sample = result.content[:500]
            content_relevance = self._calculate_text_similarity(query, content_sample)
            scores.append(content_relevance * 0.3)  # 内容权重0.3
        
        # 如果有原始分数，考虑进去
        if hasattr(result, 'score'):
            scores.append(result.score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _evaluate_completeness(self, result: SearchResult) -> float:
        """评估完整性"""
        scores = []
        
        # 1. 基础字段完整性
        if result.title:
            scores.append(0.2)
        if result.snippet:
            scores.append(0.2)
        if result.url:
            scores.append(0.1)
        
        # 2. 内容完整性
        if result.content:
            content_length = len(result.content)
            content_score = min(1.0, content_length / 1000) * 0.3
            scores.append(content_score)
        
        # 3. 元数据完整性
        if hasattr(result, 'metadata') and result.metadata:
            scores.append(0.1)
        if hasattr(result, 'publish_time') and result.publish_time:
            scores.append(0.1)
        
        return sum(scores)
    
    def _deduplicate_results(self, results: List[SearchResult],
                           method: DuplicateDetectionMethod) -> List[SearchResult]:
        """去重处理"""
        if not results:
            return []
        
        if method == DuplicateDetectionMethod.URL:
            return self._deduplicate_by_url(results)
        elif method == DuplicateDetectionMethod.CONTENT:
            return self._deduplicate_by_content(results)
        elif method == DuplicateDetectionMethod.SEMANTIC:
            return self._deduplicate_by_semantic(results)
        else:  # HYBRID
            # 先用URL去重，再用内容去重
            url_deduped = self._deduplicate_by_url(results)
            return self._deduplicate_by_content(url_deduped)
    
    def _deduplicate_by_url(self, results: List[SearchResult]) -> List[SearchResult]:
        """基于URL去重"""
        unique_results = []
        seen_urls = set()
        
        for result in results:
            normalized_url = self._normalize_url(result.url)
            if normalized_url not in seen_urls:
                unique_results.append(result)
                seen_urls.add(normalized_url)
            else:
                # 如果遇到重复URL，保留质量较高的版本
                for existing in unique_results:
                    if self._normalize_url(existing.url) == normalized_url:
                        if (hasattr(result, 'quality_metrics') and 
                            hasattr(existing, 'quality_metrics')):
                            if (result.quality_metrics.get_overall_score() > 
                                existing.quality_metrics.get_overall_score()):
                                unique_results.remove(existing)
                                unique_results.append(result)
                        break
        
        return unique_results
    
    def _deduplicate_by_content(self, results: List[SearchResult]) -> List[SearchResult]:
        """基于内容去重"""
        unique_results = []
        
        for result in results:
            is_duplicate = False
            result_content = f"{result.title} {result.snippet}"
            
            for existing in unique_results:
                existing_content = f"{existing.title} {existing.snippet}"
                similarity = self._calculate_text_similarity(result_content, existing_content)
                
                if similarity > self.similarity_thresholds["content"]:
                    is_duplicate = True
                    # 保留质量较高的版本
                    if (hasattr(result, 'quality_metrics') and 
                        hasattr(existing, 'quality_metrics')):
                        if (result.quality_metrics.get_overall_score() > 
                            existing.quality_metrics.get_overall_score()):
                            unique_results.remove(existing)
                            unique_results.append(result)
                    break
            
            if not is_duplicate:
                unique_results.append(result)
        
        return unique_results
    
    def _deduplicate_by_semantic(self, results: List[SearchResult]) -> List[SearchResult]:
        """基于语义去重（需要实现更复杂的语义相似度计算）"""
        # TODO: 实现基于语义的去重
        return self._deduplicate_by_content(results)
    
    def _rank_results(self, results: List[SearchResult],
                     method: RankingMethod,
                     weights: Optional[Dict[str, float]] = None) -> List[SearchResult]:
        """结果排序"""
        if not results:
            return []
        
        if weights is None:
            weights = {
                "relevance": 0.3,
                "quality": 0.3,
                "freshness": 0.2,
                "authority": 0.2
            }
        
        for result in results:
            if not hasattr(result, 'ranking_score'):
                result.ranking_score = 0.0
            
            metrics = result.quality_metrics
            
            if method == RankingMethod.RELEVANCE:
                result.ranking_score = metrics.relevance
            elif method == RankingMethod.FRESHNESS:
                result.ranking_score = metrics.freshness
            elif method == RankingMethod.QUALITY:
                result.ranking_score = metrics.content_quality
            elif method == RankingMethod.AUTHORITY:
                result.ranking_score = metrics.source_authority
            else:  # HYBRID
                result.ranking_score = (
                    metrics.relevance * weights.get("relevance", 0.0) +
                    metrics.content_quality * weights.get("quality", 0.0) +
                    metrics.freshness * weights.get("freshness", 0.0) +
                    metrics.source_authority * weights.get("authority", 0.0)
                )
        
        # 排序
        results.sort(key=lambda x: x.ranking_score, reverse=True)
        return results
    
    def _normalize_url(self, url: str) -> str:
        """标准化URL"""
        if not url:
            return ""
        
        # 解析URL
        parsed = urlparse(url)
        
        # 移除www前缀
        netloc = parsed.netloc.replace("www.", "")
        
        # 移除URL参数
        path = parsed.path
        if path.endswith("/"):
            path = path[:-1]
        
        return f"{parsed.scheme}://{netloc}{path}"
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 使用序列匹配算法计算相似度
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _calculate_readability_score(self, text: str) -> float:
        """计算可读性分数"""
        if not text:
            return 0.0
        
        # 简单的可读性评估
        sentences = len(re.split(r'[。！？!?.]', text))
        words = len(text)
        
        if sentences == 0:
            return 0.0
        
        # 计算平均句子长度
        avg_sentence_length = words / sentences
        
        # 基于平均句子长度评分（假设理想长度为15-25个字）
        if 15 <= avg_sentence_length <= 25:
            return 1.0
        elif avg_sentence_length < 15:
            return avg_sentence_length / 15
        else:
            return 25 / avg_sentence_length
    
    def _calculate_information_density(self, text: str) -> float:
        """计算信息密度分数"""
        if not text:
            return 0.0
        
        # 1. 计算标点符号比例
        punctuation_ratio = len(re.findall(r'[。，、：；！？""]', text)) / len(text)
        
        # 2. 计算数字和英文比例
        number_ratio = len(re.findall(r'\d', text)) / len(text)
        english_ratio = len(re.findall(r'[a-zA-Z]', text)) / len(text)
        
        # 3. 计算重复词比例
        words = text.split()
        unique_words = len(set(words))
        word_diversity = unique_words / len(words) if words else 0
        
        # 4. 综合评分
        density_score = (
            (1 - punctuation_ratio) * 0.3 +  # 标点符号比例越低越好
            (number_ratio + english_ratio) * 0.3 +  # 数字和英文比例适中
            word_diversity * 0.4  # 词汇多样性越高越好
        )
        
        return min(1.0, max(0.0, density_score))
    
    def _calculate_url_authority(self, url: str) -> float:
        """计算URL权威性分数"""
        if not url:
            return 0.0
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # 权威域名后缀加分
        authority_score = 0.5  # 基础分
        
        if domain.endswith(('.gov', '.edu')):
            authority_score += 0.4
        elif domain.endswith(('.org', '.net')):
            authority_score += 0.2
        elif domain.endswith('.com'):
            authority_score += 0.1
        
        # 域名长度适中加分（假设理想长度为5-15个字符）
        domain_length = len(domain)
        if 5 <= domain_length <= 15:
            authority_score += 0.1
        
        # 路径深度适中加分（假设理想深度为1-3层）
        path_depth = len([p for p in parsed.path.split('/') if p])
        if 1 <= path_depth <= 3:
            authority_score += 0.1
        
        return min(1.0, authority_score)
