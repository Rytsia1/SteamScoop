import { useCallback, useSyncExternalStore } from "react";

/** Minimal game snapshot kept in the browser for favorites / recently viewed. */
export interface SavedGame {
  id: string;
  name: string;
  header_image_url?: string | null;
}

const FAVORITES_KEY = "steamscoop_favorite_games";
const RECENT_KEY = "steamscoop_recent_games";
const RECENT_LIMIT = 8;
const EMPTY: SavedGame[] = [];

// ponytail: browser-only, per device; move to the workspace API if favorites must follow the account.
const cache = new Map<string, SavedGame[]>();
const listeners = new Set<() => void>();

function isSavedGame(value: unknown): value is SavedGame {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return typeof v.id === "string" && typeof v.name === "string";
}

function read(key: string): SavedGame[] {
  const cached = cache.get(key);
  if (cached) return cached;

  let list: SavedGame[] = EMPTY;
  try {
    const parsed: unknown = JSON.parse(window.localStorage.getItem(key) || "[]");
    if (Array.isArray(parsed)) list = parsed.filter(isSavedGame);
  } catch {
    // Storage unavailable or corrupted: start empty
  }
  cache.set(key, list);
  return list;
}

function write(key: string, list: SavedGame[]): void {
  cache.set(key, list);
  try {
    window.localStorage.setItem(key, JSON.stringify(list));
  } catch {
    // Storage unavailable: keep the in-memory copy for this session
  }
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function toSaved(game: SavedGame): SavedGame {
  return { id: game.id, name: game.name, header_image_url: game.header_image_url ?? null };
}

function useStoredList(key: string): SavedGame[] {
  return useSyncExternalStore(
    subscribe,
    () => read(key),
    () => EMPTY
  );
}

export function useFavorites() {
  const favorites = useStoredList(FAVORITES_KEY);

  const isFavorite = useCallback(
    (id: string) => favorites.some((g) => g.id === id),
    [favorites]
  );

  const toggleFavorite = useCallback((game: SavedGame) => {
    const current = read(FAVORITES_KEY);
    write(
      FAVORITES_KEY,
      current.some((g) => g.id === game.id)
        ? current.filter((g) => g.id !== game.id)
        : [toSaved(game), ...current]
    );
  }, []);

  return { favorites, isFavorite, toggleFavorite };
}

export function useRecentlyViewed() {
  const recent = useStoredList(RECENT_KEY);

  const pushRecent = useCallback((game: SavedGame) => {
    const current = read(RECENT_KEY);
    if (current[0]?.id === game.id) return;
    write(
      RECENT_KEY,
      [toSaved(game), ...current.filter((g) => g.id !== game.id)].slice(0, RECENT_LIMIT)
    );
  }, []);

  return { recent, pushRecent };
}
