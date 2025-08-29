"""
Multi Agent System 核心架构

实现多智能体协同搜索系统，包含：
- Agent 协调器 (Coordinator)
- 专门化搜索代理 (Specialized Agents)
- 通信和任务分配机制
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from loguru import logger

from ...search_orchestrator import SearchOrchestrator
from .models import (
    AgentSearchRequest,
    AgentSearchResponse,
    ExecutionState,
    ExecutionStatus,
    AgentResult,
)


class AgentType(Enum):
    """Agent 类型枚举"""
    COORDINATOR = "coordinator"          # 协调器
    SEARCH_SPECIALIST = "search_specialist"  # 搜索专家
    CONTENT_ANALYZER = "content_analyzer"    # 内容分析师
    RESULT_SYNTHESIZER = "result_synthesizer"  # 结果综合器
    QUALITY_ASSESSOR = "quality_assessor"     # 质量评估师


class TaskType(Enum):
    """任务类型枚举"""
    SEARCH = "search"
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"
    ASSESS = "assess"
    COORDINATE = "coordinate"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AgentTask:
    """Agent 任务"""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    data: Dict[str, Any]
    assigned_to: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: float = field(default_factory=lambda: 0.0)
    completed_at: float = field(default_factory=lambda: 0.0)
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)


@dataclass
class AgentMessage:
    """Agent 间消息"""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)  # 使用时间戳
    processed: bool = False


class BaseAgent:
    """基础 Agent 类"""
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = ExecutionStatus.PENDING
        self.current_task: Optional[AgentTask] = None
        self.task_queue: List[AgentTask] = []
        self.message_queue: List[AgentMessage] = []
        self.capabilities: Set[TaskType] = set()
        self.performance_metrics: Dict[str, Any] = {}
        
        # 思考过程记录
        self.thought_process = {
            "decisions": [],  # 决策记录
            "evaluations": [],  # 评估记录
            "interactions": [],  # 交互记录
            "metrics": {  # 性能指标
                "decisions_made": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "avg_task_time": 0.0,
                "total_interactions": 0
            }
        }
        
        logger.info(f"Agent {agent_id} ({agent_type.value}) 初始化完成")
    
    async def process_task(self, task: AgentTask) -> Any:
        """处理任务 - 子类需要实现"""
        raise NotImplementedError("子类必须实现 process_task 方法")
    
    async def send_message(self, receiver_id: str, message_type: str, content: Dict[str, Any]):
        """发送消息给其他 Agent"""
        message = AgentMessage(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            timestamp=float(time.time())  # 确保时间戳是浮点数
        )
        
        # 记录发送消息的交互
        self.record_interaction(
            interaction_type="message_send",
            with_agent=receiver_id,
            content={
                "message_id": message.message_id,
                "message_type": message_type,
                "content_summary": str(content)[:100] + "..." if len(str(content)) > 100 else str(content)
            },
            result="sent"
        )
        
        # 这里需要通过协调器路由消息
        logger.debug(f"Agent {self.agent_id} 发送消息给 {receiver_id}: {message_type}")
        return message
    
    async def receive_message(self, message: AgentMessage):
        """接收消息"""
        self.message_queue.append(message)
        
        # 记录接收消息的交互
        self.record_interaction(
            interaction_type="message_receive",
            with_agent=message.sender_id,
            content={
                "message_id": message.message_id,
                "message_type": message.message_type,
                "content_summary": str(message.content)[:100] + "..." if len(str(message.content)) > 100 else str(message.content)
            },
            result="received"
        )
        
        logger.debug(f"Agent {self.agent_id} 收到消息: {message.message_type}")
    
    async def execute_task(self, task: AgentTask) -> Any:
        """执行任务"""
        self.current_task = task
        task.assigned_to = self.agent_id
        task.started_at = float(time.time())  # 设置开始时间
        task.completed_at = 0.0  # 清除完成时间
        task.status = ExecutionStatus.RUNNING
        
        # 记录任务开始的决策过程
        self.record_decision(
            decision_type="task_acceptance",
            context={
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "priority": task.priority.value
            },
            reasoning=[
                f"1. 任务类型 {task.task_type.value} 在能力范围内",
                f"2. 当前状态可用，无其他进行中的任务",
                f"3. 任务优先级为 {task.priority.value}，符合处理条件"
            ],
            outcome="accepted"
        )
        
        try:
            logger.info(f"Agent {self.agent_id} 开始执行任务: {task.task_id}")
            
            # 执行任务前的评估
            self.record_evaluation(
                target=f"task_{task.task_id}",
                criteria={
                    "priority_score": task.priority.value / 4.0,  # 归一化优先级分数
                    "capability_match": 1.0 if task.task_type in self.capabilities else 0.0,
                    "resource_availability": 1.0 if self.is_available() else 0.0
                },
                result=1.0,  # 已决定执行
                notes=[
                    "任务类型匹配当前智能体能力",
                    "资源状态良好，可以执行",
                    f"任务优先级 {task.priority.value} 适合当前处理"
                ]
            )
            
            # 执行任务
            result = await self.process_task(task)
            
            # 记录执行结果
            task.result = result
            task.status = ExecutionStatus.COMPLETED
            task.completed_at = float(time.time())  # 确保时间戳是浮点数
            execution_time = task.completed_at - task.started_at
            self.update_metrics(task_success=True, task_time=execution_time)
            
            # 记录成功完成的决策过程
            self.record_decision(
                decision_type="task_completion",
                context={
                    "task_id": task.task_id,
                    "execution_time": execution_time,
                    "result_type": type(result).__name__
                },
                reasoning=[
                    "1. 任务执行完成，结果符合预期",
                    f"2. 执行耗时 {execution_time:.2f} 秒",
                    "3. 结果数据结构完整"
                ],
                outcome="success"
            )
            
            logger.info(f"Agent {self.agent_id} 完成任务: {task.task_id}")
            return result
            
        except Exception as e:
            # 记录失败情况
            task.error = str(e)
            task.status = ExecutionStatus.FAILED
            task.completed_at = float(time.time())  # 确保时间戳是浮点数
            execution_time = task.completed_at - task.started_at
            self.update_metrics(task_success=False, task_time=execution_time)
            
            self.record_decision(
                decision_type="task_error",
                context={
                    "task_id": task.task_id,
                    "error": str(e),
                    "execution_time": execution_time
                },
                reasoning=[
                    "1. 任务执行过程中遇到异常",
                    f"2. 错误类型: {type(e).__name__}",
                    "3. 需要终止执行并报告错误"
                ],
                outcome="failure"
            )
            
            logger.error(f"Agent {self.agent_id} 任务失败: {task.task_id} - {e}")
            raise
        finally:
            self.current_task = None
    
    def can_handle_task(self, task: AgentTask) -> bool:
        """检查是否能处理任务"""
        return task.task_type in self.capabilities
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.current_task is None and self.status == ExecutionStatus.RUNNING

    def record_decision(self, decision_type: str, context: Dict[str, Any], reasoning: List[str], outcome: str):
        """记录决策过程"""
        decision = {
            "timestamp": float(time.time()),  # 确保时间戳是浮点数
            "type": decision_type,
            "context": context,
            "reasoning": reasoning,
            "outcome": outcome
        }
        self.thought_process["decisions"].append(decision)
        self.thought_process["metrics"]["decisions_made"] += 1
        logger.debug(f"Agent {self.agent_id} 记录决策: {decision_type}")
    
    def record_evaluation(self, target: str, criteria: Dict[str, float], result: float, notes: List[str]):
        """记录评估过程"""
        evaluation = {
            "timestamp": float(time.time()),  # 确保时间戳是浮点数
            "target": target,
            "criteria": criteria,
            "result": result,
            "notes": notes
        }
        self.thought_process["evaluations"].append(evaluation)
        logger.debug(f"Agent {self.agent_id} 记录评估: {target}")
    
    def record_interaction(self, interaction_type: str, with_agent: str, content: Dict[str, Any], result: str):
        """记录交互过程"""
        interaction = {
            "timestamp": float(time.time()),  # 确保时间戳是浮点数
            "type": interaction_type,
            "with_agent": with_agent,
            "content": content,
            "result": result
        }
        self.thought_process["interactions"].append(interaction)
        self.thought_process["metrics"]["total_interactions"] += 1
        logger.debug(f"Agent {self.agent_id} 记录交互: {interaction_type} with {with_agent}")
    
    def update_metrics(self, task_success: bool, task_time: float):
        """更新性能指标"""
        metrics = self.thought_process["metrics"]
        if task_success:
            metrics["successful_tasks"] += 1
        else:
            metrics["failed_tasks"] += 1
            
        total_tasks = metrics["successful_tasks"] + metrics["failed_tasks"]
        current_avg = metrics["avg_task_time"]
        metrics["avg_task_time"] = (current_avg * (total_tasks - 1) + task_time) / total_tasks if total_tasks > 0 else task_time


class SearchSpecialistAgent(BaseAgent):
    """搜索专家 Agent - 简化版本"""
    
    def __init__(self, agent_id: str, search_orchestrator: SearchOrchestrator):
        super().__init__(agent_id, AgentType.SEARCH_SPECIALIST)
        self.search_orchestrator = search_orchestrator
        self.capabilities = {TaskType.SEARCH}
    
    async def process_task(self, task: AgentTask) -> Any:
        """处理搜索任务"""
        if task.task_type != TaskType.SEARCH:
            raise ValueError(f"SearchSpecialist 无法处理任务类型: {task.task_type}")
        
        query = task.data.get("query")
        sources = task.data.get("sources", ["zai"])
        max_results = task.data.get("max_results", 10)
        
        # 创建搜索请求
        from ...models import SearchRequest, SourceType
        
        internal_sources = [
            SourceType(source) if isinstance(source, str) else source
            for source in sources
        ]
        
        search_request = SearchRequest(
            query=query,
            max_results=max_results,
            sources=internal_sources,
            include_content=True,
            llm_summary=False,
            llm_tags=False,
        )
        
        # 执行搜索
        search_response = await self.search_orchestrator.search(search_request)
        
        return {
            "results": search_response.results,
            "total_count": len(search_response.results),
            "sources_used": search_response.sources_used,
        }


class ContentAnalyzerAgent(BaseAgent):
    """内容分析师 Agent - 简化版本"""
    
    def __init__(self, agent_id: str, search_orchestrator: SearchOrchestrator):
        super().__init__(agent_id, AgentType.CONTENT_ANALYZER)
        self.llm_enhancer = search_orchestrator.llm_enhancer
        self.capabilities = {TaskType.ANALYZE}
    
    async def process_task(self, task: AgentTask) -> Any:
        """处理内容分析任务"""
        if task.task_type != TaskType.ANALYZE:
            raise ValueError(f"ContentAnalyzer 无法处理任务类型: {task.task_type}")
        
        results = task.data.get("results", [])
        query = task.data.get("query", "")
        
        logger.info(f"内容分析师 {self.agent_id} 分析 {len(results)} 个结果")
        
        # 简化处理：直接返回结果
        return {
            "analyzed_results": results,
            "analysis_count": len(results),
        }


class ResultSynthesizerAgent(BaseAgent):
    """结果综合器 Agent - 简化版本"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.RESULT_SYNTHESIZER)
        self.capabilities = {TaskType.SYNTHESIZE}
    
    async def process_task(self, task: AgentTask) -> Any:
        """处理结果综合任务"""
        if task.task_type != TaskType.SYNTHESIZE:
            raise ValueError(f"ResultSynthesizer 无法处理任务类型: {task.task_type}")
        
        all_results = task.data.get("all_results", [])
        max_results = task.data.get("max_results", 10)
        
        logger.info(f"结果综合器 {self.agent_id} 处理 {len(all_results)} 个结果")
        
        # 简化处理：取前N个结果
        synthesized_results = all_results[:max_results]
        
        return {
            "synthesized_results": synthesized_results,
        }


