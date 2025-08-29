"""
E-WebSearch API 服务主入口
"""

from contextlib import asynccontextmanager
import os
from pathlib import Path

# 导入本地模块
import sys
import time
import traceback
from typing import List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 加载环境变量
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    print(f"📁 加载环境配置: {env_path}")
    load_dotenv(env_path)
else:
    print("⚠️  未找到 .env 文件，使用默认配置")

from core.models import SearchRequest, SourceType
from core.search_orchestrator import SearchOrchestrator
from core.agents.legacy.search_agent import SearchAgent
from core.llm_enhancer import LLMEnhancer

from .models import (
    AgentSearchRequest,
    AgentSearchResponse,
    CacheOperationResponse,
    ErrorResponse,
    HealthCheckResponse,
    SearchRequestAPI,
    SearchResponseAPI,
    SearchResultAPI,
    SourceTypeAPI,
    StatisticsResponse,
    SuggestionsRequest,
    SuggestionsResponse,
)

# 导入 Agent API 路由和变量
from .agent_api import (
    agent_router, init_search_agent, close_search_agent,
    search_agent, multi_agent_system
)

# 全局变量
search_orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global search_orchestrator, search_agent

    # 启动时初始化
    print("🚀 初始化 E-WebSearch API 服务...")
    try:
        search_orchestrator = SearchOrchestrator()
        # 初始化 Agent API
        init_search_agent(search_orchestrator)
        print("✅ 搜索协调器和搜索代理初始化成功")
    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        traceback.print_exc()
        search_orchestrator = None

    yield

    # 关闭时清理
    print("🔄 关闭 E-WebSearch API 服务...")
    await close_search_agent()
    if search_orchestrator:
        await search_orchestrator.close()
        print("✅ 搜索协调器已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="E-WebSearch API",
    description="基于 ZAI Search Pro 的增强版 Web 搜索 API 服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含 Agent API 路由
app.include_router(agent_router)


def get_orchestrator():
    """获取搜索协调器实例"""
    if search_orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="搜索服务暂时不可用，请稍后重试",
        )
    return search_orchestrator


def get_agent():
    """获取搜索代理实例"""
    from .agent_api import search_agent
    if search_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="搜索代理服务暂时不可用，请稍后重试",
        )
    return search_agent


def convert_source_type(source: SourceTypeAPI):
    """转换 API 源类型到内部源类型"""
    if "SourceType" not in globals():
        # 如果 SourceType 未定义，返回字符串值
        return source.value

    mapping = {
        SourceTypeAPI.BING: SourceType.BING,
        SourceTypeAPI.ZAI: SourceType.ZAI,
        SourceTypeAPI.WECHAT: SourceType.WECHAT,
        SourceTypeAPI.ZHIHU: SourceType.ZHIHU,
        SourceTypeAPI.BAIDU: SourceType.BAIDU,
        SourceTypeAPI.CUSTOM: SourceType.CUSTOM,
    }
    return mapping[source]


def convert_api_source_type(source) -> SourceTypeAPI:
    """转换内部源类型到 API 源类型"""
    if isinstance(source, str):
        # 特殊处理 mock 源
        if source == "mock":
            return SourceTypeAPI.CUSTOM
        # 如果是字符串，直接转换
        try:
            return SourceTypeAPI(source)
        except ValueError:
            # 如果无法转换，返回自定义类型
            return SourceTypeAPI.CUSTOM

    if "SourceType" not in globals():
        return SourceTypeAPI.CUSTOM

    mapping = {
        SourceType.BING: SourceTypeAPI.BING,
        SourceType.ZAI: SourceTypeAPI.ZAI,
        SourceType.WECHAT: SourceTypeAPI.WECHAT,
        SourceType.ZHIHU: SourceTypeAPI.ZHIHU,
        SourceType.BAIDU: SourceTypeAPI.BAIDU,
        SourceType.CUSTOM: SourceTypeAPI.CUSTOM,
    }
    return mapping.get(source, SourceTypeAPI.CUSTOM)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    error_detail = str(exc)
    error_traceback = traceback.format_exc()

    print(f"❌ API 错误: {error_detail}")
    print(f"📍 错误堆栈: {error_traceback}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="服务器内部错误",
            details={"error": error_detail},
        ).dict(),
    )


@app.get("/", response_model=dict)
async def root():
    """根路径 - API 信息"""
    return {
        "name": "E-WebSearch API",
        "version": "1.0.0",
        "description": "基于 ZAI Search Pro 的增强版 Web 搜索 API 服务",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "search": "/search",
            "health": "/health",
            "suggestions": "/suggestions",
            "statistics": "/statistics",
            "cache": "/cache",
        },
    }


