"""
Recognition Service

整合 Vision + OCR + LLM Provider 提供完整的图书识别服务
"""
import logging
from typing import List, Optional, Dict, Any
from io import BytesIO
from PIL import Image

from app.services.ai.vision_provider import VisionProvider
from app.services.ai.ocr_provider import OCRProvider
from app.services.ai.llm_provider import LLMProvider
from app.services.ai.mock_providers import (
    MockVisionProvider,
    MockOCRProvider,
    MockLLMProvider,
)
from app.services.ai.dto import (
    ImageAnalysisResult,
    RecognitionResult,
    BookDetectionResult,
    ClassificationResult,
    EditionMatchResult,
    BoundingBox,
)
from app.services.metadata import MetadataService

logger = logging.getLogger(__name__)


class RecognitionService:
    """
    图书识别服务

    整合多个 AI Provider，提供端到端的图书识别能力：
    1. 检测图片中的书籍位置
    2. OCR 识别书籍文字
    3. 与元数据匹配
    4. 分类图书

    Usage:
        service = RecognitionService()

        # 分析书柜图片
        result = await service.analyze_bookshelf(image)

        # 识别单本书籍
        book_info = await service.recognize_book(image)
    """

    def __init__(
        self,
        vision_provider: Optional[VisionProvider] = None,
        ocr_provider: Optional[OCRProvider] = None,
        llm_provider: Optional[LLMProvider] = None,
        metadata_service: Optional[MetadataService] = None,
    ):
        """
        初始化 Recognition Service

        Args:
            vision_provider: 视觉模型 Provider（None 则使用 Mock）
            ocr_provider: OCR Provider（None 则使用 Mock）
            llm_provider: LLM Provider（None 则使用 Mock）
            metadata_service: 元数据服务
        """
        self.vision = vision_provider or MockVisionProvider()
        self.ocr = ocr_provider or MockOCRProvider()
        self.llm = llm_provider or MockLLMProvider()
        self.metadata = metadata_service or MetadataService()

        logger.info(
            f"RecognitionService initialized with "
            f"vision={self.vision.name}, ocr={self.ocr.name}, llm={self.llm.name}"
        )

    async def analyze_bookshelf(
        self,
        image: Image.Image,
        match_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        分析书柜图片，返回检测到的所有书籍信息

        Args:
            image: PIL Image 对象
            match_metadata: 是否匹配元数据

        Returns:
            包含检测结果的完整字典
        """
        logger.info(f"Analyzing bookshelf image: {image.size}")

        try:
            # 1. Vision: 检测书籍位置
            analysis = await self.vision.analyze_image(
                image,
                detect_books=True,
                extract_features=True,
            )

            books = []
            for detection in analysis.detected_books:
                book_info = {
                    "detected_id": detection.detected_id,
                    "bbox": detection.bbox.model_dump(),
                    "confidence": detection.confidence,
                    "text": detection.text,
                }

                # 2. OCR: 精确识别文字（如果需要）
                if not detection.text:
                    ocr_results = await self._ocr_book_region(image, detection.bbox)
                    book_info["ocr_results"] = [r.model_dump() for r in ocr_results]

                # 3. Metadata: 匹配元数据
                if match_metadata and (detection.text or book_info.get("ocr_results")):
                    matches = await self._match_metadata(detection.text or "")
                    book_info["metadata_matches"] = [m.model_dump() for m in matches]

                books.append(book_info)

            return {
                "success": True,
                "total_books": len(books),
                "books": books,
                "image_quality": analysis.image_quality,
                "processing_time_ms": analysis.processing_time_ms,
                "source": analysis.source,
            }

        except Exception as e:
            logger.error(f"Bookshelf analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_books": 0,
                "books": [],
            }

    async def recognize_book(
        self,
        image: Image.Image,
    ) -> Dict[str, Any]:
        """
        识别单本书籍（封面或书脊）

        Args:
            image: PIL Image 对象

        Returns:
            识别结果字典
        """
        logger.info(f"Recognizing single book: {image.size}")

        try:
            # 1. OCR: 识别文字
            ocr_results = await self.ocr.recognize_text(image, return_bbox=True)

            # 2. 提取关键信息
            all_text = " ".join([r.text for r in ocr_results])
            isbn_result = await self.ocr.recognize_isbn(image)

            # 3. Metadata: 优先用 ISBN 查询
            if isbn_result:
                metadata_result = await self.metadata.search_by_isbn(isbn_result.text)
                if metadata_result.found:
                    return {
                        "success": True,
                        "source": "isbn_lookup",
                        "isbn": isbn_result.text,
                        "candidate": metadata_result.candidate.model_dump(),
                        "ocr_text": all_text,
                        "confidence": isbn_result.confidence,
                    }

            # 4. LLM: 提取元数据并搜索
            extracted = await self.llm.extract_metadata(all_text)
            if extracted.get("title"):
                search_result = await self.metadata.search_by_title(
                    extracted["title"],
                    max_results=3,
                )
                if search_result.candidates:
                    return {
                        "success": True,
                        "source": "text_search",
                        "extracted_metadata": extracted,
                        "candidates": [c.model_dump() for c in search_result.candidates],
                        "ocr_results": [r.model_dump() for r in ocr_results],
                    }

            # 5. 返回原始 OCR 结果
            return {
                "success": True,
                "source": "ocr_only",
                "ocr_results": [r.model_dump() for r in ocr_results],
                "extracted_metadata": extracted,
            }

        except Exception as e:
            logger.error(f"Book recognition failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def test_recognition(
        self,
        image: Image.Image,
    ) -> Dict[str, Any]:
        """
        测试识别流程，返回所有中间结果

        Args:
            image: PIL Image 对象

        Returns:
            详细的测试结果
        """
        logger.info(f"Running recognition test: {image.size}")

        result = {
            "success": True,
            "image_info": {
                "size": image.size,
                "mode": image.mode,
            },
            "vision": None,
            "ocr": None,
            "llm": None,
            "metadata": None,
        }

        # 1. Vision
        try:
            vision_result = await self.vision.analyze_image(image)
            result["vision"] = {
                "success": True,
                "detected_books": len(vision_result.detected_books),
                "books": [
                    {
                        "id": b.detected_id,
                        "confidence": b.confidence,
                        "text": b.text,
                        "bbox": b.bbox.model_dump() if b.bbox else None,
                    }
                    for b in vision_result.detected_books
                ],
            }
        except Exception as e:
            result["vision"] = {"success": False, "error": str(e)}

        # 2. OCR
        try:
            ocr_results = await self.ocr.recognize_text(image)
            result["ocr"] = {
                "success": True,
                "texts": [r.text for r in ocr_results],
                "details": [r.model_dump() for r in ocr_results],
            }
        except Exception as e:
            result["ocr"] = {"success": False, "error": str(e)}

        # 3. LLM
        try:
            if ocr_results:
                classification = await self.llm.classify_book(
                    title=ocr_results[0].text if ocr_results else "Unknown",
                )
                result["llm"] = {
                    "success": True,
                    "classification": classification.model_dump(),
                }
        except Exception as e:
            result["llm"] = {"success": False, "error": str(e)}

        # 4. Metadata
        try:
            if ocr_results:
                search_result = await self.metadata.search(
                    ocr_results[0].text,
                    max_results=3,
                )
                result["metadata"] = {
                    "success": True,
                    "candidates_found": search_result.total_found,
                    "candidates": [c.model_dump() for c in search_result.candidates],
                }
        except Exception as e:
            result["metadata"] = {"success": False, "error": str(e)}

        return result

    async def _ocr_book_region(
        self,
        image: Image.Image,
        bbox: BoundingBox,
    ) -> List[RecognitionResult]:
        """
        对图片特定区域进行 OCR

        Args:
            image: 原图
            bbox: 区域边界框

        Returns:
            OCR 结果列表
        """
        width, height = image.size

        # 裁剪区域
        left = int(bbox.x * width)
        top = int(bbox.y * height)
        right = int((bbox.x + bbox.width) * width)
        bottom = int((bbox.y + bbox.height) * height)

        try:
            region = image.crop((left, top, right, bottom))
            return await self.ocr.recognize_book_spine(region) or []
        except Exception as e:
            logger.warning(f"OCR region failed: {e}")
            return []

    async def _match_metadata(
        self,
        text: str,
    ) -> List[EditionMatchResult]:
        """
        将 OCR 文本与元数据匹配

        Args:
            text: OCR 识别的文本

        Returns:
            匹配结果列表
        """
        try:
            # 搜索元数据
            search_result = await self.metadata.search(text, max_results=5)

            if not search_result.candidates:
                return []

            # 转换为匹配结果格式
            candidates_data = [
                {
                    "id": i,
                    "title": c.title,
                    "authors": c.authors,
                    "isbn13": c.isbn13,
                }
                for i, c in enumerate(search_result.candidates)
            ]

            # 使用 LLM 匹配
            ocr_results = [RecognitionResult(text=text, confidence=0.9, source="ocr")]
            matches = await self.llm.match_edition(ocr_results, candidates_data)

            return matches

        except Exception as e:
            logger.warning(f"Metadata matching failed: {e}")
            return []

    async def health_check(self) -> Dict[str, bool]:
        """
        检查所有 Provider 健康状态

        Returns:
            各 Provider 健康状态字典
        """
        return {
            "vision": await self.vision.health_check(),
            "ocr": await self.ocr.health_check(),
            "llm": await self.llm.health_check(),
        }

    async def close(self):
        """关闭所有 Provider"""
        await self.vision.__aexit__(None, None, None)
        await self.ocr.__aexit__(None, None, None)
        await self.llm.__aexit__(None, None, None)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return False
