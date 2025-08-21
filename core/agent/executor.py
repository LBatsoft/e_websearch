"""
Search Agent 循环执行器组件

负责执行搜索计划、管理执行状态、评估执行条件
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Tuple
from loguru import logger

from ..search_orchestrator import SearchOrchestrator
from ..models import SearchRequest, SearchResult, SourceType
from .models import (
    AgentSearchRequest,
    ExecutionPlan,
    ExecutionStep,
    ExecutionState,
    ExecutionStatus,
    StepType,
    AgentResult,
)


class StateManager:
    """状态管理器 - 管理执行状态和上下文"""
    
    def __init__(self):
        self.states: Dict[str, ExecutionState] = {}
    
    def create_state(self, request: AgentSearchRequest, plan: ExecutionPlan) -> ExecutionState:
        """创建新的执行状态"""
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        state = ExecutionState(
            session_id=session_id,
            request=request,
            plan=plan,
            status=ExecutionStatus.PENDING,
        )
        
        self.states[session_id] = state
        logger.info(f"创建执行状态: {session_id}")
        return state
    
    def get_state(self, session_id: str) -> Optional[ExecutionState]:
        """获取执行状态"""
        return self.states.get(session_id)
    
    def update_state(self, session_id: str, **updates):
        """更新执行状态"""
        if session_id in self.states:
            state = self.states[session_id]
            for key, value in updates.items():
                if hasattr(state, key):
                    setattr(state, key, value)
    
    def cleanup_state(self, session_id: str):
        """清理执行状态"""
        if session_id in self.states:
            del self.states[session_id]
            logger.info(f"清理执行状态: {session_id}")


class ConditionEvaluator:
    """条件判断器 - 评估执行条件和决策"""
    
    def __init__(self):
        pass
    
    def should_continue_execution(self, state: ExecutionState) -> Tuple[bool, str]:
        """判断是否应该继续执行"""
        # 检查超时
        if self._is_timeout(state):
            return False, "执行超时"
        
        # 检查是否达到最大迭代次数
        if self._reached_max_iterations(state):
            return False, "达到最大迭代次数"
        
        # 检查是否有足够的结果
        if self._has_sufficient_results(state):
            return False, "已获得足够的结果"
        
        # 检查是否有严重错误
        if self._has_critical_errors(state):
            return False, "遇到严重错误"
        
        return True, "继续执行"
    
    def should_refine_query(self, step: ExecutionStep, state: ExecutionState) -> Tuple[bool, str]:
        """判断是否需要优化查询"""
        if not state.request.enable_refinement:
            return False, "查询优化已禁用"
        
        # 如果结果太少，建议优化
        if len(step.results) < 3:
            return True, "结果数量不足，建议优化查询"
        
        # 如果置信度太低，建议优化
        if step.confidence_score < state.request.confidence_threshold:
            return True, "结果置信度不足，建议优化查询"
        
        return False, "无需优化查询"
    
    def evaluate_step_success(self, step: ExecutionStep) -> Tuple[bool, float, str]:
        """评估步骤执行成功度"""
        if step.status == ExecutionStatus.FAILED:
            return False, 0.0, step.error or "步骤执行失败"
        
        if step.status != ExecutionStatus.COMPLETED:
            return False, 0.0, "步骤未完成"
        
        # 基于结果数量和质量评估成功度
        result_count = len(step.results)
        if result_count == 0:
            return False, 0.0, "未找到任何结果"
        
        # 计算成功度分数
        success_score = min(result_count / 5.0, 1.0)  # 5个结果为满分
        if step.confidence_score > 0:
            success_score = (success_score + step.confidence_score) / 2
        
        if success_score >= 0.7:
            return True, success_score, "步骤执行成功"
        elif success_score >= 0.4:
            return True, success_score, "步骤部分成功"
        else:
            return False, success_score, "步骤执行效果不佳"
    
    def _is_timeout(self, state: ExecutionState) -> bool:
        """检查是否超时"""
        if state.request.timeout <= 0:
            return False
        
        elapsed = time.time() - state.start_time
        return elapsed > state.request.timeout
    
    def _reached_max_iterations(self, state: ExecutionState) -> bool:
        """检查是否达到最大迭代次数"""
        completed_steps = sum(1 for step in state.plan.steps 
                            if step.status == ExecutionStatus.COMPLETED)
        return completed_steps >= state.request.max_iterations
    
    def _has_sufficient_results(self, state: ExecutionState) -> bool:
        """检查是否有足够的结果"""
        return len(state.all_results) >= state.request.total_max_results
    
    def _has_critical_errors(self, state: ExecutionState) -> bool:
        """检查是否有严重错误"""
        # 如果连续多个步骤失败，认为是严重错误
        failed_count = 0
        for step in state.plan.steps[-3:]:  # 检查最近3个步骤
            if step.status == ExecutionStatus.FAILED:
                failed_count += 1
        
        return failed_count >= 2


class ExecutionEngine:
    """执行引擎 - 执行具体的搜索步骤"""
    
    def __init__(self, search_orchestrator: SearchOrchestrator):
        self.search_orchestrator = search_orchestrator
    
    async def execute_step(self, step: ExecutionStep, state: ExecutionState) -> bool:
        """执行单个步骤"""
        logger.info(f"开始执行步骤: {step.step_id} - {step.description}")
        
        step.start()
        
        try:
            if step.step_type == StepType.SEARCH:
                await self._execute_search_step(step, state)
            elif step.step_type == StepType.ANALYZE:
                await self._execute_analyze_step(step, state)
            elif step.step_type == StepType.REFINE:
                await self._execute_refine_step(step, state)
            elif step.step_type == StepType.SUMMARIZE:
                await self._execute_summarize_step(step, state)
            elif step.step_type == StepType.VALIDATE:
                await self._execute_validate_step(step, state)
            else:
                raise ValueError(f"未知的步骤类型: {step.step_type}")
            
            # 计算置信度
            confidence = self._calculate_step_confidence(step, state)
            step.complete(
                results=step.results,
                summary=step.summary,
                tags=step.tags,
                confidence_score=confidence
            )
            
            logger.info(f"步骤执行完成: {step.step_id}, 结果数: {len(step.results)}, 置信度: {confidence:.2f}")
            return True
            
        except Exception as e:
            error_msg = f"步骤执行失败: {str(e)}"
            logger.error(error_msg)
            step.fail(error_msg)
            state.add_error(error_msg)
            return False
    
    async def _execute_search_step(self, step: ExecutionStep, state: ExecutionState):
        """执行搜索步骤"""
        # 构建搜索请求
        search_request = SearchRequest(
            query=step.query,
            max_results=step.max_results,
            sources=step.sources,
            include_content=state.request.include_content,
            llm_summary=state.request.llm_summary,
            llm_tags=state.request.llm_tags,
            llm_per_result=state.request.llm_per_result,
            llm_language=state.request.llm_language,
            model_provider=state.request.model_provider,
            model_name=state.request.model_name,
        )
        
        # 执行搜索
        response = await self.search_orchestrator.search(search_request)
        
        # 处理结果
        step.results = response.results
        step.summary = response.llm_summary
        step.tags = response.llm_tags or []
        
        # 更新状态
        state.add_results(response.results)
        state.total_searches += 1
        if response.cache_hit:
            state.cache_hits += 1
        
        # 记录元数据
        step.metadata.update({
            "execution_time": response.execution_time,
            "cache_hit": response.cache_hit,
            "sources_used": [s.value for s in response.sources_used],
        })
    
    async def _execute_analyze_step(self, step: ExecutionStep, state: ExecutionState):
        """执行分析步骤"""
        # 分析已有结果，提取关键信息
        all_results = state.all_results
        if not all_results:
            step.results = []
            step.summary = "没有可分析的结果"
            return
        
        # 使用 LLM 进行结果分析
        if self.search_orchestrator.llm_enhancer and self.search_orchestrator.llm_enhancer.is_available():
            try:
                analysis_summary, analysis_tags, _ = await self.search_orchestrator.llm_enhancer.enhance(
                    all_results[:10],  # 分析前10个结果
                    step.query,
                    {
                        "llm_summary": True,
                        "llm_tags": True,
                        "llm_per_result": False,
                        "language": state.request.llm_language,
                        "model_provider": state.request.model_provider,
                        "model_name": state.request.model_name,
                    }
                )
                
                step.summary = analysis_summary
                step.tags = analysis_tags
                
            except Exception as e:
                logger.warning(f"LLM 分析失败: {e}")
                step.summary = "分析过程中遇到问题"
                step.tags = []
        
        step.results = []  # 分析步骤不产生新结果
    
    async def _execute_refine_step(self, step: ExecutionStep, state: ExecutionState):
        """执行查询优化步骤"""
        # 基于之前的结果优化查询
        previous_results = state.all_results
        if not previous_results:
            # 如果没有之前的结果，执行原始查询
            await self._execute_search_step(step, state)
            return
        
        # 分析之前结果的关键词，优化查询
        refined_query = self._refine_query_based_on_results(step.query, previous_results)
        step.query = refined_query
        step.description = f"优化查询: {refined_query}"
        
        # 执行优化后的搜索
        await self._execute_search_step(step, state)
    
    async def _execute_summarize_step(self, step: ExecutionStep, state: ExecutionState):
        """执行总结步骤"""
        all_results = state.all_results
        if not all_results:
            step.summary = "没有可总结的结果"
            step.results = []
            return
        
        # 使用 LLM 生成最终总结
        if self.search_orchestrator.llm_enhancer and self.search_orchestrator.llm_enhancer.is_available():
            try:
                final_summary, final_tags, _ = await self.search_orchestrator.llm_enhancer.enhance(
                    all_results,
                    state.request.query,
                    {
                        "llm_summary": True,
                        "llm_tags": True,
                        "llm_per_result": False,
                        "llm_max_items": min(len(all_results), 20),
                        "language": state.request.llm_language,
                        "model_provider": state.request.model_provider,
                        "model_name": state.request.model_name,
                    }
                )
                
                step.summary = final_summary
                step.tags = final_tags
                
                # 更新状态的最终结果
                state.final_summary = final_summary
                state.final_tags = final_tags
                
            except Exception as e:
                logger.warning(f"最终总结生成失败: {e}")
                step.summary = "总结生成过程中遇到问题"
                step.tags = []
        
        step.results = []  # 总结步骤不产生新结果
    
    async def _execute_validate_step(self, step: ExecutionStep, state: ExecutionState):
        """执行验证步骤"""
        # 验证结果的质量和相关性
        all_results = state.all_results
        validated_results = []
        
        for result in all_results:
            # 简单的相关性验证
            relevance_score = self._calculate_relevance(result, state.request.query)
            if relevance_score >= state.request.confidence_threshold:
                validated_results.append(result)
        
        step.results = validated_results
        step.summary = f"验证完成，保留 {len(validated_results)} 个高质量结果"
        
        # 更新状态
        state.all_results = validated_results
    
    def _refine_query_based_on_results(self, original_query: str, results: List[SearchResult]) -> str:
        """基于搜索结果优化查询"""
        if not results:
            return original_query
        
        # 提取结果中的关键词
        keywords = set()
        for result in results[:5]:  # 只分析前5个结果
            # 从标题和摘要中提取关键词
            text = f"{result.title} {result.snippet}"
            words = text.split()
            for word in words:
                if len(word) > 2 and word.isalpha():
                    keywords.add(word)
        
        # 选择最相关的关键词添加到查询中
        if keywords:
            top_keywords = list(keywords)[:2]  # 选择前2个关键词
            refined_query = f"{original_query} {' '.join(top_keywords)}"
            return refined_query
        
        return original_query
    
    def _calculate_relevance(self, result: SearchResult, query: str) -> float:
        """计算结果与查询的相关性"""
        query_words = set(query.lower().split())
        result_text = f"{result.title} {result.snippet}".lower()
        result_words = set(result_text.split())
        
        # 计算词汇重叠度
        overlap = len(query_words.intersection(result_words))
        total_words = len(query_words)
        
        if total_words == 0:
            return 0.0
        
        return overlap / total_words
    
    def _calculate_step_confidence(self, step: ExecutionStep, state: ExecutionState) -> float:
        """计算步骤置信度"""
        base_confidence = 0.5
        
        # 基于结果数量
        result_count = len(step.results)
        if result_count > 0:
            base_confidence += min(result_count / 10.0, 0.3)
        
        # 基于执行时间（快速执行通常意味着缓存命中或简单查询）
        if step.execution_time and step.execution_time < 2.0:
            base_confidence += 0.1
        
        # 基于步骤类型
        if step.step_type == StepType.SEARCH:
            base_confidence += 0.1
        elif step.step_type == StepType.ANALYZE:
            base_confidence += 0.2
        
        return min(max(base_confidence, 0.0), 1.0)


class LoopExecutor:
    """循环执行器 - 协调整个执行流程"""
    
    def __init__(self, search_orchestrator: SearchOrchestrator):
        self.state_manager = StateManager()
        self.condition_evaluator = ConditionEvaluator()
        self.execution_engine = ExecutionEngine(search_orchestrator)
    
    async def execute_plan(self, request: AgentSearchRequest, plan: ExecutionPlan) -> ExecutionState:
        """执行完整的搜索计划"""
        # 创建执行状态
        state = self.state_manager.create_state(request, plan)
        state.status = ExecutionStatus.RUNNING
        
        logger.info(f"开始执行搜索计划: {plan.plan_id}, 会话: {state.session_id}")
        
        try:
            # 执行计划中的每个步骤
            for step_index, step in enumerate(plan.steps):
                # 检查是否应该继续执行
                should_continue, reason = self.condition_evaluator.should_continue_execution(state)
                if not should_continue:
                    logger.info(f"停止执行: {reason}")
                    break
                
                # 执行当前步骤
                success = await self.execution_engine.execute_step(step, state)
                
                # 评估步骤执行结果
                step_success, success_score, message = self.condition_evaluator.evaluate_step_success(step)
                logger.info(f"步骤评估: {message}, 成功度: {success_score:.2f}")
                
                # 如果步骤失败且不是最后一步，可以尝试优化
                if not step_success and step_index < len(plan.steps) - 1:
                    should_refine, refine_reason = self.condition_evaluator.should_refine_query(step, state)
                    if should_refine:
                        logger.info(f"尝试查询优化: {refine_reason}")
                        # 这里可以添加查询优化逻辑
                
                # 更新计划进度
                plan.current_step_index = step_index + 1
            
            # 执行完成，生成最终结果
            await self._finalize_execution(state)
            
            state.complete(state.final_summary, state.final_tags)
            logger.info(f"执行计划完成: {state.session_id}, 总结果数: {len(state.all_results)}")
            
        except Exception as e:
            error_msg = f"执行计划失败: {str(e)}"
            logger.error(error_msg)
            state.fail(error_msg)
        
        return state
    
    async def _finalize_execution(self, state: ExecutionState):
        """完成执行，生成最终结果"""
        # 如果还没有最终总结，生成一个
        if not state.final_summary and state.all_results:
            # 创建一个总结步骤
            summarize_step = ExecutionStep(
                step_id=f"final_summary_{uuid.uuid4().hex[:8]}",
                step_type=StepType.SUMMARIZE,
                description="生成最终总结",
                query=state.request.query,
                sources=[],
                max_results=0,
            )
            
            await self.execution_engine.execute_step(summarize_step, state)
        
        # 去重和排序结果
        state.all_results = self._deduplicate_and_sort_results(state.all_results)
        
        # 限制结果数量
        if len(state.all_results) > state.request.total_max_results:
            state.all_results = state.all_results[:state.request.total_max_results]
    
    def _deduplicate_and_sort_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重和排序结果"""
        # 基于 URL 去重
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        # 按分数排序
        unique_results.sort(key=lambda x: x.score, reverse=True)
        
        return unique_results
    
    def get_execution_state(self, session_id: str) -> Optional[ExecutionState]:
        """获取执行状态"""
        return self.state_manager.get_state(session_id)
    
    def cleanup_session(self, session_id: str):
        """清理会话"""
        self.state_manager.cleanup_state(session_id)
