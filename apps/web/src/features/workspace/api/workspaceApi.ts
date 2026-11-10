import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient, apiClientWithMeta } from "../../../lib/api-client";
import {
  AnalysisSnapshot,
  ProjectAddMemberPayload,
  ProjectCreatePayload,
  ProjectGameItem,
  ProjectListResponse,
  ProjectMemberItem,
  ProjectUpdatePayload,
  ResearchProject,
  SavedAnalysis,
  SavedAnalysisCreatePayload,
  SavedAnalysisUpdatePayload,
  SnapshotCreatePayload,
} from "../types/workspace";

// Projects API
export async function fetchProjects(limit = 20, cursor?: string): Promise<ProjectListResponse> {
  const result = await apiClientWithMeta<ResearchProject[]>("/projects", {
    params: { limit, cursor },
  });
  return {
    items: result.data,
    pagination: result.meta.pagination,
  };
}

export async function fetchProject(projectId: string): Promise<ResearchProject> {
  return apiClient<ResearchProject>(`/projects/${encodeURIComponent(projectId)}`);
}

export async function createProject(payload: ProjectCreatePayload): Promise<ResearchProject> {
  return apiClient<ResearchProject>("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateProject(
  projectId: string,
  payload: ProjectUpdatePayload
): Promise<ResearchProject> {
  return apiClient<ResearchProject>(`/projects/${encodeURIComponent(projectId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiClient<void>(`/projects/${encodeURIComponent(projectId)}`, {
    method: "DELETE",
  });
}

// Project Games API
export async function fetchProjectGames(projectId: string): Promise<ProjectGameItem[]> {
  return apiClient<ProjectGameItem[]>(`/projects/${encodeURIComponent(projectId)}/games`);
}

export async function addGameToProject(
  projectId: string,
  gameId: string
): Promise<ProjectGameItem> {
  return apiClient<ProjectGameItem>(`/projects/${encodeURIComponent(projectId)}/games`, {
    method: "POST",
    body: JSON.stringify({ game_id: gameId }),
  });
}

export async function removeGameFromProject(
  projectId: string,
  gameId: string
): Promise<void> {
  await apiClient<void>(
    `/projects/${encodeURIComponent(projectId)}/games/${encodeURIComponent(gameId)}`,
    {
      method: "DELETE",
    }
  );
}

// Saved Analyses API
export async function fetchSavedAnalyses(projectId: string): Promise<SavedAnalysis[]> {
  return apiClient<SavedAnalysis[]>(`/projects/${encodeURIComponent(projectId)}/analyses`);
}

export async function fetchSavedAnalysis(
  projectId: string,
  analysisId: string
): Promise<SavedAnalysis> {
  return apiClient<SavedAnalysis>(
    `/projects/${encodeURIComponent(projectId)}/analyses/${encodeURIComponent(analysisId)}`
  );
}

export async function createSavedAnalysis(
  projectId: string,
  payload: SavedAnalysisCreatePayload
): Promise<SavedAnalysis> {
  return apiClient<SavedAnalysis>(`/projects/${encodeURIComponent(projectId)}/analyses`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateSavedAnalysis(
  projectId: string,
  analysisId: string,
  payload: SavedAnalysisUpdatePayload
): Promise<SavedAnalysis> {
  return apiClient<SavedAnalysis>(
    `/projects/${encodeURIComponent(projectId)}/analyses/${encodeURIComponent(analysisId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export async function deleteSavedAnalysis(
  projectId: string,
  analysisId: string
): Promise<void> {
  await apiClient<void>(
    `/projects/${encodeURIComponent(projectId)}/analyses/${encodeURIComponent(analysisId)}`,
    {
      method: "DELETE",
    }
  );
}

// Snapshots API
export async function fetchSnapshots(
  projectId: string,
  analysisId: string
): Promise<AnalysisSnapshot[]> {
  return apiClient<AnalysisSnapshot[]>(
    `/projects/${encodeURIComponent(projectId)}/analyses/${encodeURIComponent(analysisId)}/snapshots`
  );
}

export async function createSnapshot(
  projectId: string,
  analysisId: string,
  payload: SnapshotCreatePayload
): Promise<AnalysisSnapshot> {
  return apiClient<AnalysisSnapshot>(
    `/projects/${encodeURIComponent(projectId)}/analyses/${encodeURIComponent(analysisId)}/snapshots`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

// Project Members API
export async function fetchProjectMembers(projectId: string): Promise<ProjectMemberItem[]> {
  return apiClient<ProjectMemberItem[]>(`/projects/${encodeURIComponent(projectId)}/members`);
}

export async function addProjectMember(
  projectId: string,
  payload: ProjectAddMemberPayload
): Promise<ProjectMemberItem> {
  return apiClient<ProjectMemberItem>(`/projects/${encodeURIComponent(projectId)}/members`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function removeProjectMember(
  projectId: string,
  userId: string
): Promise<void> {
  await apiClient<void>(
    `/projects/${encodeURIComponent(projectId)}/members/${encodeURIComponent(userId)}`,
    {
      method: "DELETE",
    }
  );
}

// React Query Hooks
export function useProjects(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["workspaceProjects"],
    queryFn: () => fetchProjects(),
    enabled: options?.enabled ?? true,
  });
}

export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: ["workspaceProject", projectId],
    queryFn: () => fetchProject(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceProjects"] });
    },
  });
}

export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProjectUpdatePayload) => updateProject(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceProject", projectId] });
      queryClient.invalidateQueries({ queryKey: ["workspaceProjects"] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceProjects"] });
    },
  });
}

export function useProjectGames(projectId: string | undefined) {
  return useQuery({
    queryKey: ["workspaceProjectGames", projectId],
    queryFn: () => fetchProjectGames(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useAddGameToProject(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (gameId: string) => addGameToProject(projectId, gameId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceProjectGames", projectId] });
    },
  });
}

export function useRemoveGameFromProject(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (gameId: string) => removeGameFromProject(projectId, gameId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceProjectGames", projectId] });
    },
  });
}

export function useSavedAnalyses(projectId: string | undefined) {
  return useQuery({
    queryKey: ["workspaceSavedAnalyses", projectId],
    queryFn: () => fetchSavedAnalyses(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useCreateSavedAnalysis(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SavedAnalysisCreatePayload) => createSavedAnalysis(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceSavedAnalyses", projectId] });
    },
  });
}

export function useDeleteSavedAnalysis(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (analysisId: string) => deleteSavedAnalysis(projectId, analysisId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceSavedAnalyses", projectId] });
    },
  });
}

export function useSnapshots(projectId: string | undefined, analysisId: string | undefined) {
  return useQuery({
    queryKey: ["workspaceSnapshots", projectId, analysisId],
    queryFn: () => fetchSnapshots(projectId!, analysisId!),
    enabled: Boolean(projectId) && Boolean(analysisId),
  });
}

export function useCreateSnapshot(projectId: string, analysisId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SnapshotCreatePayload) => createSnapshot(projectId, analysisId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceSnapshots", projectId, analysisId] });
    },
  });
}

export function useProjectMembers(projectId: string | undefined) {
  return useQuery({
    queryKey: ["workspaceProjectMembers", projectId],
    queryFn: () => fetchProjectMembers(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useAddProjectMember(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProjectAddMemberPayload) => addProjectMember(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceProjectMembers", projectId] });
    },
  });
}

export function useRemoveProjectMember(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => removeProjectMember(projectId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaceProjectMembers", projectId] });
    },
  });
}

