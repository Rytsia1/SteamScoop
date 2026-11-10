export interface ComparisonPeriod {
  from?: string;
  to?: string;
}

export interface ComparisonRequestPayload {
  game_ids: string[];
  metrics?: string[];
  period?: ComparisonPeriod | null;
  model_version?: string;
}

export interface GameComparisonResult {
  game_id: string;
  name: string;
  title?: string;
  steam_app_id?: number;
  review_volume?: number | null;
  steam_recommendation_rate?: number | null;
  model_positive_rate?: number | null;
  model_sentiment_rate?: number | null;
  sentiment_score?: number | null;
  aspect_sentiment?: Record<string, number> | null;
  coverage_percentage?: number | null;
  steam_total_reviews?: number | null;
  model_version?: string | null;
}

export interface ComparisonResponseData {
  games: GameComparisonResult[];
  period?: ComparisonPeriod | null;
  model_version?: string | null;
}
