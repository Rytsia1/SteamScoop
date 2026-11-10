import React, { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartContainer, DataPoint } from "./ChartContainer";
import { AnalyticsPoint } from "../../features/intelligence/types/intelligence";

export interface ReviewActivityChartProps {
  points: AnalyticsPoint[] | null | undefined;
  period?: "day" | "week" | "month";
  title?: string;
  description?: string;
  height?: number | string;
  className?: string;
}

export const ReviewActivityChart: React.FC<ReviewActivityChartProps> = ({
  points,
  period = "week",
  title = "Review Activity & Community Sentiment Volume",
  description = "Review influx broken down by Steam recommendations alongside NLP model net sentiment score.",
  height = 340,
  className,
}) => {
  const empty = !points || points.length === 0;

  const chartOption = useMemo<EChartsOption>(() => {
    if (!points || points.length === 0) return {};

    const dates = points.map((p) => p.period_start);
    const steamRecommended = points.map((p) => p.steam_recommended_count);
    const steamNotRecommended = points.map((p) => p.steam_not_recommended_count);
    const sentimentScores = points.map((p) => {
      if (p.sentiment_score != null) {
        return +p.sentiment_score.toFixed(2);
      }
      const classified = p.positive_count + p.negative_count;
      if (classified > 0) {
        return +((p.positive_count - p.negative_count) / classified).toFixed(2);
      }
      return 0;
    });

    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: unknown) => {
          if (!Array.isArray(params)) return "";
          const first = params[0] as { dataIndex: number; name: string };
          const pt = points[first.dataIndex];
          if (!pt) return "";

          const score =
            pt.sentiment_score != null
              ? pt.sentiment_score.toFixed(2)
              : pt.positive_count + pt.negative_count > 0
              ? (
                  (pt.positive_count - pt.negative_count) /
                  (pt.positive_count + pt.negative_count)
                ).toFixed(2)
              : "N/A";

          return `
            <div class="font-sans text-xs">
              <div class="font-bold text-slate-200 pb-1 mb-1 border-b border-slate-700">
                ${pt.period_start} &rarr; ${pt.period_end}
              </div>
              <div class="text-slate-300">Total Influx: <b>${pt.review_count.toLocaleString()}</b> reviews</div>
              <div class="text-emerald-400">&bull; Steam Recommended: <b>${pt.steam_recommended_count.toLocaleString()}</b></div>
              <div class="text-rose-400">&bull; Steam Not Recommended: <b>${pt.steam_not_recommended_count.toLocaleString()}</b></div>
              <div class="text-sky-400 mt-1 pt-1 border-t border-slate-700/60">
                &bull; Model Net Sentiment Score: <b>${score}</b> (range -1.0 to +1.0)
              </div>
            </div>
          `;
        },
      },
      legend: {
        data: ["Steam Recommended", "Steam Not Recommended", "Model Net Score"],
        textStyle: { color: "#94a3b8" },
        bottom: 0,
      },
      xAxis: {
        type: "category",
        data: dates,
        axisLine: { lineStyle: { color: "#334155" } },
        axisLabel: { color: "#94a3b8", fontSize: 11 },
      },
      yAxis: [
        {
          type: "value",
          name: "Reviews",
          min: 0,
          position: "left",
          axisLabel: { color: "#94a3b8", fontSize: 11 },
          splitLine: { lineStyle: { color: "#1e293b", type: "dashed" } },
        },
        {
          type: "value",
          name: "Net Score",
          min: -1.0,
          max: 1.0,
          interval: 0.5,
          position: "right",
          axisLabel: {
            formatter: "{value}",
            color: "#38bdf8",
            fontSize: 11,
          },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: "Steam Recommended",
          type: "bar",
          stack: "volume",
          data: steamRecommended,
          itemStyle: { color: "#10b981" },
        },
        {
          name: "Steam Not Recommended",
          type: "bar",
          stack: "volume",
          data: steamNotRecommended,
          itemStyle: { color: "#f43f5e" },
        },
        {
          name: "Model Net Score",
          type: "line",
          yAxisIndex: 1,
          smooth: true,
          showSymbol: true,
          symbolSize: 6,
          data: sentimentScores,
          itemStyle: { color: "#38bdf8" },
          lineStyle: { width: 2.5, color: "#38bdf8" },
        },
      ],
    };
  }, [points]);

  const tabularData = useMemo<DataPoint[]>(() => {
    if (!points) return [];
    return points.map((p) => {
      const score =
        p.sentiment_score != null
          ? p.sentiment_score.toFixed(2)
          : p.positive_count + p.negative_count > 0
          ? ((p.positive_count - p.negative_count) / (p.positive_count + p.negative_count)).toFixed(2)
          : "N/A";

      return {
        label: `${p.period_start} to ${p.period_end}`,
        value: `${p.review_count.toLocaleString()} (${p.steam_recommended_count.toLocaleString()} rec / ${p.steam_not_recommended_count.toLocaleString()} not rec)`,
        secondaryValue: `Score: ${score}`,
      };
    });
  }, [points]);

  const totalWindowVolume = useMemo(() => {
    if (!points) return 0;
    return points.reduce((acc, curr) => acc + curr.review_count, 0);
  }, [points]);

  return (
    <div className="space-y-2">
      <ChartContainer
        title={title}
        description={description}
        option={chartOption}
        height={height}
        tabularData={tabularData}
        tabularHeaders={["Date Interval", "Review Volume (Rec / Not Rec)", "Net Sentiment Score"]}
        empty={empty}
        emptyMessage="No review activity recorded for this period."
        className={className}
      />
      {!empty && (
        <div className="text-xs text-slate-400 px-2 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
          <span>
            Total interval volume: <b>{totalWindowVolume.toLocaleString()}</b> reviews ({period} buckets).
          </span>
          <span className="text-slate-500 text-[11px]">
            * Net Sentiment Score: -1.0 (unanimously negative) to +1.0 (unanimously positive).
          </span>
        </div>
      )}
    </div>
  );
};
