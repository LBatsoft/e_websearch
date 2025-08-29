"""
查询分析器配置

提供不同场景下的分析器配置方案
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .advanced_query_analyzer import (
    BERTQueryAnalyzer,
    MLQueryClassifier,
    LLMQueryAnalyzer,
    HybridQueryAnalyzer
)


class AnalyzerType(Enum):
    """分析器类型"""
    RULE_BASED = "rule_based"
    MACHINE_LEARNING = "machine_learning"
    BERT = "bert"
    LLM = "llm"
    HYBRID = "hybrid"


@dataclass
class AnalyzerConfig:
    """分析器配置"""
    analyzer_type: AnalyzerType
    model_path: Optional[str] = None
    bert_model_name: str = "bert-base-chinese"
    enable_llm_analysis: bool = True
    enable_cot_analysis: bool = False
    enable_few_shot_analysis: bool = True
    confidence_threshold: float = 0.7
    max_analysis_time: int = 30  # 最大分析时间（秒）
    
    # 混合分析器权重配置
    rule_weight: float = 0.2
    ml_weight: float = 0.3
    bert_weight: float = 0.3
    llm_weight: float = 0.2


class AnalyzerFactory:
    """分析器工厂类"""
    
    @staticmethod
    def create_analyzer(config: AnalyzerConfig, llm_enhancer=None):
        """根据配置创建分析器"""
        if config.analyzer_type == AnalyzerType.RULE_BASED:
            # 使用原始的规则分析器
            from .planner import QueryAnalyzer
            return QueryAnalyzer(llm_enhancer)
        
        elif config.analyzer_type == AnalyzerType.MACHINE_LEARNING:
            return MLQueryClassifier(config.model_path)
        
        elif config.analyzer_type == AnalyzerType.BERT:
            return BERTQueryAnalyzer(config.bert_model_name)
        
        elif config.analyzer_type == AnalyzerType.LLM:
            return LLMQueryAnalyzer(llm_enhancer)
        
        elif config.analyzer_type == AnalyzerType.HYBRID:
            return HybridQueryAnalyzer(llm_enhancer, config.model_path)
        
        else:
            raise ValueError(f"不支持的分析器类型: {config.analyzer_type}")


# 预定义配置方案
ANALYZER_CONFIGS = {
    "development": AnalyzerConfig(
        analyzer_type=AnalyzerType.RULE_BASED,
        enable_llm_analysis=False,
        confidence_threshold=0.6
    ),
    
    "testing": AnalyzerConfig(
        analyzer_type=AnalyzerType.MACHINE_LEARNING,
        enable_llm_analysis=True,
        confidence_threshold=0.7
    ),
    
    "production_fast": AnalyzerConfig(
        analyzer_type=AnalyzerType.MACHINE_LEARNING,
        enable_llm_analysis=False,
        confidence_threshold=0.8
    ),
    
    "production_accurate": AnalyzerConfig(
        analyzer_type=AnalyzerType.HYBRID,
        enable_llm_analysis=True,
        enable_cot_analysis=True,
        enable_few_shot_analysis=True,
        confidence_threshold=0.8,
        rule_weight=0.1,
        ml_weight=0.3,
        bert_weight=0.3,
        llm_weight=0.3
    ),
    
    "research": AnalyzerConfig(
        analyzer_type=AnalyzerType.LLM,
        enable_llm_analysis=True,
        enable_cot_analysis=True,
        enable_few_shot_analysis=True,
        confidence_threshold=0.9,
        max_analysis_time=60
    )
}


def get_analyzer_config(environment: str = "production_accurate") -> AnalyzerConfig:
    """获取分析器配置"""
    if environment in ANALYZER_CONFIGS:
        return ANALYZER_CONFIGS[environment]
    else:
        # 默认返回生产环境配置
        return ANALYZER_CONFIGS["production_accurate"]


def create_analyzer_from_env(environment: str = "production_accurate", 
                           llm_enhancer=None):
    """从环境配置创建分析器"""
    config = get_analyzer_config(environment)
    return AnalyzerFactory.create_analyzer(config, llm_enhancer)

