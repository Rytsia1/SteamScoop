import React, { useState, useEffect } from "react";
import { useGames } from "../features/games/api/gamesApi";
import { GameSearchFilters } from "../features/games/components/GameSearchFilters";
import { GameCatalogGrid } from "../features/games/components/GameCatalogGrid";
import { useSearchParams } from "../app/router/RouterContext";
import { GameSortOption } from "../features/games/types/game";
import { BarChart3, Database } from "lucide-react";

export const GamesCatalogPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [searchQuery, setSearchQuery] = useState(() => searchParams.get("q") || "");
  const [statusFilter, setStatusFilter] = useState(() => searchParams.get("status") || "indexed");
  const [genreFilter, setGenreFilter] = useState(() => searchParams.get("genre") || "");
  const [sortOption, setSortOption] = useState<GameSortOption>(
    () => (searchParams.get("sort") as GameSortOption) || "name_asc"
  );

  const [cursor, setCursor] = useState<string | undefined>(undefined);
  const [cursorHistory, setCursorHistory] = useState<string[]>([]);

  // Synchronize state changes to URL search params
  useEffect(() => {
    setSearchParams({
      q: searchQuery || undefined,
      genre: genreFilter || undefined,
      status: statusFilter !== "indexed" ? statusFilter : undefined,
      sort: sortOption !== "name_asc" ? sortOption : undefined,
    });
  }, [searchQuery, genreFilter, statusFilter, sortOption, setSearchParams]);

  const { data, isLoading, error, refetch } = useGames({
    q: searchQuery || undefined,
    catalog_status: statusFilter || undefined,
    genre: genreFilter || undefined,
    sort: sortOption,
    limit: 12,
    cursor,
  });

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
    setSortOption("name_asc");
    setCursor(undefined);
    setCursorHistory([]);
  };

  const currentPage = cursorHistory.length + 1;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8">
      {/* Hero Header */}
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-950/70 border border-sky-800/60 text-xs font-medium text-sky-300">
          <Database className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Public Game Intelligence & Research Platform</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
          Explore Steam Player Sentiment & Game Dynamics
        </h1>
        <p className="text-sm sm:text-base text-slate-400 max-w-2xl leading-relaxed">
          Access structured Natural Language Processing intelligence, aspect-based sentiment
          analysis, and topic models across indexed Steam titles without login gates.
        </p>
      </div>

      {/* Search and Filters */}
      <GameSearchFilters
        searchQuery={searchQuery}
        onSearchChange={(q) => {
          setSearchQuery(q);
          setCursor(undefined);
          setCursorHistory([]);
        }}
        statusFilter={statusFilter}
        onStatusChange={(s) => {
          setStatusFilter(s);
          setCursor(undefined);
          setCursorHistory([]);
        }}
        genreFilter={genreFilter}
        onGenreChange={(g) => {
          setGenreFilter(g);
          setCursor(undefined);
          setCursorHistory([]);
        }}
        sortOption={sortOption}
        onSortChange={(sort) => {
          setSortOption(sort);
          setCursor(undefined);
          setCursorHistory([]);
        }}
        onReset={handleResetFilters}
      />

      {/* Catalog Grid Section */}
      <section aria-label="Game Catalog Results">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-sky-400" aria-hidden="true" />
            <h2 className="text-base font-bold text-white">Indexed Game Catalog</h2>
          </div>

          {searchQuery && (
            <span className="text-xs text-slate-400">
              Filtering for &ldquo;{searchQuery}&rdquo;
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
          activeSearchQuery={searchQuery}
          onResetFilters={handleResetFilters}
        />
      </section>
    </div>
  );
};
