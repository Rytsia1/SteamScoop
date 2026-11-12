import React, { useState, useEffect } from "react";
import { useGames } from "../features/games/api/gamesApi";
import {
  GameSearchFilters,
  PriceFilter,
} from "../features/games/components/GameSearchFilters";
import { GameCatalogGrid } from "../features/games/components/GameCatalogGrid";
import { useRouter, useSearchParams } from "../app/router/RouterContext";
import { Link } from "../app/router/Router";
import { gameOverviewPath, ROUTES } from "../app/router/routes";
import { GameSortOption } from "../features/games/types/game";
import {
  SavedGame,
  useFavorites,
  useRecentlyViewed,
} from "../features/games/hooks/useGameList";
import { useDebouncedValue } from "../lib/useDebouncedValue";
import { BarChart3, CalendarClock, Database, History, Star } from "lucide-react";

/** A 4-digit year the API accepts, or undefined while the user is still typing. */
function toYear(value: string): number | undefined {
  const year = Number(value);
  return /^\d{4}$/.test(value) && year >= 1970 && year <= 2100 ? year : undefined;
}

function parsePrice(value: string | null): PriceFilter {
  return value === "free" || value === "paid" ? value : "";
}

const SavedGamesStrip: React.FC<{
  title: string;
  icon: React.ReactNode;
  games: SavedGame[];
}> = ({ title, icon, games }) => {
  if (games.length === 0) return null;

  return (
    <section aria-label={title} className="space-y-2">
      <h2 className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
        {icon}
        {title}
      </h2>
      <ul className="flex flex-wrap gap-2">
        {games.map((game) => (
          <li key={game.id}>
            <Link
              to={gameOverviewPath(game.id)}
              className="inline-flex items-center gap-2 pl-1 pr-3 py-1 rounded-lg bg-slate-900/70 border border-slate-800 hover:border-sky-700 text-xs text-slate-200 hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
            >
              {game.header_image_url ? (
                <img
                  src={game.header_image_url}
                  alt=""
                  loading="lazy"
                  className="w-10 h-5 rounded object-cover"
                />
              ) : (
                <span className="w-10 h-5 rounded bg-slate-800" aria-hidden="true" />
              )}
              <span className="max-w-[160px] truncate">{game.name}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
};

const CatalogView: React.FC<{ isUpcoming: boolean }> = ({ isUpcoming }) => {
  const defaultSort: GameSortOption = isUpcoming ? "release_asc" : "name_asc";
  const [searchParams, setSearchParams] = useSearchParams();

  const [searchQuery, setSearchQuery] = useState(() => searchParams.get("q") || "");
  const [statusFilter, setStatusFilter] = useState(() => searchParams.get("status") || "indexed");
  const [genreFilter, setGenreFilter] = useState(() => searchParams.get("genre") || "");
  const [priceFilter, setPriceFilter] = useState<PriceFilter>(() =>
    parsePrice(searchParams.get("price"))
  );
  const [yearFrom, setYearFrom] = useState(() => searchParams.get("from") || "");
  const [yearTo, setYearTo] = useState(() => searchParams.get("to") || "");
  const [sortOption, setSortOption] = useState<GameSortOption>(
    () => (searchParams.get("sort") as GameSortOption) || defaultSort
  );

  const [cursor, setCursor] = useState<string | undefined>(undefined);
  const [cursorHistory, setCursorHistory] = useState<string[]>([]);

  // Typed inputs only hit the API / URL once the user pauses
  const debouncedQuery = useDebouncedValue(searchQuery, 300);
  const debouncedYearFrom = toYear(useDebouncedValue(yearFrom, 300));
  const debouncedYearTo = toYear(useDebouncedValue(yearTo, 300));

  const { favorites } = useFavorites();
  const { recent } = useRecentlyViewed();

  // Synchronize filter state to URL search params
  useEffect(() => {
    setSearchParams({
      q: debouncedQuery || undefined,
      genre: genreFilter || undefined,
      status: statusFilter !== "indexed" ? statusFilter : undefined,
      price: priceFilter || undefined,
      from: debouncedYearFrom,
      to: debouncedYearTo,
      sort: sortOption !== defaultSort ? sortOption : undefined,
    });
  }, [
    debouncedQuery,
    genreFilter,
    statusFilter,
    priceFilter,
    debouncedYearFrom,
    debouncedYearTo,
    sortOption,
    defaultSort,
    setSearchParams,
  ]);

  const { data, isLoading, error, refetch } = useGames({
    q: debouncedQuery || undefined,
    catalog_status: isUpcoming ? undefined : statusFilter,
    genre: genreFilter || undefined,
    is_free: priceFilter === "" ? undefined : priceFilter === "free",
    year_from: debouncedYearFrom,
    year_to: debouncedYearTo,
    upcoming: isUpcoming || undefined,
    sort: sortOption,
    limit: 12,
    cursor,
  });

  const resetPaging = () => {
    setCursor(undefined);
    setCursorHistory([]);
  };

  /** Wrap a filter setter so changing the filter returns to page 1. */
  const withPageReset =
    <T,>(setter: (value: T) => void) =>
    (value: T) => {
      setter(value);
      resetPaging();
    };

  const handleNextPage = () => {
    if (data?.pagination?.next_cursor) {
      setCursorHistory((prev) => [...prev, cursor || ""]);
      setCursor(data.pagination.next_cursor);
      window.scrollTo({ top: 300, behavior: "smooth" });
    }
  };

  const handlePrevPage = () => {
    if (cursorHistory.length > 0) {
      const prevCursor = cursorHistory[cursorHistory.length - 1];
      setCursorHistory((prev) => prev.slice(0, -1));
      setCursor(prevCursor || undefined);
      window.scrollTo({ top: 300, behavior: "smooth" });
    }
  };

  const handleResetFilters = () => {
    setSearchQuery("");
    setStatusFilter("indexed");
    setGenreFilter("");
    setPriceFilter("");
    setYearFrom("");
    setYearTo("");
    setSortOption(defaultSort);
    resetPaging();
  };

  const hasActiveFilters = Boolean(
    searchQuery ||
      genreFilter ||
      priceFilter ||
      yearFrom ||
      yearTo ||
      (!isUpcoming && statusFilter !== "indexed") ||
      sortOption !== defaultSort
  );

  const currentPage = cursorHistory.length + 1;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8">
      {/* Hero Header */}
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-950/70 border border-sky-800/60 text-xs font-medium text-sky-300">
          {isUpcoming ? (
            <CalendarClock className="w-3.5 h-3.5" aria-hidden="true" />
          ) : (
            <Database className="w-3.5 h-3.5" aria-hidden="true" />
          )}
          <span>
            {isUpcoming ? "Release Radar" : "Public Game Intelligence & Research Platform"}
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
          {isUpcoming ? "Upcoming Releases" : "Explore Steam Player Sentiment & Game Dynamics"}
        </h1>
        <p className="text-sm sm:text-base text-slate-400 max-w-2xl leading-relaxed">
          {isUpcoming
            ? "Unreleased titles tracked in the catalog, soonest first. Sentiment analytics appear once player reviews are collected after launch."
            : "Access structured Natural Language Processing intelligence, aspect-based sentiment analysis, and topic models across indexed Steam titles without login gates."}
        </p>
      </div>

      {!isUpcoming && (
        <>
          <SavedGamesStrip
            title="Favorites"
            icon={<Star className="w-3.5 h-3.5 text-amber-400" aria-hidden="true" />}
            games={favorites}
          />
          <SavedGamesStrip
            title="Recently Viewed"
            icon={<History className="w-3.5 h-3.5 text-sky-400" aria-hidden="true" />}
            games={recent}
          />
        </>
      )}

      {/* Search and Filters */}
      <GameSearchFilters
        searchQuery={searchQuery}
        onSearchChange={withPageReset(setSearchQuery)}
        statusFilter={statusFilter}
        onStatusChange={withPageReset(setStatusFilter)}
        showStatusFilter={!isUpcoming}
        genreFilter={genreFilter}
        onGenreChange={withPageReset(setGenreFilter)}
        priceFilter={priceFilter}
        onPriceChange={withPageReset(setPriceFilter)}
        yearFrom={yearFrom}
        onYearFromChange={withPageReset(setYearFrom)}
        yearTo={yearTo}
        onYearToChange={withPageReset(setYearTo)}
        sortOption={sortOption}
        onSortChange={withPageReset(setSortOption)}
        hasActiveFilters={hasActiveFilters}
        onReset={handleResetFilters}
      />

      {/* Catalog Grid Section */}
      <section aria-label="Game Catalog Results">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-sky-400" aria-hidden="true" />
            <h2 className="text-base font-bold text-white">
              {isUpcoming ? "Upcoming Games" : "Indexed Game Catalog"}
            </h2>
          </div>

          {debouncedQuery && (
            <span className="text-xs text-slate-400">
              Filtering for &ldquo;{debouncedQuery}&rdquo;
            </span>
          )}
        </div>

        <GameCatalogGrid
          games={data?.items}
          isLoading={isLoading}
          error={error}
          onRetry={() => refetch()}
          pagination={data?.pagination}
          onNextPage={handleNextPage}
          onPrevPage={handlePrevPage}
          hasPrevPage={cursorHistory.length > 0}
          currentPage={currentPage}
          activeSearchQuery={debouncedQuery}
          onResetFilters={handleResetFilters}
        />
      </section>
    </div>
  );
};

export const GamesCatalogPage: React.FC = () => {
  const { currentPath } = useRouter();
  const isUpcoming = currentPath === ROUTES.UPCOMING;
  // Remount on view switch so each view starts from its own URL-derived state
  return <CatalogView key={isUpcoming ? "upcoming" : "catalog"} isUpcoming={isUpcoming} />;
};
