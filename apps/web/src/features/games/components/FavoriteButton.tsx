import React from "react";
import { Star } from "lucide-react";
import { clsx } from "clsx";
import { SavedGame, useFavorites } from "../hooks/useGameList";

export const FavoriteButton: React.FC<{ game: SavedGame; className?: string }> = ({
  game,
  className,
}) => {
  const { isFavorite, toggleFavorite } = useFavorites();
  const active = isFavorite(game.id);

  return (
    <button
      type="button"
      aria-pressed={active}
      aria-label={active ? `Remove ${game.name} from favorites` : `Add ${game.name} to favorites`}
      title={active ? "Remove from favorites" : "Add to favorites"}
      onClick={() => toggleFavorite(game)}
      className={clsx(
        "shrink-0 p-1 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400",
        active ? "text-amber-400 hover:text-amber-300" : "text-slate-500 hover:text-amber-300",
        className
      )}
    >
      <Star className={clsx("w-4 h-4", active && "fill-current")} aria-hidden="true" />
    </button>
  );
};
