import React, { useState } from "react";
import {
  useDatasets,
  useMethodology,
  useModelCards,
} from "../features/methodology/api/methodologyApi";
import { ModelCardItemView } from "../features/methodology/components/ModelCardItemView";
import { DatasetManifestView } from "../features/methodology/components/DatasetManifestView";
import { MetricDefinitionsView } from "../features/methodology/components/MetricDefinitionsView";
import { Tabs } from "../components/ui/Tabs";
import { CardSkeleton } from "../components/feedback/LoadingSkeleton";
import { ErrorAlert } from "../components/feedback/ErrorAlert";
import { BookOpen, Cpu, Database, ShieldCheck } from "lucide-react";

export const MethodologyPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("methodology");

  const {
    data: methodology,
    isLoading: isLoadingMethodology,
    error: methodologyError,
    refetch: refetchMethodology,
  } = useMethodology();

  const {
    data: modelCards,
    isLoading: isLoadingModels,
    error: modelsError,
    refetch: refetchModels,
  } = useModelCards();

  const {
    data: datasets,
    isLoading: isLoadingDatasets,
    error: datasetsError,
    refetch: refetchDatasets,
  } = useDatasets();

  const tabs = [
    {
      id: "methodology",
      label: "Scientific Methodology & Sampling",
      icon: <BookOpen className="w-4 h-4 text-sky-400" aria-hidden="true" />,
    },
    {
      id: "models",
      label: "Model Cards Registry",
      icon: <Cpu className="w-4 h-4 text-emerald-400" aria-hidden="true" />,
      count: modelCards?.length,
    },
    {
      id: "datasets",
      label: "Dataset Provenance Manifests",
      icon: <Database className="w-4 h-4 text-purple-400" aria-hidden="true" />,
      count: datasets?.length,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-950/70 border border-sky-800/60 text-xs font-medium text-sky-300">
          <ShieldCheck className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Research Validity & Reproducibility</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Scientific Methodology & Model Registry
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
          Open documentation of Steam review sampling policies, evaluation benchmarks, dataset
          provenance manifests, and model cards.
        </p>
      </div>

      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onChange={setActiveTab}
        ariaLabel="Methodology sections"
      />

      {/* Tab 1: Methodology */}
      {activeTab === "methodology" && (
        <div className="space-y-6">
          {isLoadingMethodology ? (
            <CardSkeleton count={2} />
          ) : methodologyError ? (
            <ErrorAlert
              title="Failed to load methodology"
              message={methodologyError.message}
              onRetry={() => refetchMethodology()}
            />
          ) : methodology ? (
            <>
              {/* Metric Definitions */}
              <MetricDefinitionsView definitions={methodology.definitions} />

              {/* Collection Policy Card */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
                <h3 className="text-base font-bold text-white">Ingestion & Sampling Policy</h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {methodology.collection_policy.method}
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs pt-2">
                  <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800">
                    <span className="font-semibold text-slate-400 block">
                      Target Historical Sample
                    </span>
                    <span className="text-sm font-bold text-sky-400">
                      {methodology.collection_policy.historical_sample_target.toLocaleString()}{" "}
                      reviews
                    </span>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800">
                    <span className="font-semibold text-slate-400 block">
                      Incremental Refresh Cadence
                    </span>
                    <span className="text-slate-300">
                      {methodology.collection_policy.weekly_refresh_policy}
                    </span>
                  </div>
                </div>

                <div className="pt-2">
                  <span className="text-xs font-semibold text-slate-400 block mb-1.5">
                    Known Limitations & Boundaries:
                  </span>
                  <ul className="list-disc list-inside text-xs text-slate-400 space-y-1">
                    {methodology.collection_policy.known_limitations.map((lim, i) => (
                      <li key={i}>{lim}</li>
                    ))}
                  </ul>
                </div>

                <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-500 font-mono">
                  Methodology Version: {methodology.version} &bull; Updated:{" "}
                  {new Date(methodology.updated_at).toLocaleDateString()}
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* Tab 2: Model Cards */}
      {activeTab === "models" && (
        <div className="space-y-6">
          {isLoadingModels ? (
            <CardSkeleton count={3} />
          ) : modelsError ? (
            <ErrorAlert
              title="Failed to load model registry"
              message={modelsError.message}
              onRetry={() => refetchModels()}
            />
          ) : modelCards ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {modelCards.map((model) => (
                <ModelCardItemView key={model.model_id} model={model} />
              ))}
            </div>
          ) : null}
        </div>
      )}

      {/* Tab 3: Datasets */}
      {activeTab === "datasets" && (
        <div className="space-y-6">
          {isLoadingDatasets ? (
            <CardSkeleton count={2} />
          ) : datasetsError ? (
            <ErrorAlert
              title="Failed to load dataset manifests"
              message={datasetsError.message}
              onRetry={() => refetchDatasets()}
            />
          ) : datasets ? (
            <DatasetManifestView datasets={datasets} />
          ) : null}
        </div>
      )}
    </div>
  );
};
