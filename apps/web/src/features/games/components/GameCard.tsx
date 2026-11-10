import React, { useState } from "react";
import { GameItem, getGameName, getGameDeveloper } from "../types/game";
import { Card, CardContent } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { Link } from "../../../app/router/Router";
import { gameOverviewPath, gameReviewsPath } from "../../../app/router/routes";
import {
  ThumbsUp,
  Brain,
  MessagesSquare,
  Calendar,
  ImageOff,
  ChevronRight,
} from "lucide-react";

export interface GameCardProps {
  game: GameItem;
}

export const GameCard: React.FC<GameCardProps> = ({ game }) => {
  const [imageError, setImageError] = useState(false);
  const title = getGameName(game);
  const developer = getGameDeveloper(game);

  const statusBadgeVariant =
    game.catalog_status === "indexed"
      ? "positive"
      : game.catalog_status === "failed"
      ? "negative"
      : "warning";

  const formattedReleaseDate = game.release_date
    ? new Date(game.release_date).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "TBA / Unavailable";

  const visibleGenres = (game.genres || []).slice(0, 3);
  const extraGenresCount = (game.genres || []).length - visibleGenres.length;

  return (
    <Card hoverable className="flex flex-col justify-between h-full group overflow-hidden">
      {/* Game Header Banner Image */}
      <div className="relative w-full h-36 bg-slate-950 border-b border-slate-800/80 overflow-hidden flex items-center justify-center">
        {game.header_image_url && !imageError ? (
          <img
            src={game.header_image_url}
            alt={`${title} cover`}
            loading="lazy"
            onError={() => setImageError(true)}
            className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="flex flex-col items-center justify-center gap-1.5 text-slate-600">
            <ImageOff className="w-8 h-8" aria-hidden="true" />
            <span className="text-[11px] font-mono">No Image Available</span>
          </div>
        )}

        {/* Floating Badges */}
        <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
          <Badge variant={statusBadgeVariant} size="sm" className="shadow-md backdrop-blur-sm bg-opacity-90">
            {String(game.catalog_status).toUpperCase()}
          </Badge>
        </div>

        <div className="absolute top-2.5 right-2.5">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-950/80 backdrop-blur-sm text-slate-300 border border-slate-700/60 shadow">
            App #{game.steam_app_id}
          </span>
        </div>
      </div>

      <CardContent className="p-5 flex-1 flex flex-col justify-between gap-4">
        {/* Title, Developer & Release Date */}
        <div className="space-y-1.5">
          <Link
            to={gameOverviewPath(game.id)}
            className="text-base font-bold text-white group-hover:text-sky-400 transition-colors line-clamp-1 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-sky-400 rounded"
          >
            {title}
          </Link>

          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="line-clamp-1 max-w-[60%]">{developer}</span>
            <span className="flex items-center gap-1 text-[11px] text-slate-500 shrink-0">
              <Calendar className="w-3 h-3 text-slate-500" aria-hidden="true" />
              {formattedReleaseDate}
            </span>
          </div>
        </div>

        {/* Genres & Tags */}
        <div className="flex flex-wrap gap-1.5">
          {visibleGenres.length > 0 ? (
            visibleGenres.map((genre) => (
              <span
                key={genre}
                className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700/50"
              >
                {genre}
              </span>
            ))
          ) : (
            <span className="text-[11px] text-slate-500 italic">No genres listed</span>
          )}
          {extraGenresCount > 0 && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-800/60 text-slate-400 border border-slate-700/40">
              +{extraGenresCount}
            </span>
          )}
        </div>

        {/* Intelligence Metric Comparison Strip */}
        <div className="grid grid-cols-2 gap-2 pt-3 border-t border-slate-800/80 text-xs">
          {/* Steam Recommendation */}
          <div className="p-2 rounded-lg bg-slate-950/40 border border-slate-800/60 flex flex-col gap-0.5">
            <div className="flex items-center gap-1.5 text-slate-400 text-[11px]">
              <ThumbsUp className="w-3 h-3 text-sky-400" aria-hidden="true" />
              <span>Steam Rec.</span>
            </div>
            <span className="font-semibold text-slate-200">
              {game.steam_positive_percentage !== null &&
              game.steam_positive_percentage !== undefined
                ? `${game.steam_positive_percentage.toFixed(0)}%`
                : "N/A"}
            </span>
          </div>

          {/* Model Sentiment */}
          <div className="p-2 rounded-lg bg-slate-950/40 border border-slate-800/60 flex flex-col gap-0.5">
            <div className="flex items-center gap-1.5 text-slate-400 text-[11px]">
              <Brain className="w-3 h-3 text-emerald-400" aria-hidden="true" />
              <span>NLP Sentiment</span>
            </div>
            <span className="font-semibold text-emerald-400">
              {game.model_sentiment_positive_rate !== null &&
              game.model_sentiment_positive_rate !== undefined
                ? `${(game.model_sentiment_positive_rate * 100).toFixed(0)}%`
                : "N/A"}
            </span>
          </div>
        </div>

        {/* Footer: Reviews count and Explore CTA */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs text-slate-400">
          <Link
            to={gameReviewsPath(game.id)}
            className="flex items-center gap-1.5 text-slate-400 hover:text-slate-200 transition-colors focus-visible:outline-none"
          >
            <MessagesSquare className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
            <span className="text-[11px]">
              {game.review_count !== undefined && game.review_count !== null
                ? `${game.review_count.toLocaleString()} reviews collected`
                : "Explore reviews"}
            </span>
          </Link>

          <Link
            to={gameOverviewPath(game.id)}
            className="inline-flex items-center gap-1 text-sky-400 hover:text-sky-300 font-semibold text-xs group-hover:translate-x-0.5 transition-all focus-visible:outline-none"
          >
            <span>Overview</span>
            <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
          </Link>
        </div>
      </CardContent>
    </Card>
  );
};
