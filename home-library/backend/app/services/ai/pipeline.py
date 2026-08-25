"""
识别管道 - Phase 7 MVP
整合 Preprocessing → Detection → OCR
"""
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

from .mock_providers import MockVisionProvider, MockOCRProvider


class RecognitionPipeline:
    """
    书架图片识别管道

    Pipeline:
        Image → Preprocessing → Book Detection → OCR → RecognitionResults
    """

    def __init__(self):
        self.vision = MockVisionProvider()
        self.ocr = MockOCRProvider()

    async def recognize_shelf(
        self,
        image: Image.Image,
        preprocess: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        识别书架图片中的所有书籍

        Args:
            image: PIL Image 对象
            preprocess: 是否进行预处理

        Returns:
            识别结果列表，每项包含:
            - detected_id: 检测序号
            - text: 识别文本
            - confidence: 置信度
            - bbox: 边界框 {x, y, width, height} (归一化 0~1)
            - source: 识别来源
        """
        results = []

        # 1. 预处理
        if preprocess:
            processed_image = self._preprocess(image)
        else:
            processed_image = image

        # 2. 检测书籍区域
        detections = await self.vision.detect_books(processed_image)

        # 3. 对每个检测区域进行 OCR
        for i, detection in enumerate(detections):
            # 裁剪出单本书的区域
            book_image = self._crop_book(processed_image, detection.bbox)

            # OCR 识别
            ocr_results = await self.ocr.recognize_book_spine(book_image)

            if ocr_results:
                # 使用最高置信度的结果
                best_result = max(ocr_results, key=lambda r: r.confidence)

                results.append({
                    "detected_id": i + 1,
                    "text": best_result.text,
                    "confidence": round(best_result.confidence, 3),
                    "bbox": {
                        "x": round(detection.bbox.x, 4),
                        "y": round(detection.bbox.y, 4),
                        "width": round(detection.bbox.width, 4),
                        "height": round(detection.bbox.height, 4),
                    },
                    "source": "mock_ocr",
                })
            else:
                # 没有识别到文字，但检测到书籍
                results.append({
                    "detected_id": i + 1,
                    "text": f"[未识别]",
                    "confidence": 0.0,
                    "bbox": {
                        "x": round(detection.bbox.x, 4),
                        "y": round(detection.bbox.y, 4),
                        "width": round(detection.bbox.width, 4),
                        "height": round(detection.bbox.height, 4),
                    },
                    "source": "mock_vision",
                })

        return results

    def _preprocess(self, image: Image.Image) -> Image.Image:
        """
        图像预处理

        - 调整大小（保持比例，最大宽度 1920）
        - 增强对比度
        - 轻微锐化
        """
        # 调整大小
        max_width = 1920
        if image.width > max_width:
            ratio = max_width / image.width
            new_size = (max_width, int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # 增强对比度
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)

        # 锐化
        image = image.filter(ImageFilter.SHARPEN)

        return image

    def _crop_book(
        self,
        image: Image.Image,
        bbox,
    ) -> Image.Image:
        """
        根据归一化 bbox 裁剪出书籍区域

        Args:
            image: 原图
            bbox: BoundingBox (x, y, width, height in 0~1)

        Returns:
            裁剪后的图片
        """
        width, height = image.size

        x1 = int(bbox.x * width)
        y1 = int(bbox.y * height)
        x2 = int((bbox.x + bbox.width) * width)
        y2 = int((bbox.y + bbox.height) * height)

        # 确保坐标在有效范围内
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)

        return image.crop((x1, y1, x2, y2))

    async def quick_scan(
        self,
        image: Image.Image,
    ) -> Dict[str, Any]:
        """
        快速扫描 - 返回概览信息

        Returns:
            {
                "total_detected": int,
                "high_confidence": int,
                "low_confidence": int,
                "results": List[Dict],
            }
        """
        results = await self.recognize_shelf(image, preprocess=True)

        high = sum(1 for r in results if r["confidence"] >= 0.8)
        medium = sum(1 for r in results if 0.5 <= r["confidence"] < 0.8)
        low = sum(1 for r in results if r["confidence"] < 0.5)

        return {
            "total_detected": len(results),
            "high_confidence": high,
            "medium_confidence": medium,
            "low_confidence": low,
            "results": results,
        }