class QualityAssessorAgent(BaseAgent):
    """质量评估师 Agent - 简化版本"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.QUALITY_ASSESSOR)
        self.capabilities = {TaskType.ASSESS}
    
    async def process_task(self, task: AgentTask) -> Any:
        """处理质量评估任务"""
        if task.task_type != TaskType.ASSESS:
            raise ValueError(f"QualityAssessor 无法处理任务类型: {task.task_type}")
        
        results = task.data.get("results", [])
        
        logger.info(f"质量评估师 {self.agent_id} 评估 {len(results)} 个结果")
        
        # 简化处理：为每个结果添加基本评估
        assessed_results = []
        for result in results:
            if not hasattr(result, 'metadata'):
                result.metadata = {}
            result.metadata.update({
                "quality_score": 0.8,
                "relevance_score": 0.7,
                "assessment_time": float(time.time())
            })
            assessed_results.append(result)
        
        return {
            "assessed_results": assessed_results,
            "quality_metrics": {
                "total_assessed": len(assessed_results),
                "avg_quality_score": 0.8,
                "avg_relevance_score": 0.7,
            }
        }


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
        for i in range(2):  # 2个搜索专家并行工作
            agent_id = f"search_specialist_{i+1}"
            self.agents[agent_id] = SearchSpecialistAgent(agent_id, self.search_orchestrator)
        
        # 创建内容分析师
        self.agents["content_analyzer"] = ContentAnalyzerAgent("content_analyzer", self.search_orchestrator)
        
        # 创建结果综合器
        self.agents["result_synthesizer"] = ResultSynthesizerAgent("result_synthesizer")
        
        # 创建质量评估师
        self.agents["quality_assessor"] = QualityAssessorAgent("quality_assessor")
        
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
            
            # 3. 内容分析任务
            analysis_task = await self._create_analysis_task(search_results, request.query)
            analyzed_results = await self._execute_task(analysis_task)
            
            # 4. 结果综合任务
            synthesis_task = await self._create_synthesis_task(
                analyzed_results["analyzed_results"], 
                request.query, 
                request.total_max_results
            )
            synthesized_results = await self._execute_task(synthesis_task)
            
            # 5. 质量评估任务
            assessment_task = await self._create_assessment_task(
                synthesized_results["synthesized_results"], 
                request.query
            )
            final_assessment = await self._execute_task(assessment_task)
            
            # 6. 构建响应
            response = await self._build_multi_agent_response(
                final_assessment, session_id, start_time, request
            )
            
            logger.info(f"多智能体搜索完成: {session_id}, 耗时: {response.total_execution_time:.2f}s")
            return response
            
        except Exception as e:
            error_msg = f"多智能体搜索失败: {str(e)}"
            logger.error(error_msg)
            
            return AgentSearchResponse(
                success=False,
                session_id=session_id,
                message=error_msg,
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
    
    async def _create_analysis_task(self, search_results: List[Any], query: str) -> AgentTask:
        """创建内容分析任务"""
        # 合并所有搜索结果
        all_results = []
        for result_data in search_results:
            if isinstance(result_data, dict) and "results" in result_data:
                all_results.extend(result_data["results"])
        
        task_id = f"analysis_task_{uuid.uuid4().hex[:8]}"
        task = AgentTask(
            task_id=task_id,
            task_type=TaskType.ANALYZE,
            priority=TaskPriority.MEDIUM,
            data={
                "results": all_results,
                "query": query,
            }
        )
        
        self.tasks[task_id] = task
        return task
    
    async def _create_synthesis_task(self, analyzed_results: List[Any], query: str, max_results: int) -> AgentTask:
        """创建结果综合任务"""
        task_id = f"synthesis_task_{uuid.uuid4().hex[:8]}"
        task = AgentTask(
            task_id=task_id,
            task_type=TaskType.SYNTHESIZE,
            priority=TaskPriority.MEDIUM,
            data={
                "all_results": analyzed_results,
                "query": query,
                "max_results": max_results,
            }
        )
        
        self.tasks[task_id] = task
        return task
    
    async def _create_assessment_task(self, synthesized_results: List[Any], query: str) -> AgentTask:
        """创建质量评估任务"""
        task_id = f"assessment_task_{uuid.uuid4().hex[:8]}"
        task = AgentTask(
            task_id=task_id,
            task_type=TaskType.ASSESS,
            priority=TaskPriority.LOW,
            data={
                "results": synthesized_results,
                "query": query,
            }
        )
        
        self.tasks[task_id] = task
        return task
    
    async def _execute_task(self, task: AgentTask) -> Any:
        """执行单个任务"""
        # 找到能处理该任务的可用 Agent
        suitable_agents = [
            agent for agent in self.agents.values()
            if agent.can_handle_task(task) and agent.is_available()
        ]
        
        if not suitable_agents:
            raise RuntimeError(f"没有可用的 Agent 处理任务类型: {task.task_type}")
        
        # 选择第一个可用的 Agent
        agent = suitable_agents[0]
        result = await agent.execute_task(task)
        
        return result
    
    async def _build_multi_agent_response(
        self, 
        final_assessment: Dict[str, Any], 
        session_id: str, 
        start_time: float,
        request: AgentSearchRequest
    ) -> AgentSearchResponse:
        """构建多智能体响应"""
        total_time = float(time.time()) - start_time
        
        assessed_results = final_assessment.get("assessed_results", [])
        quality_metrics = final_assessment.get("quality_metrics", {})
        
        # 收集所有智能体的思考过程
        agent_thoughts = []
        agent_interactions = []
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
            
            # 收集交互记录
            agent_interactions.extend([
                {**interaction, "agent_id": agent_id}
                for interaction in agent.thought_process["interactions"]
            ])
            
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
        
        # 转换为 AgentResult 格式
        agent_results = []
        for result in assessed_results:
            agent_result = AgentResult.from_search_result(result)
            
            # 从metadata中提取置信度和相关性分数
            metadata = getattr(result, 'metadata', {}) or {}
            agent_result.confidence_score = metadata.get('quality_score', 0.0)
            agent_result.relevance_score = metadata.get('relevance_score', 0.0)
            
            agent_results.append(agent_result)
        
        # 构建响应
        response = AgentSearchResponse(
            success=True,
            session_id=session_id,
            message="多智能体搜索完成",
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
                "quality_metrics": quality_metrics,
                "task_count": len(self.tasks),
                "thought_process": {
                    "agent_thoughts": agent_thoughts,  # 智能体思考过程
                    "agent_interactions": agent_interactions,  # 智能体交互记录
                    "agent_metrics": agent_metrics,  # 智能体性能指标
                },
                "execution_summary": {
                    "total_time": total_time,
                    "total_tasks": len(self.tasks),
                    "search_tasks": len([t for t in self.tasks.values() if t.task_type == TaskType.SEARCH]),
                    "analyze_tasks": len([t for t in self.tasks.values() if t.task_type == TaskType.ANALYZE]),
                    "synthesize_tasks": len([t for t in self.tasks.values() if t.task_type == TaskType.SYNTHESIZE]),
                    "assess_tasks": len([t for t in self.tasks.values() if t.task_type == TaskType.ASSESS]),
                    "task_success_rate": len([t for t in self.tasks.values() if t.status == ExecutionStatus.COMPLETED]) / len(self.tasks) if self.tasks else 0,
                    "parallel_efficiency": total_time / (sum(t.completed_at - t.started_at for t in self.tasks.values() if t.completed_at > 0 and t.started_at > 0) or 1)
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