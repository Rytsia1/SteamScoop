import React, { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartContainer, DataPoint } from "./ChartContainer";
import { SENTIMENT_COLORS } from "../../lib/tokens";

export interface SentimentTrendPoint {
  date: string;
  positiveRate: number;
  negativeRate: number;
  reviewCount: number;
}

export interface SentimentTrendChartProps {
  data: SentimentTrendPoint[] | null | undefined;
  title?: string;
  description?: string;
  height?: number | string;
  className?: string;
}

export const SentimentTrendChart: React.FC<SentimentTrendChartProps> = ({
  data,
  title = "Sentiment Trajectory Over Time",
  description = "Positive vs negative sentiment trends across collection intervals.",
  height = 300,
  className,
}) => {
  const empty = !data || data.length === 0;

  const chartOption = useMemo<EChartsOption>(() => {
    if (!data || data.length === 0) return {};

    const dates = data.map((d) => d.date);
    const positiveRates = data.map((d) => +(d.positiveRate * 100).toFixed(1));
    const negativeRates = data.map((d) => +(d.negativeRate * 100).toFixed(1));

    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "cross", label: { backgroundColor: "#1e293b" } },
        formatter: (params: unknown) => {
          if (!Array.isArray(params)) return "";
          const first = params[0] as { name: string; dataIndex: number };
          const item = data[first.dataIndex];
          const lines = params.map(
            (p: { marker: string; seriesName: string; value: number }) =>
              `<div>${p.marker} ${p.seriesName}: <b>${p.value}%</b></div>`
          );
          return `<div class="font-sans">
            <div class="font-semibold text-slate-300 pb-1 mb-1 border-b border-slate-700">${first.name} (Volume: ${item?.reviewCount ?? 0})</div>
            ${lines.join("")}
          </div>`;
        },
      },
      legend: {
        data: ["Positive Rate", "Negative Rate"],
        textStyle: { color: "#94a3b8" },
        bottom: 0,
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: dates,
        axisLine: { lineStyle: { color: "#334155" } },
        axisLabel: { color: "#94a3b8", fontSize: 11 },
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 100,
        axisLabel: { formatter: "{value}%", color: "#94a3b8", fontSize: 11 },
        splitLine: { lineStyle: { color: "#1e293b", type: "dashed" } },
      },
      series: [
        {
          name: "Positive Rate",
          type: "line",
          smooth: true,
          showSymbol: false,
          data: positiveRates,
          itemStyle: { color: SENTIMENT_COLORS.positive },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(16, 185, 129, 0.25)" },
                { offset: 1, color: "rgba(16, 185, 129, 0.0)" },
              ],
            },
          },
        },
        {
          name: "Negative Rate",
          type: "line",
          smooth: true,
          showSymbol: false,
          data: negativeRates,
          itemStyle: { color: SENTIMENT_COLORS.negative },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(244, 63, 94, 0.25)" },
                { offset: 1, color: "rgba(244, 63, 94, 0.0)" },
              ],
            },
          },
        },
      ],
    };
  }, [data]);

  const tabularData = useMemo<DataPoint[]>(() => {
    if (!data) return [];
    return data.map((d) => ({
      label: d.date,
      value: `+${(d.positiveRate * 100).toFixed(1)}% / -${(d.negativeRate * 100).toFixed(1)}%`,
      secondaryValue: `${d.reviewCount.toLocaleString()} reviews`,
    }));
  }, [data]);

  return (
    <ChartContainer
      title={title}
      description={description}
      option={chartOption}
      height={height}
      tabularData={tabularData}
      tabularHeaders={["Date", "Sentiment Split (+ / -)", "Sample Volume"]}
      empty={empty}
      className={className}
    />
  );
};

