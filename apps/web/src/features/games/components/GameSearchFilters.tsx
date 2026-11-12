import React, { useState, useRef, useEffect } from "react";
import { Search, X, Loader2, ArrowRight } from "lucide-react";
import { Select } from "../../../components/ui/Select";
import { Input } from "../../../components/ui/Input";
import { Button } from "../../../components/ui/Button";
import { useGameSuggestions, useGenres } from "../api/gamesApi";
import { Link } from "../../../app/router/Router";
import { gameOverviewPath } from "../../../app/router/routes";
import { GameSortOption } from "../types/game";
import { useDebouncedValue } from "../../../lib/useDebouncedValue";
import { clsx } from "clsx";

export type PriceFilter = "" | "free" | "paid";

export interface GameSearchFiltersProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  statusFilter: string;
  onStatusChange: (status: string) => void;
  /** Hidden on the upcoming view, where both indexed and pending games are listed. */
  showStatusFilter?: boolean;
  genreFilter: string;
  onGenreChange: (genre: string) => void;
  priceFilter: PriceFilter;
  onPriceChange: (price: PriceFilter) => void;
  yearFrom: string;
  onYearFromChange: (year: string) => void;
  yearTo: string;
  onYearToChange: (year: string) => void;
  sortOption: GameSortOption | string;
  onSortChange: (sort: GameSortOption) => void;
  hasActiveFilters: boolean;
  onReset: () => void;
}

/** Fallback while /games/genres loads or if it returns nothing. */
const COMMON_GENRES = [
  "Action",
  "Adventure",
  "RPG",
  "Strategy",
  "Simulation",
  "Indie",
  "Shooter",
];

const STATUS_OPTIONS = [
  { value: "indexed", label: "Indexed (Full Analytics)" },
  { value: "pending", label: "Pending Ingestion" },
];

const SORT_OPTIONS = [
  { value: "name_asc", label: "Title: A to Z" },
  { value: "name_desc", label: "Title: Z to A" },
  { value: "release_desc", label: "Release: Newest First" },
  { value: "release_asc", label: "Release: Oldest First" },
  { value: "recently_updated", label: "Recently Updated" },
];

const PRICE_OPTIONS = [
  { value: "", label: "Free & Paid" },
  { value: "free", label: "Free to Play" },
  { value: "paid", label: "Paid" },
];

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
}

