"""
测试 Metadata Service

运行: pytest tests/services/metadata/ -v
"""
import pytest
import anyio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.metadata import (
    MetadataService,
    GoogleBooksProvider,
    OpenLibraryProvider,
    BookMetadataCandidate,
    MetadataSearchResult,
    ISBNLookupResult,
)


# ============= Fixtures =============

@pytest.fixture
def sample_google_book():
    """Google Books API 返回的示例数据"""
    return {
        "id": "abc123",
        "volumeInfo": {
            "title": "三体",
            "subtitle": "地球往事三部曲之一",
            "authors": ["刘慈欣"],
            "publisher": "重庆出版社",
            "publishedDate": "2008-01",
            "description": "文化大革命如火如荼进行的同时...",
            "industryIdentifiers": [
                {"type": "ISBN_10", "identifier": "7536692935"},
                {"type": "ISBN_13", "identifier": "9787536692930"},
            ],
            "pageCount": 302,
            "language": "zh",
            "imageLinks": {
                "thumbnail": "https://example.com/cover.jpg",
            },
        },
    }


@pytest.fixture
def sample_openlibrary_doc():
    """Open Library 搜索结果示例数据"""
    return {
        "key": "/works/OL123456W",
        "title": "三体",
        "author_name": ["刘慈欣"],
        "first_publish_year": 2008,
        "publisher": ["重庆出版社"],
        "isbn": ["9787536692930", "7536692935"],
        "cover_i": 12345,
        "language": ["chi"],
    }


@pytest.fixture
def mock_google_provider():
    """Mock Google Books Provider"""
    provider = MagicMock(spec=GoogleBooksProvider)
    provider.name = "google_books"
    provider.timeout = 10.0
    return provider


@pytest.fixture
def mock_openlibrary_provider():
    """Mock Open Library Provider"""
    provider = MagicMock(spec=OpenLibraryProvider)
    provider.name = "open_library"
    provider.timeout = 10.0
    return provider


# ============= DTO Tests =============

class TestBookMetadataCandidate:
    """测试 BookMetadataCandidate DTO"""

    def test_create_candidate(self):
        """测试创建候选对象"""
        candidate = BookMetadataCandidate(
            source="test",
            source_id="123",
            title="Test Book",
            authors=["Author 1", "Author 2"],
            isbn13="9781234567890",
        )

        assert candidate.source == "test"
        assert candidate.title == "Test Book"
        assert len(candidate.authors) == 2
        assert candidate.isbn13 == "9781234567890"

    def test_candidate_with_all_fields(self):
        """测试完整字段的候选对象"""
        candidate = BookMetadataCandidate(
            source="google_books",
            source_id="abc",
            title="三体",
            subtitle="地球往事",
            authors=["刘慈欣"],
            publisher="重庆出版社",
            publish_date="2008-01",
            publish_year=2008,
            isbn10="7536692935",
            isbn13="9787536692930",
            language="zh",
            page_count=302,
            cover_url="https://example.com/cover.jpg",
            description="A great book",
        )

        assert candidate.publish_year == 2008
        assert candidate.page_count == 302


# ============= GoogleBooksProvider Tests =============

