import { apiClient } from "../../../lib/api-client";
import {
  AdminAuditLog,
  AdminGame,
  AdminGameCreate,
  AdminGameUpdate,
  AdminIngestionJob,
  AdminIngestionJobCreate,
  AdminMetadataRefreshResponse,
  AdminModel,
  AdminModelActivateResponse,
  AdminOperationalErrors,
  AdminPipelineRun,
} from "../../../types/admin";

export const adminClient = {
  // Catalog Operations
  async listGames(params?: { limit?: number; offset?: number }): Promise<AdminGame[]> {
    return apiClient<AdminGame[]>("/admin/games", { params });
  },

  async createGame(data: AdminGameCreate): Promise<AdminGame> {
    return apiClient<AdminGame>("/admin/games", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateGame(gameId: string, data: AdminGameUpdate): Promise<AdminGame> {
    return apiClient<AdminGame>(`/admin/games/${encodeURIComponent(gameId)}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async refreshMetadata(gameId: string): Promise<AdminMetadataRefreshResponse> {
    return apiClient<AdminMetadataRefreshResponse>(
      `/admin/games/${encodeURIComponent(gameId)}/metadata-refresh`,
      { method: "POST" }
    );
  },

  // Ingestion Operations
  async queueIngestionJob(
    gameId: string,
    data: AdminIngestionJobCreate
  ): Promise<AdminIngestionJob> {
    return apiClient<AdminIngestionJob>(
      `/admin/games/${encodeURIComponent(gameId)}/ingestion-jobs`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async listIngestionJobs(params?: {
    game_id?: string;
    job_type?: string;
    status?: string;
    limit?: number;
  }): Promise<AdminIngestionJob[]> {
    return apiClient<AdminIngestionJob[]>("/admin/ingestion-jobs", { params });
  },

  async getIngestionJob(jobId: string): Promise<AdminIngestionJob> {
    return apiClient<AdminIngestionJob>(`/admin/ingestion-jobs/${encodeURIComponent(jobId)}`);
  },

  async cancelIngestionJob(jobId: string): Promise<AdminIngestionJob> {
    return apiClient<AdminIngestionJob>(
      `/admin/ingestion-jobs/${encodeURIComponent(jobId)}/cancel`,
      { method: "POST" }
    );
  },

  async retryIngestionJob(jobId: string): Promise<AdminIngestionJob> {
    return apiClient<AdminIngestionJob>(
      `/admin/ingestion-jobs/${encodeURIComponent(jobId)}/retry`,
      { method: "POST" }
    );
  },

  // Pipeline Runs
  async listPipelineRuns(params?: {
    pipeline_type?: string;
    limit?: number;
  }): Promise<AdminPipelineRun[]> {
    return apiClient<AdminPipelineRun[]>("/admin/pipeline-runs", { params });
  },

  async getPipelineRun(runId: string): Promise<AdminPipelineRun> {
    return apiClient<AdminPipelineRun>(`/admin/pipeline-runs/${encodeURIComponent(runId)}`);
  },

  // Models
  async listModels(): Promise<AdminModel[]> {
    return apiClient<AdminModel[]>("/admin/models");
  },

  async activateModel(modelId: string): Promise<AdminModelActivateResponse> {
    return apiClient<AdminModelActivateResponse>(
      `/admin/models/${encodeURIComponent(modelId)}/activate`,
      { method: "POST" }
    );
  },

  // Audit Logs & Operational Errors
  async listAuditLogs(params?: {
    limit?: number;
    action?: string;
    resource_type?: string;
  }): Promise<AdminAuditLog[]> {
    return apiClient<AdminAuditLog[]>("/admin/audit-logs", { params });
  },

  async getOperationalErrors(limit = 50): Promise<AdminOperationalErrors> {
    return apiClient<AdminOperationalErrors>("/admin/operational-errors", {
      params: { limit },
    });
  },
};

