"""
任务管理器

负责管理多智能体系统中的任务分配、调度和监控。
"""

from typing import Dict, List, Optional, Set
from loguru import logger

from ..base.models import AgentTask, TaskType, TaskPriority, ExecutionStatus


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, AgentTask] = {}
        self.task_queue: List[str] = []
        self.running_tasks: Set[str] = set()
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        
        logger.info("任务管理器初始化完成")
    
    def add_task(self, task: AgentTask) -> None:
        """添加任务"""
        self.tasks[task.task_id] = task
        self.task_queue.append(task.task_id)
        logger.debug(f"添加任务: {task.task_id} ({task.task_type.value})")
    
    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: ExecutionStatus) -> None:
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            
            # 更新内部状态跟踪
            if status == ExecutionStatus.RUNNING:
                self.running_tasks.add(task_id)
            elif status == ExecutionStatus.COMPLETED:
                self.running_tasks.discard(task_id)
                self.completed_tasks.add(task_id)
            elif status == ExecutionStatus.FAILED:
                self.running_tasks.discard(task_id)
                self.failed_tasks.add(task_id)
            
            logger.debug(f"任务 {task_id} 状态更新为: {status.value}")
    
    def get_pending_tasks(self) -> List[AgentTask]:
        """获取待处理任务"""
        return [
            task for task in self.tasks.values()
            if task.status == ExecutionStatus.PENDING
        ]
    
    def get_running_tasks(self) -> List[AgentTask]:
        """获取运行中任务"""
        return [
            task for task in self.tasks.values()
            if task.status == ExecutionStatus.RUNNING
        ]
    
    def get_task_statistics(self) -> Dict[str, int]:
        """获取任务统计信息"""
        return {
            "total": len(self.tasks),
            "pending": len([t for t in self.tasks.values() if t.status == ExecutionStatus.PENDING]),
            "running": len(self.running_tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
        }
