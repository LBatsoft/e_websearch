#!/usr/bin/env python3
"""
简化的 API 测试版本，用于验证 API 框架是否正常工作
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import time

# 创建 FastAPI 应用
app = FastAPI(
    title="E-WebSearch API (测试版)",
    description="基于 ZAI Search Pro 的增强版 Web 搜索 API 服务 - 测试版本",
    version="1.0.0-test",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 简化的数据模型
class SearchRequestSimple(BaseModel):
    query: str
    max_results: int = 10
    sources: List[str] = ["zai"]

class SearchResultSimple(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    score: float = 0.0

class SearchResponseSimple(BaseModel):
    success: bool
    message: str
    results: List[SearchResultSimple]
    total_count: int
    query: str
    execution_time: float

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: float

@app.get("/")
async def root():
    """根路径 - API 信息"""
    return {
        "name": "E-WebSearch API (测试版)",
        "version": "1.0.0-test",
        "description": "基于 ZAI Search Pro 的增强版 Web 搜索 API 服务 - 测试版本",
        "status": "running",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "search": "/search",
            "health": "/health"
        }
    }

@app.post("/search", response_model=SearchResponseSimple)
async def search(request: SearchRequestSimple):
    """执行搜索 (测试版)"""
    start_time = time.time()
    
    # 模拟搜索结果
    mock_results = [
        SearchResultSimple(
            title=f"关于'{request.query}'的搜索结果 {i+1}",
            url=f"https://example.com/result-{i+1}",
            snippet=f"这是关于'{request.query}'的第{i+1}个搜索结果的摘要内容...",
            source="zai",
            score=0.9 - i * 0.1
        )
        for i in range(min(request.max_results, 3))
    ]
    
    execution_time = time.time() - start_time
    
    return SearchResponseSimple(
        success=True,
        message="搜索完成 (模拟)",
        results=mock_results,
        total_count=len(mock_results),
        query=request.query,
        execution_time=execution_time
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        message="API 服务运行正常 (测试版)",
        timestamp=time.time()
    )

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动 E-WebSearch API 测试服务...")
    print("📍 地址: http://localhost:8001")
    print("📚 文档: http://localhost:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")