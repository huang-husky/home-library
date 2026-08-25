"""
FastAPI 应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.database import init_db
from app.api.books import router as books_router
from app.api.bookshelves import router as bookshelves_router, shelf_router
from app.api.metadata import router as metadata_router
from app.api.recognition import router as recognition_router
from app.api.scans import router as scans_router
from app.api.ai_import import router as ai_import_router
from app.api.categories import router as categories_router
from app.api.book_classification import router as book_classification_router
from app.api.shelf_positions import router as shelf_positions_router

settings = get_settings()

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 家庭图书馆管理系统",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(books_router)
app.include_router(bookshelves_router)
app.include_router(shelf_router)
app.include_router(metadata_router)
app.include_router(recognition_router)
app.include_router(scans_router)
app.include_router(ai_import_router)
app.include_router(categories_router)
app.include_router(book_classification_router)
app.include_router(shelf_positions_router)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "version": settings.app_version,
        "app": settings.app_name,
    }


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print(f"🚀 {settings.app_name} v{settings.app_version} started")
    print(f"   Debug mode: {settings.debug}")
    # 初始化数据库
    await init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
