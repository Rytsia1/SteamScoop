import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../../lib/api-client";
import {
  GameAnalyticsData,
  GameAspectsData,
  GameTopicsData,
  SentimentDistributionData,
} from "../types/intelligence";

export interface AnalyticsQueryParams {
  period?: "day" | "week" | "month";
  from?: string;
  to?: string;
  model_version?: string;
}

export async function fetchGameAnalytics(
  gameId: string,
  params?: AnalyticsQueryParams
): Promise<GameAnalyticsData> {
  const queryParams: Record<string, string> = {};
  if (params?.period) queryParams.period = params.period;
  if (params?.from) queryParams.from = params.from;
  if (params?.to) queryParams.to = params.to;
  if (params?.model_version) queryParams.model_version = params.model_version;

  return apiClient<GameAnalyticsData>(`/games/${encodeURIComponent(gameId)}/analytics`, {
    params: queryParams,
  });
}

export async function fetchGameSentiment(
  gameId: string,
  params?: { model_version?: string }
): Promise<SentimentDistributionData> {
  return apiClient<SentimentDistributionData>(
    `/games/${encodeURIComponent(gameId)}/sentiment`,
    { params }
  );
}

export async function fetchGameAspects(
  gameId: string,
  params?: { model_version?: string }
): Promise<GameAspectsData> {
  return apiClient<GameAspectsData>(`/games/${encodeURIComponent(gameId)}/aspects`, {
    params,
  });
}

export async function fetchGameTopics(
  gameId: string,
  params?: { model_version?: string }
): Promise<GameTopicsData> {
  return apiClient<GameTopicsData>(`/games/${encodeURIComponent(gameId)}/topics`, {
    params,
  });
}

export function useGameAnalytics(
  gameId: string | undefined,
  params?: AnalyticsQueryParams
) {
  return useQuery({
    queryKey: ["gameAnalytics", gameId, params],
    queryFn: () => fetchGameAnalytics(gameId!, params),
    enabled: Boolean(gameId),
  });
}

export function useGameSentiment(
  gameId: string | undefined,
  params?: { model_version?: string }
) {
  return useQuery({
    queryKey: ["gameSentiment", gameId, params],
    queryFn: () => fetchGameSentiment(gameId!, params),
    enabled: Boolean(gameId),
  });
}

export function useGameAspects(
  gameId: string | undefined,
  params?: { model_version?: string }
) {
  return useQuery({
    queryKey: ["gameAspects", gameId, params],
    queryFn: () => fetchGameAspects(gameId!, params),
    enabled: Boolean(gameId),
  });
}

export function useGameTopics(
  gameId: string | undefined,
  params?: { model_version?: string }
) {
  return useQuery({
    queryKey: ["gameTopics", gameId, params],
    queryFn: () => fetchGameTopics(gameId!, params),
    enabled: Boolean(gameId),
  });
}

