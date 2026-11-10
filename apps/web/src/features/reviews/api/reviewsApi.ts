import { useQuery } from "@tanstack/react-query";
import { apiClient, apiClientWithMeta } from "../../../lib/api-client";
import {
  ReviewDetailData,
  ReviewFilterParams,
  ReviewIntelligenceData,
  ReviewItem,
} from "../types/review";
import { PaginationMeta } from "../../../types/api";

export async function fetchGameReviews(
  gameId: string,
  params?: ReviewFilterParams
): Promise<{ items: ReviewItem[]; pagination?: PaginationMeta | null }> {
  const queryParams: Record<string, string | number | boolean> = {};

  if (params?.sentiment) queryParams.sentiment = params.sentiment;

  // Handle recommendation filter
  if (params?.steam_recommended !== undefined && params?.steam_recommended !== "") {
    queryParams.steam_recommended =
      params.steam_recommended === true || params.steam_recommended === "true";
  } else if (params?.voted_up !== undefined && params?.voted_up !== "") {
    queryParams.steam_recommended =
      params.voted_up === true || params.voted_up === "true";
  }

  if (params?.language) queryParams.language = params.language;
  if (params?.aspect) queryParams.aspect = params.aspect;
  if (params?.topic_id) queryParams.topic_id = params.topic_id;
  if (params?.sort) queryParams.sort = params.sort;
  if (params?.limit) queryParams.limit = params.limit;
  if (params?.cursor) queryParams.cursor = params.cursor;

  const result = await apiClientWithMeta<ReviewItem[]>(
    `/games/${encodeURIComponent(gameId)}/reviews`,
    { params: queryParams }
  );

  return {
    items: result.data,
    pagination: result.meta.pagination,
  };
}

export async function fetchReview(reviewId: string): Promise<ReviewDetailData> {
  return apiClient<ReviewDetailData>(`/reviews/${encodeURIComponent(reviewId)}`);
}

export async function fetchReviewIntelligence(
  reviewId: string
): Promise<ReviewIntelligenceData> {
  return apiClient<ReviewIntelligenceData>(
    `/reviews/${encodeURIComponent(reviewId)}/intelligence`
  );
}

export function useGameReviews(
  gameId: string | undefined,
  params?: ReviewFilterParams
) {
  return useQuery({
    queryKey: ["gameReviews", gameId, params],
    queryFn: () => fetchGameReviews(gameId!, params),
    enabled: Boolean(gameId),
  });
}

export function useReview(reviewId: string | undefined) {
  return useQuery({
    queryKey: ["reviewDetail", reviewId],
    queryFn: () => fetchReview(reviewId!),
    enabled: Boolean(reviewId),
  });
}

export function useReviewIntelligence(reviewId: string | undefined) {
  return useQuery({
    queryKey: ["reviewIntelligence", reviewId],
    queryFn: () => fetchReviewIntelligence(reviewId!),
    enabled: Boolean(reviewId),
  });
}
