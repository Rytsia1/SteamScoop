import React from "react";
import { ModelCardItem } from "../types/methodology";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { AlertTriangle } from "lucide-react";

export interface ModelCardItemViewProps {
  model: ModelCardItem;
}

export const ModelCardItemView: React.FC<ModelCardItemViewProps> = ({ model }) => {
  return (
    <Card className="h-full flex flex-col justify-between">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <Badge variant={model.is_active ? "positive" : "outline"} size="sm">
            {model.is_active ? "ACTIVE PRODUCTION" : "CANDIDATE"}
          </Badge>
          <span className="text-[11px] font-mono text-slate-500 uppercase">{model.task}</span>
        </div>
        <CardTitle className="text-base font-bold text-white mt-1">{model.model_key}</CardTitle>
        <p className="text-xs text-slate-400 font-mono">
          Version: {model.version} &bull; Framework: {model.framework}
        </p>
      </CardHeader>

      <CardContent className="space-y-4 pt-0">
        {/* Evaluation Metrics Grid */}
        <div className="space-y-1.5">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
            Evaluation Benchmarks
          </span>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(model.evaluation_metrics).map(([metric, val]) => (
              <div
                key={metric}
                className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800 flex flex-col"
              >
                <span className="text-[10px] text-slate-400 uppercase font-mono">{metric}</span>
                <span className="text-sm font-bold text-sky-400">
                  {typeof val === "number" ? val.toFixed(3) : val}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Supported Languages */}
        <div className="space-y-1.5">
          <span className="text-xs font-semibold text-slate-400 block">Supported Languages:</span>
          <div className="flex flex-wrap gap-1">
            {model.supported_languages.map((lang) => (
              <span
                key={lang}
                className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700/50"
              >
                {lang}
              </span>
            ))}
          </div>
        </div>

        {/* Limitations */}
        {model.limitations.length > 0 && (
          <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-900/40 space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-amber-300 font-medium">
              <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Documented Limitations</span>
            </div>
            <ul className="list-disc list-inside text-[11px] text-amber-200/80 space-y-0.5 pl-1">
              {model.limitations.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
