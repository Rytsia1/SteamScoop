import React, { useState } from "react";
import { PlusCircle, X, Loader2 } from "lucide-react";
import { AdminGameCreate, CatalogStatus } from "../../../types/admin";

export interface NewGameModalProps {
  isOpen: boolean;
  isLoading: boolean;
  onClose: () => void;
  onSubmit: (data: AdminGameCreate) => Promise<void>;
}

export const NewGameModal: React.FC<NewGameModalProps> = ({
  isOpen,
  isLoading,
  onClose,
  onSubmit,
}) => {
  const [steamAppId, setSteamAppId] = useState("");
  const [name, setName] = useState("");
  const [shortDescription, setShortDescription] = useState("");
  const [genresText, setGenresText] = useState("");
  const [catalogStatus, setCatalogStatus] = useState<CatalogStatus>("indexed");
  const [isFree, setIsFree] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const appIdNum = parseInt(steamAppId, 10);
    if (isNaN(appIdNum) || appIdNum <= 0) {
      setError("Please provide a valid numeric Steam App ID.");
      return;
    }

    if (!name.trim()) {
      setError("Game title is required.");
      return;
    }

    const genres = genresText
      .split(",")
      .map((g) => g.trim())
      .filter(Boolean);

    try {
      await onSubmit({
        steam_app_id: appIdNum,
        name: name.trim(),
        short_description: shortDescription.trim() || undefined,
        genres: genres.length > 0 ? genres : undefined,
        catalog_status: catalogStatus,
        is_free: isFree,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add game to catalog.");
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="new-game-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150"
    >
      <div className="w-full max-w-lg rounded-xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <PlusCircle className="w-5 h-5 text-sky-400" />
            <h3 id="new-game-modal-title" className="text-base font-bold text-slate-100">
              Add Game to Catalog
            </h3>
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
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="steam-app-id-input" className="block text-xs font-medium text-slate-300 mb-1">
                Steam App ID *
              </label>
              <input
                id="steam-app-id-input"
                type="number"
                required
                value={steamAppId}
                onChange={(e) => setSteamAppId(e.target.value)}
                placeholder="e.g. 1145360"
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500 text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
              />
            </div>
            <div>
              <label htmlFor="catalog-status-select" className="block text-xs font-medium text-slate-300 mb-1">
                Catalog Status
              </label>
              <select
                id="catalog-status-select"
                value={catalogStatus}
                onChange={(e) => setCatalogStatus(e.target.value as CatalogStatus)}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
              >
                <option value="indexed">Indexed (Active Collection)</option>
                <option value="pending">Pending Review</option>
                <option value="disabled">Disabled</option>
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="game-name-input" className="block text-xs font-medium text-slate-300 mb-1">
              Game Title *
            </label>
            <input
              id="game-name-input"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Hades II"
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500 text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="game-description-input" className="block text-xs font-medium text-slate-300 mb-1">
              Short Description
            </label>
            <textarea
              id="game-description-input"
              rows={2}
              value={shortDescription}
              onChange={(e) => setShortDescription(e.target.value)}
              placeholder="Brief game synopsis or genre summary"
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500 text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="genres-input" className="block text-xs font-medium text-slate-300 mb-1">
              Genres (comma-separated)
            </label>
            <input
              id="genres-input"
              type="text"
              value={genresText}
              onChange={(e) => setGenresText(e.target.value)}
              placeholder="Action, Roguelike, Indie"
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500 text-xs focus:ring-2 focus:ring-sky-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              id="is-free-checkbox"
              type="checkbox"
              checked={isFree}
              onChange={(e) => setIsFree(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-sky-500 focus:ring-sky-500 w-4 h-4"
            />
            <label htmlFor="is-free-checkbox" className="text-xs text-slate-300 select-none">
              Free-to-play title
            </label>
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
              <span>Add Game</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

