"""
Search Agent API 端点

提供智能搜索代理的 REST API 接口
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from loguru import logger

from core.agent import SearchAgent
from core.search_orchestrator import SearchOrchestrator
from core.models import SourceType
from core.agent.models import (
    AgentSearchRequest,
    PlanningStrategy,
    ExecutionStatus,
    StepType,
)

from .agent_models import (
    AgentSearchRequestAPI,
    AgentSearchResponseAPI,
    SearchStatusResponseAPI,
    CancelSearchResponseAPI,
    ExecutionTraceResponseAPI,
    PerformanceMetricsResponseAPI,
    ErrorResponseAPI,
    PlanningStrategyAPI,
    ExecutionStatusAPI,
    StepTypeAPI,
    SourceTypeAPI,
    ExecutionStateAPI,
    ExecutionPlanAPI,
    ExecutionStepAPI,
    AgentResultAPI,
)

# 创建路由器
agent_router = APIRouter(prefix="/agent", tags=["Search Agent"])

# 全局 Search Agent 实例
search_agent: Optional[SearchAgent] = None


def get_search_agent():
    """获取 Search Agent 实例"""
    global search_agent
    if search_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Search Agent 服务暂时不可用，请稍后重试"
        )
    return search_agent


def init_search_agent(search_orchestrator: SearchOrchestrator):
    """初始化 Search Agent"""
    global search_agent
    try:
        search_agent = SearchAgent(search_orchestrator)
        logger.info("Search Agent API 初始化成功")
    except Exception as e:
        logger.error(f"Search Agent API 初始化失败: {e}")
        search_agent = None


async def close_search_agent():
    """关闭 Search Agent"""
    global search_agent
    if search_agent:
        await search_agent.close()
        search_agent = None
        logger.info("Search Agent API 已关闭")


def convert_api_to_internal_request(api_request: AgentSearchRequestAPI) -> AgentSearchRequest:
    """转换 API 请求到内部请求"""
    # 转换源类型
    sources = []
    for source in api_request.sources:
        if source == SourceTypeAPI.BING:
            sources.append(SourceType.BING)
        elif source == SourceTypeAPI.ZAI:
            sources.append(SourceType.ZAI)
        elif source == SourceTypeAPI.WECHAT:
            sources.append(SourceType.WECHAT)
        elif source == SourceTypeAPI.ZHIHU:
            sources.append(SourceType.ZHIHU)
        elif source == SourceTypeAPI.BAIDU:
            sources.append(SourceType.BAIDU)
        else:
            sources.append(SourceType.CUSTOM)
    
    # 转换规划策略
    strategy_mapping = {
        PlanningStrategyAPI.SIMPLE: PlanningStrategy.SIMPLE,
        PlanningStrategyAPI.ITERATIVE: PlanningStrategy.ITERATIVE,
        PlanningStrategyAPI.PARALLEL: PlanningStrategy.PARALLEL,
        PlanningStrategyAPI.ADAPTIVE: PlanningStrategy.ADAPTIVE,
    }
    
    return AgentSearchRequest(
        query=api_request.query,
        max_iterations=api_request.max_iterations,
        max_results_per_iteration=api_request.max_results_per_iteration,
        total_max_results=api_request.total_max_results,
        sources=sources,
        include_content=api_request.include_content,
        llm_summary=api_request.llm_summary,
        llm_tags=api_request.llm_tags,
        llm_per_result=api_request.llm_per_result,
        llm_language=api_request.llm_language,
        model_provider=api_request.model_provider,
        model_name=api_request.model_name,
        planning_strategy=strategy_mapping.get(api_request.planning_strategy, PlanningStrategy.ADAPTIVE),
        enable_refinement=api_request.enable_refinement,
        confidence_threshold=api_request.confidence_threshold,
        enable_tracing=api_request.enable_tracing,
        enable_performance_monitoring=api_request.enable_performance_monitoring,
        timeout=api_request.timeout,
        metadata=api_request.metadata,
    )


def convert_internal_to_api_response(internal_response) -> AgentSearchResponseAPI:
    """转换内部响应到 API 响应"""
    # 转换执行状态
    execution_state_api = None
    if internal_response.execution_state:
        execution_state_api = ExecutionStateAPI(
            session_id=internal_response.execution_state.session_id,
            status=ExecutionStatusAPI(internal_response.execution_state.status.value),
            start_time=internal_response.execution_state.start_time,
            end_time=internal_response.execution_state.end_time,
            total_execution_time=internal_response.execution_state.total_execution_time,
            total_searches=internal_response.execution_state.total_searches,
            total_results_found=internal_response.execution_state.total_results_found,
            cache_hits=internal_response.execution_state.cache_hits,
            errors=internal_response.execution_state.errors,
            final_summary=internal_response.execution_state.final_summary,
            final_tags=internal_response.execution_state.final_tags,
        )
    
    # 转换执行计划
    execution_plan_api = None
    if internal_response.execution_state and internal_response.execution_state.plan:
        plan = internal_response.execution_state.plan
        steps_api = []
        
        for step in plan.steps:
            # 转换源类型
            sources_api = []
            for source in step.sources:
                if source == SourceType.BING:
                    sources_api.append(SourceTypeAPI.BING)
                elif source == SourceType.ZAI:
                    sources_api.append(SourceTypeAPI.ZAI)
                elif source == SourceType.WECHAT:
                    sources_api.append(SourceTypeAPI.WECHAT)
                elif source == SourceType.ZHIHU:
                    sources_api.append(SourceTypeAPI.ZHIHU)
                elif source == SourceType.BAIDU:
                    sources_api.append(SourceTypeAPI.BAIDU)
                else:
                    sources_api.append(SourceTypeAPI.CUSTOM)
            
            step_api = ExecutionStepAPI(
                step_id=step.step_id,
                step_type=StepTypeAPI(step.step_type.value),
                description=step.description,
                query=step.query,
                sources=sources_api,
                max_results=step.max_results,
                status=ExecutionStatusAPI(step.status.value),
                start_time=step.start_time,
                end_time=step.end_time,
                execution_time=step.execution_time,
                results_count=len(step.results),
                summary=step.summary,
                tags=step.tags,
                confidence_score=step.confidence_score,
                error=step.error,
                metadata=step.metadata,
            )
            steps_api.append(step_api)
        
        execution_plan_api = ExecutionPlanAPI(
            plan_id=plan.plan_id,
            original_query=plan.original_query,
            strategy=PlanningStrategyAPI(plan.strategy.value),
            steps=steps_api,
            created_at=plan.created_at,
            estimated_time=plan.estimated_time,
            confidence_score=plan.confidence_score,
            current_step_index=plan.current_step_index,
        )
    
    # 转换结果
    results_api = []
    for result in internal_response.results:
        # 转换源类型
        source_api = SourceTypeAPI.CUSTOM
        if hasattr(result.source, 'value'):
            source_value = result.source.value
        else:
            source_value = str(result.source)
        
        if source_value == "bing":
            source_api = SourceTypeAPI.BING
        elif source_value == "zai":
            source_api = SourceTypeAPI.ZAI
        elif source_value == "wechat":
            source_api = SourceTypeAPI.WECHAT
        elif source_value == "zhihu":
            source_api = SourceTypeAPI.ZHIHU
        elif source_value == "baidu":
            source_api = SourceTypeAPI.BAIDU
        
        # 转换步骤类型
        step_type_api = None
        if result.step_type:
            step_type_api = StepTypeAPI(result.step_type.value)
        
        # 转换 publish_time 为字符串
        publish_time_str = None
        if result.publish_time:
            if hasattr(result.publish_time, 'isoformat'):
                # datetime 对象
                publish_time_str = result.publish_time.isoformat()
            else:
                # 已经是字符串
                publish_time_str = str(result.publish_time)
        
        result_api = AgentResultAPI(
            title=result.title,
            url=result.url,
            snippet=result.snippet,
            source=source_api,
            score=result.score,
            publish_time=publish_time_str,
            author=result.author,
            content=result.content,
            images=result.images,
            relevance_score=result.relevance_score,
            confidence_score=result.confidence_score,
            found_in_step=result.found_in_step,
            step_type=step_type_api,
            llm_summary=result.llm_summary,
            labels=result.labels,
            key_insights=result.key_insights,
            citations=result.citations,
            related_results=result.related_results,
            metadata=result.metadata,
        )
        results_api.append(result_api)
    
    # 转换源类型列表
    sources_used_api = []
    for source in internal_response.sources_used:
        if hasattr(source, 'value'):
            source_value = source.value
        else:
            source_value = str(source)
        
        if source_value == "bing":
            sources_used_api.append(SourceTypeAPI.BING)
        elif source_value == "zai":
            sources_used_api.append(SourceTypeAPI.ZAI)
        elif source_value == "wechat":
            sources_used_api.append(SourceTypeAPI.WECHAT)
        elif source_value == "zhihu":
            sources_used_api.append(SourceTypeAPI.ZHIHU)
        elif source_value == "baidu":
            sources_used_api.append(SourceTypeAPI.BAIDU)
        else:
            sources_used_api.append(SourceTypeAPI.CUSTOM)
    
    return AgentSearchResponseAPI(
        success=internal_response.success,
        session_id=internal_response.session_id,
        message=internal_response.message,
        execution_state=execution_state_api,
        execution_plan=execution_plan_api,
        results=results_api,
        total_count=internal_response.total_count,
        original_query=internal_response.original_query,
        final_query=internal_response.final_query,
        total_execution_time=internal_response.total_execution_time,
        total_iterations=internal_response.total_iterations,
        total_searches=internal_response.total_searches,
        cache_hits=internal_response.cache_hits,
        final_summary=internal_response.final_summary,
        final_tags=internal_response.final_tags,
        execution_trace=internal_response.execution_trace,
        performance_metrics=internal_response.performance_metrics,
        sources_used=sources_used_api,
        citations=internal_response.citations,
        errors=internal_response.errors,
        warnings=internal_response.warnings,
        metadata=internal_response.metadata,
    )


@agent_router.post("/search", response_model=AgentSearchResponseAPI)
async def agent_search(
    request: AgentSearchRequestAPI,
    agent: SearchAgent = Depends(get_search_agent)
):
    """执行智能搜索"""
    try:
        # 转换请求
        internal_request = convert_api_to_internal_request(request)
        
        # 执行搜索
        internal_response = await agent.search(internal_request)
        
        # 转换响应
        api_response = convert_internal_to_api_response(internal_response)
        
        return api_response
        
    except Exception as e:
        logger.error(f"Agent 搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索执行失败: {str(e)}")


@agent_router.get("/search/{session_id}/status", response_model=SearchStatusResponseAPI)
async def get_search_status(
    session_id: str,
    agent: SearchAgent = Depends(get_search_agent)
):
    """获取搜索状态"""
    try:
        status = await agent.get_search_status(session_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return SearchStatusResponseAPI(
            success=True,
            session_id=session_id,
            status=ExecutionStatusAPI(status["status"]),
            progress=status["progress"],
            current_step=status["current_step"],
            results_count=status["results_count"],
            execution_time=status["execution_time"],
            errors=status["errors"],
            message="状态获取成功",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取搜索状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@agent_router.post("/search/{session_id}/cancel", response_model=CancelSearchResponseAPI)
async def cancel_search(
    session_id: str,
    agent: SearchAgent = Depends(get_search_agent)
):
    """取消搜索"""
    try:
        success = await agent.cancel_search(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在或无法取消")
        
        return CancelSearchResponseAPI(
            success=True,
            session_id=session_id,
            message="搜索已取消",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"取消搜索失败: {str(e)}")


@agent_router.get("/search/{session_id}/trace", response_model=ExecutionTraceResponseAPI)
async def get_execution_trace(
    session_id: str,
    agent: SearchAgent = Depends(get_search_agent)
):
    """获取执行追踪记录"""
    try:
        trace_events = await agent.get_execution_trace(session_id)
        trace_summary = agent.tracer.get_trace_summary(session_id)
        
        return ExecutionTraceResponseAPI(
            success=True,
            session_id=session_id,
            trace_events=trace_events,
            trace_summary=trace_summary,
        )
        
    except Exception as e:
        logger.error(f"获取执行追踪失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取追踪记录失败: {str(e)}")


@agent_router.get("/search/{session_id}/metrics", response_model=PerformanceMetricsResponseAPI)
async def get_performance_metrics(
    session_id: str,
    agent: SearchAgent = Depends(get_search_agent)
):
    """获取性能指标"""
    try:
        metrics = await agent.get_performance_metrics(session_id)
        
        return PerformanceMetricsResponseAPI(
            success=True,
            session_id=session_id,
            metrics=metrics,
        )
        
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")


@agent_router.get("/health")
async def agent_health_check():
    """Agent 健康检查"""
    try:
        agent = get_search_agent()
        
        return {
            "status": "healthy",
            "service": "Search Agent",
            "version": "1.0.0",
            "features": {
                "planning": True,
                "execution": True,
                "tools": True,
                "observability": True,
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Search Agent",
            "error": str(e),
        }
