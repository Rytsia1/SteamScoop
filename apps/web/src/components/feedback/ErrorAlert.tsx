import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { Button } from "../ui/Button";

export interface ErrorAlertProps {
  title?: string;
  message: string;
  code?: string;
  requestId?: string | null;
  onRetry?: () => void;
  className?: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = "Failed to load data",
  message,
  code,
  requestId,
  onRetry,
  className,
}) => {
  return (
    <div
      role="alert"
      className={twMerge(
        clsx(
          "w-full rounded-xl border border-rose-900/60 bg-rose-950/30 p-5 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between text-slate-200",
          className
        )
      )}
    >
      <div className="flex items-start gap-3.5">
        <div className="p-2 rounded-lg bg-rose-900/50 text-rose-300 shrink-0 mt-0.5">
          <AlertTriangle className="w-5 h-5" aria-hidden="true" />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-rose-200">{title}</h4>
          <p className="text-xs text-rose-300/80 leading-relaxed max-w-xl">{message}</p>
          {(code || requestId) && (
            <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] font-mono text-rose-400/70">
              {code && <span>Code: {code}</span>}
              {requestId && <span>Request ID: {requestId}</span>}
            </div>
          )}
        </div>
      </div>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />}
          className="border-rose-800 text-rose-200 hover:bg-rose-900/50 hover:text-white shrink-0"
        >
          Retry
        </Button>
      )}
    </div>
  );
};

