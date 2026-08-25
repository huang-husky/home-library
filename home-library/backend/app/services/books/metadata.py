"""
Metadata Provider 接口
阶段零：仅定义接口，不实现具体 Provider
"""
from typing import List, Optional, Protocol
from pydantic import BaseModel

class MetadataSearchResult(BaseModel):
    """图书元数据搜索结果"""
    title: str
    authors: List[str] = []
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    isbn10: Optional[str] = None
    isbn13: Optional[str] = None
    page_count: Optional[int] = None
    language: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None
    source: str
    source_id: str
    confidence: float = 0.0


class MetadataProvider(Protocol):
    """图书元数据提供者接口"""

    async def search_by_title(self, title: str) -> List[MetadataSearchResult]:
        """根据书名搜索"""
        ...

    async def search_by_isbn(self, isbn: str) -> Optional[MetadataSearchResult]:
        """根据 ISBN 搜索"""
        ...


# 阶段零：暂不实现具体 Provider
# 后续将实现：
# - GoogleBooksProvider
# - OpenLibraryProvider
