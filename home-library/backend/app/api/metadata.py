"""
Metadata API

图书元数据查询 API，支持 ISBN、书名、作者搜索
"""
from fastapi import APIRouter, HTTPException, Query, status
from app.services.metadata import MetadataService, MetadataSearchResult, ISBNLookupResult

router = APIRouter(prefix="/metadata", tags=["metadata"])

# 全局 MetadataService 实例
_metadata_service: MetadataService | None = None


def get_metadata_service() -> MetadataService:
    """获取或创建 MetadataService 实例（单例模式）"""
    global _metadata_service
    if _metadata_service is None:
        _metadata_service = MetadataService()
    return _metadata_service


@router.get("/search", response_model=MetadataSearchResult)
async def search_metadata(
    q: str = Query(..., min_length=1, description="搜索查询（书名或 ISBN）"),
    max_results: int = Query(10, ge=1, le=40, description="最大返回结果数"),
    author: str | None = Query(None, description="作者名（可选）"),
):
    """
    搜索图书元数据

    支持以下查询方式：
    - ISBN: 10 或 13 位数字（自动检测）
    - 书名: 任意书名关键词
    - 作者+书名: 提供 author 参数和 q 参数

    系统会同时查询多个 Provider（Google Books、Open Library），
    自动去重并按来源聚合结果。

    Examples:
        - /api/metadata/search?q=三体
        - /api/metadata/search?q=9787536692930
        - /api/metadata/search?q=三体&author=刘慈欣
    """
    service = get_metadata_service()

    try:
        if author:
            # 作者 + 书名搜索
            result = await service.search_by_author_title(
                author=author,
                title=q,
                max_results=max_results,
            )
        else:
            # 通用搜索（自动检测 ISBN 或书名）
            result = await service.search(query=q, max_results=max_results)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Metadata service unavailable: {str(e)}",
        )


@router.get("/isbn/{isbn}", response_model=ISBNLookupResult)
async def search_by_isbn(isbn: str):
    """
    通过 ISBN 查询图书元数据

    Args:
        isbn: ISBN-10 或 ISBN-13（支持带横杠格式）

    Returns:
        ISBNLookupResult，包含找到的元数据或 not found 状态

    Examples:
        - /api/metadata/isbn/9787536692930
        - /api/metadata/isbn/978-7-5366-9293-0
    """
    service = get_metadata_service()

    try:
        result = await service.search_by_isbn(isbn)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Metadata service unavailable: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """
    检查 Metadata Service 健康状态

    返回所有 Provider 的健康状态，包括响应时间和可用性。
    """
    service = get_metadata_service()

    try:
        health = await service.health_check()
        return {
            "status": "healthy" if any(h.available for h in health) else "degraded",
            "providers": health,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "providers": [],
        }
