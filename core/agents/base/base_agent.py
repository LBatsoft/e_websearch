"""
基础智能体类

定义了所有智能体的基础接口和通用功能。
"""

import time
import uuid
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set
from loguru import logger

from .models import AgentType, TaskType, ExecutionStatus, AgentTask


class BaseAgent(ABC):
    """智能体基础类"""
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = ExecutionStatus.IDLE
        self.capabilities: Set[TaskType] = set()
        self.task_queue: List[AgentTask] = []
        self.current_task: AgentTask = None
        
        # 思考过程记录
        self.thought_process = {
            "decisions": [],      # 决策记录
            "evaluations": [],    # 评估记录
            "interactions": [],   # 交互记录
            "metrics": {          # 性能指标
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "avg_task_time": 0.0,
                "last_activity": float(time.time())
            }
        }
        
        logger.info(f"智能体 {self.agent_id} ({self.agent_type.value}) 初始化完成")
    
    def can_handle_task(self, task: AgentTask) -> bool:
        """检查是否能处理指定任务"""
        return task.task_type in self.capabilities
    
    def is_available(self) -> bool:
        """检查智能体是否可用"""
        return self.status in [ExecutionStatus.IDLE, ExecutionStatus.RUNNING]
    
    async def execute_task(self, task: AgentTask) -> Any:
        """执行任务的主要入口点"""
        if not self.can_handle_task(task):
            raise ValueError(f"智能体 {self.agent_id} 无法处理任务类型: {task.task_type}")
        
        self.current_task = task
        task.status = ExecutionStatus.RUNNING
        task.started_at = float(time.time())
        
        # 记录任务接受决策
        self.record_decision(
            decision_type="task_acceptance",
            context={
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "priority": task.priority.value,
                "agent_load": len(self.task_queue)
            },
            reasoning=[
                f"接受任务 {task.task_id}",
                f"任务类型: {task.task_type.value}",
                f"优先级: {task.priority.value}",
                f"当前队列长度: {len(self.task_queue)}"
            ],
            outcome="task_accepted"
        )
        
        # 记录任务评估
        self.record_evaluation(
            target=f"task_{task.task_id}",
            criteria={
                "task_complexity": self._evaluate_task_complexity(task),
                "resource_availability": self._evaluate_resource_availability(),
                "expected_success_rate": self._evaluate_expected_success_rate(task)
            },
            result=0.8,  # 示例评分
            notes=[
                f"任务 {task.task_id} 评估完成",
                f"预期执行时间: {self._estimate_execution_time(task):.2f}秒"
            ]
        )
        
        logger.info(f"Agent {self.agent_id} 开始执行任务: {task.task_id}")
        
        try:
            # 执行具体任务
            result = await self.process_task(task)
            
            # 任务成功完成
            task.status = ExecutionStatus.COMPLETED
            task.completed_at = float(time.time())
            task.result = result
            
            # 记录完成决策
            self.record_decision(
                decision_type="task_completion",
                context={
                    "task_id": task.task_id,
                    "execution_time": task.completed_at - task.started_at,
                    "result_type": type(result).__name__,
                    "success": True
                },
                reasoning=[
                    f"任务 {task.task_id} 成功完成",
                    f"执行时间: {task.completed_at - task.started_at:.2f}秒",
                    f"结果类型: {type(result).__name__}"
                ],
                outcome="success"
            )
            
            # 更新性能指标
            self._update_task_metrics(task, success=True)
            
            logger.info(f"Agent {self.agent_id} 完成任务: {task.task_id}")
            return result
            
        except Exception as e:
            # 任务执行失败
            task.status = ExecutionStatus.FAILED
            task.completed_at = float(time.time())
            task.error = str(e)
            
            # 记录失败决策
            self.record_decision(
                decision_type="task_failure",
                context={
                    "task_id": task.task_id,
                    "error": str(e),
                    "execution_time": task.completed_at - task.started_at
                },
                reasoning=[
                    f"任务 {task.task_id} 执行失败",
                    f"错误信息: {str(e)}",
                    f"执行时间: {task.completed_at - task.started_at:.2f}秒"
                ],
                outcome="failure"
            )
            
            # 更新性能指标
            self._update_task_metrics(task, success=False)
            
            logger.error(f"Agent {self.agent_id} 任务失败: {task.task_id} - {str(e)}")
            raise
        
        finally:
            self.current_task = None
    
    @abstractmethod
    async def process_task(self, task: AgentTask) -> Any:
        """处理具体任务的抽象方法，由子类实现"""
        pass
    
    def record_decision(self, decision_type: str, context: Dict[str, Any], 
                       reasoning: List[str], outcome: str):
        """记录决策过程"""
        decision = {
            "timestamp": float(time.time()),
            "type": decision_type,
            "context": context,
            "reasoning": reasoning,
            "outcome": outcome,
            "agent_id": self.agent_id
        }
        self.thought_process["decisions"].append(decision)
        logger.debug(f"Agent {self.agent_id} 记录决策: {decision_type}")
    
    def record_evaluation(self, target: str, criteria: Dict[str, float], 
                         result: float, notes: List[str]):
        """记录评估过程"""
        evaluation = {
            "timestamp": float(time.time()),
            "target": target,
            "criteria": criteria,
            "result": result,
            "notes": notes,
            "agent_id": self.agent_id
        }
        self.thought_process["evaluations"].append(evaluation)
        logger.debug(f"Agent {self.agent_id} 记录评估: {target}")
    
    def record_interaction(self, interaction_type: str, with_agent: str, 
                          content: Dict[str, Any], result: str):
        """记录交互过程"""
        interaction = {
            "timestamp": float(time.time()),
            "type": interaction_type,
            "with_agent": with_agent,
            "content": content,
            "result": result,
            "agent_id": self.agent_id
        }
        self.thought_process["interactions"].append(interaction)
        logger.debug(f"Agent {self.agent_id} 记录交互: {interaction_type} with {with_agent}")
    
    def _evaluate_task_complexity(self, task: AgentTask) -> float:
        """评估任务复杂度"""
        # 基础实现，子类可以重写
        data_size = len(str(task.data)) if task.data else 0
        if data_size < 100:
            return 0.3
        elif data_size < 1000:
            return 0.6
        else:
            return 0.9
    
    def _evaluate_resource_availability(self) -> float:
        """评估资源可用性"""
        # 基础实现，基于当前负载
        load_factor = len(self.task_queue) / 10.0  # 假设最大队列长度为10
        return max(0.1, 1.0 - load_factor)
    
    def _evaluate_expected_success_rate(self, task: AgentTask) -> float:
        """评估预期成功率"""
        # 基于历史性能
        metrics = self.thought_process["metrics"]
        total_tasks = metrics["successful_tasks"] + metrics["failed_tasks"]
        if total_tasks == 0:
            return 0.8  # 默认成功率
        return metrics["successful_tasks"] / total_tasks
    
    def _estimate_execution_time(self, task: AgentTask) -> float:
        """估算执行时间"""
        # 基于历史平均时间和任务复杂度
        base_time = self.thought_process["metrics"]["avg_task_time"]
        complexity = self._evaluate_task_complexity(task)
        return base_time * (1 + complexity)
    
    def _update_task_metrics(self, task: AgentTask, success: bool):
        """更新任务执行指标"""
        metrics = self.thought_process["metrics"]
        metrics["total_tasks"] += 1
        metrics["last_activity"] = float(time.time())
        
        task_time = task.completed_at - task.started_at
        
        if success:
            metrics["successful_tasks"] += 1
        else:
            metrics["failed_tasks"] += 1
            
        # 更新平均执行时间
        total_tasks = metrics["successful_tasks"] + metrics["failed_tasks"]
        current_avg = metrics["avg_task_time"]
        metrics["avg_task_time"] = (current_avg * (total_tasks - 1) + task_time) / total_tasks if total_tasks > 0 else task_time
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取智能体状态摘要"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "capabilities": [cap.value for cap in self.capabilities],
            "queue_length": len(self.task_queue),
            "current_task": self.current_task.task_id if self.current_task else None,
            "metrics": self.thought_process["metrics"],
            "decision_count": len(self.thought_process["decisions"]),
            "evaluation_count": len(self.thought_process["evaluations"]),
            "interaction_count": len(self.thought_process["interactions"])
        }
