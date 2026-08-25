"""
OCR Provider 接口
阶段零：仅定义接口，不实现具体 Provider
"""
from typing import List, Optional, Protocol
from pydantic import BaseModel

class OCRResult(BaseModel):
    """OCR 识别结果"""
    text: str
    confidence: float
    bbox: Optional[dict] = None  # 文本位置


class OCRProvider(Protocol):
    """OCR 提供者接口"""

    async def recognize(self, image_path: str) -> List[OCRResult]:
        """识别图片中的文字"""
        ...


# 阶段零：暂不实现具体 Provider
# 后续将实现：
# - PaddleOCRProvider
# - VisionModelProvider
