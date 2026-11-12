import { useQuery } from "@tanstack/react-query";
import { apiClient, apiClientWithMeta } from "../../../lib/api-client";
import {
  GameFilterParams,
  GameItem,
  GameOverviewData,
  GameSuggestionItem,
} from "../types/game";
import { PaginationMeta } from "../../../types/api";

export async function fetchGames(
  params?: GameFilterParams
): Promise<{ items: GameItem[]; pagination?: PaginationMeta | null }> {
  // apiClient drops undefined / empty values from the query string
  const result = await apiClientWithMeta<GameItem[]>("/games", {
    params: {
      q: params?.q,
      genre: params?.genre,
      sort: params?.sort,
      catalog_status: params?.catalog_status,
      is_free: params?.is_free,
      year_from: params?.year_from,
      year_to: params?.year_to,
      upcoming: params?.upcoming || undefined,
      limit: params?.limit,
      cursor: params?.cursor,
    },
  });

  return {
    items: result.data,
    pagination: result.meta.pagination,
  };
}

export async function fetchGame(gameId: string): Promise<GameItem> {
  return apiClient<GameItem>(`/games/${encodeURIComponent(gameId)}`);
}

export async function fetchGameOverview(gameId: string): Promise<GameOverviewData> {
  return apiClient<GameOverviewData>(`/games/${encodeURIComponent(gameId)}/overview`);
}

export async function fetchGameSuggestions(
  query: string
): Promise<GameSuggestionItem[]> {
  const trimmed = query.trim();
  if (trimmed.length < 2) return [];

  const result = await apiClient<GameItem[]>("/games", {
    params: { q: trimmed, limit: 5 },
  });

  return (result || []).map((g) => ({
    id: g.id,
    steam_app_id: g.steam_app_id,
    name: g.name || g.title || "Unknown Game",
    header_image_url: g.header_image_url,
    release_date: g.release_date,
    genres: g.genres || [],
  }));
}

export async function fetchGenres(): Promise<string[]> {
  return apiClient<string[]>("/games/genres");
}

export function useGenres() {
  return useQuery({
    queryKey: ["gameGenres"],
    queryFn: fetchGenres,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}

export function useGames(params?: GameFilterParams) {
  return useQuery({
    queryKey: ["games", params],
    queryFn: () => fetchGames(params),
  });
}

export function useGame(gameId: string | undefined) {
  return useQuery({
    queryKey: ["game", gameId],
    queryFn: () => fetchGame(gameId!),
    enabled: Boolean(gameId),
  });
}

export function useGameOverview(gameId: string | undefined) {
  return useQuery({
    queryKey: ["gameOverview", gameId],
    queryFn: () => fetchGameOverview(gameId!),
    enabled: Boolean(gameId),
  });
}

export function useGameSuggestions(query: string) {
  const trimmed = query.trim();
  return useQuery({
    queryKey: ["gameSuggestions", trimmed],
    queryFn: () => fetchGameSuggestions(trimmed),
    enabled: trimmed.length >= 2,
    staleTime: 1000 * 60, // 1 minute
  });
}
