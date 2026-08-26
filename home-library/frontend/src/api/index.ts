import axios, { AxiosInstance, AxiosError } from 'axios';

// API 基础 URL 配置
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// 创建 axios 实例
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const data = error.response?.data as { detail?: string } | undefined;
    const message = data?.detail || error.message || '请求失败';
    console.error('[API Error]', message);
    return Promise.reject(error);
  }
);

export default api;

// ===== Health API =====
export const healthApi = {
  check: () => api.get('/health'),
};

// ===== Books API =====
export interface Book {
  id: number;
  edition_id?: number;
  status: string;
  owner?: string;
  notes?: string;
  confidence?: number;
  created_at: string;
  updated_at: string;
  work?: {
    id: number;
    title: string;
    subtitle?: string;
    description?: string;
  };
  edition?: {
    id: number;
    title: string;
    isbn13?: string;
    publisher?: string;
    cover_url?: string;
  };
}

export interface BookListResponse {
  total: number;
  items: Book[];
}

export interface BookCreate {
  title: string;
  subtitle?: string;
  isbn13?: string;
  publisher?: string;
  status?: string;
  owner?: string;
  notes?: string;
}

export interface BookUpdate {
  status?: string;
  owner?: string;
  notes?: string;
}

export const booksApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get<BookListResponse>('/books', { params }),

  search: (q: string, params?: { skip?: number; limit?: number }) =>
    api.get<BookListResponse>('/books/search', { params: { q, ...params } }),

  get: (id: number) =>
    api.get<Book>(`/books/${id}`),

  create: (data: BookCreate) =>
    api.post<Book>('/books', data),

  update: (id: number, data: BookUpdate) =>
    api.put<Book>(`/books/${id}`, data),

  delete: (id: number) =>
    api.delete(`/books/${id}`),
};

// ===== Bookshelves API =====
export interface Bookshelf {
  id: number;
  name: string;
  location?: string;
  width?: number;
  height?: number;
  description?: string;
  created_at: string;
  updated_at: string;
  shelf_count?: number;
}

export interface Shelf {
  id: number;
  bookshelf_id: number;
  level: number;
  height?: number;
  created_at: string;
  updated_at: string;
  book_count?: number;
}

export const bookshelvesApi = {
  list: () =>
    api.get<Bookshelf[]>('/bookshelves'),

  get: (id: number) =>
    api.get<Bookshelf>(`/bookshelves/${id}`),

  create: (data: { name: string; location?: string; width?: number; height?: number; description?: string }) =>
    api.post<Bookshelf>('/bookshelves', data),

  update: (id: number, data: Partial<Bookshelf>) =>
    api.put<Bookshelf>(`/bookshelves/${id}`, data),

  delete: (id: number) =>
    api.delete(`/bookshelves/${id}`),

  // Shelves
  listShelves: (bookshelfId: number) =>
    api.get<Shelf[]>(`/bookshelves/${bookshelfId}/shelves`),

  createShelf: (bookshelfId: number, data: { level: number; height?: number }) =>
    api.post<Shelf>(`/bookshelves/${bookshelfId}/shelves`, data),

  updateShelf: (id: number, data: Partial<Shelf>) =>
    api.put<Shelf>(`/shelves/${id}`, data),

  deleteShelf: (id: number) =>
    api.delete(`/shelves/${id}`),
};

// ===== Metadata API =====
export interface BookMetadataCandidate {
  source: string;
  source_id: string;
  title: string;
  subtitle?: string;
  authors: string[];
  publisher?: string;
  publish_date?: string;
  publish_year?: number;
  isbn10?: string;
  isbn13?: string;
  language?: string;
  page_count?: number;
  cover_url?: string;
  description?: string;
}

export interface MetadataSearchResult {
  query: string;
  candidates: BookMetadataCandidate[];
  total_found: number;
  sources: string[];
}

export const metadataApi = {
  search: (q: string, maxResults?: number) =>
    api.get<MetadataSearchResult>('/metadata/search', {
      params: { q, max_results: maxResults || 10 }
    }),

  searchByIsbn: (isbn: string) =>
    api.get<{ isbn: string; found: boolean; candidate?: BookMetadataCandidate; source?: string }>(
      `/metadata/isbn/${isbn}`
    ),
};