class TestGoogleBooksProvider:
    """测试 Google Books Provider"""

    @pytest.mark.anyio
    async def test_map_to_candidate(self, sample_google_book):
        """测试数据映射"""
        provider = GoogleBooksProvider()

        candidate = provider._map_to_candidate(sample_google_book)

        assert candidate.source == "google_books"
        assert candidate.source_id == "abc123"
        assert candidate.title == "三体"
        assert candidate.subtitle == "地球往事三部曲之一"
        assert candidate.authors == ["刘慈欣"]
        assert candidate.publisher == "重庆出版社"
        assert candidate.isbn10 == "7536692935"
        assert candidate.isbn13 == "9787536692930"
        assert candidate.page_count == 302
        assert candidate.language == "zh"
        assert candidate.publish_year == 2008

    @pytest.mark.anyio
    async def test_extract_isbn(self):
        """测试 ISBN 提取"""
        provider = GoogleBooksProvider()

        identifiers = [
            {"type": "ISBN_10", "identifier": "1234567890"},
            {"type": "ISBN_13", "identifier": "9781234567890"},
        ]

        isbn10, isbn13 = provider._extract_isbn(identifiers)

        assert isbn10 == "1234567890"
        assert isbn13 == "9781234567890"

    @pytest.mark.anyio
    async def test_extract_year(self):
        """测试年份提取"""
        provider = GoogleBooksProvider()

        assert provider._extract_year("2008-01") == 2008
        assert provider._extract_year("2020") == 2020
        assert provider._extract_year("") is None
        assert provider._extract_year(None) is None

    @pytest.mark.anyio
    @patch("httpx.AsyncClient.get")
    async def test_search_by_title_success(self, mock_get, sample_google_book):
        """测试书名搜索成功"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": [sample_google_book]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        async with GoogleBooksProvider() as provider:
            results = await provider.search_by_title("三体", max_results=5)

        assert len(results) == 1
        assert results[0].title == "三体"
        assert results[0].source == "google_books"

    @pytest.mark.anyio
    @patch("httpx.AsyncClient.get")
    async def test_search_by_isbn_success(self, mock_get, sample_google_book):
        """测试 ISBN 搜索成功"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": [sample_google_book]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        async with GoogleBooksProvider() as provider:
            result = await provider.search_by_isbn("9787536692930")

        assert result is not None
        assert result.isbn13 == "9787536692930"
        assert result.title == "三体"

    @pytest.mark.anyio
    @patch("httpx.AsyncClient.get")
    async def test_search_by_isbn_not_found(self, mock_get):
        """测试 ISBN 搜索未找到"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        async with GoogleBooksProvider() as provider:
            result = await provider.search_by_isbn("9780000000000")

        assert result is None


# ============= OpenLibraryProvider Tests =============

class TestOpenLibraryProvider:
    """测试 Open Library Provider"""

    @pytest.mark.anyio
    async def test_map_search_result_to_candidate(self, sample_openlibrary_doc):
        """测试搜索结果映射"""
        provider = OpenLibraryProvider()

        candidate = provider._map_search_result_to_candidate(sample_openlibrary_doc)

        assert candidate.source == "open_library"
        assert candidate.title == "三体"
        assert candidate.authors == ["刘慈欣"]
        assert candidate.isbn13 == "9787536692930"
        assert candidate.isbn10 == "7536692935"
        assert candidate.publish_year == 2008
        assert candidate.cover_url is not None

    @pytest.mark.anyio
    async def test_extract_cover_url(self):
        """测试封面 URL 提取"""
        provider = OpenLibraryProvider()

        url = provider._extract_cover_url([12345])
        assert url == "https://covers.openlibrary.org/b/id/12345-M.jpg"

        no_url = provider._extract_cover_url([])
        assert no_url is None

    @pytest.mark.anyio
    @patch("httpx.AsyncClient.get")
    async def test_search_by_title_success(self, mock_get, sample_openlibrary_doc):
        """测试书名搜索成功"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"docs": [sample_openlibrary_doc]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        async with OpenLibraryProvider() as provider:
            results = await provider.search_by_title("三体", max_results=5)

        assert len(results) == 1
        assert results[0].title == "三体"
        assert results[0].source == "open_library"


# ============= MetadataService Tests =============

