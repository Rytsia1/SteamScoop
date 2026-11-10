import React, { useState } from "react";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import { Table, BarChart2 } from "lucide-react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { ECHARTS_DARK_THEME } from "../../lib/tokens";

export interface DataPoint {
  label: string;
  value: number | string;
  secondaryValue?: number | string;
}

export interface ChartContainerProps {
  title: string;
  description?: string;
  option: EChartsOption;
  height?: number | string;
  tabularData?: DataPoint[];
  tabularHeaders?: [string, string, string?];
  className?: string;
  empty?: boolean;
  emptyMessage?: string;
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  description,
  option,
  height = 320,
  tabularData,
  tabularHeaders = ["Category", "Value", "Additional"],
  className,
  empty = false,
  emptyMessage = "No analytical data available for this view.",
}) => {
  const [showTable, setShowTable] = useState(false);

  // Merge default dark theme with provided options
  const mergedOption: EChartsOption = {
    ...ECHARTS_DARK_THEME,
    ...option,
  };

  return (
    <div
      className={twMerge(
        clsx(
          "w-full rounded-xl border border-slate-800 bg-slate-900/60 p-5 flex flex-col gap-4 text-slate-100",
          className
        )
      )}
    >
      {/* Header with Title and Accessible Table Toggle */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h4 className="text-sm font-semibold text-white tracking-tight">{title}</h4>
          {description && (
            <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{description}</p>
          )}
        </div>

        {tabularData && tabularData.length > 0 && !empty && (
          <button
            type="button"
            onClick={() => setShowTable((prev) => !prev)}
            aria-label={showTable ? "Switch to chart visualization" : "Switch to accessible data table"}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
          >
            {showTable ? (
              <>
                <BarChart2 className="w-3.5 h-3.5 text-sky-400" aria-hidden="true" />
                <span>View Chart</span>
              </>
            ) : (
              <>
                <Table className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
                <span>View Table</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Main View Area */}
      {empty ? (
        <div
          style={{ height }}
          className="flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs"
        >
          {emptyMessage}
        </div>
      ) : showTable && tabularData && tabularData.length > 0 ? (
        <div style={{ minHeight: height }} className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th scope="col" className="py-2 px-3 font-semibold">
                  {tabularHeaders[0]}
                </th>
                <th scope="col" className="py-2 px-3 font-semibold text-right">
                  {tabularHeaders[1]}
                </th>
                {tabularHeaders[2] && (
                  <th scope="col" className="py-2 px-3 font-semibold text-right">
                    {tabularHeaders[2]}
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {tabularData.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30">
                  <td className="py-2 px-3 text-slate-200 font-medium">{row.label}</td>
                  <td className="py-2 px-3 text-slate-300 text-right">{row.value}</td>
                  {tabularHeaders[2] && (
                    <td className="py-2 px-3 text-slate-400 text-right">
                      {row.secondaryValue ?? "-"}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div role="img" aria-label={`${title}: chart graphic. Accessible table available via toggle.`}>
          <ReactECharts
            option={mergedOption}
            style={{ height, width: "100%" }}
            opts={{ renderer: "canvas" }}
            notMerge={true}
            lazyUpdate={true}
          />
        </div>
      )}
    </div>
  );
};