// ===== Book Import API =====
export interface BookImportRequest {
  candidate: BookMetadataCandidate;
  bookshelf_id?: number;
  shelf_id?: number;
  category_id?: number;
  tags?: string[];
  owner?: string;
  notes?: string;
}

export interface BookImportResponse {
  success: boolean;
  book_id: number;
  work_id: number;
  edition_id: number;
  is_new_work: boolean;
  is_new_edition: boolean;
  is_new_book: boolean;
  message?: string;
}

export const bookImportApi = {
  import: (data: BookImportRequest) =>
    api.post<BookImportResponse>('/books/import', data),
};

// ===== Scan API =====
export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ScanItem {
  id: number;
  detected_text: string;
  confidence: number;
  bbox: BoundingBox | null;
  status: 'detected' | 'searching' | 'matched' | 'needs_review' | 'confirmed' | 'imported' | 'failed' | 'skipped';
  matched_book_id?: number;
  created_at: string;
}

export interface Scan {
  id: number;
  bookshelf_id?: number;
  shelf_id?: number;
  image_path: string;
  scanned_at: string;
  item_count: number;
}

export interface ScanDetail extends Scan {
  items: ScanItem[];
}

export interface ScanCreateResponse {
  scan_id: number;
  detected_count: number;
  items: ScanItem[];
  message: string;
}

export interface ScanStats {
  total_items: number;
  high_confidence: number;
  medium_confidence: number;
  low_confidence: number;
  pending_count: number;
  confirmed_count: number;
  rejected_count: number;
}

