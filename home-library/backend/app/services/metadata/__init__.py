"""
Metadata Service Module

统一的图书元数据服务，支持多 Provider fallback
"""
from .dto import (
    BookMetadataCandidate,
    MetadataSearchResult,
    ISBNLookupResult,
    ProviderHealth,
)
from .provider import MetadataProvider
from .google_books import GoogleBooksProvider
from .open_library import OpenLibraryProvider
from .service import MetadataService

__all__ = [
    # DTOs
    "BookMetadataCandidate",
    "MetadataSearchResult",
    "ISBNLookupResult",
    "ProviderHealth",
    # Provider
    "MetadataProvider",
    "GoogleBooksProvider",
    "OpenLibraryProvider",
    # Service
    "MetadataService",
]
