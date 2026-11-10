import React from "react";
import { Link } from "../../../app/router/Router";
import { ROUTES } from "../../../app/router/routes";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import {
  HelpCircle,
  Cpu,
  Layers,
  MessageSquareText,
  AlertTriangle,
  Info,
  ExternalLink,
} from "lucide-react";

export interface DashboardMethodologyFooterProps {
  sentimentModelVersion?: string;
  taxonomyVersion?: string;
  topicModelVersion?: string;
  totalCollected?: number;
}

export const DashboardMethodologyFooter: React.FC<DashboardMethodologyFooterProps> = ({
  sentimentModelVersion = "sentiment-1.0.0",
  taxonomyVersion = "aspects-1.0",
  topicModelVersion = "bertopic-1.0.0",
  totalCollected = 0,
}) => {
  const isLowSample = totalCollected > 0 && totalCollected < 30;

  return (
    <Card className="w-full border-slate-800 bg-slate-900/40">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-slate-800 text-slate-300">
            <HelpCircle className="w-4 h-4 text-sky-400" aria-hidden="true" />
          </div>
          <div>
            <CardTitle className="text-sm font-semibold text-white">
              Methodology, Metric Denominators & Provenance
            </CardTitle>
            <p className="text-xs text-slate-400">
              Transparent operational definitions, statistical denominators, and active machine learning models.
            </p>
          </div>
        </div>

        <Link
          to={ROUTES.METHODOLOGY}
          className="inline-flex items-center gap-1.5 text-xs text-sky-400 hover:text-sky-300 font-medium"
        >
          <span>Full Methodology Documentation</span>
          <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
        </Link>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Low Data Warning if < 30 reviews */}
        {isLowSample && (
          <div
            className="p-4 rounded-xl border border-amber-900/60 bg-amber-950/20 flex items-start gap-3 text-xs text-amber-200"
            role="alert"
          >
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="space-y-1">
              <span className="font-semibold block text-amber-300">
                Data Volume Warning: Insufficient Sample Size ($N = {totalCollected} &lt; 30$)
              </span>
              <p className="text-amber-200/90 leading-relaxed">
                SteamScoop requires a minimum threshold of 30 reviews for robust ABSA aspect decomposition and unsupervised topic clustering. When review volume is below 30, metrics exhibit high variance and machine learning models may abstain.
              </p>
            </div>
          </div>
        )}

        {/* Metric Denominators Table */}
        <div className="space-y-2">
          <h5 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            <span>Mathematical Metric Formulations</span>
          </h5>

          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                  <th scope="col" className="py-2.5 px-3 font-semibold">Metric</th>
                  <th scope="col" className="py-2.5 px-3 font-semibold">Mathematical Formula / Denominator</th>
                  <th scope="col" className="py-2.5 px-3 font-semibold">Unit & Scale</th>
                  <th scope="col" className="py-2.5 px-3 font-semibold">Interpretation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                <tr>
                  <td className="py-2 px-3 font-medium text-white">Steam Recommendation Rate</td>
                  <td className="py-2 px-3 font-mono text-[11px] text-slate-300">
                    Pos_Steam / (Pos_Steam + Neg_Steam)
                  </td>
                  <td className="py-2 px-3 text-slate-400">0% – 100%</td>
                  <td className="py-2 px-3 text-slate-400">Binary thumbs-up recommendation submitted on Steam.</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-medium text-white">Model Positive Sentiment Rate</td>
                  <td className="py-2 px-3 font-mono text-[11px] text-emerald-400">
                    Pos_Count / Classified_Count
                  </td>
                  <td className="py-2 px-3 text-slate-400">0% – 100%</td>
                  <td className="py-2 px-3 text-slate-400">
                    NLP sentiment on text. <i>Excludes neutral and abstained/unclassified</i> from polarity denominator.
                  </td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-medium text-white">Net Sentiment Score</td>
                  <td className="py-2 px-3 font-mono text-[11px] text-sky-400">
                    (Pos_Count - Neg_Count) / Classified_Count
                  </td>
                  <td className="py-2 px-3 text-slate-400">-1.0 to +1.0</td>
                  <td className="py-2 px-3 text-slate-400">
                    Standardized sentiment polarity index where 0.0 is balanced equilibrium.
                  </td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-medium text-white">Aspect Prevalence</td>
                  <td className="py-2 px-3 font-mono text-[11px] text-purple-400">
                    Mentions(Aspect) / Total_Reviews_Evaluated
                  </td>
                  <td className="py-2 px-3 text-slate-400">0% – 100%</td>
                  <td className="py-2 px-3 text-slate-400">
                    Share of reviews that actively discuss this specific game dimension.
                  </td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-medium text-white">Sample Coverage Ratio</td>
                  <td className="py-2 px-3 font-mono text-[11px] text-slate-300">
                    Reviews_Collected / Total_Available_Steam
                  </td>
                  <td className="py-2 px-3 text-slate-400">0% – 100%</td>
                  <td className="py-2 px-3 text-slate-400">
                    Percentage of public Steam reviews ingested and available for analysis.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Model Provenance Badges */}
        <div className="pt-2 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-300 block">
              Active Machine Learning Models & Taxonomies
            </span>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" size="sm" className="font-mono text-slate-300">
                <Cpu className="w-3 h-3 mr-1 text-sky-400" aria-hidden="true" />
                Sentiment: {sentimentModelVersion}
              </Badge>
              <Badge variant="outline" size="sm" className="font-mono text-slate-300">
                <Layers className="w-3 h-3 mr-1 text-purple-400" aria-hidden="true" />
                ABSA: {taxonomyVersion}
              </Badge>
              <Badge variant="outline" size="sm" className="font-mono text-slate-300">
                <MessageSquareText className="w-3 h-3 mr-1 text-emerald-400" aria-hidden="true" />
                Topics: {topicModelVersion}
              </Badge>
            </div>
          </div>

          <div className="text-[11px] text-slate-500 max-w-sm">
            Temporal trends reflect ingestion timestamps of analyzed player reviews. Sentiment inference abstains when model confidence is below calibrated threshold.
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

