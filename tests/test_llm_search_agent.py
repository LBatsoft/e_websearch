"""
测试基于 LLM 的搜索智能体

测试场景包括：
1. 基本搜索功能
2. LLM 分析能力
3. 策略生成
4. 结果处理
5. 性能指标
"""

import pytest
import asyncio
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from core.agents.specialists.search_specialist import SearchSpecialistAgent
from core.agents.base.models import AgentType, TaskType, AgentTask
from core.agents.reasoning.reasoning_engine import ReasoningEngine, ProcessingStrategy
from core.search_orchestrator import SearchOrchestrator
from core.models import SearchResult, SourceType


@pytest.fixture
def mock_llm_enhancer():
    """模拟 LLM 增强器"""
    enhancer = Mock()
    
    async def mock_generate_completion(prompt: str, **kwargs):
        # 模拟 LLM 响应
        return '''
{
    "analysis": {
        "key_findings": [
            "检测到多个高质量结果",
            "存在部分重复内容",
            "来源分布较为集中"
        ],
        "quality_assessment": {
            "high_quality_ratio": 0.6,
            "content_completeness": 0.8,
            "source_diversity": 0.7
        },
        "content_analysis": {
            "main_topics": ["技术", "教程", "文档"],
            "content_types": {
                "tutorial": 0.4,
                "api_doc": 0.3,
                "general": 0.3
            }
        },
        "risks_and_challenges": [
            "部分结果可能过时",
            "需要处理重复内容"
        ]
    },
    "strategy": {
        "dedup_method": "hybrid",
        "ranking_method": "relevance",
        "quality_threshold": 0.7,
        "ranking_weights": {
            "relevance": 0.6,
            "quality": 0.2,
            "freshness": 0.1,
            "authority": 0.1
        },
        "processing_steps": [
            "hybrid_deduplication",
            "relevance_focused_ranking",
            "strict_quality_filter"
        ]
    },
    "reasoning": [
        "1. 基于结果质量分布（60%高质量），优先考虑相关性排序",
        "2. 发现重复内容，采用混合去重策略以保持信息完整性",
        "3. 设置较高质量阈值(0.7)以确保结果可靠性",
        "4. 权重配置偏向相关性(0.6)以提供最相关的结果"
    ]
}
'''
    
    enhancer.generate_completion = mock_generate_completion
    return enhancer


@pytest.fixture
def mock_search_orchestrator(mock_llm_enhancer):
    """模拟搜索协调器"""
    orchestrator = Mock()
    orchestrator.llm_enhancer = mock_llm_enhancer
    
    async def mock_search(request):
        # 模拟搜索结果
        results = [
            SearchResult(
                title="Python 高级教程",
                snippet="全面的 Python 高级特性教程...",
                url="https://example.com/python-advanced",
                content="详细的教程内容...",
                source=SourceType.ZAI,
                score=0.95
            ),
            SearchResult(
                title="Python 编程入门",
                snippet="Python 基础知识介绍...",
                url="https://example.com/python-basics",
                content="入门教程内容...",
                source=SourceType.ZAI,
                score=0.85
            ),
            # 重复内容
            SearchResult(
                title="Python 编程基础教程",
                snippet="Python 基础知识教程...",
                url="https://another.com/python-basics",
                content="相似的入门教程内容...",
                source=SourceType.BING,
                score=0.8
            ),
            SearchResult(
                title="Python API 文档",
                snippet="Python 标准库 API 文档...",
                url="https://example.com/python-api",
                content="API 文档内容...",
                source=SourceType.ZAI,
                score=0.9
            )
        ]
        
        return Mock(
            results=results,
            total_count=len(results),
            execution_time=0.5,
            sources_used=[SourceType.ZAI, SourceType.BING]
        )
    
    orchestrator.search = mock_search
    return orchestrator


@pytest.fixture
async def search_agent(mock_search_orchestrator):
    """创建搜索智能体"""
    agent = SearchSpecialistAgent("test_agent", mock_search_orchestrator)
    return agent


