export type CatalogStatus = "pending" | "indexed" | "failed" | "disabled";

export interface AdminGame {
  id: string;
  steam_app_id: number;
  name: string;
  catalog_status: CatalogStatus | string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminGameCreate {
  steam_app_id: number;
  name: string;
  short_description?: string;
  genres?: string[];
  release_date?: string;
  is_free?: boolean;
  catalog_status?: CatalogStatus;
}

export interface AdminGameUpdate {
  name?: string;
  short_description?: string;
  catalog_status?: CatalogStatus;
  is_active?: boolean;
}

export type IngestionJobStatus =
  | "queued"
  | "running"
  | "retrying"
  | "succeeded"
  | "partial"
  | "failed"
  | "cancelled";

export type IngestionJobType = "historical" | "incremental";

export interface AdminIngestionJob {
  job_id: string;
  game_id: string;
  job_type: IngestionJobType | string;
  status: IngestionJobStatus | string;
  target_reviews: number;
  collected_reviews: number;
  error_code?: string | null;
  error_message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface AdminIngestionJobCreate {
  job_type: IngestionJobType;
  collection_config?: {
    review_type?: string;
    purchase_type?: string;
    languages?: string[];
    overlap_days?: number;
  };
  reason: string;
}

export interface AdminPipelineRun {
  run_id: string;
  pipeline_type: string;
  status: "queued" | "running" | "succeeded" | "failed" | string;
  model_version_snapshot?: string | null;
  input_count: number;
  success_count: number;
  failure_count: number;
  error_summary?: string | null;
  started_at: string;
  finished_at?: string | null;
}

export interface AdminModel {
  id: string;
  model_key: string;
  version: string;
  task: "sentiment" | "aspect_absa" | "topic" | string;
  framework: string;
  is_active: boolean;
  created_at: string;
}

export interface AdminModelActivateResponse {
  model_id: string;
  task: string;
  is_active: boolean;
  message: string;
}

export interface AdminMetadataRefreshResponse {
  game_id: string;
  status: string;
  message: string;
}

export interface AdminAuditLog {
  id: number;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  actor_user_id?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface AdminOperationalErrors {
  failed_ingestion_jobs: AdminIngestionJob[];
  failed_pipeline_runs: AdminPipelineRun[];
  total_failures: number;
}

