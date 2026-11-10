import React from "react";
import { GameAspectsData } from "../types/intelligence";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { AspectBarChart } from "../../../components/charts/AspectBarChart";
import { EmptyState } from "../../../components/feedback/EmptyState";
import { Layers, AlertCircle } from "lucide-react";

export interface AspectBreakdownCardProps {
  aspectsData: GameAspectsData | undefined;
  isLoading: boolean;
}

export const AspectBreakdownCard: React.FC<AspectBreakdownCardProps> = ({
  aspectsData,
  isLoading,
}) => {
  if (isLoading || !aspectsData) {
    return (
      <div className="h-64 rounded-xl border border-slate-800 bg-slate-900/40 animate-pulse" />
    );
  }

  const hasAspects = aspectsData.aspects && aspectsData.aspects.length > 0;

  const chartData = hasAspects
    ? aspectsData.aspects.map((asp) => ({
        aspect: asp.display_name,
        mentionCount: asp.mention_count,
        positiveRate: asp.positive_rate,
        negativeRate: asp.negative_rate,
      }))
    : [];

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Aspect-Based Sentiment Analysis (ABSA)</CardTitle>
          <p className="text-xs text-slate-400 mt-0.5">
            Identifies specific game features players discuss and the sentiment tied to each.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" size="sm" className="font-mono text-slate-400">
            <Layers className="w-3 h-3 mr-1 text-purple-400" aria-hidden="true" />
            Taxonomy: {aspectsData.taxonomy_version}
          </Badge>
          <Badge variant="outline" size="sm" className="font-mono text-slate-400">
            Model: {aspectsData.model_version}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {!hasAspects ? (
          <EmptyState
            icon={<AlertCircle className="w-8 h-8 text-slate-500" />}
            title="Insufficient Aspect Data"
            description="No aspect mentions were detected in the currently collected review sample. ABSA requires structured reviews referencing specific gameplay, performance, or technical aspects."
          />
        ) : (
          <>
            <AspectBarChart data={chartData} height={320} />

            {/* Aspect Prevalence Badges */}
            <div className="pt-2 border-t border-slate-800">
              <h5 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Top Discussed Dimensions ({aspectsData.total_aspect_mentions.toLocaleString()} total mentions)
              </h5>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {aspectsData.aspects.slice(0, 8).map((asp) => (
                  <div
                    key={asp.aspect_key}
                    className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/80 flex flex-col gap-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white">{asp.display_name}</span>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {(asp.prevalence * 100).toFixed(0)}% prev.
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden flex">
                      <div
                        style={{ width: `${asp.positive_rate * 100}%` }}
                        className="bg-emerald-500 h-full"
                        title={`Positive: ${(asp.positive_rate * 100).toFixed(1)}%`}
                      />
                      <div
                        style={{ width: `${asp.negative_rate * 100}%` }}
                        className="bg-rose-500 h-full"
                        title={`Negative: ${(asp.negative_rate * 100).toFixed(1)}%`}
                      />
                    </div>
                    <div className="flex items-center justify-between text-[11px] pt-0.5">
                      <span className="text-emerald-400 font-medium">
                        +{(asp.positive_rate * 100).toFixed(0)}%
                      </span>
                      <span className="text-rose-400 font-medium">
                        -{(asp.negative_rate * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};
