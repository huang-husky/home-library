"""
图书分类和标签管理 API
Phase 9: Classification System
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Book, Category, Tag, book_tag_association
from app.schemas.schemas import (
    ClassificationRequest,
    ClassificationResult,
    BookClassificationUpdate,
    TagCreate,
    TagResponse,
    BookTagsUpdate,
)
from app.services.classification_service import ClassificationService

router = APIRouter(prefix="/books", tags=["book-classification"])


# ========== AI 分类建议 ==========

@router.post("/{book_id}/classify", response_model=ClassificationResult)
async def classify_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    为图书获取 AI 分类建议
    """
    # 获取图书信息
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )

    # 获取图书元数据
    title = ""
    subtitle = None
    authors = []
    publisher = None
    description = None

    if book.edition:
        title = book.edition.title
        subtitle = book.edition.subtitle
        publisher = book.edition.publisher

        if book.edition.work:
            description = book.edition.work.description

    # 调用分类服务
    classifier = ClassificationService(db)
    result = await classifier.classify_book(
        title=title,
        subtitle=subtitle,
        authors=authors,
        publisher=publisher,
        description=description,
    )

    return ClassificationResult(**result)


@router.post("/classify-suggest", response_model=ClassificationResult)
async def classify_suggest(
    request: ClassificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    根据提供的元数据获取分类建议（不保存）
    """
    classifier = ClassificationService(db)
    result = await classifier.classify_book(
        title=request.title,
        subtitle=request.subtitle,
        authors=request.authors,
        publisher=request.publisher,
        description=request.description,
    )

    return ClassificationResult(**result)


# ========== 图书分类管理 ==========

@router.get("/{book_id}/category", response_model=dict)
async def get_book_category(
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取图书的分类信息"""
    result = await db.execute(
        select(Book, Category)
        .outerjoin(Category, Book.category_id == Category.id)
        .where(Book.id == book_id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )

    book, category = row

    # 获取完整路径
    path = []
    if category:
        classifier = ClassificationService(db)
        path = await classifier.get_classification_path(category.code)

    return {
        "book_id": book.id,
        "category": {
            "id": category.id,
            "code": category.code,
            "name": category.name,
            "description": category.description,
        } if category else None,
        "path": path,
    }


@router.put("/{book_id}/category", response_model=dict)
async def update_book_category(
    book_id: int,
    update: BookClassificationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    更新图书分类

    - 可以通过 category_id 或 category_code 指定分类
    - 后端会验证分类是否存在
    """
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )

    category = None

    # 优先使用 category_code
    if update.category_code:
        classifier = ClassificationService(db)
        category = await classifier.validate_category_code(update.category_code)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category code: {update.category_code}"
            )
    elif update.category_id:
        result = await db.execute(
            select(Category).where(Category.id == update.category_id)
        )
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category id: {update.category_id}"
            )

    # 更新分类
    book.category_id = category.id if category else None

    await db.commit()
    await db.refresh(book)

    return {
        "book_id": book.id,
        "category_id": book.category_id,
        "category_code": category.code if category else None,
        "category_name": category.name if category else None,
        "confirmed": update.confirmed,
    }


@router.delete("/{book_id}/category", status_code=status.HTTP_204_NO_CONTENT)
async def remove_book_category(
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    """移除图书分类"""
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )

    book.category_id = None
    await db.commit()

    return None


# ========== 图书标签管理 ==========

@router.get("/{book_id}/tags", response_model=List[TagResponse])
async def get_book_tags(
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取图书的标签列表"""
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )

    # 获取标签
    result = await db.execute(
        select(Tag)
        .join(book_tag_association)
        .where(book_tag_association.c.book_id == book_id)
        .order_by(Tag.name)
    )
    tags = result.scalars().all()

    return tags


@router.put("/{book_id}/tags", response_model=dict)
async def update_book_tags(
    book_id: int,
    update: BookTagsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    更新图书标签

    - add_tags: 要添加的标签名称列表（不存在会自动创建）
    - remove_tag_ids: 要移除的标签 ID 列表
    """
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )

    # 移除标签
    if update.remove_tag_ids:
        for tag_id in update.remove_tag_ids:
            await db.execute(
                book_tag_association.delete()
                .where(
                    book_tag_association.c.book_id == book_id,
                    book_tag_association.c.tag_id == tag_id
                )
            )

    # 添加标签
    added_tags = []
    for tag_name in update.add_tags:
        tag_name = tag_name.strip().lower()
        if not tag_name:
            continue

        # 查找或创建标签
        result = await db.execute(
            select(Tag).where(Tag.name == tag_name)
        )
        tag = result.scalar_one_or_none()

        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            await db.flush()

        # 检查是否已关联
        result = await db.execute(
            select(book_tag_association)
            .where(
                book_tag_association.c.book_id == book_id,
                book_tag_association.c.tag_id == tag.id
            )
        )
        if not result.scalar_one_or_none():
            await db.execute(
                book_tag_association.insert()
                .values(book_id=book_id, tag_id=tag.id)
            )
            added_tags.append(tag)

    await db.commit()

    return {
        "book_id": book_id,
        "added": len(added_tags),
        "removed": len(update.remove_tag_ids),
    }


@router.post("/{book_id}/tags/{tag_name}", response_model=dict)
async def add_book_tag(
    book_id: int,
    tag_name: str,
    db: AsyncSession = Depends(get_db),
):
    """为图书添加单个标签"""
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )

    tag_name = tag_name.strip().lower()
    if not tag_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag name cannot be empty"
        )

    # 查找或创建标签
    result = await db.execute(
        select(Tag).where(Tag.name == tag_name)
    )
    tag = result.scalar_one_or_none()

    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        await db.flush()

    # 检查是否已关联
    result = await db.execute(
        select(book_tag_association)
        .where(
            book_tag_association.c.book_id == book_id,
            book_tag_association.c.tag_id == tag.id
        )
    )
    if result.scalar_one_or_none():
        return {
            "book_id": book_id,
            "tag_id": tag.id,
            "tag_name": tag.name,
            "message": "Tag already exists",
        }

    # 添加关联
    await db.execute(
        book_tag_association.insert()
        .values(book_id=book_id, tag_id=tag.id)
    )
    await db.commit()

    return {
        "book_id": book_id,
        "tag_id": tag.id,
        "tag_name": tag.name,
        "message": "Tag added successfully",
    }


@router.delete("/{book_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_book_tag(
    book_id: int,
    tag_id: int,
    db: AsyncSession = Depends(get_db),
):
    """移除图书的某个标签"""
    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found"
        )

    await db.execute(
        book_tag_association.delete()
        .where(
            book_tag_association.c.book_id == book_id,
            book_tag_association.c.tag_id == tag_id
        )
    )
    await db.commit()

    return None


# ========== 全局标签管理 ==========

@router.get("/tags/popular", response_model=List[dict])
async def get_popular_tags(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取热门标签"""
    from sqlalchemy import func

    result = await db.execute(
        select(Tag, func.count(book_tag_association.c.book_id).label("book_count"))
        .join(book_tag_association)
        .group_by(Tag.id)
        .order_by(func.count(book_tag_association.c.book_id).desc())
        .limit(limit)
    )
    rows = result.all()

    return [
        {
            "id": tag.id,
            "name": tag.name,
            "book_count": count,
        }
        for tag, count in rows
    ]