@app.post("/search", response_model=SearchResponseAPI)
async def search(request: SearchRequestAPI, orchestrator=Depends(get_orchestrator)):
    """执行搜索"""
    try:
        start_time = time.time()

        # 转换 API 请求到内部请求
        internal_sources = [convert_source_type(source) for source in request.sources]

        if "SearchRequest" in globals() and SearchRequest:
            internal_request = SearchRequest(
                query=request.query,
                max_results=request.max_results,
                include_content=request.include_content,
                sources=internal_sources,
                filters=request.filters,
                llm_summary=request.llm_summary,
                llm_tags=request.llm_tags,
                llm_per_result=request.llm_per_result,
                llm_max_items=request.llm_max_items,
                llm_language=request.llm_language,
                model_provider=request.model_provider,
                model_name=request.model_name,
            )
        else:
            # 如果 SearchRequest 不可用，创建简单的字典结构
            internal_request = {
                "query": request.query,
                "max_results": request.max_results,
                "include_content": request.include_content,
                "sources": internal_sources,
                "filters": request.filters,
                "llm_summary": request.llm_summary,
                "llm_tags": request.llm_tags,
                "llm_per_result": request.llm_per_result,
                "llm_max_items": request.llm_max_items,
                "llm_language": request.llm_language,
                "model_provider": request.model_provider,
                "model_name": request.model_name,
            }

        # 执行搜索
        response = await orchestrator.search(internal_request)

        # 处理响应（可能是字典或对象）
        if isinstance(response, dict):
            # 处理字典响应（模拟搜索）
            results_data = response.get("results", [])
            api_results = []

            for result in results_data:
                if isinstance(result, dict):
                    api_result = SearchResultAPI(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        snippet=result.get("snippet", ""),
                        source=convert_api_source_type(result.get("source", "mock")),
                        score=result.get("score", 0.0),
                        publish_time=result.get("publish_time"),
                        author=result.get("author"),
                        content=result.get("content"),
                        images=result.get("images", []),
                        metadata=result.get("metadata", {}),
                        llm_summary=result.get("llm_summary"),
                        labels=result.get("labels", []),
                    )
                    api_results.append(api_result)

            api_sources_used = [
                convert_api_source_type(source)
                for source in response.get("sources_used", [])
            ]

            return SearchResponseAPI(
                success=response.get("success", True),
                message="搜索完成",
                results=api_results,
                total_count=response.get("total_count", len(api_results)),
                query=response.get("query", request.query),
                execution_time=response.get("execution_time", 0.0),
                sources_used=api_sources_used,
                cache_hit=response.get("cache_hit", False),
                llm_summary=response.get("llm_summary"),
                llm_tags=response.get("llm_tags", []),
                llm_per_result=response.get("llm_per_result", {}),
            )
        else:
            # 处理对象响应（真实搜索）
            api_results = []
            for result in response.results:
                api_result = SearchResultAPI(
                    title=result.title,
                    url=result.url,
                    snippet=result.snippet,
                    source=convert_api_source_type(result.source),
                    score=result.score,
                    publish_time=result.publish_time,
                    author=result.author,
                    content=result.content,
                    images=result.images,
                    metadata=result.metadata,
                    llm_summary=result.llm_summary,
                    labels=result.labels or [],
                )
                api_results.append(api_result)

            api_sources_used = [
                convert_api_source_type(source) for source in response.sources_used
            ]

            return SearchResponseAPI(
                success=True,
                message="搜索完成",
                results=api_results,
                total_count=response.total_count,
                query=response.query,
                execution_time=response.execution_time,
                sources_used=api_sources_used,
                cache_hit=response.cache_hit,
                llm_summary=response.llm_summary,
                llm_tags=response.llm_tags or [],
                llm_per_result=response.llm_per_result or {},
            )

    except Exception as e:
        error_message = f"搜索执行失败: {str(e)}"
        print(f"❌ {error_message}")

        return SearchResponseAPI(
            success=False,
            message=error_message,
            results=[],
            total_count=0,
            query=request.query,
            execution_time=time.time() - start_time,
            sources_used=[],
            cache_hit=False,
        )


