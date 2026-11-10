import React, { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartContainer, DataPoint } from "./ChartContainer";
import { COMPARISON_PALETTE } from "../../lib/tokens";

export interface GameComparisonPoint {
  gameTitle: string;
  steamRecommendationRate?: number | null; // 0-1
  modelSentimentRate?: number | null; // 0-1
  gameplaySatisfaction?: number | null; // 0-1 or -1 to 1
  performanceSatisfaction?: number | null;
  contentSatisfaction?: number | null;
}

export interface ComparisonRadarChartProps {
  data: GameComparisonPoint[] | null | undefined;
  title?: string;
  description?: string;
  height?: number | string;
  className?: string;
}

export const ComparisonRadarChart: React.FC<ComparisonRadarChartProps> = ({
  data,
  title = "Aspect Dimension Multi-Game Comparison",
  description = "Comparative dimensions across player recommendation, NLP sentiment, and design facets.",
  height = 360,
  className,
}) => {
  const empty = !data || data.length === 0;

  const chartOption = useMemo<EChartsOption>(() => {
    if (!data || data.length === 0) return {};

    const indicators = [
      { name: "Steam Rec. Rate", max: 100 },
      { name: "NLP Sentiment Rate", max: 100 },
      { name: "Gameplay", max: 100 },
      { name: "Performance", max: 100 },
      { name: "Story & Content", max: 100 },
    ];

    const seriesData = data.map((game, idx) => {
      const color = COMPARISON_PALETTE[idx % COMPARISON_PALETTE.length];

      // Convert rates to percentages [0, 100]. Do not generate synthetic values!
      // If a metric is null or undefined, pass 0 with explicit tooltip handling.
      const steamRecPct =
        game.steamRecommendationRate != null
          ? +(game.steamRecommendationRate <= 1.0
              ? game.steamRecommendationRate * 100
              : game.steamRecommendationRate
            ).toFixed(1)
          : 0;

      const nlpPct =
        game.modelSentimentRate != null
          ? +(game.modelSentimentRate <= 1.0
              ? game.modelSentimentRate * 100
              : game.modelSentimentRate
            ).toFixed(1)
          : 0;

      const gameplayPct =
        game.gameplaySatisfaction != null
          ? +(game.gameplaySatisfaction <= 1.0
              ? game.gameplaySatisfaction * 100
              : game.gameplaySatisfaction
            ).toFixed(1)
          : 0;

      const perfPct =
        game.performanceSatisfaction != null
          ? +(game.performanceSatisfaction <= 1.0
              ? game.performanceSatisfaction * 100
              : game.performanceSatisfaction
            ).toFixed(1)
          : 0;

      const contentPct =
        game.contentSatisfaction != null
          ? +(game.contentSatisfaction <= 1.0
              ? game.contentSatisfaction * 100
              : game.contentSatisfaction
            ).toFixed(1)
          : 0;

      return {
        value: [steamRecPct, nlpPct, gameplayPct, perfPct, contentPct],
        name: game.gameTitle,
        itemStyle: { color },
        areaStyle: {
          color: color.replace(")", ", 0.2)").replace("#", "rgba("),
          opacity: 0.25,
        },
      };
    });

    return {
      tooltip: {
        trigger: "item",
        formatter: (params: unknown) => {
          const item = params as { name: string; value: number[] };
          if (!item || !Array.isArray(item.value)) return "";
          return `
            <div class="font-sans text-xs">
              <div class="font-bold text-slate-200 border-b border-slate-700 pb-1 mb-1">${item.name}</div>
              <div>Steam Rec. Rate: <b>${item.value[0]}%</b></div>
              <div>NLP Sentiment Rate: <b>${item.value[1]}%</b></div>
              <div>Gameplay: <b>${item.value[2] > 0 ? `${item.value[2]}%` : "N/A (No data)"}</b></div>
              <div>Performance: <b>${item.value[3] > 0 ? `${item.value[3]}%` : "N/A (No data)"}</b></div>
              <div>Story & Content: <b>${item.value[4] > 0 ? `${item.value[4]}%` : "N/A (No data)"}</b></div>
            </div>
          `;
        },
      },
      legend: {
        data: data.map((g) => g.gameTitle),
        bottom: 0,
        textStyle: { color: "#94a3b8" },
      },
      radar: {
        indicator: indicators,
        shape: "circle",
        splitNumber: 4,
        axisName: {
          color: "#cbd5e1",
          fontSize: 11,
        },
        splitLine: {
          lineStyle: {
            color: "#1e293b",
          },
        },
        splitArea: {
          show: false,
        },
        axisLine: {
          lineStyle: {
            color: "#334155",
          },
        },
      },
      series: [
        {
          name: "Comparison",
          type: "radar",
          data: seriesData,
        },
      ],
    };
  }, [data]);

  const tabularData = useMemo<DataPoint[]>(() => {
    if (!data) return [];
    return data.map((d) => {
      const rec =
        d.steamRecommendationRate != null
          ? `${(d.steamRecommendationRate * 100).toFixed(1)}%`
          : "N/A";
      const nlp =
        d.modelSentimentRate != null
          ? `${(d.modelSentimentRate * 100).toFixed(1)}%`
          : "N/A";
      const gameplay =
        d.gameplaySatisfaction != null
          ? `${(d.gameplaySatisfaction * 100).toFixed(1)}%`
          : "N/A";
      const perf =
        d.performanceSatisfaction != null
          ? `${(d.performanceSatisfaction * 100).toFixed(1)}%`
          : "N/A";
      const content =
        d.contentSatisfaction != null
          ? `${(d.contentSatisfaction * 100).toFixed(1)}%`
          : "N/A";

      return {
        label: d.gameTitle,
        value: `Steam: ${rec} | NLP: ${nlp}`,
        secondaryValue: `Gameplay: ${gameplay} • Perf: ${perf} • Story: ${content}`,
      };
    });
  }, [data]);

  return (
    <ChartContainer
      title={title}
      description={description}
      option={chartOption}
      height={height}
      tabularData={tabularData}
      tabularHeaders={["Game Title", "Key Score Comparison", "Aspect Dimensions"]}
      empty={empty}
      className={className}
    />
  );
};
