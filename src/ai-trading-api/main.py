"""
AI Trading API - FastAPI 应用入口

提供股票数据、港交所卖空数据、金管局流动性数据的 RESTful 查询接口。

启动方式：
    cd src/ai-trading-api
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

访问 API 文档：
    http://localhost:8000/docs    (Swagger UI)
    http://localhost:8000/redoc   (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings

from api.stocks_router import router as stocks_router
from api.hkex_router import router as hkex_router
from api.hkma_router import router as hkma_router

app = FastAPI(
    title="AI Trading API",
    description="AI 交易系统数据查询接口，提供股票行情、港交所卖空、金管局流动性等数据查询。",
    version="1.0.0",
)

# CORS 中间件（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(stocks_router)
app.include_router(hkex_router)
app.include_router(hkma_router)


@app.get("/")
def root():
    """API 根路径 - 健康检查"""
    return {
        "app": "AI Trading API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )