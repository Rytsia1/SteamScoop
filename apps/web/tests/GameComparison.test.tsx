import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GameSelector } from "../src/features/comparison/components/GameSelector";
import { ComparisonMetricsGrid } from "../src/features/comparison/components/ComparisonMetricsGrid";
import { ComparisonVolumeBarChart } from "../src/components/charts/ComparisonVolumeBarChart";
import { ComparisonTrendChart } from "../src/components/charts/ComparisonTrendChart";
import { ComparisonRadarChart } from "../src/components/charts/ComparisonRadarChart";
import { ComparisonTopicSection } from "../src/features/comparison/components/ComparisonTopicSection";
import { ComparisonMethodologyNotice } from "../src/features/comparison/components/ComparisonMethodologyNotice";
import { GameComparisonPage } from "../src/pages/GameComparisonPage";
import { GameItem } from "../src/features/games/types/game";
import { GameComparisonResult } from "../src/features/comparison/types/comparison";
import * as gamesApi from "../src/features/games/api/gamesApi";
import * as comparisonApi from "../src/features/comparison/api/comparisonApi";
import * as intelligenceApi from "../src/features/intelligence/api/intelligenceApi";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const mockCatalogGames: GameItem[] = [
  {
    id: "game_uuid_1",
    steam_app_id: 1086940,
    name: "Baldur's Gate 3",
    title: "Baldur's Gate 3",
    slug: "baldurs-gate-3",
    catalog_status: "indexed",
    genres: ["RPG", "Strategy"],
    review_count: 500000,
    steam_positive_percentage: 96.0,
    model_sentiment_positive_rate: 0.94,
  },
  {
    id: "game_uuid_2",
    steam_app_id: 1091500,
    name: "Cyberpunk 2077",
    title: "Cyberpunk 2077",
    slug: "cyberpunk-2077",
    catalog_status: "indexed",
    genres: ["RPG", "Action"],
    review_count: 650000,
    steam_positive_percentage: 83.0,
    model_sentiment_positive_rate: 0.81,
  },
  {
    id: "game_uuid_3",
    steam_app_id: 1145360,
    name: "Hades",
    title: "Hades",
    slug: "hades",
    catalog_status: "indexed",
    genres: ["Action", "Roguelike"],
    review_count: 220000,
    steam_positive_percentage: 98.0,
    model_sentiment_positive_rate: 0.97,
  },
  {
    id: "game_uuid_4",
    steam_app_id: 1245620,
    name: "Elden Ring",
    title: "Elden Ring",
    slug: "elden-ring",
    catalog_status: "indexed",
    genres: ["Action", "RPG"],
    review_count: 800000,
    steam_positive_percentage: 92.0,
    model_sentiment_positive_rate: 0.89,
  },
];

const mockComparisonResults: GameComparisonResult[] = [
  {
    game_id: "game_uuid_1",
    name: "Baldur's Gate 3",
    title: "Baldur's Gate 3",
    steam_app_id: 1086940,
    review_volume: 5200,
    steam_recommendation_rate: 0.96,
    model_positive_rate: 0.94,
    sentiment_score: 0.88,
    aspect_sentiment: {
      gameplay: 0.92,
      performance: 0.85,
      story: 0.97,
    },
    model_version: "roberta-sentiment-v1",
  },
  {
    game_id: "game_uuid_2",
    name: "Cyberpunk 2077",
    title: "Cyberpunk 2077",
    steam_app_id: 1091500,
    review_volume: 4800,
    steam_recommendation_rate: 0.83,
    model_positive_rate: 0.81,
    sentiment_score: 0.62,
    aspect_sentiment: {
      gameplay: 0.84,
      performance: 0.68,
      story: 0.89,
    },
    model_version: "roberta-sentiment-v1",
  },
];

