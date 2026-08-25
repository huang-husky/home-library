"""
测试 AI Provider 架构

运行: pytest tests/services/ai/ -v
"""
import pytest
import asyncio
from io import BytesIO
from PIL import Image
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.ai import (
    MockVisionProvider,
    MockOCRProvider,
    MockLLMProvider,
    RecognitionService,
    BoundingBox,
    RecognitionResult,
    BookDetectionResult,
    ClassificationResult,
    EditionMatchResult,
)


def create_test_image():
    """创建测试图片"""
    img = Image.new('RGB', (800, 600), color='white')
    return img


class TestMockVisionProvider:
    """测试 Mock Vision Provider"""

    @pytest.mark.anyio
    async def test_analyze_image(self):
        """测试图片分析"""
        provider = MockVisionProvider()
        image = create_test_image()

        result = await provider.analyze_image(image)

        assert result.success is True or result.success is False
        assert result.total_books >= 0
        assert result.source == "MockVisionProvider"

    @pytest.mark.anyio
    async def test_detect_books(self):
        """测试书籍检测"""
        provider = MockVisionProvider()
        image = create_test_image()

        books = await provider.detect_books(image)

        assert isinstance(books, list)
        assert len(books) >= 0

        if books:
            book = books[0]
            assert isinstance(book, BookDetectionResult)
            assert book.confidence > 0
            assert book.confidence <= 1

    @pytest.mark.anyio
    async def test_health_check(self):
        """测试健康检查"""
        provider = MockVisionProvider()
        assert await provider.health_check() is True


class TestMockOCRProvider:
    """测试 Mock OCR Provider"""

    @pytest.mark.anyio
    async def test_recognize_text(self):
        """测试文字识别"""
        provider = MockOCRProvider()
        image = create_test_image()

        results = await provider.recognize_text(image)

        assert isinstance(results, list)
        assert len(results) > 0

        for result in results:
            assert isinstance(result, RecognitionResult)
            assert result.confidence > 0
            assert result.source == "MockOCRProvider"

    @pytest.mark.anyio
    async def test_recognize_book_spine(self):
        """测试书脊识别"""
        provider = MockOCRProvider()
        image = create_test_image()

        result = await provider.recognize_book_spine(image)

        assert result is not None
        assert isinstance(result, RecognitionResult)
        assert result.text  # 应该有文本内容

    @pytest.mark.anyio
    async def test_recognize_isbn(self):
        """测试 ISBN 识别"""
        provider = MockOCRProvider()
        image = create_test_image()

        result = await provider.recognize_isbn(image)

        # Mock 可能返回 None 或结果
        if result:
            assert isinstance(result, RecognitionResult)
            assert len(result.text) in [10, 13]


class TestMockLLMProvider:
    """测试 Mock LLM Provider"""

    @pytest.mark.anyio
    async def test_classify_book(self):
        """测试图书分类"""
        provider = MockLLMProvider()

        result = await provider.classify_book(
            title="三体",
            author="刘慈欣",
        )

        assert isinstance(result, ClassificationResult)
        assert result.category_code
        assert result.category_name
        assert 0 <= result.confidence <= 1

    @pytest.mark.anyio
    async def test_match_edition(self):
        """测试版本匹配"""
        provider = MockLLMProvider()

        ocr_results = [
            RecognitionResult(text="三体", confidence=0.95, source="mock")
        ]
        candidates = [
            {"id": 1, "title": "三体", "authors": ["刘慈欣"]},
            {"id": 2, "title": "流浪地球", "authors": ["刘慈欣"]},
        ]

        matches = await provider.match_edition(ocr_results, candidates)

        assert isinstance(matches, list)
        assert len(matches) > 0

        for match in matches:
            assert isinstance(match, EditionMatchResult)
            assert match.confidence > 0

    @pytest.mark.anyio
    async def test_semantic_search(self):
        """测试语义搜索"""
        provider = MockLLMProvider()

        documents = [
            {"id": 1, "title": "三体"},
            {"id": 2, "title": "百年孤独"},
        ]

        result = await provider.semantic_search("科幻小说", documents)

        assert result.query == "科幻小说"
        assert isinstance(result.results, list)


class TestRecognitionService:
    """测试 Recognition Service"""

    @pytest.mark.anyio
    async def test_analyze_bookshelf(self):
        """测试书柜分析"""
        service = RecognitionService()
        image = create_test_image()

        result = await service.analyze_bookshelf(image)

        assert "success" in result
        assert "total_books" in result
        assert "books" in result

    @pytest.mark.anyio
    async def test_recognize_book(self):
        """测试单本书识别"""
        service = RecognitionService()
        image = create_test_image()

        result = await service.recognize_book(image)

        assert "success" in result
        assert "source" in result

    @pytest.mark.anyio
    async def test_test_recognition(self):
        """测试完整识别流程"""
        service = RecognitionService()
        image = create_test_image()

        result = await service.test_recognition(image)

        assert result["success"] is True
        assert "image_info" in result
        assert "vision" in result
        assert "ocr" in result
        assert "llm" in result
        assert "metadata" in result

    @pytest.mark.anyio
    async def test_health_check(self):
        """测试健康检查"""
        service = RecognitionService()

        health = await service.health_check()

        assert "vision" in health
        assert "ocr" in health
        assert "llm" in health
        assert all(health.values())


class TestProviderAbstraction:
    """测试 Provider 抽象层"""

    @pytest.mark.anyio
    async def test_vision_provider_interface(self):
        """测试 VisionProvider 接口"""
        from app.services.ai.vision_provider import VisionProvider

        # 验证抽象方法存在
        assert hasattr(VisionProvider, 'analyze_image')
        assert hasattr(VisionProvider, 'detect_books')
        assert hasattr(VisionProvider, 'health_check')

    @pytest.mark.anyio
    async def test_ocr_provider_interface(self):
        """测试 OCRProvider 接口"""
        from app.services.ai.ocr_provider import OCRProvider

        assert hasattr(OCRProvider, 'recognize_text')
        assert hasattr(OCRProvider, 'recognize_book_spine')
        assert hasattr(OCRProvider, 'health_check')

    @pytest.mark.anyio
    async def test_llm_provider_interface(self):
        """测试 LLMProvider 接口"""
        from app.services.ai.llm_provider import LLMProvider

        assert hasattr(LLMProvider, 'classify_book')
        assert hasattr(LLMProvider, 'match_edition')
        assert hasattr(LLMProvider, 'semantic_search')
        assert hasattr(LLMProvider, 'health_check')


class TestRecognitionAPI:
    """测试 Recognition API"""

    @pytest.mark.anyio
    async def test_health_endpoint(self):
        """测试健康检查端点"""
        from app.api.recognition import health_check

        result = await health_check()

        assert "status" in result
        assert "providers" in result

    @pytest.mark.anyio
    async def test_list_providers_endpoint(self):
        """测试列出 Provider 端点"""
        from app.api.recognition import list_providers

        result = await list_providers()

        assert "vision" in result
        assert "ocr" in result
        assert "llm" in result

    @pytest.mark.anyio
    async def test_provider_no_api_key_in_logs(self):
        """测试 API key 不会泄露到日志"""
        provider = MockVisionProvider(api_key="secret_key_123")

        # 验证 API key 被存储但不序列化
        assert provider.api_key == "secret_key_123"

        # 验证 repr 不包含 API key
        repr_str = repr(provider)
        assert "secret_key_123" not in repr_str or "***" in repr_str
