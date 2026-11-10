export const ROUTES = {
  HOME: "/",
  GAMES: "/games",
  GAME_OVERVIEW: "/games/:gameId",
  GAME_REVIEWS: "/games/:gameId/reviews",
  COMPARE: "/compare",
  METHODOLOGY: "/methodology",
  STATUS: "/status",
} as const;

export function gameOverviewPath(gameId: string): string {
  return `/games/${encodeURIComponent(gameId)}`;
}

export function gameReviewsPath(gameId: string): string {
  return `/games/${encodeURIComponent(gameId)}/reviews`;
}