export const scansApi = {
  // 上传图片并识别
  upload: (file: File, bookshelfId?: number, shelfId?: number, preprocess = true) => {
    const formData = new FormData();
    formData.append('file', file);
    if (bookshelfId) formData.append('bookshelf_id', bookshelfId.toString());
    if (shelfId) formData.append('shelf_id', shelfId.toString());
    formData.append('preprocess', preprocess.toString());

    return api.post<ScanCreateResponse>('/scans/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // 列出扫描记录
  list: (params?: { bookshelf_id?: number; shelf_id?: number; limit?: number; offset?: number }) =>
    api.get<Scan[]>('/scans', { params }),

  // 获取扫描详情
  get: (id: number) =>
    api.get<ScanDetail>(`/scans/${id}`),

  // 获取扫描项
  getItems: (scanId: number, status?: string) =>
    api.get<ScanItem[]>(`/scans/${scanId}/items`, { params: { status } }),

  // 更新扫描项
  updateItem: (itemId: number, data: Partial<ScanItem>) =>
    api.patch<ScanItem>(`/scans/items/${itemId}`, data),

  // 删除扫描项
  deleteItem: (itemId: number) =>
    api.delete(`/scans/items/${itemId}`),

  // 添加扫描项（手动补录）
  addItem: (scanId: number, data: { text: string; bbox: BoundingBox; confidence?: number }) =>
    api.post<ScanItem>(`/scans/${scanId}/items`, null, {
      params: {
        text: data.text,
        confidence: data.confidence || 1.0,
        bbox_x: data.bbox.x,
        bbox_y: data.bbox.y,
        bbox_width: data.bbox.width,
        bbox_height: data.bbox.height,
      },
    }),

  // 获取统计
  getStats: (scanId: number) =>
    api.get<ScanStats>(`/scans/${scanId}/stats`),

  // 删除扫描
  delete: (id: number, deleteImage = true) =>
    api.delete(`/scans/${id}`, { params: { delete_image: deleteImage } }),
};

// ===== AI Import API =====
export interface ImportCandidate {
  source: string;
  source_id: string;
  title: string;
  subtitle?: string;
  authors: string[];
  publisher?: string;
  publish_year?: number;
  isbn13?: string;
  isbn10?: string;
  cover_url?: string;
  description?: string;
}

export interface ImportItem {
  id: number;
  detected_text: string;
  confidence: number;
  bbox: BoundingBox | null;
  status: 'detected' | 'searching' | 'matched' | 'needs_review' | 'confirmed' | 'imported' | 'failed' | 'skipped';
  candidates: ImportCandidate[];
  candidates_count: number;
  matched_candidate_index: number | null;
  match_confidence: number | null;
  search_error?: string;
  match_error?: string;
  imported_book_id?: number;
}

export interface ImportItemsResponse {
  scan_id: number;
  image_path: string;
  items: ImportItem[];
  stats: {
    total: number;
    detected: number;
    searching: number;
    matched: number;
    confirmed: number;
    needs_review: number;
    imported: number;
    failed: number;
    skipped: number;
  };
}

export interface MatchResult {
  item_id: number;
  status: string;
  candidates_count: number;
  match_confidence: number | null;
}

export interface MatchSummary {
  scan_id: number;
  processed: number;
  summary: {
    matched: number;
    confirmed: number;
    needs_review: number;
    failed: number;
  };
  results: MatchResult[];
}

export interface ImportResult {
  item_id: number;
  status: string;
  book_id?: number;
  is_new_work?: boolean;
  is_new_edition?: boolean;
}

export interface BatchImportResponse {
  scan_id: number;
  total: number;
  imported: number;
  failed: number;
  imported_items: { item_id: number; book_id: number }[];
  failed_items: { item_id: number; error: string }[];
}

export const aiImportApi = {
  // 执行匹配
  match: (scanId: number, autoThreshold = 0.85) =>
    api.post<MatchSummary>(`/ai-import/scan/${scanId}/match`, null, {
      params: { auto_threshold: autoThreshold }
    }),

  // 获取导入项列表
  getItems: (scanId: number, status?: string) =>
    api.get<ImportItemsResponse>(`/ai-import/scan/${scanId}/items`, { params: { status } }),

  // 选择候选版本
  selectCandidate: (itemId: number, candidateIndex: number) =>
    api.post<{ item_id: number; status: string; selected_candidate: ImportCandidate }>(
      `/ai-import/items/${itemId}/select-candidate`,
      null,
      { params: { candidate_index: candidateIndex } }
    ),

  // 跳过项目
  skip: (itemId: number, reason?: string) =>
    api.post<{ item_id: number; status: string }>(
      `/ai-import/items/${itemId}/skip`,
      null,
      { params: { reason } }
    ),

  // 导入单个项目
  import: (itemId: number, bookshelfId?: number, shelfId?: number) =>
    api.post<ImportResult>(
      `/ai-import/items/${itemId}/import`,
      null,
      { params: { bookshelf_id: bookshelfId, shelf_id: shelfId } }
    ),

  // 批量导入
  batchImport: (scanId: number, bookshelfId?: number, shelfId?: number, onlyConfirmed = true) =>
    api.post<BatchImportResponse>(
      `/ai-import/scan/${scanId}/batch-import`,
      null,
      { params: { bookshelf_id: bookshelfId, shelf_id: shelfId, only_confirmed: onlyConfirmed } }
    ),

  // 自动确认高置信度
  autoConfirm: (scanId: number, threshold = 0.85) =>
    api.post<{ scan_id: number; confirmed_count: number; threshold: number }>(
      `/ai-import/scan/${scanId}/auto-confirm`,
      null,
      { params: { threshold } }
    ),

  // 重新匹配
  retry: (itemId: number) =>
    api.post<{ item_id: number; status: string; message: string }>(
      `/ai-import/items/${itemId}/retry`
    ),
};

// ===== Categories API =====

// ===== Categories API =====
export interface Category {
  id: number;
  code: string;
  name: string;
  description?: string;
  parent_id?: number;
  level: number;
  created_at: string;
}

export interface TagResponse {
  id: number;
  name: string;
  created_at: string;
}

export interface CategoryTree extends Category {
  children: CategoryTree[];
  book_count: number;
}

export interface CategoryPath {
  id: number;
  code: string;
  name: string;
  level: number;
}

export interface ClassificationSuggestion {
  category_code: string;
  category_name: string;
  confidence: number;
  reason: string;
}

export interface ClassificationResult {
  success: boolean;
  suggestions: ClassificationSuggestion[];
  selected_code?: string;
  selected_name?: string;
  requires_confirmation: boolean;
  message?: string;
}

export const categoriesApi = {
  list: (params?: { level?: number; parent_code?: string }) =>
    api.get<Category[]>('/categories', { params }),
  getTree: (maxLevel = 3) =>
    api.get<CategoryTree[]>('/categories/tree', { params: { max_level: maxLevel } }),
  get: (code: string) =>
    api.get<Category>(`/categories/${code}`),
  getChildren: (code: string) =>
    api.get<Category[]>(`/categories/${code}/children`),
  getPath: (code: string) =>
    api.get<CategoryPath[]>(`/categories/${code}/path`),
  getBooks: (code: string, params?: { limit?: number; offset?: number }) =>
    api.get<{ category: Category; total: number; books: Book[] }>(`/categories/${code}/books`, { params }),
};

export const bookClassificationApi = {
  getCategory: (bookId: number) =>
    api.get<{ book_id: number; category: Category | null; path: CategoryPath[] }>(`/books/${bookId}/category`),
  updateCategory: (bookId: number, data: { category_id?: number; category_code?: string; confirmed?: boolean }) =>
    api.put(`/books/${bookId}/category`, data),
  removeCategory: (bookId: number) =>
    api.delete(`/books/${bookId}/category`),
  classify: (bookId: number) =>
    api.post<ClassificationResult>(`/books/${bookId}/classify`),
  suggestClassification: (data: { title: string; subtitle?: string; authors?: string[]; publisher?: string; description?: string }) =>
    api.post<ClassificationResult>('/books/classify-suggest', data),
  getTags: (bookId: number) =>
    api.get<TagResponse[]>(`/books/${bookId}/tags`),
  updateTags: (bookId: number, data: { add_tags?: string[]; remove_tag_ids?: number[] }) =>
    api.put(`/books/${bookId}/tags`, data),
  addTag: (bookId: number, tagName: string) =>
    api.post(`/books/${bookId}/tags/${tagName}`),
  removeTag: (bookId: number, tagId: number) =>
    api.delete(`/books/${bookId}/tags/${tagId}`),
  getPopularTags: (limit = 20) =>
    api.get<{ id: number; name: string; book_count: number }[]>('/books/tags/popular', { params: { limit } }),
};

// ===== Shelf Position API =====
export interface ShelfPosition {
  id: number;
  book_id: number;
  shelf_id: number;
  position_x: number;
  position_order?: number;
  confidence: number;
  source: string;
  is_current: boolean;
  bbox?: BoundingBox;
  created_at: string;
  updated_at: string;
}

export interface ShelfPositionCreate {
  book_id: number;
  shelf_id: number;
  position_x: number;
  position_order?: number;
  confidence?: number;
  source?: string;
  scan_id?: number;
  scan_item_id?: number;
  bbox?: BoundingBox;
}

export interface ShelfVisualization {
  shelf_id: number;
  bookshelf_name: string;
  level: number;
  latest_scan_id?: number;
  scan_image_path?: string;
  books: {
    book_id: number;
    position_id: number;
    position_x: number;
    position_order?: number;
    confidence: number;
    bbox?: BoundingBox;
  }[];
}

export interface BookshelfVisualization {
  bookshelf_id: number;
  bookshelf_name: string;
  shelves: {
    shelf_id: number;
    level: number;
    latest_scan_id?: number;
    scan_image_path?: string;
    book_count: number;
    books: {
      book_id: number;
      position_id: number;
      position_x: number;
      position_order?: number;
      confidence: number;
      bbox?: BoundingBox;
    }[];
  }[];
}

export const shelfPositionApi = {
  // 获取图书位置
  getBookPositions: (bookId: number, currentOnly = true) =>
    api.get<ShelfPosition[]>(`/shelf-positions/book/${bookId}`, { params: { current_only: currentOnly } }),
  
  // 获取书架上所有位置
  getShelfPositions: (shelfId: number) =>
    api.get<ShelfPosition[]>(`/shelf-positions/shelf/${shelfId}`),
  
  // 创建位置
  create: (data: ShelfPositionCreate) =>
    api.post<ShelfPosition>('/shelf-positions', data),
  
  // 更新位置
  update: (positionId: number, data: Partial<ShelfPositionCreate>) =>
    api.put<ShelfPosition>(`/shelf-positions/${positionId}`, data),
  
  // 删除位置
  delete: (positionId: number) =>
    api.delete(`/shelf-positions/${positionId}`),
  
  // 从扫描创建位置
  createFromScan: (scanItemId: number, bookId: number) =>
    api.post<ShelfPosition>(`/shelf-positions/from-scan/${scanItemId}`, null, { params: { book_id: bookId } }),
  
  // 获取书架可视化
  getShelfVisualization: (shelfId: number) =>
    api.get<ShelfVisualization>(`/shelf-positions/visualization/shelf/${shelfId}`),
  
  // 获取书柜可视化
  getBookshelfVisualization: (bookshelfId: number) =>
    api.get<BookshelfVisualization>(`/shelf-positions/visualization/bookshelf/${bookshelfId}`),
};
