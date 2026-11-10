import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, Routes, Route } from "../src/app/router/Router";
import { ReviewCard } from "../src/features/reviews/components/ReviewCard";
import { ReviewFilters } from "../src/features/reviews/components/ReviewFilters";
import { ReviewList } from "../src/features/reviews/components/ReviewList";
import { ReviewIntelligenceModal } from "../src/features/reviews/components/ReviewIntelligenceModal";
import { GameReviewsPage } from "../src/pages/GameReviewsPage";
import {
  ReviewDetailData,
  ReviewIntelligenceData,
  ReviewItem,
} from "../src/features/reviews/types/review";
import { GameItem } from "../src/features/games/types/game";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const mockGame: GameItem = {
  id: "game_portal_2",
  steam_app_id: 620,
  name: "Portal 2",
  title: "Portal 2",
  catalog_status: "indexed",
  developer: "Valve",
  publisher: "Valve",
  genres: ["Puzzle", "Action"],
  release_date: "2011-04-19",
};

const mockReview1: ReviewItem = {
  id: "rev_uuid_1",
  steam_review_id: 11223344,
  review_text:
    "Portal 2 is an absolute masterpiece of puzzle design and narrative delivery. The banter between GLaDOS and Wheatley keeps you laughing throughout every test chamber. Co-op mode is phenomenal with friends.",
  language: "english",
  voted_up: true,
  votes_up: 350,
  votes_funny: 42,
  comment_count: 18,
  steam_playtime_forever: 3600, // 60.0 hours
  steam_created_at: "2026-10-12T14:30:00Z",
  sentiment: {
    label: "positive",
    confidence: 0.96,
    model_version: "roberta-sentiment-v1",
  },
};

const mockReviewUnclassified: ReviewItem = {
  id: "rev_uuid_2",
  steam_review_id: 55667788,
  review_text: "Good game but keeps crashing on my Linux workstation after the latest patch.",
  language: "english",
  voted_up: false,
  votes_up: 12,
  votes_funny: 1,
  comment_count: 3,
  steam_playtime_forever: 420, // 7.0 hours
  steam_created_at: "2026-10-15T09:15:00Z",
  sentiment: null, // missing prediction / abstained
};

const mockReviewDetail: ReviewDetailData = {
  ...mockReview1,
  game_id: "game_portal_2",
  steam_playtime_at_review: 2400, // 40.0 hours
  steam_purchase: true,
  received_for_free: false,
  written_during_early_access: false,
  steam_updated_at: "2026-10-13T10:00:00Z",
  first_collected_at: "2026-10-14T02:00:00Z",
  last_seen_at: "2026-10-20T02:00:00Z",
};

const mockReviewIntel: ReviewIntelligenceData = {
  review_id: "rev_uuid_1",
  sentiment: {
    label: "positive",
    confidence: 0.96,
    model_version: "roberta-sentiment-v1",
  },
  aspects: [
    {
      aspect_key: "gameplay",
      display_name: "Puzzle & Gameplay Mechanics",
      sentiment: "positive",
      confidence: 0.98,
      evidence_text: "masterpiece of puzzle design",
    },
    {
      aspect_key: "story",
      display_name: "Narrative & Dialogue",
      sentiment: "positive",
      confidence: 0.95,
      evidence_text: "banter between GLaDOS and Wheatley keeps you laughing",
    },
    {
      aspect_key: "multiplayer",
      display_name: "Co-op & Multiplayer",
      sentiment: "positive",
      confidence: 0.92,
      evidence_text: "Co-op mode is phenomenal with friends",
    },
  ],
  topics: [
    {
      topic_id: "topic_uuid_101",
      topic_key: "portal_puzzles",
      label: "Co-op Puzzles & GLaDOS Humor",
      score: 0.94,
      model_version: "bertopic-v1.0",
      is_primary: true,
    },
  ],
};

