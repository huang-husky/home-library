"""
书架扫描 API
Phase 7: Shelf Image Recognition MVP
"""
import os
import uuid
import shutil
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from PIL import Image

from app.db.database import get_db
from app.models.models import Scan, ScanItem, Bookshelf, Shelf
from app.schemas.schemas import (
    ScanResponse,
    ScanDetailResponse,
    ScanItemResponse,
    ScanItemUpdate,
    ScanCreateResponse,
    BoundingBox,
    ScanStats,
    ShelfScanRequest,
)
from app.services.ai.pipeline import RecognitionPipeline

router = APIRouter(prefix="/scans", tags=["scans"])

# 上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "scans")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def build_scan_item_response(item: ScanItem) -> ScanItemResponse:
    """构建 ScanItemResponse，处理新旧字段"""
    return ScanItemResponse(
        id=item.id,
        detected_text=item.detected_text,
        confidence=item.confidence,
        bbox=BoundingBox(**item.bbox) if item.bbox else None,
        status=item.status,
        # Phase 8 字段
        search_query=item.search_query,
        search_attempted_at=item.search_attempted_at,
        search_error=item.search_error,
        candidates=item.candidates,
        candidates_count=item.candidates_count,
        matched_candidate_index=item.matched_candidate_index,
        match_confidence=item.match_confidence,
        matched_at=item.matched_at,
        match_error=item.match_error,
        imported_book_id=item.imported_book_id,
        imported_at=item.imported_at,
        import_error=item.import_error,
        reviewed_at=item.reviewed_at,
        reviewed_by=item.reviewed_by,
        review_note=item.review_note,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post("/upload", response_model=ScanCreateResponse)
async def upload_scan(
    bookshelf_id: Optional[int] = Form(None),
    shelf_id: Optional[int] = Form(None),
    preprocess: bool = Form(True),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    上传书架图片并识别书籍

    流程：
    1. 保存原始图片
    2. 预处理（可选）
    3. 检测书籍区域
    4. OCR 识别书脊文字
    5. 保存识别结果
    """
    # 验证书柜/层是否存在
    if bookshelf_id:
        result = await db.execute(
            select(Bookshelf).where(Bookshelf.id == bookshelf_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bookshelf {bookshelf_id} not found"
            )

    if shelf_id:
        result = await db.execute(
            select(Shelf).where(Shelf.id == shelf_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shelf {shelf_id} not found"
            )

    # 生成唯一文件名
    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # 保存文件
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    finally:
        file.file.close()

    # 运行识别管道
    try:
        image = Image.open(file_path)
        pipeline = RecognitionPipeline()
        recognition_results = await pipeline.recognize_shelf(image, preprocess=preprocess)
    except Exception as e:
        # 清理文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recognition failed: {str(e)}"
        )

    # 创建扫描记录
    scan = Scan(
        bookshelf_id=bookshelf_id,
        shelf_id=shelf_id,
        image_path=file_path,
        scanned_at=datetime.utcnow(),
    )
    db.add(scan)
    await db.flush()  # 获取 scan.id

    # 创建识别项
    scan_items = []
    for i, result in enumerate(recognition_results):
        item = ScanItem(
            scan_id=scan.id,
            detected_text=result["text"],
            confidence=result["confidence"],
            bbox={
                "x": result["bbox"]["x"],
                "y": result["bbox"]["y"],
                "width": result["bbox"]["width"],
                "height": result["bbox"]["height"],
            },
            status="pending",
        )
        db.add(item)
        scan_items.append(item)

    await db.commit()

    # 刷新以获取 ID
    for item in scan_items:
        await db.refresh(item)

    return ScanCreateResponse(
        scan_id=scan.id,
        detected_count=len(scan_items),
        items=[build_scan_item_response(item) for item in scan_items],
        message=f"Successfully detected {len(scan_items)} books",
    )


@router.get("", response_model=List[ScanResponse])
async def list_scans(
    bookshelf_id: Optional[int] = None,
    shelf_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """列出扫描记录"""
    query = select(Scan).order_by(Scan.scanned_at.desc())

    if bookshelf_id:
        query = query.where(Scan.bookshelf_id == bookshelf_id)
    if shelf_id:
        query = query.where(Scan.shelf_id == shelf_id)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    scans = result.scalars().all()

    # 获取每个 scan 的 item 数量
    responses = []
    for scan in scans:
        count_result = await db.execute(
            select(ScanItem).where(ScanItem.scan_id == scan.id)
        )
        item_count = len(count_result.scalars().all())

        responses.append(ScanResponse(
            id=scan.id,
            bookshelf_id=scan.bookshelf_id,
            shelf_id=scan.shelf_id,
            image_path=scan.image_path,
            scanned_at=scan.scanned_at,
            item_count=item_count,
        ))

    return responses


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取扫描详情"""
    result = await db.execute(
        select(Scan).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )

    # 获取识别项
    items_result = await db.execute(
        select(ScanItem).where(ScanItem.scan_id == scan_id)
    )
    items = items_result.scalars().all()

    return ScanDetailResponse(
        id=scan.id,
        bookshelf_id=scan.bookshelf_id,
        shelf_id=scan.shelf_id,
        image_path=scan.image_path,
        scanned_at=scan.scanned_at,
        item_count=len(items),
        items=[build_scan_item_response(item) for item in items],
    )


@router.get("/{scan_id}/items", response_model=List[ScanItemResponse])
async def get_scan_items(
    scan_id: int,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取扫描的所有识别项"""
    # 验证 scan 存在
    result = await db.execute(
        select(Scan).where(Scan.id == scan_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )

    query = select(ScanItem).where(ScanItem.scan_id == scan_id)
    if status:
        query = query.where(ScanItem.status == status)

    result = await db.execute(query)
    items = result.scalars().all()

    return [build_scan_item_response(item) for item in items]


@router.patch("/items/{item_id}", response_model=ScanItemResponse)
async def update_scan_item(
    item_id: int,
    update: ScanItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新识别项（编辑文本、状态、位置等）"""
    result = await db.execute(
        select(ScanItem).where(ScanItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ScanItem {item_id} not found"
        )

    # 更新字段
    if update.detected_text is not None:
        item.detected_text = update.detected_text
    if update.status is not None:
        item.status = update.status
    if update.matched_book_id is not None:
        item.matched_book_id = update.matched_book_id
    if update.bbox is not None:
        item.bbox = {
            "x": update.bbox.x,
            "y": update.bbox.y,
            "width": update.bbox.width,
            "height": update.bbox.height,
        }

    await db.commit()
    await db.refresh(item)

    return build_scan_item_response(item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除识别项（误检时移除）"""
    result = await db.execute(
        select(ScanItem).where(ScanItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ScanItem {item_id} not found"
        )

    await db.delete(item)
    await db.commit()

    return None


@router.post("/{scan_id}/items", response_model=ScanItemResponse)
async def add_scan_item(
    scan_id: int,
    text: str,
    bbox: BoundingBox,
    confidence: float = 1.0,
    db: AsyncSession = Depends(get_db),
):
    """手动添加识别项（漏检时补录）"""
    # 验证 scan 存在
    result = await db.execute(
        select(Scan).where(Scan.id == scan_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )

    item = ScanItem(
        scan_id=scan_id,
        detected_text=text,
        confidence=confidence,
        bbox={
            "x": bbox.x,
            "y": bbox.y,
            "width": bbox.width,
            "height": bbox.height,
        },
        status="confirmed",  # 手动添加默认为 confirmed
    )

    db.add(item)
    await db.commit()
    await db.refresh(item)

    return build_scan_item_response(item)


@router.get("/{scan_id}/stats", response_model=ScanStats)
async def get_scan_stats(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取扫描统计信息"""
    result = await db.execute(
        select(ScanItem).where(ScanItem.scan_id == scan_id)
    )
    items = result.scalars().all()

    total = len(items)
    high = sum(1 for i in items if i.confidence >= 0.8)
    medium = sum(1 for i in items if 0.5 <= i.confidence < 0.8)
    low = sum(1 for i in items if i.confidence < 0.5)
    pending = sum(1 for i in items if i.status == "pending")
    confirmed = sum(1 for i in items if i.status == "confirmed")
    rejected = sum(1 for i in items if i.status == "rejected")

    return ScanStats(
        total_items=total,
        high_confidence=high,
        medium_confidence=medium,
        low_confidence=low,
        pending_count=pending,
        confirmed_count=confirmed,
        rejected_count=rejected,
    )


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: int,
    delete_image: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """删除扫描记录（及相关图片）"""
    result = await db.execute(
        select(Scan).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )

    # 删除图片文件
    if delete_image and scan.image_path and os.path.exists(scan.image_path):
        try:
            os.remove(scan.image_path)
        except OSError:
            pass  # 忽略文件删除错误

    # 级联删除识别项
    await db.delete(scan)
    await db.commit()

    return None


@router.get("/{scan_id}/image")
async def get_scan_image(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取扫描图片"""
    from fastapi.responses import FileResponse

    result = await db.execute(
        select(Scan).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )

    if not scan.image_path or not os.path.exists(scan.image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    return FileResponse(
        scan.image_path,
        media_type="image/jpeg",
        filename=f"scan_{scan_id}.jpg"
    )
