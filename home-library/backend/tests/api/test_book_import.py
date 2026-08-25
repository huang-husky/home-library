"""
测试图书导入功能

运行: pytest tests/api/test_book_import.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.schemas import BookMetadataImport, BookImportRequest


@pytest.fixture
def sample_candidate():
    """示例候选图书数据"""
    return BookMetadataImport(
        source="google_books",
        source_id="abc123",
        title="三体",
        subtitle="地球往事三部曲之一",
        authors=["刘慈欣"],
        publisher="重庆出版社",
        publish_date="2008-01",
        publish_year=2008,
        isbn10="7536692935",
        isbn13="9787536692930",
        language="zh",
        page_count=302,
        cover_url="https://example.com/cover.jpg",
        description="文化大革命如火如荼进行的同时...",
    )


class TestBookImport:
    """测试图书导入 API"""

    @pytest.mark.anyio
    async def test_import_new_book(self, sample_candidate):
        """测试导入全新图书"""
        from app.api.books import import_book, _find_edition_by_source, _find_edition_by_isbn, _find_work_by_title

        # Mock 数据库操作
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()

        # 模拟未找到现有数据
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        import_request = BookImportRequest(candidate=sample_candidate)

        # 执行导入
        with patch('app.api.books._find_edition_by_source', return_value=None):
            with patch('app.api.books._find_edition_by_isbn', return_value=None):
                with patch('app.api.books._find_work_by_title', return_value=None):
                    with patch('app.api.books._find_existing_book', return_value=None):
                        response = await import_book(import_request, mock_db)

        assert response.success is True
        assert response.is_new_work is True
        assert response.is_new_edition is True
        assert response.is_new_book is True

    @pytest.mark.anyio
    async def test_import_duplicate_source_id(self, sample_candidate):
        """测试重复导入同一 source + source_id"""
        from app.api.books import import_book
        from app.models.models import Edition, Work

        # Mock 已存在的 Edition
        existing_work = Work(
            id=1,
            title="三体",
            language="zh",
        )
        existing_edition = Edition(
            id=1,
            work_id=1,
            title="三体",
            isbn13="9787536692930",
            source="google_books",
            source_id="abc123",
        )
        existing_edition.work = existing_work

        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing_edition)
        mock_db.execute.return_value = mock_result

        import_request = BookImportRequest(candidate=sample_candidate)

        with patch('app.api.books._find_existing_book', return_value=None):
            response = await import_book(import_request, mock_db)

        # 应该复用已有 Edition 和 Work
        assert response.is_new_edition is False
        assert response.is_new_work is False
        assert response.edition_id == 1
        assert response.work_id == 1

    @pytest.mark.anyio
    async def test_import_duplicate_isbn(self, sample_candidate):
        """测试使用相同 ISBN 导入"""
        from app.api.books import import_book
        from app.models.models import Edition, Work

        existing_work = Work(id=1, title="三体", language="zh")
        existing_edition = Edition(
            id=1,
            work_id=1,
            title="三体",
            isbn13="9787536692930",
            source="open_library",  # 不同 source
            source_id="different_id",
        )
        existing_edition.work = existing_work

        mock_db = MagicMock()

        # 第一个查询（source + source_id）返回 None
        # 第二个查询（ISBN）返回已有 edition
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none = MagicMock(return_value=None)

        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none = MagicMock(return_value=existing_edition)

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        import_request = BookImportRequest(candidate=sample_candidate)

        with patch('app.api.books._find_existing_book', return_value=None):
            response = await import_book(import_request, mock_db)

        # 应该通过 ISBN 找到已有 Edition
        assert response.is_new_edition is False
        assert response.is_new_work is False

    @pytest.mark.anyio
    async def test_import_invalid_source(self, sample_candidate):
        """测试非法数据来源"""
        from app.api.books import import_book
        from fastapi import HTTPException

        mock_db = MagicMock()

        # 修改 candidate 的 source 为非法值
        invalid_candidate = sample_candidate.model_copy(update={"source": "invalid_source"})
        import_request = BookImportRequest(candidate=invalid_candidate)

        with pytest.raises(HTTPException) as exc_info:
            await import_book(import_request, mock_db)

        assert exc_info.value.status_code == 400
        assert "Invalid metadata source" in exc_info.value.detail

    @pytest.mark.anyio
    async def test_import_with_tags(self, sample_candidate):
        """测试导入时添加标签"""
        from app.api.books import import_book, _add_tags_to_book
        from app.models.models import Book, Tag

        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        # 模拟未找到现有数据
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        import_request = BookImportRequest(
            candidate=sample_candidate,
            tags=["科幻", "中国"],
        )

        with patch('app.api.books._find_edition_by_source', return_value=None):
            with patch('app.api.books._find_edition_by_isbn', return_value=None):
                with patch('app.api.books._find_work_by_title', return_value=None):
                    with patch('app.api.books._find_existing_book', return_value=None):
                        response = await import_book(import_request, mock_db)

        assert response.success is True

    @pytest.mark.anyio
    async def test_import_with_shelf(self, sample_candidate):
        """测试导入到指定书架"""
        from app.api.books import import_book

        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        import_request = BookImportRequest(
            candidate=sample_candidate,
            shelf_id=1,
            owner="张三",
            notes="珍藏版",
        )

        with patch('app.api.books._find_edition_by_source', return_value=None):
            with patch('app.api.books._find_edition_by_isbn', return_value=None):
                with patch('app.api.books._find_work_by_title', return_value=None):
                    with patch('app.api.books._find_existing_book', return_value=None):
                        response = await import_book(import_request, mock_db)

        assert response.success is True
        assert response.is_new_book is True


class TestImportEdgeCases:
    """测试导入边界情况"""

    @pytest.mark.anyio
    async def test_import_without_isbn(self):
        """测试导入没有 ISBN 的图书"""
        from app.api.books import import_book

        candidate = BookMetadataImport(
            source="google_books",
            source_id="no_isbn_123",
            title="古老书籍",
            authors=["佚名"],
            publisher="古籍出版社",
        )

        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        import_request = BookImportRequest(candidate=candidate)

        with patch('app.api.books._find_edition_by_source', return_value=None):
            with patch('app.api.books._find_edition_by_isbn', return_value=None):
                with patch('app.api.books._find_work_by_title', return_value=None):
                    with patch('app.api.books._find_existing_book', return_value=None):
                        response = await import_book(import_request, mock_db)

        assert response.success is True
        assert response.is_new_work is True
        assert response.is_new_edition is True

    @pytest.mark.anyio
    async def test_import_minimal_data(self):
        """测试导入最少数据（只有标题）"""
        from app.api.books import import_book
        from fastapi import HTTPException

        candidate = BookMetadataImport(
            source="google_books",
            source_id="minimal_123",
            title="只有标题的书",
        )

        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        import_request = BookImportRequest(candidate=candidate)

        with patch('app.api.books._find_edition_by_source', return_value=None):
            with patch('app.api.books._find_edition_by_isbn', return_value=None):
                with patch('app.api.books._find_work_by_title', return_value=None):
                    with patch('app.api.books._find_existing_book', return_value=None):
                        response = await import_book(import_request, mock_db)

        assert response.success is True

    @pytest.mark.anyio
    async def test_reimport_same_edition(self, sample_candidate):
        """测试重复导入同一 Edition 不创建重复 Book"""
        from app.api.books import import_book
        from app.models.models import Edition, Work, Book

        existing_work = Work(id=1, title="三体", language="zh")
        existing_edition = Edition(
            id=1,
            work_id=1,
            title="三体",
            isbn13="9787536692930",
            source="google_books",
            source_id="abc123",
        )
        existing_book = Book(
            id=1,
            edition_id=1,
            status="available",
        )

        mock_db = MagicMock()

        # 模拟找到已有数据
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing_edition)
        mock_db.execute.return_value = mock_result

        import_request = BookImportRequest(candidate=sample_candidate)

        with patch('app.api.books._find_existing_book', return_value=existing_book):
            response = await import_book(import_request, mock_db)

        # 应该复用已有 Book
        assert response.is_new_book is False
        assert response.book_id == 1
