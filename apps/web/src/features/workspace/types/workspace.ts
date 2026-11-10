import { PaginationMeta } from "../../../types/api";

export type ProjectVisibility = "private" | "shared";
export type ProjectRole = "owner" | "editor" | "viewer";

export interface ResearchProject {
  id: string;
  owner_user_id: string;
  name: string;
  description?: string | null;
  visibility: ProjectVisibility;
  status: string;
  current_user_role?: ProjectRole | string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  items: ResearchProject[];
  pagination?: PaginationMeta | null;
}

export interface ProjectGameItem {
  project_id: string;
  game_id: string;
  added_at: string;
  title?: string;
  header_image_url?: string | null;
}

export interface SavedAnalysis {
  id: string;
  project_id: string;
  name: string;
  description?: string | null;
  analysis_type: string;
  query_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AnalysisSnapshot {
  id: string;
  saved_analysis_id: string;
  name: string;
  description?: string | null;
  configuration_snapshot: Record<string, unknown>;
  result_summary: Record<string, unknown>;
  data_cutoff_at: string;
  created_at: string;
}

export interface ProjectMemberItem {
  project_id: string;
  user_id: string;
  project_role: ProjectRole;
  joined_at: string;
  email?: string | null;
  display_name?: string | null;
}

export interface ProjectCreatePayload {
  name: string;
  description?: string;
  visibility?: ProjectVisibility;
}

export interface ProjectUpdatePayload {
  name?: string;
  description?: string;
  visibility?: ProjectVisibility;
}

export interface SavedAnalysisCreatePayload {
  name: string;
  description?: string;
  analysis_type: string;
  query_config: Record<string, unknown>;
}

export interface SavedAnalysisUpdatePayload {
  name?: string;
  description?: string;
  query_config?: Record<string, unknown>;
}

export interface SnapshotCreatePayload {
  name: string;
  description?: string;
}

export interface ProjectAddMemberPayload {
  email?: string;
  user_id?: string;
  project_role: "editor" | "viewer";
}

