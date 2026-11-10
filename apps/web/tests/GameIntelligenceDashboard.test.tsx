import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, Routes, Route } from "../src/app/router/Router";
import { AnalyticsFilterBar } from "../src/features/intelligence/components/AnalyticsFilterBar";
import { ReviewActivityChart } from "../src/components/charts/ReviewActivityChart";
import { AnalyticalSummaryCard } from "../src/features/intelligence/components/AnalyticalSummaryCard";
import { DashboardMethodologyFooter } from "../src/features/intelligence/components/DashboardMethodologyFooter";
import { GameOverviewPage } from "../src/pages/GameOverviewPage";
import {
  GameOverviewData,
} from "../src/features/games/types/game";
import {
  AnalyticsPoint,
  GameAspectsData,
  GameTopicsData,
  SentimentDistributionData,
} from "../src/features/intelligence/types/intelligence";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const mockOverview: GameOverviewData = {
  game: {
    id: "game_portal_2",
    steam_app_id: 620,
    name: "Portal 2",
    title: "Portal 2",
    catalog_status: "indexed",
    developer: "Valve",
    publisher: "Valve",
    genres: ["Puzzle", "Action"],
    release_date: "2011-04-19",
    review_count: 150000,
  },
  steam_recommendations: {
    total_reviews: 150000,
    positive_reviews: 147000,
    negative_reviews: 3000,
    positive_percentage: 98.0,
  },
  model_sentiment: {
    total_classified: 140000,
    positive_count: 126000,
    negative_count: 8000,
    neutral_count: 6000,
    positive_rate: 0.90,
    negative_rate: 0.057,
    neutral_rate: 0.043,
    model_version: "roberta-sentiment-v1",
  },
  coverage: {
    total_reviews_collected: 10000,
    steam_total_reviews: 150000,
    coverage_percentage: 6.67,
  },
};

const mockPoints: AnalyticsPoint[] = [
  {
    period_start: "2026-10-01",
    period_end: "2026-10-07",
    review_count: 1200,
    positive_count: 1050,
    negative_count: 100,
    neutral_count: 50,
    steam_recommended_count: 1150,
    steam_not_recommended_count: 50,
    sentiment_score: 0.79,
  },
  {
    period_start: "2026-10-08",
    period_end: "2026-10-14",
    review_count: 1300,
    positive_count: 1100,
    negative_count: 120,
    neutral_count: 80,
    steam_recommended_count: 1220,
    steam_not_recommended_count: 80,
    sentiment_score: 0.75,
  },
];

const mockAspects: GameAspectsData = {
  game_id: "game_portal_2",
  taxonomy_version: "aspects-v1.0",
  model_version: "absa-roberta-v1",
  aspects: [
    {
      aspect_key: "gameplay",
      display_name: "Puzzle & Gameplay Mechanics",
      mention_count: 850,
      positive_count: 800,
      negative_count: 30,
      neutral_count: 20,
      positive_rate: 0.941,
      negative_rate: 0.035,
      neutral_rate: 0.024,
      sentiment_score: 0.91,
      prevalence: 0.65,
    },
    {
      aspect_key: "story",
      display_name: "Narrative & Dialogue",
      mention_count: 620,
      positive_count: 590,
      negative_count: 15,
      neutral_count: 15,
      positive_rate: 0.952,
      negative_rate: 0.024,
      neutral_rate: 0.024,
      sentiment_score: 0.93,
      prevalence: 0.48,
    },
    {
      aspect_key: "coop",
      display_name: "Co-op & Multiplayer",
      mention_count: 410,
      positive_count: 340,
      negative_count: 50,
      neutral_count: 20,
      positive_rate: 0.829,
      negative_rate: 0.122,
      neutral_rate: 0.049,
      sentiment_score: 0.71,
      prevalence: 0.32,
    },
  ],
  total_aspect_mentions: 1880,
  unique_reviews_with_aspects: 1100,
};

