import React, { useState } from "react";
import {
  RotateCcw,
  XCircle,
  CheckCircle2,
  Clock,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { AdminIngestionJob } from "../../../types/admin";
import { ConfirmationModal } from "./ConfirmationModal";

export interface IngestionJobsTabProps {
  jobs: AdminIngestionJob[];
  isLoading: boolean;
  onCancelJob: (jobId: string) => Promise<void>;
  onRetryJob: (jobId: string) => Promise<void>;
  onReload: () => void;
}

export const IngestionJobsTab: React.FC<IngestionJobsTabProps> = ({
  jobs,
  isLoading,
  onCancelJob,
  onRetryJob,
  onReload,
}) => {
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [cancelJobTarget, setCancelJobTarget] = useState<AdminIngestionJob | null>(null);
  const [retryJobTarget, setRetryJobTarget] = useState<AdminIngestionJob | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const filteredJobs = jobs.filter((job) => {
    const matchesStatus = statusFilter === "all" || job.status === statusFilter;
    const matchesType = typeFilter === "all" || job.job_type === typeFilter;
    return matchesStatus && matchesType;
  });

  const getStatusPill = (status: string) => {
    switch (status) {
      case "succeeded":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950/70 text-emerald-400 border border-emerald-800">
            <CheckCircle2 className="w-3 h-3" />
            <span>Succeeded</span>
          </span>
        );
      case "running":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-sky-950/70 text-sky-400 border border-sky-800 animate-pulse">
            <RefreshCw className="w-3 h-3 animate-spin" />
            <span>Running</span>
          </span>
        );
      case "queued":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-950/70 text-amber-400 border border-amber-800">
            <Clock className="w-3 h-3" />
            <span>Queued</span>
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-950/70 text-rose-400 border border-rose-800">
            <AlertTriangle className="w-3 h-3" />
            <span>Failed</span>
          </span>
        );
      case "cancelled":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <XCircle className="w-3 h-3" />
            <span>Cancelled</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-300">
            <span>{status}</span>
          </span>
        );
    }
  };

  const handleCancelConfirm = async () => {
    if (!cancelJobTarget) return;
    setActionLoading(true);
    try {
      await onCancelJob(cancelJobTarget.job_id);
      setCancelJobTarget(null);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetryConfirm = async () => {
    if (!retryJobTarget) return;
    setActionLoading(true);
    try {
      await onRetryJob(retryJobTarget.job_id);
      setRetryJobTarget(null);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="all">All Statuses</option>
            <option value="running">Running</option>
            <option value="queued">Queued</option>
            <option value="succeeded">Succeeded</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="all">All Modes</option>
            <option value="incremental">Incremental</option>
            <option value="historical">Historical</option>
          </select>
        </div>

        <button
          type="button"
          onClick={onReload}
          className="p-2 self-end sm:self-auto rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          title="Refresh jobs table"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Jobs Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Job ID</th>
                <th className="py-3 px-4">Mode</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 min-w-[200px]">Progress & Volume</th>
                <th className="py-3 px-4">Timeline</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    Loading ingestion collection jobs...
                  </td>
                </tr>
              ) : filteredJobs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No matching ingestion jobs found.
                  </td>
                </tr>
              ) : (
                filteredJobs.map((job) => {
                  const percent =
                    job.target_reviews > 0
                      ? Math.min(100, Math.round((job.collected_reviews / job.target_reviews) * 100))
                      : job.status === "succeeded"
                      ? 100
                      : 0;

                  return (
                    <tr key={job.job_id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {job.job_id.slice(0, 8)}...
                      </td>
                      <td className="py-3 px-4">
                        <span className="capitalize font-medium text-slate-200">
                          {job.job_type}
                        </span>
                      </td>
                      <td className="py-3 px-4">{getStatusPill(job.status)}</td>
                      <td className="py-3 px-4">
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-[11px] text-slate-400">
                            <span>
                              {job.collected_reviews.toLocaleString()} collected
                            </span>
                            {job.target_reviews > 0 && (
                              <span>of {job.target_reviews.toLocaleString()} ({percent}%)</span>
                            )}
                          </div>
                          <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                            <div
                              className={`h-full transition-all duration-300 ${
                                job.status === "failed"
                                  ? "bg-rose-500"
                                  : job.status === "succeeded"
                                  ? "bg-emerald-500"
                                  : "bg-sky-500"
                              }`}
                              style={{ width: `${percent}%` }}
                            />
                          </div>
                          {job.error_code && (
                            <p className="text-[11px] text-rose-400 font-mono">
                              Error: {job.error_code}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-[11px]">
                        <div>
                          {job.started_at
                            ? `Started: ${new Date(job.started_at).toLocaleTimeString()}`
                            : "Queued"}
                        </div>
                        {job.finished_at && (
                          <div className="text-slate-500">
                            Ended: {new Date(job.finished_at).toLocaleTimeString()}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {(job.status === "queued" || job.status === "running") && (
                            <button
                              type="button"
                              onClick={() => setCancelJobTarget(job)}
                              className="flex items-center gap-1 px-2 py-1 rounded bg-rose-950/50 hover:bg-rose-900/60 text-rose-300 border border-rose-800 text-xs font-medium transition-colors"
                            >
                              <XCircle className="w-3 h-3" />
                              <span>Cancel</span>
                            </button>
                          )}

                          {(job.status === "failed" ||
                            job.status === "partial" ||
                            job.status === "cancelled") && (
                            <button
                              type="button"
                              onClick={() => setRetryJobTarget(job)}
                              className="flex items-center gap-1 px-2.5 py-1 rounded bg-amber-950/60 hover:bg-amber-900/60 text-amber-300 border border-amber-800 text-xs font-medium transition-colors"
                            >
                              <RotateCcw className="w-3 h-3" />
                              <span>Retry</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Confirmation Modals */}
      <ConfirmationModal
        isOpen={cancelJobTarget !== null}
        title="Cancel Ingestion Job"
        message={`Are you sure you want to cancel collection job ${cancelJobTarget?.job_id}? Partial progress will be retained, but active review collection will abort immediately.`}
        confirmLabel="Cancel Ingestion Job"
        variant="danger"
        isLoading={actionLoading}
        onConfirm={handleCancelConfirm}
        onCancel={() => setCancelJobTarget(null)}
      />

      <ConfirmationModal
        isOpen={retryJobTarget !== null}
        title="Retry Ingestion Job"
        message={`Retry collection job ${retryJobTarget?.job_id}? This will enqueue a new collection task resuming from the latest checkpoint.`}
        confirmLabel="Enqueue Retry"
        variant="warning"
        isLoading={actionLoading}
        onConfirm={handleRetryConfirm}
        onCancel={() => setRetryJobTarget(null)}
      />
    </div>
  );
};
