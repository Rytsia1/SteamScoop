import React, { useState } from "react";
import { Link } from "../app/router/Router";
import { useAuth } from "../features/auth/context/AuthContext";
import {
  useCreateProject,
  useProjects,
} from "../features/workspace/api/workspaceApi";
import { ProjectVisibility } from "../features/workspace/types/workspace";
import { Button } from "../components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { CardSkeleton } from "../components/feedback/LoadingSkeleton";
import { ErrorAlert } from "../components/feedback/ErrorAlert";
import {
  Briefcase,
  Plus,
  Lock,
  Globe,
  Shield,
  ArrowRight,
  LogIn,
  Search,
} from "lucide-react";

export const WorkspaceProjectsPage: React.FC = () => {
  const { user, isAuthenticated, openAuthModal } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // New Project Form State
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectDesc, setNewProjectDesc] = useState("");
  const [newProjectVisibility, setNewProjectVisibility] = useState<ProjectVisibility>("private");

  const {
    data: projectsData,
    isLoading: isLoadingProjects,
    error: projectsError,
    refetch,
  } = useProjects({ enabled: isAuthenticated });

  const createMutation = useCreateProject();

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    await createMutation.mutateAsync({
      name: newProjectName.trim(),
      description: newProjectDesc.trim() || undefined,
      visibility: newProjectVisibility,
    });

    setNewProjectName("");
    setNewProjectDesc("");
    setNewProjectVisibility("private");
    setIsCreateModalOpen(false);
  };

  const filteredProjects = (projectsData?.items || []).filter((p) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      p.name.toLowerCase().includes(q) ||
      (p.description && p.description.toLowerCase().includes(q))
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-950/70 border border-sky-800/60 text-xs font-medium text-sky-300">
            <Briefcase className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Research Workspaces</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Research Projects & Reproducibility Studies
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
            Manage collaborative research investigations, customize game cohorts, save analytical
            query configurations, and freeze immutable reproducibility snapshots.
          </p>
        </div>

        {isAuthenticated && (
          <Button
            variant="primary"
            onClick={() => setIsCreateModalOpen(true)}
            leftIcon={<Plus className="w-4 h-4" aria-hidden="true" />}
          >
            New Project
          </Button>
        )}
      </div>

      {/* Unauthenticated Prompt */}
      {!isAuthenticated && (
        <Card className="border-sky-900/50 bg-gradient-to-br from-sky-950/30 to-slate-900/60 p-8 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 mx-auto">
            <Shield className="w-6 h-6" aria-hidden="true" />
          </div>
          <div className="space-y-1 max-w-md mx-auto">
            <h3 className="text-base font-bold text-white">Authentication Required for Workspaces</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Sign in with your researcher account to create private projects, save customized review
              explorer queries, and manage team collaboration permissions.
            </p>
          </div>
          <Button
            variant="primary"
            onClick={openAuthModal}
            leftIcon={<LogIn className="w-4 h-4" aria-hidden="true" />}
          >
            Sign In / Register Account
          </Button>
        </Card>
      )}

      {/* Authenticated Workspace Content */}
      {isAuthenticated && (
        <div className="space-y-6">
          {/* Filter & Search Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="w-full sm:w-72">
              <Input
                type="text"
                placeholder="Search projects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={<Search className="w-4 h-4 text-slate-400" aria-hidden="true" />}
                className="py-1.5 text-xs"
              />
            </div>
            <div className="text-xs text-slate-400">
              Showing <b className="text-white">{filteredProjects.length}</b> accessible projects
            </div>
          </div>

          {/* Loading State */}
          {isLoadingProjects && <CardSkeleton count={3} />}

          {/* Error State */}
          {projectsError && (
            <ErrorAlert
              title="Failed to Load Projects"
              message={projectsError.message}
              onRetry={() => refetch()}
            />
          )}

          {/* Empty State */}
          {!isLoadingProjects && filteredProjects.length === 0 && (
            <div className="p-10 rounded-2xl border border-slate-800 bg-slate-900/40 text-center space-y-3">
              <Briefcase className="w-10 h-10 text-slate-500 mx-auto" aria-hidden="true" />
              <h3 className="text-base font-bold text-white">No Research Projects Found</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                {searchQuery
                  ? "No projects match your current search query."
                  : "You haven't created or been invited to any research projects yet. Create your first project to get started."}
              </p>
              {!searchQuery && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsCreateModalOpen(true)}
                  leftIcon={<Plus className="w-3.5 h-3.5" aria-hidden="true" />}
                >
                  Create Research Project
                </Button>
              )}
            </div>
          )}

          {/* Projects Grid */}
          {!isLoadingProjects && filteredProjects.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredProjects.map((project) => {
                const isOwner = project.current_user_role === "owner" || project.owner_user_id === user?.id;
                const roleBadgeVariant =
                  project.current_user_role === "owner"
                    ? "positive"
                    : project.current_user_role === "editor"
                    ? "info"
                    : "outline";

                return (
                  <Card
                    key={project.id}
                    className="flex flex-col justify-between hover:border-slate-700 transition-colors bg-slate-900/60"
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between gap-2">
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

                        <Badge variant={roleBadgeVariant} size="sm" className="font-mono text-[10px]">
                          {project.current_user_role
                            ? project.current_user_role.charAt(0).toUpperCase() + project.current_user_role.slice(1)
                            : isOwner
                            ? "Owner"
                            : "Viewer"}
                        </Badge>
                      </div>
                      <CardTitle className="text-base line-clamp-1 mt-2">
                        {project.name}
                      </CardTitle>
                    </CardHeader>

                    <CardContent className="space-y-4 pt-0">
                      <p className="text-xs text-slate-400 line-clamp-2 min-h-8">
                        {project.description || "No project description provided."}
                      </p>

                      <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                        <span className="text-[11px] text-slate-500 font-mono">
                          Updated {new Date(project.updated_at).toLocaleDateString()}
                        </span>
                        <Link
                          to={`/workspace/projects/${project.id}`}
                          className="inline-flex items-center gap-1.5 text-xs font-semibold text-sky-400 hover:text-sky-300"
                        >
                          <span>Open Workspace</span>
                          <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                        </Link>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* New Project Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Research Project"
        description="Initialize a private or shared workspace to organize games, analyses, and reproducibility snapshots."
        maxWidth="md"
      >
        <form onSubmit={handleCreateProject} className="space-y-4">
          <Input
            label="Project Name"
            type="text"
            required
            placeholder="e.g. Action RPG Sentiment Study"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
          />

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-300">
              Description (Optional)
            </label>
            <textarea
              className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-white placeholder-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 min-h-20"
              placeholder="Outline research scope, hypotheses, or analytical parameters..."
              value={newProjectDesc}
              onChange={(e) => setNewProjectDesc(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-300">
              Visibility Setting
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setNewProjectVisibility("private")}
                className={`p-3 rounded-lg border text-left flex items-start gap-2.5 transition-colors ${
                  newProjectVisibility === "private"
                    ? "bg-sky-500/10 border-sky-500/40 text-sky-300"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <Lock className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <span className="text-xs font-semibold block text-white">Private</span>
                  <span className="text-[11px] text-slate-400 leading-tight block mt-0.5">
                    Accessible only to you and invited collaborators.
                  </span>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setNewProjectVisibility("shared")}
                className={`p-3 rounded-lg border text-left flex items-start gap-2.5 transition-colors ${
                  newProjectVisibility === "shared"
                    ? "bg-sky-500/10 border-sky-500/40 text-sky-300"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <Globe className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <span className="text-xs font-semibold block text-white">Shared</span>
                  <span className="text-[11px] text-slate-400 leading-tight block mt-0.5">
                    Readable by platform members; modifications restricted.
                  </span>
                </div>
              </button>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={createMutation.isPending}
            >
              Create Workspace
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
