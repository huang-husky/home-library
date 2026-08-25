"""
LLM Provider 抽象基类

大语言模型 Provider，用于分类、匹配版本、语义搜索
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from .dto import (
    ClassificationResult,
    EditionMatchResult,
    SemanticSearchResult,
    RecognitionResult,
)


class LLMProvider(ABC):
    """
    LLM Provider 抽象基类

    负责：
    1. 图书分类（中图法等）
    2. 版本匹配（将 OCR 结果与元数据库匹配）
    3. 语义搜索
    4. 文本纠错和补全

    所有具体实现（OpenAI GPT, Claude, 本地 LLM 等）必须继承此类
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 30.0,
        max_tokens: int = 2000,
        temperature: float = 0.3,  # 较低温度以获得更确定的结果
    ):
        """
        初始化 LLM Provider

        Args:
            api_key: API 密钥
            api_base_url: API 基础 URL
            model_name: 模型名称
            timeout: 请求超时时间（秒）
            max_tokens: 最大生成 token 数
            temperature: 采样温度
        """
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        """Provider 名称"""
        return self._name

    @abstractmethod
    async def classify_book(
        self,
        title: str,
        description: Optional[str] = None,
        author: Optional[str] = None,
        categories: Optional[List[Dict[str, str]]] = None,
    ) -> ClassificationResult:
        """
        对图书进行分类

        Args:
            title: 书名
            description: 简介
            author: 作者
            categories: 可选的分类候选项

        Returns:
            ClassificationResult
        """
        pass

    @abstractmethod
    async def match_edition(
        self,
        ocr_results: List[RecognitionResult],
        candidates: List[Dict[str, Any]],
    ) -> List[EditionMatchResult]:
        """
        将 OCR 结果与候选版本匹配

        Args:
            ocr_results: OCR 识别结果列表
            candidates: 候选版本列表（从元数据服务获取）

        Returns:
            EditionMatchResult 列表，按置信度排序
        """
        pass

    @abstractmethod
    async def semantic_search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> SemanticSearchResult:
        """
        语义搜索

        Args:
            query: 搜索查询
            documents: 文档列表
            top_k: 返回结果数

        Returns:
            SemanticSearchResult
        """
        pass

    async def correct_text(
        self,
        text: str,
        context: Optional[str] = None,
    ) -> str:
        """
        纠正 OCR 识别错误的文字

        Args:
            text: 原始 OCR 文本
            context: 上下文信息（可选）

        Returns:
            纠正后的文本
        """
        # 默认实现：子类可覆盖以提供更智能的纠错
        return text.strip()

    async def extract_metadata(
        self,
        raw_text: str,
    ) -> Dict[str, Any]:
        """
        从原始文本中提取结构化元数据

        Args:
            raw_text: 原始文本

        Returns:
            提取的元数据字典
        """
        # 默认实现：提取标题、作者、ISBN 等
        import re

        metadata = {
            "title": None,
            "author": None,
            "isbn": None,
            "publisher": None,
        }

        # 提取 ISBN
        isbn_pattern = r'(?:ISBN[- ]?)?(978\d{10}|\d{9}[\dX])'
        isbn_match = re.search(isbn_pattern, raw_text.replace("-", "").replace(" ", ""))
        if isbn_match:
            metadata["isbn"] = isbn_match.group(1)

        return metadata

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
