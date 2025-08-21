"""
Search Agent 核心类

整合规划器、执行器、工具层和可观测层，提供完整的智能搜索代理功能
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any
from loguru import logger

from ..search_orchestrator import SearchOrchestrator
from ..llm_enhancer import LLMEnhancer
from .models import (
    AgentSearchRequest,
    AgentSearchResponse,
    ExecutionState,
    ExecutionStatus,
    AgentResult,
    StepType,
)
from .planner import SearchPlanner
from .executor import LoopExecutor
from .tools import SearchTools, ContentAnalysisTools, DataProcessingTools
from .observability import ExecutionTracer, PerformanceMonitor, ResultLogger


class SearchAgent:
    """智能搜索代理 - 核心协调类"""
    
    def __init__(self, search_orchestrator: SearchOrchestrator):
        self.search_orchestrator = search_orchestrator
        
        # 初始化核心组件
        self.planner = SearchPlanner(search_orchestrator.llm_enhancer)
        self.executor = LoopExecutor(search_orchestrator)
        
        # 初始化工具层
        self.search_tools = SearchTools(search_orchestrator)
        self.content_tools = ContentAnalysisTools(search_orchestrator.llm_enhancer)
        self.data_tools = DataProcessingTools()
        
        # 初始化可观测层
        self.tracer = ExecutionTracer()
        self.performance_monitor = PerformanceMonitor()
        self.result_logger = ResultLogger()
        
        logger.info("Search Agent 初始化完成")
    
    async def search(self, request: AgentSearchRequest) -> AgentSearchResponse:
        """执行智能搜索"""
        session_id = f"agent_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        logger.info(f"开始 Agent 搜索: {request.query} [会话: {session_id}]")
        
        # 初始化可观测组件
        if request.enable_tracing:
            self.tracer.start_session(session_id, self._request_to_dict(request))
        
        if request.enable_performance_monitoring:
            self.performance_monitor.start_monitoring(session_id)
        
        try:
            # 1. 创建执行计划
            plan = await self.planner.create_execution_plan(request)
            logger.info(f"执行计划创建完成: {plan.strategy.value}, {len(plan.steps)} 个步骤")
            
            if request.enable_tracing:
                self.tracer.trace_decision(session_id, "plan_created", {
                    "strategy": plan.strategy.value,
                    "steps_count": len(plan.steps),
                    "confidence": plan.confidence_score,
                })
            
            # 2. 执行计划
            execution_state = await self.executor.execute_plan(request, plan)
            
            # 3. 处理和优化结果
            final_results = await self._process_final_results(
                execution_state, request, session_id
            )
            
            # 4. 生成响应
            response = await self._build_response(
                execution_state, final_results, session_id, start_time
            )
            
            # 5. 记录最终结果
            if request.enable_tracing:
                self.result_logger.log_final_results(session_id, execution_state)
                self.tracer.end_session(session_id, execution_state)
            
            logger.info(f"Agent 搜索完成: {session_id}, 耗时: {response.total_execution_time:.2f}s")
            return response
            
        except Exception as e:
            error_msg = f"Agent 搜索失败: {str(e)}"
            logger.error(error_msg)
            
            if request.enable_tracing:
                self.tracer.trace_error(session_id, "search_failed", error_msg)
            
            # 返回错误响应
            return AgentSearchResponse(
                success=False,
                session_id=session_id,
                message=error_msg,
                total_execution_time=time.time() - start_time,
                errors=[error_msg],
            )
        
        finally:
            # 清理资源
            await self._cleanup_session(session_id)
    
    async def get_search_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取搜索状态"""
        execution_state = self.executor.get_execution_state(session_id)
        if not execution_state:
            return None
        
        status = {
            "session_id": session_id,
            "status": execution_state.status.value,
            "progress": self._calculate_progress(execution_state),
            "current_step": self._get_current_step_info(execution_state),
            "results_count": len(execution_state.all_results),
            "execution_time": time.time() - execution_state.start_time,
            "errors": execution_state.errors,
        }
        
        return status
    
    async def cancel_search(self, session_id: str) -> bool:
        """取消搜索"""
        execution_state = self.executor.get_execution_state(session_id)
        if not execution_state:
            return False
        
        execution_state.status = ExecutionStatus.CANCELLED
        
        if execution_state.request.enable_tracing:
            self.tracer.trace_decision(session_id, "search_cancelled", {
                "cancelled_at": time.time(),
                "reason": "user_request",
            })
        
        logger.info(f"搜索已取消: {session_id}")
        return True
    
    async def get_execution_trace(self, session_id: str) -> List[Dict[str, Any]]:
        """获取执行追踪记录"""
        return self.tracer.get_session_trace(session_id)
    
    async def get_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """获取性能指标"""
        return self.performance_monitor.get_performance_summary(session_id)
    
    async def _process_final_results(self, execution_state: ExecutionState,
                                   request: AgentSearchRequest, 
                                   session_id: str) -> List[AgentResult]:
        """处理最终结果"""
        if not execution_state.all_results:
            return []
        
        # 1. 去重
        unique_results = self.data_tools.deduplicate_results(
            execution_state.all_results, method="url"
        )
        
        # 2. 排序
        ranked_results = self.data_tools.rank_results(
            unique_results, request.query, ranking_method="hybrid"
        )
        
        # 3. 过滤
        filtered_results = self.data_tools.filter_results(
            ranked_results, {"min_score": 0.1}
        )
        
        # 4. 限制数量
        final_results = filtered_results[:request.total_max_results]
        
        # 5. 转换为 AgentResult
        agent_results = []
        for result in final_results:
            # 找到结果来源的步骤
            source_step = self._find_result_source_step(result, execution_state)
            
            agent_result = AgentResult.from_search_result(
                result,
                step_id=source_step.step_id if source_step else None,
                step_type=source_step.step_type if source_step else None,
            )
            
            # 计算相关性和置信度
            agent_result.relevance_score = self._calculate_relevance_score(
                result, request.query
            )
            agent_result.confidence_score = self._calculate_confidence_score(
                result, execution_state
            )
            
            agent_results.append(agent_result)
        
        # 6. 分析内容质量
        if request.enable_performance_monitoring:
            quality_analysis = await self.content_tools.analyze_content_quality(final_results)
            self.result_logger.log_analysis_results(
                session_id, "content_quality", quality_analysis
            )
        
        logger.info(f"最终结果处理完成: {len(agent_results)} 个结果")
        return agent_results
    
    def _find_result_source_step(self, result, execution_state):
        """找到结果的来源步骤"""
        for step in execution_state.plan.steps:
            if result in step.results:
                return step
        return None
    
    def _calculate_relevance_score(self, result, query: str) -> float:
        """计算相关性分数"""
        query_words = set(query.lower().split())
        result_text = f"{result.title} {result.snippet}".lower()
        result_words = set(result_text.split())
        
        if not query_words or not result_words:
            return 0.0
        
        intersection = query_words.intersection(result_words)
        return len(intersection) / len(query_words)
    
    def _calculate_confidence_score(self, result, execution_state) -> float:
        """计算置信度分数"""
        base_score = result.score
        
        # 基于来源可信度
        source_reliability = {
            "zai": 0.9,
            "bing": 0.8,
            "wechat": 0.7,
            "zhihu": 0.6,
        }
        
        source_name = result.source.value if hasattr(result.source, 'value') else str(result.source)
        reliability = source_reliability.get(source_name, 0.5)
        
        # 基于内容完整性
        content_completeness = 1.0 if result.content else 0.5
        
        # 综合计算
        confidence = (base_score * 0.5 + reliability * 0.3 + content_completeness * 0.2)
        return min(max(confidence, 0.0), 1.0)
    
    async def _build_response(self, execution_state: ExecutionState,
                            final_results: List[AgentResult],
                            session_id: str, start_time: float) -> AgentSearchResponse:
        """构建响应"""
        total_time = time.time() - start_time
        
        # 收集执行统计
        total_iterations = len([s for s in execution_state.plan.steps 
                              if s.status == ExecutionStatus.COMPLETED])
        
        sources_used = list(set(
            r.source for r in execution_state.all_results
        ))
        
        # 收集引用
        citations = []
        for result in final_results:
            if result.url not in citations:
                citations.append(result.url)
        
        # 构建响应
        response = AgentSearchResponse(
            success=execution_state.status == ExecutionStatus.COMPLETED,
            session_id=session_id,
            message="搜索完成" if execution_state.status == ExecutionStatus.COMPLETED else "搜索未完成",
            execution_state=execution_state,
            results=final_results,
            total_count=len(final_results),
            original_query=execution_state.request.query,
            final_query=execution_state.request.query,  # 可以在未来支持查询优化
            total_execution_time=total_time,
            total_iterations=total_iterations,
            total_searches=execution_state.total_searches,
            cache_hits=execution_state.cache_hits,
            final_summary=execution_state.final_summary,
            final_tags=execution_state.final_tags,
            sources_used=sources_used,
            citations=citations,
            errors=execution_state.errors,
        )
        
        # 添加可观测数据
        if execution_state.request.enable_tracing:
            response.execution_trace = self.tracer.get_session_trace(session_id)
        
        if execution_state.request.enable_performance_monitoring:
            response.performance_metrics = self.performance_monitor.get_performance_summary(session_id)
        
        return response
    
    def _calculate_progress(self, execution_state: ExecutionState) -> float:
        """计算执行进度"""
        if not execution_state.plan.steps:
            return 0.0
        
        completed_steps = sum(1 for step in execution_state.plan.steps 
                            if step.status == ExecutionStatus.COMPLETED)
        
        return completed_steps / len(execution_state.plan.steps)
    
    def _get_current_step_info(self, execution_state: ExecutionState) -> Optional[Dict[str, Any]]:
        """获取当前步骤信息"""
        current_step = execution_state.plan.get_current_step()
        if not current_step:
            return None
        
        return {
            "step_id": current_step.step_id,
            "step_type": current_step.step_type.value,
            "description": current_step.description,
            "status": current_step.status.value,
        }
    
    def _request_to_dict(self, request: AgentSearchRequest) -> Dict[str, Any]:
        """将请求转换为字典"""
        return {
            "query": request.query,
            "max_iterations": request.max_iterations,
            "max_results_per_iteration": request.max_results_per_iteration,
            "total_max_results": request.total_max_results,
            "sources": [s.value for s in request.sources],
            "planning_strategy": request.planning_strategy.value,
            "enable_refinement": request.enable_refinement,
            "confidence_threshold": request.confidence_threshold,
        }
    
    async def _cleanup_session(self, session_id: str):
        """清理会话资源"""
        try:
            # 清理执行器状态
            self.executor.cleanup_session(session_id)
            
            # 延迟清理可观测数据（保留一段时间供查询）
            await asyncio.sleep(1)
            
            # 可以选择立即清理或延迟清理
            # self.tracer.cleanup_session(session_id)
            # self.performance_monitor.cleanup_session(session_id)
            # self.result_logger.cleanup_session(session_id)
            
        except Exception as e:
            logger.warning(f"清理会话资源时出错: {e}")
    
    async def close(self):
        """关闭 Search Agent"""
        logger.info("正在关闭 Search Agent...")
        
        # 这里可以添加清理逻辑
        # 例如保存重要的追踪数据、性能指标等
        
        logger.info("Search Agent 已关闭")
