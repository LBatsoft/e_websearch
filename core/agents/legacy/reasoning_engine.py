"""
推理引擎 - 使用 LLM 进行智能推理和决策

提供基于大模型的：
- 结果分析
- 策略生成
- 推理过程生成
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from loguru import logger

from ...llm_enhancer import LLMEnhancer


@dataclass
class AnalysisRequest:
    """分析请求"""
    query: str
    results_features: Dict[str, Any]
    current_strategy: Dict[str, Any]
    execution_context: Dict[str, Any]


@dataclass
class ProcessingStrategy:
    """处理策略"""
    dedup_method: str
    ranking_method: str
    quality_threshold: float
    ranking_weights: Dict[str, float]
    processing_steps: List[str] = None
    reasoning: List[str] = None


class ReasoningEngine:
    """基于 LLM 的推理引擎"""
    
    def __init__(self, llm_enhancer: LLMEnhancer):
        self.llm = llm_enhancer
        
        # 分析提示模板
        self.analysis_prompt_template = """
作为搜索结果处理专家，请分析以下搜索场景并提供处理策略：

搜索查询: {query}

结果特征:
{results_features}

当前策略:
{current_strategy}

执行上下文:
{execution_context}

请提供：
1. 对结果集的深入分析
2. 推荐的处理策略（去重、排序、质量控制等）
3. 详细的推理过程和决策依据

输出格式要求：
{
    "analysis": {
        "key_findings": [],
        "quality_assessment": {},
        "content_analysis": {},
        "risks_and_challenges": []
    },
    "strategy": {
        "dedup_method": "",
        "ranking_method": "",
        "quality_threshold": 0.0,
        "ranking_weights": {},
        "processing_steps": []
    },
    "reasoning": []
}

请确保输出为有效的 JSON 格式。
"""

    async def analyze_and_generate_strategy(self, request: AnalysisRequest) -> ProcessingStrategy:
        """分析结果并生成处理策略"""
        try:
            # 构建提示
            prompt = self.analysis_prompt_template.format(
                query=request.query,
                results_features=json.dumps(request.results_features, indent=2, ensure_ascii=False),
                current_strategy=json.dumps(request.current_strategy, indent=2, ensure_ascii=False),
                execution_context=json.dumps(request.execution_context, indent=2, ensure_ascii=False)
            )
            
            # 调用 LLM
            response = await self.llm.generate_text(
                prompt,
                max_tokens=1000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # 解析响应
            try:
                result = json.loads(response)
                
                # 提取策略
                strategy = ProcessingStrategy(
                    dedup_method=result["strategy"]["dedup_method"],
                    ranking_method=result["strategy"]["ranking_method"],
                    quality_threshold=float(result["strategy"]["quality_threshold"]),
                    ranking_weights=result["strategy"]["ranking_weights"],
                    processing_steps=result["strategy"]["processing_steps"],
                    reasoning=result["reasoning"]
                )
                
                # 记录分析结果
                logger.info("LLM 分析结果:")
                logger.info(f"关键发现: {result['analysis']['key_findings']}")
                logger.info(f"质量评估: {result['analysis']['quality_assessment']}")
                logger.info(f"推荐策略: {strategy}")
                
                return strategy
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"解析 LLM 响应失败: {e}")
                return self._generate_fallback_strategy(request)
            
        except Exception as e:
            logger.error(f"调用 LLM 失败: {e}")
            return self._generate_fallback_strategy(request)
    
    def _generate_fallback_strategy(self, request: AnalysisRequest) -> ProcessingStrategy:
        """生成后备策略"""
        # 使用基本的启发式规则
        features = request.results_features
        
        strategy = ProcessingStrategy(
            dedup_method="hybrid",
            ranking_method="hybrid",
            quality_threshold=0.5,
            ranking_weights={
                "relevance": 0.4,
                "quality": 0.3,
                "freshness": 0.2,
                "authority": 0.1
            },
            processing_steps=["basic_dedup", "basic_ranking", "quality_filter"],
            reasoning=[
                "由于 LLM 分析失败，使用基本启发式规则",
                f"检测到 {features['total_count']} 个结果，采用通用处理策略",
                "使用混合去重和排序方法以确保基本的结果质量"
            ]
        )
        
        return strategy