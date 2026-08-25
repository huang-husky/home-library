"""
Mock AI Providers

用于测试和业务链路验证的 Mock Provider
返回固定但合理的测试结果
"""
import uuid
import random
from typing import List, Optional, Dict, Any
from PIL import Image

from app.services.ai.vision_provider import VisionProvider
from app.services.ai.ocr_provider import OCRProvider
from app.services.ai.llm_provider import LLMProvider
from app.services.ai.dto import (
    ImageAnalysisResult,
    BookDetectionResult,
    RecognitionResult,
    ClassificationResult,
    EditionMatchResult,
    SemanticSearchResult,
    BoundingBox,
)


class MockVisionProvider(VisionProvider):
    """
    Mock Vision Provider

    返回固定的模拟检测结果，用于测试业务链路
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mock_books = [
            {"title": "三体", "confidence": 0.92},
            {"title": "百年孤独", "confidence": 0.88},
            {"title": "人类简史", "confidence": 0.85},
            {"title": "深入理解计算机系统", "confidence": 0.90},
            {"title": "设计模式", "confidence": 0.87},
        ]

    async def analyze_image(
        self,
        image: Image.Image,
        detect_books: bool = True,
        extract_features: bool = False,
    ) -> ImageAnalysisResult:
        """模拟图片分析"""
        width, height = image.size

        detected_books = []
        if detect_books:
            # 模拟检测 3-5 本书
            num_books = random.randint(3, 5)
            for i in range(num_books):
                book = self._mock_books[i % len(self._mock_books)]
                detected_books.append(
                    BookDetectionResult(
                        detected_id=f"mock_{uuid.uuid4().hex[:8]}",
                        bbox=BoundingBox(
                            x=0.1 + i * 0.15,
                            y=0.2,
                            width=0.12,
                            height=0.6,
                            pixel_x=int((0.1 + i * 0.15) * width),
                            pixel_y=int(0.2 * height),
                            pixel_width=int(0.12 * width),
                            pixel_height=int(0.6 * height),
                        ),
                        confidence=book["confidence"],
                        text=book["title"],
                        text_confidence=0.8 + random.random() * 0.15,
                        source=self._name,
                        metadata={"mock": True, "index": i},
                    )
                )

        return ImageAnalysisResult(
            detected_books=detected_books,
            total_books=len(detected_books),
            image_quality=0.85 + random.random() * 0.1,
            processing_time_ms=random.randint(200, 800),
            source=self._name,
            model_version="mock-v1.0",
            metadata={"mock": True, "image_size": f"{width}x{height}"},
        )

    async def detect_books(
        self,
        image: Image.Image,
        confidence_threshold: float = 0.5,
    ) -> List[BookDetectionResult]:
        """模拟书籍检测"""
        result = await self.analyze_image(image, detect_books=True)
        return [
            book for book in result.detected_books
            if book.confidence >= confidence_threshold
        ]

    async def health_check(self) -> bool:
        """Mock Provider 永远健康"""
        return True


class MockOCRProvider(OCRProvider):
    """
    Mock OCR Provider

    返回固定的模拟 OCR 结果
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mock_texts = [
            ("三体", 0.94),
            ("刘慈欣 著", 0.89),
            ("重庆出版社", 0.87),
            ("ISBN 978-7-5366-9293-0", 0.92),
            ("百年孤独", 0.91),
            ("加西亚·马尔克斯", 0.85),
        ]

    async def recognize_text(
        self,
        image: Image.Image,
        return_bbox: bool = True,
    ) -> List[RecognitionResult]:
        """模拟文字识别"""
        width, height = image.size

        results = []
        num_texts = random.randint(2, 4)

        for i in range(num_texts):
            text, conf = self._mock_texts[i % len(self._mock_texts)]
            bbox = BoundingBox(
                x=0.1 + i * 0.2,
                y=0.3 + i * 0.1,
                width=0.3,
                height=0.08,
                pixel_x=int((0.1 + i * 0.2) * width),
                pixel_y=int((0.3 + i * 0.1) * height),
                pixel_width=int(0.3 * width),
                pixel_height=int(0.08 * height),
            ) if return_bbox else None

            results.append(
                RecognitionResult(
                    text=text,
                    confidence=conf,
                    bbox=bbox,
                    source=self._name,
                    language="zh",
                    metadata={"mock": True, "char_count": len(text)},
                )
            )

        return results

    async def recognize_book_spine(
        self,
        image: Image.Image,
    ) -> Optional[RecognitionResult]:
        """模拟书脊文字识别"""
        return RecognitionResult(
            text="三体",
            confidence=0.92,
            source=self._name,
            language="zh",
            metadata={"type": "book_spine", "mock": True},
        )

    async def health_check(self) -> bool:
        """Mock Provider 永远健康"""
        return True


class MockLLMProvider(LLMProvider):
    """
    Mock LLM Provider

    返回固定的模拟 LLM 结果
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mock_categories = [
            {"code": "I247.5", "name": "长篇小说", "confidence": 0.91},
            {"code": "G303", "name": "未来学", "confidence": 0.85},
            {"code": "TP3", "name": "计算技术、计算机技术", "confidence": 0.88},
        ]

    async def classify_book(
        self,
        title: str,
        description: Optional[str] = None,
        author: Optional[str] = None,
        categories: Optional[List[Dict[str, str]]] = None,
    ) -> ClassificationResult:
        """模拟图书分类"""
        # 根据标题关键词简单匹配
        if "三体" in title or "科幻" in (description or ""):
            cat = self._mock_categories[1]  # 未来学
        elif "计算机" in title or "编程" in title:
            cat = self._mock_categories[2]  # 计算机
        else:
            cat = self._mock_categories[0]  # 长篇小说

        return ClassificationResult(
            category_code=cat["code"],
            category_name=cat["name"],
            confidence=cat["confidence"],
            reason=f"根据标题 '{title}' 和作者 '{author}' 推断",
            alternatives=[
                {"code": c["code"], "name": c["name"], "confidence": c["confidence"] - 0.1}
                for c in self._mock_categories if c["code"] != cat["code"]
            ],
        )

    async def match_edition(
        self,
        ocr_results: List[RecognitionResult],
        candidates: List[Dict[str, Any]],
    ) -> List[EditionMatchResult]:
        """模拟版本匹配"""
        # 提取 OCR 文本
        ocr_text = " ".join([r.text for r in ocr_results])

        matches = []
        for i, candidate in enumerate(candidates[:5]):  # 最多匹配前 5 个
            # 简单模拟匹配逻辑
            confidence = 0.7 + random.random() * 0.25
            matches.append(
                EditionMatchResult(
                    candidate_id=candidate.get("id", i),
                    confidence=confidence,
                    reason=f"OCR 文本与候选 '{candidate.get('title', 'Unknown')}' 匹配",
                    matched_fields=["title"],
                    similarity_scores={"title": confidence, "author": confidence - 0.1},
                )
            )

        # 按置信度排序
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches

    async def semantic_search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> SemanticSearchResult:
        """模拟语义搜索"""
        # 模拟搜索结果
        results = []
        for i, doc in enumerate(documents[:top_k]):
            score = 0.8 + random.random() * 0.18 - (i * 0.05)
            results.append({
                "id": doc.get("id", i),
                "title": doc.get("title", "Unknown"),
                "score": max(0.0, score),
            })

        return SemanticSearchResult(
            query=query,
            results=results,
            total_found=len(results),
            search_time_ms=random.randint(100, 500),
            embedding_model="mock-embedding-v1",
        )

    async def correct_text(
        self,
        text: str,
        context: Optional[str] = None,
    ) -> str:
        """模拟文本纠错"""
        # 简单的模拟纠错
        corrections = {
            "三休": "三体",
            "刘慈欣": "刘慈欣",  # 已经是正确的
        }
        return corrections.get(text, text)

    async def extract_metadata(
        self,
        raw_text: str,
    ) -> Dict[str, Any]:
        """模拟元数据提取"""
        metadata = await super().extract_metadata(raw_text)

        # 添加模拟数据
        if "三体" in raw_text:
            metadata["title"] = "三体"
            metadata["author"] = "刘慈欣"

        return metadata

    async def health_check(self) -> bool:
        """Mock Provider 永远健康"""
        return True
