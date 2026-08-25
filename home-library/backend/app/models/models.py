"""
数据库模型定义
Phase 2: 核心数据模型
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Text, Integer, Float, ForeignKey, DateTime,
    Boolean, Table, Column, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import JSON

from app.db.database import Base


# ========== 关联表 ==========

book_tag_association = Table(
    "book_tag",
    Base.metadata,
    Column("book_id", ForeignKey("books.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


# ========== Work: 作品 ==========

class Work(Base):
    """作品 - 抽象的著作概念"""
    __tablename__ = "works"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    subtitle: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    original_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    editions: Mapped[List["Edition"]] = relationship(
        back_populates="work", cascade="all, delete-orphan"
    )


# ========== Edition: 版本 ==========

class Edition(Base):
    """版本 - 具体出版版本"""
    __tablename__ = "editions"
    __table_args__ = (
        UniqueConstraint("isbn13", name="uix_edition_isbn13"),
        UniqueConstraint("isbn10", name="uix_edition_isbn10"),
        Index("ix_edition_title", "title"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id"), nullable=False)

    # ISBN
    isbn10: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, unique=True)
    isbn13: Mapped[Optional[str]] = mapped_column(String(13), nullable=True, unique=True)

    # 出版信息
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publish_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cover_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # 数据来源
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    work: Mapped["Work"] = relationship(back_populates="editions")
    books: Mapped[List["Book"]] = relationship(back_populates="edition")


# ========== Book: 藏书 ==========

class Book(Base):
    """藏书 - 用户实际拥有的一册书"""
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    edition_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("editions.id"), nullable=True
    )

    # Phase 9: 中图法分类
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )

    # 状态
    status: Mapped[str] = mapped_column(
        String(20), default="available"  # available, borrowed, lost
    )
    owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI 识别置信度
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    edition: Mapped[Optional["Edition"]] = relationship(back_populates="books")
    category: Mapped[Optional["Category"]] = relationship(back_populates="books")
    shelf_positions: Mapped[List["ShelfPosition"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    tags: Mapped[List["Tag"]] = relationship(
        secondary=book_tag_association, back_populates="books"
    )
    scan_items: Mapped[List["ScanItem"]] = relationship(back_populates="imported_book")


# ========== Bookshelf: 书柜 ==========

class Bookshelf(Base):
    """书柜"""
    __tablename__ = "bookshelves"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    width: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    shelves: Mapped[List["Shelf"]] = relationship(
        back_populates="bookshelf", cascade="all, delete-orphan", order_by="Shelf.level"
    )
    scans: Mapped[List["Scan"]] = relationship(back_populates="bookshelf")


# ========== Shelf: 书架层 ==========

class Shelf(Base):
    """书架层"""
    __tablename__ = "shelves"
    __table_args__ = (
        UniqueConstraint("bookshelf_id", "level", name="uix_shelf_bookshelf_level"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    bookshelf_id: Mapped[int] = mapped_column(
        ForeignKey("bookshelves.id"), nullable=False
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)  # 从上到下 1, 2, 3...
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    bookshelf: Mapped["Bookshelf"] = relationship(back_populates="shelves")
    positions: Mapped[List["ShelfPosition"]] = relationship(
        back_populates="shelf", cascade="all, delete-orphan"
    )
    scans: Mapped[List["Scan"]] = relationship(back_populates="shelf")


# ========== ShelfPosition: 书架位置 ==========

class ShelfPosition(Base):
    """书籍在书架上的位置 - Phase 10: 支持重新扫描和位置追踪"""
    __tablename__ = "shelf_positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    shelf_id: Mapped[int] = mapped_column(ForeignKey("shelves.id"), nullable=False)

    # 核心位置信息
    position_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    position_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Phase 10: 位置元数据
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source: Mapped[str] = mapped_column(String(20), default="manual")  # scan, manual, adjusted

    # Phase 10: 与扫描关联（追踪位置来源）
    scan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scans.id"), nullable=True)
    scan_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scan_items.id"), nullable=True)

    # Phase 10: 位置历史（用于变化检测）
    previous_position_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("shelf_positions.id"), nullable=True
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    # 边界框（用于可视化）
    bbox: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    book: Mapped["Book"] = relationship(back_populates="shelf_positions")
    shelf: Mapped["Shelf"] = relationship(back_populates="positions")
    scan: Mapped[Optional["Scan"]] = relationship(back_populates="shelf_positions")
    scan_item: Mapped[Optional["ScanItem"]] = relationship(back_populates="shelf_position")
    previous_position: Mapped[Optional["ShelfPosition"]] = relationship(
        remote_side=[id], back_populates="next_positions"
    )
    next_positions: Mapped[List["ShelfPosition"]] = relationship(
        back_populates="previous_position"
    )


# ========== Category: 中图法分类 ==========

class Category(Base):
    """中图法分类 - 支持树形结构"""
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("code", name="uix_category_code"),
        Index("ix_category_parent", "parent_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )
    level: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    books: Mapped[List["Book"]] = relationship(back_populates="category")


# ========== Book-Category Association ==========
# 在 Book 模型中添加 category 关系


# ========== Tag: 标签 ==========

class Tag(Base):
    """标签"""
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    books: Mapped[List["Book"]] = relationship(
        secondary=book_tag_association, back_populates="tags"
    )


# ========== Scan: 扫描记录 ==========

class Scan(Base):
    """书柜扫描记录"""
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    bookshelf_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bookshelves.id"), nullable=True
    )
    shelf_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("shelves.id"), nullable=True
    )
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    bookshelf: Mapped[Optional["Bookshelf"]] = relationship(back_populates="scans")
    shelf: Mapped[Optional["Shelf"]] = relationship(back_populates="scans")
    items: Mapped[List["ScanItem"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )
    shelf_positions: Mapped[List["ShelfPosition"]] = relationship(back_populates="scan")


# ========== ScanItem: 扫描识别项 ==========

class ScanItem(Base):
    """扫描识别的单本书 - Phase 8: 支持 AI Import Pipeline"""
    __tablename__ = "scan_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"), nullable=False)

    # 识别结果
    detected_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # 边界框 JSON: {"x": float, "y": float, "width": float, "height": float}
    bbox: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ===== Phase 8: AI Import Pipeline 状态 =====

    # 状态: detected, searching, matched, needs_review, confirmed, imported, failed, skipped
    status: Mapped[str] = mapped_column(String(20), default="detected")

    # 元数据搜索相关
    search_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    search_attempted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    search_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 候选结果 JSON: [{"source": "google_books", "candidate": {...}, "score": 0.95}]
    candidates: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    candidates_count: Mapped[int] = mapped_column(Integer, default=0)

    # AI 匹配结果
    matched_candidate_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    match_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    match_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 最终导入的书籍
    imported_book_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("books.id"), nullable=True
    )
    imported_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    import_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 用户操作记录
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    scan: Mapped["Scan"] = relationship(back_populates="items")
    imported_book: Mapped[Optional["Book"]] = relationship(back_populates="scan_items")
    shelf_position: Mapped[Optional["ShelfPosition"]] = relationship(back_populates="scan_item")


# ========== MetadataSource: 元数据源 ==========

class MetadataSource(Base):
    """图书元数据源配置"""
    __tablename__ = "metadata_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    base_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
