import React, { useState } from "react";
import { ReviewItem } from "../types/review";
import { ReviewCard } from "./ReviewCard";
import { ReviewIntelligenceModal } from "./ReviewIntelligenceModal";
import { CardSkeleton } from "../../../components/feedback/LoadingSkeleton";
import { ErrorAlert } from "../../../components/feedback/ErrorAlert";
import { EmptyState } from "../../../components/feedback/EmptyState";
import { Button } from "../../../components/ui/Button";
import { PaginationMeta } from "../../../types/api";
import { ArrowLeft, ArrowRight, MessageSquareOff } from "lucide-react";

export interface ReviewListProps {
  reviews: ReviewItem[] | undefined;
  isLoading: boolean;
  error: Error | null;
  onRetry: () => void;
  pagination?: PaginationMeta | null;
  onNextPage?: () => void;
  onPrevPage?: () => void;
  hasPrevPage?: boolean;
}

export const ReviewList: React.FC<ReviewListProps> = ({
  reviews,
  isLoading,
  error,
  onRetry,
  pagination,
  onNextPage,
  onPrevPage,
  hasPrevPage = false,
}) => {
  const [selectedReview, setSelectedReview] = useState<ReviewItem | null>(null);

  if (isLoading) {
    return <CardSkeleton count={4} />;
  }

  if (error) {
    return (
      <ErrorAlert
        title="Could not load game reviews"
        message={error.message || "An unexpected error occurred while fetching reviews."}
        onRetry={onRetry}
      />
    );
  }

  if (!reviews || reviews.length === 0) {
    return (
      <EmptyState
        icon={<MessageSquareOff className="w-8 h-8 text-slate-500" />}
        title="No reviews match your filters"
        description="Try relaxing your sentiment, recommendation, or language filters to view more player feedback."
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Review Cards Stack */}
      <div className="space-y-3" role="feed" aria-label="Player reviews list">
        {reviews.map((rev) => (
          <ReviewCard
            key={rev.id}
            review={rev}
            onViewIntelligence={(r) => setSelectedReview(r)}
          />
        ))}
      </div>

      {/* Keyset / Cursor Pagination Bar */}
      {pagination && (pagination.has_more || hasPrevPage) && (
        <nav
          aria-label="Reviews pagination"
          className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-slate-800"
        >
          <span className="text-xs text-slate-400">
            {pagination.total_count !== undefined && pagination.total_count !== null
              ? `Total reviews: ${pagination.total_count.toLocaleString()}`
              : "Showing paginated review sample"}
          </span>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onPrevPage}
              disabled={!hasPrevPage}
              leftIcon={<ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />}
              aria-label="Previous review batch"
            >
              Previous Batch
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={onNextPage}
              disabled={!pagination.has_more}
              rightIcon={<ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />}
              aria-label="Next review batch"
            >
              Next Batch
            </Button>
          </div>
        </nav>
      )}

      {/* Review Intelligence & Detail Modal */}
      <ReviewIntelligenceModal
        review={selectedReview}
        isOpen={Boolean(selectedReview)}
        onClose={() => setSelectedReview(null)}
      />
    </div>
  );
};
