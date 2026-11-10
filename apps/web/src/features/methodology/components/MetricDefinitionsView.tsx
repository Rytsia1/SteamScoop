import React from "react";
import { MetricDefinitions } from "../types/methodology";
import { Card, CardTitle } from "../../../components/ui/Card";
import { BookOpen } from "lucide-react";

export const MetricDefinitionsView: React.FC<{ definitions: MetricDefinitions }> = ({
  definitions,
}) => {
  return (
    <Card className="p-6 space-y-4">
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <BookOpen className="w-5 h-5 text-sky-400" aria-hidden="true" />
        <CardTitle className="text-base font-bold text-white">
          Formal Metric & Analytical Definitions
        </CardTitle>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
          <span className="font-bold text-sky-400 block">Steam Recommendation Status</span>
          <p className="text-slate-300 leading-relaxed">{definitions.steam_recommendation}</p>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
          <span className="font-bold text-emerald-400 block">NLP Model Sentiment Score</span>
          <p className="text-slate-300 leading-relaxed">{definitions.model_sentiment}</p>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
          <span className="font-bold text-purple-400 block">Aspect Polarity (ABSA)</span>
          <p className="text-slate-300 leading-relaxed">{definitions.aspect_sentiment}</p>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 space-y-1">
          <span className="font-bold text-amber-400 block">Topic Prevalence Share</span>
          <p className="text-slate-300 leading-relaxed">{definitions.topic_prevalence}</p>
        </div>
      </div>
    </Card>
  );
};
