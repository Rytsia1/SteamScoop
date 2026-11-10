import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  Database,
  DownloadCloud,
  Cpu,
  Sparkles,
  AlertOctagon,
  ScrollText,
  Lock,
} from "lucide-react";
import { useAuth } from "../features/auth/context/AuthContext";
import { adminClient } from "../features/admin/api/admin-client";
import {
  AdminAuditLog,
  AdminGame,
  AdminGameCreate,
  AdminIngestionJob,
  AdminIngestionJobCreate,
  AdminModel,
  AdminOperationalErrors,
  AdminPipelineRun,
} from "../types/admin";
import { CatalogManagementTab } from "../features/admin/components/CatalogManagementTab";
import { IngestionJobsTab } from "../features/admin/components/IngestionJobsTab";
import { PipelineRunsTab } from "../features/admin/components/PipelineRunsTab";
import { ModelRegistryTab } from "../features/admin/components/ModelRegistryTab";
import { OperationalErrorsTab } from "../features/admin/components/OperationalErrorsTab";
import { AuditLogsTab } from "../features/admin/components/AuditLogsTab";

type AdminTab =
  | "catalog"
  | "ingestion"
  | "pipelines"
  | "models"
  | "errors"
  | "audit";

export const AdminDashboardPage: React.FC = () => {
  const { user, isAuthenticated, openAuthModal } = useAuth();
  const [activeTab, setActiveTab] = useState<AdminTab>("catalog");

  // Domain states
  const [games, setGames] = useState<AdminGame[]>([]);
  const [ingestionJobs, setIngestionJobs] = useState<AdminIngestionJob[]>([]);
  const [pipelineRuns, setPipelineRuns] = useState<AdminPipelineRun[]>([]);
  const [models, setModels] = useState<AdminModel[]>([]);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLog[]>([]);
  const [operationalErrors, setOperationalErrors] =
    useState<AdminOperationalErrors | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const isAdmin = Boolean(
    isAuthenticated && user && user.roles && user.roles.includes("admin")
  );

  const loadData = async () => {
    if (!isAdmin) return;
    setIsLoading(true);
    try {
      const [
        fetchedGames,
        fetchedJobs,
        fetchedRuns,
        fetchedModels,
        fetchedLogs,
        fetchedErrors,
      ] = await Promise.all([
        adminClient.listGames({ limit: 100 }),
        adminClient.listIngestionJobs({ limit: 100 }),
        adminClient.listPipelineRuns({ limit: 100 }),
        adminClient.listModels(),
        adminClient.listAuditLogs({ limit: 100 }),
        adminClient.getOperationalErrors(50),
      ]);

      setGames(fetchedGames);
      setIngestionJobs(fetchedJobs);
      setPipelineRuns(fetchedRuns);
      setModels(fetchedModels);
      setAuditLogs(fetchedLogs);
      setOperationalErrors(fetchedErrors);
    } catch (err: unknown) {
      setNotification({
        type: "error",
        message:
          err instanceof Error
            ? err.message
            : "Failed to load administrative telemetry.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      loadData();
    }
  }, [isAdmin]);

  // Handler functions
  const handleRefreshMetadata = async (gameId: string) => {
    try {
      const res = await adminClient.refreshMetadata(gameId);
      setNotification({ type: "success", message: res.message });
      loadData();
    } catch (err: unknown) {
      setNotification({
        type: "error",
        message:
          err instanceof Error ? err.message : "Metadata refresh failed.",
      });
    }
  };

  const handleQueueIngestion = async (
    gameId: string,
    data: AdminIngestionJobCreate
  ) => {
    try {
      const job = await adminClient.queueIngestionJob(gameId, data);
      setNotification({
        type: "success",
        message: `Successfully queued ${job.job_type} collection job.`,
      });
      loadData();
    } catch (err: unknown) {
      setNotification({
        type: "error",
        message:
          err instanceof Error ? err.message : "Failed to queue ingestion job.",
      });
    }
  };

  const handleCreateGame = async (data: AdminGameCreate) => {
    try {
      const newGame = await adminClient.createGame(data);
      setNotification({
        type: "success",
        message: `Game '${newGame.name}' added to managed catalog.`,
      });
      loadData();
    } catch (err: unknown) {
      setNotification({
        type: "error",
        message:
          err instanceof Error ? err.message : "Failed to add game to catalog.",
      });
    }
  };

  const handleToggleActive = async (
    gameId: string,
    currentActive: boolean
  ) => {
    try {
      await adminClient.updateGame(gameId, { is_active: !currentActive });
      setNotification({
        type: "success",
        message: `Game catalog active status updated.`,
      });
      loadData();
    } catch (err: unknown) {
      setNotification({
        type: "error",
        message:
          err instanceof Error ? err.message : "Failed to update game status.",
      });
    }
  };

  const handleCancelJob = async (jobId: string) => {
    try {
      await adminClient.cancelIngestionJob(jobId);
      setNotification({
        type: "success",
        message: `Collection job cancelled successfully.`,
      });
      loadData();
    } catch (err: unknown) {
      setNotification({
        type: "error",
        message:
          err instanceof Error ? err.message : "Failed to cancel collection job.",
      });
    }
  };

  const handleRetryJob = async (jobId: string) => {
    try {
      await adminClient.retryIngestionJob(jobId);
      setNotification({
        type: "success",
        message: `Retry job enqueued successfully.`,
      });
      loadData();
    } catch (err: unknown) {
      setNotification({
        type: "error",
        message:
          err instanceof Error ? err.message : "Failed to enqueue job retry.",
      });
    }
  };

  const handleActivateModel = async (modelId: string) => {
    try {
      const res = await adminClient.activateModel(modelId);
      setNotification({ type: "success", message: res.message });
      loadData();
    } catch (err: unknown) {
      setNotification({
        type: "error",
        message:
          err instanceof Error ? err.message : "Model activation failed.",
      });
    }
  };

  // If user is not authorized as an admin
  if (!isAuthenticated || !isAdmin) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-8 sm:p-12 text-center space-y-6 shadow-2xl">
          <div className="w-16 h-16 rounded-2xl bg-rose-950/50 border border-rose-800/60 flex items-center justify-center mx-auto text-rose-400">
            <Lock className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h1 className="text-xl sm:text-2xl font-extrabold text-slate-100">
              Administrator Access Required
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto leading-relaxed">
              Administrative telemetry, catalog controls, and model activations
              are restricted to verified SteamScoop administrators.
            </p>
          </div>
          <div className="pt-2">
            {!isAuthenticated ? (
              <button
                type="button"
                onClick={openAuthModal}
                className="px-6 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs shadow-lg shadow-sky-600/20 transition-all"
              >
                Sign In as Administrator
              </button>
            ) : (
              <div className="p-3 rounded-lg bg-amber-950/40 border border-amber-800/50 text-amber-300 text-xs inline-block">
                Your current account ({user?.email}) is not provisioned with
                the <code className="font-mono font-bold">admin</code> role.
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  const tabs: {
    id: AdminTab;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: number;
  }[] = [
    { id: "catalog", label: "Game Catalog", icon: Database, badge: games.length },
    {
      id: "ingestion",
      label: "Ingestion Jobs",
      icon: DownloadCloud,
      badge: ingestionJobs.filter(
        (j) => j.status === "running" || j.status === "queued"
      ).length,
    },
    { id: "pipelines", label: "Pipeline Runs", icon: Cpu },
    {
      id: "models",
      label: "Model Registry",
      icon: Sparkles,
      badge: models.filter((m) => m.is_active).length,
    },
    {
      id: "errors",
      label: "Operational Errors",
      icon: AlertOctagon,
      badge: operationalErrors?.total_failures,
    },
    { id: "audit", label: "Audit Trail", icon: ScrollText },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-slate-100 tracking-tight">
              Administrative Command Center
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            System health, catalog curation, ingestion orchestration, and
            active model registry.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider bg-sky-950 text-sky-400 border border-sky-800">
            Admin: {user?.display_name || user?.email}
          </span>
        </div>
      </div>

      {/* Notification Toast */}
      {notification && (
        <div
          role="status"
          className={`p-3 rounded-xl border text-xs flex items-center justify-between animate-in fade-in ${
            notification.type === "success"
              ? "bg-emerald-950/70 border-emerald-800 text-emerald-300"
              : "bg-rose-950/70 border-rose-800 text-rose-300"
          }`}
        >
          <span>{notification.message}</span>
          <button
            type="button"
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-white ml-4 font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-slate-800">
        {tabs.map(({ id, label, icon: Icon, badge }) => {
          const isActive = activeTab === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
                isActive
                  ? "bg-sky-600 text-white shadow-sm shadow-sky-900/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-850"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
              {badge !== undefined && badge > 0 && (
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                    isActive
                      ? "bg-sky-900/80 text-sky-200"
                      : "bg-slate-800 text-slate-300"
                  }`}
                >
                  {badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === "catalog" && (
          <CatalogManagementTab
            games={games}
            isLoading={isLoading}
            onRefreshMetadata={handleRefreshMetadata}
            onQueueIngestion={handleQueueIngestion}
            onCreateGame={handleCreateGame}
            onToggleActive={handleToggleActive}
            onReload={loadData}
          />
        )}

        {activeTab === "ingestion" && (
          <IngestionJobsTab
            jobs={ingestionJobs}
            isLoading={isLoading}
            onCancelJob={handleCancelJob}
            onRetryJob={handleRetryJob}
            onReload={loadData}
          />
        )}

        {activeTab === "pipelines" && (
          <PipelineRunsTab
            runs={pipelineRuns}
            isLoading={isLoading}
            onReload={loadData}
          />
        )}

        {activeTab === "models" && (
          <ModelRegistryTab
            models={models}
            isLoading={isLoading}
            onActivateModel={handleActivateModel}
            onReload={loadData}
          />
        )}

        {activeTab === "errors" && (
          <OperationalErrorsTab
            errors={operationalErrors}
            isLoading={isLoading}
            onRetryJob={handleRetryJob}
            onReload={loadData}
          />
        )}

        {activeTab === "audit" && (
          <AuditLogsTab
            logs={auditLogs}
            isLoading={isLoading}
            onReload={loadData}
          />
        )}
      </div>
    </div>
  );
};

