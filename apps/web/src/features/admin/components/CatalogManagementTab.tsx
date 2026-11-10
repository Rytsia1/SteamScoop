import React, { useState } from "react";
import {
  PlusCircle,
  RefreshCw,
  DownloadCloud,
  CheckCircle2,
  Clock,
  AlertOctagon,
  EyeOff,
  Search,
  ExternalLink,
} from "lucide-react";
import { AdminGame, AdminGameCreate } from "../../../types/admin";
import { ConfirmationModal } from "./ConfirmationModal";
import { NewGameModal } from "./NewGameModal";
import { QueueIngestionModal } from "./QueueIngestionModal";
import { AdminIngestionJobCreate } from "../../../types/admin";

export interface CatalogManagementTabProps {
  games: AdminGame[];
  isLoading: boolean;
  onRefreshMetadata: (gameId: string) => Promise<void>;
  onQueueIngestion: (gameId: string, data: AdminIngestionJobCreate) => Promise<void>;
  onCreateGame: (data: AdminGameCreate) => Promise<void>;
  onToggleActive: (gameId: string, currentActive: boolean) => Promise<void>;
  onReload: () => void;
}

export const CatalogManagementTab: React.FC<CatalogManagementTabProps> = ({
  games,
  isLoading,
  onRefreshMetadata,
  onQueueIngestion,
  onCreateGame,
  onToggleActive,
  onReload,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Modals state
  const [isNewGameOpen, setIsNewGameOpen] = useState(false);
  const [queueModalGame, setQueueModalGame] = useState<{ id: string; name: string } | null>(null);
  const [confirmMetadataGame, setConfirmMetadataGame] = useState<{ id: string; name: string } | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const filteredGames = games.filter((g) => {
    const matchesSearch =
      g.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(g.steam_app_id).includes(searchTerm);
    const matchesStatus = statusFilter === "all" || g.catalog_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "indexed":
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950/70 text-emerald-400 border border-emerald-800/80">
            <CheckCircle2 className="w-3 h-3" />
            <span>Indexed</span>
          </span>
        );
      case "pending":
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-950/70 text-amber-400 border border-amber-800/80">
            <Clock className="w-3 h-3" />
            <span>Pending</span>
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-950/70 text-rose-400 border border-rose-800/80">
            <AlertOctagon className="w-3 h-3" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <EyeOff className="w-3 h-3" />
            <span className="capitalize">{status}</span>
          </span>
        );
    }
  };

  const handleMetadataConfirm = async () => {
    if (!confirmMetadataGame) return;
    try {
      setActionLoading(true);
      await onRefreshMetadata(confirmMetadataGame.id);
      setConfirmMetadataGame(null);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Action Controls & Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex flex-1 items-center gap-2">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter by title or App ID..."
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="all">All Statuses</option>
            <option value="indexed">Indexed Only</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
            <option value="disabled">Disabled</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onReload}
            title="Refresh game catalog table"
            className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => setIsNewGameOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-xs font-semibold text-white shadow-sm shadow-sky-900/30 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add Game</span>
          </button>
        </div>
      </div>

      {/* Catalog Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Game</th>
                <th className="py-3 px-4">Steam App ID</th>
                <th className="py-3 px-4">Indexing Status</th>
                <th className="py-3 px-4">Active</th>
                <th className="py-3 px-4">Last Updated</th>
                <th className="py-3 px-4 text-right">Administrative Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    Loading managed game catalog...
                  </td>
                </tr>
              ) : filteredGames.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No matching games in catalog.
                  </td>
                </tr>
              ) : (
                filteredGames.map((game) => (
                  <tr key={game.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-medium text-slate-200">
                      <div className="flex items-center gap-2">
                        <span>{game.name}</span>
                        <a
                          href={`https://store.steampowered.com/app/${game.steam_app_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-slate-500 hover:text-sky-400 transition-colors"
                          title="Open on Steam Store"
                        >
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400">{game.steam_app_id}</td>
                    <td className="py-3 px-4">{getStatusBadge(game.catalog_status)}</td>
                    <td className="py-3 px-4">
                      <button
                        type="button"
                        onClick={() => onToggleActive(game.id, game.is_active)}
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase transition-colors ${
                          game.is_active
                            ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                            : "bg-slate-800 text-slate-400 border border-slate-700"
                        }`}
                      >
                        {game.is_active ? "Active" : "Disabled"}
                      </button>
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {new Date(game.updated_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            setConfirmMetadataGame({ id: game.id, name: game.name })
                          }
                          title="Queue metadata & media assets refresh"
                          className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs transition-colors"
                        >
                          <RefreshCw className="w-3 h-3 text-sky-400" />
                          <span>Refresh Metadata</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setQueueModalGame({ id: game.id, name: game.name })}
                          title="Queue review collection job"
                          className="flex items-center gap-1 px-2.5 py-1 rounded bg-sky-950/60 hover:bg-sky-900/60 text-sky-300 border border-sky-800 text-xs font-semibold transition-colors"
                        >
                          <DownloadCloud className="w-3 h-3" />
                          <span>Queue Ingestion</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Confirmation & Form Modals */}
      <ConfirmationModal
        isOpen={confirmMetadataGame !== null}
        title="Confirm Metadata Refresh"
        message={`Queue an asynchronous refresh of Steam store metadata and media assets for '${confirmMetadataGame?.name}'?`}
        confirmLabel="Queue Refresh"
        variant="primary"
        isLoading={actionLoading}
        onConfirm={handleMetadataConfirm}
        onCancel={() => setConfirmMetadataGame(null)}
      />

      {queueModalGame && (
        <QueueIngestionModal
          isOpen={true}
          gameId={queueModalGame.id}
          gameName={queueModalGame.name}
          isLoading={actionLoading}
          onClose={() => setQueueModalGame(null)}
          onSubmit={async (id, data) => {
            setActionLoading(true);
            try {
              await onQueueIngestion(id, data);
            } finally {
              setActionLoading(false);
            }
          }}
        />
      )}

      <NewGameModal
        isOpen={isNewGameOpen}
        isLoading={actionLoading}
        onClose={() => setIsNewGameOpen(false)}
        onSubmit={async (data) => {
          setActionLoading(true);
          try {
            await onCreateGame(data);
          } finally {
            setActionLoading(false);
          }
        }}
      />
    </div>
  );
};
