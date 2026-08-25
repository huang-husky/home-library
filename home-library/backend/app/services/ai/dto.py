"""
AI Provider DTOs

统一 AI/ML 服务的结果结构，与具体模型厂商解耦
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class BoundingBox(BaseModel):
    """
    边界框坐标

    归一化坐标 (0.0 ~ 1.0) 或像素坐标
    """
    x: float = Field(..., description="左上角 x 坐标")
    y: float = Field(..., description="左上角 y 坐标")
    width: float = Field(..., description="宽度")
    height: float = Field(..., description="高度")

    # 可选：原始像素坐标
    pixel_x: Optional[int] = None
    pixel_y: Optional[int] = None
    pixel_width: Optional[int] = None
    pixel_height: Optional[int] = None


class RecognitionResult(BaseModel):
    """
    OCR 文本识别结果

    统一的文本识别输出格式
    """
    text: str = Field(..., description="识别的文本内容")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度 0-1")
    bbox: Optional[BoundingBox] = Field(None, description="文本位置边界框")
    source: str = Field(..., description="识别来源 Provider")

    # 元数据
    language: Optional[str] = Field(None, description="检测到的语言")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    # 原始数据（调试用，不序列化）
    raw_data: Optional[Any] = Field(None, exclude=True)


class BookDetectionResult(BaseModel):
    """
    书籍检测结果

    从图片中检测到的单本书籍
    """
    detected_id: str = Field(..., description="检测实例唯一 ID")
    bbox: BoundingBox = Field(..., description="书籍边界框")
    confidence: float = Field(..., ge=0.0, le=1.0, description="检测置信度")

    # OCR 结果
    text: Optional[str] = Field(None, description="书籍上的文本（书名等）")
    text_confidence: Optional[float] = Field(None, description="文本识别置信度")

    # 来源
    source: str = Field(..., description="检测来源 Provider")

    # 额外特征
    features: Dict[str, Any] = Field(default_factory=dict, description="视觉特征")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class EditionMatchResult(BaseModel):
    """
    版本匹配结果

    将检测到的书籍与元数据库匹配
    """
    candidate_id: int = Field(..., description="匹配的 Edition ID")
    confidence: float = Field(..., ge=0.0, le=1.0, description="匹配置信度")
    reason: str = Field(..., description="匹配理由")

    # 匹配详情
    matched_fields: List[str] = Field(default_factory=list, description="匹配的字段")
    similarity_scores: Dict[str, float] = Field(default_factory=dict, description="各字段相似度")


class ClassificationResult(BaseModel):
    """
    图书分类结果

    中图法分类或其他分类体系
    """
    category_code: str = Field(..., description="分类代码")
    category_name: str = Field(..., description="分类名称")
    confidence: float = Field(..., ge=0.0, le=1.0, description="分类置信度")
    reason: str = Field(..., description="分类理由")

    # 备选分类
    alternatives: List[Dict[str, Any]] = Field(default_factory=list, description="备选分类")


class SemanticSearchResult(BaseModel):
    """
    语义搜索结果

    基于语义相似度的搜索结果
    """
    query: str = Field(..., description="原始查询")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="搜索结果")
    total_found: int = Field(0, description="找到的数量")

    # 搜索元数据
    search_time_ms: Optional[float] = None
    embedding_model: Optional[str] = None


class ImageAnalysisResult(BaseModel):
    """
    图像分析结果

    Vision Provider 的完整分析输出
    """
    # 检测到的书籍列表
    detected_books: List[BookDetectionResult] = Field(default_factory=list)

    # 整体分析
    total_books: int = Field(0, description="检测到的书籍总数")
    image_quality: Optional[float] = Field(None, description="图像质量评分")

    # 处理信息
    processing_time_ms: Optional[float] = None
    source: str = Field(..., description="分析来源")
    model_version: Optional[str] = None

    # 原始数据
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderHealth(BaseModel):
    """
    Provider 健康状态
    """
    name: str = Field(..., description="Provider 名称")
    provider_type: str = Field(..., description="Provider 类型")
    available: bool = Field(True, description="是否可用")
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_checked: datetime = Field(default_factory=datetime.utcnow)

    # 配额信息（可选）
    quota_remaining: Optional[int] = None
    quota_total: Optional[int] = None


class ProviderConfig(BaseModel):
    """
    Provider 配置
    """
    name: str
    provider_type: str  # "vision", "ocr", "llm"
    enabled: bool = True
    priority: int = 0  # 优先级，数字越小优先级越高
    timeout: float = 30.0
    max_retries: int = 3

    # API 配置（从环境变量读取，不存储实际 key）
    api_key_env_var: Optional[str] = None  # 如 "OPENAI_API_KEY"
    api_base_url: Optional[str] = None
    model_name: Optional[str] = None

    # 额外配置
    extra_config: Dict[str, Any] = Field(default_factory=dict)
