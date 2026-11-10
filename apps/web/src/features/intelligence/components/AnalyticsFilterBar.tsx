import React, { useState } from "react";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { Select } from "../../../components/ui/Select";
import { Calendar, Filter, Clock } from "lucide-react";

export type AnalyticsPeriod = "day" | "week" | "month";
export type DatePreset = "all" | "30d" | "90d" | "1y" | "custom";

export interface AnalyticsFilterState {
  preset: DatePreset;
  period: AnalyticsPeriod;
  from?: string;
  to?: string;
}

export interface AnalyticsFilterBarProps {
  initialState?: Partial<AnalyticsFilterState>;
  onFilterChange: (filters: AnalyticsFilterState) => void;
  isLoading?: boolean;
}

function calculateDatesForPreset(preset: DatePreset): { from?: string; to?: string } {
  const now = new Date();
  const to = now.toISOString().split("T")[0];

  switch (preset) {
    case "30d": {
      const fromDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      return { from: fromDate.toISOString().split("T")[0], to };
    }
    case "90d": {
      const fromDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
      return { from: fromDate.toISOString().split("T")[0], to };
    }
    case "1y": {
      const fromDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
      return { from: fromDate.toISOString().split("T")[0], to };
    }
    case "all":
    case "custom":
    default:
      return { from: undefined, to: undefined };
  }
}

export const AnalyticsFilterBar: React.FC<AnalyticsFilterBarProps> = ({
  initialState,
  onFilterChange,
  isLoading = false,
}) => {
  const [preset, setPreset] = useState<DatePreset>(initialState?.preset || "all");
  const [period, setPeriod] = useState<AnalyticsPeriod>(initialState?.period || "week");
  const [fromDate, setFromDate] = useState<string>(initialState?.from || "");
  const [toDate, setToDate] = useState<string>(initialState?.to || "");
  const [dateError, setDateError] = useState<string | null>(null);

  const presets: { id: DatePreset; label: string }[] = [
    { id: "all", label: "All Time" },
    { id: "30d", label: "30 Days" },
    { id: "90d", label: "90 Days" },
    { id: "1y", label: "1 Year" },
    { id: "custom", label: "Custom Range" },
  ];

  const periodOptions = [
    { value: "day", label: "Daily" },
    { value: "week", label: "Weekly" },
    { value: "month", label: "Monthly" },
  ];

  const handlePresetSelect = (newPreset: DatePreset) => {
    setPreset(newPreset);
    setDateError(null);

    if (newPreset === "custom") {
      // Don't trigger change until user specifies dates
      return;
    }

    const { from, to } = calculateDatesForPreset(newPreset);
    setFromDate(from || "");
    setToDate(to || "");

    onFilterChange({
      preset: newPreset,
      period,
      from,
      to,
    });
  };

  const handlePeriodChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newPeriod = e.target.value as AnalyticsPeriod;
    setPeriod(newPeriod);

    onFilterChange({
      preset,
      period: newPeriod,
      from: fromDate || undefined,
      to: toDate || undefined,
    });
  };

  const handleApplyCustomDates = () => {
    if (!fromDate && !toDate) {
      setDateError("Please enter at least a start or end date.");
      return;
    }

    if (fromDate && toDate && fromDate > toDate) {
      setDateError("Start date cannot be after end date.");
      return;
    }

    setDateError(null);
    onFilterChange({
      preset: "custom",
      period,
      from: fromDate || undefined,
      to: toDate || undefined,
    });
  };

  const activeRangeText =
    preset === "all"
      ? "All indexed reviews"
      : fromDate || toDate
      ? `${fromDate || "Start"} to ${toDate || "Present"}`
      : "Custom date filter";

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Preset Selector Buttons */}
        <div className="flex items-center gap-1.5 flex-wrap" role="group" aria-label="Date range presets">
          <span className="text-xs font-semibold text-slate-400 mr-1 inline-flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Range:</span>
          </span>
          {presets.map((p) => {
            const isActive = preset === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => handlePresetSelect(p.id)}
                className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 ${
                  isActive
                    ? "bg-sky-500/20 text-sky-300 border border-sky-500/40 font-semibold"
                    : "bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/50"
                }`}
                aria-pressed={isActive}
              >
                {p.label}
              </button>
            );
          })}
        </div>

        {/* Aggregation Period Selector */}
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-semibold text-slate-400 inline-flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Bucket:</span>
          </span>
          <div className="w-28">
            <Select
              options={periodOptions}
              value={period}
              onChange={handlePeriodChange}
              disabled={isLoading}
              aria-label="Analytics aggregation period"
              className="py-1 text-xs"
            />
          </div>
        </div>
      </div>

      {/* Custom Range Inputs (collapsible if 'custom' selected) */}
      {preset === "custom" && (
        <div className="pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row items-end gap-3 animate-fadeIn">
          <div className="w-full sm:w-44">
            <Input
              type="date"
              label="Start Date"
              value={fromDate}
              onChange={(e) => {
                setFromDate(e.target.value);
                setDateError(null);
              }}
              error={dateError || undefined}
            />
          </div>
          <div className="w-full sm:w-44">
            <Input
              type="date"
              label="End Date"
              value={toDate}
              onChange={(e) => {
                setToDate(e.target.value);
                setDateError(null);
              }}
            />
          </div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleApplyCustomDates}
            disabled={isLoading}
            className="w-full sm:w-auto"
          >
            Apply Range
          </Button>
        </div>
      )}

      {/* Active Range Disclosure */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
        <span className="inline-flex items-center gap-1.5">
          <Calendar className="w-3 h-3 text-sky-400" aria-hidden="true" />
          <span>Active filter: <b className="text-slate-200">{activeRangeText}</b></span>
        </span>
        <span className="font-mono text-slate-500">
          Granularity: {period.toUpperCase()}
        </span>
      </div>
    </div>
  );
};

