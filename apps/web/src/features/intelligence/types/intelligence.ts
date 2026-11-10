export interface AnalyticsPoint {
  period_start: string;
  period_end: string;
  review_count: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  steam_recommended_count: number;
  steam_not_recommended_count: number;
  sentiment_score?: number | null;
}

export interface GameAnalyticsData {
  game_id: string;
  period: "day" | "week" | "month";
  model_version: string;
  points: AnalyticsPoint[];
}

export interface SentimentDistributionData {
  game_id: string;
  model_version: string;
  total_reviews: number;
  classified_count: number;
  unclassified_count: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_rate: number;
  negative_rate: number;
  neutral_rate: number;
  coverage_rate: number;
  unclassified_rate: number;
  sentiment_score?: number | null;
  timeline?: AnalyticsPoint[] | null;
}

export interface AspectSummaryPoint {
  aspect_key: string;
  display_name: string;
  mention_count: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_rate: number;
  negative_rate: number;
  neutral_rate: number;
  sentiment_score?: number | null;
  prevalence: number;
}

export interface GameAspectsData {
  game_id: string;
  taxonomy_version: string;
  model_version: string;
  aspects: AspectSummaryPoint[];
  total_aspect_mentions: number;
  unique_reviews_with_aspects: number;
}

export interface TopicSummaryPoint {
  topic_key: string;
  label: string;
  review_count: number;
  prevalence: number;
  avg_score: number;
  is_outlier: boolean;
  keywords: string[];
}

export interface GameTopicsData {
  game_id: string;
  model_version: string;
  topics: TopicSummaryPoint[];
  total_assigned_reviews: number;
  outlier_count: number;
  outlier_rate: number;
}

