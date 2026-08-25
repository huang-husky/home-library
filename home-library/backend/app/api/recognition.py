"""
Recognition API

图书识别相关 API，用于测试 AI Provider 链路
"""
import logging
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse
from PIL import Image

from app.services.ai.recognition_service import RecognitionService
from app.services.ai.dto import ProviderHealth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recognition", tags=["recognition"])

# 全局 RecognitionService 实例（单例）
_recognition_service: Optional[RecognitionService] = None


def get_recognition_service() -> RecognitionService:
    """获取或创建 RecognitionService 实例"""
    global _recognition_service
    if _recognition_service is None:
        _recognition_service = RecognitionService()
        logger.info("RecognitionService initialized")
    return _recognition_service


@router.post("/test")
async def test_recognition(
    image: UploadFile = File(..., description="要识别的图片文件"),
    analyze_type: str = Form("bookshelf", description="分析类型: bookshelf, book, full"),
):
    """
    测试图书识别流程

    使用 Mock Provider 返回固定的测试结果，用于验证业务链路。

    Args:
        image: 图片文件（JPG, PNG 等）
        analyze_type: 分析类型
            - bookshelf: 分析书柜（检测多本书）
            - book: 识别单本书
            - full: 完整测试流程

    Returns:
        结构化识别结果，包含：
        - vision: 视觉检测结果
        - ocr: OCR 识别结果
        - llm: LLM 处理结果
        - metadata: 元数据匹配结果

    Example:
        curl -X POST "http://localhost:8000/api/recognition/test" \\
             -F "image=@bookshelf.jpg" \\
             -F "analyze_type=bookshelf"
    """
    service = get_recognition_service()

    # 验证文件类型
    allowed_types = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type: {image.content_type}. Allowed: {allowed_types}"
        )

    try:
        # 读取图片
        contents = await image.read()
        pil_image = Image.open(BytesIO(contents))

        # 转换为 RGB（处理 RGBA 等模式）
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        logger.info(f"Processing image: {pil_image.size}, type={analyze_type}")

        # 根据分析类型调用不同方法
        if analyze_type == "bookshelf":
            result = await service.analyze_bookshelf(pil_image, match_metadata=True)
        elif analyze_type == "book":
            result = await service.recognize_book(pil_image)
        else:  # full
            result = await service.test_recognition(pil_image)

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recognition test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recognition failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    检查识别服务健康状态

    返回所有 AI Provider 的健康状态。
    """
    service = get_recognition_service()

    try:
        health = await service.health_check()

        providers = [
            ProviderHealth(
                name="vision",
                provider_type="vision",
                available=health.get("vision", False),
            ),
            ProviderHealth(
                name="ocr",
                provider_type="ocr",
                available=health.get("ocr", False),
            ),
            ProviderHealth(
                name="llm",
                provider_type="llm",
                available=health.get("llm", False),
            ),
        ]

        all_healthy = all(p.available for p in providers)

        return {
            "status": "healthy" if all_healthy else "degraded",
            "providers": [p.model_dump() for p in providers],
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "providers": [],
        }


@router.get("/providers")
async def list_providers():
    """
    列出可用的 AI Provider

    返回当前配置的 Provider 信息（不含 API key）。
    """
    service = get_recognition_service()

    return {
        "vision": {
            "name": service.vision.name,
            "type": "vision",
            "model": getattr(service.vision, "model_name", None),
        },
        "ocr": {
            "name": service.ocr.name,
            "type": "ocr",
            "model": getattr(service.ocr, "model_name", None),
            "language": getattr(service.ocr, "language", None),
        },
        "llm": {
            "name": service.llm.name,
            "type": "llm",
            "model": getattr(service.llm, "model_name", None),
        },
    }
