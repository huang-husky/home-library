"""
Metadata Provider 抽象基类

定义统一的 Provider 接口，所有具体 Provider 必须实现此接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .dto import BookMetadataCandidate, ISBNLookupResult


class MetadataProvider(ABC):
    """
    图书元数据 Provider 抽象基类

    所有具体的元数据 Provider（Google Books、Open Library 等）必须继承此类
    并实现其抽象方法。业务代码只依赖此抽象接口，不依赖具体实现。
    """

    def __init__(self, timeout: float = 10.0):
        """
        初始化 Provider

        Args:
            timeout: HTTP 请求超时时间（秒）
        """
        self.timeout = timeout
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        """Provider 名称标识"""
        return self._name

    @abstractmethod
    async def search_by_title(
        self, title: str, max_results: int = 10
    ) -> List[BookMetadataCandidate]:
        """
        通过书名搜索图书元数据

        Args:
            title: 书名
            max_results: 最大返回结果数

        Returns:
            BookMetadataCandidate 列表
        """
        pass

    @abstractmethod
    async def search_by_author_title(
        self, author: str, title: str, max_results: int = 10
    ) -> List[BookMetadataCandidate]:
        """
        通过作者和书名搜索图书元数据

        Args:
            author: 作者名
            title: 书名
            max_results: 最大返回结果数

        Returns:
            BookMetadataCandidate 列表
        """
        pass

    @abstractmethod
    async def search_by_isbn(self, isbn: str) -> Optional[BookMetadataCandidate]:
        """
        通过 ISBN 搜索图书元数据

        Args:
            isbn: ISBN-10 或 ISBN-13

        Returns:
            单个 BookMetadataCandidate，未找到返回 None
        """
        pass

    @abstractmethod
    def _map_to_candidate(self, raw_data: dict) -> BookMetadataCandidate:
        """
        将原始 API 数据映射为统一的 BookMetadataCandidate

        Args:
            raw_data: Provider 返回的原始数据

        Returns:
            映射后的 BookMetadataCandidate
        """
        pass

    async def health_check(self) -> bool:
        """
        检查 Provider 健康状态

        Returns:
            True if provider 可用，False otherwise
        """
        try:
            # 默认实现：尝试一个简单的搜索
            await self.search_by_title("test", max_results=1)
            return True
        except Exception:
            return False
