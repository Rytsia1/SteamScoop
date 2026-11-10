import React, { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartContainer, DataPoint } from "./ChartContainer";
import { SENTIMENT_COLORS } from "../../lib/tokens";

export interface SentimentDistributionData {
  positiveCount: number;
  negativeCount: number;
  neutralCount: number;
  positiveRate: number;
  negativeRate: number;
  neutralRate: number;
  totalClassified: number;
}

export interface SentimentPieChartProps {
  data: SentimentDistributionData | null | undefined;
  title?: string;
  description?: string;
  height?: number | string;
  className?: string;
}

export const SentimentPieChart: React.FC<SentimentPieChartProps> = ({
  data,
  title = "Sentiment Distribution",
  description = "NLP model sentiment classification across sampled player reviews.",
  height = 280,
  className,
}) => {
  const empty = !data || data.totalClassified === 0;

  const chartOption = useMemo<EChartsOption>(() => {
    if (!data) return {};

    return {
      tooltip: {
        trigger: "item",
        formatter: "{b}: {c} reviews ({d}%)",
      },
      legend: {
        bottom: "0%",
        left: "center",
        textStyle: { color: "#94a3b8" },
      },
      series: [
        {
          name: "Sentiment",
          type: "pie",
          radius: ["45%", "70%"],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 6,
            borderColor: "#0f172a",
            borderWidth: 2,
          },
          label: {
            show: false,
            position: "center",
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: "bold",
              color: "#f8fafc",
              formatter: "{b}\n{d}%",
            },
          },
          data: [
            {
              value: data.positiveCount,
              name: "Positive",
              itemStyle: { color: SENTIMENT_COLORS.positive },
            },
            {
              value: data.negativeCount,
              name: "Negative",
              itemStyle: { color: SENTIMENT_COLORS.negative },
            },
            {
              value: data.neutralCount,
              name: "Neutral",
              itemStyle: { color: SENTIMENT_COLORS.neutral },
            },
          ],
        },
      ],
    };
  }, [data]);

  const tabularData = useMemo<DataPoint[]>(() => {
    if (!data) return [];
    return [
      {
        label: "Positive Sentiment",
        value: `${data.positiveCount.toLocaleString()} (${(data.positiveRate * 100).toFixed(1)}%)`,
      },
      {
        label: "Negative Sentiment",
        value: `${data.negativeCount.toLocaleString()} (${(data.negativeRate * 100).toFixed(1)}%)`,
      },
      {
        label: "Neutral / Unclassified",
        value: `${data.neutralCount.toLocaleString()} (${(data.neutralRate * 100).toFixed(1)}%)`,
      },
    ];
  }, [data]);

  return (
    <ChartContainer
      title={title}
      description={description}
      option={chartOption}
      height={height}
      tabularData={tabularData}
      tabularHeaders={["Sentiment Class", "Count & Proportion"]}
      empty={empty}
      className={className}
    />
  );
};

