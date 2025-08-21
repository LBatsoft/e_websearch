"""
Search Agent 规划器组件

负责分析查询、分解任务、生成执行策略
"""

import re
import uuid
from typing import Dict, List, Optional, Tuple
from loguru import logger

from ..llm_enhancer import LLMEnhancer
from ..models import SourceType
from .models import (
    AgentSearchRequest,
    ExecutionPlan,
    ExecutionStep,
    StepType,
    PlanningStrategy,
    ExecutionStatus,
)
# from .dynamic_planner import DynamicStepGenerator  # TODO: 实现动态规划器


class QueryAnalyzer:
    """查询分析器 - 分析用户查询的意图和复杂度"""
    
    def __init__(self, llm_enhancer: Optional[LLMEnhancer] = None):
        self.llm_enhancer = llm_enhancer
        
        # 预定义的查询模式
        self.patterns = {
            "comparison": [r"对比|比较|vs|versus|区别|差异"],
            "tutorial": [r"教程|如何|怎么|步骤|方法"],
            "definition": [r"什么是|定义|含义|概念"],
            "latest": [r"最新|最近|2024|2023|今年|最新消息"],
            "deep_dive": [r"详细|深入|全面|完整|系统"],
            "multi_aspect": [r"和|与|以及|还有|包括"],
        }
    
    async def analyze_query(self, query: str) -> Dict[str, any]:
        """分析查询，返回分析结果"""
        analysis = {
            "original_query": query,
            "query_type": self._classify_query_type(query),
            "complexity": self._assess_complexity(query),
            "entities": self._extract_entities(query),
            "intent": self._infer_intent(query),
            "requires_multiple_searches": self._needs_multiple_searches(query),
            "suggested_refinements": self._suggest_refinements(query),
        }
        
        # 如果有 LLM 增强，使用 LLM 进行更深入的分析
        if self.llm_enhancer and self.llm_enhancer.is_available():
            try:
                llm_analysis = await self._llm_analyze_query(query)
                analysis.update(llm_analysis)
            except Exception as e:
                logger.warning(f"LLM 查询分析失败: {e}")
        
        logger.info(f"查询分析完成: {query} -> {analysis['query_type']}, 复杂度: {analysis['complexity']}")
        return analysis
    
    def _classify_query_type(self, query: str) -> str:
        """分类查询类型"""
        query_lower = query.lower()
        
        for query_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return query_type
        
        return "general"
    
    def _assess_complexity(self, query: str) -> str:
        """评估查询复杂度"""
        # 基于查询长度、关键词数量、特殊模式等评估
        words = query.split()
        
        if len(words) <= 2:
            return "simple"
        elif len(words) <= 5:
            return "medium"
        else:
            return "complex"
    
    def _extract_entities(self, query: str) -> List[str]:
        """提取查询中的实体"""
        # 简单的实体提取，可以后续用 NER 模型增强
        words = query.split()
        entities = []
        
        # 提取可能的实体（大写开头的词、专业术语等）
        for word in words:
            if word[0].isupper() and len(word) > 1:
                entities.append(word)
        
        return entities
    
    def _infer_intent(self, query: str) -> str:
        """推断查询意图"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["如何", "怎么", "方法"]):
            return "how_to"
        elif any(word in query_lower for word in ["什么是", "定义", "含义"]):
            return "definition"
        elif any(word in query_lower for word in ["最新", "最近", "新闻"]):
            return "latest_info"
        elif any(word in query_lower for word in ["对比", "比较", "区别"]):
            return "comparison"
        else:
            return "information_seeking"
    
    def _needs_multiple_searches(self, query: str) -> bool:
        """判断是否需要多次搜索"""
        # 基于查询复杂度和类型判断
        complexity = self._assess_complexity(query)
        query_type = self._classify_query_type(query)
        
        return (
            complexity in ["medium", "complex"] or
            query_type in ["comparison", "deep_dive", "multi_aspect"]
        )
    
    def _suggest_refinements(self, query: str) -> List[str]:
        """建议查询优化"""
        refinements = []
        query_type = self._classify_query_type(query)
        
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
        
        return refinements[:3]  # 最多返回3个建议
    
    async def _llm_analyze_query(self, query: str) -> Dict[str, any]:
        """使用 LLM 进行查询分析"""
        prompt = f"""
        请分析以下搜索查询，返回JSON格式的分析结果：
        
        查询: {query}
        
        请分析：
        1. 查询的主要意图
        2. 是否需要多步骤搜索
        3. 建议的搜索策略
        4. 可能的子查询
        
        返回格式：
        {{
            "main_intent": "主要意图描述",
            "needs_multi_step": true/false,
            "suggested_strategy": "建议的搜索策略",
            "sub_queries": ["子查询1", "子查询2"]
        }}
        """
        
        try:
            response = await self.llm_enhancer._select_provider().generate(
                [{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            if response:
                import json
                return json.loads(response)
        except Exception as e:
            logger.debug(f"LLM 查询分析解析失败: {e}")
        
        return {}


class TaskDecomposer:
    """任务分解器 - 将复杂查询分解为多个子任务"""
    
    def __init__(self, query_analyzer: QueryAnalyzer, llm_enhancer: Optional[LLMEnhancer] = None):
        self.query_analyzer = query_analyzer
        self.dynamic_generator = None  # TODO: 实现动态规划器
        # self.dynamic_generator = DynamicStepGenerator(llm_enhancer)
        self.use_dynamic_generation = True  # 默认使用动态生成
    
    async def decompose_task(self, request: AgentSearchRequest, 
                           analysis) -> List[ExecutionStep]:
        """分解任务为执行步骤"""
        steps = []
        
        try:
            # 标准化分析结果
            normalized_analysis = self._normalize_analysis_result(analysis)
            
            logger.debug(f"标准化分析结果: {normalized_analysis}")
            
            if not normalized_analysis["requires_multiple_searches"]:
                # 简单查询，单步执行
                if self.use_dynamic_generation:
                    # 使用动态生成器，即使是简单查询也可能生成多个优化步骤
                    # TODO: 实现动态规划器
                    # steps.extend(await self.dynamic_generator.generate_steps(request, normalized_analysis))
                    pass
                    logger.info(f"✅ 动态生成简单执行计划: {len(steps)}个步骤")
                else:
                    # 传统方式
                    steps.append(self._create_simple_search_step(request, normalized_analysis))
                    logger.info(f"✅ 创建简单执行计划: 1个步骤")
            else:
                # 复杂查询，多步执行
                if self.use_dynamic_generation:
                    # 使用动态生成器
                    # TODO: 实现动态规划器
                    # steps.extend(await self.dynamic_generator.generate_steps(request, normalized_analysis))
                    pass
                    logger.info(f"✅ 动态生成多步执行计划: {len(steps)}个步骤")
                else:
                    # 传统硬编码方式（保留作为回退）
                    steps.extend(await self._create_multi_step_plan(request, normalized_analysis))
                    logger.info(f"✅ 创建多步执行计划: {len(steps)}个步骤")
            
            # 验证步骤
            if not steps:
                logger.warning("⚠️ 任务分解结果为空，创建默认步骤")
                steps.append(self._create_simple_search_step(request, normalized_analysis))
            
            return steps
            
        except Exception as e:
            logger.error(f"❌ 任务分解失败: {e}")
            # 创建默认的简单搜索步骤
            return [self._create_simple_search_step(request, {})]
    
    def _normalize_analysis_result(self, analysis) -> Dict[str, any]:
        """标准化不同类型的分析结果"""
        if hasattr(analysis, 'requires_multiple_searches'):
            # 高级分析器结果（对象类型）
            return {
                "requires_multiple_searches": analysis.requires_multiple_searches,
                "query_type": analysis.query_type,
                "complexity": analysis.complexity,
                "intent": analysis.intent,
                "entities": getattr(analysis, 'entities', []),
                "keywords": getattr(analysis, 'keywords', []),
                "suggested_refinements": analysis.suggested_refinements or [],
                "confidence_scores": getattr(analysis, 'confidence_scores', {})
            }
        else:
            # 基础分析器结果（字典类型）
            return {
                "requires_multiple_searches": analysis.get("requires_multiple_searches", False),
                "query_type": analysis.get("query_type", "general"),
                "complexity": analysis.get("complexity", "simple"),
                "intent": analysis.get("intent", "information_seeking"),
                "entities": analysis.get("entities", []),
                "keywords": analysis.get("keywords", []),
                "suggested_refinements": analysis.get("suggested_refinements", []),
                "confidence_scores": {}
            }
    
    def _create_simple_search_step(self, request: AgentSearchRequest, 
                                 analysis: Dict[str, any]) -> ExecutionStep:
        """创建简单搜索步骤"""
        return ExecutionStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=f"搜索: {request.query}",
            query=request.query,
            sources=request.sources,
            max_results=request.max_results_per_iteration,
            metadata={
                "is_primary_search": True,
                "query_type": analysis.get("query_type", "general"),
                "complexity": analysis.get("complexity", "simple"),
            }
        )
    
    async def _create_multi_step_plan(self, request: AgentSearchRequest, 
                                    analysis: Dict[str, any]) -> List[ExecutionStep]:
        """创建多步执行计划"""
        steps = []
        query_type = analysis.get("query_type", "general")
        
        if query_type == "comparison":
            steps.extend(self._create_comparison_steps(request, analysis))
        elif query_type == "deep_dive":
            steps.extend(self._create_deep_dive_steps(request, analysis))
        elif query_type == "tutorial":
            steps.extend(self._create_tutorial_steps(request, analysis))
        else:
            steps.extend(self._create_general_multi_steps(request, analysis))
        
        return steps
    
    def _create_comparison_steps(self, request: AgentSearchRequest, 
                               analysis: Dict[str, any]) -> List[ExecutionStep]:
        """创建对比类查询的步骤"""
        steps = []
        
        # 第一步：基础搜索
        steps.append(ExecutionStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=f"基础搜索: {request.query}",
            query=request.query,
            sources=request.sources,
            max_results=request.max_results_per_iteration,
            metadata={"step_purpose": "baseline_search"}
        ))
        
        # 第二步：深入对比
        steps.append(ExecutionStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=f"深入对比: {request.query} 详细对比",
            query=f"{request.query} 详细对比 优缺点",
            sources=request.sources,
            max_results=request.max_results_per_iteration,
            metadata={"step_purpose": "detailed_comparison"}
        ))
        
        # 第三步：总结分析
        steps.append(ExecutionStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            step_type=StepType.ANALYZE,
            description="分析对比结果",
            query=request.query,
            sources=[],
            max_results=0,
            metadata={"step_purpose": "comparison_analysis"}
        ))
        
        return steps
    
    def _create_deep_dive_steps(self, request: AgentSearchRequest, 
                              analysis: Dict[str, any]) -> List[ExecutionStep]:
        """创建深度挖掘类查询的步骤"""
        steps = []
        
        # 第一步：概览搜索
        steps.append(ExecutionStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=f"概览搜索: {request.query}",
            query=request.query,
            sources=request.sources,
            max_results=request.max_results_per_iteration,
            metadata={"step_purpose": "overview_search"}
        ))
        
        # 第二步：详细信息
        steps.append(ExecutionStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=f"详细信息: {request.query} 详细介绍",
            query=f"{request.query} 详细介绍 深入分析",
            sources=request.sources,
            max_results=request.max_results_per_iteration,
            metadata={"step_purpose": "detailed_search"}
        ))
        
        # 第三步：相关应用
        steps.append(ExecutionStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=f"相关应用: {request.query} 应用案例",
            query=f"{request.query} 应用案例 实际使用",
            sources=request.sources,
            max_results=request.max_results_per_iteration,
            metadata={"step_purpose": "application_search"}
        ))
        
        return steps
    
    def _create_tutorial_steps(self, request: AgentSearchRequest, 
                             analysis: Dict[str, any]) -> List[ExecutionStep]:
        """创建教程类查询的步骤"""
        steps = []
        
        # 第一步：基础教程
        steps.append(ExecutionStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=f"基础教程: {request.query}",
            query=request.query,
            sources=request.sources,
            max_results=request.max_results_per_iteration,
            metadata={"step_purpose": "basic_tutorial"}
        ))
        
        # 第二步：详细步骤
        steps.append(ExecutionStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=f"详细步骤: {request.query} 详细步骤",
            query=f"{request.query} 详细步骤 具体方法",
            sources=request.sources,
            max_results=request.max_results_per_iteration,
            metadata={"step_purpose": "detailed_steps"}
        ))
        
        # 第三步：注意事项
        steps.append(ExecutionStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=f"注意事项: {request.query} 注意事项",
            query=f"{request.query} 注意事项 常见问题",
            sources=request.sources,
            max_results=request.max_results_per_iteration,
            metadata={"step_purpose": "precautions"}
        ))
        
        return steps
    
    def _create_general_multi_steps(self, request: AgentSearchRequest, 
                                  analysis: Dict[str, any]) -> List[ExecutionStep]:
        """创建通用多步查询"""
        steps = []
        
        # 第一步：主要搜索
        steps.append(ExecutionStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=f"主要搜索: {request.query}",
            query=request.query,
            sources=request.sources,
            max_results=request.max_results_per_iteration,
            metadata={"step_purpose": "primary_search"}
        ))
        
        # 第二步：补充搜索
        refinements = analysis.get("suggested_refinements", [])
        if refinements:
            steps.append(ExecutionStep(
                step_id=f"step_{uuid.uuid4().hex[:8]}",
                step_type=StepType.SEARCH,
                description=f"补充搜索: {refinements[0]}",
                query=refinements[0],
                sources=request.sources,
                max_results=request.max_results_per_iteration,
                metadata={"step_purpose": "supplementary_search"}
            ))
        
        return steps


class StrategyGenerator:
    """策略生成器 - 根据分析结果生成执行策略"""
    
    def __init__(self):
        # 策略选择权重配置
        self.strategy_weights = {
            PlanningStrategy.SIMPLE: {
                "simple": 0.8, "medium": 0.3, "complex": 0.1,
                "general": 0.7, "definition": 0.8, "tutorial": 0.6,
                "comparison": 0.2, "deep_dive": 0.1
            },
            PlanningStrategy.ITERATIVE: {
                "simple": 0.1, "medium": 0.6, "complex": 0.7,
                "general": 0.2, "definition": 0.1, "tutorial": 0.7,
                "comparison": 0.8, "deep_dive": 0.9
            },
            PlanningStrategy.PARALLEL: {
                "simple": 0.1, "medium": 0.1, "complex": 0.2,
                "general": 0.1, "definition": 0.1, "tutorial": 0.1,
                "comparison": 0.0, "deep_dive": 0.0
            }
        }
    
    def generate_strategy(self, request: AgentSearchRequest, 
                         analysis) -> PlanningStrategy:
        """生成执行策略"""
        # 标准化分析结果
        if hasattr(analysis, 'complexity'):
            complexity = analysis.complexity
            query_type = analysis.query_type
            needs_multiple = analysis.requires_multiple_searches
            confidence_scores = getattr(analysis, 'confidence_scores', {})
        else:
            complexity = analysis.get("complexity", "simple")
            query_type = analysis.get("query_type", "general")
            needs_multiple = analysis.get("requires_multiple_searches", False)
            confidence_scores = analysis.get("confidence_scores", {})
        
        # 根据用户指定的策略
        if request.planning_strategy != PlanningStrategy.ADAPTIVE:
            logger.info(f"🎯 使用用户指定策略: {request.planning_strategy.value}")
            return request.planning_strategy
        
        # 智能自适应策略选择
        strategy = self._select_adaptive_strategy(
            complexity, query_type, needs_multiple, confidence_scores
        )
        
        logger.info(f"🤖 自适应策略选择: {strategy.value} (复杂度: {complexity}, 类型: {query_type})")
        return strategy
    
    def _select_adaptive_strategy(self, complexity: str, query_type: str, 
                                needs_multiple: bool, confidence_scores: Dict) -> PlanningStrategy:
        """智能选择自适应策略"""
        
        # 计算每种策略的得分
        strategy_scores = {}
        
        for strategy in PlanningStrategy:
            if strategy == PlanningStrategy.ADAPTIVE:
                continue
                
            score = 0.0
            weights = self.strategy_weights.get(strategy, {})
            
            # 复杂度权重
            score += weights.get(complexity, 0.0) * 0.4
            
            # 查询类型权重
            score += weights.get(query_type, 0.0) * 0.3
            
            # 多步需求权重
            if needs_multiple:
                if strategy == PlanningStrategy.SIMPLE:
                    score -= 0.2
                else:
                    score += 0.2
            else:
                if strategy == PlanningStrategy.SIMPLE:
                    score += 0.1
            
            # 置信度权重
            if confidence_scores:
                avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
                if avg_confidence > 0.7:
                    # 高置信度时偏向简单策略
                    if strategy == PlanningStrategy.SIMPLE:
                        score += 0.1
                elif avg_confidence < 0.5:
                    # 低置信度时偏向迭代策略
                    if strategy == PlanningStrategy.ITERATIVE:
                        score += 0.1
            
            strategy_scores[strategy] = score
        
        # 选择得分最高的策略
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])[0]
        
        logger.debug(f"策略得分: {[(s.value, round(score, 3)) for s, score in strategy_scores.items()]}")
        
        return best_strategy


class SearchPlanner:
    """搜索规划器 - 协调查询分析、任务分解和策略生成"""
    
    def __init__(self, llm_enhancer: Optional[LLMEnhancer] = None, 
                 analyzer_type: str = "rule_based"):
        self.llm_enhancer = llm_enhancer
        self.analyzer_type = analyzer_type
        
        # 根据配置选择查询分析器
        self.query_analyzer = self._initialize_analyzer(analyzer_type, llm_enhancer)
        self.task_decomposer = TaskDecomposer(self.query_analyzer, llm_enhancer)
        self.strategy_generator = StrategyGenerator()
        
        logger.info(f"SearchPlanner 初始化完成，分析器类型: {analyzer_type}")
    
    def set_dynamic_generation(self, enabled: bool):
        """设置是否启用动态步骤生成"""
        self.task_decomposer.use_dynamic_generation = enabled
        logger.info(f"动态步骤生成: {'启用' if enabled else '禁用'}")
    
    def _initialize_analyzer(self, analyzer_type: str, llm_enhancer: Optional[LLMEnhancer]):
        """初始化查询分析器"""
        if analyzer_type == "advanced":
            try:
                from .advanced_query_analyzer import HybridQueryAnalyzer
                analyzer = HybridQueryAnalyzer(llm_enhancer)
                logger.info("✅ 使用高级混合查询分析器")
                return analyzer
            except ImportError as e:
                logger.warning(f"❌ 高级分析器不可用: {e}，回退到基础规则分析器")
                return QueryAnalyzer(llm_enhancer)
            except Exception as e:
                logger.error(f"❌ 高级分析器初始化失败: {e}，回退到基础规则分析器")
                return QueryAnalyzer(llm_enhancer)
        elif analyzer_type == "bert":
            try:
                from .advanced_query_analyzer import BERTQueryAnalyzer
                analyzer = BERTQueryAnalyzer()
                if analyzer.is_available():
                    logger.info("✅ 使用BERT查询分析器")
                    return analyzer
                else:
                    logger.warning("❌ BERT分析器不可用，回退到基础规则分析器")
                    return QueryAnalyzer(llm_enhancer)
            except ImportError:
                logger.warning("❌ BERT分析器依赖不可用，回退到基础规则分析器")
                return QueryAnalyzer(llm_enhancer)
        elif analyzer_type == "llm":
            try:
                from .advanced_query_analyzer import LLMQueryAnalyzer
                analyzer = LLMQueryAnalyzer(llm_enhancer)
                if analyzer.is_available():
                    logger.info("✅ 使用LLM查询分析器")
                    return analyzer
                else:
                    logger.warning("❌ LLM分析器不可用，回退到基础规则分析器")
                    return QueryAnalyzer(llm_enhancer)
            except ImportError:
                logger.warning("❌ LLM分析器依赖不可用，回退到基础规则分析器")
                return QueryAnalyzer(llm_enhancer)
        else:
            logger.info("✅ 使用基础规则查询分析器")
            return QueryAnalyzer(llm_enhancer)
    
    async def create_execution_plan(self, request: AgentSearchRequest) -> ExecutionPlan:
        """创建执行计划"""
        logger.info(f"🚀 开始创建执行计划: {request.query}")
        
        try:
            # 1. 分析查询
            logger.debug(f"步骤1: 使用 {self.analyzer_type} 分析器分析查询")
            analysis = await self._safe_analyze_query(request.query)
            
            # 2. 生成策略
            logger.debug("步骤2: 生成执行策略")
            strategy = self.strategy_generator.generate_strategy(request, analysis)
            
            # 3. 分解任务
            logger.debug("步骤3: 分解执行任务")
            steps = await self.task_decomposer.decompose_task(request, analysis)
            
            # 4. 验证计划
            logger.debug("步骤4: 验证执行计划")
            self._validate_plan(steps)
            
            # 5. 创建执行计划
            plan = ExecutionPlan(
                plan_id=f"plan_{uuid.uuid4().hex[:8]}",
                original_query=request.query,
                strategy=strategy,
                steps=steps,
                confidence_score=self._calculate_plan_confidence(analysis, steps)
            )
            
            logger.info(f"✅ 执行计划创建完成: {plan.plan_id}, 策略: {strategy.value}, 步骤数: {len(steps)}")
            return plan
            
        except Exception as e:
            logger.error(f"❌ 执行计划创建失败: {e}")
            # 创建简单的回退计划
            return self._create_fallback_plan(request)
    
    async def _safe_analyze_query(self, query: str):
        """安全的查询分析，包含错误处理"""
        try:
            return await self.query_analyzer.analyze_query(query)
        except Exception as e:
            logger.warning(f"查询分析失败: {e}，使用基础分析")
            # 回退到基础规则分析
            basic_analyzer = QueryAnalyzer(self.llm_enhancer)
            return await basic_analyzer.analyze_query(query)
    
    def _validate_plan(self, steps: List[ExecutionStep]):
        """验证执行计划的有效性"""
        if not steps:
            raise ValueError("执行计划不能为空")
        
        # 检查步骤ID唯一性
        step_ids = [step.step_id for step in steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("执行步骤ID必须唯一")
        
        # 检查必要字段
        for step in steps:
            if not step.query and step.step_type == StepType.SEARCH:
                raise ValueError(f"搜索步骤 {step.step_id} 缺少查询内容")
    
    def _extract_analysis_summary(self, analysis) -> Dict[str, any]:
        """提取分析结果摘要"""
        if hasattr(analysis, 'query_type'):
            # 高级分析器结果
            return {
                "query_type": analysis.query_type,
                "complexity": analysis.complexity,
                "intent": analysis.intent,
                "confidence": getattr(analysis, 'confidence_scores', {}),
                "requires_multiple": analysis.requires_multiple_searches
            }
        else:
            # 基础分析器结果
            return {
                "query_type": analysis.get("query_type", "unknown"),
                "complexity": analysis.get("complexity", "unknown"),
                "intent": analysis.get("intent", "unknown"),
                "requires_multiple": analysis.get("requires_multiple_searches", False)
            }
    
    def _create_fallback_plan(self, request: AgentSearchRequest) -> ExecutionPlan:
        """创建回退执行计划"""
        logger.info("创建简单回退执行计划")
        
        fallback_step = ExecutionStep(
            step_id=f"fallback_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=f"简单搜索: {request.query}",
            query=request.query,
            sources=request.sources,
            max_results=request.max_results_per_iteration,
            metadata={"is_fallback": True}
        )
        
        return ExecutionPlan(
            plan_id=f"fallback_{uuid.uuid4().hex[:8]}",
            original_query=request.query,
            strategy=PlanningStrategy.SIMPLE,
            steps=[fallback_step],
            confidence_score=0.5
        )
    
    def _calculate_plan_confidence(self, analysis, steps: List[ExecutionStep]) -> float:
        """计算计划置信度"""
        base_confidence = 0.7
        
        # 根据分析器类型调整基础置信度
        if self.analyzer_type == "advanced":
            base_confidence = 0.8
        elif self.analyzer_type in ["bert", "llm"]:
            base_confidence = 0.75
        
        # 根据查询复杂度调整
        if hasattr(analysis, 'complexity'):
            complexity = analysis.complexity
        else:
            complexity = analysis.get("complexity", "simple")
            
        if complexity == "simple":
            base_confidence += 0.15
        elif complexity == "medium":
            base_confidence += 0.05
        elif complexity == "complex":
            base_confidence -= 0.1
        
        # 根据步骤数量调整
        step_count = len(steps)
        if step_count == 1:
            base_confidence += 0.1
        elif step_count == 2:
            base_confidence += 0.05
        elif step_count > 4:
            base_confidence -= 0.15
        
        # 根据分析器置信度调整（如果可用）
        if hasattr(analysis, 'confidence_scores'):
            avg_confidence = sum(analysis.confidence_scores.values()) / len(analysis.confidence_scores)
            base_confidence = (base_confidence + avg_confidence) / 2
        
        # 根据步骤类型多样性调整
        step_types = set(step.step_type for step in steps)
        if len(step_types) > 1:
            base_confidence += 0.05  # 多样化的步骤类型提高置信度
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def optimize_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """优化执行计划"""
        logger.info(f"🔧 开始优化执行计划: {plan.plan_id}")
        
        try:
            # 1. 去重相似步骤
            optimized_steps = self._deduplicate_steps(plan.steps)
            
            # 2. 重新排序步骤
            optimized_steps = self._reorder_steps(optimized_steps, plan.strategy)
            
            # 3. 合并可合并的步骤
            optimized_steps = self._merge_compatible_steps(optimized_steps)
            
            # 4. 验证优化后的计划
            self._validate_plan(optimized_steps)
            
            # 创建优化后的计划
            optimized_plan = ExecutionPlan(
                plan_id=plan.plan_id,
                original_query=plan.original_query,
                strategy=plan.strategy,
                steps=optimized_steps,
                confidence_score=plan.confidence_score
            )
            
            logger.info(f"✅ 计划优化完成: {len(plan.steps)} -> {len(optimized_steps)} 步骤")
            return optimized_plan
            
        except Exception as e:
            logger.warning(f"⚠️ 计划优化失败: {e}，返回原计划")
            return plan
    
    def _deduplicate_steps(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """去重相似的执行步骤"""
        unique_steps = []
        seen_queries = set()
        
        for step in steps:
            # 简单的查询去重
            query_key = step.query.lower().strip()
            if query_key not in seen_queries:
                unique_steps.append(step)
                seen_queries.add(query_key)
            else:
                logger.debug(f"去重步骤: {step.description}")
        
        return unique_steps
    
    def _reorder_steps(self, steps: List[ExecutionStep], strategy: PlanningStrategy) -> List[ExecutionStep]:
        """根据策略重新排序步骤"""
        if strategy == PlanningStrategy.SIMPLE:
            # 简单策略：保持原顺序
            return steps
        elif strategy == PlanningStrategy.ITERATIVE:
            # 迭代策略：搜索步骤在前，分析步骤在后
            search_steps = [s for s in steps if s.step_type == StepType.SEARCH]
            analyze_steps = [s for s in steps if s.step_type == StepType.ANALYZE]
            other_steps = [s for s in steps if s.step_type not in [StepType.SEARCH, StepType.ANALYZE]]
            return search_steps + other_steps + analyze_steps
        else:
            # 其他策略：保持原顺序
            return steps
    
    def _merge_compatible_steps(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """合并兼容的执行步骤"""
        if len(steps) <= 1:
            return steps
        
        merged_steps = []
        i = 0
        
        while i < len(steps):
            current_step = steps[i]
            
            # 检查是否可以与下一个步骤合并
            if (i + 1 < len(steps) and 
                self._can_merge_steps(current_step, steps[i + 1])):
                
                merged_step = self._merge_two_steps(current_step, steps[i + 1])
                merged_steps.append(merged_step)
                i += 2  # 跳过下一个步骤
                logger.debug(f"合并步骤: {current_step.description} + {steps[i-1].description}")
            else:
                merged_steps.append(current_step)
                i += 1
        
        return merged_steps
    
    def _can_merge_steps(self, step1: ExecutionStep, step2: ExecutionStep) -> bool:
        """判断两个步骤是否可以合并"""
        # 只合并相同类型的搜索步骤
        if (step1.step_type != StepType.SEARCH or 
            step2.step_type != StepType.SEARCH):
            return False
        
        # 检查查询相似性
        query1_words = set(step1.query.lower().split())
        query2_words = set(step2.query.lower().split())
        
        # 如果有超过50%的词汇重叠，认为可以合并
        overlap = len(query1_words & query2_words)
        total = len(query1_words | query2_words)
        
        return overlap / total > 0.5 if total > 0 else False
    
    def _merge_two_steps(self, step1: ExecutionStep, step2: ExecutionStep) -> ExecutionStep:
        """合并两个执行步骤"""
        merged_query = f"{step1.query} {step2.query}"
        merged_description = f"合并搜索: {step1.query} & {step2.query}"
        
        return ExecutionStep(
            step_id=f"merged_{uuid.uuid4().hex[:8]}",
            step_type=StepType.SEARCH,
            description=merged_description,
            query=merged_query,
            sources=list(set(step1.sources + step2.sources)),
            max_results=max(step1.max_results, step2.max_results),
            metadata={
                "merged_from": [step1.step_id, step2.step_id],
                "original_queries": [step1.query, step2.query]
            }
        )
