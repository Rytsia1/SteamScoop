import React from "react";
import { GameComparisonResult } from "../types/comparison";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { ThumbsUp, Brain, MessagesSquare, Gauge, AlertTriangle } from "lucide-react";
import { COMPARISON_PALETTE } from "../../../lib/tokens";

export interface ComparisonMetricsGridProps {
  games: GameComparisonResult[];
}

export const ComparisonMetricsGrid: React.FC<ComparisonMetricsGridProps> = ({ games }) => {
  if (games.length === 0) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {games.map((game, idx) => {
        const color = COMPARISON_PALETTE[idx % COMPARISON_PALETTE.length];
        const title = game.title || game.name || "Game";
        const volume = game.review_volume ?? 0;
        const isLowSample = volume < 30;

        const recRate =
          game.steam_recommendation_rate !== null && game.steam_recommendation_rate !== undefined
            ? `${(game.steam_recommendation_rate * 100).toFixed(1)}%`
            : "N/A";

        const nlpRaw = game.model_positive_rate ?? game.model_sentiment_rate;
        const nlpRate =
          nlpRaw !== null && nlpRaw !== undefined
            ? `${(nlpRaw * 100).toFixed(1)}%`
            : "N/A";

        const netScore =
          game.sentiment_score !== null && game.sentiment_score !== undefined
            ? game.sentiment_score > 0
              ? `+${game.sentiment_score.toFixed(2)}`
              : game.sentiment_score.toFixed(2)
            : "N/A";

        return (
          <Card
            key={game.game_id}
            className="relative overflow-hidden border-t-4 bg-slate-900/60"
            style={{ borderTopColor: color }}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[11px] font-mono text-slate-500">
                  {game.steam_app_id ? `App ID: ${game.steam_app_id}` : `ID: ${game.game_id.slice(0, 8)}`}
                </span>
                {isLowSample && (
                  <Badge variant="warning" size="sm" className="text-[10px] py-0">
                    <AlertTriangle className="w-2.5 h-2.5 mr-1" aria-hidden="true" />
                    N &lt; 30 Low Sample
                  </Badge>
                )}
              </div>
              <CardTitle className="line-clamp-1 text-base">{title}</CardTitle>
            </CardHeader>

            <CardContent className="space-y-2.5 pt-0">
              {/* Review Volume */}
              <div className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-950/40 border border-slate-800">
                <div className="flex items-center gap-2 text-slate-400">
                  <MessagesSquare className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
                  <span>Review Sample</span>
                </div>
                <span className="font-semibold text-white">
                  {volume.toLocaleString()}
                </span>
              </div>

              {/* Steam Recommendation */}
              <div className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-950/40 border border-slate-800">
                <div className="flex items-center gap-2 text-slate-400">
                  <ThumbsUp className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" />
                  <span>Steam Recommendation</span>
                </div>
                <span className="font-semibold text-emerald-400">{recRate}</span>
              </div>

              {/* Model Sentiment */}
              <div className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-950/40 border border-slate-800">
                <div className="flex items-center gap-2 text-slate-400">
                  <Brain className="w-3.5 h-3.5 text-sky-400" aria-hidden="true" />
                  <span>Model Positive Rate</span>
                </div>
                <span className="font-semibold text-sky-400">{nlpRate}</span>
              </div>

              {/* Net Sentiment Score */}
              <div className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-950/40 border border-slate-800">
                <div className="flex items-center gap-2 text-slate-400">
                  <Gauge className="w-3.5 h-3.5 text-purple-400" aria-hidden="true" />
                  <span>Net Sentiment Score</span>
                </div>
                <span className="font-semibold text-purple-300 font-mono">{netScore}</span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

