import React from "react";
import { ReviewSortOption } from "../types/review";
import { Select } from "../../../components/ui/Select";
import { Button } from "../../../components/ui/Button";
import { Filter, X } from "lucide-react";

export interface ReviewFiltersProps {
  sentiment: string;
  onSentimentChange: (val: string) => void;
  votedUp: string;
  onVotedUpChange: (val: string) => void;
  aspect: string;
  onAspectChange: (val: string) => void;
  language: string;
  onLanguageChange: (val: string) => void;
  sort: ReviewSortOption | string;
  onSortChange: (val: string) => void;
  onReset: () => void;
}

export const ReviewFilters: React.FC<ReviewFiltersProps> = ({
  sentiment,
  onSentimentChange,
  votedUp,
  onVotedUpChange,
  aspect,
  onAspectChange,
  language,
  onLanguageChange,
  sort = "created_at_desc",
  onSortChange,
  onReset,
}) => {
  const sentimentOptions = [
    { value: "", label: "All Model Sentiments" },
    { value: "positive", label: "Positive Sentiment" },
    { value: "negative", label: "Negative Sentiment" },
    { value: "neutral", label: "Neutral / Ambiguous" },
    { value: "unclassified", label: "Unclassified / Abstained" },
  ];

  const recommendationOptions = [
    { value: "", label: "All Steam Recommendations" },
    { value: "true", label: "Recommended (Thumbs Up)" },
    { value: "false", label: "Not Recommended (Thumbs Down)" },
  ];

  const aspectOptions = [
    { value: "", label: "All Aspects Discussed" },
    { value: "gameplay", label: "Gameplay & Mechanics" },
    { value: "performance", label: "Performance & Stability" },
    { value: "graphics", label: "Graphics & Art Style" },
    { value: "story", label: "Story & Narrative" },
    { value: "audio", label: "Audio & Music" },
    { value: "multiplayer", label: "Multiplayer & Netcode" },
    { value: "pricing", label: "Pricing & Value" },
  ];

  const languageOptions = [
    { value: "", label: "All Languages" },
    { value: "english", label: "English" },
    { value: "schinese", label: "Simplified Chinese" },
    { value: "russian", label: "Russian" },
    { value: "german", label: "German" },
    { value: "french", label: "French" },
    { value: "spanish", label: "Spanish" },
    { value: "japanese", label: "Japanese" },
  ];

  const sortOptions = [
    { value: "created_at_desc", label: "Most Recent First" },
    { value: "created_at_asc", label: "Oldest First" },
    { value: "votes_up_desc", label: "Most Helpful First" },
  ];

  const hasActiveFilters = Boolean(
    sentiment || votedUp || aspect || language || sort !== "created_at_desc"
  );

  return (
    <div className="w-full rounded-xl border border-slate-800 bg-slate-900/60 p-4 sm:p-5 flex flex-col gap-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <Select
          label="Model Sentiment"
          value={sentiment}
          onChange={(e) => onSentimentChange(e.target.value)}
          options={sentimentOptions}
          aria-label="Filter by model sentiment"
        />
        <Select
          label="Steam Recommendation"
          value={votedUp}
          onChange={(e) => onVotedUpChange(e.target.value)}
          options={recommendationOptions}
          aria-label="Filter by Steam recommendation"
        />
        <Select
          label="Aspect Dimension"
          value={aspect}
          onChange={(e) => onAspectChange(e.target.value)}
          options={aspectOptions}
          aria-label="Filter by discussed aspect"
        />
        <Select
          label="Language"
          value={language}
          onChange={(e) => onLanguageChange(e.target.value)}
          options={languageOptions}
          aria-label="Filter by review language"
        />
        <Select
          label="Sort Reviews"
          value={sort}
          onChange={(e) => onSortChange(e.target.value)}
          options={sortOptions}
          aria-label="Sort order"
        />
      </div>

      <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 text-xs text-slate-400">
        <div className="flex items-center gap-1.5">
          <Filter className="w-3.5 h-3.5 text-sky-400" aria-hidden="true" />
          <span>
            Filtering by NLP inferences, Steam verdict, and community attributes
          </span>
        </div>

        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            className="text-xs text-slate-400 hover:text-white"
            leftIcon={<X className="w-3 h-3" aria-hidden="true" />}
          >
            Reset Filters
          </Button>
        )}
      </div>
    </div>
  );
};
