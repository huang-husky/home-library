"""
Core 配置模块
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


def parse_cors_origins(v: str | list[str]) -> list[str]:
    """解析 CORS_ORIGINS 环境变量（逗号分隔或列表）"""
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    return v


class Settings(BaseSettings):
    """应用配置"""
    app_name: str = "HomeLib"
    app_version: str = "1.0.0"
    debug: bool = True

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./data/homelib.db"

    # CORS - 支持环境变量 CORS_ORIGINS（逗号分隔）
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        # 自定义解析 cors_origins 环境变量
        import os
        if cors_env := os.getenv("CORS_ORIGINS"):
            init_settings = init_settings.copy()
            init_settings.kwargs["cors_origins"] = parse_cors_origins(cors_env)
        return (init_settings, env_settings, dotenv_settings, file_secret_settings)


@lru_cache()
def get_settings() -> Settings:
    """获取配置（单例）"""
    return Settings()
