"""
AI Import API
Phase 8: AI Book Import Pipeline

提供 ScanItem 的匹配、审核和导入功能
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import ScanItem, Scan, Book, Edition, Work, ShelfPosition
from app.schemas.schemas import (
    ScanItemResponse,
    BookImportRequest,
    BookImportResponse,
    BookMetadataImport,
)
from app.services.matching_service import EditionMatchingService, BatchImportService
from app.services.books import create_book_with_metadata

router = APIRouter(prefix="/ai-import", tags=["ai-import"])


@router.post("/scan/{scan_id}/match", response_model=dict)
async def match_scan_items(
    scan_id: int,
    auto_threshold: float = 0.85,
    db: AsyncSession = Depends(get_db),
):
    """
    对扫描的所有项目进行元数据搜索和匹配

    - 状态: detected → searching → matched/needs_review
    - 高置信度自动匹配，低置信度需要审核
    """
    # 获取扫描项
    result = await db.execute(
        select(ScanItem).where(
            ScanItem.scan_id == scan_id,
            ScanItem.status.in_(["detected", "failed"])
        )
    )
    items = result.scalars().all()

    if not items:
        return {
            "scan_id": scan_id,
            "processed": 0,
            "message": "没有待匹配的项目",
        }

    matching_service = EditionMatchingService()
    processed = []

    for item in items:
        try:
            # 更新状态为 searching
            item.status = "searching"
            item.search_attempted_at = datetime.utcnow()
            await db.flush()

            # 执行匹配
            match_result = await matching_service.search_and_match(item.detected_text)

            # 保存结果
            item.search_query = match_result.get("search_query")
            item.candidates = match_result.get("candidates", [])
            item.candidates_count = match_result.get("candidates_count", 0)

            if match_result["status"] == "matched":
                item.status = "matched"
                item.matched_candidate_index = match_result["matched_index"]
                item.match_confidence = match_result["match_confidence"]
                item.matched_at = datetime.utcnow()

                # 高置信度自动标记为 confirmed
                if item.match_confidence >= auto_threshold:
                    item.status = "confirmed"
                    item.reviewed_at = datetime.utcnow()
                    item.review_note = f"Auto-confirmed (confidence: {item.match_confidence:.2f})"

            elif match_result["status"] == "needs_review":
                item.status = "needs_review"
                item.matched_candidate_index = match_result.get("matched_index")
                item.match_confidence = match_result.get("match_confidence")

            elif match_result["status"] == "no_candidates":
                item.status = "failed"
                item.search_error = "No candidates found"

            else:
                item.status = "failed"
                item.search_error = match_result.get("reason", "Unknown error")

            processed.append({
                "item_id": item.id,
                "status": item.status,
                "candidates_count": item.candidates_count,
                "match_confidence": item.match_confidence,
            })

        except Exception as e:
            item.status = "failed"
            item.search_error = str(e)
            processed.append({
                "item_id": item.id,
                "status": "failed",
                "error": str(e),
            })

    await db.commit()

    return {
        "scan_id": scan_id,
        "processed": len(processed),
        "results": processed,
        "summary": {
            "matched": sum(1 for p in processed if p["status"] == "matched"),
            "confirmed": sum(1 for p in processed if p["status"] == "confirmed"),
            "needs_review": sum(1 for p in processed if p["status"] == "needs_review"),
            "failed": sum(1 for p in processed if p["status"] == "failed"),
        }
    }


@router.get("/scan/{scan_id}/items", response_model=dict)
async def get_import_items(
    scan_id: int,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取扫描项及其匹配状态（用于审核页面）"""
    query = select(ScanItem).where(ScanItem.scan_id == scan_id)
    if status:
        query = query.where(ScanItem.status == status)

    result = await db.execute(query.order_by(ScanItem.id))
    items = result.scalars().all()

    # 获取 Scan 信息
    scan_result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = scan_result.scalar_one_or_none()

    return {
        "scan_id": scan_id,
        "image_path": scan.image_path if scan else None,
        "items": [
            {
                "id": item.id,
                "detected_text": item.detected_text,
                "confidence": item.confidence,
                "bbox": item.bbox,
                "status": item.status,
                "candidates": item.candidates,
                "candidates_count": item.candidates_count,
                "matched_candidate_index": item.matched_candidate_index,
                "match_confidence": item.match_confidence,
                "search_error": item.search_error,
                "match_error": item.match_error,
                "imported_book_id": item.imported_book_id,
            }
            for item in items
        ],
        "stats": {
            "total": len(items),
            "detected": sum(1 for i in items if i.status == "detected"),
            "searching": sum(1 for i in items if i.status == "searching"),
            "matched": sum(1 for i in items if i.status == "matched"),
            "confirmed": sum(1 for i in items if i.status == "confirmed"),
            "needs_review": sum(1 for i in items if i.status == "needs_review"),
            "imported": sum(1 for i in items if i.status == "imported"),
            "failed": sum(1 for i in items if i.status == "failed"),
            "skipped": sum(1 for i in items if i.status == "skipped"),
        }
    }


