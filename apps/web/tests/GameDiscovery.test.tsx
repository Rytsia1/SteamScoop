import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GameSearchFilters } from "../src/features/games/components/GameSearchFilters";
import { GameCatalogGrid } from "../src/features/games/components/GameCatalogGrid";
import { GameCard } from "../src/features/games/components/GameCard";
import { GameItem } from "../src/features/games/types/game";
import { RouterProvider } from "../src/app/router/Router";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

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
  it("renders search input and triggers search query change", () => {
    const handleSearchChange = vi.fn();
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <GameSearchFilters
          searchQuery=""
          onSearchChange={handleSearchChange}
          statusFilter="indexed"
          onStatusChange={vi.fn()}
          genreFilter=""
          onGenreChange={vi.fn()}
          sortOption="name_asc"
          onSortChange={vi.fn()}
          onReset={vi.fn()}
        />
      </QueryClientProvider>
    );

    const searchInput = screen.getByRole("combobox", {
      name: /Search Game by Name or Steam App ID/i,
    });
    expect(searchInput).toBeInTheDocument();

    fireEvent.change(searchInput, { target: { value: "Portal" } });
    expect(handleSearchChange).toHaveBeenCalledWith("Portal");
  });

  it("handles genre button toggle in search filters", () => {
    const handleGenreChange = vi.fn();
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <GameSearchFilters
          searchQuery=""
          onSearchChange={vi.fn()}
          statusFilter="indexed"
          onStatusChange={vi.fn()}
          genreFilter=""
          onGenreChange={handleGenreChange}
          sortOption="name_asc"
          onSortChange={vi.fn()}
          onReset={vi.fn()}
        />
      </QueryClientProvider>
    );

    const rpgBtn = screen.getByRole("button", { name: "RPG" });
    fireEvent.click(rpgBtn);
    expect(handleGenreChange).toHaveBeenCalledWith("RPG");
  });

  it("handles sort option changes", () => {
    const handleSortChange = vi.fn();
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <GameSearchFilters
          searchQuery=""
          onSearchChange={vi.fn()}
          statusFilter="indexed"
          onStatusChange={vi.fn()}
          genreFilter=""
          onGenreChange={vi.fn()}
          sortOption="name_asc"
          onSortChange={handleSortChange}
          onReset={vi.fn()}
        />
      </QueryClientProvider>
    );

    const sortSelect = screen.getByLabelText(/Sort Catalog By/i);
    fireEvent.change(sortSelect, { target: { value: "recently_updated" } });
    expect(handleSortChange).toHaveBeenCalledWith("recently_updated");
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