@pytest.mark.asyncio
async def test_basic_search(search_agent):
    """测试基本搜索功能"""
    # 创建搜索任务
    task = AgentTask(
        task_id="test_task",
        task_type=TaskType.SEARCH,
        priority=3,
        data={
            "query": "Python 高级教程",
            "max_results": 5
        }
    )
    
    # 执行搜索
    result = await search_agent.process_task(task)
    
    # 验证结果
    assert result is not None
    assert "results" in result
    assert len(result["results"]) > 0
    assert result["total_count"] > 0
    assert result["execution_time"] > 0
    
    # 验证结果处理
    assert "quality_metrics" in result
    assert "strategy_metrics" in result
    assert "processing_metrics" in result


@pytest.mark.asyncio
async def test_llm_analysis(search_agent):
    """测试 LLM 分析能力"""
    task = AgentTask(
        task_id="test_task",
        task_type=TaskType.SEARCH,
        priority=3,
        data={
            "query": "Python 高级教程",
            "max_results": 5
        }
    )
    
    # 执行搜索
    result = await search_agent.process_task(task)
    
    # 验证 LLM 指标
    assert "llm_metrics" in search_agent.performance_metrics
    metrics = search_agent.performance_metrics["llm_metrics"]
    assert metrics["fallback_count"] > 0
    
    # 验证推理过程
    reasoning = result.get("strategy_metrics", {}).get("reasoning", [])
    assert len(reasoning) > 0
    assert "由于 LLM 分析失败" in reasoning[0]


@pytest.mark.asyncio
async def test_deduplication(search_agent):
    """测试去重功能"""
    task = AgentTask(
        task_id="test_task",
        task_type=TaskType.SEARCH,
        priority=3,
        data={
            "query": "Python 教程",
            "max_results": 5
        }
    )
    
    # 执行搜索
    result = await search_agent.process_task(task)
    
    # 验证去重效果
    assert result["original_count"] > result["total_count"]
    assert result["processing_metrics"]["duplicate_count"] > 0
    
    # 验证没有重复 URL
    urls = set()
    for r in result["results"]:
        assert r.url not in urls
        urls.add(r.url)


@pytest.mark.asyncio
async def test_quality_control(search_agent):
    """测试质量控制"""
    task = AgentTask(
        task_id="test_task",
        task_type=TaskType.SEARCH,
        priority=3,
        data={
            "query": "Python 高级教程",
            "max_results": 5
        }
    )
    
    # 执行搜索
    result = await search_agent.process_task(task)
    
    # 验证质量指标
    quality_metrics = result["quality_metrics"]
    assert quality_metrics["relevance"] > 0
    assert quality_metrics["quality"] > 0
    assert quality_metrics["authority"] > 0
    assert quality_metrics["freshness"] > 0
    
    # 验证结果排序
    scores = [r.ranking_score for r in result["results"]]
    assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1))


@pytest.mark.asyncio
async def test_error_handling(search_agent):
    """测试错误处理"""
    # 模拟 LLM 失败
    with patch.object(search_agent.reasoning_engine, 'analyze_and_generate_strategy',
                     side_effect=Exception("LLM 分析失败")):
        task = AgentTask(
            task_id="test_task",
            task_type=TaskType.SEARCH,
            priority=3,
            data={
                "query": "Python 教程",
                "max_results": 5
            }
        )
        
        # 执行搜索
        result = await search_agent.process_task(task)
        
        # 验证使用了后备策略
        assert result is not None
        assert len(result["results"]) > 0
        assert search_agent.performance_metrics["llm_metrics"]["fallback_count"] > 0


@pytest.mark.asyncio
async def test_performance_metrics(search_agent):
    """测试性能指标"""
    # 执行多次搜索
    queries = ["Python 基础", "Python 高级", "Python API"]
    for query in queries:
        task = AgentTask(
            task_id=f"test_task_{query}",
            task_type=TaskType.SEARCH,
            priority=3,
            data={
                "query": query,
                "max_results": 5
            }
        )
        await search_agent.process_task(task)
    
    # 验证指标累积
    metrics = search_agent.performance_metrics
    assert metrics["avg_result_count"] > 0
    assert metrics["avg_execution_time"] > 0
    assert metrics["success_rate"] > 0
    
    # 验证质量指标
    quality_metrics = metrics["result_quality_metrics"]
    assert quality_metrics["avg_relevance"] > 0
    assert quality_metrics["avg_quality"] > 0
    
    # 验证 LLM 指标
    llm_metrics = metrics["llm_metrics"]
    assert llm_metrics["fallback_count"] >= len(queries)  # 每次查询都使用后备策略
