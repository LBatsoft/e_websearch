"""
搜索策略定义和管理

实现灵活的搜索策略定义、评估和动态调整机制
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import time


class StrategyPriority(Enum):
    """策略优先级"""
    SPEED = "speed"          # 速度优先
    RELEVANCE = "relevance"  # 相关性优先
    COVERAGE = "coverage"    # 覆盖度优先
    QUALITY = "quality"      # 质量优先
    BALANCED = "balanced"    # 平衡模式


@dataclass
class SearchStrategyConfig:
    """搜索策略配置"""
    name: str
    priority: StrategyPriority
    sources: List[str]
    max_results: int
    min_confidence: float = 0.0
    timeout: Optional[float] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    ranking_weights: Dict[str, float] = field(default_factory=dict)
    
    # 性能指标
    avg_execution_time: float = 0.0
    avg_result_count: float = 0.0
    success_rate: float = 0.0
    usage_count: int = 0
    
    def update_metrics(self, execution_time: float, result_count: int, success: bool):
        """更新性能指标"""
        self.usage_count += 1
        weight = 1.0 / self.usage_count
        
        self.avg_execution_time = (self.avg_execution_time * (1 - weight) + 
                                 execution_time * weight)
        self.avg_result_count = (self.avg_result_count * (1 - weight) + 
                               result_count * weight)
        self.success_rate = (self.success_rate * (1 - weight) + 
                           (1.0 if success else 0.0) * weight)


class SearchStrategyManager:
    """搜索策略管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, SearchStrategyConfig] = {}
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """初始化默认策略"""
        self.strategies["default"] = SearchStrategyConfig(
            name="default",
            priority=StrategyPriority.BALANCED,
            sources=["zai"],
            max_results=10,
            min_confidence=0.5,
            ranking_weights={
                "relevance": 0.4,
                "freshness": 0.3,
                "quality": 0.3
            }
        )
        
        self.strategies["comprehensive"] = SearchStrategyConfig(
            name="comprehensive",
            priority=StrategyPriority.COVERAGE,
            sources=["zai", "bing"],
            max_results=20,
            min_confidence=0.3,
            timeout=10.0,
            ranking_weights={
                "relevance": 0.3,
                "coverage": 0.4,
                "diversity": 0.3
            }
        )
        
        self.strategies["fast"] = SearchStrategyConfig(
            name="fast",
            priority=StrategyPriority.SPEED,
            sources=["zai"],
            max_results=5,
            min_confidence=0.7,
            timeout=2.0,
            ranking_weights={
                "relevance": 0.6,
                "speed": 0.4
            }
        )
        
        self.strategies["quality"] = SearchStrategyConfig(
            name="quality",
            priority=StrategyPriority.QUALITY,
            sources=["zai"],
            max_results=10,
            min_confidence=0.8,
            ranking_weights={
                "quality": 0.5,
                "relevance": 0.3,
                "authority": 0.2
            }
        )
    
    def get_strategy(self, name: str) -> Optional[SearchStrategyConfig]:
        """获取策略配置"""
        return self.strategies.get(name)
    
    def add_strategy(self, config: SearchStrategyConfig):
        """添加新策略"""
        self.strategies[config.name] = config
    
    def update_strategy(self, name: str, updates: Dict[str, Any]):
        """更新策略配置"""
        if name not in self.strategies:
            raise ValueError(f"策略不存在: {name}")
        
        strategy = self.strategies[name]
        for key, value in updates.items():
            if hasattr(strategy, key):
                setattr(strategy, key, value)
    
    def remove_strategy(self, name: str):
        """删除策略"""
        if name in self.strategies:
            del self.strategies[name]
    
    def select_strategy(self, query: str, context: Dict[str, Any]) -> str:
        """选择最适合的策略"""
        scores = {}
        
        for name, strategy in self.strategies.items():
            score = self._evaluate_strategy_fitness(strategy, query, context)
            scores[name] = score
        
        # 选择得分最高的策略
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _evaluate_strategy_fitness(self, strategy: SearchStrategyConfig, 
                                 query: str, context: Dict[str, Any]) -> float:
        """评估策略适合度"""
        scores = []
        
        # 1. 查询复杂度评分
        query_length = len(query.split())
        complexity_score = min(1.0, query_length / 10.0)
        if strategy.priority == StrategyPriority.COVERAGE:
            scores.append(complexity_score)
        elif strategy.priority == StrategyPriority.SPEED:
            scores.append(1.0 - complexity_score)
        else:
            scores.append(0.5)  # 中性评分
        
        # 2. 性能历史评分
        if strategy.usage_count > 0:
            performance_score = (
                strategy.success_rate * 0.4 +
                min(1.0, 10.0 / strategy.avg_execution_time) * 0.3 +
                min(1.0, strategy.avg_result_count / 10.0) * 0.3
            )
            scores.append(performance_score)
        
        # 3. 上下文匹配评分
        context_score = self._evaluate_context_match(strategy, context)
        scores.append(context_score)
        
        return sum(scores) / len(scores)
    
    def _evaluate_context_match(self, strategy: SearchStrategyConfig, 
                              context: Dict[str, Any]) -> float:
        """评估策略与上下文的匹配度"""
        score = 0.5  # 默认中性评分
        
        # 1. 时间限制
        if "max_time" in context:
            if strategy.timeout and strategy.timeout <= context["max_time"]:
                score += 0.2
            elif strategy.priority == StrategyPriority.SPEED:
                score += 0.1
        
        # 2. 质量要求
        if "quality_requirement" in context:
            if (strategy.priority == StrategyPriority.QUALITY and 
                context["quality_requirement"] == "high"):
                score += 0.2
            elif (strategy.priority == StrategyPriority.COVERAGE and 
                  context["quality_requirement"] == "comprehensive"):
                score += 0.2
        
        # 3. 资源限制
        if "resource_constraint" in context:
            if context["resource_constraint"] == "limited":
                if len(strategy.sources) <= 1:
                    score += 0.1
            else:
                if len(strategy.sources) > 1:
                    score += 0.1
        
        return min(1.0, score)
    
    def adapt_strategy(self, name: str, feedback: Dict[str, Any]):
        """根据反馈调整策略"""
        if name not in self.strategies:
            return
        
        strategy = self.strategies[name]
        
        # 1. 更新性能指标
        if "execution_time" in feedback and "result_count" in feedback:
            strategy.update_metrics(
                execution_time=feedback["execution_time"],
                result_count=feedback["result_count"],
                success=feedback.get("success", True)
            )
        
        # 2. 动态调整参数
        if strategy.usage_count >= 10:  # 有足够的使用数据时才调整
            self._adjust_strategy_parameters(strategy, feedback)
    
    def _adjust_strategy_parameters(self, strategy: SearchStrategyConfig, 
                                  feedback: Dict[str, Any]):
        """动态调整策略参数"""
        # 1. 调整超时时间
        if strategy.timeout:
            if strategy.avg_execution_time > strategy.timeout * 0.8:
                # 执行时间接近超时，增加超时时间
                strategy.timeout *= 1.2
            elif strategy.avg_execution_time < strategy.timeout * 0.5:
                # 执行时间远小于超时，可以适当减少
                strategy.timeout *= 0.9
        
        # 2. 调整结果数量
        if strategy.avg_result_count < strategy.max_results * 0.5:
            # 平均结果数太少，增加限制
            strategy.max_results = min(30, int(strategy.max_results * 1.2))
        elif strategy.avg_result_count > strategy.max_results * 0.9:
            # 经常达到限制，可以适当增加
            strategy.max_results = min(30, int(strategy.max_results * 1.1))
        
        # 3. 调整最小置信度
        if "avg_confidence" in feedback:
            avg_confidence = feedback["avg_confidence"]
            if avg_confidence > strategy.min_confidence * 1.2:
                # 实际置信度远高于要求，可以适当提高要求
                strategy.min_confidence = min(0.9, strategy.min_confidence * 1.1)
            elif avg_confidence < strategy.min_confidence:
                # 难以达到置信度要求，适当降低
                strategy.min_confidence = max(0.3, strategy.min_confidence * 0.9)
        
        # 4. 调整排序权重
        if "effective_weights" in feedback:
            effective_weights = feedback["effective_weights"]
            for metric, weight in strategy.ranking_weights.items():
                if metric in effective_weights:
                    # 逐渐调整权重以接近有效权重
                    strategy.ranking_weights[metric] = (
                        weight * 0.9 + effective_weights[metric] * 0.1
                    )
