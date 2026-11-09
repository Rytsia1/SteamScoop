import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api-client";
import { HealthData } from "../types/api";

export const HealthStatus: React.FC = () => {
  const { data, isLoading, isError, error, refetch } = useQuery<HealthData>({
    queryKey: ["health"],
    queryFn: () => apiClient<HealthData>("/health"),
  });

  if (isLoading) {
    return (
      <div
        role="status"
        aria-label="Checking system health"
        className="flex items-center gap-2 p-4 rounded-lg bg-slate-800 border border-slate-700 animate-pulse text-slate-400"
      >
        <div className="w-3 h-3 rounded-full bg-slate-500" />
        <span className="text-sm font-medium">Checking system health...</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div
        role="alert"
        aria-live="assertive"
        className="p-4 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-200 flex flex-col gap-2"
      >
        <div className="flex items-center gap-2 font-semibold">
          <div className="w-3 h-3 rounded-full bg-rose-500" />
          <span>System Status: Disconnected</span>
        </div>
        <p className="text-sm text-rose-300">
          {error instanceof Error ? error.message : "Unable to reach the backend API."}
        </p>
        <button
          type="button"
          onClick={() => refetch()}
          className="self-start text-xs font-semibold px-3 py-1.5 rounded bg-rose-800 hover:bg-rose-700 text-white transition-colors"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const isDegraded = data?.status === "degraded";

  return (
    <div
      role="region"
      aria-label="System Health"
      className={`p-4 rounded-lg border flex flex-col gap-2 ${
        isDegraded
          ? "bg-amber-950/40 border-amber-800/80 text-amber-200"
          : "bg-emerald-950/40 border-emerald-800/80 text-emerald-200"
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 font-semibold">
          <div
            className={`w-3 h-3 rounded-full ${
              isDegraded ? "bg-amber-400" : "bg-emerald-400 animate-ping"
            }`}
          />
          <span>Backend Connected: {data?.status.toUpperCase()}</span>
        </div>
        <span
          className={`text-xs px-2 py-0.5 rounded font-mono ${
            isDegraded ? "bg-amber-900/80 text-amber-300" : "bg-emerald-900/80 text-emerald-300"
          }`}
        >
          v{data?.version}
        </span>
      </div>

      <div
        className={`text-xs font-mono flex flex-wrap gap-x-4 ${
          isDegraded ? "text-amber-400/80" : "text-emerald-400/80"
        }`}
      >
        <span>Env: {data?.app_env}</span>
        <span>
          Server Time:{" "}
          {data?.timestamp ? new Date(data.timestamp).toLocaleTimeString() : "N/A"}
        </span>
      </div>

      {data?.dependencies && (
        <div
          className={`flex gap-4 pt-2 border-t text-xs font-mono ${
            isDegraded ? "border-amber-900/50" : "border-emerald-900/50"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                data.dependencies.database === "connected" ? "bg-emerald-400" : "bg-rose-500"
              }`}
            />
            <span>DB: {data.dependencies.database}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                data.dependencies.redis === "connected" ? "bg-emerald-400" : "bg-rose-500"
              }`}
            />
            <span>Redis: {data.dependencies.redis}</span>
          </div>
        </div>
      )}
    </div>
  );
};
