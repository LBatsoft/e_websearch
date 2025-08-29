"""
Search Agent 可观测层

提供执行追踪、性能监控、结果记录等功能
"""

import time
import json
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import asdict
from datetime import datetime
from loguru import logger

from .models import ExecutionState, ExecutionStep, ExecutionStatus, StepType


class ExecutionTracer:
    """执行追踪器 - 记录执行过程的详细信息"""
    
    def __init__(self):
        self.traces: Dict[str, List[Dict[str, Any]]] = {}
    
    def start_session(self, session_id: str, request_data: Dict[str, Any]):
        """开始会话追踪"""
        self.traces[session_id] = []
        
        trace_event = {
            "event_id": f"trace_{uuid.uuid4().hex[:8]}",
            "session_id": session_id,
            "event_type": "session_start",
            "timestamp": time.time(),
            "data": {
                "request": request_data,
                "start_time": datetime.now().isoformat(),
            }
        }
        
        self.traces[session_id].append(trace_event)
        logger.info(f"开始会话追踪: {session_id}")
    
    def trace_step_start(self, session_id: str, step: ExecutionStep):
        """追踪步骤开始"""
        if session_id not in self.traces:
            self.traces[session_id] = []
        
        trace_event = {
            "event_id": f"trace_{uuid.uuid4().hex[:8]}",
            "session_id": session_id,
            "event_type": "step_start",
            "timestamp": time.time(),
            "data": {
                "step_id": step.step_id,
                "step_type": step.step_type.value,
                "description": step.description,
                "query": step.query,
                "sources": [s.value for s in step.sources],
                "max_results": step.max_results,
            }
        }
        
        self.traces[session_id].append(trace_event)
    
    def trace_step_complete(self, session_id: str, step: ExecutionStep):
        """追踪步骤完成"""
        if session_id not in self.traces:
            return
        
        trace_event = {
            "event_id": f"trace_{uuid.uuid4().hex[:8]}",
            "session_id": session_id,
            "event_type": "step_complete",
            "timestamp": time.time(),
            "data": {
                "step_id": step.step_id,
                "status": step.status.value,
                "execution_time": step.execution_time,
                "results_count": len(step.results),
                "confidence_score": step.confidence_score,
                "error": step.error,
                "metadata": step.metadata,
            }
        }
        
        self.traces[session_id].append(trace_event)
    
    def trace_decision(self, session_id: str, decision_type: str, 
                      decision_data: Dict[str, Any]):
        """追踪决策过程"""
        if session_id not in self.traces:
            return
        
        trace_event = {
            "event_id": f"trace_{uuid.uuid4().hex[:8]}",
            "session_id": session_id,
            "event_type": "decision",
            "timestamp": time.time(),
            "data": {
                "decision_type": decision_type,
                **decision_data
            }
        }
        
        self.traces[session_id].append(trace_event)
    
    def trace_error(self, session_id: str, error_type: str, error_message: str,
                   context: Dict[str, Any] = None):
        """追踪错误"""
        if session_id not in self.traces:
            self.traces[session_id] = []
        
        trace_event = {
            "event_id": f"trace_{uuid.uuid4().hex[:8]}",
            "session_id": session_id,
            "event_type": "error",
            "timestamp": time.time(),
            "data": {
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {},
            }
        }
        
        self.traces[session_id].append(trace_event)
        logger.error(f"追踪错误 [{session_id}]: {error_type} - {error_message}")
    
    def end_session(self, session_id: str, final_state: ExecutionState):
        """结束会话追踪"""
        if session_id not in self.traces:
            return
        
        trace_event = {
            "event_id": f"trace_{uuid.uuid4().hex[:8]}",
            "session_id": session_id,
            "event_type": "session_end",
            "timestamp": time.time(),
            "data": {
                "final_status": final_state.status.value,
                "total_execution_time": final_state.total_execution_time,
                "total_results": len(final_state.all_results),
                "total_searches": final_state.total_searches,
                "cache_hits": final_state.cache_hits,
                "errors": final_state.errors,
                "end_time": datetime.now().isoformat(),
            }
        }
        
        self.traces[session_id].append(trace_event)
        logger.info(f"结束会话追踪: {session_id}")
    
    def get_session_trace(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话追踪记录"""
        return self.traces.get(session_id, [])
    
    def get_trace_summary(self, session_id: str) -> Dict[str, Any]:
        """获取追踪摘要"""
        traces = self.traces.get(session_id, [])
        if not traces:
            return {}
        
        summary = {
            "session_id": session_id,
            "total_events": len(traces),
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "steps_executed": 0,
            "errors_count": 0,
            "decisions_count": 0,
        }
        
        for trace in traces:
            event_type = trace["event_type"]
            
            if event_type == "session_start":
                summary["start_time"] = trace["timestamp"]
            elif event_type == "session_end":
                summary["end_time"] = trace["timestamp"]
            elif event_type == "step_complete":
                summary["steps_executed"] += 1
            elif event_type == "error":
                summary["errors_count"] += 1
            elif event_type == "decision":
                summary["decisions_count"] += 1
        
        if summary["start_time"] and summary["end_time"]:
            summary["duration"] = summary["end_time"] - summary["start_time"]
        
        return summary
    
    def cleanup_session(self, session_id: str):
        """清理会话追踪数据"""
        if session_id in self.traces:
            del self.traces[session_id]
            logger.info(f"清理会话追踪数据: {session_id}")


class PerformanceMonitor:
    """性能监控器 - 监控系统性能指标"""
    
    def __init__(self):
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.session_metrics: Dict[str, Dict[str, Any]] = {}
    
    def start_monitoring(self, session_id: str):
        """开始性能监控"""
        self.session_metrics[session_id] = {
            "start_time": time.time(),
            "step_times": [],
            "search_times": [],
            "llm_times": [],
            "memory_usage": [],
            "api_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        
        logger.info(f"开始性能监控: {session_id}")
    
    def record_step_performance(self, session_id: str, step: ExecutionStep):
        """记录步骤性能"""
        if session_id not in self.session_metrics:
            return
        
        metrics = self.session_metrics[session_id]
        
        if step.execution_time:
            metrics["step_times"].append({
                "step_id": step.step_id,
                "step_type": step.step_type.value,
                "execution_time": step.execution_time,
                "results_count": len(step.results),
                "timestamp": time.time(),
            })
        
        # 记录搜索时间
        if step.step_type == StepType.SEARCH and step.execution_time:
            metrics["search_times"].append(step.execution_time)
        
        # 记录API调用
        metrics["api_calls"] += 1
        
        # 记录缓存命中
        if step.metadata.get("cache_hit"):
            metrics["cache_hits"] += 1
        else:
            metrics["cache_misses"] += 1
    
    def record_llm_performance(self, session_id: str, operation: str, 
                             execution_time: float, success: bool):
        """记录LLM性能"""
        if session_id not in self.session_metrics:
            return
        
        metrics = self.session_metrics[session_id]
        metrics["llm_times"].append({
            "operation": operation,
            "execution_time": execution_time,
            "success": success,
            "timestamp": time.time(),
        })
    
    def record_memory_usage(self, session_id: str, memory_mb: float):
        """记录内存使用"""
        if session_id not in self.session_metrics:
            return
        
        metrics = self.session_metrics[session_id]
        metrics["memory_usage"].append({
            "memory_mb": memory_mb,
            "timestamp": time.time(),
        })
    
    def get_performance_summary(self, session_id: str) -> Dict[str, Any]:
        """获取性能摘要"""
        if session_id not in self.session_metrics:
            return {}
        
        metrics = self.session_metrics[session_id]
        current_time = time.time()
        
        summary = {
            "session_id": session_id,
            "total_duration": current_time - metrics["start_time"],
            "total_api_calls": metrics["api_calls"],
            "cache_hit_rate": 0.0,
            "avg_step_time": 0.0,
            "avg_search_time": 0.0,
            "avg_llm_time": 0.0,
            "peak_memory_mb": 0.0,
            "performance_score": 0.0,
        }
        
        # 计算缓存命中率
        total_cache_ops = metrics["cache_hits"] + metrics["cache_misses"]
        if total_cache_ops > 0:
            summary["cache_hit_rate"] = metrics["cache_hits"] / total_cache_ops
        
        # 计算平均步骤时间
        if metrics["step_times"]:
            step_times = [s["execution_time"] for s in metrics["step_times"]]
            summary["avg_step_time"] = sum(step_times) / len(step_times)
        
        # 计算平均搜索时间
        if metrics["search_times"]:
            summary["avg_search_time"] = sum(metrics["search_times"]) / len(metrics["search_times"])
        
        # 计算平均LLM时间
        if metrics["llm_times"]:
            llm_times = [l["execution_time"] for l in metrics["llm_times"]]
            summary["avg_llm_time"] = sum(llm_times) / len(llm_times)
        
        # 计算峰值内存
        if metrics["memory_usage"]:
            summary["peak_memory_mb"] = max(m["memory_mb"] for m in metrics["memory_usage"])
        
        # 计算性能分数
        summary["performance_score"] = self._calculate_performance_score(summary)
        
        return summary
    
    def _calculate_performance_score(self, summary: Dict[str, Any]) -> float:
        """计算性能分数"""
        score = 1.0
        
        # 基于平均步骤时间
        avg_step_time = summary.get("avg_step_time", 0)
        if avg_step_time > 10:  # 超过10秒
            score -= 0.3
        elif avg_step_time > 5:  # 超过5秒
            score -= 0.1
        
        # 基于缓存命中率
        cache_hit_rate = summary.get("cache_hit_rate", 0)
        if cache_hit_rate < 0.3:
            score -= 0.2
        elif cache_hit_rate > 0.7:
            score += 0.1
        
        # 基于总时长
        total_duration = summary.get("total_duration", 0)
        if total_duration > 60:  # 超过1分钟
            score -= 0.2
        elif total_duration > 30:  # 超过30秒
            score -= 0.1
        
        return max(min(score, 1.0), 0.0)
    
    def cleanup_session(self, session_id: str):
        """清理会话性能数据"""
        if session_id in self.session_metrics:
            del self.session_metrics[session_id]
            logger.info(f"清理会话性能数据: {session_id}")


class ResultLogger:
    """结果记录器 - 记录搜索结果和分析数据"""
    
    def __init__(self):
        self.results_log: Dict[str, Dict[str, Any]] = {}
    
    def log_search_results(self, session_id: str, step_id: str, 
                          query: str, results: List[Any], metadata: Dict[str, Any] = None):
        """记录搜索结果"""
        if session_id not in self.results_log:
            self.results_log[session_id] = {"searches": [], "analyses": []}
        
        search_log = {
            "log_id": f"search_{uuid.uuid4().hex[:8]}",
            "step_id": step_id,
            "query": query,
            "timestamp": time.time(),
            "results_count": len(results),
            "results_summary": self._summarize_results(results),
            "metadata": metadata or {},
        }
        
        self.results_log[session_id]["searches"].append(search_log)
        logger.info(f"记录搜索结果: {session_id}/{step_id}, 结果数: {len(results)}")
    
    def log_analysis_results(self, session_id: str, analysis_type: str,
                           analysis_data: Dict[str, Any]):
        """记录分析结果"""
        if session_id not in self.results_log:
            self.results_log[session_id] = {"searches": [], "analyses": []}
        
        analysis_log = {
            "log_id": f"analysis_{uuid.uuid4().hex[:8]}",
            "analysis_type": analysis_type,
            "timestamp": time.time(),
            "data": analysis_data,
        }
        
        self.results_log[session_id]["analyses"].append(analysis_log)
        logger.info(f"记录分析结果: {session_id}, 类型: {analysis_type}")
    
    def log_final_results(self, session_id: str, final_state: ExecutionState):
        """记录最终结果"""
        if session_id not in self.results_log:
            self.results_log[session_id] = {"searches": [], "analyses": []}
        
        final_log = {
            "session_id": session_id,
            "timestamp": time.time(),
            "status": final_state.status.value,
            "total_results": len(final_state.all_results),
            "final_summary": final_state.final_summary,
            "final_tags": final_state.final_tags,
            "execution_time": final_state.total_execution_time,
            "quality_metrics": self._calculate_result_quality(final_state),
        }
        
        self.results_log[session_id]["final"] = final_log
        logger.info(f"记录最终结果: {session_id}")
    
    def _summarize_results(self, results: List[Any]) -> Dict[str, Any]:
        """总结搜索结果"""
        if not results:
            return {"count": 0}
        
        summary = {
            "count": len(results),
            "sources": [],
            "avg_score": 0.0,
            "has_content_count": 0,
        }
        
        total_score = 0
        sources = set()
        
        for result in results:
            if hasattr(result, 'source'):
                source_value = result.source.value if hasattr(result.source, 'value') else str(result.source)
                sources.add(source_value)
            
            if hasattr(result, 'score'):
                total_score += result.score
            
            if hasattr(result, 'content') and result.content:
                summary["has_content_count"] += 1
        
        summary["sources"] = list(sources)
        if len(results) > 0:
            summary["avg_score"] = total_score / len(results)
        
        return summary
    
    def _calculate_result_quality(self, final_state: ExecutionState) -> Dict[str, Any]:
        """计算结果质量指标"""
        results = final_state.all_results
        
        if not results:
            return {"quality_score": 0.0, "metrics": {}}
        
        metrics = {
            "total_results": len(results),
            "unique_sources": len(set(r.source.value if hasattr(r.source, 'value') else str(r.source) for r in results)),
            "avg_score": sum(r.score for r in results) / len(results),
            "content_coverage": sum(1 for r in results if r.content) / len(results),
            "has_summary": bool(final_state.final_summary),
            "tags_count": len(final_state.final_tags),
        }
        
        # 计算质量分数
        quality_score = 0.0
        quality_score += min(metrics["total_results"] / 20, 1.0) * 0.3  # 结果数量
        quality_score += min(metrics["unique_sources"] / 3, 1.0) * 0.2   # 来源多样性
        quality_score += metrics["avg_score"] * 0.2                      # 平均分数
        quality_score += metrics["content_coverage"] * 0.2               # 内容覆盖率
        quality_score += (1.0 if metrics["has_summary"] else 0.0) * 0.1  # 有摘要
        
        return {
            "quality_score": quality_score,
            "metrics": metrics,
        }
    
    def get_session_log(self, session_id: str) -> Dict[str, Any]:
        """获取会话日志"""
        return self.results_log.get(session_id, {})
    
    def cleanup_session(self, session_id: str):
        """清理会话日志"""
        if session_id in self.results_log:
            del self.results_log[session_id]
            logger.info(f"清理会话日志: {session_id}")
