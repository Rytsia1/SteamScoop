import React from "react";
import { ReviewItem } from "../types/review";
import { useReview, useReviewIntelligence } from "../api/reviewsApi";
import { Modal } from "../../../components/ui/Modal";
import { Badge } from "../../../components/ui/Badge";
import { Skeleton } from "../../../components/feedback/LoadingSkeleton";
import { ErrorAlert } from "../../../components/feedback/ErrorAlert";
import { Button } from "../../../components/ui/Button";
import {
  Brain,
  Layers,
  MessageSquareText,
  ThumbsUp,
  ThumbsDown,
  ShieldCheck,
  Quote,
  HelpCircle,
} from "lucide-react";

export interface ReviewIntelligenceModalProps {
  review: ReviewItem | null;
  isOpen: boolean;
  onClose: () => void;
}

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return "N/A";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export const ReviewIntelligenceModal: React.FC<ReviewIntelligenceModalProps> = ({
  review,
  isOpen,
  onClose,
}) => {
  const reviewId = isOpen ? review?.id : undefined;

  const {
    data: detailData,
    isLoading: isLoadingDetail,
  } = useReview(reviewId);

  const {
    data: intelligence,
    isLoading: isLoadingIntel,
    error: intelError,
    refetch: refetchIntel,
  } = useReviewIntelligence(reviewId);

  if (!review) return null;

  const effectiveDetail = detailData || review;
  const isLoading = isLoadingDetail || isLoadingIntel;

  const playtimeHours = effectiveDetail.steam_playtime_forever
    ? (effectiveDetail.steam_playtime_forever / 60).toFixed(1)
    : null;

  const playtimeAtReviewHours =
    detailData?.steam_playtime_at_review
      ? (detailData.steam_playtime_at_review / 60).toFixed(1)
      : null;

  const sentiment = intelligence?.sentiment || effectiveDetail.sentiment;
  const sentimentLabel = sentiment?.label?.toLowerCase();
  const sentimentVariant =
    sentimentLabel === "positive"
      ? "positive"
      : sentimentLabel === "negative"
      ? "negative"
      : sentimentLabel === "neutral"
      ? "neutral"
      : "outline";

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Review Intelligence & Metadata Details"
      description={`Review ID: ${review.id}`}
      maxWidth="2xl"
      footer={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" />
            <span>Privacy Preserved: Author profile data and personal SteamIDs are not stored or exposed.</span>
          </div>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Signals Header: Steam Recommendation vs NLP Model Sentiment */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Signal 1: Steam Player Recommendation */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex items-start gap-3">
            <div
              className={`p-2 rounded-lg shrink-0 ${
                effectiveDetail.voted_up
                  ? "bg-emerald-950/60 text-emerald-400"
                  : "bg-rose-950/60 text-rose-400"
              }`}
            >
              {effectiveDetail.voted_up ? (
                <ThumbsUp className="w-4 h-4" aria-hidden="true" />
              ) : (
                <ThumbsDown className="w-4 h-4" aria-hidden="true" />
              )}
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Steam Player Verdict
              </span>
              <span className="text-sm font-semibold text-white">
                {effectiveDetail.voted_up ? "Recommended (Thumbs Up)" : "Not Recommended (Thumbs Down)"}
              </span>
              <span className="text-[11px] text-slate-400 block mt-0.5">
                Submitted directly by Steam player
              </span>
            </div>
          </div>

          {/* Signal 2: NLP Text Sentiment */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 flex items-start gap-3">
            <div className="p-2 rounded-lg bg-sky-950/60 text-sky-400 shrink-0">
              <Brain className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                NLP Model Classification
              </span>
              <div className="flex items-center gap-2 mt-0.5">
                {sentiment ? (
                  <Badge variant={sentimentVariant} size="sm" className="font-mono">
                    {sentiment.label.toUpperCase()}
                  </Badge>
                ) : (
                  <Badge variant="outline" size="sm" className="text-slate-400 font-mono">
                    UNCLASSIFIED
                  </Badge>
                )}
                {sentiment?.confidence !== null && sentiment?.confidence !== undefined && (
                  <span className="text-xs font-mono text-sky-300">
                    {(sentiment.confidence * 100).toFixed(1)}% conf.
                  </span>
                )}
              </div>
              <span className="text-[11px] text-slate-500 font-mono block mt-1">
                Model: {sentiment?.model_version || "Not evaluated"}
              </span>
            </div>
          </div>
        </div>

        {/* Full Review Text */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold text-slate-300 flex items-center gap-1.5">
              <Quote className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
              <span>Full Review Content</span>
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Language: {effectiveDetail.language}
            </span>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs sm:text-sm text-slate-200 leading-relaxed font-sans max-h-56 overflow-y-auto whitespace-pre-line">
            {effectiveDetail.review_text}
          </div>
        </div>

        {/* Public Metadata Attributes */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/40 text-xs">
          <div>
            <span className="text-slate-500 block text-[11px]">Reviewed On</span>
            <span className="font-medium text-slate-200">
              {formatDate(effectiveDetail.steam_created_at)}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Playtime at Review</span>
            <span className="font-medium text-slate-200">
              {playtimeAtReviewHours ? `${playtimeAtReviewHours} hrs` : playtimeHours ? `${playtimeHours} hrs` : "N/A"}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Community Helpful</span>
            <span className="font-medium text-slate-200">
              {(effectiveDetail.votes_up ?? 0).toLocaleString()} votes
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Steam Review ID</span>
            <span className="font-mono text-slate-300 text-[11px]">
              {effectiveDetail.steam_review_id ?? "N/A"}
            </span>
          </div>
        </div>

        {/* Loading / Error States for Intelligence */}
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton variant="text" className="w-48 h-4" />
            <Skeleton variant="rectangular" className="w-full h-20" />
            <Skeleton variant="rectangular" className="w-full h-20" />
          </div>
        ) : intelError ? (
          <ErrorAlert
            title="Could not load multi-task intelligence"
            message={intelError.message}
            onRetry={() => refetchIntel()}
          />
        ) : intelligence ? (
          <div className="space-y-5">
            {/* Aspect-Level Sentiment Analysis (ABSA) */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400" aria-hidden="true" />
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                    Aspect-Level Predictions ({intelligence.aspects.length})
                  </h4>
                </div>
                <span className="text-[11px] text-slate-500 font-mono">
                  Aspect-Based Sentiment Analysis
                </span>
              </div>

              {intelligence.aspects.length === 0 ? (
                <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/80 text-xs text-slate-500 italic flex items-center gap-2">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
                  <span>No explicit design aspects detected above the confidence threshold.</span>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {intelligence.aspects.map((asp, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-xl border border-slate-800 bg-slate-950/40 flex flex-col justify-between gap-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-white">
                          {asp.display_name}
                        </span>
                        <div className="flex items-center gap-1.5">
                          <Badge
                            variant={
                              asp.sentiment === "positive"
                                ? "positive"
                                : asp.sentiment === "negative"
                                ? "negative"
                                : "neutral"
                            }
                            size="sm"
                          >
                            {asp.sentiment.toUpperCase()}
                          </Badge>
                          {asp.confidence !== null && asp.confidence !== undefined && (
                            <span className="text-[10px] text-slate-400 font-mono">
                              {(asp.confidence * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>
                      </div>
                      {asp.evidence_text && (
                        <p className="text-[11px] text-slate-300 italic line-clamp-2 border-l-2 border-purple-500/40 pl-2">
                          &ldquo;{asp.evidence_text}&rdquo;
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Topic Assignment */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquareText className="w-4 h-4 text-sky-400" aria-hidden="true" />
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                    Topic Clustering Assignment
                  </h4>
                </div>
                <span className="text-[11px] text-slate-500 font-mono">
                  Unsupervised Topic Modeling
                </span>
              </div>

              {intelligence.topics.length === 0 ? (
                <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/80 text-xs text-slate-500 italic flex items-center gap-2">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
                  <span>Review was classified as an unclustered outlier or ambiguous topic.</span>
                </div>
              ) : (
                <div className="space-y-2">
                  {intelligence.topics.map((t, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/40 flex items-center justify-between gap-3"
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-white">
                            {t.label}
                          </span>
                          {t.is_primary && (
                            <Badge variant="info" size="sm" className="text-[10px] py-0">
                              Primary
                            </Badge>
                          )}
                        </div>
                        <span className="text-[11px] text-slate-400 font-mono block">
                          Key: {t.topic_key} &bull; Model: {t.model_version}
                        </span>
                      </div>
                      {t.score !== null && t.score !== undefined && (
                        <Badge variant="outline" size="sm" className="font-mono text-sky-300">
                          Score: {t.score.toFixed(2)}
                        </Badge>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </Modal>
  );
};
