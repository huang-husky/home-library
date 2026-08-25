"""
LLM Provider 接口
阶段零：仅定义接口，不实现具体 Provider
"""
from typing import Optional, Protocol
from pydantic import BaseModel

class ClassificationResult(BaseModel):
    """分类结果"""
    category_code: str
    category_name: str
    confidence: float
    reason: str


class LLMProvider(Protocol):
    """大语言模型提供者接口"""

    async def classify_book(self, title: str, description: Optional[str]) -> ClassificationResult:
        """对图书进行中图法分类"""
        ...


# 阶段零：暂不实现具体 Provider
