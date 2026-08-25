/**
 * 通用类型定义
 */

// API 响应基础类型
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

// 分页请求参数
export interface PaginationParams {
  skip?: number;
  limit?: number;
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// Health 检查响应
export interface HealthResponse {
  status: string;
  version: string;
}
