"""
Multi Agent Search System - 主入口

整合多智能体系统，提供统一的搜索接口
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any
from loguru import logger

from ...search_orchestrator import SearchOrchestrator
from .models import (
    AgentSearchRequest,
    AgentSearchResponse,
    ExecutionStatus,
)
from .multi_agent_system import MultiAgentCoordinator
from .observability import ExecutionTracer, PerformanceMonitor, ResultLogger


class MultiAgentSearchSystem:
    """多智能体搜索系统 - 主接口"""
    
    def __init__(self, search_orchestrator: SearchOrchestrator):
        self.search_orchestrator = search_orchestrator
        self.coordinator = MultiAgentCoordinator(search_orchestrator)
        
        # 可观测组件
        self.tracer = ExecutionTracer()
        self.performance_monitor = PerformanceMonitor()
        self.result_logger = ResultLogger()
        
        # 系统状态
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("多智能体搜索系统初始化完成")
    
    async def search(self, request: AgentSearchRequest) -> AgentSearchResponse:
        """执行多智能体搜索"""
        session_id = f"multi_agent_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        logger.info(f"开始多智能体搜索: {request.query} [会话: {session_id}]")
        
        # 记录会话信息
        self.active_sessions[session_id] = {
            "request": request,
            "start_time": start_time,
            "status": ExecutionStatus.RUNNING,
        }
        
        # 初始化可观测组件
        if request.enable_tracing:
            self.tracer.start_session(session_id, self._request_to_dict(request))
        
        if request.enable_performance_monitoring:
            self.performance_monitor.start_monitoring(session_id)
        
        try:
            # 执行多智能体搜索
            response = await self.coordinator.execute_multi_agent_search(request)
            
            # 更新会话状态
            self.active_sessions[session_id]["status"] = ExecutionStatus.COMPLETED
            self.active_sessions[session_id]["response"] = response
            
            # 记录最终结果
            if request.enable_tracing:
                # 为Multi Agent创建简化的执行状态用于日志记录
                from .models import ExecutionState, ExecutionPlan
                mock_execution_state = ExecutionState(
                    session_id=session_id,
                    request=request,
                    plan=ExecutionPlan(
                        plan_id=f"multi_agent_{session_id}",
                        original_query=request.query,
                        strategy=request.planning_strategy,
                        steps=[]
                    ),
                    status=ExecutionStatus.COMPLETED,
                    all_results=[],  # Multi Agent的结果已经在response中
                    final_summary=response.final_summary,
                    final_tags=response.final_tags,
                )
                
                self.result_logger.log_final_results(session_id, mock_execution_state)
                self.tracer.end_session(session_id, mock_execution_state)
            
            # 添加可观测数据
            if request.enable_tracing:
                response.execution_trace = self.tracer.get_session_trace(session_id)
            
            if request.enable_performance_monitoring:
                response.performance_metrics = self.performance_monitor.get_performance_summary(session_id)
            
            logger.info(f"多智能体搜索完成: {session_id}, 耗时: {response.total_execution_time:.2f}s")
            return response
            
        except Exception as e:
            error_msg = f"多智能体搜索失败: {str(e)}"
            logger.error(error_msg)
            
            # 更新会话状态
            self.active_sessions[session_id]["status"] = ExecutionStatus.FAILED
            self.active_sessions[session_id]["error"] = error_msg
            
            if request.enable_tracing:
                self.tracer.trace_error(session_id, "multi_agent_search_failed", error_msg)
            
            # 返回错误响应
            return AgentSearchResponse(
                success=False,
                session_id=session_id,
                message=error_msg,
                total_execution_time=time.time() - start_time,
                errors=[error_msg],
                metadata={"multi_agent": True, "error": True},
            )
        
        finally:
            # 清理会话资源
            await self._cleanup_session(session_id)
    
    async def get_search_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取搜索状态"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            return None
        
        status = {
            "session_id": session_id,
            "status": session_info["status"].value,
            "start_time": session_info["start_time"],
            "execution_time": time.time() - session_info["start_time"],
            "multi_agent": True,
            "active_agents": list(self.coordinator.agents.keys()),
            "task_count": len(self.coordinator.tasks),
            "completed_tasks": len([
                t for t in self.coordinator.tasks.values() 
                if t.status == ExecutionStatus.COMPLETED
            ]),
            "failed_tasks": len([
                t for t in self.coordinator.tasks.values() 
                if t.status == ExecutionStatus.FAILED
            ]),
        }
        
        # 添加结果信息（如果有）
        if "response" in session_info:
            response = session_info["response"]
            status.update({
                "results_count": response.total_count,
                "success": response.success,
            })
        
        return status
    
    async def cancel_search(self, session_id: str) -> bool:
        """取消搜索"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            return False
        
        # 取消所有相关任务
        for task in self.coordinator.tasks.values():
            if task.status == ExecutionStatus.RUNNING:
                task.status = ExecutionStatus.CANCELLED
        
        # 更新会话状态
        session_info["status"] = ExecutionStatus.CANCELLED
        
        if session_info["request"].enable_tracing:
            self.tracer.trace_decision(session_id, "search_cancelled", {
                "cancelled_at": time.time(),
                "reason": "user_request",
            })
        
        logger.info(f"多智能体搜索已取消: {session_id}")
        return True
    
    async def get_execution_trace(self, session_id: str) -> List[Dict[str, Any]]:
        """获取执行追踪记录"""
        return self.tracer.get_session_trace(session_id)
    
    async def get_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """获取性能指标"""
        base_metrics = self.performance_monitor.get_performance_summary(session_id)
        
        # 添加多智能体特定指标
        session_info = self.active_sessions.get(session_id)
        if session_info:
            multi_agent_metrics = {
                "multi_agent": True,
                "total_agents": len(self.coordinator.agents),
                "active_agents": len([
                    a for a in self.coordinator.agents.values() 
                    if a.status == ExecutionStatus.RUNNING
                ]),
                "total_tasks": len(self.coordinator.tasks),
                "completed_tasks": len([
                    t for t in self.coordinator.tasks.values() 
                    if t.status == ExecutionStatus.COMPLETED
                ]),
                "failed_tasks": len([
                    t for t in self.coordinator.tasks.values() 
                    if t.status == ExecutionStatus.FAILED
                ]),
                "parallel_efficiency": self._calculate_parallel_efficiency(),
            }
            
            base_metrics.update(multi_agent_metrics)
        
        return base_metrics
    
    def _calculate_parallel_efficiency(self) -> float:
        """计算并行效率"""
        completed_tasks = [
            t for t in self.coordinator.tasks.values() 
            if t.status == ExecutionStatus.COMPLETED and t.started_at and t.completed_at
        ]
        
        if len(completed_tasks) < 2:
            return 1.0
        
        # 计算总执行时间 vs 并行执行时间
        total_execution_time = sum(
            t.completed_at - t.started_at for t in completed_tasks
        )
        
        earliest_start = min(t.started_at for t in completed_tasks)
        latest_end = max(t.completed_at for t in completed_tasks)
        parallel_time = latest_end - earliest_start
        
        if parallel_time > 0:
            efficiency = total_execution_time / (parallel_time * len(completed_tasks))
            return min(efficiency, 1.0)
        
        return 1.0
    
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
            "multi_agent": True,
        }
    
    async def _cleanup_session(self, session_id: str):
        """清理会话资源"""
        try:
            # 延迟清理会话数据（保留一段时间供查询）
            await asyncio.sleep(1)
            
            # 可以选择立即清理或延迟清理
            # if session_id in self.active_sessions:
            #     del self.active_sessions[session_id]
            
        except Exception as e:
            logger.warning(f"清理会话资源时出错: {e}")
    
    async def close(self):
        """关闭多智能体搜索系统"""
        logger.info("正在关闭多智能体搜索系统...")
        
        # 关闭协调器
        await self.coordinator.close()
        
        # 清理所有会话
        self.active_sessions.clear()
        
        logger.info("多智能体搜索系统已关闭")
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "system_type": "multi_agent",
            "total_agents": len(self.coordinator.agents),
            "agent_types": list(set(a.agent_type.value for a in self.coordinator.agents.values())),
            "active_sessions": len(self.active_sessions),
            "capabilities": [
                "parallel_search",
                "content_analysis", 
                "result_synthesis",
                "quality_assessment",
                "real_time_coordination",
            ],
            "coordinator_id": self.coordinator.coordinator_id,
        }
