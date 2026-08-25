"""
Metadata Service DTOs

统一内部数据结构，与具体 Provider 解耦
"""
from typing import List, Optional, Any
from pydantic import BaseModel, Field


class BookMetadataCandidate(BaseModel):
    """
    图书元数据候选对象

    统一的内部 DTO，用于封装来自不同 Provider 的图书元数据。
    业务层只感知此结构，不感知第三方 API 的具体字段。
    """

    # 来源信息
    source: str = Field(..., description="数据来源，如 'google_books', 'open_library'")
    source_id: str = Field(..., description="Provider 内部的唯一标识")

    # 核心元数据
    title: str = Field(..., description="书名")
    subtitle: Optional[str] = Field(None, description="副标题")
    authors: List[str] = Field(default_factory=list, description="作者列表")

    # 出版信息
    publisher: Optional[str] = Field(None, description="出版社")
    publish_date: Optional[str] = Field(None, description="出版日期（原始字符串）")
    publish_year: Optional[int] = Field(None, description="出版年份")

    # 标识符
    isbn10: Optional[str] = Field(None, description="ISBN-10")
    isbn13: Optional[str] = Field(None, description="ISBN-13")

    # 其他元数据
    language: Optional[str] = Field(None, description="语言代码")
    page_count: Optional[int] = Field(None, description="页数")
    cover_url: Optional[str] = Field(None, description="封面图片 URL")
    description: Optional[str] = Field(None, description="简介/描述")

    # 原始数据（调试用，不写入数据库）
    raw_data: Optional[Any] = Field(None, description="Provider 返回的原始数据（调试用）")

    class Config:
        """Pydantic V2 配置"""
        json_schema_extra = {
            "example": {
                "source": "google_books",
                "source_id": "abc123",
                "title": "三体",
                "subtitle": "地球往事三部曲之一",
                "authors": ["刘慈欣"],
                "publisher": "重庆出版社",
                "publish_date": "2008-01",
                "publish_year": 2008,
                "isbn10": "7536692935",
                "isbn13": "9787536692930",
                "language": "zh",
                "page_count": 302,
                "cover_url": "https://example.com/cover.jpg",
                "description": "文化大革命如火如荼进行的同时...",
            }
        }


class MetadataSearchResult(BaseModel):
    """
    元数据搜索结果

    包含多个候选对象，按相关度排序
    """

    query: str = Field(..., description="搜索查询")
    candidates: List[BookMetadataCandidate] = Field(default_factory=list, description="候选列表")
    total_found: int = Field(0, description="找到的候选总数")
    sources: List[str] = Field(default_factory=list, description="使用的数据源")


class ISBNLookupResult(BaseModel):
    """
    ISBN 查询结果

    ISBN 查询通常返回单个最匹配的结果
    """

    isbn: str = Field(..., description="查询的 ISBN")
    found: bool = Field(False, description="是否找到")
    candidate: Optional[BookMetadataCandidate] = Field(None, description="找到的候选对象")
    source: Optional[str] = Field(None, description="数据来源")


class ProviderHealth(BaseModel):
    """
    Provider 健康状态
    """

    name: str = Field(..., description="Provider 名称")
    available: bool = Field(True, description="是否可用")
    response_time_ms: Optional[float] = Field(None, description="响应时间（毫秒）")
    error_message: Optional[str] = Field(None, description="错误信息（如不可用）")
