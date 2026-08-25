"""
Books API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.models import Book, Work, Edition, ShelfPosition, Shelf, Bookshelf
from app.schemas.schemas import (
    BookCreate, BookUpdate, BookResponse, BookDetailResponse, BookListResponse
)

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=BookListResponse)
async def list_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取图书列表"""
    # 构建查询
    stmt = select(Book).options(
        selectinload(Book.edition).selectinload(Edition.work),
    ).order_by(Book.created_at.desc())

    # 获取总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # 分页
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    books = result.scalars().all()

    # 构建响应
    items = []
    for book in books:
        # 手动构建响应数据
        edition_data = None
        work_data = None
        if book.edition:
            edition_data = {
                "id": book.edition.id,
                "work_id": book.edition.work_id,
                "title": book.edition.title,
                "isbn10": book.edition.isbn10,
                "isbn13": book.edition.isbn13,
                "publisher": book.edition.publisher,
                "publish_date": book.edition.publish_date,
                "page_count": book.edition.page_count,
                "cover_url": book.edition.cover_url,
                "source": book.edition.source,
                "source_id": book.edition.source_id,
                "created_at": book.edition.created_at,
                "updated_at": book.edition.updated_at,
            }
            if book.edition.work:
                work_data = {
                    "id": book.edition.work.id,
                    "title": book.edition.work.title,
                    "subtitle": book.edition.work.subtitle,
                    "original_title": book.edition.work.original_title,
                    "description": book.edition.work.description,
                    "language": book.edition.work.language,
                    "created_at": book.edition.work.created_at,
                    "updated_at": book.edition.work.updated_at,
                }

        detail = BookDetailResponse(
            id=book.id,
            edition_id=book.edition_id,
            status=book.status,
            owner=book.owner,
            notes=book.notes,
            confidence=book.confidence,
            created_at=book.created_at,
            updated_at=book.updated_at,
            edition=edition_data,
            work=work_data,
        )
        items.append(detail)

    return BookListResponse(total=total, items=items)