class TestMetadataService:
    """测试 Metadata Service"""

    @pytest.mark.anyio
    async def test_deduplicate_candidates(self):
        """测试去重功能"""
        service = MetadataService(providers=[])

        candidates = [
            BookMetadataCandidate(source="a", source_id="1", title="Book 1", isbn13="9781111111111"),
            BookMetadataCandidate(source="b", source_id="2", title="Book 1 Dup", isbn13="9781111111111"),  # 重复
            BookMetadataCandidate(source="c", source_id="3", title="Book 2", isbn13="9782222222222"),
        ]

        unique = service._deduplicate_candidates(candidates)

        assert len(unique) == 2
        assert unique[0].source == "a"  # 保留第一个

    @pytest.mark.anyio
    async def test_deduplicate_with_isbn10(self):
        """测试使用 ISBN-10 去重"""
        service = MetadataService(providers=[])

        candidates = [
            BookMetadataCandidate(source="a", source_id="1", title="Book 1", isbn10="1111111111"),
            BookMetadataCandidate(source="b", source_id="2", title="Book 1 Dup", isbn10="1111111111"),
        ]

        unique = service._deduplicate_candidates(candidates)

        assert len(unique) == 1

    @pytest.mark.anyio
    async def test_search_by_isbn_fallback(self, mock_google_provider, mock_openlibrary_provider):
        """测试 ISBN 搜索 fallback"""
        # Google Books 失败，Open Library 成功
        mock_google_provider.search_by_isbn = AsyncMock(return_value=None)

        openlib_result = BookMetadataCandidate(
            source="open_library",
            source_id="ol123",
            title="Test Book",
            isbn13="9781234567890",
        )
        mock_openlibrary_provider.search_by_isbn = AsyncMock(return_value=openlib_result)

        service = MetadataService(providers=[mock_google_provider, mock_openlibrary_provider])

        result = await service.search_by_isbn("9781234567890")

        assert result.found is True
        assert result.source == "open_library"
        assert result.candidate.isbn13 == "9781234567890"

    @pytest.mark.anyio
    async def test_search_by_isbn_all_fail(self, mock_google_provider, mock_openlibrary_provider):
        """测试所有 Provider 都失败"""
        mock_google_provider.search_by_isbn = AsyncMock(side_effect=Exception("Timeout"))
        mock_openlibrary_provider.search_by_isbn = AsyncMock(return_value=None)

        service = MetadataService(providers=[mock_google_provider, mock_openlibrary_provider])

        result = await service.search_by_isbn("9781234567890")

        assert result.found is False
        assert result.candidate is None

    @pytest.mark.anyio
    async def test_search_auto_detect_isbn(self, mock_google_provider, mock_openlibrary_provider):
        """测试自动检测 ISBN"""
        google_result = BookMetadataCandidate(
            source="google_books",
            source_id="gb123",
            title="Test Book",
            isbn13="9781234567890",
        )
        mock_google_provider.search_by_isbn = AsyncMock(return_value=google_result)

        service = MetadataService(providers=[mock_google_provider])

        # 使用带横杠的 ISBN
        result = await service.search("978-1-234-56789-0")

        assert result.total_found == 1
        assert result.candidates[0].isbn13 == "9781234567890"

    @pytest.mark.anyio
    async def test_search_by_title_fallback(self, mock_google_provider, mock_openlibrary_provider):
        """测试书名搜索 fallback"""
        # Google Books 失败
        mock_google_provider.search_by_title = AsyncMock(side_effect=Exception("Timeout"))

        # Open Library 成功
        openlib_result = [
            BookMetadataCandidate(
                source="open_library",
                source_id="ol1",
                title="Test Book",
                isbn13="9781234567890",
            )
        ]
        mock_openlibrary_provider.search_by_title = AsyncMock(return_value=openlib_result)

        service = MetadataService(providers=[mock_google_provider, mock_openlibrary_provider])

        result = await service.search_by_title("Test Book")

        assert result.total_found == 1
        assert result.candidates[0].source == "open_library"

    @pytest.mark.anyio
    async def test_search_by_author_title(self, mock_google_provider, mock_openlibrary_provider):
        """测试作者+书名搜索"""
        google_result = [
            BookMetadataCandidate(
                source="google_books",
                source_id="gb1",
                title="三体",
                authors=["刘慈欣"],
            )
        ]
        mock_google_provider.search_by_author_title = AsyncMock(return_value=google_result)
        mock_openlibrary_provider.search_by_author_title = AsyncMock(return_value=[])

        service = MetadataService(providers=[mock_google_provider, mock_openlibrary_provider])

        result = await service.search_by_author_title("刘慈欣", "三体")

        assert result.total_found == 1
        assert result.query == "刘慈欣 三体"


