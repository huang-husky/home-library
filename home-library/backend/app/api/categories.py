"""
分类管理 API
Phase 9: Classification System
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Category, Book
from app.schemas.schemas import (
    CategoryResponse,
    CategoryTreeResponse,
    CategoryPathResponse,
    CategoryCreate,
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    level: Optional[int] = None,
    parent_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """列出所有分类"""
    query = select(Category)

    if level:
        query = query.where(Category.level == level)

    if parent_code:
        # 先找到父分类
        parent_result = await db.execute(
            select(Category).where(Category.code == parent_code)
        )
        parent = parent_result.scalar_one_or_none()
        if parent:
            query = query.where(Category.parent_id == parent.id)

    query = query.order_by(Category.code)
    result = await db.execute(query)
    categories = result.scalars().all()

    return categories


@router.get("/tree", response_model=List[CategoryTreeResponse])
async def get_category_tree(
    max_level: int = 3,
    db: AsyncSession = Depends(get_db),
):
    """获取分类树"""
    # 获取所有分类
    result = await db.execute(
        select(Category).where(Category.level <= max_level).order_by(Category.code)
    )
    categories = result.scalars().all()

    # 构建树
    category_map = {c.id: CategoryTreeResponse(**{
        "id": c.id,
        "code": c.code,
        "name": c.name,
        "description": c.description,
        "parent_id": c.parent_id,
        "level": c.level,
        "created_at": c.created_at,
        "children": [],
        "book_count": 0,
    }) for c in categories}

    # 统计每个分类的图书数量
    for cat_id in category_map.keys():
        count_result = await db.execute(
            select(func.count(Book.id)).where(Book.category_id == cat_id)
        )
        category_map[cat_id].book_count = count_result.scalar() or 0

    # 构建树结构
    roots = []
    for cat in categories:
        node = category_map[cat.id]
        if cat.parent_id and cat.parent_id in category_map:
            category_map[cat.parent_id].children.append(node)
        else:
            roots.append(node)

    return roots


@router.get("/{code}", response_model=CategoryResponse)
async def get_category(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """获取单个分类详情"""
    result = await db.execute(
        select(Category).where(Category.code == code)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with code '{code}' not found"
        )

    return category


@router.get("/{code}/children", response_model=List[CategoryResponse])
async def get_category_children(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """获取分类的子分类"""
    # 先找到父分类
    result = await db.execute(
        select(Category).where(Category.code == code)
    )
    parent = result.scalar_one_or_none()

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with code '{code}' not found"
        )

    # 获取子分类
    result = await db.execute(
        select(Category)
        .where(Category.parent_id == parent.id)
        .order_by(Category.code)
    )
    children = result.scalars().all()

    return children


@router.get("/{code}/path", response_model=List[CategoryPathResponse])
async def get_category_path(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """获取分类的完整路径（从根到当前）"""
    result = await db.execute(
        select(Category).where(Category.code == code)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with code '{code}' not found"
        )

    # 构建路径
    path = []
    current = category
    while current:
        path.append(CategoryPathResponse(
            id=current.id,
            code=current.code,
            name=current.name,
            level=current.level,
        ))
        if current.parent_id:
            result = await db.execute(
                select(Category).where(Category.id == current.parent_id)
            )
            current = result.scalar_one_or_none()
        else:
            current = None

    # 反转，使根在前
    return list(reversed(path))


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新分类（用于导入中图法数据）"""
    # 检查 code 是否已存在
    existing = await db.execute(
        select(Category).where(Category.code == data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with code '{data.code}' already exists"
        )

    # 验证父分类
    if data.parent_id:
        parent_result = await db.execute(
            select(Category).where(Category.id == data.parent_id)
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent category with id {data.parent_id} not found"
            )

    category = Category(
        code=data.code,
        name=data.name,
        description=data.description,
        parent_id=data.parent_id,
        level=data.level,
    )

    db.add(category)
    await db.commit()
    await db.refresh(category)

    return category


@router.get("/{code}/books", response_model=dict)
async def get_category_books(
    code: str,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """获取分类下的图书（包括子分类）"""
    # 获取分类
    result = await db.execute(
        select(Category).where(Category.code == code)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with code '{code}' not found"
        )

    # 获取该分类及其所有子分类的 ID
    category_ids = [category.id]

    async def get_children_ids(parent_id: int):
        result = await db.execute(
            select(Category.id).where(Category.parent_id == parent_id)
        )
        children = result.scalars().all()
        for child_id in children:
            category_ids.append(child_id)
            await get_children_ids(child_id)

    await get_children_ids(category.id)

    # 查询图书
    from app.schemas.schemas import BookDetailResponse
    from app.models.models import Edition, Work

    result = await db.execute(
        select(Book, Edition, Work)
        .join(Edition, Book.edition_id == Edition.id, isouter=True)
        .join(Work, Edition.work_id == Work.id, isouter=True)
        .where(Book.category_id.in_(category_ids))
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()

    books = []
    for book, edition, work in rows:
        book_data = {
            "id": book.id,
            "edition_id": book.edition_id,
            "status": book.status,
            "owner": book.owner,
            "notes": book.notes,
            "confidence": book.confidence,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
            "work": work,
            "edition": edition,
        }
        books.append(book_data)

    # 统计总数
    count_result = await db.execute(
        select(func.count(Book.id)).where(Book.category_id.in_(category_ids))
    )
    total = count_result.scalar() or 0

    return {
        "category": {
            "id": category.id,
            "code": category.code,
            "name": category.name,
        },
        "total": total,
        "books": books,
    }
