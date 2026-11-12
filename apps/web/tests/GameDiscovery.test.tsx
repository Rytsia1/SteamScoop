import { render, screen, fireEvent, act, renderHook } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  GameSearchFilters,
  GameSearchFiltersProps,
} from "../src/features/games/components/GameSearchFilters";
import { GameCatalogGrid } from "../src/features/games/components/GameCatalogGrid";
import { GameCard } from "../src/features/games/components/GameCard";
import { GameItem, daysUntilRelease } from "../src/features/games/types/game";
import { RouterProvider } from "../src/app/router/Router";
import { useDebouncedValue } from "../src/lib/useDebouncedValue";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

function filterProps(overrides: Partial<GameSearchFiltersProps> = {}): GameSearchFiltersProps {
  return {
    searchQuery: "",
    onSearchChange: vi.fn(),
    statusFilter: "indexed",
    onStatusChange: vi.fn(),
    genreFilter: "",
    onGenreChange: vi.fn(),
    priceFilter: "",
    onPriceChange: vi.fn(),
    yearFrom: "",
    onYearFromChange: vi.fn(),
    yearTo: "",
    onYearToChange: vi.fn(),
    sortOption: "name_asc",
    onSortChange: vi.fn(),
    hasActiveFilters: false,
    onReset: vi.fn(),
    ...overrides,
  };
}

function renderFilters(overrides: Partial<GameSearchFiltersProps> = {}) {
  return render(
    <QueryClientProvider client={createTestQueryClient()}>
      <GameSearchFilters {...filterProps(overrides)} />
    </QueryClientProvider>
  );
}

const mockGames: GameItem[] = [
  {
    id: "game-1",
    steam_app_id: 220,
    name: "Half-Life 2",
    genres: ["Action", "Shooter"],
    catalog_status: "indexed",
    developer: "Valve",
    publisher: "Valve",
    release_date: "2004-11-16",
    review_count: 140000,
    steam_positive_percentage: 97.0,
    model_sentiment_positive_rate: 0.95,
  },
  {
    id: "game-2",
    steam_app_id: 1091500,
    name: "Cyberpunk 2077",
    genres: ["RPG", "Action"],
    catalog_status: "indexed",
    developer: "CD PROJEKT RED",
    publisher: "CD PROJEKT RED",
    release_date: "2020-12-10",
    review_count: 650000,
    steam_positive_percentage: 84.0,
    model_sentiment_positive_rate: 0.82,
  },
];

describe("Game Discovery Experience", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders search input and triggers search query change", () => {
    const handleSearchChange = vi.fn();
    renderFilters({ onSearchChange: handleSearchChange });

    const searchInput = screen.getByRole("combobox", {
      name: /Search Game by Name or Steam App ID/i,
    });
    expect(searchInput).toBeInTheDocument();

    fireEvent.change(searchInput, { target: { value: "Portal" } });
    expect(handleSearchChange).toHaveBeenCalledWith("Portal");
  });

  it("handles genre button toggle in search filters", () => {
    const handleGenreChange = vi.fn();
    renderFilters({ onGenreChange: handleGenreChange });

    const rpgBtn = screen.getByRole("button", { name: "RPG" });
    fireEvent.click(rpgBtn);
    expect(handleGenreChange).toHaveBeenCalledWith("RPG");
  });

  it("clears the active genre when its pill is clicked again", () => {
    const handleGenreChange = vi.fn();
    renderFilters({ genreFilter: "RPG", onGenreChange: handleGenreChange });

    const rpgBtn = screen.getByRole("button", { name: "RPG" });
    expect(rpgBtn).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(rpgBtn);
    expect(handleGenreChange).toHaveBeenCalledWith("");
  });

  it("handles sort option changes, including release date sorts", () => {
    const handleSortChange = vi.fn();
    renderFilters({ onSortChange: handleSortChange });

    const sortSelect = screen.getByLabelText(/Sort Catalog By/i);
    fireEvent.change(sortSelect, { target: { value: "recently_updated" } });
    expect(handleSortChange).toHaveBeenCalledWith("recently_updated");

    fireEvent.change(sortSelect, { target: { value: "release_desc" } });
    expect(handleSortChange).toHaveBeenCalledWith("release_desc");
  });

  it("forwards price and release year filter changes", () => {
    const onPriceChange = vi.fn();
    const onYearFromChange = vi.fn();
    const onYearToChange = vi.fn();
    renderFilters({ onPriceChange, onYearFromChange, onYearToChange });

    fireEvent.change(screen.getByLabelText("Price"), { target: { value: "free" } });
    expect(onPriceChange).toHaveBeenCalledWith("free");

    fireEvent.change(screen.getByLabelText("Released From"), { target: { value: "2015" } });
    expect(onYearFromChange).toHaveBeenCalledWith("2015");

    fireEvent.change(screen.getByLabelText("Released To"), { target: { value: "2020" } });
    expect(onYearToChange).toHaveBeenCalledWith("2020");
  });

  it("hides the catalog status select on the upcoming view", () => {
    renderFilters({ showStatusFilter: false });
    expect(screen.queryByLabelText("Catalog Status")).not.toBeInTheDocument();
  });

  it("shows Reset Filters only when a filter is active", () => {
    const onReset = vi.fn();
    const { unmount } = renderFilters({ hasActiveFilters: false, onReset });
    expect(screen.queryByRole("button", { name: /Reset Filters/i })).not.toBeInTheDocument();
    unmount();

    renderFilters({ hasActiveFilters: true, onReset });
    fireEvent.click(screen.getByRole("button", { name: /Reset Filters/i }));
    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it("focuses the search box when '/' is pressed outside an input", () => {
    renderFilters();
    const searchInput = screen.getByRole("combobox", {
      name: /Search Game by Name or Steam App ID/i,
    });
    expect(searchInput).not.toHaveFocus();

    fireEvent.keyDown(document.body, { key: "/" });
    expect(searchInput).toHaveFocus();
  });

  it("does not steal '/' while typing in another field", () => {
    renderFilters();
    const yearInput = screen.getByLabelText("Released From");
    yearInput.focus();

    fireEvent.keyDown(yearInput, { key: "/" });
    expect(yearInput).toHaveFocus();
  });

  it("debounces values until input pauses", () => {
    vi.useFakeTimers();
    const { result, rerender } = renderHook(({ value }) => useDebouncedValue(value, 300), {
      initialProps: { value: "a" },
    });

    rerender({ value: "ab" });
    rerender({ value: "abc" });
    act(() => {
      vi.advanceTimersByTime(299);
    });
    expect(result.current).toBe("a");

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(result.current).toBe("abc");
  });

  it("computes days until a future release and null otherwise", () => {
    const now = Date.parse("2026-01-01T00:00:00Z");
    expect(daysUntilRelease("2026-01-11", now)).toBe(10);
    expect(daysUntilRelease("2025-12-01", now)).toBeNull();
    expect(daysUntilRelease(null, now)).toBeNull();
    expect(daysUntilRelease("not-a-date", now)).toBeNull();
  });

  it("renders game cards with metadata and API metrics", () => {
    render(
      <RouterProvider initialPath="/">
        <GameCard game={mockGames[0]} />
      </RouterProvider>
    );

    expect(screen.getByText("Half-Life 2")).toBeInTheDocument();
    expect(screen.getByText("App #220")).toBeInTheDocument();
    expect(screen.getByText("INDEXED")).toBeInTheDocument();
    expect(screen.getByText("Valve")).toBeInTheDocument();
    expect(screen.getByText("97%")).toBeInTheDocument(); // Steam Rec %
    expect(screen.getByText("95%")).toBeInTheDocument(); // Model NLP %
    expect(screen.getByText(/140[.,]000 reviews collected/i)).toBeInTheDocument();
  });

  it("shows a release countdown instead of metrics for unreleased games", () => {
    const inTenDays = new Date(Date.now() + 10 * 86_400_000).toISOString().slice(0, 10);
    render(
      <RouterProvider initialPath="/">
        <GameCard
          game={{
            id: "game-upcoming",
            steam_app_id: 4242,
            name: "Future Game",
            genres: ["Strategy"],
            catalog_status: "pending",
            release_date: inTenDays,
          }}
        />
      </RouterProvider>
    );

    expect(screen.getByText(/Releases in \d+ days?/)).toBeInTheDocument();
    expect(screen.queryByText("NLP Sentiment")).not.toBeInTheDocument();
  });

  it("toggles a favorite and persists it to localStorage", () => {
    render(
      <RouterProvider initialPath="/">
        <GameCard game={mockGames[1]} />
      </RouterProvider>
    );

    const star = screen.getByRole("button", { name: "Add Cyberpunk 2077 to favorites" });
    expect(star).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(star);
    const pressed = screen.getByRole("button", { name: "Remove Cyberpunk 2077 from favorites" });
    expect(pressed).toHaveAttribute("aria-pressed", "true");
    const stored: unknown = JSON.parse(
      window.localStorage.getItem("steamscoop_favorite_games") || "[]"
    );
    expect(stored).toEqual([
      { id: "game-2", name: "Cyberpunk 2077", header_image_url: null },
    ]);

    fireEvent.click(pressed);
    expect(window.localStorage.getItem("steamscoop_favorite_games")).toBe("[]");
  });

  it("gracefully displays placeholder when game has no header image or missing release date", () => {
    const gameWithoutImage: GameItem = {
      id: "game-3",
      steam_app_id: 9999,
      name: "Indie Prototype",
      genres: [],
      catalog_status: "pending",
      header_image_url: null,
      release_date: null,
    };

    render(
      <RouterProvider initialPath="/">
        <GameCard game={gameWithoutImage} />
      </RouterProvider>
    );

    expect(screen.getByText("Indie Prototype")).toBeInTheDocument();
    expect(screen.getByText("No Image Available")).toBeInTheDocument();
    expect(screen.getByText("TBA / Unavailable")).toBeInTheDocument();
    expect(screen.getByText("No genres listed")).toBeInTheDocument();
  });

  it("displays custom empty search state with query and reset button", () => {
    const handleReset = vi.fn();

    render(
      <GameCatalogGrid
        games={[]}
        isLoading={false}
        error={null}
        onRetry={vi.fn()}
        activeSearchQuery="NonexistentGame12345"
        onResetFilters={handleReset}
      />
    );

    expect(
      screen.getByText('No results for "NonexistentGame12345"')
    ).toBeInTheDocument();

    const resetBtn = screen.getByRole("button", { name: "Reset All Filters" });
    fireEvent.click(resetBtn);
    expect(handleReset).toHaveBeenCalledTimes(1);
  });

  it("renders loading skeleton during catalog loading state", () => {
    render(
      <GameCatalogGrid
        games={undefined}
        isLoading={true}
        error={null}
        onRetry={vi.fn()}
      />
    );

    expect(screen.getByLabelText("Loading games")).toBeInTheDocument();
  });

  it("renders ErrorAlert with retry trigger when API fails", () => {
    const handleRetry = vi.fn();
    const testError = new Error("503 Service Unavailable");

    render(
      <GameCatalogGrid
        games={undefined}
        isLoading={false}
        error={testError}
        onRetry={handleRetry}
      />
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Could not load game catalog")).toBeInTheDocument();
    expect(screen.getByText("503 Service Unavailable")).toBeInTheDocument();

    const retryBtn = screen.getByRole("button", { name: /Retry/i });
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it("handles pagination navigation buttons", () => {
    const handleNext = vi.fn();
    const handlePrev = vi.fn();

    render(
      <RouterProvider initialPath="/">
        <GameCatalogGrid
          games={mockGames}
          isLoading={false}
          error={null}
          onRetry={vi.fn()}
          pagination={{ has_more: true, next_cursor: "cur_token_next", total_count: 50 }}
          onNextPage={handleNext}
          onPrevPage={handlePrev}
          hasPrevPage={true}
          currentPage={2}
        />
      </RouterProvider>
    );

    expect(screen.getByText(/Page 2 • Showing 2 titles/i)).toBeInTheDocument();
    expect(screen.getByText(/Total:/i)).toBeInTheDocument();
    expect(screen.getByText("50")).toBeInTheDocument();

    const nextBtn = screen.getByRole("button", { name: /Next Page/i });
    fireEvent.click(nextBtn);
    expect(handleNext).toHaveBeenCalledTimes(1);

    const prevBtn = screen.getByRole("button", { name: /Previous Page/i });
    fireEvent.click(prevBtn);
    expect(handlePrev).toHaveBeenCalledTimes(1);
  });
});
