"""
Pydantic Schemas
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# ========== Work Schemas ==========

class WorkBase(BaseModel):
    title: str
    subtitle: Optional[str] = None
    original_title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None


class WorkCreate(WorkBase):
    pass


class WorkResponse(WorkBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


# ========== Edition Schemas ==========

class EditionBase(BaseModel):
    title: str
    isbn10: Optional[str] = None
    isbn13: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[str] = None
    page_count: Optional[int] = None
    cover_url: Optional[str] = None


class EditionCreate(EditionBase):
    work_id: int


class EditionResponse(EditionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    work_id: int
    created_at: datetime
    updated_at: datetime


# ========== Book Schemas ==========

class BookBase(BaseModel):
    status: str = "available"
    owner: Optional[str] = None
    notes: Optional[str] = None


class BookCreate(BaseModel):
    # 创建时需要的信息
    title: str
    subtitle: Optional[str] = None
    isbn13: Optional[str] = None
    publisher: Optional[str] = None
    status: str = "available"
    owner: Optional[str] = None
    notes: Optional[str] = None


class BookUpdate(BaseModel):
    status: Optional[str] = None
    owner: Optional[str] = None
    notes: Optional[str] = None


class BookResponse(BookBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    edition_id: Optional[int]
    confidence: Optional[float]
    created_at: datetime
    updated_at: datetime


class TagResponse(BaseModel):
    """标签响应"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    created_at: datetime

class BookDetailResponse(BookResponse):
    """图书详情（包含位置和分类）"""
    work: Optional[WorkResponse] = None
    edition: Optional[EditionResponse] = None
    category: Optional[CategoryResponse] = None
    tags: List["TagResponse"] = Field(default_factory=list)
    shelf_positions: List[ShelfPositionResponse] = Field(default_factory=list)


class BookWithLocationResponse(BaseModel):
    """带位置信息的图书响应"""
    model_config = ConfigDict(from_attributes=True)
    book: BookDetailResponse
    current_location: Optional[dict] = Field(None, description="当前位置")
    location_history: List[dict] = Field(default_factory=list, description="位置历史")


class BookListResponse(BaseModel):
    total: int
    items: List[BookDetailResponse]


# ========== Bookshelf Schemas ==========

class BookshelfBase(BaseModel):
    name: str
    location: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    description: Optional[str] = None


class BookshelfCreate(BookshelfBase):
    pass


class BookshelfUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    description: Optional[str] = None


