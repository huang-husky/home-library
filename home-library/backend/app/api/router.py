"""
API 路由聚合
Phase 1: 暂无具体路由，仅保留框架
"""
from fastapi import APIRouter

# 创建主路由
api_router = APIRouter()

# Phase 2+ 将在这里注册子路由
# api_router.include_router(books.router, prefix="/books", tags=["books"])
# api_router.include_router(bookshelves.router, prefix="/bookshelves", tags=["bookshelves"])
