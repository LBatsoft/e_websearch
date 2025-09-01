"""
多智能体协调器

负责协调多个智能体的工作，管理任务分配和执行流程。
"""

import time
import uuid
import asyncio
from typing import Dict, List, Optional, Any, Set
from loguru import logger

from ...search_orchestrator import SearchOrchestrator
from ..base.models import (
    AgentSearchRequest,
    AgentSearchResponse,
    ExecutionStatus,
    ExecutionState,
    ExecutionPlan,
    PlanningStrategy,
    AgentResult,
    AgentType,
    TaskType,
    TaskPriority,
    AgentTask,
    AgentMessage,
)
from ..base.base_agent import BaseAgent


class MultiAgentCoordinator:
    """多智能体协调器"""
    
    def __init__(self, search_orchestrator: SearchOrchestrator):
        self.coordinator_id = f"coordinator_{uuid.uuid4().hex[:8]}"
        self.search_orchestrator = search_orchestrator
        self.agents: Dict[str, BaseAgent] = {}
        self.tasks: Dict[str, AgentTask] = {}
        self.task_dependencies: Dict[str, Set[str]] = {}
        self.message_bus: List[AgentMessage] = []
        
        # 初始化专门化 Agents
        self._initialize_agents()
        
        logger.info(f"多智能体协调器 {self.coordinator_id} 初始化完成")
    
    def _initialize_agents(self):
        """初始化所有 Agents"""
        # 创建搜索专家（可以有多个）
        from ..specialists.search_specialist import SearchSpecialistAgent
        
        for i in range(2):  # 2个搜索专家并行工作
            agent_id = f"search_specialist_{i+1}"
            self.agents[agent_id] = SearchSpecialistAgent(agent_id, self.search_orchestrator)
        
        # TODO: 其他智能体将在后续实现
        # 创建内容分析师
        # self.agents["content_analyzer"] = ContentAnalyzerAgent("content_analyzer", self.search_orchestrator)
        
        # 创建结果综合器
        # self.agents["result_synthesizer"] = ResultSynthesizerAgent("result_synthesizer")
        
        # 创建质量评估师
        # self.agents["quality_assessor"] = QualityAssessorAgent("quality_assessor")
        
        # 启动所有 Agents
        for agent in self.agents.values():
            agent.status = ExecutionStatus.RUNNING
    
    async def execute_multi_agent_search(self, request: AgentSearchRequest) -> AgentSearchResponse:
        """执行多智能体搜索"""
        session_id = f"multi_agent_{uuid.uuid4().hex[:8]}"
        start_time = float(time.time())
        
        logger.info(f"开始多智能体搜索: {request.query} [会话: {session_id}]")
        
        try:
            # 1. 创建搜索任务
            search_tasks = await self._create_search_tasks(request)
            
            # 2. 并行执行搜索任务
            search_results = await self._execute_parallel_search(search_tasks)
            
            # 3. 简化处理：直接构建响应（后续可以添加更多处理步骤）
            response = await self._build_simple_response(
                search_results, session_id, start_time, request
            )
            
            logger.info(f"多智能体搜索完成: {session_id}, 耗时: {response.total_execution_time:.2f}s")
            return response
            
        except Exception as e:
            error_msg = f"多智能体搜索失败: {str(e)}"
            logger.error(error_msg)
            
            # 创建失败的执行计划和状态
            execution_plan = ExecutionPlan(
                plan_id=f"multi_agent_plan_{session_id}",
                original_query=request.query,
                strategy=request.planning_strategy,
                steps=[]
            )
            
            execution_state = ExecutionState(
                session_id=session_id,
                request=request,
                plan=execution_plan,
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=float(time.time()),
                total_execution_time=float(time.time()) - start_time,
                errors=[error_msg]
            )

            return AgentSearchResponse(
                success=False,
                session_id=session_id,
                message=error_msg,
                execution_state=execution_state,
                total_execution_time=float(time.time()) - start_time,
                errors=[error_msg],
            )
    
    async def _create_search_tasks(self, request: AgentSearchRequest) -> List[AgentTask]:
        """创建搜索任务"""
        tasks = []
        
        # 根据查询复杂度决定搜索策略
        if request.planning_strategy.value in ["parallel", "adaptive"]:
            # 并行搜索 - 分配给多个搜索专家
            search_specialists = [aid for aid, agent in self.agents.items() 
                                if agent.agent_type == AgentType.SEARCH_SPECIALIST]
            
            results_per_agent = request.max_results_per_iteration // len(search_specialists)
            
            for i, agent_id in enumerate(search_specialists):
                task_id = f"search_task_{i+1}_{uuid.uuid4().hex[:8]}"
                task = AgentTask(
                    task_id=task_id,
                    task_type=TaskType.SEARCH,
                    priority=TaskPriority.HIGH,
                    data={
                        "query": request.query,
                        "sources": request.sources,
                        "max_results": results_per_agent,
                    }
                )
                tasks.append(task)
                self.tasks[task_id] = task
        else:
            # 单个搜索任务
            task_id = f"search_task_{uuid.uuid4().hex[:8]}"
            task = AgentTask(
                task_id=task_id,
                task_type=TaskType.SEARCH,
                priority=TaskPriority.HIGH,
                data={
                    "query": request.query,
                    "sources": request.sources,
                    "max_results": request.max_results_per_iteration,
                }
            )
            tasks.append(task)
            self.tasks[task_id] = task
        
        return tasks
    
    async def _execute_parallel_search(self, search_tasks: List[AgentTask]) -> List[Any]:
        """并行执行搜索任务"""
        logger.info(f"并行执行 {len(search_tasks)} 个搜索任务")
        
        # 分配任务给可用的搜索专家
        available_specialists = [
            agent for agent in self.agents.values()
            if agent.agent_type == AgentType.SEARCH_SPECIALIST and agent.is_available()
        ]
        
        if len(available_specialists) == 0:
            raise RuntimeError("没有可用的搜索专家")
        
        # 并行执行任务
        tasks_and_agents = []
        for i, task in enumerate(search_tasks):
            agent = available_specialists[i % len(available_specialists)]
            tasks_and_agents.append((task, agent))
        
        # 使用 asyncio.gather 并行执行
        results = await asyncio.gather(*[
            agent.execute_task(task) for task, agent in tasks_and_agents
        ])
        
        return results
    
    async def _build_simple_response(
        self, 
        search_results: List[Any], 
        session_id: str, 
        start_time: float,
        request: AgentSearchRequest
    ) -> AgentSearchResponse:
        """构建简化的响应"""
        total_time = float(time.time()) - start_time
        
        # 合并所有搜索结果
        all_results = []
        for result_data in search_results:
            if isinstance(result_data, dict) and "results" in result_data:
                all_results.extend(result_data["results"])
        
        # 转换为 AgentResult 格式
        agent_results = []
        for result in all_results:
            agent_result = AgentResult.from_search_result(result)
            agent_results.append(agent_result)
        
        # 收集智能体思考过程
        agent_thoughts = []
        agent_metrics = {}
        
        for agent_id, agent in self.agents.items():
            # 收集决策和评估记录
            agent_thought_process = {
                "agent_id": agent_id,
                "agent_type": agent.agent_type.value,
                "decisions": agent.thought_process["decisions"],
                "evaluations": agent.thought_process["evaluations"],
                "metrics": agent.thought_process["metrics"]
            }
            agent_thoughts.append(agent_thought_process)
            
            # 收集性能指标
            agent_metrics[agent_id] = {
                "type": agent.agent_type.value,
                "metrics": agent.thought_process["metrics"],
                "task_success_rate": (
                    agent.thought_process["metrics"]["successful_tasks"] /
                    (agent.thought_process["metrics"]["successful_tasks"] + 
                     agent.thought_process["metrics"]["failed_tasks"])
                    if (agent.thought_process["metrics"]["successful_tasks"] + 
                        agent.thought_process["metrics"]["failed_tasks"]) > 0
                    else 0
                )
            }
        
        # 创建执行计划
        execution_plan = ExecutionPlan(
            plan_id=f"multi_agent_plan_{session_id}",
            original_query=request.query,
            strategy=request.planning_strategy,
            steps=[]
        )
        
        # 创建执行状态
        execution_state = ExecutionState(
            session_id=session_id,
            request=request,
            plan=execution_plan,
            status=ExecutionStatus.COMPLETED,
            start_time=start_time,
            end_time=float(time.time()),
            total_execution_time=total_time,
            total_searches=len([t for t in self.tasks.values() if t.task_type == TaskType.SEARCH]),
            total_results_found=len(agent_results),
            cache_hits=0,
        )

        # 构建响应
        response = AgentSearchResponse(
            success=True,
            session_id=session_id,
            message="多智能体搜索完成",
            execution_state=execution_state,
            results=agent_results,
            total_count=len(agent_results),
            original_query=request.query,
            final_query=request.query,
            total_execution_time=total_time,
            total_iterations=1,  # Multi-agent 是并行的，算作1次迭代
            total_searches=len([t for t in self.tasks.values() if t.task_type == TaskType.SEARCH]),
            cache_hits=0,  # TODO: 实现缓存统计
            sources_used=request.sources,
            citations=[r.url for r in agent_results],
            metadata={
                "multi_agent": True,
                "agents_used": list(self.agents.keys()),
                "task_count": len(self.tasks),
                "thought_process": {
                    "agent_thoughts": agent_thoughts,  # 智能体思考过程
                    "agent_metrics": agent_metrics,  # 智能体性能指标
                },
                "execution_summary": {
                    "total_time": total_time,
                    "total_tasks": len(self.tasks),
                    "search_tasks": len([t for t in self.tasks.values() if t.task_type == TaskType.SEARCH]),
                    "task_success_rate": len([t for t in self.tasks.values() if t.status == ExecutionStatus.COMPLETED]) / len(self.tasks) if self.tasks else 0,
                }
            }
        )
        
        return response
    
    async def close(self):
        """关闭多智能体系统"""
        logger.info("正在关闭多智能体系统...")
        
        for agent in self.agents.values():
            agent.status = ExecutionStatus.CANCELLED
        
        logger.info("多智能体系统已关闭")