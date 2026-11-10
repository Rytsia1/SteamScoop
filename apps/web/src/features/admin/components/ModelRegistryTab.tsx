import React, { useState } from "react";
import {
  Sparkles,
  CheckCircle,
  Clock,
  RefreshCw,
  Zap,
} from "lucide-react";
import { AdminModel } from "../../../types/admin";
import { ConfirmationModal } from "./ConfirmationModal";

export interface ModelRegistryTabProps {
  models: AdminModel[];
  isLoading: boolean;
  onActivateModel: (modelId: string) => Promise<void>;
  onReload: () => void;
}

export const ModelRegistryTab: React.FC<ModelRegistryTabProps> = ({
  models,
  isLoading,
  onActivateModel,
  onReload,
}) => {
  const [taskFilter, setTaskFilter] = useState("all");
  const [activateTarget, setActivateTarget] = useState<AdminModel | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const filteredModels = models.filter((m) => {
    return taskFilter === "all" || m.task === taskFilter;
  });

  const handleActivateConfirm = async () => {
    if (!activateTarget) return;
    setActionLoading(true);
    try {
      await onActivateModel(activateTarget.id);
      setActivateTarget(null);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <select
            value={taskFilter}
            onChange={(e) => setTaskFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="all">All NLP / Analytics Tasks</option>
            <option value="sentiment">Sentiment Classification</option>
            <option value="aspect_absa">Aspect Extraction (ABSA)</option>
            <option value="topic">Topic Modeling</option>
          </select>
        </div>

        <button
          type="button"
          onClick={onReload}
          className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          title="Refresh models"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Model Cards / Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Model & Key</th>
                <th className="py-3 px-4">Version</th>
                <th className="py-3 px-4">Task</th>
                <th className="py-3 px-4">Framework</th>
                <th className="py-3 px-4">Production Status</th>
                <th className="py-3 px-4">Registered Date</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    Loading model registry...
                  </td>
                </tr>
              ) : filteredModels.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    No models registered in this category.
                  </td>
                </tr>
              ) : (
                filteredModels.map((model) => (
                  <tr key={model.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-200">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-sky-400" />
                        <span>{model.model_key}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-sky-300">{model.version}</td>
                    <td className="py-3 px-4">
                      <span className="capitalize text-slate-300 font-medium">
                        {model.task.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="uppercase text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {model.framework}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {model.is_active ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800 shadow-sm shadow-emerald-950">
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>Active (Production)</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] text-slate-500 bg-slate-800/60 border border-slate-700/60">
                          <Clock className="w-3 h-3" />
                          <span>Standby / Candidate</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {new Date(model.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {!model.is_active && (
                        <button
                          type="button"
                          onClick={() => setActivateTarget(model)}
                          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-sm shadow-sky-900/30 transition-all"
                        >
                          <Zap className="w-3 h-3" />
                          <span>Activate</span>
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={activateTarget !== null}
        title="Confirm Model Activation"
        message={`Activate model '${activateTarget?.model_key}' (${activateTarget?.version}) for task '${activateTarget?.task}'? This will atomically switch live batch inference to use this version and mark prior versions standby.`}
        confirmLabel="Activate in Production"
        variant="warning"
        isLoading={actionLoading}
        onConfirm={handleActivateConfirm}
        onCancel={() => setActivateTarget(null)}
      />
    </div>
  );
};
