"""
多智能体搜索系统 - 主接口

这是多智能体搜索系统的主要入口点，提供统一的接口来访问
所有智能体功能和协调机制。
"""

import time
from typing import Dict, Any
from loguru import logger

from .base.models import AgentSearchRequest, AgentSearchResponse, ExecutionState, ExecutionStatus, ExecutionPlan, PlanningStrategy
from .coordination.coordinator import MultiAgentCoordinator
from .base.observability import ExecutionTracer, PerformanceMonitor, ResultLogger
from ..search_orchestrator import SearchOrchestrator


class MultiAgentSearchSystem:
    """多智能体搜索系统 - 主接口"""
    
    def __init__(self, search_orchestrator: SearchOrchestrator):
        self.search_orchestrator = search_orchestrator
        self.coordinator = MultiAgentCoordinator(search_orchestrator)
        
        # 可观测性组件
        self.tracer = ExecutionTracer()
        self.monitor = PerformanceMonitor()
        self.logger = ResultLogger()
        
        logger.info("多智能体搜索系统初始化完成")
    
    async def search(self, request: AgentSearchRequest) -> AgentSearchResponse:
        """执行多智能体搜索"""
        session_id = f"multi_agent_{request.query[:20]}_{hash(request.query) % 10000:04d}"
        
        # 开始会话追踪
        self.tracer.start_session(session_id, {
            "query": request.query,
            "sources": request.sources,
            "strategy": request.planning_strategy.value
        })
        
        # 开始性能监控
        self.monitor.start_monitoring(session_id)
        
        logger.info(f"开始多智能体搜索: {request.query} [会话: {session_id}]")
        
        response = None
        try:
            # 执行多智能体搜索
            response = await self.coordinator.execute_multi_agent_search(request)
            
            # 记录最终结果
            if hasattr(response, 'execution_state') and response.execution_state:
                self.logger.log_final_results(session_id, response.execution_state)
            else:
                logger.warning(f"响应缺少execution_state，跳过最终结果记录: {session_id}")
            
            logger.info(f"多智能体搜索完成: {session_id}, 耗时: {response.total_execution_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"多智能体搜索失败: {session_id} - {str(e)}")
            raise
        
        finally:
            # 结束会话追踪
            final_state = ExecutionState(
                session_id=session_id,
                request=request,
                plan=ExecutionPlan(
                    plan_id=f"final_{session_id}",
                    original_query=request.query,
                    strategy=request.planning_strategy,
                    steps=[]
                )
            )
            # 安全地设置状态
            if response and hasattr(response, 'success'):
                final_state.status = ExecutionStatus.COMPLETED if response.success else ExecutionStatus.FAILED
            else:
                final_state.status = ExecutionStatus.FAILED
            final_state.end_time = time.time()
            self.tracer.end_session(session_id, final_state)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "coordinator_status": "active",
            "agents": {
                agent_id: agent.get_status_summary()
                for agent_id, agent in self.coordinator.agents.items()
            },
            "performance_metrics": self.monitor.get_summary(),
            "recent_sessions": self.tracer.get_recent_sessions(limit=10)
        }
    
    async def close(self):
        """关闭多智能体系统"""
        await self.coordinator.close()
        logger.info("多智能体搜索系统已关闭")
