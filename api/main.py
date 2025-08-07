"""
E-WebSearch API 服务主入口
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import traceback
from typing import List

# 导入本地模块
import sys
import os

from core.search_orchestrator import SearchOrchestrator
from core.models import SearchRequest, SourceType
from .models import (
    SearchRequestAPI, SearchResponseAPI, SearchResultAPI, SourceTypeAPI,
    HealthCheckResponse, ErrorResponse, SuggestionsRequest, SuggestionsResponse,
    StatisticsResponse, CacheOperationResponse
)


# 全局变量
search_orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global search_orchestrator
    
    # 启动时初始化
    print("🚀 初始化 E-WebSearch API 服务...")
    try:
        search_orchestrator = SearchOrchestrator()
        print("✅ 搜索协调器初始化成功")
    except Exception as e:
        print(f"❌ 搜索协调器初始化失败: {e}")
        search_orchestrator = None
    
    yield
    
    # 关闭时清理
    print("🔄 关闭 E-WebSearch API 服务...")


# 创建 FastAPI 应用
app = FastAPI(
    title="E-WebSearch API",
    description="基于 ZAI Search Pro 的增强版 Web 搜索 API 服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_orchestrator():
    """获取搜索协调器实例"""
    if search_orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="搜索服务暂时不可用，请稍后重试"
        )
    return search_orchestrator


def convert_source_type(source: SourceTypeAPI):
    """转换 API 源类型到内部源类型"""
    if 'SourceType' not in globals():
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
        if source == 'mock':
            return SourceTypeAPI.CUSTOM
        # 如果是字符串，直接转换
        try:
            return SourceTypeAPI(source)
        except ValueError:
            # 如果无法转换，返回自定义类型
            return SourceTypeAPI.CUSTOM
    
    if 'SourceType' not in globals():
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
            details={"error": error_detail}
        ).dict()
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
            "cache": "/cache"
        }
    }


@app.post("/search", response_model=SearchResponseAPI)
async def search(
    request: SearchRequestAPI,
    orchestrator = Depends(get_orchestrator)
):
    """执行搜索"""
    try:
        start_time = time.time()
        
        # 转换 API 请求到内部请求
        internal_sources = [convert_source_type(source) for source in request.sources]
        
        if 'SearchRequest' in globals() and SearchRequest:
            internal_request = SearchRequest(
                query=request.query,
                max_results=request.max_results,
                include_content=request.include_content,
                sources=internal_sources,
                filters=request.filters
            )
        else:
            # 如果 SearchRequest 不可用，创建简单的字典结构
            internal_request = {
                'query': request.query,
                'max_results': request.max_results,
                'include_content': request.include_content,
                'sources': internal_sources,
                'filters': request.filters
            }
        
        # 执行搜索
        response = await orchestrator.search(internal_request)
        
        # 处理响应（可能是字典或对象）
        if isinstance(response, dict):
            # 处理字典响应（模拟搜索）
            results_data = response.get('results', [])
            api_results = []
            
            for result in results_data:
                if isinstance(result, dict):
                    api_result = SearchResultAPI(
                        title=result.get('title', ''),
                        url=result.get('url', ''),
                        snippet=result.get('snippet', ''),
                        source=convert_api_source_type(result.get('source', 'mock')),
                        score=result.get('score', 0.0),
                        publish_time=result.get('publish_time'),
                        author=result.get('author'),
                        content=result.get('content'),
                        images=result.get('images', []),
                        metadata=result.get('metadata', {})
                    )
                    api_results.append(api_result)
            
            api_sources_used = [convert_api_source_type(source) for source in response.get('sources_used', [])]
            
            return SearchResponseAPI(
                success=response.get('success', True),
                message="搜索完成",
                results=api_results,
                total_count=response.get('total_count', len(api_results)),
                query=response.get('query', request.query),
                execution_time=response.get('execution_time', 0.0),
                sources_used=api_sources_used,
                cache_hit=response.get('cache_hit', False)
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
                    metadata=result.metadata
                )
                api_results.append(api_result)
            
            api_sources_used = [convert_api_source_type(source) for source in response.sources_used]
            
            return SearchResponseAPI(
                success=True,
                message="搜索完成",
                results=api_results,
                total_count=response.total_count,
                query=response.query,
                execution_time=response.execution_time,
                sources_used=api_sources_used,
                cache_hit=response.cache_hit
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
            cache_hit=False
        )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check(orchestrator = Depends(get_orchestrator)):
    """健康检查"""
    try:
        health_data = await orchestrator.health_check()
        
        # 转换可用源类型
        available_sources = [
            convert_api_source_type(source) 
            for source in orchestrator.get_available_sources()
        ]
        
        return HealthCheckResponse(
            status=health_data.get('status', 'unknown'),
            engines=health_data.get('engines', {}),
            available_sources=available_sources,
            cache_enabled=health_data.get('cache_enabled', False),
            last_search_time=health_data.get('last_search_time'),
            error=health_data.get('error')
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
            error=error_message
        )


@app.post("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    request: SuggestionsRequest,
    orchestrator = Depends(get_orchestrator)
):
    """获取搜索建议"""
    try:
        suggestions = await orchestrator.get_search_suggestions(request.query)
        
        return SuggestionsResponse(
            success=True,
            suggestions=suggestions,
            query=request.query
        )
        
    except Exception as e:
        error_message = f"获取搜索建议失败: {str(e)}"
        print(f"❌ {error_message}")
        
        return SuggestionsResponse(
            success=False,
            suggestions=[],
            query=request.query
        )


@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(orchestrator = Depends(get_orchestrator)):
    """获取系统统计信息"""
    try:
        # 这里可以添加更多统计信息
        stats = {
            "available_sources": [s.value for s in orchestrator.get_available_sources()],
            "cache_enabled": orchestrator.cache_manager.enabled,
            "service_status": "running"
        }
        
        return StatisticsResponse(
            success=True,
            statistics=stats
        )
        
    except Exception as e:
        error_message = f"获取统计信息失败: {str(e)}"
        print(f"❌ {error_message}")
        
        return StatisticsResponse(
            success=False,
            statistics={}
        )


@app.delete("/cache", response_model=CacheOperationResponse)
async def clear_cache(orchestrator = Depends(get_orchestrator)):
    """清空缓存"""
    try:
        orchestrator.clear_cache()
        
        return CacheOperationResponse(
            success=True,
            message="缓存已清空",
            cache_size=0
        )
        
    except Exception as e:
        error_message = f"清空缓存失败: {str(e)}"
        print(f"❌ {error_message}")
        
        return CacheOperationResponse(
            success=False,
            message=error_message
        )


@app.post("/cache/cleanup", response_model=CacheOperationResponse)
async def cleanup_cache(orchestrator = Depends(get_orchestrator)):
    """清理过期缓存"""
    try:
        orchestrator.cleanup_expired_cache()
        
        return CacheOperationResponse(
            success=True,
            message="过期缓存已清理"
        )
        
    except Exception as e:
        error_message = f"清理过期缓存失败: {str(e)}"
        print(f"❌ {error_message}")
        
        return CacheOperationResponse(
            success=False,
            message=error_message
        )


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动 E-WebSearch API 服务...")
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )