import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GameCard } from "../src/features/games/components/GameCard";
import { GameSearchFilters } from "../src/features/games/components/GameSearchFilters";
import { ReviewCard } from "../src/features/reviews/components/ReviewCard";
import { GameItem } from "../src/features/games/types/game";
import { ReviewItem } from "../src/features/reviews/types/review";
import { RouterProvider } from "../src/app/router/Router";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const mockGame: GameItem = {
  id: "game_uuid_1",
  steam_app_id: 570,
  name: "Dota 2",
  title: "Dota 2",
  slug: "dota-2",
  catalog_status: "indexed",
  developer: "Valve",
  publisher: "Valve",
  genres: ["Action", "Strategy"],
  tags: ["MOBA", "Competitive"],
  review_count: 50000,
  steam_positive_percentage: 82.5,
  model_sentiment_positive_rate: 0.79,
};

const mockReview: ReviewItem = {
  id: "review_uuid_1",
  steam_review_id: 12345678,
  review_text: "Incredible game mechanics and deep strategic depth. Highly recommended!",
  language: "english",
  voted_up: true,
  votes_up: 120,
  votes_funny: 5,
  comment_count: 12,
  steam_playtime_forever: 6000, // 100 hours
  sentiment: {
    label: "positive",
    confidence: 0.94,
    model_version: "sentiment-lr-v1",
  },
};

describe("Game Feature Components", () => {
  it("renders GameCard with title, app id, status, and metrics", () => {
    render(
      <RouterProvider initialPath="/">
        <GameCard game={mockGame} />
      </RouterProvider>
    );

    expect(screen.getByText("Dota 2")).toBeInTheDocument();
    expect(screen.getByText(/App\s*(#|ID:)\s*570/i)).toBeInTheDocument();
    expect(screen.getByText("INDEXED")).toBeInTheDocument();
    expect(screen.getByText("83%")).toBeInTheDocument(); // 82.5 formatted
    expect(screen.getByText("79%")).toBeInTheDocument(); // 0.79 formatted
    expect(screen.getByText(/50[.,]000 reviews collected/i)).toBeInTheDocument();
  });

  it("handles GameSearchFilters interactions", () => {
    const handleSearchChange = vi.fn();
    const handleStatusChange = vi.fn();
    const handleGenreChange = vi.fn();
    const handleSortChange = vi.fn();
    const handleReset = vi.fn();
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <GameSearchFilters
          searchQuery="Half-Life"
          onSearchChange={handleSearchChange}
          statusFilter="indexed"
          onStatusChange={handleStatusChange}
          genreFilter="Action"
          onGenreChange={handleGenreChange}
          priceFilter=""
          onPriceChange={vi.fn()}
          yearFrom=""
          onYearFromChange={vi.fn()}
          yearTo=""
          onYearToChange={vi.fn()}
          sortOption="name_asc"
          onSortChange={handleSortChange}
          hasActiveFilters={true}
          onReset={handleReset}
        />
      </QueryClientProvider>
    );

    const input = screen.getByLabelText(/Search Game by Name/i);
    expect(input).toHaveValue("Half-Life");

    const clearBtn = screen.getByRole("button", { name: /Reset Filters/i });
    fireEvent.click(clearBtn);
    expect(handleReset).toHaveBeenCalledTimes(1);
  });

  it("renders ReviewCard with recommendation status, playtime, and intelligence trigger", () => {
    const handleViewIntel = vi.fn();

    render(<ReviewCard review={mockReview} onViewIntelligence={handleViewIntel} />);

    expect(screen.getByText("Steam: Recommended")).toBeInTheDocument();
    expect(screen.getByText(/100\.0\s*hrs/i)).toBeInTheDocument();
    expect(screen.getByText("120 found helpful")).toBeInTheDocument();
    expect(screen.getByText(/Incredible game mechanics/i)).toBeInTheDocument();

    const intelBtn = screen.getByRole("button", { name: /Review Intelligence & Details/i });
    fireEvent.click(intelBtn);
    expect(handleViewIntel).toHaveBeenCalledWith(mockReview);
  });
});
