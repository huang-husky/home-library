"""
Bookshelves API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.models import Bookshelf, Shelf, Book, ShelfPosition
from app.schemas.schemas import (
    BookshelfCreate, BookshelfUpdate, BookshelfResponse, BookshelfDetailResponse,
    ShelfCreate, ShelfUpdate, ShelfResponse, ShelfDetailResponse
)

router = APIRouter(prefix="/bookshelves", tags=["bookshelves"])


# ========== Bookshelf Endpoints ==========

@router.get("", response_model=List[BookshelfDetailResponse])
async def list_bookshelves(db: AsyncSession = Depends(get_db)):
    """获取所有书柜"""
    stmt = select(Bookshelf).order_by(Bookshelf.created_at.desc())
    result = await db.execute(stmt)
    bookshelves = result.scalars().all()

    # 计算每个书柜的层数
    response_items = []
    for bs in bookshelves:
        shelf_count_stmt = select(func.count()).where(Shelf.bookshelf_id == bs.id)
        shelf_count_result = await db.execute(shelf_count_stmt)
        shelf_count = shelf_count_result.scalar()

        response_items.append(BookshelfDetailResponse(
            id=bs.id,
            name=bs.name,
            location=bs.location,
            width=bs.width,
            height=bs.height,
            description=bs.description,
            created_at=bs.created_at,
            updated_at=bs.updated_at,
            shelf_count=shelf_count,
        ))

    return response_items


@router.post("", response_model=BookshelfResponse, status_code=status.HTTP_201_CREATED)
async def create_bookshelf(
    data: BookshelfCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建书柜"""
    bookshelf = Bookshelf(**data.model_dump())
    db.add(bookshelf)
    await db.commit()
    await db.refresh(bookshelf)
    return bookshelf


@router.get("/{bookshelf_id}", response_model=BookshelfResponse)
async def get_bookshelf(bookshelf_id: int, db: AsyncSession = Depends(get_db)):
    """获取书柜详情"""
    stmt = select(Bookshelf).where(Bookshelf.id == bookshelf_id)
    result = await db.execute(stmt)
    bookshelf = result.scalar_one_or_none()

    if not bookshelf:
        raise HTTPException(status_code=404, detail="Bookshelf not found")

    return bookshelf


@router.put("/{bookshelf_id}", response_model=BookshelfResponse)
async def update_bookshelf(
    bookshelf_id: int,
    data: BookshelfUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新书柜"""
    stmt = select(Bookshelf).where(Bookshelf.id == bookshelf_id)
    result = await db.execute(stmt)
    bookshelf = result.scalar_one_or_none()

    if not bookshelf:
        raise HTTPException(status_code=404, detail="Bookshelf not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bookshelf, field, value)

    await db.commit()
    await db.refresh(bookshelf)
    return bookshelf


@router.delete("/{bookshelf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookshelf(bookshelf_id: int, db: AsyncSession = Depends(get_db)):
    """删除书柜（级联删除层）"""
    stmt = select(Bookshelf).where(Bookshelf.id == bookshelf_id)
    result = await db.execute(stmt)
    bookshelf = result.scalar_one_or_none()

    if not bookshelf:
        raise HTTPException(status_code=404, detail="Bookshelf not found")

    await db.delete(bookshelf)
    await db.commit()
    return None


# ========== Shelf Endpoints ==========

@router.get("/{bookshelf_id}/shelves", response_model=List[ShelfDetailResponse])
async def list_shelves(bookshelf_id: int, db: AsyncSession = Depends(get_db)):
    """获取书柜的所有层"""
    # 验证书柜存在
    stmt = select(Bookshelf).where(Bookshelf.id == bookshelf_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bookshelf not found")

    # 查询层
    stmt = select(Shelf).where(
        Shelf.bookshelf_id == bookshelf_id
    ).order_by(Shelf.level)

    result = await db.execute(stmt)
    shelves = result.scalars().all()

    # 计算每层的书籍数量
    response_items = []
    for shelf in shelves:
        book_count_stmt = select(func.count()).where(ShelfPosition.shelf_id == shelf.id)
        book_count_result = await db.execute(book_count_stmt)
        book_count = book_count_result.scalar()

        response_items.append(ShelfDetailResponse(
            id=shelf.id,
            bookshelf_id=shelf.bookshelf_id,
            level=shelf.level,
            height=shelf.height,
            created_at=shelf.created_at,
            updated_at=shelf.updated_at,
            book_count=book_count,
        ))

    return response_items


@router.post("/{bookshelf_id}/shelves", response_model=ShelfResponse, status_code=status.HTTP_201_CREATED)
async def create_shelf(
    bookshelf_id: int,
    data: ShelfCreate,
    db: AsyncSession = Depends(get_db)
):
    """为书柜添加一层"""
    # 验证书柜存在
    stmt = select(Bookshelf).where(Bookshelf.id == bookshelf_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bookshelf not found")

    shelf = Shelf(
        bookshelf_id=bookshelf_id,
        level=data.level,
        height=data.height,
    )
    db.add(shelf)
    await db.commit()
    await db.refresh(shelf)
    return shelf


# 单独的 shelf 路由
shelf_router = APIRouter(prefix="/shelves", tags=["shelves"])


@shelf_router.get("/{shelf_id}", response_model=ShelfResponse)
async def get_shelf(shelf_id: int, db: AsyncSession = Depends(get_db)):
    """获取层详情"""
    stmt = select(Shelf).where(Shelf.id == shelf_id)
    result = await db.execute(stmt)
    shelf = result.scalar_one_or_none()

    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    return shelf


@shelf_router.put("/{shelf_id}", response_model=ShelfResponse)
async def update_shelf(
    shelf_id: int,
    data: ShelfUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新层信息"""
    stmt = select(Shelf).where(Shelf.id == shelf_id)
    result = await db.execute(stmt)
    shelf = result.scalar_one_or_none()

    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shelf, field, value)

    await db.commit()
    await db.refresh(shelf)
    return shelf


@shelf_router.delete("/{shelf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shelf(shelf_id: int, db: AsyncSession = Depends(get_db)):
    """删除层"""
    stmt = select(Shelf).where(Shelf.id == shelf_id)
    result = await db.execute(stmt)
    shelf = result.scalar_one_or_none()

    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    await db.delete(shelf)
    await db.commit()
    return None
