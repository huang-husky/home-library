"""
Metadata Service

聚合多个 Metadata Provider，提供统一的搜索接口，支持 fallback 机制
"""
import os
from typing import List, Optional
import asyncio
from app.services.metadata.provider import MetadataProvider
from app.services.metadata.dto import (
    BookMetadataCandidate,
    MetadataSearchResult,
    ISBNLookupResult,
    ProviderHealth,
)
from app.services.metadata.google_books import GoogleBooksProvider
from app.services.metadata.open_library import OpenLibraryProvider


class MetadataService:
    """
    图书元数据服务

    聚合多个 Provider（Google Books、Open Library 等），提供统一的搜索接口。
    支持 fallback 机制：当某个 Provider 失败时，自动切换到下一个 Provider。

    Usage:
        service = MetadataService()

        # ISBN 查询
        result = await service.search_by_isbn("9787536692930")

        # 书名搜索
        result = await service.search_by_title("三体")

        # 作者+书名搜索
        result = await service.search_by_author_title("刘慈欣", "三体")
    """

    def __init__(
        self,
        providers: Optional[List[MetadataProvider]] = None,
        timeout: float = 10.0,
    ):
        """
        初始化 Metadata Service

        Args:
            providers: 自定义 Provider 列表（None 则使用默认配置）
            timeout: 单个 Provider 超时时间
        """
        self.timeout = timeout

        if providers:
            self.providers = providers
        else:
            # 默认配置：Google Books + Open Library
            self.providers = [
                GoogleBooksProvider(timeout=timeout),
                OpenLibraryProvider(timeout=timeout),
            ]

    def _deduplicate_candidates(
        self, candidates: List[BookMetadataCandidate]
    ) -> List[BookMetadataCandidate]:
        """
        去重候选结果

        基于 ISBN-13 或 ISBN-10 去重，优先保留排名靠前的结果

        Args:
            candidates: 候选列表

        Returns:
            去重后的候选列表
        """
        seen = set()
        unique = []

        for candidate in candidates:
            # 使用 ISBN-13 或 ISBN-10 作为唯一标识
            key = candidate.isbn13 or candidate.isbn10

            if key and key in seen:
                continue

            if key:
                seen.add(key)

            unique.append(candidate)

        return unique

    async def _search_with_fallback(
        self,
        search_func,
        max_results: int = 10,
    ) -> List[BookMetadataCandidate]:
        """
        使用 fallback 机制搜索

        依次尝试每个 Provider，直到有足够结果或所有 Provider 都失败

        Args:
            search_func: 搜索函数，接收一个 Provider 参数
            max_results: 最大返回结果数

        Returns:
            合并后的候选列表
        """
        all_candidates = []
        errors = []

        for provider in self.providers:
            try:
                # 使用 asyncio.wait_for 设置超时
                candidates = await asyncio.wait_for(
                    search_func(provider),
                    timeout=self.timeout + 2,  # 额外缓冲时间
                )

                if candidates:
                    all_candidates.extend(candidates)

                    # 如果已有足够结果，可以提前返回
                    if len(all_candidates) >= max_results:
                        break

            except asyncio.TimeoutError:
                errors.append(f"{provider.name}: timeout")
            except Exception as e:
                errors.append(f"{provider.name}: {str(e)}")
                # 继续尝试下一个 Provider
                continue

        # 去重并限制结果数量
        unique_candidates = self._deduplicate_candidates(all_candidates)
        return unique_candidates[:max_results]

    async def search_by_title(
        self, title: str, max_results: int = 10
    ) -> MetadataSearchResult:
        """
        通过书名搜索

        Args:
            title: 书名
            max_results: 最大返回结果数

        Returns:
            MetadataSearchResult
        """
        candidates = await self._search_with_fallback(
            lambda p: p.search_by_title(title, max_results=max_results),
            max_results=max_results,
        )

        return MetadataSearchResult(
            query=title,
            candidates=candidates,
            total_found=len(candidates),
            sources=[p.name for p in self.providers],
        )

    async def search_by_author_title(
        self, author: str, title: str, max_results: int = 10
    ) -> MetadataSearchResult:
        """
        通过作者和书名搜索

        Args:
            author: 作者名
            title: 书名
            max_results: 最大返回结果数

        Returns:
            MetadataSearchResult
        """
        candidates = await self._search_with_fallback(
            lambda p: p.search_by_author_title(author, title, max_results=max_results),
            max_results=max_results,
        )

        return MetadataSearchResult(
            query=f"{author} {title}",
            candidates=candidates,
            total_found=len(candidates),
            sources=[p.name for p in self.providers],
        )

    async def search_by_isbn(self, isbn: str) -> ISBNLookupResult:
        """
        通过 ISBN 搜索

        依次尝试每个 Provider，直到找到结果或所有 Provider 都失败

        Args:
            isbn: ISBN-10 或 ISBN-13

        Returns:
            ISBNLookupResult
        """
        # 清理 ISBN
        clean_isbn = isbn.replace("-", "").replace(" ", "")

        for provider in self.providers:
            try:
                candidate = await asyncio.wait_for(
                    provider.search_by_isbn(clean_isbn),
                    timeout=self.timeout + 2,
                )

                if candidate:
                    return ISBNLookupResult(
                        isbn=clean_isbn,
                        found=True,
                        candidate=candidate,
                        source=provider.name,
                    )

            except asyncio.TimeoutError:
                continue
            except Exception:
                continue

        return ISBNLookupResult(
            isbn=clean_isbn,
            found=False,
            candidate=None,
            source=None,
        )

    async def search(self, query: str, max_results: int = 10) -> MetadataSearchResult:
        """
        通用搜索

        自动检测查询类型（ISBN 或书名）并执行相应搜索

        Args:
            query: 搜索查询（ISBN 或书名）
            max_results: 最大返回结果数

        Returns:
            MetadataSearchResult
        """
        # 清理查询
        clean_query = query.strip()

        # 检测是否为 ISBN（10 或 13 位数字）
        isbn_digits = clean_query.replace("-", "").replace(" ", "")
        if len(isbn_digits) in [10, 13] and isbn_digits.isdigit():
            # ISBN 查询
            isbn_result = await self.search_by_isbn(isbn_digits)

            if isbn_result.found and isbn_result.candidate:
                return MetadataSearchResult(
                    query=query,
                    candidates=[isbn_result.candidate],
                    total_found=1,
                    sources=[isbn_result.source] if isbn_result.source else [],
                )
            else:
                return MetadataSearchResult(
                    query=query,
                    candidates=[],
                    total_found=0,
                    sources=[],
                )

        # 普通书名搜索
        return await self.search_by_title(clean_query, max_results=max_results)

    async def health_check(self) -> List[ProviderHealth]:
        """
        检查所有 Provider 的健康状态

        Returns:
            ProviderHealth 列表
        """
        results = []

        for provider in self.providers:
            import time

            start_time = time.time()
            try:
                available = await asyncio.wait_for(
                    provider.health_check(),
                    timeout=self.timeout,
                )
                response_time = (time.time() - start_time) * 1000

                results.append(
                    ProviderHealth(
                        name=provider.name,
                        available=available,
                        response_time_ms=round(response_time, 2),
                        error_message=None,
                    )
                )
            except asyncio.TimeoutError:
                results.append(
                    ProviderHealth(
                        name=provider.name,
                        available=False,
                        response_time_ms=None,
                        error_message="Timeout",
                    )
                )
            except Exception as e:
                results.append(
                    ProviderHealth(
                        name=provider.name,
                        available=False,
                        response_time_ms=None,
                        error_message=str(e),
                    )
                )

        return results

    async def close(self):
        """关闭所有 Provider 的 HTTP 客户端"""
        for provider in self.providers:
            if hasattr(provider, "close"):
                await provider.close()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        return False
