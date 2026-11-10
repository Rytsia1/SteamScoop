import React, { useState } from "react";
import { Link } from "../app/router/Router";
import { useParams, useRouter } from "../app/router/RouterContext";
import { useAuth } from "../features/auth/context/AuthContext";
import { useGames } from "../features/games/api/gamesApi";
import {
  useAddGameToProject,
  useAddProjectMember,
  useCreateSavedAnalysis,
  useCreateSnapshot,
  useDeleteProject,
  useDeleteSavedAnalysis,
  useProject,
  useProjectGames,
  useProjectMembers,
  useRemoveGameFromProject,
  useRemoveProjectMember,
  useSavedAnalyses,
  useSnapshots,
  useUpdateProject,
} from "../features/workspace/api/workspaceApi";
import { SavedAnalysis } from "../features/workspace/types/workspace";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { Modal } from "../components/ui/Modal";
import { Tabs } from "../components/ui/Tabs";
import { ErrorAlert } from "../components/feedback/ErrorAlert";
import { CardSkeleton } from "../components/feedback/LoadingSkeleton";
import {
  ArrowLeft,
  Lock,
  Globe,
  Settings,
  Trash2,
  Gamepad2,
  Plus,
  X,
  Camera,
  Users,
  Shield,
  AlertTriangle,
  UserPlus,
  Sliders,
} from "lucide-react";