@router.post("/items/{item_id}/select-candidate", response_model=dict)
async def select_candidate(
    item_id: int,
    candidate_index: int,
    db: AsyncSession = Depends(get_db),
):
    """
    用户选择候选版本
    - 状态变为 confirmed
    """
    result = await db.execute(
        select(ScanItem).where(ScanItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if not item.candidates or candidate_index >= len(item.candidates):
        raise HTTPException(status_code=400, detail="Invalid candidate index")

    item.matched_candidate_index = candidate_index
    item.status = "confirmed"
    item.reviewed_at = datetime.utcnow()

    await db.commit()

    return {
        "item_id": item_id,
        "status": "confirmed",
        "selected_candidate": item.candidates[candidate_index],
    }


@router.post("/items/{item_id}/skip", response_model=dict)
async def skip_item(
    item_id: int,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """跳过此项目（无法识别或不需要导入）"""
    result = await db.execute(
        select(ScanItem).where(ScanItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.status = "skipped"
    item.reviewed_at = datetime.utcnow()
    item.review_note = reason or "User skipped"

    await db.commit()

    return {"item_id": item_id, "status": "skipped"}


@router.post("/items/{item_id}/import", response_model=dict)
async def import_item(
    item_id: int,
    bookshelf_id: Optional[int] = None,
    shelf_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    导入单个项目到图书馆
    - 需要状态为 confirmed
    """
    result = await db.execute(
        select(ScanItem).where(ScanItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.status not in ["confirmed", "matched"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot import item with status: {item.status}"
        )

    if not item.candidates or item.matched_candidate_index is None:
        raise HTTPException(status_code=400, detail="No candidate selected")

    try:
        # 构建导入请求
        candidate = item.candidates[item.matched_candidate_index]
        from app.schemas.schemas import BookMetadataImport

        metadata = BookMetadataImport(
            source=candidate["source"],
            source_id=candidate["source_id"],
            title=candidate["title"],
            subtitle=candidate.get("subtitle"),
            authors=candidate.get("authors", []),
            publisher=candidate.get("publisher"),
            publish_date=candidate.get("publish_date"),
            publish_year=candidate.get("publish_year"),
            isbn13=candidate.get("isbn13"),
            isbn10=candidate.get("isbn10"),
            language=candidate.get("language"),
            page_count=candidate.get("page_count"),
            cover_url=candidate.get("cover_url"),
            description=candidate.get("description"),
        )

        import_request = BookImportRequest(
            candidate=metadata,
            bookshelf_id=bookshelf_id,
            shelf_id=shelf_id,
        )

        # 执行导入
        import_result = await create_book_with_metadata(db, import_request)

        # 更新 ScanItem
        item.status = "imported"
        item.imported_book_id = import_result.book_id
        item.imported_at = datetime.utcnow()

        # Phase 10: 创建 ShelfPosition 记录位置
        scan_result = await db.execute(
            select(Scan).where(Scan.id == item.scan_id)
        )
        scan = scan_result.scalar_one_or_none()

        if scan and scan.shelf_id and item.bbox:
            # 计算 position_x（bbox 中心点）
            position_x = item.bbox.get("x", 0.0) + item.bbox.get("width", 0.0) / 2

            # 创建位置记录
            position = ShelfPosition(
                book_id=import_result.book_id,
                shelf_id=scan.shelf_id,
                position_x=position_x,
                confidence=item.confidence,
                source="scan",
                scan_id=scan.id,
                scan_item_id=item.id,
                is_current=True,
                bbox=item.bbox,
            )
            db.add(position)

        await db.commit()

        return {
            "item_id": item_id,
            "status": "imported",
            "book_id": import_result.book_id,
            "is_new_work": import_result.is_new_work,
            "is_new_edition": import_result.is_new_edition,
        }

    except Exception as e:
        item.status = "failed"
        item.import_error = str(e)
        await db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )


@router.post("/scan/{scan_id}/batch-import", response_model=dict)
async def batch_import(
    scan_id: int,
    bookshelf_id: Optional[int] = None,
    shelf_id: Optional[int] = None,
    only_confirmed: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """
    批量导入所有已确认的项目

    - only_confirmed=True: 只导入 confirmed 状态
    - only_confirmed=False: 尝试导入 matched 状态（自动确认）
    """
    statuses = ["confirmed"] if only_confirmed else ["confirmed", "matched"]

    result = await db.execute(
        select(ScanItem).where(
            ScanItem.scan_id == scan_id,
            ScanItem.status.in_(statuses)
        )
    )
    items = result.scalars().all()

    imported = []
    failed = []

    for item in items:
        try:
            # 自动确认 matched 状态
            if item.status == "matched":
                item.status = "confirmed"
                item.reviewed_at = datetime.utcnow()
                item.review_note = "Auto-confirmed during batch import"

            # 执行导入
            candidate = item.candidates[item.matched_candidate_index]
            from app.schemas.schemas import BookMetadataImport, BookImportRequest

            metadata = BookMetadataImport(**candidate)
            import_request = BookImportRequest(
                candidate=metadata,
                bookshelf_id=bookshelf_id,
                shelf_id=shelf_id,
            )

            import_result = await create_book_with_metadata(db, import_request)

            item.status = "imported"
            item.imported_book_id = import_result.book_id
            item.imported_at = datetime.utcnow()

            # Phase 10: 创建 ShelfPosition
            scan_result = await db.execute(
                select(Scan).where(Scan.id == item.scan_id)
            )
            scan = scan_result.scalar_one_or_none()

            if scan and scan.shelf_id and item.bbox:
                position_x = item.bbox.get("x", 0.0) + item.bbox.get("width", 0.0) / 2

                position = ShelfPosition(
                    book_id=import_result.book_id,
                    shelf_id=scan.shelf_id,
                    position_x=position_x,
                    confidence=item.confidence,
                    source="scan",
                    scan_id=scan.id,
                    scan_item_id=item.id,
                    is_current=True,
                    bbox=item.bbox,
                )
                db.add(position)

            imported.append({
                "item_id": item.id,
                "book_id": import_result.book_id,
            })

        except Exception as e:
            failed.append({
                "item_id": item.id,
                "error": str(e),
            })

    await db.commit()

    return {
        "scan_id": scan_id,
        "total": len(items),
        "imported": len(imported),
        "failed": len(failed),
        "imported_items": imported,
        "failed_items": failed,
    }


@router.post("/scan/{scan_id}/auto-confirm", response_model=dict)
async def auto_confirm_high_confidence(
    scan_id: int,
    threshold: float = 0.85,
    db: AsyncSession = Depends(get_db),
):
    """自动确认高置信度的匹配结果"""
    result = await db.execute(
        select(ScanItem).where(
            ScanItem.scan_id == scan_id,
            ScanItem.status == "matched",
            ScanItem.match_confidence >= threshold
        )
    )
    items = result.scalars().all()

    confirmed_count = 0
    for item in items:
        item.status = "confirmed"
        item.reviewed_at = datetime.utcnow()
        item.review_note = f"Auto-confirmed (confidence: {item.match_confidence:.2f})"
        confirmed_count += 1

    await db.commit()

    return {
        "scan_id": scan_id,
        "confirmed_count": confirmed_count,
        "threshold": threshold,
    }


@router.post("/items/{item_id}/retry", response_model=dict)
async def retry_match(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """重新匹配失败的项目"""
    result = await db.execute(
        select(ScanItem).where(ScanItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # 重置状态
    item.status = "detected"
    item.search_query = None
    item.candidates = None
    item.candidates_count = 0
    item.matched_candidate_index = None
    item.match_confidence = None
    item.search_error = None
    item.match_error = None

    await db.commit()

    return {"item_id": item_id, "status": "reset", "message": "Ready to re-match"}
