import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { HelpCircle, AlertTriangle, Info, CheckCircle2 } from "lucide-react";

export interface ComparisonMethodologyNoticeProps {
  modelVersions?: string[];
  hasInsufficientDataGames?: boolean;
}

export const ComparisonMethodologyNotice: React.FC<ComparisonMethodologyNoticeProps> = ({
  modelVersions = [],
  hasInsufficientDataGames = false,
}) => {
  const uniqueModels = Array.from(new Set(modelVersions.filter(Boolean)));
  const hasIncompatibleModels = uniqueModels.length > 1;

  return (
    <Card className="w-full border-slate-800 bg-slate-900/40">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-sky-400" aria-hidden="true" />
          <CardTitle className="text-sm font-semibold text-white">
            Comparative Methodology, Metric Definitions & Model Compatibility
          </CardTitle>
        </div>
        <p className="text-xs text-slate-400 mt-0.5">
          Standardized metric formulations, statistical confidence criteria, and model compatibility disclosures.
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Incompatible Model Versions Warning */}
        {hasIncompatibleModels ? (
          <div
            className="p-3.5 rounded-xl border border-amber-900/60 bg-amber-950/20 text-xs text-amber-200 flex items-start gap-3"
            role="alert"
          >
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="space-y-1">
              <span className="font-semibold block text-amber-300">
                Incompatible Model Versions Detected across Titles
              </span>
              <p className="text-[11px] text-amber-200/90 leading-relaxed">
                The evaluated games were analyzed using different machine learning model versions (
                {uniqueModels.join(", ")}). Direct score comparisons may reflect calibration differences rather than genuine community perception shifts.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-xs text-emerald-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" aria-hidden="true" />
            <span>
              Model Harmonization: All compared titles use compatible model version:{" "}
              <b className="font-mono text-emerald-200">{uniqueModels[0] || "Standard Baseline"}</b>
            </span>
          </div>
        )}

        {/* Insufficient Sample Size Callout */}
        {hasInsufficientDataGames && (
          <div
            className="p-3.5 rounded-xl border border-amber-900/50 bg-amber-950/20 text-xs text-amber-300 flex items-start gap-3"
            role="alert"
          >
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <span className="font-semibold block">Sample Size Safeguard ($N &lt; 30$)</span>
              <p className="text-[11px] text-amber-200/90 leading-relaxed mt-0.5">
                One or more selected titles have fewer than 30 indexed reviews in the database. Aspect and topic metrics for low-volume games are provisional and exhibit high statistical variance.
              </p>
            </div>
          </div>
        )}

        {/* Metric Formulations Table */}
        <div className="space-y-1.5 pt-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
            <Info className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            <span>Consistent Metric Definitions</span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                  <th scope="col" className="py-2 px-3 font-semibold">Comparative Metric</th>
                  <th scope="col" className="py-2 px-3 font-semibold">Formula / Denominator</th>
                  <th scope="col" className="py-2 px-3 font-semibold">Scale</th>
                  <th scope="col" className="py-2 px-3 font-semibold">Methodological Integrity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                <tr>
                  <td className="py-2 px-3 font-medium text-white">Review Volume</td>
                  <td className="py-2 px-3 font-mono text-[11px] text-slate-400">Count(Reviews) in window</td>
                  <td className="py-2 px-3 text-slate-400">Integer</td>
                  <td className="py-2 px-3 text-slate-400">Raw sample size indexed in database.</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-medium text-white">Steam Recommendation Rate</td>
                  <td className="py-2 px-3 font-mono text-[11px] text-emerald-400">
                    Pos_Steam / (Pos_Steam + Neg_Steam)
                  </td>
                  <td className="py-2 px-3 text-slate-400">0% – 100%</td>
                  <td className="py-2 px-3 text-slate-400">Direct player thumbs-up verdict on Steam.</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-medium text-white">Model Positive Sentiment Rate</td>
                  <td className="py-2 px-3 font-mono text-[11px] text-sky-400">
                    Pos_Count / Classified_Count
                  </td>
                  <td className="py-2 px-3 text-slate-400">0% – 100%</td>
                  <td className="py-2 px-3 text-slate-400">
                    Excludes neutral and unclassified reviews from polarity denominator.
                  </td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-medium text-white">Net Sentiment Score</td>
                  <td className="py-2 px-3 font-mono text-[11px] text-purple-400">
                    (Pos - Neg) / Classified
                  </td>
                  <td className="py-2 px-3 text-slate-400">-1.0 to +1.0</td>
                  <td className="py-2 px-3 text-slate-400">
                    Zero represents neutral balance; non-truncated visual scale.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Provenance footer badges */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800 text-xs">
          <span className="text-slate-400 text-[11px]">Active Evaluation Models:</span>
          {uniqueModels.map((m) => (
            <Badge key={m} variant="outline" size="sm" className="font-mono text-[11px] text-slate-300">
              {m}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

