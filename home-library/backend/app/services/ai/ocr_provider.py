"""
OCR Provider 抽象基类

文本识别 Provider，用于从书籍图片中提取文字
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from PIL import Image

from .dto import RecognitionResult


class OCRProvider(ABC):
    """
    OCR Provider 抽象基类

    负责：
    1. 从书籍图片中提取文字
    2. 识别书名、作者、ISBN 等
    3. 支持多语言识别

    所有具体实现（PaddleOCR, Tesseract, AWS Textract, Azure Read 等）必须继承此类
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 30.0,
        language: str = "zh+en",  # 默认中英文混合
    ):
        """
        初始化 OCR Provider

        Args:
            api_key: API 密钥
            api_base_url: API 基础 URL
            model_name: 模型名称
            timeout: 请求超时时间（秒）
            language: 识别语言，如 "zh", "en", "zh+en", "jpn"
        """
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.timeout = timeout
        self.language = language
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        """Provider 名称"""
        return self._name

    @abstractmethod
    async def recognize_text(
        self,
        image: Image.Image,
        return_bbox: bool = True,
    ) -> List[RecognitionResult]:
        """
        识别图片中的文字

        Args:
            image: PIL Image 对象
            return_bbox: 是否返回文字位置

        Returns:
            RecognitionResult 列表
        """
        pass

    @abstractmethod
    async def recognize_book_spine(
        self,
        image: Image.Image,
    ) -> Optional[RecognitionResult]:
        """
        专门识别书脊文字（竖排文字处理）

        Args:
            image: PIL Image 对象

        Returns:
            最可能的书名 RecognitionResult，或 None
        """
        pass

    async def recognize_isbn(
        self,
        image: Image.Image,
    ) -> Optional[RecognitionResult]:
        """
        专门识别 ISBN 号码

        Args:
            image: PIL Image 对象

        Returns:
            包含 ISBN 的 RecognitionResult，或 None
        """
        # 默认实现：识别所有文字并筛选 ISBN 格式
        results = await self.recognize_text(image, return_bbox=False)

        import re
        isbn_pattern = r'(?:ISBN[- ]?)?(978\d{10}|\d{9}[\dX])'

        for result in results:
            match = re.search(isbn_pattern, result.text.replace("-", "").replace(" ", ""))
            if match:
                return RecognitionResult(
                    text=match.group(1),
                    confidence=result.confidence,
                    source=self._name,
                    metadata={"type": "ISBN", "original_text": result.text},
                )

        return None

    async def batch_recognize(
        self,
        images: List[Image.Image],
    ) -> List[List[RecognitionResult]]:
        """
        批量识别多张图片

        Args:
            images: PIL Image 列表

        Returns:
            每张图片的 RecognitionResult 列表的列表
        """
        results = []
        for image in images:
            result = await self.recognize_text(image)
            results.append(result)
        return results

    @abstractmethod
    async def health_check(self) -> bool:
        """
        检查 Provider 健康状态

        Returns:
            True if 可用，False otherwise
        """
        pass

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        return False
