"""
书架位置管理 API
Phase 10: Shelf Positioning
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.models import ShelfPosition, Book, Shelf, Bookshelf, Scan, ScanItem
from app.schemas.schemas import (
    ShelfPositionResponse,
    ShelfPositionCreate,
    ShelfPositionUpdate,
    ShelfVisualizationResponse,
)

router = APIRouter(prefix="/shelf-positions", tags=["shelf-positions"])


@router.get("/book/{book_id}", response_model=List[ShelfPositionResponse])
async def get_book_positions(
    book_id: int,
    current_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """
    获取图书的所有位置记录

    - current_only=True: 只返回当前有效位置
    - current_only=False: 返回所有历史位置
    """
    # 验证图书存在
    book_result = await db.execute(select(Book).where(Book.id == book_id))
    if not book_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")

    query = (
        select(ShelfPosition)
        .where(ShelfPosition.book_id == book_id)
        .order_by(ShelfPosition.created_at.desc())
    )

    if current_only:
        query = query.where(ShelfPosition.is_current == True)

    result = await db.execute(query)
    positions = result.scalars().all()

    return positions


@router.get("/shelf/{shelf_id}", response_model=List[ShelfPositionResponse])
async def get_shelf_positions(
    shelf_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取书架上所有书籍的当前位置"""
    # 验证书架存在
    shelf_result = await db.execute(select(Shelf).where(Shelf.id == shelf_id))
    if not shelf_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Shelf {shelf_id} not found")

    result = await db.execute(
        select(ShelfPosition)
        .where(ShelfPosition.shelf_id == shelf_id, ShelfPosition.is_current == True)
        .order_by(ShelfPosition.position_x)
    )
    positions = result.scalars().all()

    return positions