export const GameSearchFilters: React.FC<GameSearchFiltersProps> = ({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusChange,
  showStatusFilter = true,
  genreFilter,
  onGenreChange,
  priceFilter,
  onPriceChange,
  yearFrom,
  onYearFromChange,
  yearTo,
  onYearToChange,
  sortOption,
  onSortChange,
  hasActiveFilters,
  onReset,
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const debouncedQuery = useDebouncedValue(searchQuery, 300);
  const { data: suggestions, isLoading: isLoadingSuggestions } = useGameSuggestions(debouncedQuery);
  const { data: genres } = useGenres();
  const genreList = genres && genres.length > 0 ? genres : COMMON_GENRES;

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        searchContainerRef.current &&
        !searchContainerRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // "/" focuses the search box (matches the hint shown in the header)
  useEffect(() => {
    const handleSlash = (e: KeyboardEvent) => {
      if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey || isTypingTarget(e.target)) {
        return;
      }
      e.preventDefault();
      searchInputRef.current?.focus();
    };

    document.addEventListener("keydown", handleSlash);
    return () => document.removeEventListener("keydown", handleSlash);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || !suggestions || suggestions.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % suggestions.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === "Escape") {
      e.preventDefault();
      setShowSuggestions(false);
    } else if (e.key === "Enter" && selectedIndex >= 0) {
      e.preventDefault();
      const selected = suggestions[selectedIndex];
      onSearchChange(selected.name);
      setShowSuggestions(false);
    }
  };

  return (
    <div
      role="search"
      aria-label="Game catalog search and filter controls"
      className="w-full rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-md p-5 sm:p-6 flex flex-col gap-5 shadow-lg shadow-black/20"
    >
      {/* Top Search Bar & Suggestions Combobox */}
      <div ref={searchContainerRef} className="relative w-full">
        <label htmlFor="game-search-input" className="text-xs font-semibold text-slate-300 block mb-1.5">
          Search Game by Name or Steam App ID
        </label>

        <div className="relative flex items-center">
          <div className="absolute left-3.5 text-slate-400 pointer-events-none flex items-center">
            {isLoadingSuggestions ? (
              <Loader2 className="w-4 h-4 animate-spin text-sky-400" aria-hidden="true" />
            ) : (
              <Search className="w-4 h-4 text-slate-400" aria-hidden="true" />
            )}
          </div>

          <input
            ref={searchInputRef}
            id="game-search-input"
            type="search"
            role="combobox"
            aria-autocomplete="list"
            aria-expanded={showSuggestions && Boolean(suggestions && suggestions.length > 0)}
            aria-controls="search-suggestions-list"
            aria-keyshortcuts="/"
            autoComplete="off"
            placeholder="Type a game name or App ID (e.g., 'Hades', '1145360')..."
            value={searchQuery}
            onChange={(e) => {
              onSearchChange(e.target.value);
              setShowSuggestions(true);
              setSelectedIndex(-1);
            }}
            onFocus={() => {
              if (searchQuery.trim().length >= 2) setShowSuggestions(true);
            }}
            onKeyDown={handleKeyDown}
            className="w-full rounded-xl bg-slate-950/80 border border-slate-700/80 pl-10 pr-10 py-3 text-sm text-slate-100 placeholder-slate-500 transition-colors focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/20"
          />

          {searchQuery && (
            <button
              type="button"
              onClick={() => {
                onSearchChange("");
                setShowSuggestions(false);
              }}
              aria-label="Clear search query"
              className="absolute right-3 p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors focus-visible:outline-none"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </button>
          )}
        </div>

        {/* Live Search Suggestions Dropdown */}
        {showSuggestions && suggestions && suggestions.length > 0 && (
          <div
            id="search-suggestions-list"
            role="listbox"
            aria-label="Live search suggestions"
            className="absolute left-0 right-0 top-full mt-2 z-50 rounded-xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden divide-y divide-slate-800 animate-in fade-in zoom-in-95 duration-100"
          >
            <div className="px-3 py-1.5 bg-slate-950/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>Matching Games ({suggestions.length})</span>
              <span className="text-[10px] font-mono lowercase">use &uarr;&darr; to navigate</span>
            </div>

            {suggestions.map((item, idx) => {
              const isHighlighted = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  role="option"
                  aria-selected={isHighlighted}
                  className={clsx(
                    "p-3 flex items-center justify-between gap-3 cursor-pointer transition-colors",
                    isHighlighted ? "bg-slate-800 text-white" : "hover:bg-slate-800/60 text-slate-200"
                  )}
                  onClick={() => {
                    onSearchChange(item.name);
                    setShowSuggestions(false);
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-slate-950 border border-slate-800 flex items-center justify-center text-xs font-bold text-sky-400 shrink-0">
                      #{item.steam_app_id}
                    </div>
                    <div>
                      <span className="text-sm font-semibold block">{item.name}</span>
                      <span className="text-[11px] text-slate-400">
                        {item.genres.slice(0, 2).join(", ") || "General"}
                      </span>
                    </div>
                  </div>

                  <Link
                    to={gameOverviewPath(item.id)}
                    className="p-1 rounded text-slate-400 hover:text-sky-400 focus-visible:outline-none"
                    onClick={(e) => e.stopPropagation()}
                    aria-label={`Open overview for ${item.name}`}
                  >
                    <ArrowRight className="w-4 h-4" aria-hidden="true" />
                  </Link>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Genre Pills */}
      <fieldset className="space-y-2 border-0 p-0 m-0">
        <legend className="text-xs font-semibold text-slate-400">Genres:</legend>
        <div className="flex flex-wrap gap-1.5 items-center">
          {["", ...genreList].map((genre) => {
            const isActive = genreFilter.toLowerCase() === genre.toLowerCase();
            return (
              <button
                key={genre || "all"}
                type="button"
                aria-pressed={isActive}
                onClick={() => onGenreChange(isActive ? "" : genre)}
                className={clsx(
                  "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400",
                  isActive
                    ? "bg-sky-500 text-white font-semibold shadow-md shadow-sky-500/20"
                    : "bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-700/60"
                )}
              >
                {genre || "All Genres"}
              </button>
            );
          })}
        </div>
      </fieldset>

      {/* Secondary Controls: Sorting, Price, Release Year, Status, Reset */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3 pt-3 border-t border-slate-800/80 items-end">
        <div className="col-span-2 lg:col-span-1">
          <Select
            label="Sort Catalog By"
            value={sortOption}
            onChange={(e) => onSortChange(e.target.value as GameSortOption)}
            options={SORT_OPTIONS}
          />
        </div>

        <div className="col-span-2 lg:col-span-1">
          <Select
            label="Price"
            value={priceFilter}
            onChange={(e) => onPriceChange(e.target.value as PriceFilter)}
            options={PRICE_OPTIONS}
          />
        </div>

        <Input
          label="Released From"
          type="number"
          inputMode="numeric"
          min={1970}
          max={2100}
          placeholder="Year"
          value={yearFrom}
          onChange={(e) => onYearFromChange(e.target.value)}
        />

        <Input
          label="Released To"
          type="number"
          inputMode="numeric"
          min={1970}
          max={2100}
          placeholder="Year"
          value={yearTo}
          onChange={(e) => onYearToChange(e.target.value)}
        />

        {showStatusFilter && (
          <div className="col-span-2 lg:col-span-1">
            <Select
              label="Catalog Status"
              value={statusFilter}
              onChange={(e) => onStatusChange(e.target.value)}
              options={STATUS_OPTIONS}
            />
          </div>
        )}

        <div className="col-span-2 lg:col-span-1">
          {hasActiveFilters ? (
            <Button
              type="button"
              variant="outline"
              size="md"
              onClick={onReset}
              className="w-full text-xs text-slate-300 hover:text-white hover:bg-slate-800 border-slate-700"
              leftIcon={<X className="w-3.5 h-3.5 text-rose-400" aria-hidden="true" />}
            >
              Reset Filters
            </Button>
          ) : (
            <div className="text-[11px] text-slate-500 py-2.5 text-center">Filters clear</div>
          )}
        </div>
      </div>
    </div>
  );
};