@app.post("/agent_search", response_model=AgentSearchResponse)
async def agent_search(
    request: AgentSearchRequest, agent: SearchAgent = Depends(get_agent)
):
    """
    使用 Agent 模式执行复杂的研究任务
    """
    try:
        response = await agent.search(request)
        return response
    except Exception as e:
        error_message = f"Agent search failed: {str(e)}"
        print(f"❌ {error_message}")
        traceback.print_exc()
        return AgentSearchResponse(
            success=False,
            final_answer="",
            intermediate_steps=[],
            query=request.query,
            execution_time=0, # This might need adjustment
            error_message=error_message,
        )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check(orchestrator=Depends(get_orchestrator)):
    """健康检查"""
    try:
        health_data = await orchestrator.health_check()

        # 转换可用源类型
        available_sources = [
            convert_api_source_type(source)
            for source in orchestrator.get_available_sources()
        ]

        return HealthCheckResponse(
            status=health_data.get("status", "unknown"),
            engines=health_data.get("engines", {}),
            available_sources=available_sources,
            cache_enabled=health_data.get("cache_enabled", False),
            last_search_time=health_data.get("last_search_time"),
            error=health_data.get("error"),
        )

    except Exception as e:
        error_message = f"健康检查失败: {str(e)}"
        print(f"❌ {error_message}")

        return HealthCheckResponse(
            status="error",
            engines={},
            available_sources=[],
            cache_enabled=False,
            last_search_time=None,
            error=error_message,
        )


@app.post("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    request: SuggestionsRequest, orchestrator=Depends(get_orchestrator)
):
    """获取搜索建议"""
    try:
        suggestions = await orchestrator.get_search_suggestions(request.query)

        return SuggestionsResponse(
            success=True, suggestions=suggestions, query=request.query
        )

    except Exception as e:
        error_message = f"获取搜索建议失败: {str(e)}"
        print(f"❌ {error_message}")

        return SuggestionsResponse(success=False, suggestions=[], query=request.query)


@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(orchestrator=Depends(get_orchestrator)):
    """获取系统统计信息"""
    try:
        # 获取缓存统计信息
        cache_stats = await orchestrator.cache_manager.get_stats()

        # 构建统计信息
        stats = {
            "available_sources": [
                s.value for s in orchestrator.get_available_sources()
            ],
            "cache_enabled": orchestrator.cache_manager.enabled,
            "service_status": "running",
            "cache_stats": cache_stats,
        }

        return StatisticsResponse(success=True, statistics=stats)

    except Exception as e:
        error_message = f"获取统计信息失败: {str(e)}"
        print(f"❌ {error_message}")

        return StatisticsResponse(success=False, statistics={})


@app.delete("/cache", response_model=CacheOperationResponse)
async def clear_cache(orchestrator=Depends(get_orchestrator)):
    """清空缓存"""
    try:
        await orchestrator.clear_cache()

        # 获取清理后的缓存统计
        cache_stats = await orchestrator.cache_manager.get_stats()
        cache_size = (
            cache_stats.get("current_size", 0) if isinstance(cache_stats, dict) else 0
        )

        return CacheOperationResponse(
            success=True, message="缓存已清空", cache_size=cache_size
        )

    except Exception as e:
        error_message = f"清空缓存失败: {str(e)}"
        print(f"❌ {error_message}")

        return CacheOperationResponse(success=False, message=error_message)


@app.get("/cache/stats", response_model=dict)
async def get_cache_stats(orchestrator=Depends(get_orchestrator)):
    """获取详细的缓存统计信息"""
    try:
        cache_stats = await orchestrator.cache_manager.get_stats()

        return {"success": True, "cache_stats": cache_stats, "timestamp": time.time()}

    except Exception as e:
        error_message = f"获取缓存统计失败: {str(e)}"
        print(f"❌ {error_message}")

        return {"success": False, "error": error_message, "cache_stats": {}}


@app.get("/cache/health", response_model=dict)
async def get_cache_health(orchestrator=Depends(get_orchestrator)):
    """获取缓存健康状态"""
    try:
        health_status = await orchestrator.cache_manager.health_check()
        cache_stats = await orchestrator.cache_manager.get_stats()

        return {
            "success": True,
            "healthy": health_status,
            "cache_type": cache_stats.get("type", "unknown"),
            "fallback_enabled": cache_stats.get("fallback_enabled", False),
            "redis_healthy": (
                cache_stats.get("redis_healthy", False)
                if cache_stats.get("type") == "distributed"
                else None
            ),
            "timestamp": time.time(),
        }

    except Exception as e:
        error_message = f"获取缓存健康状态失败: {str(e)}"
        print(f"❌ {error_message}")

        return {"success": False, "healthy": False, "error": error_message}


if __name__ == "__main__":
    import uvicorn

    print("🚀 启动 E-WebSearch API 服务...")
    uvicorn.run(
        "api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
