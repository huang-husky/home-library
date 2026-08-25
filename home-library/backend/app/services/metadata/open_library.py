"""
Open Library Metadata Provider

实现 MetadataProvider 接口，从 Open Library API 获取图书元数据
"""
from typing import List, Optional
import httpx
from app.services.metadata.provider import MetadataProvider
from app.services.metadata.dto import BookMetadataCandidate


class OpenLibraryProvider(MetadataProvider):
    """
    Open Library API Provider

    API 文档: https://openlibrary.org/developers/api
    """

    BASE_URL = "https://openlibrary.org"

    def __init__(self, timeout: float = 10.0):
        """
        初始化 Open Library Provider

        Args:
            timeout: HTTP 请求超时时间（秒）
        """
        super().__init__(timeout=timeout)
        self._client = httpx.AsyncClient(timeout=timeout)
        self._name = "open_library"

    async def _make_request(
        self, endpoint: str, params: Optional[dict] = None
    ) -> dict:
        """
        发送 HTTP 请求到 Open Library API

        Args:
            endpoint: API 端点
            params: 查询参数

        Returns:
            JSON 响应数据

        Raises:
            httpx.HTTPError: HTTP 请求失败
        """
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise Exception(f"Open Library API timeout after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Open Library API error: {e.response.status_code}")

    async def _fetch_author_name(self, author_key: str) -> Optional[str]:
        """
        获取作者名称

        Open Library 的作者信息是分开存储的，需要额外请求

        Args:
            author_key: 作者 key（如 "/authors/OL123456A"）

        Returns:
            作者名称
        """
        try:
            # 移除开头的斜杠
            clean_key = author_key.lstrip("/")
            data = await self._make_request(f"{clean_key}.json")
            return data.get("name")
        except Exception:
            return None

    def _extract_isbn(self, data: dict) -> tuple[Optional[str], Optional[str]]:
        """
        从数据中提取 ISBN-10 和 ISBN-13

        Args:
            data: Open Library 返回的数据

        Returns:
            (isbn10, isbn13) 元组
        """
        isbn10 = None
        isbn13 = None

        # 优先从 identifiers 提取
        identifiers = data.get("identifiers", {})
        isbn10_list = identifiers.get("isbn_10", [])
        isbn13_list = identifiers.get("isbn_13", [])

        if isbn10_list:
            isbn10 = isbn10_list[0]
        if isbn13_list:
            isbn13 = isbn13_list[0]

        # 如果没有，直接从 isbn_10 和 isbn_13 字段提取
        if not isbn10:
            isbn10_list = data.get("isbn_10", [])
            if isbn10_list:
                isbn10 = isbn10_list[0]

        if not isbn13:
            isbn13_list = data.get("isbn_13", [])
            if isbn13_list:
                isbn13 = isbn13_list[0]

        return isbn10, isbn13

    def _extract_cover_url(self, cover_ids: Optional[List[int]]) -> Optional[str]:
        """
        提取封面图片 URL

        Args:
            cover_ids: 封面 ID 列表

        Returns:
            封面图片 URL
        """
        if not cover_ids:
            return None

        # Open Library 封面服务
        cover_id = cover_ids[0]
        return f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"

    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """
        从日期字符串中提取年份

        Args:
            date_str: 日期字符串

        Returns:
            年份整数，或 None
        """
        if not date_str:
            return None

        try:
            # 尝试提取前 4 位数字作为年份
            year_str = date_str[:4]
            return int(year_str)
        except (ValueError, IndexError):
            return None

    def _map_to_candidate(self, raw_data: dict) -> BookMetadataCandidate:
        """
        实现抽象方法：将原始 API 数据映射为 BookMetadataCandidate

        此方法根据数据结构自动选择合适的映射方式
        """
        # 检测数据类型：edition 或 search result
        if "key" in raw_data and raw_data.get("key", "").startswith("/books/"):
            # Edition 数据
            return self._map_edition_to_candidate(raw_data)
        else:
            # 搜索结果数据
            return self._map_search_result_to_candidate(raw_data)

    def _map_edition_to_candidate(
        self, edition_data: dict, work_data: Optional[dict] = None
    ) -> BookMetadataCandidate:
        """
        将 Open Library Edition 数据映射为 BookMetadataCandidate

        Args:
            edition_data: Edition 数据
            work_data: 关联的 Work 数据（可选）

        Returns:
            BookMetadataCandidate
        """
        isbn10, isbn13 = self._extract_isbn(edition_data)

        # 优先使用 Edition 的标题，如果没有则使用 Work 的标题
        title = edition_data.get("title") or (
            work_data.get("title") if work_data else None
        )

        # 提取描述（Work 通常有描述）
        description = None
        if work_data:
            desc = work_data.get("description")
            if isinstance(desc, dict):
                description = desc.get("value")
            elif isinstance(desc, str):
                description = desc

        # 提取作者
        authors = []
        author_keys = edition_data.get("authors", [])
        if not author_keys and work_data:
            author_keys = work_data.get("authors", [])

        for author_info in author_keys:
            if isinstance(author_info, dict):
                author_name = author_info.get("name")
                if author_name:
                    authors.append(author_name)

        # 提取出版日期和年份
        publish_date = edition_data.get("publish_date")
        publish_year = self._extract_year(publish_date)

        # 提取封面
        cover_ids = edition_data.get("covers", [])
        if not cover_ids and work_data:
            cover_ids = work_data.get("covers", [])
        cover_url = self._extract_cover_url(cover_ids)

        return BookMetadataCandidate(
            source=self._name,
            source_id=edition_data.get("key", "").replace("/books/", ""),
            title=title or "Unknown Title",
            subtitle=None,  # Open Library 没有直接的 subtitle 字段
            authors=authors,
            publisher=edition_data.get("publishers", [None])[0],
            publish_date=publish_date,
            publish_year=publish_year,
            isbn10=isbn10,
            isbn13=isbn13,
            language=edition_data.get("languages", [{}])[0].get("key", "").replace("/languages/", "") if edition_data.get("languages") else None,
            page_count=edition_data.get("number_of_pages"),
            cover_url=cover_url,
            description=description,
            raw_data=None,  # 不保存原始数据以减少内存占用
        )

    def _map_search_result_to_candidate(self, doc: dict) -> BookMetadataCandidate:
        """
        将搜索结果映射为 BookMetadataCandidate

        Args:
            doc: 搜索结果文档

        Returns:
            BookMetadataCandidate
        """
        # 提取 ISBN
        isbn10 = None
        isbn13 = None

        isbn_list = doc.get("isbn", [])
        for isbn in isbn_list:
            if len(isbn) == 10:
                isbn10 = isbn
            elif len(isbn) == 13:
                isbn13 = isbn

        # 提取作者
        authors = doc.get("author_name", [])

        # 提取封面
        cover_id = doc.get("cover_i")
        cover_url = (
            f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
            if cover_id else None
        )

        # 提取年份
        publish_year = doc.get("first_publish_year")

        return BookMetadataCandidate(
            source=self._name,
            source_id=str(doc.get("key", "").replace("/works/", "")),
            title=doc.get("title", "Unknown Title"),
            subtitle=None,
            authors=authors,
            publisher=doc.get("publisher", [None])[0] if doc.get("publisher") else None,
            publish_date=str(publish_year) if publish_year else None,
            publish_year=publish_year,
            isbn10=isbn10,
            isbn13=isbn13,
            language=doc.get("language", [None])[0] if doc.get("language") else None,
            page_count=None,  # 搜索结果通常不包含页数
            cover_url=cover_url,
            description=None,  # 搜索结果通常不包含描述
            raw_data=None,
        )

    async def search_by_title(
        self, title: str, max_results: int = 10
    ) -> List[BookMetadataCandidate]:
        """
        通过书名搜索

        Args:
            title: 书名
            max_results: 最大返回结果数

        Returns:
            BookMetadataCandidate 列表
        """
        params = {
            "q": title,
            "fields": "key,title,author_name,first_publish_year,publisher,isbn,cover_i,language",
            "limit": max_results,
        }

        data = await self._make_request("search.json", params)
        docs = data.get("docs", [])

        return [self._map_search_result_to_candidate(doc) for doc in docs]

    async def search_by_author_title(
        self, author: str, title: str, max_results: int = 10
    ) -> List[BookMetadataCandidate]:
        """
        通过作者和书名搜索

        Args:
            author: 作者名
            title: 书名
            max_results: 最大返回结果数

        Returns:
            BookMetadataCandidate 列表
        """
        params = {
            "q": f"title:{title} author:{author}",
            "fields": "key,title,author_name,first_publish_year,publisher,isbn,cover_i,language",
            "limit": max_results,
        }

        data = await self._make_request("search.json", params)
        docs = data.get("docs", [])

        return [self._map_search_result_to_candidate(doc) for doc in docs]

    async def search_by_isbn(
        self, isbn: str
    ) -> Optional[BookMetadataCandidate]:
        """
        通过 ISBN 搜索

        Args:
            isbn: ISBN-10 或 ISBN-13

        Returns:
            单个 BookMetadataCandidate，未找到返回 None
        """
        # 清理 ISBN
        clean_isbn = isbn.replace("-", "").replace(" ", "")

        try:
            # 使用 ISBN API 获取 Edition 信息
            data = await self._make_request(f"isbn/{clean_isbn}.json")

            if not data:
                return None

            # 获取关联的 Work 信息以获取更完整的数据
            work_data = None
            works = data.get("works", [])
            if works:
                work_key = works[0].get("key", "").lstrip("/")
                if work_key:
                    try:
                        work_data = await self._make_request(f"{work_key}.json")
                    except Exception:
                        pass  # Work 获取失败不影响主流程

            return self._map_edition_to_candidate(data, work_data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def close(self):
        """关闭 HTTP 客户端"""
        await self._client.aclose()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        return False
