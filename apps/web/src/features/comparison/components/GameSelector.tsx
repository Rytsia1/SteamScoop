import React, { useState } from "react";
import { GameItem } from "../../games/types/game";
import { Badge } from "../../../components/ui/Badge";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { X, Plus, AlertCircle } from "lucide-react";

export interface GameSelectorProps {
  availableGames: GameItem[] | undefined;
  selectedGameIds: string[];
  onSelectGame: (gameId: string) => void;
  onRemoveGame: (gameId: string) => void;
  isLoadingAvailable?: boolean;
}

export const GameSelector: React.FC<GameSelectorProps> = ({
  availableGames = [],
  selectedGameIds,
  onSelectGame,
  onRemoveGame,
  isLoadingAvailable,
}) => {
  const [searchQuery, setSearchQuery] = useState("");

  const selectedGames = availableGames.filter((g) => selectedGameIds.includes(g.id));
  const unselectedGames = availableGames
    .filter((g) => !selectedGameIds.includes(g.id))
    .filter((g) =>
      searchQuery.trim() === ""
        ? true
        : (g.title || "").toLowerCase().includes(searchQuery.toLowerCase())
    );

  const count = selectedGameIds.length;
  const isTooFew = count < 2;
  const isMaxReached = count >= 5;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-white">Select Games to Compare</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Select between 2 and 5 games for comparative intelligence analysis.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant={isTooFew ? "warning" : "positive"}
            size="sm"
            className="font-mono"
          >
            {count} / 5 Selected
          </Badge>
        </div>
      </div>

      {/* Selected Games Badges */}
      <div className="flex flex-wrap gap-2 min-h-10 items-center p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
        {selectedGames.length === 0 ? (
          <span className="text-xs text-slate-500 italic">
            No games selected yet. Choose from the available catalog below.
          </span>
        ) : (
          selectedGames.map((game) => (
            <div
              key={game.id}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-medium text-white shadow-sm"
            >
              <span>{game.title}</span>
              <button
                type="button"
                onClick={() => onRemoveGame(game.id)}
                aria-label={`Remove ${game.title} from comparison`}
                className="text-slate-400 hover:text-rose-400 focus-visible:outline-none"
              >
                <X className="w-3.5 h-3.5" aria-hidden="true" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Warning message if fewer than 2 */}
      {isTooFew && (
        <div className="flex items-center gap-2 text-xs text-amber-400/90 font-medium">
          <AlertCircle className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Please select at least 2 games to perform a valid comparison.</span>
        </div>
      )}

      {/* Available Games Picker */}
      {!isMaxReached && (
        <div className="space-y-2 pt-2 border-t border-slate-800/80">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <span className="text-xs font-semibold text-slate-400 block">
              Add from Indexed Catalog:
            </span>
            {availableGames.length > 6 && (
              <div className="w-full sm:w-64">
                <Input
                  type="text"
                  placeholder="Filter catalog..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="py-1 text-xs"
                />
              </div>
            )}
          </div>
          {isLoadingAvailable ? (
            <div className="text-xs text-slate-500">Loading catalog games...</div>
          ) : (
            <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
              {unselectedGames.length === 0 ? (
                <span className="text-xs text-slate-500 italic py-1">
                  {searchQuery ? "No games match your search query." : "All available games are already selected."}
                </span>
              ) : (
                unselectedGames.map((game) => (
                  <Button
                    key={game.id}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      onSelectGame(game.id);
                      setSearchQuery("");
                    }}
                    leftIcon={<Plus className="w-3 h-3 text-sky-400" aria-hidden="true" />}
                    className="text-xs py-1"
                  >
                    {game.title}
                  </Button>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

