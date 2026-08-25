"""
AI Services Module

统一的 AI/ML 服务抽象层，支持多 Provider 切换
"""
from .dto import (
    BoundingBox,
    RecognitionResult,
    BookDetectionResult,
    EditionMatchResult,
    ClassificationResult,
    SemanticSearchResult,
    ImageAnalysisResult,
    ProviderHealth,
    ProviderConfig,
)
from .vision_provider import VisionProvider
from .ocr_provider import OCRProvider
from .llm_provider import LLMProvider
from .mock_providers import MockVisionProvider, MockOCRProvider, MockLLMProvider
from .recognition_service import RecognitionService
from .pipeline import RecognitionPipeline

__all__ = [
    # DTOs
    "BoundingBox",
    "RecognitionResult",
    "BookDetectionResult",
    "EditionMatchResult",
    "ClassificationResult",
    "SemanticSearchResult",
    "ImageAnalysisResult",
    "ProviderHealth",
    "ProviderConfig",
    # Providers
    "VisionProvider",
    "OCRProvider",
    "LLMProvider",
    "MockVisionProvider",
    "MockOCRProvider",
    "MockLLMProvider",
    # Services
    "RecognitionService",
    "RecognitionPipeline",
]