export const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { user } = useAuth();
  const { navigate } = useRouter();

  const [activeTab, setActiveTab] = useState<string>("analyses");

  // Edit Project Modal State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editVisibility, setEditVisibility] = useState<"private" | "shared">("private");

  // Add Game Modal State
  const [isAddGameModalOpen, setIsAddGameModalOpen] = useState(false);
  const [selectedGameCatalogId, setSelectedGameCatalogId] = useState("");

  // Create Analysis Modal State
  const [isCreateAnalysisModalOpen, setIsCreateAnalysisModalOpen] = useState(false);
  const [analysisName, setAnalysisName] = useState("");
  const [analysisDesc, setAnalysisDesc] = useState("");
  const [analysisType, setAnalysisType] = useState<string>("review_explorer");
  const [analysisAspect, setAnalysisAspect] = useState<string>("gameplay");
  const [analysisSentiment, setAnalysisSentiment] = useState<string>("all");

  // Create Snapshot Modal State
  const [isCreateSnapshotModalOpen, setIsCreateSnapshotModalOpen] = useState(false);
  const [activeAnalysisForSnapshot, setActiveAnalysisForSnapshot] = useState<SavedAnalysis | null>(null);
  const [snapshotName, setSnapshotName] = useState("");
  const [snapshotDesc, setSnapshotDesc] = useState("");

  // Add Member Modal State
  const [isAddMemberModalOpen, setIsAddMemberModalOpen] = useState(false);
  const [memberEmail, setMemberEmail] = useState("");
  const [memberRole, setMemberRole] = useState<"editor" | "viewer">("viewer");

  // API Queries & Mutations
  const {
    data: project,
    isLoading: isLoadingProject,
    error: projectError,
  } = useProject(projectId);

  const { data: projectGames = [], isLoading: isLoadingGames } = useProjectGames(projectId);
  const { data: savedAnalyses = [], isLoading: isLoadingAnalyses } = useSavedAnalyses(projectId);
  const { data: projectMembers = [] } = useProjectMembers(projectId);
  const { data: catalogData } = useGames({ limit: 50 });

  // Currently inspected analysis snapshots
  const [inspectedAnalysisId, setInspectedAnalysisId] = useState<string | null>(null);
  const { data: snapshots = [] } = useSnapshots(
    projectId,
    inspectedAnalysisId || (savedAnalyses[0]?.id ?? undefined)
  );

  const updateProjectMutation = useUpdateProject(projectId || "");
  const deleteProjectMutation = useDeleteProject();
  const addGameMutation = useAddGameToProject(projectId || "");
  const removeGameMutation = useRemoveGameFromProject(projectId || "");
  const createAnalysisMutation = useCreateSavedAnalysis(projectId || "");
  const deleteAnalysisMutation = useDeleteSavedAnalysis(projectId || "");
  const createSnapshotMutation = useCreateSnapshot(
    projectId || "",
    activeAnalysisForSnapshot?.id || ""
  );
  const addMemberMutation = useAddProjectMember(projectId || "");
  const removeMemberMutation = useRemoveProjectMember(projectId || "");

  // Permissions resolution
  const userRole = project?.current_user_role || (project?.owner_user_id === user?.id ? "owner" : "viewer");
  const isOwner = userRole === "owner";
  const canEdit = isOwner || userRole === "editor";

  // Handlers
  const handleOpenEdit = () => {
    if (!project) return;
    setEditName(project.name);
    setEditDesc(project.description || "");
    setEditVisibility(project.visibility);
    setIsEditModalOpen(true);
  };

  const handleUpdateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editName.trim()) return;

    await updateProjectMutation.mutateAsync({
      name: editName.trim(),
      description: editDesc.trim() || undefined,
      visibility: editVisibility,
    });
    setIsEditModalOpen(false);
  };

  const handleDeleteProject = async () => {
    if (!project || !isOwner) return;
    const confirmed = window.confirm(
      `Are you sure you want to permanently delete project "${project.name}"? This action cannot be undone.`
    );
    if (!confirmed) return;

    await deleteProjectMutation.mutateAsync(project.id);
    navigate("/workspace");
  };

  const handleAddGame = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGameCatalogId) return;

    await addGameMutation.mutateAsync(selectedGameCatalogId);
    setSelectedGameCatalogId("");
    setIsAddGameModalOpen(false);
  };

  const handleCreateAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!analysisName.trim()) return;

    await createAnalysisMutation.mutateAsync({
      name: analysisName.trim(),
      description: analysisDesc.trim() || undefined,
      analysis_type: analysisType,
      query_config: {
        game_ids: projectGames.map((g) => g.game_id),
        aspect: analysisAspect !== "all" ? analysisAspect : undefined,
        sentiment: analysisSentiment !== "all" ? analysisSentiment : undefined,
        model_version: "baseline",
      },
    });

    setAnalysisName("");
    setAnalysisDesc("");
    setIsCreateAnalysisModalOpen(false);
  };

  const handleOpenSnapshotModal = (analysis: SavedAnalysis) => {
    setActiveAnalysisForSnapshot(analysis);
    setSnapshotName(`Snapshot - ${new Date().toLocaleDateString()}`);
    setSnapshotDesc("");
    setIsCreateSnapshotModalOpen(true);
  };

  const handleCreateSnapshot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!snapshotName.trim() || !activeAnalysisForSnapshot) return;

    await createSnapshotMutation.mutateAsync({
      name: snapshotName.trim(),
      description: snapshotDesc.trim() || undefined,
    });

    setIsCreateSnapshotModalOpen(false);
    setActiveAnalysisForSnapshot(null);
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!memberEmail.trim()) return;

    await addMemberMutation.mutateAsync({
      email: memberEmail.trim(),
      project_role: memberRole,
    });

    setMemberEmail("");
    setMemberRole("viewer");
    setIsAddMemberModalOpen(false);
  };

  if (isLoadingProject) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="h-6 w-32 bg-slate-800 rounded animate-pulse" />
        <CardSkeleton count={2} />
      </div>
    );
  }

  if (projectError || !project) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <Link
          to="/workspace"
          className="inline-flex items-center gap-1.5 text-xs text-sky-400 hover:text-sky-300 font-medium"
        >
          <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Back to Research Workspaces</span>
        </Link>
        <ErrorAlert
          title="Project Not Accessible"
          message={
            projectError?.message ||
            "The requested project was not found or you lack permission to view this private workspace."
          }
        />
      </div>
    );
  }

  const tabItems = [
    {
      id: "analyses",
      label: `Saved Analyses (${savedAnalyses.length})`,
      icon: <Sliders className="w-4 h-4" aria-hidden="true" />,
    },
    {
      id: "games",
      label: `Project Games (${projectGames.length})`,
      icon: <Gamepad2 className="w-4 h-4" aria-hidden="true" />,
    },
    {
      id: "snapshots",
      label: "Reproducibility Snapshots",
      icon: <Camera className="w-4 h-4" aria-hidden="true" />,
    },
    {
      id: "collaborators",
      label: `Collaborators (${projectMembers.length})`,
      icon: <Users className="w-4 h-4" aria-hidden="true" />,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Breadcrumb Navigation */}
      <Link
        to="/workspace"
        className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-sky-400 font-medium transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
        <span>Back to Research Workspaces</span>
      </Link>

      {/* Project Header Banner */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge
                variant={project.visibility === "private" ? "outline" : "info"}
                size="sm"
                className="text-[10px] uppercase font-mono"
              >
                {project.visibility === "private" ? (
                  <>
                    <Lock className="w-2.5 h-2.5 mr-1 text-slate-400" aria-hidden="true" />
                    Private
                  </>
                ) : (
                  <>
                    <Globe className="w-2.5 h-2.5 mr-1 text-sky-400" aria-hidden="true" />
                    Shared
                  </>
                )}
              </Badge>

              <Badge
                variant={isOwner ? "positive" : userRole === "editor" ? "info" : "outline"}
                size="sm"
                className="font-mono text-[10px] capitalize"
              >
                Your Role: {userRole}
              </Badge>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {project.name}
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 max-w-3xl leading-relaxed">
              {project.description || "No project description provided."}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 shrink-0">
            {canEdit && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleOpenEdit}
                leftIcon={<Settings className="w-3.5 h-3.5" aria-hidden="true" />}
              >
                Settings
              </Button>
            )}

            {isOwner && (
              <Button
                variant="danger"
                size="sm"
                onClick={handleDeleteProject}
                isLoading={deleteProjectMutation.isPending}
                leftIcon={<Trash2 className="w-3.5 h-3.5" aria-hidden="true" />}
              >
                Delete
              </Button>
            )}
          </div>
        </div>

        <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span className="font-mono text-[11px] text-slate-500">
            Project ID: <b className="text-slate-300">{project.id}</b>
          </span>
          <span className="font-mono text-[11px] text-slate-500">
            Last modified: {new Date(project.updated_at).toLocaleString()}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <Tabs tabs={tabItems} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: Saved Analyses */}
      {activeTab === "analyses" && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                Saved Analytical Query Configurations
              </h3>
              <p className="text-xs text-slate-400">
                Reusable research query configurations, sentiment filters, and evaluation criteria.
              </p>
            </div>

            {canEdit && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsCreateAnalysisModalOpen(true)}
                leftIcon={<Plus className="w-3.5 h-3.5" aria-hidden="true" />}
              >
                New Analysis
              </Button>
            )}
          </div>

          {isLoadingAnalyses && <CardSkeleton count={2} />}

          {!isLoadingAnalyses && savedAnalyses.length === 0 && (
            <div className="p-8 rounded-xl border border-slate-800 bg-slate-900/40 text-center space-y-2">
              <Sliders className="w-8 h-8 text-slate-500 mx-auto" aria-hidden="true" />
              <h4 className="text-sm font-semibold text-white">No Saved Analyses Yet</h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Save customized Review Explorer or Game Comparison configurations to quickly re-evaluate
                or freeze into reproducibility snapshots.
              </p>
              {canEdit && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsCreateAnalysisModalOpen(true)}
                  leftIcon={<Plus className="w-3 h-3" aria-hidden="true" />}
                >
                  Save First Analysis
                </Button>
              )}
            </div>
          )}

          {!isLoadingAnalyses && savedAnalyses.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {savedAnalyses.map((ana) => (
                <Card key={ana.id} className="bg-slate-900/60 flex flex-col justify-between">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between gap-2">
                      <Badge variant="outline" size="sm" className="font-mono text-[10px] uppercase">
                        {ana.analysis_type}
                      </Badge>
                      <span className="text-[10px] font-mono text-slate-500">
                        {new Date(ana.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                    <CardTitle className="text-base mt-1 line-clamp-1">{ana.name}</CardTitle>
                  </CardHeader>

                  <CardContent className="space-y-4 pt-0">
                    <p className="text-xs text-slate-400 line-clamp-2 min-h-8">
                      {ana.description || "No notes provided for this analysis configuration."}
                    </p>

                    {/* Query Config Badges */}
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1 text-xs">
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Aspect Focus:</span>
                        <b className="text-slate-200 capitalize">
                          {String(ana.query_config?.aspect || "All Aspects")}
                        </b>
                      </div>
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Sentiment Polarity:</span>
                        <b className="text-slate-200 capitalize">
                          {String(ana.query_config?.sentiment || "All Sentiments")}
                        </b>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                      {canEdit && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleOpenSnapshotModal(ana)}
                          leftIcon={<Camera className="w-3 h-3 text-sky-400" aria-hidden="true" />}
                          className="text-xs py-1"
                        >
                          Freeze Snapshot
                        </Button>
                      )}

                      {canEdit && (
                        <button
                          type="button"
                          onClick={() => deleteAnalysisMutation.mutate(ana.id)}
                          className="text-slate-500 hover:text-rose-400 text-xs flex items-center gap-1 transition-colors"
                          aria-label={`Delete ${ana.name}`}
                        >
                          <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                          <span>Delete</span>
                        </button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Tab 2: Project Games */}
      {activeTab === "games" && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                Project Game Selection
              </h3>
              <p className="text-xs text-slate-400">
                Titles included in this research study cohort for multi-game benchmarks and cross-game NLP analysis.
              </p>
            </div>

            {canEdit && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsAddGameModalOpen(true)}
                leftIcon={<Plus className="w-3.5 h-3.5" aria-hidden="true" />}
              >
                Add Game to Project
              </Button>
            )}
          </div>

          {isLoadingGames && <CardSkeleton count={2} />}

          {!isLoadingGames && projectGames.length === 0 && (
            <div className="p-8 rounded-xl border border-slate-800 bg-slate-900/40 text-center space-y-2">
              <Gamepad2 className="w-8 h-8 text-slate-500 mx-auto" aria-hidden="true" />
              <h4 className="text-sm font-semibold text-white">No Games Added Yet</h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Associate games from SteamScoop's indexed catalog with this workspace to scope analyses.
              </p>
              {canEdit && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsAddGameModalOpen(true)}
                  leftIcon={<Plus className="w-3 h-3" aria-hidden="true" />}
                >
                  Select Games
                </Button>
              )}
            </div>
          )}

          {!isLoadingGames && projectGames.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {projectGames.map((pg) => {
                const catalogMatch = catalogData?.items?.find((g) => g.id === pg.game_id);
                const title =
                  pg.title ||
                  catalogMatch?.title ||
                  catalogMatch?.name ||
                  `Game ${pg.game_id.slice(0, 8)}`;

                return (
                  <Card key={pg.game_id} className="bg-slate-900/60">
                    <CardHeader className="pb-2">
                      <span className="text-[10px] font-mono text-slate-500">
                        Added: {new Date(pg.added_at).toLocaleDateString()}
                      </span>
                      <CardTitle className="text-sm line-clamp-1">{title}</CardTitle>
                    </CardHeader>

                    <CardContent className="pt-2 flex items-center justify-between border-t border-slate-800/80">
                      <Link
                        to={`/games/${pg.game_id}`}
                        className="text-xs text-sky-400 hover:text-sky-300 font-semibold"
                      >
                        View Intelligence &rarr;
                      </Link>

                      {canEdit && (
                        <button
                          type="button"
                          onClick={() => removeGameMutation.mutate(pg.game_id)}
                          className="text-slate-500 hover:text-rose-400 text-xs flex items-center gap-1 transition-colors"
                          aria-label={`Remove ${title} from project`}
                        >
                          <X className="w-3.5 h-3.5" aria-hidden="true" />
                          <span>Remove</span>
                        </button>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </section>
      )}

      {/* Tab 3: Reproducibility Snapshots */}
      {activeTab === "snapshots" && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                Reproducibility Snapshots & Audit History
              </h3>
              <p className="text-xs text-slate-400">
                Immutable records capturing exact model versions, review cutoff timestamps, and query configurations.
              </p>
            </div>
          </div>

          {savedAnalyses.length > 0 && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              <span className="text-xs text-slate-400 shrink-0">Analysis:</span>
              {savedAnalyses.map((ana) => {
                const isSelected =
                  (inspectedAnalysisId || savedAnalyses[0].id) === ana.id;
                return (
                  <button
                    key={ana.id}
                    type="button"
                    onClick={() => setInspectedAnalysisId(ana.id)}
                    className={`px-2.5 py-1 text-xs rounded-lg transition-colors shrink-0 ${
                      isSelected
                        ? "bg-sky-500/20 text-sky-300 border border-sky-500/40 font-semibold"
                        : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                    }`}
                  >
                    {ana.name}
                  </button>
                );
              })}
            </div>
          )}

          {snapshots.length === 0 ? (
            <div className="p-8 rounded-xl border border-slate-800 bg-slate-900/40 text-center space-y-2">
              <Camera className="w-8 h-8 text-slate-500 mx-auto" aria-hidden="true" />
              <h4 className="text-sm font-semibold text-white">No Snapshots Captured</h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Freeze an analysis configuration to preserve an immutable result audit for scientific reporting.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {snapshots.map((snap) => (
                <div
                  key={snap.id}
                  className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Camera className="w-4 h-4 text-sky-400 shrink-0" aria-hidden="true" />
                      <span className="text-sm font-bold text-white">{snap.name}</span>
                      <Badge variant="outline" size="sm" className="font-mono text-[10px]">
                        Immutable
                      </Badge>
                    </div>
                    <span className="text-[11px] text-slate-500 font-mono">
                      Captured: {new Date(snap.created_at).toLocaleString()}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 text-xs text-slate-300 pt-1">
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                      <span className="text-slate-400 block text-[11px]">Data Cutoff Watermark:</span>
                      <b className="font-mono text-emerald-300 text-[11px]">
                        {new Date(snap.data_cutoff_at).toLocaleString()}
                      </b>
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                      <span className="text-slate-400 block text-[11px]">Snapshot ID:</span>
                      <b className="font-mono text-slate-300 text-[11px]">{snap.id}</b>
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                      <span className="text-slate-400 block text-[11px]">Parent Analysis:</span>
                      <b className="font-mono text-sky-300 text-[11px]">{snap.saved_analysis_id}</b>
                    </div>
                  </div>

                  {/* Filter Snapshot JSON Preview */}
                  <div className="space-y-1">
                    <span className="text-[11px] font-semibold text-slate-400">
                      Frozen Query Parameters:
                    </span>
                    <pre className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto">
                      {JSON.stringify(snap.configuration_snapshot, null, 2)}
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Tab 4: Collaborators & Permissions */}
      {activeTab === "collaborators" && (
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                Project Collaborators & Role Permissions
              </h3>
              <p className="text-xs text-slate-400">
                Manage team access, granular ownership, editor modifications, and viewer access.
              </p>
            </div>

            {isOwner && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsAddMemberModalOpen(true)}
                leftIcon={<UserPlus className="w-3.5 h-3.5" aria-hidden="true" />}
              >
                Add Collaborator
              </Button>
            )}
          </div>

          {/* Members Table */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                  <th scope="col" className="py-2.5 px-4 font-semibold">User</th>
                  <th scope="col" className="py-2.5 px-4 font-semibold">Email</th>
                  <th scope="col" className="py-2.5 px-4 font-semibold">Role</th>
                  <th scope="col" className="py-2.5 px-4 font-semibold">Joined</th>
                  {isOwner && <th scope="col" className="py-2.5 px-4 font-semibold text-right">Action</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {projectMembers.map((m) => {
                  const isThisOwner = m.project_role === "owner";
                  return (
                    <tr key={m.user_id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 font-medium text-white">
                        {m.display_name || "Researcher"}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-slate-400">
                        {m.email || m.user_id}
                      </td>
                      <td className="py-2.5 px-4">
                        <Badge
                          variant={isThisOwner ? "positive" : m.project_role === "editor" ? "info" : "outline"}
                          size="sm"
                          className="font-mono text-[10px] capitalize"
                        >
                          {m.project_role}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-4 text-slate-400">
                        {new Date(m.joined_at).toLocaleDateString()}
                      </td>
                      {isOwner && (
                        <td className="py-2.5 px-4 text-right">
                          {!isThisOwner && (
                            <button
                              type="button"
                              onClick={() => removeMemberMutation.mutate(m.user_id)}
                              className="text-slate-500 hover:text-rose-400 font-semibold text-xs transition-colors"
                            >
                              Remove
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Authorization Matrix Explanation */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-white">
              <Shield className="w-4 h-4 text-sky-400" aria-hidden="true" />
              <span>Workspace Authorization Contract</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1">
                <span className="font-semibold text-emerald-400 block">Owner</span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Full management authority: add/remove collaborators, delete project, configure analyses, and freeze snapshots.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1">
                <span className="font-semibold text-sky-400 block">Editor</span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Permitted to modify game cohorts, create/edit saved analyses, and generate reproducibility snapshots.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1">
                <span className="font-semibold text-slate-300 block">Viewer</span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Read-only access to shared project analyses and immutable snapshots. Cannot modify project content.
                </p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Edit Project Settings Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Project Settings"
        description="Modify project details and visibility."
        maxWidth="md"
      >
        <form onSubmit={handleUpdateProject} className="space-y-4">
          <Input
            label="Project Name"
            type="text"
            required
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
          />

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-300">Description</label>
            <textarea
              className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-white placeholder-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 min-h-20"
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-300">Visibility</label>
            <Select
              options={[
                { value: "private", label: "Private (Owner & Invited Members Only)" },
                { value: "shared", label: "Shared (All Platform Members Can View)" },
              ]}
              value={editVisibility}
              onChange={(e) => setEditVisibility(e.target.value as "private" | "shared")}
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={updateProjectMutation.isPending}>
              Save Settings
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Game to Project Modal */}
      <Modal
        isOpen={isAddGameModalOpen}
        onClose={() => setIsAddGameModalOpen(false)}
        title="Add Game to Project"
        description="Select an indexed title from the catalog to associate with this workspace."
        maxWidth="md"
      >
        <form onSubmit={handleAddGame} className="space-y-4">
          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-300">Select Game</label>
            <Select
              options={[
                { value: "", label: "Choose an indexed game..." },
                ...(catalogData?.items || []).map((g) => ({
                  value: g.id,
                  label: `${g.title} (${g.review_count?.toLocaleString() || 0} reviews)`,
                })),
              ]}
              value={selectedGameCatalogId}
              onChange={(e) => setSelectedGameCatalogId(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsAddGameModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={!selectedGameCatalogId}
              isLoading={addGameMutation.isPending}
            >
              Add to Cohort
            </Button>
          </div>
        </form>
      </Modal>

      {/* Create Saved Analysis Modal */}
      <Modal
        isOpen={isCreateAnalysisModalOpen}
        onClose={() => setIsCreateAnalysisModalOpen(false)}
        title="Save Analytical Query Configuration"
        description="Define search filters and analysis parameters to preserve in this workspace."
        maxWidth="md"
      >
        <form onSubmit={handleCreateAnalysis} className="space-y-4">
          <Input
            label="Analysis Name"
            type="text"
            required
            placeholder="e.g. Negative Controls Feedback"
            value={analysisName}
            onChange={(e) => setAnalysisName(e.target.value)}
          />

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-300">Description</label>
            <textarea
              className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-white placeholder-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 min-h-16"
              placeholder="Hypothesis or analytical purpose..."
              value={analysisDesc}
              onChange={(e) => setAnalysisDesc(e.target.value)}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-300">Analysis Type</label>
            <Select
              options={[
                { value: "review_explorer", label: "Review Explorer Query" },
                { value: "aspect_explorer", label: "Aspect Sentiment Deep Dive" },
                { value: "cohort_comparison", label: "Cohort Comparison Study" },
              ]}
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="block text-xs font-medium text-slate-300">Aspect Filter</label>
              <Select
                options={[
                  { value: "all", label: "All Aspects" },
                  { value: "gameplay", label: "Gameplay" },
                  { value: "performance", label: "Performance" },
                  { value: "story", label: "Story" },
                  { value: "audio", label: "Audio" },
                  { value: "multiplayer", label: "Multiplayer" },
                  { value: "pricing", label: "Pricing" },
                ]}
                value={analysisAspect}
                onChange={(e) => setAnalysisAspect(e.target.value)}
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-medium text-slate-300">Sentiment Polarity</label>
              <Select
                options={[
                  { value: "all", label: "All Polarity" },
                  { value: "positive", label: "Positive" },
                  { value: "negative", label: "Negative" },
                  { value: "neutral", label: "Neutral" },
                ]}
                value={analysisSentiment}
                onChange={(e) => setAnalysisSentiment(e.target.value)}
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreateAnalysisModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={createAnalysisMutation.isPending}
            >
              Save Configuration
            </Button>
          </div>
        </form>
      </Modal>

      {/* Freeze Snapshot Modal */}
      <Modal
        isOpen={isCreateSnapshotModalOpen}
        onClose={() => setIsCreateSnapshotModalOpen(false)}
        title="Freeze Reproducibility Snapshot"
        description="Create an immutable audit snapshot of this analysis's exact filters and model versions."
        maxWidth="md"
      >
        <form onSubmit={handleCreateSnapshot} className="space-y-4">
          <Input
            label="Snapshot Name"
            type="text"
            required
            value={snapshotName}
            onChange={(e) => setSnapshotName(e.target.value)}
          />

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-300">Description</label>
            <textarea
              className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-white placeholder-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 min-h-16"
              placeholder="e.g. Pre-patch baseline evaluation..."
              value={snapshotDesc}
              onChange={(e) => setSnapshotDesc(e.target.value)}
            />
          </div>

          <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-900/40 text-xs text-amber-200 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
            <span className="text-[11px] leading-relaxed">
              Snapshots are permanently immutable once frozen. Updates to future queries will not alter this snapshot.
            </span>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreateSnapshotModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={createSnapshotMutation.isPending}
            >
              Freeze Snapshot
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Collaborator Modal */}
      <Modal
        isOpen={isAddMemberModalOpen}
        onClose={() => setIsAddMemberModalOpen(false)}
        title="Invite Collaborator"
        description="Grant a researcher access to this project workspace."
        maxWidth="md"
      >
        <form onSubmit={handleAddMember} className="space-y-4">
          <Input
            label="Collaborator Email"
            type="email"
            required
            placeholder="colleague@institution.edu"
            value={memberEmail}
            onChange={(e) => setMemberEmail(e.target.value)}
          />

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-300">Permission Role</label>
            <Select
              options={[
                { value: "editor", label: "Editor (Can modify games & analyses)" },
                { value: "viewer", label: "Viewer (Read-only access)" },
              ]}
              value={memberRole}
              onChange={(e) => setMemberRole(e.target.value as "editor" | "viewer")}
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsAddMemberModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={addMemberMutation.isPending}
            >
              Grant Access
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
