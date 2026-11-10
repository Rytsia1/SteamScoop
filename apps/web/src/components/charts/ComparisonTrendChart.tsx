import React, { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartContainer, DataPoint } from "./ChartContainer";
import { COMPARISON_PALETTE } from "../../lib/tokens";

export interface GameTrendSeries {
  gameTitle: string;
  points: { date: string; score: number }[];
}

export interface ComparisonTrendChartProps {
  series: GameTrendSeries[];
  title?: string;
  description?: string;
  height?: number | string;
  className?: string;
}

export const ComparisonTrendChart: React.FC<ComparisonTrendChartProps> = ({
  series,
  title = "Longitudinal Sentiment Trajectory Comparison",
  description = "Timeline comparison of calibrated net sentiment scores across evaluated games.",
  height = 340,
  className,
}) => {
  const empty = !series || series.length === 0 || series.every((s) => s.points.length === 0);

  const chartOption = useMemo<EChartsOption>(() => {
    if (empty) return {};

    // Collect all unique sorted dates
    const dateSet = new Set<string>();
    series.forEach((s) => s.points.forEach((p) => dateSet.add(p.date)));
    const allDates = Array.from(dateSet).sort();

    const eSeries = series.map((s, idx) => {
      const color = COMPARISON_PALETTE[idx % COMPARISON_PALETTE.length];
      const dateMap = new Map(s.points.map((p) => [p.date, p.score]));
      const scores = allDates.map((d) => (dateMap.has(d) ? +(dateMap.get(d)!).toFixed(2) : null));

      return {
        name: s.gameTitle,
        type: "line" as const,
        smooth: true,
        connectNulls: true,
        showSymbol: true,
        symbolSize: 6,
        data: scores,
        itemStyle: { color },
        lineStyle: { width: 2.5, color },
      };
    });

    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "cross" },
        formatter: (params: unknown) => {
          if (!Array.isArray(params)) return "";
          const first = params[0] as { name: string };
          const lines = params.map(
            (p: { marker: string; seriesName: string; value: number | null }) =>
              `<div>${p.marker} ${p.seriesName}: <b>${p.value != null ? p.value : "N/A"}</b></div>`
          );
          return `
            <div class="font-sans text-xs">
              <div class="font-semibold text-slate-300 border-b border-slate-700 pb-1 mb-1">
                Period: ${first.name}
              </div>
              ${lines.join("")}
            </div>
          `;
        },
      },
      legend: {
        data: series.map((s) => s.gameTitle),
        bottom: 0,
        textStyle: { color: "#94a3b8" },
      },
      xAxis: {
        type: "category",
        data: allDates,
        axisLine: { lineStyle: { color: "#334155" } },
        axisLabel: { color: "#94a3b8", fontSize: 11 },
      },
      yAxis: {
        type: "value",
        name: "Net Score (-1.0 to +1.0)",
        min: -1.0,
        max: 1.0,
        interval: 0.5,
        axisLabel: { formatter: "{value}", color: "#94a3b8" },
        splitLine: { lineStyle: { color: "#1e293b", type: "dashed" } },
      },
      series: eSeries,
    };
  }, [series, empty]);

  const tabularData = useMemo<DataPoint[]>(() => {
    if (empty) return [];
    return series.map((s) => {
      const avg =
        s.points.length > 0
          ? (s.points.reduce((acc, curr) => acc + curr.score, 0) / s.points.length).toFixed(2)
          : "N/A";

      return {
        label: s.gameTitle,
        value: `Avg Score: ${avg}`,
        secondaryValue: `${s.points.length} evaluation intervals`,
      };
    });
  }, [series, empty]);

  return (
    <ChartContainer
      title={title}
      description={description}
      option={chartOption}
      height={height}
      tabularData={tabularData}
      tabularHeaders={["Game Title", "Average Temporal Net Score", "Timeline Span"]}
      empty={empty}
      emptyMessage="No longitudinal trend points recorded for the selected comparison window."
      className={className}
    />
  );
};
