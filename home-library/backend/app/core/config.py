"""
Core 配置模块
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    app_name: str = "HomeLib"
    app_version: str = "1.0.0"
    debug: bool = True

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./data/homelib.db"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置（单例）"""
    return Settings()
