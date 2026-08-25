"""
图书服务模块

提供图书导入相关的业务逻辑
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Book, Work, Edition, Tag, ShelfPosition
from app.schemas.schemas import BookImportRequest, BookImportResponse

# 合法的 Metadata Provider 列表
VALID_METADATA_SOURCES = {"google_books", "open_library"}


async def create_book_with_metadata(
    db: AsyncSession,
    import_data: BookImportRequest
) -> BookImportResponse:
    """
    从 Metadata Candidate 导入图书

    处理逻辑：
    1. 验证 candidate 来源是否合法
    2. 根据 source + source_id 检查是否已存在 Edition
    3. 根据 ISBN 检查是否已存在 Edition
    4. 根据 title + authors 检查是否已存在 Work
    5. 复用或创建 Work、Edition、Book
    """
    from fastapi import HTTPException, status

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
