import React, { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartContainer, DataPoint } from "./ChartContainer";
import { SENTIMENT_COLORS } from "../../lib/tokens";

export interface AspectMetricItem {
  aspect: string;
  mentionCount: number;
  positiveRate: number;
  negativeRate: number;
  neutralRate?: number;
}

export interface AspectBarChartProps {
  data: AspectMetricItem[] | null | undefined;
  title?: string;
  description?: string;
  height?: number | string;
  className?: string;
}

export const AspectBarChart: React.FC<AspectBarChartProps> = ({
  data,
  title = "Aspect-Based Sentiment Breakdown (ABSA)",
  description = "Player sentiment segmented across identified game design dimensions.",
  height = 340,
  className,
}) => {
  const empty = !data || data.length === 0;

  const sortedData = useMemo(() => {
    if (!data) return [];
    return [...data].sort((a, b) => b.mentionCount - a.mentionCount);
  }, [data]);

  const chartOption = useMemo<EChartsOption>(() => {
    if (!sortedData || sortedData.length === 0) return {};

    const categories = sortedData.map((d) =>
      d.aspect.charAt(0).toUpperCase() + d.aspect.slice(1)
    );
    const positivePercentages = sortedData.map((d) => +(d.positiveRate * 100).toFixed(1));
    const negativePercentages = sortedData.map((d) => +(d.negativeRate * 100).toFixed(1));

    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: unknown) => {
          if (!Array.isArray(params)) return "";
          const first = params[0] as { name: string; dataIndex: number };
          const item = sortedData[first.dataIndex];
          return `<div class="font-sans">
            <div class="font-semibold text-slate-200 border-b border-slate-700 pb-1 mb-1">
              ${first.name} (${item.mentionCount.toLocaleString()} mentions)
            </div>
            <div class="text-emerald-400">Positive: <b>${(item.positiveRate * 100).toFixed(1)}%</b></div>
            <div class="text-rose-400">Negative: <b>${(item.negativeRate * 100).toFixed(1)}%</b></div>
          </div>`;
        },
      },
      legend: {
        data: ["Positive Sentiment", "Negative Sentiment"],
        textStyle: { color: "#94a3b8" },
        bottom: 0,
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "10%",
        top: "3%",
        containLabel: true,
      },
      xAxis: {
        type: "value",
        min: 0,
        max: 100,
        axisLabel: { formatter: "{value}%", color: "#94a3b8" },
        splitLine: { lineStyle: { color: "#1e293b", type: "dashed" } },
      },
      yAxis: {
        type: "category",
        data: categories.reverse(),
        axisLabel: { color: "#cbd5e1", fontSize: 12 },
        axisLine: { lineStyle: { color: "#334155" } },
      },
      series: [
        {
          name: "Positive Sentiment",
          type: "bar",
          stack: "total",
          data: [...positivePercentages].reverse(),
          itemStyle: { color: SENTIMENT_COLORS.positive },
        },
        {
          name: "Negative Sentiment",
          type: "bar",
          stack: "total",
          data: [...negativePercentages].reverse(),
          itemStyle: { color: SENTIMENT_COLORS.negative },
        },
      ],
    };
  }, [sortedData]);

  const tabularData = useMemo<DataPoint[]>(() => {
    if (!sortedData) return [];
    return sortedData.map((d) => ({
      label: d.aspect.charAt(0).toUpperCase() + d.aspect.slice(1),
      value: `+${(d.positiveRate * 100).toFixed(1)}% / -${(d.negativeRate * 100).toFixed(1)}%`,
      secondaryValue: `${d.mentionCount.toLocaleString()} mentions`,
    }));
  }, [sortedData]);

  return (
    <ChartContainer
      title={title}
      description={description}
      option={chartOption}
      height={height}
      tabularData={tabularData}
      tabularHeaders={["Aspect", "Positive / Negative Ratio", "Volume"]}
      empty={empty}
      className={className}
    />
  );
};

