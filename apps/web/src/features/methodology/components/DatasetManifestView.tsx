import React from "react";
import { DatasetDocumentationItem } from "../types/methodology";
import { Card } from "../../../components/ui/Card";
import { Database } from "lucide-react";

export const DatasetManifestView: React.FC<{ datasets: DatasetDocumentationItem[] }> = ({
  datasets,
}) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Database className="w-5 h-5 text-sky-400" aria-hidden="true" />
        <h3 className="text-base font-bold text-white">Dataset Manifests & Provenance</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {datasets.map((ds) => (
          <Card key={ds.dataset_version} className="p-5 flex flex-col justify-between gap-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-white font-mono">{ds.dataset_version}</span>
                <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                  {ds.license}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{ds.description}</p>
              <div className="text-[11px] text-slate-400 pt-1 font-mono">
                Source: {ds.source} &bull; Window: {ds.collection_window.start} to{" "}
                {ds.collection_window.end}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1 text-xs">
              <span className="font-semibold text-slate-400 block">Dataset Splits:</span>
              <div className="flex items-center gap-4 text-slate-300 font-mono text-[11px]">
                <span>Train: {(ds.splits.train * 100).toFixed(0)}%</span>
                <span>Val: {(ds.splits.val * 100).toFixed(0)}%</span>
                <span>Test: {(ds.splits.test * 100).toFixed(0)}%</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

