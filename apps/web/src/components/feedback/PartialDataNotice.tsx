import React from "react";
import { Info } from "lucide-react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface PartialDataNoticeProps {
  coveragePercent?: number | null;
  sampleCount?: number | null;
  totalAvailable?: number | null;
  message?: string;
  className?: string;
}

export const PartialDataNotice: React.FC<PartialDataNoticeProps> = ({
  coveragePercent,
  sampleCount,
  totalAvailable,
  message,
  className,
}) => {
  return (
    <div
      role="note"
      aria-label="Dataset coverage and methodology notice"
      className={twMerge(
        clsx(
          "w-full rounded-xl border border-sky-900/50 bg-sky-950/20 px-4 py-3 flex items-start gap-3 text-xs text-sky-200/90",
          className
        )
      )}
    >
      <div className="p-1 rounded-md bg-sky-900/40 text-sky-300 shrink-0 mt-0.5">
        <Info className="w-4 h-4" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <p className="font-medium text-sky-100">
          Provisional Analytics & Statistical Sampling
        </p>
        <p className="text-sky-300/80 leading-relaxed">
          {message ||
            "Analysis is calculated over a stratified historical sample. Results reflect NLP model inferences and may differ from aggregate Steam recommendation ratios."}
        </p>
        {(coveragePercent !== undefined || (sampleCount && totalAvailable)) && (
          <div className="flex flex-wrap items-center gap-3 pt-0.5 text-[11px] font-mono text-sky-400">
            {coveragePercent !== undefined && coveragePercent !== null && (
              <span>Coverage: {coveragePercent.toFixed(1)}%</span>
            )}
            {sampleCount && totalAvailable && (
              <span>
                Analyzed: {sampleCount.toLocaleString()} / {totalAvailable.toLocaleString()} reviews
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

