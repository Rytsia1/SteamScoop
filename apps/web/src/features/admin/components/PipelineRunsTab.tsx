import React, { useState } from "react";
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Clock,
  RefreshCw,
  Layers,
} from "lucide-react";
import { AdminPipelineRun } from "../../../types/admin";

export interface PipelineRunsTabProps {
  runs: AdminPipelineRun[];
  isLoading: boolean;
  onReload: () => void;
}

export const PipelineRunsTab: React.FC<PipelineRunsTabProps> = ({
  runs,
  isLoading,
  onReload,
}) => {
  const [typeFilter, setTypeFilter] = useState("all");

  const filteredRuns = runs.filter((run) => {
    return typeFilter === "all" || run.pipeline_type === typeFilter;
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
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-950/70 text-rose-400 border border-rose-800">
            <AlertTriangle className="w-3 h-3" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-300">
            <Clock className="w-3 h-3" />
            <span>{status}</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="all">All Pipeline Tasks</option>
            <option value="sentiment_batch">Sentiment Inference</option>
            <option value="aspect_extraction">Aspect-Based ABSA</option>
            <option value="topic_modeling">Topic Modeling</option>
          </select>
        </div>

        <button
          type="button"
          onClick={onReload}
          className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          title="Refresh pipeline runs"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Run ID</th>
                <th className="py-3 px-4">Pipeline Task</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Model Provenance</th>
                <th className="py-3 px-4">Inference Counters</th>
                <th className="py-3 px-4">Started At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    Loading pipeline executions...
                  </td>
                </tr>
              ) : filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No pipeline runs recorded.
                  </td>
                </tr>
              ) : (
                filteredRuns.map((run) => (
                  <tr key={run.run_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {run.run_id.slice(0, 8)}...
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 font-medium text-slate-200">
                        <Cpu className="w-3.5 h-3.5 text-sky-400" />
                        <span className="capitalize">
                          {run.pipeline_type.replace("_", " ")}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4">{getStatusPill(run.status)}</td>
                    <td className="py-3 px-4">
                      {run.model_version_snapshot ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 font-mono text-[11px] text-sky-300 border border-slate-700">
                          <Layers className="w-3 h-3 text-slate-400" />
                          <span>{run.model_version_snapshot}</span>
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2 text-[11px]">
                          <span className="text-slate-400">Total: {run.input_count.toLocaleString()}</span>
                          <span className="text-emerald-400">✓ {run.success_count.toLocaleString()}</span>
                          {run.failure_count > 0 && (
                            <span className="text-rose-400">✗ {run.failure_count.toLocaleString()}</span>
                          )}
                        </div>
                        {run.error_summary && (
                          <p className="text-[11px] text-rose-400 font-mono truncate max-w-xs">
                            {run.error_summary}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

