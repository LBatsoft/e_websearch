"""
搜索专家智能体

专门负责执行搜索任务的智能体，具有以下能力：
- 智能搜索策略选择
- 并行多源搜索
- 搜索结果初步处理
- 搜索性能优化
"""

import time
from typing import Any, Dict, List
from loguru import logger

from ..base.base_agent import BaseAgent
from ..base.models import AgentType, TaskType, AgentTask
from ...search_orchestrator import SearchOrchestrator
from ...models import SearchRequest, SourceType


class SearchSpecialistAgent(BaseAgent):
    """搜索专家智能体"""
    
    def __init__(self, agent_id: str, search_orchestrator: SearchOrchestrator):
        super().__init__(agent_id, AgentType.SEARCH_SPECIALIST)
        self.search_orchestrator = search_orchestrator
        self.capabilities = {TaskType.SEARCH}
        
        # 搜索专家特有的性能指标
        self.performance_metrics = {
            "avg_result_count": 0,
            "avg_execution_time": 0.0,
            "success_rate": 0.0,
            "cache_hit_rate": 0.0,
            "source_performance": {},  # 各搜索源的性能统计
        }
        
        logger.info(f"搜索专家 {self.agent_id} 初始化完成")
    
    async def process_task(self, task: AgentTask) -> Any:
        """处理搜索任务"""
        if task.task_type != TaskType.SEARCH:
            raise ValueError(f"搜索专家无法处理任务类型: {task.task_type}")
        
        query = task.data.get("query")
        sources = task.data.get("sources", ["zai"])
        max_results = task.data.get("max_results", 10)
        
        # 记录搜索策略决策
        self.record_decision(
            decision_type="search_strategy",
            context={
                "query": query,
                "sources": sources,
                "max_results": max_results,
                "query_length": len(query) if query else 0,
                "source_count": len(sources)
            },
            reasoning=[
                f"分析查询: {query[:50]}..." if len(query) > 50 else f"分析查询: {query}",
                f"选择搜索源: {', '.join(sources)}",
                f"设置结果数量上限: {max_results}",
                "基于查询复杂度选择搜索策略"
            ],
            outcome="strategy_selected"
        )
        
        # 创建搜索请求
        internal_sources = []
        for source in sources:
            if isinstance(source, str):
                internal_sources.append(SourceType(source))
            elif hasattr(source, 'value'):
                internal_sources.append(SourceType(source.value))
            else:
                internal_sources.append(source)
        
        search_request = SearchRequest(
            query=query,
            max_results=max_results,
            sources=internal_sources,
            include_content=True,
            llm_summary=False,  # 由内容分析师处理
            llm_tags=False,
        )
        
        # 记录搜索前评估
        self.record_evaluation(
            target="search_preparation",
            criteria={
                "query_quality": self._evaluate_query_quality(query),
                "source_coverage": len(sources) / 3.0,  # 归一化源覆盖率
                "resource_efficiency": 1.0 if max_results <= 20 else 0.7
            },
            result=0.8,
            notes=[
                f"查询质量评估完成",
                f"计划使用 {len(sources)} 个搜索源",
                f"结果数量限制在 {max_results} 个"
            ]
        )
        
        # 执行搜索
        start_time = time.time()
        search_response = await self.search_orchestrator.search(search_request)
        execution_time = time.time() - start_time
        
        # 记录搜索交互
        self.record_interaction(
            interaction_type="search_execution",
            with_agent="search_orchestrator",
            content={
                "query": query,
                "sources": sources,
                "max_results": max_results,
                "execution_time": execution_time
            },
            result="success" if search_response.total_count > 0 else "partial_success"
        )
        
        # 记录搜索结果评估
        self.record_evaluation(
            target="search_results",
            criteria={
                "result_count": min(1.0, search_response.total_count / max_results),
                "execution_speed": 1.0 if execution_time < 2.0 else 0.5,
                "source_diversity": len(search_response.sources_used) / len(sources),
                "cache_efficiency": 1.0 if hasattr(search_response, 'from_cache') and search_response.from_cache else 0.8
            },
            result=min(1.0, search_response.total_count / max_results),
            notes=[
                f"搜索完成，获得 {search_response.total_count} 个结果",
                f"执行时间: {execution_time:.2f}秒",
                f"使用的搜索源: {', '.join(search_response.sources_used)}",
                f"平均结果质量: {self._calculate_avg_quality(search_response.results):.2f}"
            ]
        )
        
        # 更新性能指标
        self._update_search_metrics(search_response, execution_time)
        
        return {
            "results": search_response.results,
            "total_count": len(search_response.results),
            "sources_used": search_response.sources_used,
            "execution_time": execution_time,
            "cache_hit": hasattr(search_response, 'from_cache') and search_response.from_cache,
            "quality_metrics": {
                "avg_relevance": self._calculate_avg_relevance(search_response.results),
                "source_diversity": len(search_response.sources_used) / len(sources),
                "result_completeness": search_response.total_count / max_results
            }
        }
    
    def _evaluate_query_quality(self, query: str) -> float:
        """评估查询质量"""
        if not query:
            return 0.0
        
        # 基于查询长度、关键词数量等因素评估
        words = query.split()
        word_count = len(words)
        
        if word_count < 2:
            return 0.3
        elif word_count < 5:
            return 0.6
        elif word_count < 10:
            return 0.8
        else:
            return 0.9
    
    def _calculate_avg_quality(self, results: List[Any]) -> float:
        """计算平均结果质量"""
        if not results:
            return 0.0
        
        total_quality = 0.0
        for result in results:
            # 基于结果的各种属性计算质量分数
            quality = 0.5  # 基础分数
            
            if hasattr(result, 'title') and result.title:
                quality += 0.2
            if hasattr(result, 'content') and result.content:
                quality += 0.2
            if hasattr(result, 'url') and result.url:
                quality += 0.1
            
            total_quality += quality
        
        return total_quality / len(results)
    
    def _calculate_avg_relevance(self, results: List[Any]) -> float:
        """计算平均相关性"""
        if not results:
            return 0.0
        
        total_relevance = 0.0
        for result in results:
            # 如果结果有相关性分数，使用它；否则使用默认值
            relevance = getattr(result, 'relevance_score', 0.7)
            total_relevance += relevance
        
        return total_relevance / len(results)
    
    def _update_search_metrics(self, search_response, execution_time: float):
        """更新搜索性能指标"""
        metrics = self.performance_metrics
        
        # 更新平均结果数量
        current_avg_count = metrics["avg_result_count"]
        total_searches = self.thought_process["metrics"]["total_tasks"]
        metrics["avg_result_count"] = (
            (current_avg_count * (total_searches - 1) + search_response.total_count) / total_searches
            if total_searches > 0 else search_response.total_count
        )
        
        # 更新平均执行时间
        current_avg_time = metrics["avg_execution_time"]
        metrics["avg_execution_time"] = (
            (current_avg_time * (total_searches - 1) + execution_time) / total_searches
            if total_searches > 0 else execution_time
        )
        
        # 更新成功率
        successful_tasks = self.thought_process["metrics"]["successful_tasks"]
        total_tasks = self.thought_process["metrics"]["total_tasks"]
        metrics["success_rate"] = successful_tasks / total_tasks if total_tasks > 0 else 0
        
        # 更新各搜索源的性能统计
        for source in search_response.sources_used:
            if source not in metrics["source_performance"]:
                metrics["source_performance"][source] = {
                    "usage_count": 0,
                    "avg_results": 0,
                    "avg_time": 0
                }
            
            source_metrics = metrics["source_performance"][source]
            source_metrics["usage_count"] += 1
            # 这里可以添加更详细的源级别统计
    
    def get_search_performance_summary(self) -> Dict[str, Any]:
        """获取搜索性能摘要"""
        return {
            "agent_id": self.agent_id,
            "agent_type": "search_specialist",
            "performance_metrics": self.performance_metrics,
            "recent_decisions": self.thought_process["decisions"][-5:],  # 最近5个决策
            "recent_evaluations": self.thought_process["evaluations"][-3:],  # 最近3个评估
        }
