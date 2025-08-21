"""
高级查询分析器 - 基于机器学习和预训练模型的查询理解

提供多种先进的查询分析方案：
1. 基于BERT的语义理解
2. 基于机器学习的分类模型
3. 基于LLM的深度分析
4. 混合式多模型集成
"""

import asyncio
import json
import pickle
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from loguru import logger

# 尝试导入机器学习库
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.svm import SVC
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn 不可用，将使用基础分析功能")

# 尝试导入transformers
try:
    from transformers import AutoTokenizer, AutoModel, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers 不可用，将使用基础分析功能")

from ..llm_enhancer import LLMEnhancer


@dataclass
class QueryAnalysisResult:
    """查询分析结果"""
    original_query: str
    query_type: str
    complexity: str
    intent: str
    entities: List[str]
    keywords: List[str]
    semantic_features: Optional[np.ndarray] = None
    confidence_scores: Dict[str, float] = None
    requires_multiple_searches: bool = False
    suggested_refinements: List[str] = None
    llm_analysis: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = {}
        if self.suggested_refinements is None:
            self.suggested_refinements = []
        if self.llm_analysis is None:
            self.llm_analysis = {}


class BERTQueryAnalyzer:
    """基于BERT的查询分析器"""
    
    def __init__(self, model_name: str = "bert-base-chinese"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.classifier = None
        self.available = False
        
        if TRANSFORMERS_AVAILABLE:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModel.from_pretrained(model_name)
                self.classifier = pipeline(
                    "text-classification",
                    model=model_name,
                    tokenizer=model_name
                )
                self.available = True
                logger.info(f"BERT查询分析器初始化成功: {model_name}")
            except Exception as e:
                logger.warning(f"BERT模型加载失败: {e}")
    
    def is_available(self) -> bool:
        return self.available
    
    async def encode_query(self, query: str) -> Optional[np.ndarray]:
        """将查询编码为向量表示"""
        if not self.is_available():
            return None
        
        try:
            inputs = self.tokenizer(query, return_tensors="pt", 
                                  padding=True, truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                # 使用[CLS]标记的表示作为查询向量
                query_vector = outputs.last_hidden_state[:, 0, :].numpy()
            
            return query_vector.flatten()
        except Exception as e:
            logger.error(f"查询编码失败: {e}")
            return None
    
    async def classify_intent(self, query: str) -> Dict[str, float]:
        """基于BERT分类查询意图"""
        if not self.is_available():
            return {}
        
        try:
            # 使用预训练的分类器
            result = self.classifier(query)
            
            # 转换为我们的意图类别
            intent_mapping = {
                "POSITIVE": "information_seeking",
                "NEGATIVE": "problem_solving",
                "NEUTRAL": "comparison"
            }
            
            confidence_scores = {}
            for item in result:
                mapped_intent = intent_mapping.get(item["label"], item["label"].lower())
                confidence_scores[mapped_intent] = item["score"]
            
            return confidence_scores
        except Exception as e:
            logger.error(f"意图分类失败: {e}")
            return {}


class MLQueryClassifier:
    """基于机器学习的查询分类器"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.models = {}
        self.vectorizers = {}
        self.available = SKLEARN_AVAILABLE
        
        if self.available:
            self._init_models()
    
    def _init_models(self):
        """初始化机器学习模型"""
        # 查询类型分类器
        self.models['query_type'] = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
            ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        
        # 复杂度分类器
        self.models['complexity'] = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=3000, ngram_range=(1, 2))),
            ('classifier', SVC(kernel='rbf', probability=True, random_state=42))
        ])
        
        # 意图分类器
        self.models['intent'] = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=4000, ngram_range=(1, 3))),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        # 如果有预训练模型，加载它们
        if self.model_path and Path(self.model_path).exists():
            self._load_models()
        else:
            # 使用示例数据训练模型
            self._train_with_sample_data()
    
    def _train_with_sample_data(self):
        """使用示例数据训练模型"""
        # 示例训练数据
        sample_data = {
            'query_type': {
                'queries': [
                    "ChatGPT vs Claude 对比", "Python和Java区别", "iPhone和安卓手机比较",
                    "如何学习机器学习", "Python入门教程", "怎么做红烧肉",
                    "什么是区块链", "人工智能定义", "深度学习含义",
                    "最新AI发展", "2024年科技趋势", "今年最新消息",
                    "详细介绍量子计算", "深入分析股市", "全面了解云计算"
                ],
                'labels': [
                    "comparison", "comparison", "comparison",
                    "tutorial", "tutorial", "tutorial", 
                    "definition", "definition", "definition",
                    "latest", "latest", "latest",
                    "deep_dive", "deep_dive", "deep_dive"
                ]
            },
            'complexity': {
                'queries': [
                    "AI", "机器学习", "Python",
                    "如何学习Python", "机器学习入门教程", "深度学习基础知识",
                    "人工智能在医疗领域的具体应用案例和未来发展前景分析"
                ],
                'labels': [
                    "simple", "simple", "simple",
                    "medium", "medium", "medium",
                    "complex"
                ]
            },
            'intent': {
                'queries': [
                    "如何学习Python", "怎么做蛋糕", "学习方法",
                    "什么是AI", "区块链定义", "深度学习含义",
                    "最新科技新闻", "今年发展趋势", "最近更新",
                    "Python vs Java", "iPhone对比安卓", "比较分析"
                ],
                'labels': [
                    "how_to", "how_to", "how_to",
                    "definition", "definition", "definition",
                    "latest_info", "latest_info", "latest_info",
                    "comparison", "comparison", "comparison"
                ]
            }
        }
        
        # 训练每个模型
        for model_name, data in sample_data.items():
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    data['queries'], data['labels'], 
                    test_size=0.2, random_state=42
                )
                
                self.models[model_name].fit(X_train, y_train)
                
                # 评估模型
                y_pred = self.models[model_name].predict(X_test)
                logger.info(f"{model_name} 模型训练完成")
                
            except Exception as e:
                logger.error(f"{model_name} 模型训练失败: {e}")
    
    def _load_models(self):
        """加载预训练模型"""
        try:
            with open(self.model_path, 'rb') as f:
                saved_models = pickle.load(f)
                self.models.update(saved_models)
            logger.info("预训练模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            self._train_with_sample_data()
    
    def save_models(self, path: str):
        """保存训练好的模型"""
        try:
            with open(path, 'wb') as f:
                pickle.dump(self.models, f)
            logger.info(f"模型保存成功: {path}")
        except Exception as e:
            logger.error(f"模型保存失败: {e}")
    
    def predict_query_type(self, query: str) -> Tuple[str, float]:
        """预测查询类型"""
        if not self.available or 'query_type' not in self.models:
            return "general", 0.5
        
        try:
            prediction = self.models['query_type'].predict([query])[0]
            probabilities = self.models['query_type'].predict_proba([query])[0]
            confidence = max(probabilities)
            return prediction, confidence
        except Exception as e:
            logger.error(f"查询类型预测失败: {e}")
            return "general", 0.5
    
    def predict_complexity(self, query: str) -> Tuple[str, float]:
        """预测查询复杂度"""
        if not self.available or 'complexity' not in self.models:
            return "medium", 0.5
        
        try:
            prediction = self.models['complexity'].predict([query])[0]
            probabilities = self.models['complexity'].predict_proba([query])[0]
            confidence = max(probabilities)
            return prediction, confidence
        except Exception as e:
            logger.error(f"复杂度预测失败: {e}")
            return "medium", 0.5
    
    def predict_intent(self, query: str) -> Tuple[str, float]:
        """预测查询意图"""
        if not self.available or 'intent' not in self.models:
            return "information_seeking", 0.5
        
        try:
            prediction = self.models['intent'].predict([query])[0]
            probabilities = self.models['intent'].predict_proba([query])[0]
            confidence = max(probabilities)
            return prediction, confidence
        except Exception as e:
            logger.error(f"意图预测失败: {e}")
            return "information_seeking", 0.5


class LLMQueryAnalyzer:
    """基于LLM的高级查询分析器"""
    
    def __init__(self, llm_enhancer: Optional[LLMEnhancer] = None):
        self.llm_enhancer = llm_enhancer
    
    def is_available(self) -> bool:
        return self.llm_enhancer and self.llm_enhancer.is_available()
    
    async def analyze_with_cot(self, query: str) -> Dict[str, Any]:
        """使用Chain-of-Thought进行查询分析"""
        if not self.is_available():
            return {}
        
        prompt = f"""
        请使用逐步推理的方式分析以下搜索查询：

        查询: "{query}"

        请按以下步骤进行分析：

        步骤1: 词汇分析
        - 识别关键词和短语
        - 分析词性和语法结构
        - 提取专有名词和实体

        步骤2: 语义理解
        - 理解查询的核心含义
        - 识别隐含的信息需求
        - 分析上下文和背景

        步骤3: 意图推断
        - 判断用户的搜索目的
        - 分析期望的结果类型
        - 评估信息的紧急程度

        步骤4: 复杂度评估
        - 评估查询的复杂程度
        - 判断是否需要多步搜索
        - 预估搜索难度

        步骤5: 策略建议
        - 推荐最佳搜索策略
        - 建议查询优化方案
        - 提出可能的子查询

        请以JSON格式返回分析结果：
        {{
            "step1_lexical": {{
                "keywords": ["关键词1", "关键词2"],
                "entities": ["实体1", "实体2"],
                "pos_tags": ["词性分析"]
            }},
            "step2_semantic": {{
                "core_meaning": "核心含义",
                "implicit_needs": ["隐含需求1", "隐含需求2"],
                "context": "上下文分析"
            }},
            "step3_intent": {{
                "primary_intent": "主要意图",
                "secondary_intents": ["次要意图1", "次要意图2"],
                "result_type": "期望结果类型",
                "urgency": "紧急程度"
            }},
            "step4_complexity": {{
                "complexity_level": "复杂度等级",
                "needs_multi_step": true/false,
                "difficulty_score": 0.8,
                "reasoning": "复杂度判断理由"
            }},
            "step5_strategy": {{
                "recommended_strategy": "推荐策略",
                "query_optimizations": ["优化建议1", "优化建议2"],
                "sub_queries": ["子查询1", "子查询2"]
            }}
        }}
        """
        
        try:
            provider = self.llm_enhancer._select_provider()
            response = await provider.generate(
                [{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            if response:
                # 尝试解析JSON响应
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"raw_response": response}
        except Exception as e:
            logger.error(f"LLM Chain-of-Thought分析失败: {e}")
            return {}
    
    async def analyze_with_few_shot(self, query: str) -> Dict[str, Any]:
        """使用Few-shot学习进行查询分析"""
        if not self.is_available():
            return {}
        
        prompt = f"""
        以下是一些查询分析的示例：

        示例1:
        查询: "ChatGPT vs Claude 对比分析"
        分析: {{
            "query_type": "comparison",
            "complexity": "medium",
            "intent": "comparison",
            "entities": ["ChatGPT", "Claude"],
            "needs_multi_step": true,
            "strategy": "iterative"
        }}

        示例2:
        查询: "Python机器学习入门教程"
        分析: {{
            "query_type": "tutorial",
            "complexity": "medium", 
            "intent": "how_to",
            "entities": ["Python"],
            "needs_multi_step": true,
            "strategy": "iterative"
        }}

        示例3:
        查询: "什么是区块链"
        分析: {{
            "query_type": "definition",
            "complexity": "simple",
            "intent": "definition",
            "entities": [],
            "needs_multi_step": false,
            "strategy": "simple"
        }}

        现在请分析以下查询：
        查询: "{query}"

        请按照相同的格式返回分析结果：
        """
        
        try:
            provider = self.llm_enhancer._select_provider()
            response = await provider.generate(
                [{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            if response:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"LLM Few-shot分析失败: {e}")
            return {}


class HybridQueryAnalyzer:
    """混合式查询分析器 - 集成多种分析方法"""
    
    def __init__(self, llm_enhancer: Optional[LLMEnhancer] = None, 
                 model_path: Optional[str] = None):
        # 初始化各种分析器
        self.bert_analyzer = BERTQueryAnalyzer()
        self.ml_classifier = MLQueryClassifier(model_path)
        self.llm_analyzer = LLMQueryAnalyzer(llm_enhancer)
        
        # 基础规则分析器（作为后备）
        self.rule_patterns = {
            "comparison": [r"对比|比较|vs|versus|区别|差异"],
            "tutorial": [r"教程|如何|怎么|步骤|方法"],
            "definition": [r"什么是|定义|含义|概念"],
            "latest": [r"最新|最近|2024|2023|今年|最新消息"],
            "deep_dive": [r"详细|深入|全面|完整|系统"],
            "multi_aspect": [r"和|与|以及|还有|包括"],
        }
    
    async def analyze_query(self, query: str) -> QueryAnalysisResult:
        """综合分析查询"""
        logger.info(f"开始混合式查询分析: {query}")
        
        # 并行执行多种分析方法
        tasks = []
        
        # 1. 基础规则分析
        rule_analysis = self._rule_based_analysis(query)
        
        # 2. 机器学习分析
        if self.ml_classifier.available:
            tasks.append(self._ml_analysis(query))
        
        # 3. BERT分析
        if self.bert_analyzer.is_available():
            tasks.append(self._bert_analysis(query))
        
        # 4. LLM分析
        if self.llm_analyzer.is_available():
            tasks.append(self._llm_analysis(query))
        
        # 等待所有分析完成
        analysis_results = []
        if tasks:
            analysis_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 融合分析结果
        final_result = self._fuse_analysis_results(
            query, rule_analysis, analysis_results
        )
        
        logger.info(f"混合式分析完成: {query} -> {final_result.query_type}")
        return final_result
    
    def _rule_based_analysis(self, query: str) -> Dict[str, Any]:
        """基于规则的分析"""
        query_lower = query.lower()
        
        # 查询类型分类
        query_type = "general"
        for qtype, patterns in self.rule_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    query_type = qtype
                    break
            if query_type != "general":
                break
        
        # 复杂度评估
        words = query.split()
        if len(words) <= 2:
            complexity = "simple"
        elif len(words) <= 5:
            complexity = "medium"
        else:
            complexity = "complex"
        
        # 实体提取
        entities = [word for word in words if word[0].isupper() and len(word) > 1]
        
        return {
            "method": "rule_based",
            "query_type": query_type,
            "complexity": complexity,
            "entities": entities,
            "confidence": 0.6
        }
    
    async def _ml_analysis(self, query: str) -> Dict[str, Any]:
        """机器学习分析"""
        try:
            query_type, type_conf = self.ml_classifier.predict_query_type(query)
            complexity, comp_conf = self.ml_classifier.predict_complexity(query)
            intent, intent_conf = self.ml_classifier.predict_intent(query)
            
            return {
                "method": "machine_learning",
                "query_type": query_type,
                "complexity": complexity,
                "intent": intent,
                "confidence": (type_conf + comp_conf + intent_conf) / 3
            }
        except Exception as e:
            logger.error(f"ML分析失败: {e}")
            return {"method": "machine_learning", "error": str(e)}
    
    async def _bert_analysis(self, query: str) -> Dict[str, Any]:
        """BERT分析"""
        try:
            semantic_features = await self.bert_analyzer.encode_query(query)
            intent_scores = await self.bert_analyzer.classify_intent(query)
            
            return {
                "method": "bert",
                "semantic_features": semantic_features,
                "intent_scores": intent_scores,
                "confidence": max(intent_scores.values()) if intent_scores else 0.5
            }
        except Exception as e:
            logger.error(f"BERT分析失败: {e}")
            return {"method": "bert", "error": str(e)}
    
    async def _llm_analysis(self, query: str) -> Dict[str, Any]:
        """LLM分析"""
        try:
            cot_result = await self.llm_analyzer.analyze_with_cot(query)
            few_shot_result = await self.llm_analyzer.analyze_with_few_shot(query)
            
            return {
                "method": "llm",
                "cot_analysis": cot_result,
                "few_shot_analysis": few_shot_result,
                "confidence": 0.8
            }
        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            return {"method": "llm", "error": str(e)}
    
    def _fuse_analysis_results(self, query: str, rule_analysis: Dict[str, Any], 
                             ml_results: List[Any]) -> QueryAnalysisResult:
        """融合多种分析结果"""
        # 收集所有有效的分析结果
        all_results = [rule_analysis]
        for result in ml_results:
            if isinstance(result, dict) and "error" not in result:
                all_results.append(result)
        
        # 投票决定查询类型
        type_votes = {}
        complexity_votes = {}
        intent_votes = {}
        
        for result in all_results:
            if "query_type" in result:
                qtype = result["query_type"]
                confidence = result.get("confidence", 0.5)
                type_votes[qtype] = type_votes.get(qtype, 0) + confidence
            
            if "complexity" in result:
                complexity = result["complexity"]
                confidence = result.get("confidence", 0.5)
                complexity_votes[complexity] = complexity_votes.get(complexity, 0) + confidence
            
            if "intent" in result:
                intent = result["intent"]
                confidence = result.get("confidence", 0.5)
                intent_votes[intent] = intent_votes.get(intent, 0) + confidence
        
        # 选择得票最高的结果
        final_query_type = max(type_votes.items(), key=lambda x: x[1])[0] if type_votes else "general"
        final_complexity = max(complexity_votes.items(), key=lambda x: x[1])[0] if complexity_votes else "medium"
        final_intent = max(intent_votes.items(), key=lambda x: x[1])[0] if intent_votes else "information_seeking"
        
        # 收集实体
        all_entities = set()
        for result in all_results:
            if "entities" in result:
                all_entities.update(result["entities"])
        
        # 收集关键词
        keywords = self._extract_keywords(query)
        
        # 判断是否需要多步搜索
        needs_multi_step = (
            final_complexity in ["medium", "complex"] or
            final_query_type in ["comparison", "deep_dive", "multi_aspect"]
        )
        
        # 生成优化建议
        refinements = self._generate_refinements(query, final_query_type)
        
        # 计算置信度分数
        confidence_scores = {
            "query_type": type_votes.get(final_query_type, 0.5),
            "complexity": complexity_votes.get(final_complexity, 0.5),
            "intent": intent_votes.get(final_intent, 0.5)
        }
        
        # 收集语义特征
        semantic_features = None
        for result in all_results:
            if result.get("method") == "bert" and "semantic_features" in result:
                semantic_features = result["semantic_features"]
                break
        
        # 收集LLM分析结果
        llm_analysis = {}
        for result in all_results:
            if result.get("method") == "llm":
                llm_analysis = result
                break
        
        return QueryAnalysisResult(
            original_query=query,
            query_type=final_query_type,
            complexity=final_complexity,
            intent=final_intent,
            entities=list(all_entities),
            keywords=keywords,
            semantic_features=semantic_features,
            confidence_scores=confidence_scores,
            requires_multiple_searches=needs_multi_step,
            suggested_refinements=refinements,
            llm_analysis=llm_analysis
        )
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        words = query.split()
        # 过滤停用词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '了', '也', '就', '都', '要', '可以'}
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        return keywords
    
    def _generate_refinements(self, query: str, query_type: str) -> List[str]:
        """生成查询优化建议"""
        refinements = []
        
        if query_type == "comparison":
            refinements.extend([
                f"{query} 优缺点",
                f"{query} 详细对比",
                f"{query} 选择建议"
            ])
        elif query_type == "tutorial":
            refinements.extend([
                f"{query} 详细步骤",
                f"{query} 实例",
                f"{query} 注意事项"
            ])
        elif query_type == "latest":
            refinements.extend([
                f"{query} 2024",
                f"{query} 最新发展",
                f"{query} 趋势分析"
            ])
        elif query_type == "deep_dive":
            refinements.extend([
                f"{query} 详细介绍",
                f"{query} 深入分析",
                f"{query} 应用案例"
            ])
        
        return refinements[:3]