describe("Game Comparison Components & Visualizations", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("GameSelector", () => {
    it("renders selected games, available catalog items, and bounds counter", () => {
      const handleSelect = vi.fn();
      const handleRemove = vi.fn();

      render(
        <GameSelector
          availableGames={mockCatalogGames}
          selectedGameIds={["game_uuid_1", "game_uuid_2"]}
          onSelectGame={handleSelect}
          onRemoveGame={handleRemove}
        />
      );

      expect(screen.getByText("Select Games to Compare")).toBeInTheDocument();
      expect(screen.getByText("2 / 5 Selected")).toBeInTheDocument();

      // Selected chips
      expect(screen.getByText("Baldur's Gate 3")).toBeInTheDocument();
      expect(screen.getByText("Cyberpunk 2077")).toBeInTheDocument();

      // Unselected games available to add
      expect(screen.getByRole("button", { name: /Hades/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Elden Ring/i })).toBeInTheDocument();
    });

    it("triggers onSelectGame when adding a game and onRemoveGame when removing", () => {
      const handleSelect = vi.fn();
      const handleRemove = vi.fn();

      render(
        <GameSelector
          availableGames={mockCatalogGames}
          selectedGameIds={["game_uuid_1", "game_uuid_2"]}
          onSelectGame={handleSelect}
          onRemoveGame={handleRemove}
        />
      );

      // Add Hades
      const addHadesBtn = screen.getByRole("button", { name: /Hades/i });
      fireEvent.click(addHadesBtn);
      expect(handleSelect).toHaveBeenCalledWith("game_uuid_3");

      // Remove Baldur's Gate 3
      const removeBg3Btn = screen.getByRole("button", {
        name: /Remove Baldur's Gate 3 from comparison/i,
      });
      fireEvent.click(removeBg3Btn);
      expect(handleRemove).toHaveBeenCalledWith("game_uuid_1");
    });

    it("shows warning when fewer than 2 games are selected", () => {
      render(
        <GameSelector
          availableGames={mockCatalogGames}
          selectedGameIds={["game_uuid_1"]}
          onSelectGame={vi.fn()}
          onRemoveGame={vi.fn()}
        />
      );

      expect(screen.getByText("1 / 5 Selected")).toBeInTheDocument();
      expect(
        screen.getByText(/Please select at least 2 games to perform a valid comparison/i)
      ).toBeInTheDocument();
    });

    it("hides add picker when max bound of 5 games is reached", () => {
      const fiveIds = ["1", "2", "3", "4", "5"];
      const fiveGames: GameItem[] = fiveIds.map((id) => ({
        id,
        steam_app_id: 1000 + Number(id),
        name: `Game ${id}`,
        title: `Game ${id}`,
        slug: `game-${id}`,
        catalog_status: "indexed",
        genres: ["Action"],
      }));

      render(
        <GameSelector
          availableGames={fiveGames}
          selectedGameIds={fiveIds}
          onSelectGame={vi.fn()}
          onRemoveGame={vi.fn()}
        />
      );

      expect(screen.getByText("5 / 5 Selected")).toBeInTheDocument();
      expect(screen.queryByText(/Add from Indexed Catalog:/i)).not.toBeInTheDocument();
    });
  });

  describe("ComparisonMetricsGrid", () => {
    it("renders game KPI cards with correct metric representations", () => {
      render(<ComparisonMetricsGrid games={mockComparisonResults} />);

      expect(screen.getByText("Baldur's Gate 3")).toBeInTheDocument();
      expect(screen.getByText("Cyberpunk 2077")).toBeInTheDocument();

      // Sample reviews (locale resilient)
      expect(screen.getByText(/5[.,]200/)).toBeInTheDocument();
      expect(screen.getByText(/4[.,]800/)).toBeInTheDocument();

      // Steam recommendation percentages
      expect(screen.getByText("96.0%")).toBeInTheDocument();
      expect(screen.getByText("83.0%")).toBeInTheDocument();

      // Model sentiment percentages
      expect(screen.getByText("94.0%")).toBeInTheDocument();
      expect(screen.getByText("81.0%")).toBeInTheDocument();

      // Net Sentiment scores
      expect(screen.getByText("+0.88")).toBeInTheDocument();
      expect(screen.getByText("+0.62")).toBeInTheDocument();
    });

    it("displays warning badge for low sample games (N < 30)", () => {
      const lowSampleGame: GameComparisonResult = {
        game_id: "low_1",
        name: "Indie Prototype",
        title: "Indie Prototype",
        review_volume: 12,
        steam_recommendation_rate: 0.75,
        model_positive_rate: 0.67,
        sentiment_score: 0.34,
      };

      render(<ComparisonMetricsGrid games={[lowSampleGame]} />);

      expect(screen.getByText(/N < 30 Low Sample/i)).toBeInTheDocument();
    });
  });

  describe("ComparisonVolumeBarChart", () => {
    it("renders chart and provides accessible data table", () => {
      render(<ComparisonVolumeBarChart games={mockComparisonResults} />);

      expect(screen.getByText("Review Volume & Sentiment Ratio Benchmark")).toBeInTheDocument();

      // Toggle accessible table
      const tableToggle = screen.getByRole("button", { name: /Switch to accessible data table|View Table/i });
      fireEvent.click(tableToggle);

      expect(screen.getByRole("table")).toBeInTheDocument();
      expect(screen.getByText(/5[.,]200 reviews sample/)).toBeInTheDocument();
      expect(screen.getByText(/4[.,]800 reviews sample/)).toBeInTheDocument();
    });
  });

  describe("ComparisonTrendChart", () => {
    const mockSeries = [
      {
        gameTitle: "Baldur's Gate 3",
        points: [
          { date: "2024-01-01", score: 0.85 },
          { date: "2024-02-01", score: 0.91 },
        ],
      },
      {
        gameTitle: "Cyberpunk 2077",
        points: [
          { date: "2024-01-01", score: 0.55 },
          { date: "2024-02-01", score: 0.68 },
        ],
      },
    ];

    it("renders longitudinal trajectory comparison and accessible data table", () => {
      render(<ComparisonTrendChart series={mockSeries} />);

      expect(
        screen.getByText("Longitudinal Sentiment Trajectory Comparison")
      ).toBeInTheDocument();

      const tableToggle = screen.getByRole("button", { name: /Switch to accessible data table|View Table/i });
      fireEvent.click(tableToggle);

      expect(screen.getByRole("table")).toBeInTheDocument();
      expect(screen.getAllByText("2 evaluation intervals")).toHaveLength(2);
    });

    it("handles empty trend series gracefully", () => {
      render(<ComparisonTrendChart series={[]} />);

      expect(
        screen.getByText("No longitudinal trend points recorded for the selected comparison window.")
      ).toBeInTheDocument();
    });
  });

  describe("ComparisonRadarChart", () => {
    it("handles aspect dimensions without synthetic fallbacks", () => {
      const dataWithMissingAspects = [
        {
          gameTitle: "Baldur's Gate 3",
          steamRecommendationRate: 0.96,
          modelSentimentRate: 0.94,
          gameplaySatisfaction: 0.92,
          performanceSatisfaction: 0.85,
          contentSatisfaction: 0.97,
        },
        {
          gameTitle: "Game Without Aspects",
          steamRecommendationRate: 0.7,
          modelSentimentRate: 0.65,
          gameplaySatisfaction: null, // explicit null
          performanceSatisfaction: null,
          contentSatisfaction: null,
        },
      ];

      render(<ComparisonRadarChart data={dataWithMissingAspects} />);

      expect(screen.getByText("Aspect Dimension Multi-Game Comparison")).toBeInTheDocument();

      // Open accessible table to verify real values vs N/A (no synthetic 0.75!)
      const tableToggle = screen.getByRole("button", { name: /Switch to accessible data table|View Table/i });
      fireEvent.click(tableToggle);

      expect(screen.getByText("Steam: 96.0% | NLP: 94.0%")).toBeInTheDocument();
      expect(screen.getByText(/Gameplay: 92.0% • Perf: 85.0% • Story: 97.0%/i)).toBeInTheDocument();
      expect(screen.getByText(/Gameplay: N\/A • Perf: N\/A • Story: N\/A/i)).toBeInTheDocument();
    });
  });

  describe("ComparisonTopicSection", () => {
    it("renders side-by-side topics for games with valid clusters", () => {
      const mockTopicItems = [
        {
          gameId: "game_uuid_1",
          gameTitle: "Baldur's Gate 3",
          topicsData: {
            game_id: "game_uuid_1",
            model_version: "bertopic-v1",
            total_assigned_reviews: 4500,
            outlier_count: 500,
            outlier_rate: 0.1,
            topics: [
              {
                topic_key: "narrative_choices",
                label: "Narrative & Companions",
                review_count: 1800,
                prevalence: 0.42,
                avg_score: 0.85,
                keywords: ["dialogue", "choice", "astarion"],
                is_outlier: false,
              },
            ],
          },
        },
        {
          gameId: "game_uuid_2",
          gameTitle: "Cyberpunk 2077",
          topicsData: {
            game_id: "game_uuid_2",
            model_version: "bertopic-v1",
            total_assigned_reviews: 4000,
            outlier_count: 500,
            outlier_rate: 0.11,
            topics: [
              {
                topic_key: "night_city_visuals",
                label: "Night City Atmosphere",
                review_count: 1500,
                prevalence: 0.38,
                avg_score: 0.65,
                keywords: ["city", "graphics", "raytracing"],
                is_outlier: false,
              },
            ],
          },
        },
      ];

      render(<ComparisonTopicSection games={mockTopicItems} />);

      expect(screen.getByText("Community Discussion Clusters Comparison")).toBeInTheDocument();
      expect(screen.getByText("Narrative & Companions")).toBeInTheDocument();
      expect(screen.getByText("Night City Atmosphere")).toBeInTheDocument();
      expect(screen.getByText("42% prev.")).toBeInTheDocument();
      expect(screen.getByText("38% prev.")).toBeInTheDocument();
    });

    it("displays insufficient corpus safeguard when game has no topics", () => {
      const mockEmptyTopicItem = [
        {
          gameId: "game_uuid_low",
          gameTitle: "Low Review Game",
          topicsData: {
            game_id: "game_uuid_low",
            model_version: "bertopic-v1",
            total_assigned_reviews: 0,
            outlier_count: 10,
            outlier_rate: 1.0,
            topics: [],
          },
        },
      ];

      render(<ComparisonTopicSection games={mockEmptyTopicItem} />);

      expect(screen.getByText("Insufficient Corpus for Topics")).toBeInTheDocument();
      expect(screen.getByText(/requires an aggregated corpus of representative reviews/i)).toBeInTheDocument();
    });
  });

  describe("ComparisonMethodologyNotice", () => {
    it("displays harmonization status when models match and metric definitions table", () => {
      render(
        <ComparisonMethodologyNotice
          modelVersions={["roberta-sentiment-v1", "roberta-sentiment-v1"]}
          hasInsufficientDataGames={false}
        />
      );

      expect(
        screen.getByText(/All compared titles use compatible model version:/i)
      ).toBeInTheDocument();
      expect(screen.getByText("Consistent Metric Definitions")).toBeInTheDocument();
      expect(screen.getByText("Pos_Steam / (Pos_Steam + Neg_Steam)")).toBeInTheDocument();
      expect(screen.getByText("Pos_Count / Classified_Count")).toBeInTheDocument();
    });

    it("warns about calibration differences when incompatible models are compared", () => {
      render(
        <ComparisonMethodologyNotice
          modelVersions={["roberta-sentiment-v1", "baseline"]}
          hasInsufficientDataGames={true}
        />
      );

      expect(
        screen.getByText("Incompatible Model Versions Detected across Titles")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Direct score comparisons may reflect calibration differences/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/Sample Size Safeguard/i)).toBeInTheDocument();
    });
  });

  describe("GameComparisonPage Full Integration", () => {
    it("renders full comparison page with charts, metrics, date-range filter, and provenance", async () => {
      const queryClient = createTestQueryClient();

      vi.spyOn(gamesApi, "useGames").mockReturnValue({
        data: {
          items: mockCatalogGames,
          total: 4,
          page: 1,
          size: 50,
          pages: 1,
        },
        isLoading: false,
      } as unknown as ReturnType<typeof gamesApi.useGames>);

      vi.spyOn(comparisonApi, "useCompareGames").mockReturnValue({
        data: {
          games: mockComparisonResults,
          model_version: "roberta-sentiment-v1",
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as unknown as ReturnType<typeof comparisonApi.useCompareGames>);

      vi.spyOn(intelligenceApi, "fetchGameAnalytics").mockResolvedValue({
        game_id: "game_uuid_1",
        period: "week",
        model_version: "roberta-sentiment-v1",
        points: [
          {
            period_start: "2024-01-01",
            period_end: "2024-01-07",
            review_count: 100,
            positive_count: 90,
            negative_count: 10,
            neutral_count: 0,
            steam_recommended_count: 92,
            steam_not_recommended_count: 8,
            sentiment_score: 0.8,
          },
        ],
      });

      vi.spyOn(intelligenceApi, "fetchGameTopics").mockResolvedValue({
        game_id: "game_uuid_1",
        model_version: "bertopic-v1",
        total_assigned_reviews: 450,
        outlier_count: 50,
        outlier_rate: 0.1,
        topics: [
          {
            topic_key: "gameplay_mechanics",
            label: "Tactical Combat",
            review_count: 180,
            prevalence: 0.4,
            avg_score: 0.8,
            keywords: ["turn-based", "tactics", "rules"],
            is_outlier: false,
          },
        ],
      });

      render(
        <QueryClientProvider client={queryClient}>
          <GameComparisonPage />
        </QueryClientProvider>
      );

      // Page Title
      expect(screen.getByText("Benchmark Game Perception Across Titles")).toBeInTheDocument();

      // Range Presets
      expect(screen.getByRole("button", { name: "All Time" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "30 Days" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "90 Days" })).toBeInTheDocument();

      // Overview grid
      expect(screen.getByText("Comparative Overview & Core Metrics")).toBeInTheDocument();

      // Volume & sentiment chart
      expect(screen.getByText("Review Volume & Sentiment Ratio Benchmark")).toBeInTheDocument();

      // Methodology
      expect(
        screen.getByText("Comparative Methodology, Metric Definitions & Model Compatibility")
      ).toBeInTheDocument();

      // Date preset interaction
      const thirtyDaysBtn = screen.getByRole("button", { name: "30 Days" });
      fireEvent.click(thirtyDaysBtn);
      expect(thirtyDaysBtn).toHaveAttribute("aria-pressed", "true");
    });
  });
});