const mockTopics: GameTopicsData = {
  game_id: "game_portal_2",
  model_version: "bertopic-v1.0",
  topics: [
    {
      topic_key: "portal_puzzles",
      label: "Co-op Puzzles & GLaDOS Humor",
      review_count: 550,
      prevalence: 0.42,
      avg_score: 0.92,
      is_outlier: false,
      keywords: ["glados", "wheatley", "puzzles", "coop"],
    },
    {
      topic_key: "level_editor",
      label: "Community Workshop & Level Editor",
      review_count: 280,
      prevalence: 0.21,
      avg_score: 0.84,
      is_outlier: false,
      keywords: ["workshop", "maps", "editor", "custom"],
    },
  ],
  total_assigned_reviews: 830,
  outlier_count: 70,
  outlier_rate: 0.078,
};

const mockSentiment: SentimentDistributionData = {
  game_id: "game_portal_2",
  model_version: "roberta-sentiment-v1",
  total_reviews: 10000,
  classified_count: 9500,
  unclassified_count: 500,
  positive_count: 8550,
  negative_count: 570,
  neutral_count: 380,
  positive_rate: 0.90,
  negative_rate: 0.06,
  neutral_rate: 0.04,
  coverage_rate: 0.95,
  unclassified_rate: 0.05,
  sentiment_score: 0.84,
  timeline: mockPoints,
};

describe("Game Intelligence Dashboard Components", () => {
  describe("AnalyticsFilterBar", () => {
    it("renders presets and triggers callback when selected", () => {
      const handleFilterChange = vi.fn();
      render(
        <AnalyticsFilterBar
          onFilterChange={handleFilterChange}
        />
      );

      expect(screen.getByRole("group", { name: /Date range presets/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "All Time" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "30 Days" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "90 Days" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "1 Year" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Custom Range" })).toBeInTheDocument();

      // Click 30 Days preset
      fireEvent.click(screen.getByRole("button", { name: "30 Days" }));
      expect(handleFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({
          preset: "30d",
          period: "week",
          from: expect.any(String),
          to: expect.any(String),
        })
      );
    });

    it("changes aggregation period bucket", () => {
      const handleFilterChange = vi.fn();
      render(<AnalyticsFilterBar onFilterChange={handleFilterChange} />);

      const select = screen.getByLabelText(/Analytics aggregation period/i);
      fireEvent.change(select, { target: { value: "month" } });

      expect(handleFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({
          period: "month",
        })
      );
    });

    it("validates custom range dates", () => {
      const handleFilterChange = vi.fn();
      render(<AnalyticsFilterBar onFilterChange={handleFilterChange} />);

      // Switch to custom
      fireEvent.click(screen.getByRole("button", { name: "Custom Range" }));

      const startDateInput = screen.getByLabelText(/Start Date/i);
      const endDateInput = screen.getByLabelText(/End Date/i);
      const applyBtn = screen.getByRole("button", { name: /Apply Range/i });

      // Put invalid dates: start after end
      fireEvent.change(startDateInput, { target: { value: "2026-12-01" } });
      fireEvent.change(endDateInput, { target: { value: "2026-01-01" } });
      fireEvent.click(applyBtn);

      expect(screen.getByText(/Start date cannot be after end date/i)).toBeInTheDocument();
      expect(handleFilterChange).not.toHaveBeenCalled();

      // Put valid dates
      fireEvent.change(startDateInput, { target: { value: "2026-01-01" } });
      fireEvent.change(endDateInput, { target: { value: "2026-12-01" } });
      fireEvent.click(applyBtn);

      expect(handleFilterChange).toHaveBeenCalledWith({
        preset: "custom",
        period: "week",
        from: "2026-01-01",
        to: "2026-12-01",
      });
    });
  });

  describe("ReviewActivityChart", () => {
    it("renders chart with title and point summaries", () => {
      render(
        <ReviewActivityChart
          points={mockPoints}
          period="week"
        />
      );

      expect(
        screen.getByText("Review Activity & Community Sentiment Volume")
      ).toBeInTheDocument();
      expect(screen.getByText(/Total interval volume:/i)).toBeInTheDocument();
      expect(screen.getByText(/2[.,]500/)).toBeInTheDocument();
    });

    it("toggles to accessible data table with volume and net scores", () => {
      render(
        <ReviewActivityChart
          points={mockPoints}
          period="week"
        />
      );

      const tableToggle = screen.getByRole("button", {
        name: /Switch to accessible data table/i,
      });
      fireEvent.click(tableToggle);

      expect(screen.getByRole("table")).toBeInTheDocument();
      expect(screen.getByText("2026-10-01 to 2026-10-07")).toBeInTheDocument();
      expect(screen.getAllByText(/rec \/.*not rec/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Score: 0.79")).toBeInTheDocument();
    });

    it("handles empty points cleanly", () => {
      render(<ReviewActivityChart points={[]} />);
      expect(
        screen.getByText(/No review activity recorded for this period/i)
      ).toBeInTheDocument();
    });
  });

  describe("AnalyticalSummaryCard", () => {
    it("synthesizes divergence, top aspect, and core topic", () => {
      render(
        <AnalyticalSummaryCard
          overview={mockOverview}
          sentiment={mockSentiment}
          aspects={mockAspects}
          topics={mockTopics}
        />
      );

      expect(screen.getByText("Synthesized Intelligence Summary")).toBeInTheDocument();
      expect(screen.getByText(/Steam recommendations sit at/i)).toBeInTheDocument();
      expect(screen.getByText("98.0%")).toBeInTheDocument();
      expect(screen.getByText("90.0%")).toBeInTheDocument();

      // Leading aspect
      expect(screen.getByText("Narrative & Dialogue")).toBeInTheDocument();
      expect(screen.getByText(/95% positive/i)).toBeInTheDocument();

      // Top topic
      expect(screen.getByText("Co-op Puzzles & GLaDOS Humor")).toBeInTheDocument();
      expect(screen.getByText(/42\.0%/i)).toBeInTheDocument();
    });

    it("displays low sample warning alert when reviews are under 30", () => {
      const lowOverview: GameOverviewData = {
        ...mockOverview,
        coverage: {
          total_reviews_collected: 14,
          steam_total_reviews: 50,
          coverage_percentage: 28.0,
        },
      };

      render(
        <AnalyticalSummaryCard
          overview={lowOverview}
          sentiment={{ ...mockSentiment, total_reviews: 14 }}
        />
      );

      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/Low Sample Size Alert/i)).toBeInTheDocument();
      expect(screen.getByText("14")).toBeInTheDocument();
    });
  });

  describe("DashboardMethodologyFooter", () => {
    it("renders mathematical metric formulations, model badges, and methodology link", () => {
      render(
        <RouterProvider initialPath="/games/game_portal_2">
          <DashboardMethodologyFooter
            sentimentModelVersion="sentiment-v2"
            taxonomyVersion="aspects-v1.0"
            topicModelVersion="bertopic-v1"
            totalCollected={5000}
          />
        </RouterProvider>
      );

      expect(screen.getByText(/Mathematical Metric Formulations/i)).toBeInTheDocument();
      expect(screen.getByText("Steam Recommendation Rate")).toBeInTheDocument();
      expect(screen.getByText("Model Positive Sentiment Rate")).toBeInTheDocument();
      expect(screen.getByText("Net Sentiment Score")).toBeInTheDocument();
      expect(screen.getByText("Aspect Prevalence")).toBeInTheDocument();
      expect(screen.getByText("Sample Coverage Ratio")).toBeInTheDocument();

      expect(screen.getByText(/Sentiment: sentiment-v2/i)).toBeInTheDocument();
      expect(screen.getByText(/ABSA: aspects-v1.0/i)).toBeInTheDocument();
      expect(screen.getByText(/Topics: bertopic-v1/i)).toBeInTheDocument();

      const methodologyLink = screen.getByRole("link", {
        name: /Full Methodology Documentation/i,
      });
      expect(methodologyLink).toBeInTheDocument();
      expect(methodologyLink).toHaveAttribute("href", "/methodology");
    });

    it("displays insufficient data warning if totalCollected < 30", () => {
      render(
        <RouterProvider initialPath="/games/game_portal_2">
          <DashboardMethodologyFooter
            sentimentModelVersion="sentiment-v1"
            totalCollected={18}
          />
        </RouterProvider>
      );

      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/Insufficient Sample Size/i)).toBeInTheDocument();
    });
  });

  describe("GameOverviewPage Integration", () => {
    it("renders full dashboard with KPIs, charts, tabs, and filter bar", async () => {
      // Mock global fetch for API endpoints called in GameOverviewPage
      vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
        const urlStr = String(url);
        if (urlStr.includes("/overview")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ data: mockOverview, error: null, meta: {} }),
          } as Response);
        }
        if (urlStr.includes("/analytics")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              data: {
                game_id: "game_portal_2",
                period: "week",
                model_version: "roberta-sentiment-v1",
                points: mockPoints,
              },
              error: null,
              meta: {},
            }),
          } as Response);
        }
        if (urlStr.includes("/sentiment")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ data: mockSentiment, error: null, meta: {} }),
          } as Response);
        }
        if (urlStr.includes("/aspects")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ data: mockAspects, error: null, meta: {} }),
          } as Response);
        }
        if (urlStr.includes("/topics")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ data: mockTopics, error: null, meta: {} }),
          } as Response);
        }
        return Promise.reject(new Error(`Unhandled URL: ${urlStr}`));
      });

      const queryClient = createTestQueryClient();

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/games/game_portal_2">
            <Routes>
              <Route path="/games/:gameId" component={GameOverviewPage} />
            </Routes>
          </RouterProvider>
        </QueryClientProvider>
      );

      // Wait for overview query to resolve
      await waitFor(() => {
        expect(screen.getByText("Portal 2")).toBeInTheDocument();
      });

      // Verify Game Header Info
      expect(screen.getByText(/Developer:/i)).toBeInTheDocument();
      expect(screen.getAllByText("Valve").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Puzzle")).toBeInTheDocument();
      expect(screen.getByText(/App ID:/i)).toBeInTheDocument();
      expect(screen.getByText("620")).toBeInTheDocument();

      // Verify KPI Summary Cards
      expect(screen.getByText("Dataset Ingestion")).toBeInTheDocument();
      expect(screen.getAllByText(/10[.,]000/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Steam Recommended")).toBeInTheDocument();
      expect(screen.getAllByText("98.0%").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Model Positive Rate")).toBeInTheDocument();
      expect(screen.getAllByText("90.0%").length).toBeGreaterThanOrEqual(1);

      // Verify Synthesized Intelligence Summary Card
      expect(screen.getByText("Synthesized Intelligence Summary")).toBeInTheDocument();

      // Verify Temporal Activity & Volume Dynamics Chart & Filters
      expect(screen.getByText("Temporal Activity & Volume Dynamics")).toBeInTheDocument();
      expect(screen.getByRole("group", { name: /Date range presets/i })).toBeInTheDocument();

      // Verify Tabs: Sentiment, Aspects, Topics
      const aspectsTab = screen.getByRole("tab", { name: /Aspect Dimensions \(ABSA\)/i });
      expect(aspectsTab).toBeInTheDocument();
      fireEvent.click(aspectsTab);

      await waitFor(() => {
        expect(screen.getByText("Aspect-Based Sentiment Analysis (ABSA)")).toBeInTheDocument();
        expect(screen.getByText(/Top Discussed Dimensions/i)).toBeInTheDocument();
      });

      const topicsTab = screen.getByRole("tab", { name: /Recurring Topics/i });
      expect(topicsTab).toBeInTheDocument();
      fireEvent.click(topicsTab);

      await waitFor(() => {
        expect(screen.getByText("Topic Clustering & Recurring Themes")).toBeInTheDocument();
        expect(screen.getAllByText("Co-op Puzzles & GLaDOS Humor").length).toBeGreaterThanOrEqual(1);
      });

      // Verify Methodology Footer
      expect(screen.getByText(/Methodology, Metric Denominators & Provenance/i)).toBeInTheDocument();
    });
  });
});
