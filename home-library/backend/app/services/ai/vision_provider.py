"""
Vision Provider 抽象基类

视觉模型 Provider，用于分析书柜图片、检测书籍位置
"""
from abc import ABC, abstractmethod
from typing import List, Optional, BinaryIO
from PIL import Image

from .dto import ImageAnalysisResult, BookDetectionResult, BoundingBox


class VisionProvider(ABC):
    """
    视觉模型 Provider 抽象基类

    负责：
    1. 分析书柜图片
    2. 检测书籍位置和边界框
    3. 提取书籍视觉特征

    所有具体实现（OpenAI GPT-4V, Claude, 本地模型等）必须继承此类
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        初始化 Vision Provider

        Args:
            api_key: API 密钥（从环境变量读取）
            api_base_url: API 基础 URL
            model_name: 模型名称
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.timeout = timeout
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        """Provider 名称"""
        return self._name

    @abstractmethod
    async def analyze_image(
        self,
        image: Image.Image,
        detect_books: bool = True,
        extract_features: bool = False,
    ) -> ImageAnalysisResult:
        """
        分析图片

        Args:
            image: PIL Image 对象
            detect_books: 是否检测书籍位置
            extract_features: 是否提取视觉特征

        Returns:
            ImageAnalysisResult: 分析结果
        """
        pass

    @abstractmethod
    async def detect_books(
        self,
        image: Image.Image,
        confidence_threshold: float = 0.5,
    ) -> List[BookDetectionResult]:
        """
        检测图片中的书籍

        Args:
            image: PIL Image 对象
            confidence_threshold: 置信度阈值，低于此值的结果会被过滤

        Returns:
            BookDetectionResult 列表
        """
        pass

    async def detect_book_spines(
        self,
        image: Image.Image,
    ) -> List[BookDetectionResult]:
        """
        专门检测书脊（横向排列的书籍）

        Args:
            image: PIL Image 对象

        Returns:
            BookDetectionResult 列表
        """
        # 默认实现调用 detect_books
        # 子类可以覆盖以提供专门的实现
        return await self.detect_books(image)

    async def detect_book_covers(
        self,
        image: Image.Image,
    ) -> List[BookDetectionResult]:
        """
        专门检测封面（平铺或散落的书籍）

        Args:
            image: PIL Image 对象

        Returns:
            BookDetectionResult 列表
        """
        # 默认实现调用 detect_books
        return await self.detect_books(image)

    @abstractmethod
    async def health_check(self) -> bool:
        """
        检查 Provider 健康状态

        Returns:
            True if 可用，False otherwise
        """
        pass

    def _load_image(self, image_data: BinaryIO) -> Image.Image:
        """
        加载图片数据为 PIL Image

        Args:
            image_data: 图片二进制数据

        Returns:
            PIL Image 对象
        """
        return Image.open(image_data)

    def _normalize_bbox(
        self,
        bbox: dict,
        image_width: int,
        image_height: int,
    ) -> BoundingBox:
        """
        将原始边界框转换为归一化 BoundingBox

        Args:
            bbox: 原始边界框数据
            image_width: 图片宽度
            image_height: 图片高度

        Returns:
            归一化的 BoundingBox
        """
        x = bbox.get("x", 0) / image_width
        y = bbox.get("y", 0) / image_height
        width = bbox.get("width", 0) / image_width
        height = bbox.get("height", 0) / image_height

        return BoundingBox(
            x=max(0.0, min(1.0, x)),
            y=max(0.0, min(1.0, y)),
            width=max(0.0, min(1.0, width)),
            height=max(0.0, min(1.0, height)),
            pixel_x=bbox.get("x"),
            pixel_y=bbox.get("y"),
            pixel_width=bbox.get("width"),
            pixel_height=bbox.get("height"),
        )

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        return False
