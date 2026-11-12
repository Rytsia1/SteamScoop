export type GameCatalogStatus = "pending" | "indexed" | "failed" | "disabled";

export type GameSortOption =
  | "name_asc"
  | "name_desc"
  | "recently_updated"
  | "release_desc"
  | "release_asc";

export interface GameItem {
  id: string;
  steam_app_id: number;
  name: string;
  title?: string;
  slug?: string;
  catalog_status: GameCatalogStatus | string;
  is_active?: boolean;
  header_image_url?: string | null;
  short_description?: string | null;
  developer?: string | null;
  publisher?: string | null;
  developers?: string[];
  publishers?: string[];
  genres: string[];
  categories?: string[];
  tags?: string[];
  release_date?: string | null;
  is_free?: boolean | null;
  review_count?: number;
  steam_positive_percentage?: number | null;
  model_sentiment_positive_rate?: number | null;
  last_synced_at?: string | null;
}

export function getGameName(game: GameItem): string {
  return game.name || game.title || "Untitled Game";
}

export function getGameDeveloper(game: GameItem): string {
  if (game.developer) return game.developer;
  if (game.developers && game.developers.length > 0) return game.developers[0];
  if (game.publisher) return game.publisher;
  if (game.publishers && game.publishers.length > 0) return game.publishers[0];
  return "Unknown Developer";
}

export interface SteamRecommendationSummary {
  total_reviews: number;
  positive_reviews: number;
  negative_reviews: number;
  positive_percentage: number;
}

export interface ModelSentimentSummary {
  total_classified: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_rate: number;
  negative_rate: number;
  neutral_rate: number;
  model_version: string;
}

export interface CoverageSummary {
  total_reviews_collected: number;
  steam_total_reviews?: number | null;
  coverage_percentage: number;
}

export interface GameOverviewData {
  game: GameItem;
  steam_recommendations: SteamRecommendationSummary;
  model_sentiment: ModelSentimentSummary;
  coverage: CoverageSummary;
}

export interface GameFilterParams {
  q?: string;
  genre?: string;
  catalog_status?: string;
  is_free?: boolean;
  year_from?: number;
  year_to?: number;
  upcoming?: boolean;
  sort?: GameSortOption | string;
  limit?: number;
  cursor?: string;
}

/** Whole days until a future release date, or null when released / undated. */
export function daysUntilRelease(releaseDate: string | null | undefined, now = Date.now()): number | null {
  if (!releaseDate) return null;
  const releaseMs = Date.parse(releaseDate);
  if (Number.isNaN(releaseMs)) return null;
  const days = Math.ceil((releaseMs - now) / 86_400_000);
  return days > 0 ? days : null;
}

export interface GameSuggestionItem {
  id: string;
  steam_app_id: number;
  name: string;
  header_image_url?: string | null;
  release_date?: string | null;
  genres: string[];
}
