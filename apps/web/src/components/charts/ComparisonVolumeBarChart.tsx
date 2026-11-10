import React, { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartContainer, DataPoint } from "./ChartContainer";
import { GameComparisonResult } from "../../features/comparison/types/comparison";

export interface ComparisonVolumeBarChartProps {
  games: GameComparisonResult[];
  title?: string;
  description?: string;
  height?: number | string;
  className?: string;
}

export const ComparisonVolumeBarChart: React.FC<ComparisonVolumeBarChartProps> = ({
  games,
  title = "Review Volume & Sentiment Ratio Benchmark",
  description = "Comparative sample volume alongside Steam positive recommendations and calibrated NLP sentiment rates.",
  height = 360,
  className,
}) => {
  const empty = !games || games.length === 0;

  const chartOption = useMemo<EChartsOption>(() => {
    if (!games || games.length === 0) return {};

    const titles = games.map((g) => g.title || g.name || "Unknown");
    const steamRecRates = games.map((g) => {
      if (g.steam_recommendation_rate != null) {
        const raw = g.steam_recommendation_rate;
        return +(raw <= 1.0 ? raw * 100 : raw).toFixed(1);
      }
      return null;
    });

    const modelRates = games.map((g) => {
      const raw = g.model_positive_rate ?? g.model_sentiment_rate;
      if (raw != null) {
        return +(raw <= 1.0 ? raw * 100 : raw).toFixed(1);
      }
      return null;
    });

    const reviewVolumes = games.map((g) => g.review_volume ?? 0);

    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: unknown) => {
          if (!Array.isArray(params)) return "";
          const first = params[0] as { dataIndex: number; name: string };
          const g = games[first.dataIndex];
          if (!g) return "";

          const recStr =
            g.steam_recommendation_rate != null
              ? `${(g.steam_recommendation_rate * 100).toFixed(1)}%`
              : "N/A (Missing data)";
          const nlpStr =
            (g.model_positive_rate ?? g.model_sentiment_rate) != null
              ? `${(((g.model_positive_rate ?? g.model_sentiment_rate)!) * 100).toFixed(1)}%`
              : "N/A (Missing data)";

          return `
            <div class="font-sans text-xs">
              <div class="font-bold text-slate-200 border-b border-slate-700 pb-1 mb-1">${first.name}</div>
              <div class="text-slate-300">Sample Volume: <b>${g.review_volume?.toLocaleString() ?? 0}</b> reviews</div>
              <div class="text-emerald-400">&bull; Steam Recommendation: <b>${recStr}</b></div>
              <div class="text-sky-400">&bull; Model NLP Sentiment: <b>${nlpStr}</b></div>
            </div>
          `;
        },
      },
      legend: {
        data: ["Steam Recommendation %", "Model Sentiment %", "Review Sample Volume"],
        bottom: 0,
        textStyle: { color: "#94a3b8" },
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "12%",
        top: "10%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        data: titles,
        axisLine: { lineStyle: { color: "#334155" } },
        axisLabel: { color: "#cbd5e1", fontSize: 11 },
      },
      yAxis: [
        {
          type: "value",
          name: "Percentage",
          min: 0,
          max: 100,
          position: "left",
          axisLabel: { formatter: "{value}%", color: "#94a3b8" },
          splitLine: { lineStyle: { color: "#1e293b", type: "dashed" } },
        },
        {
          type: "value",
          name: "Volume (Reviews)",
          min: 0,
          position: "right",
          axisLabel: { color: "#94a3b8" },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: "Steam Recommendation %",
          type: "bar" as const,
          yAxisIndex: 0,
          data: steamRecRates,
          itemStyle: { color: "#10b981" },
        },
        {
          name: "Model Sentiment %",
          type: "bar" as const,
          yAxisIndex: 0,
          data: modelRates,
          itemStyle: { color: "#38bdf8" },
        },
        {
          name: "Review Sample Volume",
          type: "line" as const,
          yAxisIndex: 1,
          smooth: true,
          showSymbol: true,
          symbolSize: 7,
          data: reviewVolumes,
          itemStyle: { color: "#a855f7" },
          lineStyle: { width: 2, color: "#a855f7" },
        },
      ],
    };
  }, [games]);

  const tabularData = useMemo<DataPoint[]>(() => {
    if (!games) return [];
    return games.map((g) => {
      const rec =
        g.steam_recommendation_rate != null
          ? `${(g.steam_recommendation_rate * 100).toFixed(1)}%`
          : "N/A";
      const nlp =
        (g.model_positive_rate ?? g.model_sentiment_rate) != null
          ? `${(((g.model_positive_rate ?? g.model_sentiment_rate)!) * 100).toFixed(1)}%`
          : "N/A";
      const vol = g.review_volume?.toLocaleString() ?? "0";

      return {
        label: g.title || g.name || "Game",
        value: `Steam: ${rec} | NLP: ${nlp}`,
        secondaryValue: `${vol} reviews sample`,
      };
    });
  }, [games]);

  return (
    <ChartContainer
      title={title}
      description={description}
      option={chartOption}
      height={height}
      tabularData={tabularData}
      tabularHeaders={["Game Title", "Sentiment Split (Steam vs NLP)", "Analyzed Sample"]}
      empty={empty}
      className={className}
    />
  );
};
