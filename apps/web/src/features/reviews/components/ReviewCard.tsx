import React, { useState } from "react";
import { ReviewItem } from "../types/review";
import { Card, CardContent } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { Button } from "../../../components/ui/Button";
import { ThumbsUp, ThumbsDown, Clock, Sparkles, Calendar, HelpCircle } from "lucide-react";

export interface ReviewCardProps {
  review: ReviewItem;
  onViewIntelligence: (review: ReviewItem) => void;
}

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return "Date unrecorded";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export const ReviewCard: React.FC<ReviewCardProps> = ({ review, onViewIntelligence }) => {
  const [expanded, setExpanded] = useState(false);

  const playtimeHours = review.steam_playtime_forever
    ? (review.steam_playtime_forever / 60).toFixed(1)
    : null;

  const sentimentLabel = review.sentiment?.label?.toLowerCase();
  const sentimentVariant =
    sentimentLabel === "positive"
      ? "positive"
      : sentimentLabel === "negative"
      ? "negative"
      : sentimentLabel === "neutral"
      ? "neutral"
      : "outline";

  const isLongText = review.review_text.length > 360;
  const displayText =
    isLongText && !expanded
      ? `${review.review_text.slice(0, 360)}...`
      : review.review_text;

  return (
    <Card className="hover:border-slate-700 transition-colors">
      <CardContent className="p-5 flex flex-col gap-3.5">
        {/* Top Header: Steam Recommendation vs NLP Model Sentiment */}
        <div className="flex flex-wrap items-center justify-between gap-2.5">
          <div className="flex flex-wrap items-center gap-2">
            {/* Steam Player Recommendation */}
            <div title="Player recommendation vote submitted on Steam">
              {review.voted_up ? (
                <Badge variant="positive" size="sm" className="gap-1 font-semibold">
                  <ThumbsUp className="w-3 h-3" aria-hidden="true" />
                  <span>Steam: Recommended</span>
                </Badge>
              ) : (
                <Badge variant="negative" size="sm" className="gap-1 font-semibold">
                  <ThumbsDown className="w-3 h-3" aria-hidden="true" />
                  <span>Steam: Not Recommended</span>
                </Badge>
              )}
            </div>

            {/* NLP Sentiment Model Prediction */}
            <div title="Machine learning model prediction on review text">
              {review.sentiment ? (
                <Badge variant={sentimentVariant} size="sm" className="font-mono">
                  <span>NLP: {review.sentiment.label.toUpperCase()}</span>
                  {review.sentiment.confidence !== null && review.sentiment.confidence !== undefined && (
                    <span className="opacity-80 ml-1">
                      ({(review.sentiment.confidence * 100).toFixed(0)}%)
                    </span>
                  )}
                </Badge>
              ) : (
                <Badge variant="outline" size="sm" className="text-slate-400 font-mono">
                  <HelpCircle className="w-2.5 h-2.5 mr-1" aria-hidden="true" />
                  <span>NLP: Unclassified</span>
                </Badge>
              )}
            </div>
          </div>

          {/* Metadata: Date, Playtime, Language */}
          <div className="flex flex-wrap items-center gap-2.5 text-xs text-slate-400 font-mono">
            {review.steam_created_at && (
              <span className="flex items-center gap-1 text-[11px] text-slate-400">
                <Calendar className="w-3 h-3 text-slate-500" aria-hidden="true" />
                <time dateTime={review.steam_created_at}>
                  {formatDate(review.steam_created_at)}
                </time>
              </span>
            )}
            {playtimeHours && (
              <span className="flex items-center gap-1 text-[11px]">
                <Clock className="w-3 h-3 text-slate-400" aria-hidden="true" />
                <span>{playtimeHours} hrs</span>
              </span>
            )}
            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 uppercase text-[10px]">
              {review.language}
            </span>
          </div>
        </div>

        {/* Review Text */}
        <p className="text-xs sm:text-sm text-slate-200 leading-relaxed whitespace-pre-line font-sans">
          {displayText}
        </p>

        {isLongText && (
          <button
            type="button"
            onClick={() => setExpanded((prev) => !prev)}
            className="text-xs text-sky-400 hover:text-sky-300 font-medium self-start focus-visible:outline-none"
          >
            {expanded ? "Show less" : "Read full review"}
          </button>
        )}

        {/* Footer info & Intelligence trigger */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs text-slate-400">
          <div className="flex items-center gap-3 text-[11px]">
            <span>{review.votes_up.toLocaleString()} found helpful</span>
            {review.votes_funny > 0 && (
              <span>&bull; {review.votes_funny.toLocaleString()} funny</span>
            )}
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => onViewIntelligence(review)}
            leftIcon={<Sparkles className="w-3.5 h-3.5 text-sky-400" aria-hidden="true" />}
            className="text-sky-400 hover:text-sky-300 hover:bg-sky-950/40"
          >
            Review Intelligence & Details
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
