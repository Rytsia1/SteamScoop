import React from "react";
import { HealthStatus } from "../components/HealthStatus";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Activity, Server, Database, Layers } from "lucide-react";

export const SystemStatusPage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Title */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-950/70 border border-sky-800/60 text-xs font-medium text-sky-300">
          <Activity className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Infrastructure Telemetry</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          System Health & Services Status
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
          Real-time health status of SteamScoop backend services, PostgreSQL database, and Redis cache.
        </p>
      </div>

      {/* Live Health Status Card */}
      <div className="max-w-2xl">
        <HealthStatus />
      </div>

      {/* Architectural Services Stack */}
      <section className="space-y-4 pt-4 border-t border-slate-800">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
          Active Services Topology
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="p-5">
            <CardHeader className="p-0 pb-3 flex flex-row items-center gap-3">
              <div className="p-2 rounded-lg bg-sky-950 text-sky-400">
                <Server className="w-5 h-5" aria-hidden="true" />
              </div>
              <div>
                <CardTitle className="text-sm">Public API Cluster</CardTitle>
                <span className="text-[11px] text-slate-400">FastAPI 0.110+</span>
              </div>
            </CardHeader>
            <CardContent className="p-0 text-xs text-slate-300 leading-relaxed">
              Provides standardized JSON envelopes, rate limiting, and cached analytics.
            </CardContent>
          </Card>

          <Card className="p-5">
            <CardHeader className="p-0 pb-3 flex flex-row items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-950 text-emerald-400">
                <Database className="w-5 h-5" aria-hidden="true" />
              </div>
              <div>
                <CardTitle className="text-sm">Analytical Datastore</CardTitle>
                <span className="text-[11px] text-slate-400">PostgreSQL 15+</span>
              </div>
            </CardHeader>
            <CardContent className="p-0 text-xs text-slate-300 leading-relaxed">
              Stores normalized reviews, sentiment predictions, ABSA categories, and topics.
            </CardContent>
          </Card>

          <Card className="p-5">
            <CardHeader className="p-0 pb-3 flex flex-row items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-950 text-purple-400">
                <Layers className="w-5 h-5" aria-hidden="true" />
              </div>
              <div>
                <CardTitle className="text-sm">Cache & Queues</CardTitle>
                <span className="text-[11px] text-slate-400">Redis 7+ / Celery</span>
              </div>
            </CardHeader>
            <CardContent className="p-0 text-xs text-slate-300 leading-relaxed">
              Handles background review ingestion, NLP batch inference, and rate quotas.
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
};