class BookshelfResponse(BookshelfBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class BookshelfDetailResponse(BookshelfResponse):
    shelf_count: int = 0


# ========== Shelf Schemas ==========

class ShelfBase(BaseModel):
    level: int
    height: Optional[float] = None


class ShelfCreate(ShelfBase):
    bookshelf_id: int


class ShelfUpdate(BaseModel):
    level: Optional[int] = None
    height: Optional[float] = None


class ShelfResponse(ShelfBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    bookshelf_id: int
    created_at: datetime
    updated_at: datetime


class ShelfDetailResponse(ShelfResponse):
    book_count: int = 0


# ========== ShelfPosition Schemas ==========

class BoundingBox(BaseModel):
    """边界框 - 归一化坐标 0~1"""
    x: float = Field(..., ge=0.0, le=1.0, description="左上角 x 坐标")
    y: float = Field(..., ge=0.0, le=1.0, description="左上角 y 坐标")
    width: float = Field(..., ge=0.0, le=1.0, description="宽度")
    height: float = Field(..., ge=0.0, le=1.0, description="高度")


class ShelfPositionBase(BaseModel):
    position_x: float = Field(0.0, ge=0.0, le=1.0, description="归一化位置 (0~1)")
    position_order: Optional[int] = Field(None, description="从左到右的顺序")


class ShelfPositionCreate(ShelfPositionBase):
    book_id: int
    shelf_id: int
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    source: str = Field("manual", description="位置来源: scan, manual, adjusted")
    scan_id: Optional[int] = None
    scan_item_id: Optional[int] = None
    bbox: Optional[BoundingBox] = None


class ShelfPositionResponse(ShelfPositionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    book_id: int
    shelf_id: int
    confidence: float
    source: str
    scan_id: Optional[int] = None
    scan_item_id: Optional[int] = None
    is_current: bool = True
    bbox: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class ShelfPositionUpdate(BaseModel):
    """更新位置请求"""
    position_x: Optional[float] = Field(None, ge=0.0, le=1.0)
    position_order: Optional[int] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    bbox: Optional[BoundingBox] = None


class ShelfPositionBookInfo(BaseModel):
    """书架上的图书位置信息"""
    book_id: int
    position_id: int
    position_x: float
    position_order: Optional[int]
    confidence: float
    bbox: Optional[dict] = None


class ShelfVisualizationResponse(BaseModel):
    """书架可视化响应"""
    shelf_id: int
    bookshelf_name: str
    level: int
    latest_scan_id: Optional[int] = None
    scan_image_path: Optional[str] = None
    books: List[ShelfPositionBookInfo]


# ========== Category Schemas ==========

class CategoryBase(BaseModel):
    code: str = Field(..., description="中图法分类号")
    name: str = Field(..., description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, description="父分类 ID")
    level: int = Field(1, description="层级 (1-3)")


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class CategoryTreeResponse(CategoryResponse):
    """分类树响应"""
    children: List["CategoryTreeResponse"] = Field(default_factory=list)
    book_count: int = Field(0, description="该分类下的图书数量")


class CategoryPathResponse(BaseModel):
    """分类路径响应"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    level: int


# ========== AI Classification Schemas ==========

class ClassificationSuggestion(BaseModel):
    """AI 分类建议"""
    category_code: str = Field(..., description="中图法分类号")
    category_name: str = Field(..., description="分类名称")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    reason: str = Field(..., description="推荐理由")


class ClassificationRequest(BaseModel):
    """分类请求"""
    title: str = Field(..., description="书名")
    subtitle: Optional[str] = Field(None, description="副标题")
    authors: List[str] = Field(default_factory=list, description="作者")
    publisher: Optional[str] = Field(None, description="出版社")
    description: Optional[str] = Field(None, description="简介")
    existing_category_id: Optional[int] = Field(None, description="当前分类 ID（可选）")


class ClassificationResult(BaseModel):
    """分类结果"""
    success: bool
    suggestions: List[ClassificationSuggestion] = Field(default_factory=list)
    selected_code: Optional[str] = Field(None, description="选中的分类号")
    selected_name: Optional[str] = Field(None, description="选中的分类名")
    requires_confirmation: bool = Field(True, description="是否需要人工确认")
    message: Optional[str] = None


class BookClassificationUpdate(BaseModel):
    """更新图书分类请求"""
    category_id: Optional[int] = Field(None, description="分类 ID")
    category_code: Optional[str] = Field(None, description="分类号（优先使用）")
    confirmed: bool = Field(False, description="是否已人工确认")


# ========== Tag Schemas ==========

class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)





class BookTagsUpdate(BaseModel):
    """更新图书标签请求"""
    add_tags: List[str] = Field(default_factory=list, description="要添加的标签名称列表")
    remove_tag_ids: List[int] = Field(default_factory=list, description="要移除的标签 ID 列表")

class BookMetadataImport(BaseModel):
    """图书元数据导入请求"""
    source: str = Field(..., description="数据来源，如 'google_books', 'open_library'")
    source_id: str = Field(..., description="Provider 内部的唯一标识")
    title: str = Field(..., description="书名")
    subtitle: Optional[str] = Field(None, description="副标题")
    authors: List[str] = Field(default_factory=list, description="作者列表")
    publisher: Optional[str] = Field(None, description="出版社")
    publish_date: Optional[str] = Field(None, description="出版日期")
    publish_year: Optional[int] = Field(None, description="出版年份")
    isbn10: Optional[str] = Field(None, description="ISBN-10")
    isbn13: Optional[str] = Field(None, description="ISBN-13")
    language: Optional[str] = Field(None, description="语言代码")
    page_count: Optional[int] = Field(None, description="页数")
    cover_url: Optional[str] = Field(None, description="封面图片 URL")
    description: Optional[str] = Field(None, description="简介/描述")


class BookImportRequest(BaseModel):
    """导入图书请求"""
    candidate: BookMetadataImport
    bookshelf_id: Optional[int] = Field(None, description="书柜 ID")
    shelf_id: Optional[int] = Field(None, description="书架层 ID")
    category_id: Optional[int] = Field(None, description="分类 ID")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    owner: Optional[str] = Field(None, description="所有者")
    notes: Optional[str] = Field(None, description="备注")


class BookImportResponse(BaseModel):
    """导入图书响应"""
    success: bool
    book_id: int
    work_id: int
    edition_id: int
    is_new_work: bool = Field(..., description="是否新创建 Work")
    is_new_edition: bool = Field(..., description="是否新创建 Edition")
    is_new_book: bool = Field(..., description="是否新创建 Book")
    message: Optional[str] = None


# ========== Scan Schemas ==========


class ScanItemResponse(BaseModel):
    """扫描识别项响应 - Phase 8: 支持 AI Import"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    detected_text: str
    confidence: float
    bbox: Optional[BoundingBox] = None

    # Phase 8: 状态
    status: str = Field(..., description="状态: detected, searching, matched, needs_review, confirmed, imported, failed, skipped")

    # Phase 8: 搜索相关
    search_query: Optional[str] = None
    search_attempted_at: Optional[datetime] = None
    search_error: Optional[str] = None

    # Phase 8: 候选和匹配
    candidates: Optional[List[Dict[str, Any]]] = None
    candidates_count: int = 0
    matched_candidate_index: Optional[int] = None
    match_confidence: Optional[float] = None
    matched_at: Optional[datetime] = None
    match_error: Optional[str] = None

    # Phase 8: 导入
    imported_book_id: Optional[int] = None
    imported_at: Optional[datetime] = None
    import_error: Optional[str] = None

    # Phase 8: 审核
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_note: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None


class ScanItemUpdate(BaseModel):
    """更新识别项请求 - Phase 8"""
    detected_text: Optional[str] = None
    status: Optional[str] = Field(
        None,
        pattern="^(detected|searching|matched|needs_review|confirmed|imported|failed|skipped)$"
    )
    matched_candidate_index: Optional[int] = None
    bbox: Optional[BoundingBox] = None
    review_note: Optional[str] = None


class ScanResponse(BaseModel):
    """扫描记录响应"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    bookshelf_id: Optional[int] = None
    shelf_id: Optional[int] = None
    image_path: str
    scanned_at: datetime
    item_count: int = Field(0, description="识别项数量")


class ScanDetailResponse(ScanResponse):
    """扫描记录详情（含识别项）"""
    items: List[ScanItemResponse] = Field(default_factory=list)


class ScanCreateResponse(BaseModel):
    """创建扫描响应"""
    scan_id: int
    detected_count: int
    items: List[ScanItemResponse]
    message: str


class ScanStats(BaseModel):
    """扫描统计"""
    total_items: int
    high_confidence: int  # >= 0.8
    medium_confidence: int  # 0.5 ~ 0.8
    low_confidence: int  # < 0.5
    pending_count: int
    confirmed_count: int
    rejected_count: int


class RecognitionResultItem(BaseModel):
    """识别结果单项 - 用于前端展示"""
    detected_id: int = Field(..., description="检测 ID")
    text: str = Field(..., description="识别的文本")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    bbox: BoundingBox = Field(..., description="边界框")
    source: str = Field(..., description="识别来源: mock_ocr, mock_vision, etc.")
    status: str = Field(default="pending", description="状态")


class ShelfScanRequest(BaseModel):
    """书架扫描请求"""
    bookshelf_id: Optional[int] = Field(None, description="书柜 ID")
    shelf_id: Optional[int] = Field(None, description="书架层 ID")
    preprocess: bool = Field(True, description="是否预处理图片")
