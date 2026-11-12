export const ROUTES = {
  HOME: "/",
  GAMES: "/games",
  UPCOMING: "/upcoming",
  GAME_OVERVIEW: "/games/:gameId",
  GAME_REVIEWS: "/games/:gameId/reviews",
  COMPARE: "/compare",
  METHODOLOGY: "/methodology",
  STATUS: "/status",
  WORKSPACE: "/workspace",
  PROJECT_DETAIL: "/workspace/projects/:projectId",
  ADMIN: "/admin",
} as const;

export function gameOverviewPath(gameId: string): string {
  return `/games/${encodeURIComponent(gameId)}`;
}

export function gameReviewsPath(gameId: string): string {
  return `/games/${encodeURIComponent(gameId)}/reviews`;
}

export function projectDetailPath(projectId: string): string {
  return `/workspace/projects/${encodeURIComponent(projectId)}`;
}

