import React, { useState } from "react";
import { DownloadCloud, X, Loader2 } from "lucide-react";
import { AdminIngestionJobCreate, IngestionJobType } from "../../../types/admin";

export interface QueueIngestionModalProps {
  isOpen: boolean;
  gameId: string;
  gameName: string;
  isLoading: boolean;
  onClose: () => void;
  onSubmit: (gameId: string, data: AdminIngestionJobCreate) => Promise<void>;
}

export const QueueIngestionModal: React.FC<QueueIngestionModalProps> = ({
  isOpen,
  gameId,
  gameName,
  isLoading,
  onClose,
  onSubmit,
}) => {
  const [jobType, setJobType] = useState<IngestionJobType>("incremental");
  const [reviewType, setReviewType] = useState("all");
  const [purchaseType, setPurchaseType] = useState("all");
  const [overlapDays, setOverlapDays] = useState(7);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (reason.trim().length < 3) {
      setError("Please provide an audit rationale (at least 3 characters) for this ingestion run.");
      return;
    }

    try {
      await onSubmit(gameId, {
        job_type: jobType,
        collection_config: {
          review_type: reviewType,
          purchase_type: purchaseType,
          languages: ["all"],
          overlap_days: jobType === "incremental" ? overlapDays : undefined,
        },
        reason: reason.trim(),
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to queue ingestion job.");
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="queue-ingestion-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150"
    >
      <div className="w-full max-w-lg rounded-xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <DownloadCloud className="w-5 h-5 text-sky-400" />
            <div>
              <h3 id="queue-ingestion-modal-title" className="text-base font-bold text-slate-100">
                Queue Review Collection
              </h3>
              <p className="text-xs text-slate-400">Target Game: {gameName}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="job-type-select" className="block text-xs font-medium text-slate-300 mb-1">
              Collection Mode *
            </label>
            <select
              id="job-type-select"
              value={jobType}
              onChange={(e) => setJobType(e.target.value as IngestionJobType)}
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
            >
              <option value="incremental">Incremental (Sync recent reviews with safety overlap)</option>
              <option value="historical">Historical (Complete backfill of full review corpus)</option>
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="review-type-select" className="block text-xs font-medium text-slate-300 mb-1">
                Review Sentiment Filter
              </label>
              <select
                id="review-type-select"
                value={reviewType}
                onChange={(e) => setReviewType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
              >
                <option value="all">All Reviews (Positive & Negative)</option>
                <option value="positive">Positive Only</option>
                <option value="negative">Negative Only</option>
              </select>
            </div>
            <div>
              <label htmlFor="purchase-type-select" className="block text-xs font-medium text-slate-300 mb-1">
                Purchase Source
              </label>
              <select
                id="purchase-type-select"
                value={purchaseType}
                onChange={(e) => setPurchaseType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
              >
                <option value="all">All Purchase Types</option>
                <option value="steam">Steam Store Direct Purchases</option>
                <option value="non_steam_purchase">Activated Keys / Retail</option>
              </select>
            </div>
          </div>

          {jobType === "incremental" && (
            <div>
              <label htmlFor="overlap-days-input" className="block text-xs font-medium text-slate-300 mb-1">
                Safety Overlap Window (days)
              </label>
              <input
                id="overlap-days-input"
                type="number"
                min={1}
                max={90}
                value={overlapDays}
                onChange={(e) => setOverlapDays(parseInt(e.target.value, 10) || 7)}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Captures retroactively edited or delayed reviews within the safety window.
              </p>
            </div>
          )}

          <div>
            <label htmlFor="reason-input" className="block text-xs font-medium text-slate-300 mb-1">
              Operation Rationale / Audit Reason *
            </label>
            <input
              id="reason-input"
              type="text"
              required
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Scheduled sync after new patch release"
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500 text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              disabled={isLoading}
              onClick={onClose}
              className="px-3.5 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700/80 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-xs font-semibold text-white shadow-md shadow-sky-900/30 transition-all disabled:opacity-50"
            >
              {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>Queue Ingestion</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

