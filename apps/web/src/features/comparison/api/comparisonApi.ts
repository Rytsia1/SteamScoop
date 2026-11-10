import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../../lib/api-client";
import { ComparisonRequestPayload, ComparisonResponseData } from "../types/comparison";

export async function compareGames(
  payload: ComparisonRequestPayload
): Promise<ComparisonResponseData> {
  return apiClient<ComparisonResponseData>("/comparisons", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function useCompareGames(
  payload: ComparisonRequestPayload,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ["gameComparison", payload],
    queryFn: () => compareGames(payload),
    enabled: (options?.enabled ?? true) && payload.game_ids.length >= 2,
  });
}

