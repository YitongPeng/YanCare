"""
YanCare API 主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import (
    auth_router,
    stores_router,
    cards_router,
    schedules_router,
    appointments_router,
    users_router,
    ai_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    print("数据库初始化完成")
    yield
    # 关闭时的清理工作
    print("应用关闭")


app = FastAPI(
    title=settings.APP_NAME,
    description="养发馆管理系统 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api")
app.include_router(stores_router, prefix="/api")
app.include_router(cards_router, prefix="/api")
app.include_router(schedules_router, prefix="/api")
app.include_router(appointments_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(ai_router, prefix="/api")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to YanCare API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
