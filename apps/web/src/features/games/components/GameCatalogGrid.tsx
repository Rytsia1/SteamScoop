import React from "react";
import { GameItem } from "../types/game";
import { GameCard } from "./GameCard";
import { CardSkeleton } from "../../../components/feedback/LoadingSkeleton";
import { ErrorAlert } from "../../../components/feedback/ErrorAlert";
import { EmptyState } from "../../../components/feedback/EmptyState";
import { Button } from "../../../components/ui/Button";
import { PaginationMeta } from "../../../types/api";
import { ChevronLeft, ChevronRight, Gamepad2 } from "lucide-react";

export interface GameCatalogGridProps {
  games: GameItem[] | undefined;
  isLoading: boolean;
  error: Error | null;
  onRetry: () => void;
  pagination?: PaginationMeta | null;
  onNextPage?: () => void;
  onPrevPage?: () => void;
  hasPrevPage?: boolean;
  currentPage?: number;
  activeSearchQuery?: string;
  onResetFilters?: () => void;
}

export const GameCatalogGrid: React.FC<GameCatalogGridProps> = ({
  games,
  isLoading,
  error,
  onRetry,
  pagination,
  onNextPage,
  onPrevPage,
  hasPrevPage = false,
  currentPage = 1,
  activeSearchQuery,
  onResetFilters,
}) => {
  if (isLoading) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Loading games">
        <CardSkeleton count={6} />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorAlert
        title="Could not load game catalog"
        message={error.message || "An unexpected error occurred while fetching games."}
        onRetry={onRetry}
      />
    );
  }

  if (!games || games.length === 0) {
    const isSearching = Boolean(activeSearchQuery && activeSearchQuery.trim());
    return (
      <EmptyState
        title={isSearching ? `No results for "${activeSearchQuery}"` : "No games found"}
        description={
          isSearching
            ? "We couldn't find any indexed games matching your search. Check for typos or try clearing genre and status filters."
            : "No games are currently listed matching your selected criteria. Try adjusting or resetting your filters."
        }
        icon={<Gamepad2 className="w-7 h-7 text-sky-400" aria-hidden="true" />}
        actionLabel={onResetFilters ? "Reset All Filters" : undefined}
        onAction={onResetFilters}
      />
    );
  }

  return (
    <div className="space-y-8">
      {/* Catalog Grid */}
      <div
        role="region"
        aria-label="Games list"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        {games.map((game) => (
          <GameCard key={game.id} game={game} />
        ))}
      </div>

      {/* Pagination Bar */}
      {pagination && (pagination.has_more || hasPrevPage) && (
        <nav
          aria-label="Game catalog pagination"
          className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-slate-800"
        >
          <div className="text-xs text-slate-400 font-mono">
            <span>
              Page {currentPage} &bull; Showing {games.length} titles
            </span>
            {pagination.total_count !== undefined && pagination.total_count !== null && (
              <span> &bull; Total: <b>{pagination.total_count.toLocaleString()}</b></span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!hasPrevPage}
              onClick={onPrevPage}
              leftIcon={<ChevronLeft className="w-3.5 h-3.5" aria-hidden="true" />}
            >
              Previous Page
            </Button>

            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!pagination.has_more}
              onClick={onNextPage}
              rightIcon={<ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />}
            >
              Next Page
            </Button>
          </div>
        </nav>
      )}
    </div>
  );
};