@router.post("", response_model=ShelfPositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    data: ShelfPositionCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的位置记录

    如果图书在当前书架已有位置，会将旧位置标记为历史
    """
    # 验证图书存在
    book_result = await db.execute(select(Book).where(Book.id == data.book_id))
    if not book_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Book {data.book_id} not found")

    # 验证书架存在
    shelf_result = await db.execute(select(Shelf).where(Shelf.id == data.shelf_id))
    shelf = shelf_result.scalar_one_or_none()
    if not shelf:
        raise HTTPException(status_code=404, detail=f"Shelf {data.shelf_id} not found")

    # 检查是否已有当前位置
    existing_result = await db.execute(
        select(ShelfPosition)
        .where(
            ShelfPosition.book_id == data.book_id,
            ShelfPosition.shelf_id == data.shelf_id,
            ShelfPosition.is_current == True,
        )
    )
    existing = existing_result.scalar_one_or_none()

    # 计算 position_order（如果没有提供）
    position_order = data.position_order
    if position_order is None:
        # 根据 position_x 计算顺序
        count_result = await db.execute(
            select(func.count(ShelfPosition.id))
            .where(
                ShelfPosition.shelf_id == data.shelf_id,
                ShelfPosition.is_current == True,
                ShelfPosition.position_x < data.position_x,
            )
        )
        position_order = (count_result.scalar() or 0) + 1

    # 创建新位置
    position = ShelfPosition(
        book_id=data.book_id,
        shelf_id=data.shelf_id,
        position_x=data.position_x,
        position_order=position_order,
        confidence=data.confidence,
        source=data.source,
        scan_id=data.scan_id,
        scan_item_id=data.scan_item_id,
        previous_position_id=existing.id if existing else None,
        is_current=True,
        bbox=data.bbox,
    )

    db.add(position)

    # 将旧位置标记为非当前
    if existing:
        existing.is_current = False

    await db.commit()
    await db.refresh(position)

    return position


@router.put("/{position_id}", response_model=ShelfPositionResponse)
async def update_position(
    position_id: int,
    data: ShelfPositionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新位置信息"""
    result = await db.execute(
        select(ShelfPosition).where(ShelfPosition.id == position_id)
    )
    position = result.scalar_one_or_none()

    if not position:
        raise HTTPException(status_code=404, detail=f"Position {position_id} not found")

    # 更新字段
    if data.position_x is not None:
        position.position_x = data.position_x
    if data.position_order is not None:
        position.position_order = data.position_order
    if data.confidence is not None:
        position.confidence = data.confidence
    if data.bbox is not None:
        position.bbox = data.bbox

    await db.commit()
    await db.refresh(position)

    return position


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position(
    position_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除位置记录"""
    result = await db.execute(
        select(ShelfPosition).where(ShelfPosition.id == position_id)
    )
    position = result.scalar_one_or_none()

    if not position:
        raise HTTPException(status_code=404, detail=f"Position {position_id} not found")

    await db.delete(position)
    await db.commit()

    return None


@router.get("/visualization/shelf/{shelf_id}", response_model=ShelfVisualizationResponse)
async def get_shelf_visualization(
    shelf_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取书架可视化数据

    返回书架上的所有书籍及其位置信息，用于可视化展示
    """
    # 获取书架信息
    shelf_result = await db.execute(
        select(Shelf, Bookshelf)
        .join(Bookshelf, Shelf.bookshelf_id == Bookshelf.id)
        .where(Shelf.id == shelf_id)
    )
    row = shelf_result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail=f"Shelf {shelf_id} not found")

    shelf, bookshelf = row

    # 获取最新扫描
    scan_result = await db.execute(
        select(Scan)
        .where(Scan.shelf_id == shelf_id)
        .order_by(Scan.scanned_at.desc())
        .limit(1)
    )
    latest_scan = scan_result.scalar_one_or_none()

    # 获取位置数据
    positions_result = await db.execute(
        select(ShelfPosition, Book)
        .join(Book, ShelfPosition.book_id == Book.id)
        .where(
            ShelfPosition.shelf_id == shelf_id,
            ShelfPosition.is_current == True,
        )
        .order_by(ShelfPosition.position_x)
    )
    position_rows = positions_result.all()

    books = []
    for pos, book in position_rows:
        book_data = {
            "book_id": book.id,
            "position_id": pos.id,
            "position_x": pos.position_x,
            "position_order": pos.position_order,
            "confidence": pos.confidence,
            "bbox": pos.bbox,
        }
        books.append(book_data)

    return {
        "shelf_id": shelf_id,
        "bookshelf_name": bookshelf.name,
        "level": shelf.level,
        "latest_scan_id": latest_scan.id if latest_scan else None,
        "scan_image_path": latest_scan.image_path if latest_scan else None,
        "books": books,
    }


@router.get("/visualization/bookshelf/{bookshelf_id}")
async def get_bookshelf_visualization(
    bookshelf_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取整个书柜的可视化数据
    """
    # 验证书柜存在
    bookshelf_result = await db.execute(
        select(Bookshelf).where(Bookshelf.id == bookshelf_id)
    )
    bookshelf = bookshelf_result.scalar_one_or_none()

    if not bookshelf:
        raise HTTPException(status_code=404, detail=f"Bookshelf {bookshelf_id} not found")

    # 获取所有层
    shelves_result = await db.execute(
        select(Shelf).where(Shelf.bookshelf_id == bookshelf_id).order_by(Shelf.level)
    )
    shelves = shelves_result.scalars().all()

    shelves_data = []
    for shelf in shelves:
        # 获取每层的扫描
        scan_result = await db.execute(
            select(Scan)
            .where(Scan.shelf_id == shelf.id)
            .order_by(Scan.scanned_at.desc())
            .limit(1)
        )
        latest_scan = scan_result.scalar_one_or_none()

        # 获取每层的位置
        positions_result = await db.execute(
            select(ShelfPosition, Book)
            .join(Book, ShelfPosition.book_id == Book.id)
            .where(
                ShelfPosition.shelf_id == shelf.id,
                ShelfPosition.is_current == True,
            )
            .order_by(ShelfPosition.position_x)
        )
        positions = positions_result.all()

        shelves_data.append({
            "shelf_id": shelf.id,
            "level": shelf.level,
            "latest_scan_id": latest_scan.id if latest_scan else None,
            "scan_image_path": latest_scan.image_path if latest_scan else None,
            "book_count": len(positions),
            "books": [
                {
                    "book_id": book.id,
                    "position_id": pos.id,
                    "position_x": pos.position_x,
                    "position_order": pos.position_order,
                    "confidence": pos.confidence,
                    "bbox": pos.bbox,
                }
                for pos, book in positions
            ],
        })

    return {
        "bookshelf_id": bookshelf_id,
        "bookshelf_name": bookshelf.name,
        "shelves": shelves_data,
    }


@router.post("/from-scan/{scan_item_id}", response_model=ShelfPositionResponse)
async def create_position_from_scan(
    scan_item_id: int,
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    从扫描结果创建位置记录

    将识别项与图书关联，并记录位置
    """
    # 获取扫描项
    scan_item_result = await db.execute(
        select(ScanItem).where(ScanItem.id == scan_item_id)
    )
    scan_item = scan_item_result.scalar_one_or_none()

    if not scan_item:
        raise HTTPException(status_code=404, detail=f"ScanItem {scan_item_id} not found")

    # 获取扫描信息
    scan_result = await db.execute(
        select(Scan).where(Scan.id == scan_item.scan_id)
    )
    scan = scan_result.scalar_one_or_none()

    if not scan or not scan.shelf_id:
        raise HTTPException(
            status_code=400, detail="Scan item is not associated with a shelf"
        )

    # 计算 position_x 从 bbox
    position_x = 0.0
    if scan_item.bbox:
        position_x = scan_item.bbox.get("x", 0.0) + scan_item.bbox.get("width", 0.0) / 2

    # 创建位置记录
    position = ShelfPosition(
        book_id=book_id,
        shelf_id=scan.shelf_id,
        position_x=position_x,
        confidence=scan_item.confidence,
        source="scan",
        scan_id=scan.id,
        scan_item_id=scan_item.id,
        is_current=True,
        bbox=scan_item.bbox,
    )

    db.add(position)
    await db.commit()
    await db.refresh(position)

    return position
