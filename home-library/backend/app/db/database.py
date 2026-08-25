"""
数据库配置
支持 async 和 sync 两种模式（Alembic 需要 sync）
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# 声明基类
Base = declarative_base()

# ========== Async 配置（应用运行时）==========

async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """获取数据库会话（依赖注入用）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库（创建表）- 应用启动时使用"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ========== Sync 配置（Alembic 使用）==========

# 转换 async URL 为 sync URL（去掉 +aiosqlite）
SYNC_DATABASE_URL = settings.database_url.replace("+aiosqlite", "")

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=settings.debug,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)


def get_sync_db():
    """获取同步数据库会话（用于脚本）"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
