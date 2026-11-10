export type ReviewSortOption = "created_at_desc" | "created_at_asc" | "votes_up_desc";

export interface SentimentSummary {
  label: "positive" | "negative" | "neutral" | "unclassified" | string;
  confidence?: number | null;
  model_version: string;
}

export interface ReviewAspectIntel {
  aspect_key: string;
  display_name: string;
  sentiment: string;
  confidence?: number | null;
  evidence_text?: string | null;
  start_offset?: number | null;
  end_offset?: number | null;
}

export interface ReviewTopicIntel {
  topic_id: string;
  topic_key: string;
  label: string;
  score?: number | null;
  model_version: string;
  is_primary?: boolean;
}

export interface ReviewIntelligenceData {
  review_id: string;
  sentiment?: SentimentSummary | null;
  aspects: ReviewAspectIntel[];
  topics: ReviewTopicIntel[];
}

export interface ReviewItem {
  id: string;
  steam_review_id: number;
  review_text: string;
  language: string;
  voted_up: boolean;
  votes_up: number;
  votes_funny: number;
  weighted_vote_score?: number | null;
  comment_count: number;
  steam_playtime_forever?: number | null;
  steam_created_at?: string | null;
  sentiment?: SentimentSummary | null;
}

export interface ReviewDetailData extends ReviewItem {
  game_id: string;
  steam_playtime_at_review?: number | null;
  steam_playtime_last_two_weeks?: number | null;
  steam_purchase?: boolean | null;
  received_for_free?: boolean | null;
  written_during_early_access?: boolean | null;
  steam_updated_at?: string | null;
  first_collected_at?: string | null;
  last_seen_at?: string | null;
}

export interface ReviewFilterParams {
  sentiment?: string;
  steam_recommended?: boolean | string;
  voted_up?: boolean | string;
  aspect?: string;
  topic_id?: string;
  language?: string;
  sort?: ReviewSortOption | string;
  limit?: number;
  cursor?: string;
}
