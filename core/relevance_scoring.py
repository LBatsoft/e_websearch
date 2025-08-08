"""
相关性评分模块，包含 TF-IDF 和向量模型实现
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class BaseScorer(ABC):
    """评分器基类"""

    @abstractmethod
    def calculate_score(self, query: str, title: str, snippet: str) -> float:
        """计算相关性得分"""
        pass


class TfidfScorer(BaseScorer):
    """基于 TF-IDF 的评分器"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer="char",  # 使用字符级分析，适合中文
            ngram_range=(2, 4),  # 使用2-4字符组合
            max_features=10000,
            # 移除英文停用词，因为处理中文文本
            stop_words=None,
        )
        self._vectors_cache: Dict[str, np.ndarray] = {}
        self._is_fitted = False
        self._all_texts = []

    def _get_vector(self, text: str) -> np.ndarray:
        """获取文本的 TF-IDF 向量"""
        if text in self._vectors_cache:
            return self._vectors_cache[text]

        try:
            # 如果是第一次调用，先拟合向量器
            if not self._is_fitted:
                # 收集所有文本用于拟合
                self._all_texts.append(text)
                # 暂时返回零向量，稍后会重新计算
                self._vectors_cache[text] = np.zeros((1, self.vectorizer.max_features))
                return self._vectors_cache[text]
            else:
                # 向量器已经拟合，直接转换
                vector = self.vectorizer.transform([text]).toarray()
                self._vectors_cache[text] = vector
                return vector
        except Exception as e:
            logger.error(f"TF-IDF向量化失败: {str(e)}")
            return np.zeros((1, self.vectorizer.max_features))

    def _fit_vectorizer(self):
        """拟合向量器"""
        if not self._is_fitted and self._all_texts:
            try:
                # 拟合向量器
                self.vectorizer.fit(self._all_texts)
                self._is_fitted = True

                # 重新计算所有缓存的向量
                for text in self._all_texts:
                    if text in self._vectors_cache:
                        vector = self.vectorizer.transform([text]).toarray()
                        self._vectors_cache[text] = vector
            except Exception as e:
                logger.error(f"拟合TF-IDF向量器失败: {str(e)}")

    def calculate_score(self, query: str, title: str, snippet: str) -> float:
        """计算相关性得分

        Args:
            query: 查询词
            title: 标题
            snippet: 摘要

        Returns:
            float: 相关性得分 (0-1)
        """
        # 收集所有文本用于拟合
        if not self._is_fitted:
            self._all_texts.extend([query, title, snippet])

        # 获取向量表示
        query_vector = self._get_vector(query)
        title_vector = self._get_vector(title)
        snippet_vector = self._get_vector(snippet)

        # 如果向量器还没拟合，先拟合
        if not self._is_fitted:
            self._fit_vectorizer()
            # 重新获取向量
            query_vector = self._get_vector(query)
            title_vector = self._get_vector(title)
            snippet_vector = self._get_vector(snippet)

        # 计算余弦相似度
        title_sim = cosine_similarity(query_vector, title_vector)[0][0]
        snippet_sim = cosine_similarity(query_vector, snippet_vector)[0][0]

        # 标题权重更高
        score = 0.7 * title_sim + 0.3 * snippet_sim

        return float(min(max(score, 0.0), 1.0))


class VectorScorer(BaseScorer):
    """基于预训练语言模型的向量评分器"""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """初始化向量评分器

        Args:
            model_name: 预训练模型名称，默认使用支持多语言的轻量级模型
        """
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"加载向量模型失败: {str(e)}")
            self.model = None

        self._vectors_cache: Dict[str, np.ndarray] = {}

    def _get_vector(self, text: str) -> Optional[np.ndarray]:
        """获取文本的向量表示"""
        if not self.model:
            return None

        if text in self._vectors_cache:
            return self._vectors_cache[text]

        try:
            vector = self.model.encode([text], convert_to_tensor=False)[0]
            self._vectors_cache[text] = vector
            return vector
        except Exception as e:
            logger.error(f"文本向量化失败: {str(e)}")
            return None

    def calculate_score(self, query: str, title: str, snippet: str) -> float:
        """计算相关性得分

        使用预训练语言模型将文本转换为向量，然后计算余弦相似度

        Args:
            query: 查询词
            title: 标题
            snippet: 摘要

        Returns:
            float: 相关性得分 (0-1)
        """
        if not self.model:
            return 0.0

        # 获取向量表示
        query_vector = self._get_vector(query)
        title_vector = self._get_vector(title)
        snippet_vector = self._get_vector(snippet)

        if query_vector is None or title_vector is None or snippet_vector is None:
            return 0.0

        # 计算余弦相似度
        title_sim = cosine_similarity([query_vector], [title_vector])[0][0]
        snippet_sim = cosine_similarity([query_vector], [snippet_vector])[0][0]

        # 标题权重更高
        score = 0.7 * title_sim + 0.3 * snippet_sim

        return float(min(max(score, 0.0), 1.0))


class HybridScorer(BaseScorer):
    """混合评分器，结合多种评分方法"""

    def __init__(self):
        self.tfidf_scorer = TfidfScorer()
        self.vector_scorer = VectorScorer()

    def calculate_score(self, query: str, title: str, snippet: str) -> float:
        """计算混合相关性得分

        结合 TF-IDF 和向量模型的评分结果，取加权平均

        Args:
            query: 查询词
            title: 标题
            snippet: 摘要

        Returns:
            float: 相关性得分 (0-1)
        """
        tfidf_score = self.tfidf_scorer.calculate_score(query, title, snippet)
        vector_score = self.vector_scorer.calculate_score(query, title, snippet)

        # 向量模型权重更高，因为它能更好地理解语义
        score = 0.3 * tfidf_score + 0.7 * vector_score

        return float(min(max(score, 0.0), 1.0))
