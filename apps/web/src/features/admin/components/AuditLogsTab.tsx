import React from "react";
import { ShieldCheck, RefreshCw } from "lucide-react";
import { AdminAuditLog } from "../../../types/admin";

export interface AuditLogsTabProps {
  logs: AdminAuditLog[];
  isLoading: boolean;
  onReload: () => void;
}

export const AuditLogsTab: React.FC<AuditLogsTabProps> = ({
  logs,
  isLoading,
  onReload,
}) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">
            Security & Operational Audit Log
          </h3>
          <p className="text-xs text-slate-400">
            Immutable log of catalog modifications, collection jobs, and model activations.
          </p>
        </div>
        <button
          type="button"
          onClick={onReload}
          className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          title="Refresh audit logs"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/90 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Resource</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Details</th>
                <th className="py-3 px-4">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    Loading audit records...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No audit records recorded yet.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono text-slate-400">#{log.id}</td>
                    <td className="py-3 px-4 font-medium text-slate-200">
                      <div className="flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
                        <span className="font-mono text-xs">{log.action}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {log.resource_type ? (
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[11px] text-slate-300 border border-slate-700 font-mono">
                          {log.resource_type}:{log.resource_id ? log.resource_id.slice(0, 8) : ""}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                      {log.actor_user_id ? `${log.actor_user_id.slice(0, 8)}...` : "System / Scheduled"}
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[11px] max-w-xs truncate">
                      {JSON.stringify(log.metadata)}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {new Date(log.created_at).toLocaleString()}
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

