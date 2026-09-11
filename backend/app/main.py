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


@app.post("/init-data")
async def init_data():
    """初始化数据（仅用于部署后首次初始化）"""
    import sys
    import os
    
    # 导入初始化脚本
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts.init_data import init_card_types, init_stores, create_admin_user, create_test_staff
    
    try:
        await init_card_types()
        await init_stores()
        await create_admin_user()
        await create_test_staff()
        return {"message": "数据初始化成功"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/init-knowledge")
async def init_knowledge():
    """初始化知识库（导入养发知识到向量数据库）"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 导入知识库文档
        from scripts.init_knowledge import SERVICE_DOCS, CARD_DOCS, FAQ_DOCS
        from app.services.rag import rag_service
        
        # 合并所有文档
        all_docs = SERVICE_DOCS + CARD_DOCS + FAQ_DOCS
        
        # 批量添加文档
        for doc in all_docs:
            rag_service.add_document(
                doc_id=doc["id"],
                content=doc["content"],
                metadata=doc["metadata"]
            )
        
        return {
            "message": "知识库初始化成功",
            "total_docs": len(all_docs)
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
