"""
Google Books Metadata Provider

实现 MetadataProvider 接口，从 Google Books API 获取图书元数据
"""
import os
from typing import List, Optional
import httpx
from app.services.metadata.provider import MetadataProvider
from app.services.metadata.dto import BookMetadataCandidate


class GoogleBooksProvider(MetadataProvider):
    """
    Google Books API Provider

    API 文档: https://developers.google.com/books/docs/v1/using
    """

    BASE_URL = "https://www.googleapis.com/books/v1"

    def __init__(self, timeout: float = 10.0, api_key: Optional[str] = None):
        """
        初始化 Google Books Provider

        Args:
            timeout: HTTP 请求超时时间（秒）
            api_key: Google Books API Key（可选，从环境变量 GOOGLE_BOOKS_API_KEY 读取）
        """
        super().__init__(timeout=timeout)
        self.api_key = api_key or os.getenv("GOOGLE_BOOKS_API_KEY")
        self._client = httpx.AsyncClient(timeout=timeout)
        self._name = "google_books"

    async def _make_request(self, endpoint: str, params: dict) -> dict:
        """
        发送 HTTP 请求到 Google Books API

        Args:
            endpoint: API 端点
            params: 查询参数

        Returns:
            JSON 响应数据

        Raises:
            httpx.HTTPError: HTTP 请求失败
        """
        url = f"{self.BASE_URL}/{endpoint}"

        # 如果有 API key，添加到参数中
        if self.api_key:
            params["key"] = self.api_key

        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise Exception(f"Google Books API timeout after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Google Books API error: {e.response.status_code}")

    def _extract_isbn(self, identifiers: List[dict]) -> tuple[Optional[str], Optional[str]]:
        """
        从 identifiers 中提取 ISBN-10 和 ISBN-13

        Args:
            identifiers: Google Books 返回的 industryIdentifiers

        Returns:
            (isbn10, isbn13) 元组
        """
        isbn10 = None
        isbn13 = None

        for identifier in identifiers:
            type_ = identifier.get("type", "").upper()
            value = identifier.get("identifier", "")

            if type_ == "ISBN_10":
                isbn10 = value
            elif type_ == "ISBN_13":
                isbn13 = value

        return isbn10, isbn13

    def _extract_authors(self, authors: Optional[List[str]]) -> List[str]:
        """
        提取作者列表

        Args:
            authors: Google Books 返回的作者列表

        Returns:
            清理后的作者列表
        """
        if not authors:
            return []

        # 清理作者名，移除多余空格
        return [author.strip() for author in authors if author.strip()]

    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        """
        从日期字符串中提取年份

        Args:
            date_str: 日期字符串（如 "2008-01" 或 "2008"）

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
        将 Google Books API 数据映射为 BookMetadataCandidate

        Args:
            raw_data: Google Books API 返回的 volume 对象

        Returns:
            BookMetadataCandidate
        """
        volume_info = raw_data.get("volumeInfo", {})

        # 提取 ISBN
        identifiers = volume_info.get("industryIdentifiers", [])
        isbn10, isbn13 = self._extract_isbn(identifiers)

        # 提取出版日期和年份
        publish_date = volume_info.get("publishedDate")
        publish_year = self._extract_year(publish_date)

        # 提取封面图片 URL
        image_links = volume_info.get("imageLinks", {})
        cover_url = (
            image_links.get("thumbnail")
            or image_links.get("smallThumbnail")
            or None
        )

        return BookMetadataCandidate(
            source=self._name,
            source_id=raw_data.get("id", ""),
            title=volume_info.get("title", ""),
            subtitle=volume_info.get("subtitle"),
            authors=self._extract_authors(volume_info.get("authors")),
            publisher=volume_info.get("publisher"),
            publish_date=publish_date,
            publish_year=publish_year,
            isbn10=isbn10,
            isbn13=isbn13,
            language=volume_info.get("language"),
            page_count=volume_info.get("pageCount"),
            cover_url=cover_url,
            description=volume_info.get("description"),
            raw_data=raw_data if os.getenv("DEBUG") else None,
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
            "q": f"intitle:{title}",
            "maxResults": min(max_results, 40),  # Google Books 最大支持 40
            "printType": "books",
            "projection": "full",
        }

        data = await self._make_request("volumes", params)
        items = data.get("items", [])

        return [self._map_to_candidate(item) for item in items]

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
            "q": f"inauthor:{author}+intitle:{title}",
            "maxResults": min(max_results, 40),
            "printType": "books",
            "projection": "full",
        }

        data = await self._make_request("volumes", params)
        items = data.get("items", [])

        return [self._map_to_candidate(item) for item in items]

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
        # 清理 ISBN，移除横杠和空格
        clean_isbn = isbn.replace("-", "").replace(" ", "")

        params = {
            "q": f"isbn:{clean_isbn}",
            "maxResults": 1,
            "printType": "books",
        }

        data = await self._make_request("volumes", params)
        items = data.get("items", [])

        if not items:
            return None

        return self._map_to_candidate(items[0])

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
