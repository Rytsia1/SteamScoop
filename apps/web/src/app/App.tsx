import React from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "../lib/query-client";
import { HealthStatus } from "../components/HealthStatus";

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
        {/* Navigation bar */}
        <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center font-bold text-white shadow-lg shadow-sky-500/20">
                S
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight text-white">SteamScoop</span>
                <span className="hidden sm:inline-block ml-2 text-xs text-slate-400 font-medium">
                  | Game Intelligence & Research
                </span>
              </div>
            </div>
            <div className="text-xs font-mono text-slate-400">
              v0.1.0-alpha
            </div>
          </div>
        </header>

        {/* Hero & System Info */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col gap-8">
          <section className="space-y-3">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              Understand Games Through Data.
            </h1>
            <p className="text-base sm:text-lg text-slate-400 max-w-2xl">
              Public Game Intelligence and Academic Research Platform analyzing player feedback
              through Natural Language Processing, Sentiment Analysis, and Aspect Modeling.
            </p>
          </section>

          {/* Real-time Health Check Card */}
          <section className="max-w-xl">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3">
              Core Backend Connection
            </h2>
            <HealthStatus />
          </section>

          {/* Architectural Stack Matrix */}
          <section className="border border-slate-800 rounded-xl p-6 bg-slate-900/40">
            <h3 className="text-base font-semibold text-white mb-4">
              Baseline Monorepo Architecture
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/50">
                <span className="font-semibold text-sky-400 block mb-1">Frontend Layer</span>
                <span className="text-slate-300 text-xs">React 18 + TypeScript + Vite + Tailwind CSS + ECharts</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/50">
                <span className="font-semibold text-emerald-400 block mb-1">Backend Core</span>
                <span className="text-slate-300 text-xs">FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/50">
                <span className="font-semibold text-amber-400 block mb-1">Data & Async</span>
                <span className="text-slate-300 text-xs">PostgreSQL 15+ & Redis 7+ via Celery Background Workers</span>
              </div>
            </div>
          </section>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
          SteamScoop &copy; 2026. Data sourced from Steam Public Reviews API. Not affiliated with Valve Corporation.
        </footer>
      </div>
    </QueryClientProvider>
  );
};