describe("SteamScoop Review Explorer", () => {
  describe("ReviewCard", () => {
    it("renders Steam recommendation signal, model sentiment, and review date", () => {
      const handleViewIntel = vi.fn();
      render(<ReviewCard review={mockReview1} onViewIntelligence={handleViewIntel} />);

      // Distinction between Steam Recommendation and NLP Model Sentiment
      expect(screen.getByText("Steam: Recommended")).toBeInTheDocument();
      expect(screen.getByText(/NLP:\s*POSITIVE/i)).toBeInTheDocument();
      expect(screen.getByText(/\(96%\)/)).toBeInTheDocument();

      // Formatted Playtime & Language
      expect(screen.getByText(/60\.0\s*hrs/i)).toBeInTheDocument();
      expect(screen.getByText("english")).toBeInTheDocument();

      // Review Text & Helpful count
      expect(
        screen.getByText(/Portal 2 is an absolute masterpiece of puzzle design/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/350 found helpful/i)).toBeInTheDocument();
      expect(screen.getByText(/42 funny/i)).toBeInTheDocument();

      // Trigger detail view
      const detailBtn = screen.getByRole("button", {
        name: /Review Intelligence & Details/i,
      });
      fireEvent.click(detailBtn);
      expect(handleViewIntel).toHaveBeenCalledWith(mockReview1);
    });

    it("handles unclassified sentiment and negative Steam recommendations gracefully", () => {
      const handleViewIntel = vi.fn();
      render(
        <ReviewCard review={mockReviewUnclassified} onViewIntelligence={handleViewIntel} />
      );

      expect(screen.getByText("Steam: Not Recommended")).toBeInTheDocument();
      expect(screen.getByText("NLP: Unclassified")).toBeInTheDocument();
      expect(screen.getByText(/7\.0\s*hrs/i)).toBeInTheDocument();
      expect(screen.getByText(/keeps crashing on my Linux workstation/i)).toBeInTheDocument();
    });
  });

  describe("ReviewFilters", () => {
    it("triggers callbacks on filter adjustments and resets when requested", () => {
      const handleSentimentChange = vi.fn();
      const handleVotedUpChange = vi.fn();
      const handleAspectChange = vi.fn();
      const handleLanguageChange = vi.fn();
      const handleSortChange = vi.fn();
      const handleReset = vi.fn();

      render(
        <ReviewFilters
          sentiment="positive"
          onSentimentChange={handleSentimentChange}
          votedUp="true"
          onVotedUpChange={handleVotedUpChange}
          aspect="gameplay"
          onAspectChange={handleAspectChange}
          language="english"
          onLanguageChange={handleLanguageChange}
          sort="votes_up_desc"
          onSortChange={handleSortChange}
          onReset={handleReset}
        />
      );

      // Verify filter selects exist
      const sentimentSelect = screen.getByLabelText(/Filter by model sentiment/i);
      expect(sentimentSelect).toHaveValue("positive");
      fireEvent.change(sentimentSelect, { target: { value: "negative" } });
      expect(handleSentimentChange).toHaveBeenCalledWith("negative");

      const recSelect = screen.getByLabelText(/Filter by Steam recommendation/i);
      expect(recSelect).toHaveValue("true");
      fireEvent.change(recSelect, { target: { value: "false" } });
      expect(handleVotedUpChange).toHaveBeenCalledWith("false");

      const aspectSelect = screen.getByLabelText(/Filter by discussed aspect/i);
      expect(aspectSelect).toHaveValue("gameplay");
      fireEvent.change(aspectSelect, { target: { value: "performance" } });
      expect(handleAspectChange).toHaveBeenCalledWith("performance");

      const sortSelect = screen.getByLabelText(/Sort order/i);
      expect(sortSelect).toHaveValue("votes_up_desc");
      fireEvent.change(sortSelect, { target: { value: "created_at_desc" } });
      expect(handleSortChange).toHaveBeenCalledWith("created_at_desc");

      // Reset button should be visible when filters are active
      const resetBtn = screen.getByRole("button", { name: /Reset Filters/i });
      fireEvent.click(resetBtn);
      expect(handleReset).toHaveBeenCalledTimes(1);
    });
  });

  describe("ReviewList with Cursor Pagination", () => {
    it("renders reviews, empty state, and handles cursor pagination controls", () => {
      const handleNext = vi.fn();
      const handlePrev = vi.fn();
      const queryClient = createTestQueryClient();

      render(
        <QueryClientProvider client={queryClient}>
          <ReviewList
            reviews={[mockReview1, mockReviewUnclassified]}
            isLoading={false}
            error={null}
            onRetry={vi.fn()}
            pagination={{
              limit: 2,
              has_more: true,
              next_cursor: "cursor_batch_2_token",
              total_count: 50,
            }}
            onNextPage={handleNext}
            onPrevPage={handlePrev}
            hasPrevPage={true}
          />
        </QueryClientProvider>
      );

      expect(screen.getByRole("feed", { name: /Player reviews list/i })).toBeInTheDocument();
      expect(screen.getByText(/Total reviews:\s*50/i)).toBeInTheDocument();

      const nextBtn = screen.getByRole("button", { name: /Next review batch/i });
      fireEvent.click(nextBtn);
      expect(handleNext).toHaveBeenCalledTimes(1);

      const prevBtn = screen.getByRole("button", { name: /Previous review batch/i });
      fireEvent.click(prevBtn);
      expect(handlePrev).toHaveBeenCalledTimes(1);
    });

    it("displays EmptyState when no reviews match filters", () => {
      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <ReviewList
            reviews={[]}
            isLoading={false}
            error={null}
            onRetry={vi.fn()}
          />
        </QueryClientProvider>
      );

      expect(screen.getByText("No reviews match your filters")).toBeInTheDocument();
      expect(
        screen.getByText(/Try relaxing your sentiment, recommendation, or language filters/i)
      ).toBeInTheDocument();
    });
  });

  describe("ReviewIntelligenceModal (Detail View)", () => {
    it("renders complete review detail, aspect extractions, topic clusters, and privacy note", async () => {
      vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
        const urlStr = String(url);
        if (urlStr.includes("/intelligence")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ data: mockReviewIntel, error: null, meta: {} }),
          } as Response);
        }
        if (urlStr.includes("/reviews/")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ data: mockReviewDetail, error: null, meta: {} }),
          } as Response);
        }
        return Promise.reject(new Error(`Unhandled URL: ${urlStr}`));
      });

      const queryClient = createTestQueryClient();
      const handleClose = vi.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <ReviewIntelligenceModal
            review={mockReview1}
            isOpen={true}
            onClose={handleClose}
          />
        </QueryClientProvider>
      );

      // Title & Privacy Notice
      expect(screen.getByText("Review Intelligence & Metadata Details")).toBeInTheDocument();
      expect(
        screen.getByText(/Author profile data and personal SteamIDs are not stored or exposed/i)
      ).toBeInTheDocument();

      // Signals Comparison
      expect(screen.getByText("Steam Player Verdict")).toBeInTheDocument();
      expect(screen.getByText("Recommended (Thumbs Up)")).toBeInTheDocument();
      expect(screen.getByText("NLP Model Classification")).toBeInTheDocument();
      expect(screen.getByText(/96\.0%\s*conf\./i)).toBeInTheDocument();

      // Aspects (ABSA)
      await waitFor(() => {
        expect(screen.getByText(/Aspect-Level Predictions \(3\)/i)).toBeInTheDocument();
        expect(screen.getByText("Puzzle & Gameplay Mechanics")).toBeInTheDocument();
        expect(screen.getByText("Narrative & Dialogue")).toBeInTheDocument();
        expect(screen.getByText("Co-op & Multiplayer")).toBeInTheDocument();
        expect(screen.getAllByText(/masterpiece of puzzle design/i).length).toBeGreaterThanOrEqual(1);
      });

      // Topic Assignment
      expect(screen.getByText("Topic Clustering Assignment")).toBeInTheDocument();
      expect(screen.getByText("Co-op Puzzles & GLaDOS Humor")).toBeInTheDocument();
      expect(screen.getByText("Primary")).toBeInTheDocument();
      expect(screen.getByText("Score: 0.94")).toBeInTheDocument();

      // Close button
      const closeBtn = screen.getByRole("button", { name: "Close" });
      fireEvent.click(closeBtn);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it("handles missing aspect and topic predictions gracefully", async () => {
      vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
        const urlStr = String(url);
        if (urlStr.includes("/intelligence")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              data: {
                review_id: "rev_uuid_2",
                sentiment: null,
                aspects: [],
                topics: [],
              },
              error: null,
              meta: {},
            }),
          } as Response);
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            data: { ...mockReviewDetail, id: "rev_uuid_2", steam_review_id: 55667788 },
            error: null,
            meta: {},
          }),
        } as Response);
      });

      const queryClient = createTestQueryClient();

      render(
        <QueryClientProvider client={queryClient}>
          <ReviewIntelligenceModal
            review={mockReviewUnclassified}
            isOpen={true}
            onClose={vi.fn()}
          />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/No explicit design aspects detected above the confidence threshold/i)
        ).toBeInTheDocument();
        expect(
          screen.getByText(/Review was classified as an unclustered outlier or ambiguous topic/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe("GameReviewsPage Integration", () => {
    it("renders explorer page with URL search params filter synchronization", async () => {
      vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
        const urlStr = String(url);
        if (urlStr.includes("/games/game_portal_2/reviews")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              data: [mockReview1],
              error: null,
              meta: {
                pagination: {
                  limit: 15,
                  has_more: true,
                  next_cursor: "cursor_page_2",
                  total_count: 1500,
                },
              },
            }),
          } as Response);
        }
        if (urlStr.includes("/games/game_portal_2")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ data: mockGame, error: null, meta: {} }),
          } as Response);
        }
        return Promise.reject(new Error(`Unhandled URL: ${urlStr}`));
      });

      const queryClient = createTestQueryClient();

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/games/game_portal_2/reviews?sentiment=positive&sort=votes_up_desc">
            <Routes>
              <Route path="/games/:gameId/reviews" component={GameReviewsPage} />
            </Routes>
          </RouterProvider>
        </QueryClientProvider>
      );

      // Title & Game breadcrumb
      await waitFor(() => {
        expect(screen.getByText("Player Review Explorer")).toBeInTheDocument();
        expect(screen.getByText(/Back to Portal 2 Overview/i)).toBeInTheDocument();
      });

      // Filter state preserved from URL search params
      const sentimentSelect = screen.getByLabelText(/Filter by model sentiment/i);
      expect(sentimentSelect).toHaveValue("positive");

      const sortSelect = screen.getByLabelText(/Sort order/i);
      expect(sortSelect).toHaveValue("votes_up_desc");

      // Verify Review List
      expect(screen.getByText("Steam: Recommended")).toBeInTheDocument();
      expect(screen.getByText(/masterpiece of puzzle design/i)).toBeInTheDocument();
      expect(screen.getByText(/Total reviews:\s*1[.,]500/i)).toBeInTheDocument();
    });
  });
});