# ============= Integration Tests =============

@pytest.mark.anyio
class TestMetadataIntegration:
    """
    集成测试

    这些测试会实际调用外部 API，默认跳过。
    运行: pytest tests/services/metadata/ -v --run-integration
    """

    @pytest.mark.integration
    async def test_google_books_live_search(self):
        """测试真实的 Google Books API"""
        async with GoogleBooksProvider(timeout=15.0) as provider:
            results = await provider.search_by_title("三体", max_results=3)

        assert len(results) > 0
        print(f"\nGoogle Books found {len(results)} results")
        for r in results:
            print(f"  - {r.title} by {', '.join(r.authors)}")

    @pytest.mark.integration
    async def test_open_library_live_search(self):
        """测试真实的 Open Library API"""
        async with OpenLibraryProvider(timeout=15.0) as provider:
            results = await provider.search_by_title("三体", max_results=3)

        assert len(results) >= 0
        print(f"\nOpen Library found {len(results)} results")
        for r in results:
            print(f"  - {r.title} by {', '.join(r.authors)}")

    @pytest.mark.integration
    async def test_service_live_search(self):
        """测试真实的 MetadataService"""
        async with MetadataService(timeout=15.0) as service:
            result = await service.search("三体", max_results=5)

        print(f"\nMetadataService found {result.total_found} results from {result.sources}")
        for c in result.candidates[:3]:
            print(f"  [{c.source}] {c.title} by {', '.join(c.authors)}")

    @pytest.mark.integration
    async def test_service_live_isbn(self):
        """测试真实的 ISBN 查询"""
        # 三体的 ISBN
        isbn = "9787536692930"

        async with MetadataService(timeout=15.0) as service:
            result = await service.search_by_isbn(isbn)

        if result.found:
            print(f"\nFound by {result.source}:")
            c = result.candidate
            print(f"  Title: {c.title}")
            print(f"  Authors: {', '.join(c.authors)}")
            print(f"  Publisher: {c.publisher}")
        else:
            print(f"\nISBN {isbn} not found")


# ============= API Tests =============

class TestMetadataAPI:
    """测试 Metadata API 路由"""

    @pytest.mark.anyio
    async def test_search_endpoint(self, mock_google_provider):
        """测试搜索端点"""
        from app.api.metadata import search_metadata

        google_result = MetadataSearchResult(
            query="三体",
            candidates=[
                BookMetadataCandidate(
                    source="google_books",
                    source_id="gb1",
                    title="三体",
                    authors=["刘慈欣"],
                )
            ],
            total_found=1,
            sources=["google_books"],
        )

        with patch("app.api.metadata.get_metadata_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.search = AsyncMock(return_value=google_result)
            mock_service.search_by_author_title = AsyncMock(return_value=google_result)
            mock_get_service.return_value = mock_service

            result = await search_metadata(q="三体", max_results=10)

            assert result.total_found == 1
            assert result.candidates[0].title == "三体"

    @pytest.mark.anyio
    async def test_isbn_endpoint(self, mock_google_provider):
        """测试 ISBN 端点"""
        from app.api.metadata import search_by_isbn

        candidate = BookMetadataCandidate(
            source="google_books",
            source_id="gb1",
            title="三体",
            isbn13="9787536692930",
        )
        isbn_result = ISBNLookupResult(
            isbn="9787536692930",
            found=True,
            candidate=candidate,
            source="google_books",
        )

        with patch("app.api.metadata.get_metadata_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.search_by_isbn = AsyncMock(return_value=isbn_result)
            mock_get_service.return_value = mock_service

            result = await search_by_isbn("9787536692930")

            assert result.found is True
            assert result.candidate.isbn13 == "9787536692930"
