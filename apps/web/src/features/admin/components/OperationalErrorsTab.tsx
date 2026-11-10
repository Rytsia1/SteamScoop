import React from "react";
import {
  RotateCcw,
  CheckCircle2,
  RefreshCw,
  Cpu,
  DownloadCloud,
} from "lucide-react";
import { AdminOperationalErrors } from "../../../types/admin";

export interface OperationalErrorsTabProps {
  errors: AdminOperationalErrors | null;
  isLoading: boolean;
  onRetryJob: (jobId: string) => Promise<void>;
  onReload: () => void;
}

export const OperationalErrorsTab: React.FC<OperationalErrorsTabProps> = ({
  errors,
  isLoading,
  onRetryJob,
  onReload,
}) => {
  const hasErrors =
    errors &&
    (errors.failed_ingestion_jobs.length > 0 || errors.failed_pipeline_runs.length > 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">
            System Failures & Operational Diagnostics
          </h3>
          <p className="text-xs text-slate-400">
            Real-time diagnostics across ingestion engines and ML execution pipelines.
          </p>
        </div>
        <button
          type="button"
          onClick={onReload}
          className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          title="Refresh operational errors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-xs text-slate-500">
          Scanning operational telemetry and job history...
        </div>
      ) : !hasErrors ? (
        <div className="rounded-xl border border-emerald-900/60 bg-emerald-950/20 p-8 text-center space-y-2">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
          <h4 className="text-sm font-bold text-emerald-300">No Operational Failures</h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            All background ingestion jobs and inference pipelines are currently healthy or have
            completed successfully.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Failed Ingestion Jobs */}
          {errors.failed_ingestion_jobs.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs">
                <DownloadCloud className="w-4 h-4" />
                <span>Failed Collection Jobs ({errors.failed_ingestion_jobs.length})</span>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/90 overflow-hidden">
                <div className="divide-y divide-slate-800/80">
                  {errors.failed_ingestion_jobs.map((job) => (
                    <div
                      key={job.job_id}
                      className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hover:bg-slate-850/50"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs text-slate-200 font-bold">
                            Job {job.job_id.slice(0, 8)}...
                          </span>
                          <span className="capitalize text-[11px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                            {job.job_type}
                          </span>
                          <span className="text-[11px] font-bold text-rose-400 uppercase">
                            [{job.status}]
                          </span>
                        </div>
                        <p className="text-xs text-rose-300 font-mono">
                          {job.error_code
                            ? `Error: ${job.error_code}`
                            : "Upstream collection error encountered"}
                        </p>
                        {job.error_message && (
                          <p className="text-[11px] text-slate-400 max-w-xl">
                            {job.error_message}
                          </p>
                        )}
                        <div className="text-[11px] text-slate-500">
                          Collected {job.collected_reviews.toLocaleString()} /{" "}
                          {job.target_reviews.toLocaleString()} reviews before interruption.
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => onRetryJob(job.job_id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-600/90 hover:bg-amber-500 text-white text-xs font-semibold shadow-sm transition-all"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>Enqueue Retry</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Failed Pipeline Runs */}
          {errors.failed_pipeline_runs.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs">
                <Cpu className="w-4 h-4" />
                <span>Failed Pipeline Executions ({errors.failed_pipeline_runs.length})</span>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/90 overflow-hidden">
                <div className="divide-y divide-slate-800/80">
                  {errors.failed_pipeline_runs.map((run) => (
                    <div
                      key={run.run_id}
                      className="p-4 space-y-1 hover:bg-slate-850/50"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-slate-200 font-bold">
                          Run {run.run_id.slice(0, 8)}...
                        </span>
                        <span className="capitalize text-[11px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                          {run.pipeline_type.replace("_", " ")}
                        </span>
                        <span className="text-[11px] font-bold text-rose-400 uppercase">
                          [Failed]
                        </span>
                      </div>
                      {run.error_summary && (
                        <p className="text-xs text-rose-300 font-mono">
                          {run.error_summary}
                        </p>
                      )}
                      <div className="text-[11px] text-slate-500">
                        Processed {run.success_count.toLocaleString()} succeeded,{" "}
                        {run.failure_count.toLocaleString()} failed out of{" "}
                        {run.input_count.toLocaleString()} items.
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