@router.get("/search", response_model=BookListResponse)
async def search_books(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """搜索图书"""
    # 通过 title 搜索 Work，然后找到对应的 Books
    stmt = select(Book).join(Edition).join(Work).where(
        or_(
            Work.title.contains(q),
            Edition.title.contains(q),
            Edition.isbn13.contains(q),
            Edition.publisher.contains(q),
        )
    ).options(
        selectinload(Book.edition).selectinload(Edition.work),
    ).order_by(Book.created_at.desc())

    # 获取总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # 分页
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    books = result.scalars().all()

    # 构建响应
    items = []
    for book in books:
        edition_data = None
        work_data = None
        if book.edition:
            edition_data = {
                "id": book.edition.id,
                "work_id": book.edition.work_id,
                "title": book.edition.title,
                "isbn10": book.edition.isbn10,
                "isbn13": book.edition.isbn13,
                "publisher": book.edition.publisher,
                "publish_date": book.edition.publish_date,
                "page_count": book.edition.page_count,
                "cover_url": book.edition.cover_url,
                "source": book.edition.source,
                "source_id": book.edition.source_id,
                "created_at": book.edition.created_at,
                "updated_at": book.edition.updated_at,
            }
            if book.edition.work:
                work_data = {
                    "id": book.edition.work.id,
                    "title": book.edition.work.title,
                    "subtitle": book.edition.work.subtitle,
                    "original_title": book.edition.work.original_title,
                    "description": book.edition.work.description,
                    "language": book.edition.work.language,
                    "created_at": book.edition.work.created_at,
                    "updated_at": book.edition.work.updated_at,
                }

        detail = BookDetailResponse(
            id=book.id,
            edition_id=book.edition_id,
            status=book.status,
            owner=book.owner,
            notes=book.notes,
            confidence=book.confidence,
            created_at=book.created_at,
            updated_at=book.updated_at,
            edition=edition_data,
            work=work_data,
        )
        items.append(detail)

    return BookListResponse(total=total, items=items)


@router.get("/{book_id}", response_model=BookDetailResponse)
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """获取图书详情"""
    stmt = select(Book).where(Book.id == book_id).options(
        selectinload(Book.edition).selectinload(Edition.work),
        selectinload(Book.shelf_positions).selectinload(ShelfPosition.shelf),
    )
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    edition_data = None
    work_data = None
    if book.edition:
        edition_data = {
            "id": book.edition.id,
            "work_id": book.edition.work_id,
            "title": book.edition.title,
            "isbn10": book.edition.isbn10,
            "isbn13": book.edition.isbn13,
            "publisher": book.edition.publisher,
            "publish_date": book.edition.publish_date,
            "page_count": book.edition.page_count,
            "cover_url": book.edition.cover_url,
            "source": book.edition.source,
            "source_id": book.edition.source_id,
            "created_at": book.edition.created_at,
            "updated_at": book.edition.updated_at,
        }
        if book.edition.work:
            work_data = {
                "id": book.edition.work.id,
                "title": book.edition.work.title,
                "subtitle": book.edition.work.subtitle,
                "original_title": book.edition.work.original_title,
                "description": book.edition.work.description,
                "language": book.edition.work.language,
                "created_at": book.edition.work.created_at,
                "updated_at": book.edition.work.updated_at,
            }

    return BookDetailResponse(
        id=book.id,
        edition_id=book.edition_id,
        status=book.status,
        owner=book.owner,
        notes=book.notes,
        confidence=book.confidence,
        created_at=book.created_at,
        updated_at=book.updated_at,
        edition=edition_data,
        work=work_data,
    )


@router.post("", response_model=BookDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_book(book_data: BookCreate, db: AsyncSession = Depends(get_db)):
    """创建图书"""
    # 1. 创建 Work
    work = Work(
        title=book_data.title,
        subtitle=book_data.subtitle,
        language="zh",
    )
    db.add(work)
    await db.flush()

    # 2. 创建 Edition
    edition = Edition(
        work_id=work.id,
        title=book_data.title,
        isbn13=book_data.isbn13,
        publisher=book_data.publisher,
    )
    db.add(edition)
    await db.flush()

    # 3. 创建 Book
    book = Book(
        edition_id=edition.id,
        status=book_data.status,
        owner=book_data.owner,
        notes=book_data.notes,
        confidence=1.0,
    )
    db.add(book)
    await db.flush()

    await db.commit()

    await db.refresh(book)
    await db.refresh(edition)
    await db.refresh(work)

    work_data = {
        "id": work.id,
        "title": work.title,
        "subtitle": work.subtitle,
        "original_title": work.original_title,
        "description": work.description,
        "language": work.language,
        "created_at": work.created_at,
        "updated_at": work.updated_at,
    }

    edition_data = {
        "id": edition.id,
        "work_id": edition.work_id,
        "title": edition.title,
        "isbn10": edition.isbn10,
        "isbn13": edition.isbn13,
        "publisher": edition.publisher,
        "publish_date": edition.publish_date,
        "page_count": edition.page_count,
        "cover_url": edition.cover_url,
        "source": edition.source,
        "source_id": edition.source_id,
        "created_at": edition.created_at,
        "updated_at": edition.updated_at,
    }

    return BookDetailResponse(
        id=book.id,
        edition_id=book.edition_id,
        status=book.status,
        owner=book.owner,
        notes=book.notes,
        confidence=book.confidence,
        created_at=book.created_at,
        updated_at=book.updated_at,
        edition=edition_data,
        work=work_data,
    )


@router.put("/{book_id}", response_model=BookDetailResponse)
async def update_book(
    book_id: int,
    book_data: BookUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新图书"""
    stmt = select(Book).where(Book.id == book_id).options(
        selectinload(Book.edition).selectinload(Edition.work),
    )
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    update_data = book_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)

    await db.commit()
    await db.refresh(book)

    edition_data = None
    work_data = None
    if book.edition:
        edition_data = {
            "id": book.edition.id,
            "work_id": book.edition.work_id,
            "title": book.edition.title,
            "isbn10": book.edition.isbn10,
            "isbn13": book.edition.isbn13,
            "publisher": book.edition.publisher,
            "publish_date": book.edition.publish_date,
            "page_count": book.edition.page_count,
            "cover_url": book.edition.cover_url,
            "source": book.edition.source,
            "source_id": book.edition.source_id,
            "created_at": book.edition.created_at,
            "updated_at": book.edition.updated_at,
        }
        if book.edition.work:
            work_data = {
                "id": book.edition.work.id,
                "title": book.edition.work.title,
                "subtitle": book.edition.work.subtitle,
                "original_title": book.edition.work.original_title,
                "description": book.edition.work.description,
                "language": book.edition.work.language,
                "created_at": book.edition.work.created_at,
                "updated_at": book.edition.work.updated_at,
            }

    return BookDetailResponse(
        id=book.id,
        edition_id=book.edition_id,
        status=book.status,
        owner=book.owner,
        notes=book.notes,
        confidence=book.confidence,
        created_at=book.created_at,
        updated_at=book.updated_at,
        edition=edition_data,
        work=work_data,
    )


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """删除图书"""
    stmt = select(Book).where(Book.id == book_id)
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    await db.delete(book)
    await db.commit()

    return None


# ========== Import Routes ==========

from app.schemas.schemas import BookImportRequest, BookImportResponse
from app.models.models import Tag, ShelfPosition

# 合法的 Metadata Provider 列表
VALID_METADATA_SOURCES = {"google_books", "open_library"}


@router.post("/import", response_model=BookImportResponse, status_code=status.HTTP_201_CREATED)
async def import_book(
    import_data: BookImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    从 Metadata Candidate 导入图书

    处理逻辑：
    1. 验证 candidate 来源是否合法
    2. 根据 source + source_id 检查是否已存在 Edition
    3. 根据 ISBN 检查是否已存在 Edition
    4. 根据 title + authors 检查是否已存在 Work
    5. 复用或创建 Work、Edition、Book
    """
    candidate = import_data.candidate

    # 1. 验证来源
    if candidate.source not in VALID_METADATA_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid metadata source: {candidate.source}. Valid sources: {VALID_METADATA_SOURCES}"
        )

    work_id: Optional[int] = None
    edition_id: Optional[int] = None
    book_id: Optional[int] = None
    is_new_work = False
    is_new_edition = False
    is_new_book = False

    try:
        # 2. 尝试根据 source + source_id 查找已有 Edition
        edition = await _find_edition_by_source(
            db, candidate.source, candidate.source_id
        )

        # 3. 如果没找到，尝试根据 ISBN 查找
        if not edition and (candidate.isbn13 or candidate.isbn10):
            edition = await _find_edition_by_isbn(
                db, candidate.isbn13, candidate.isbn10
            )

        # 4. 处理 Edition
        if edition:
            edition_id = edition.id
            work_id = edition.work_id
        else:
            is_new_edition = True

            # 5. 尝试查找已有 Work
            work = await _find_work_by_title(db, candidate.title)

            if work:
                work_id = work.id
            else:
                is_new_work = True
                work = Work(
                    title=candidate.title,
                    subtitle=candidate.subtitle,
                    language=candidate.language or "zh",
                    description=candidate.description,
                )
                db.add(work)
                await db.flush()
                work_id = work.id

            # 创建新 Edition
            edition = Edition(
                work_id=work_id,
                title=candidate.title,
                isbn10=candidate.isbn10,
                isbn13=candidate.isbn13,
                publisher=candidate.publisher,
                publish_date=candidate.publish_date,
                page_count=candidate.page_count,
                cover_url=candidate.cover_url,
                source=candidate.source,
                source_id=candidate.source_id,
            )
            db.add(edition)
            await db.flush()
            edition_id = edition.id

        # 6. 检查是否已存在相同的 Book
        existing_book = await _find_existing_book(db, edition_id)

        if existing_book:
            book_id = existing_book.id
            is_new_book = False
        else:
            is_new_book = True
            book = Book(
                edition_id=edition_id,
                status="available",
                owner=import_data.owner,
                notes=import_data.notes,
                confidence=1.0,
            )
            db.add(book)
            await db.flush()
            book_id = book.id

            # 7. 处理书架位置
            if import_data.shelf_id:
                shelf_position = ShelfPosition(
                    book_id=book_id,
                    shelf_id=import_data.shelf_id,
                    position_x=0.0,
                )
                db.add(shelf_position)

            # 8. 处理标签
            if import_data.tags:
                await _add_tags_to_book(db, book, import_data.tags)

        await db.commit()

        return BookImportResponse(
            success=True,
            book_id=book_id,
            work_id=work_id,
            edition_id=edition_id,
            is_new_work=is_new_work,
            is_new_edition=is_new_edition,
            is_new_book=is_new_book,
            message=_build_import_message(is_new_work, is_new_edition, is_new_book),
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


async def _find_edition_by_source(
    db: AsyncSession, source: str, source_id: str
) -> Optional[Edition]:
    """根据 source + source_id 查找 Edition"""
    if not source or not source_id:
        return None

    stmt = select(Edition).where(
        Edition.source == source,
        Edition.source_id == source_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _find_edition_by_isbn(
    db: AsyncSession, isbn13: Optional[str], isbn10: Optional[str]
) -> Optional[Edition]:
    """根据 ISBN 查找 Edition"""
    if isbn13:
        stmt = select(Edition).where(Edition.isbn13 == isbn13)
        result = await db.execute(stmt)
        edition = result.scalar_one_or_none()
        if edition:
            return edition

    if isbn10:
        stmt = select(Edition).where(Edition.isbn10 == isbn10)
        result = await db.execute(stmt)
        edition = result.scalar_one_or_none()
        if edition:
            return edition

    return None


async def _find_work_by_title(
    db: AsyncSession, title: str
) -> Optional[Work]:
    """根据 title 查找 Work"""
    stmt = select(Work).where(Work.title == title)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _find_existing_book(
    db: AsyncSession, edition_id: int
) -> Optional[Book]:
    """检查是否已存在相同的 Book"""
    stmt = select(Book).where(Book.edition_id == edition_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _add_tags_to_book(
    db: AsyncSession, book: Book, tag_names: list[str]
):
    """为 Book 添加标签"""
    for tag_name in tag_names:
        tag_name = tag_name.strip()
        if not tag_name:
            continue

        stmt = select(Tag).where(Tag.name == tag_name)
        result = await db.execute(stmt)
        tag = result.scalar_one_or_none()

        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            await db.flush()

        if tag not in book.tags:
            book.tags.append(tag)


def _build_import_message(
    is_new_work: bool, is_new_edition: bool, is_new_book: bool
) -> str:
    """构建导入结果消息"""
    parts = []
    if is_new_work:
        parts.append("创建新 Work")
    if is_new_edition:
        parts.append("创建新 Edition")
    if is_new_book:
        parts.append("创建新 Book")

    if parts:
        return "; ".join(parts)
    return "复用已有数据"
