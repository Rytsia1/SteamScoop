export interface PaginationMeta {
  limit?: number | null;
  next_cursor?: string | null;
  has_more: boolean;
  total_count?: number | null;
}

export interface MetaEnvelope {
  request_id: string;
  timestamp: string;
  pagination?: PaginationMeta | null;
}

export interface ErrorDetail {
  field?: string | null;
  issue: string;
}

export interface ErrorInfo {
  code: string;
  message: string;
  details?: ErrorDetail[] | null;
  request_id?: string | null;
}

export interface ResponseEnvelope<T> {
  data: T | null;
  error: ErrorInfo | null;
  meta: MetaEnvelope;
}

export interface DependencyStatus {
  database: "connected" | "unreachable" | string;
  redis: "connected" | "unreachable" | string;
}

export interface HealthData {
  status: "healthy" | "degraded" | "unhealthy" | string;
  version: string;
  app_env: string;
  timestamp: string;
  dependencies?: DependencyStatus;
}
