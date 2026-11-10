import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "../src/app/router/Router";
import { AuthModal } from "../src/features/auth/components/AuthModal";
import { WorkspaceProjectsPage } from "../src/pages/WorkspaceProjectsPage";
import { ProjectDetailPage } from "../src/pages/ProjectDetailPage";
import { Header } from "../src/app/layouts/Header";
import * as authContext from "../src/features/auth/context/AuthContext";
import * as workspaceApi from "../src/features/workspace/api/workspaceApi";
import * as gamesApi from "../src/features/games/api/gamesApi";
import {
  ResearchProject,
  ProjectGameItem,
  SavedAnalysis,
  AnalysisSnapshot,
  ProjectMemberItem,
} from "../src/features/workspace/types/workspace";
import { User } from "../src/features/auth/types/auth";
import { GameItem } from "../src/features/games/types/game";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

const mockUser: User = {
  id: "user-123",
  email: "researcher@steamscoop.ai",
  display_name: "Dr. Gordon Freeman",
  status: "active",
  roles: ["researcher"],
};

const mockProjects: ResearchProject[] = [
  {
    id: "proj-1",
    name: "RPG Narrative Sentiment Study",
    description: "Investigating player reception across CRPG titles",
    visibility: "private",
    status: "active",
    owner_user_id: "user-123",
    current_user_role: "owner",
    created_at: "2026-03-01T10:00:00Z",
    updated_at: "2026-03-02T12:00:00Z",
  },
  {
    id: "proj-2",
    name: "Multiplayer Performance Benchmarks",
    description: "Analyzing network stability and lag complaints in reviews",
    visibility: "shared",
    status: "active",
    owner_user_id: "user-456",
    current_user_role: "editor",
    created_at: "2026-03-05T09:00:00Z",
    updated_at: "2026-03-06T15:00:00Z",
  },
  {
    id: "proj-3",
    name: "Indie Roguelike Taxonomy",
    description: "Community feedback on procedural generation",
    visibility: "shared",
    status: "active",
    owner_user_id: "user-789",
    current_user_role: "viewer",
    created_at: "2026-03-08T08:00:00Z",
    updated_at: "2026-03-09T11:00:00Z",
  },
];

const mockProjectGames: ProjectGameItem[] = [
  {
    project_id: "proj-1",
    game_id: "game-101",
    title: "Baldur's Gate 3",
    added_at: "2026-03-01T10:00:00Z",
  },
  {
    project_id: "proj-1",
    game_id: "game-102",
    title: "Cyberpunk 2077",
    added_at: "2026-03-01T11:00:00Z",
  },
];

const mockSavedAnalyses: SavedAnalysis[] = [
  {
    id: "sa-1",
    project_id: "proj-1",
    name: "Story & Narrative ABSA Explorer",
    description: "Reviews focused on story aspect",
    analysis_type: "aspect_explorer",
    query_config: {
      game_ids: ["game-101", "game-102"],
      aspect: "story",
      sentiment: "all",
      model_version: "baseline",
    },
    created_at: "2026-03-02T10:00:00Z",
    updated_at: "2026-03-02T10:00:00Z",
  },
];

const mockSnapshots: AnalysisSnapshot[] = [
  {
    id: "snap-1",
    saved_analysis_id: "sa-1",
    name: "Pre-Patch 5 Benchmark Snapshot",
    description: "Frozen immutable dataset checkpoint before patch release",
    data_cutoff_at: "2026-03-02T14:00:00Z",
    configuration_snapshot: {
      aspect: "story",
      model_version: "baseline",
    },
    result_summary: {
      positive_ratio: 0.92,
      story_prominence: 0.85,
    },
    created_at: "2026-03-02T14:30:00Z",
  },
];

const mockMembers: ProjectMemberItem[] = [
  {
    project_id: "proj-1",
    user_id: "user-123",
    project_role: "owner",
    email: "researcher@steamscoop.ai",
    display_name: "Dr. Gordon Freeman",
    joined_at: "2026-03-01T10:00:00Z",
  },
  {
    project_id: "proj-1",
    user_id: "user-456",
    project_role: "editor",
    email: "alyx.vance@blackmesa.org",
    display_name: "Alyx Vance",
    joined_at: "2026-03-02T11:00:00Z",
  },
  {
    project_id: "proj-1",
    user_id: "user-789",
    project_role: "viewer",
    email: "eli.vance@blackmesa.org",
    display_name: "Eli Vance",
    joined_at: "2026-03-03T09:00:00Z",
  },
];

const mockCatalogGames: GameItem[] = [
  {
    id: "game-101",
    steam_app_id: 1086940,
    name: "Baldur's Gate 3",
    catalog_status: "indexed",
    genres: ["RPG"],
    review_count: 500000,
    model_sentiment_positive_rate: 0.94,
  },
  {
    id: "game-103",
    steam_app_id: 620,
    name: "Portal 2",
    catalog_status: "indexed",
    genres: ["Puzzle"],
    review_count: 350000,
    model_sentiment_positive_rate: 0.98,
  },
];

describe("Research Workspace Experience", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe("Header Auth Navigation & Profile", () => {
    it("renders Sign In button when user is unauthenticated", () => {
      const openAuthModalMock = vi.fn();
      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: false,
        openAuthModal: openAuthModalMock,
        closeAuthModal: vi.fn(),
      });

      render(
        <RouterProvider initialPath="/">
          <Header />
        </RouterProvider>
      );

      const signInBtn = screen.getByRole("button", { name: /sign in/i });
      expect(signInBtn).toBeInTheDocument();
      fireEvent.click(signInBtn);
      expect(openAuthModalMock).toHaveBeenCalledTimes(1);
    });

    it("renders user profile pill and logout button when authenticated", () => {
      const logoutMock = vi.fn();
      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: logoutMock,
        isAuthModalOpen: false,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      render(
        <RouterProvider initialPath="/">
          <Header />
        </RouterProvider>
      );

      expect(screen.getByText("Dr. Gordon Freeman")).toBeInTheDocument();
      expect(screen.getByText("researcher")).toBeInTheDocument();

      const logoutBtn = screen.getByRole("button", { name: /sign out/i });
      expect(logoutBtn).toBeInTheDocument();
      fireEvent.click(logoutBtn);
      expect(logoutMock).toHaveBeenCalledTimes(1);
    });
  });

  describe("AuthModal", () => {
    it("renders sign in form and switches to register tab", () => {
      const loginMock = vi.fn().mockResolvedValue(undefined);
      const registerMock = vi.fn().mockResolvedValue(undefined);
      const closeAuthModalMock = vi.fn();

      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: loginMock,
        register: registerMock,
        logout: vi.fn(),
        isAuthModalOpen: true,
        openAuthModal: vi.fn(),
        closeAuthModal: closeAuthModalMock,
      });

      render(<AuthModal />);

      expect(screen.getByText("Researcher Sign In")).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.queryByLabelText(/display name/i)).not.toBeInTheDocument();

      // Switch to Register tab
      const createAccountTab = screen.getByRole("tab", { name: /create account/i });
      fireEvent.click(createAccountTab);

      expect(screen.getByText("Register Researcher Account")).toBeInTheDocument();
      expect(screen.getByLabelText(/display name/i)).toBeInTheDocument();

      // Switch back to Sign In tab
      const signInTab = screen.getByRole("tab", { name: /sign in/i });
      fireEvent.click(signInTab);
      expect(screen.getByText("Researcher Sign In")).toBeInTheDocument();
    });

    it("handles sign in submission successfully", async () => {
      const loginMock = vi.fn().mockResolvedValue(undefined);

      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: loginMock,
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: true,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      render(<AuthModal />);

      fireEvent.change(screen.getByLabelText(/email address/i), {
        target: { value: "freeman@blackmesa.gov" },
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: "lambda-core-secret" },
      });

      const submitBtn = screen.getByRole("button", { name: /sign in to workspace/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(loginMock).toHaveBeenCalledWith({
          email: "freeman@blackmesa.gov",
          password: "lambda-core-secret",
        });
      });
    });

    it("displays error message on failed sign in", async () => {
      const loginMock = vi.fn().mockRejectedValue(new Error("Invalid researcher credentials"));

      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: loginMock,
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: true,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      render(<AuthModal />);

      fireEvent.change(screen.getByLabelText(/email address/i), {
        target: { value: "wrong@test.com" },
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: "badpass" },
      });

      const submitBtn = screen.getByRole("button", { name: /sign in to workspace/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByText("Invalid researcher credentials")).toBeInTheDocument();
      });
    });
  });

  describe("WorkspaceProjectsPage", () => {
    it("renders unauthenticated callout when user is not signed in", () => {
      const queryClient = createTestQueryClient();
      const openAuthModalMock = vi.fn();
      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: false,
        openAuthModal: openAuthModalMock,
        closeAuthModal: vi.fn(),
      });

      vi.spyOn(workspaceApi, "useProjects").mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/workspace">
            <WorkspaceProjectsPage />
          </RouterProvider>
        </QueryClientProvider>
      );

      expect(screen.getByText("Authentication Required for Workspaces")).toBeInTheDocument();
      const signInBtn = screen.getByRole("button", { name: /sign in \/ register account/i });
      fireEvent.click(signInBtn);
      expect(openAuthModalMock).toHaveBeenCalledTimes(1);
    });

    it("renders project listing with role and visibility badges when authenticated", () => {
      const queryClient = createTestQueryClient();
      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: false,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      vi.spyOn(workspaceApi, "useProjects").mockReturnValue({
        data: { items: mockProjects, total: 3 },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/workspace">
            <WorkspaceProjectsPage />
          </RouterProvider>
        </QueryClientProvider>
      );

      // Verify projects rendered
      expect(screen.getByText("RPG Narrative Sentiment Study")).toBeInTheDocument();
      expect(screen.getByText("Multiplayer Performance Benchmarks")).toBeInTheDocument();
      expect(screen.getByText("Indie Roguelike Taxonomy")).toBeInTheDocument();

      // Verify role and visibility badges
      expect(screen.getByText("Owner")).toBeInTheDocument();
      expect(screen.getByText("Editor")).toBeInTheDocument();
      expect(screen.getByText("Viewer")).toBeInTheDocument();
      expect(screen.getByText("Private")).toBeInTheDocument();
      expect(screen.getAllByText("Shared").length).toBeGreaterThanOrEqual(1);

      // Verify New Project button is visible for authenticated users
      expect(screen.getByRole("button", { name: /new project/i })).toBeInTheDocument();
    });

    it("filters projects list via search input", () => {
      const queryClient = createTestQueryClient();
      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: false,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      vi.spyOn(workspaceApi, "useProjects").mockReturnValue({
        data: { items: mockProjects, total: 3 },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/workspace">
            <WorkspaceProjectsPage />
          </RouterProvider>
        </QueryClientProvider>
      );

      const searchInput = screen.getByPlaceholderText("Search projects...");
      fireEvent.change(searchInput, { target: { value: "Narrative" } });

      expect(screen.getByText("RPG Narrative Sentiment Study")).toBeInTheDocument();
      expect(screen.queryByText("Multiplayer Performance Benchmarks")).not.toBeInTheDocument();
      expect(screen.queryByText("Indie Roguelike Taxonomy")).not.toBeInTheDocument();
    });

    it("opens New Project modal and creates a project", async () => {
      const queryClient = createTestQueryClient();
      const mutateAsyncMock = vi.fn().mockResolvedValue(mockProjects[0]);

      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: false,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      vi.spyOn(workspaceApi, "useProjects").mockReturnValue({
        data: { items: mockProjects, total: 3 },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      vi.spyOn(workspaceApi, "useCreateProject").mockReturnValue({
        mutateAsync: mutateAsyncMock,
        isPending: false,
      } as any);

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/workspace">
            <WorkspaceProjectsPage />
          </RouterProvider>
        </QueryClientProvider>
      );

      const newProjectBtn = screen.getByRole("button", { name: /new project/i });
      fireEvent.click(newProjectBtn);

      expect(screen.getByText("Create New Research Project")).toBeInTheDocument();

      fireEvent.change(screen.getByLabelText(/project name/i), {
        target: { value: "New Stealth Cohort" },
      });
      fireEvent.change(screen.getByPlaceholderText(/outline research scope/i), {
        target: { value: "Investigating stealth genre reception" },
      });

      const submitBtn = screen.getByRole("button", { name: /create workspace/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(mutateAsyncMock).toHaveBeenCalledWith({
          name: "New Stealth Cohort",
          description: "Investigating stealth genre reception",
          visibility: "private",
        });
      });
    });
  });

  describe("ProjectDetailPage & Permissions", () => {
    it("renders project details and owner controls for owner role", () => {
      const queryClient = createTestQueryClient();
      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: false,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      vi.spyOn(workspaceApi, "useProject").mockReturnValue({
        data: mockProjects[0], // current_user_role: "owner"
        isLoading: false,
        error: null,
      } as any);

      vi.spyOn(workspaceApi, "useProjectGames").mockReturnValue({
        data: mockProjectGames,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useSavedAnalyses").mockReturnValue({
        data: mockSavedAnalyses,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useProjectMembers").mockReturnValue({
        data: mockMembers,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useSnapshots").mockReturnValue({
        data: mockSnapshots,
        isLoading: false,
      } as any);

      vi.spyOn(gamesApi, "useGames").mockReturnValue({
        data: { items: mockCatalogGames, total: 2 },
      } as any);

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/workspace/projects/proj-1">
            <ProjectDetailPage />
          </RouterProvider>
        </QueryClientProvider>
      );

      // Verify header details
      expect(screen.getByText("RPG Narrative Sentiment Study")).toBeInTheDocument();
      expect(screen.getByText("Investigating player reception across CRPG titles")).toBeInTheDocument();

      // Owner should see Settings & Delete
      expect(screen.getByRole("button", { name: /^settings$/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^delete$/i })).toBeInTheDocument();

      // Verify Saved Analyses tab content
      expect(screen.getByText("Story & Narrative ABSA Explorer")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /new analysis/i })).toBeInTheDocument();
    });

    it("switches to Project Games tab and displays cohort games", () => {
      const queryClient = createTestQueryClient();
      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: false,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      vi.spyOn(workspaceApi, "useProject").mockReturnValue({
        data: mockProjects[0],
        isLoading: false,
        error: null,
      } as any);

      vi.spyOn(workspaceApi, "useProjectGames").mockReturnValue({
        data: mockProjectGames,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useSavedAnalyses").mockReturnValue({
        data: mockSavedAnalyses,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useProjectMembers").mockReturnValue({
        data: mockMembers,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useSnapshots").mockReturnValue({
        data: mockSnapshots,
        isLoading: false,
      } as any);

      vi.spyOn(gamesApi, "useGames").mockReturnValue({
        data: { items: mockCatalogGames, total: 2 },
      } as any);

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/workspace/projects/proj-1">
            <ProjectDetailPage />
          </RouterProvider>
        </QueryClientProvider>
      );

      const gamesTab = screen.getByRole("tab", { name: /project games/i });
      fireEvent.click(gamesTab);

      expect(screen.getByText("Baldur's Gate 3")).toBeInTheDocument();
      expect(screen.getByText("Cyberpunk 2077")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /add game to project/i })).toBeInTheDocument();
    });

    it("switches to Collaborators tab and displays team members with roles", () => {
      const queryClient = createTestQueryClient();
      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: false,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      vi.spyOn(workspaceApi, "useProject").mockReturnValue({
        data: mockProjects[0], // Owner
        isLoading: false,
        error: null,
      } as any);

      vi.spyOn(workspaceApi, "useProjectGames").mockReturnValue({
        data: mockProjectGames,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useSavedAnalyses").mockReturnValue({
        data: mockSavedAnalyses,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useProjectMembers").mockReturnValue({
        data: mockMembers,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useSnapshots").mockReturnValue({
        data: mockSnapshots,
        isLoading: false,
      } as any);

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/workspace/projects/proj-1">
            <ProjectDetailPage />
          </RouterProvider>
        </QueryClientProvider>
      );

      const membersTab = screen.getByRole("tab", { name: /collaborators/i });
      fireEvent.click(membersTab);

      expect(screen.getByText("Alyx Vance")).toBeInTheDocument();
      expect(screen.getByText("Eli Vance")).toBeInTheDocument();
      expect(screen.getByText("alyx.vance@blackmesa.org")).toBeInTheDocument();

      // Owner can add collaborators
      expect(screen.getByRole("button", { name: /add collaborator/i })).toBeInTheDocument();
    });

    it("switches to Snapshots tab and displays frozen reproducibility snapshot", () => {
      const queryClient = createTestQueryClient();
      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: false,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      vi.spyOn(workspaceApi, "useProject").mockReturnValue({
        data: mockProjects[0],
        isLoading: false,
        error: null,
      } as any);

      vi.spyOn(workspaceApi, "useProjectGames").mockReturnValue({
        data: mockProjectGames,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useSavedAnalyses").mockReturnValue({
        data: mockSavedAnalyses,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useProjectMembers").mockReturnValue({
        data: mockMembers,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useSnapshots").mockReturnValue({
        data: mockSnapshots,
        isLoading: false,
      } as any);

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/workspace/projects/proj-1">
            <ProjectDetailPage />
          </RouterProvider>
        </QueryClientProvider>
      );

      const snapshotsTab = screen.getByRole("tab", { name: /snapshots/i });
      fireEvent.click(snapshotsTab);

      expect(screen.getByText("Pre-Patch 5 Benchmark Snapshot")).toBeInTheDocument();
      expect(screen.getByText("Immutable")).toBeInTheDocument();
      expect(screen.getByText("Data Cutoff Watermark:")).toBeInTheDocument();
      expect(screen.getByText("Parent Analysis:")).toBeInTheDocument();
    });

    it("enforces Viewer permissions: hides settings, delete, and add member options", () => {
      const queryClient = createTestQueryClient();
      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: { ...mockUser, id: "user-999" }, // Not owner
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: false,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      // Project where current_user_role is "viewer" and owner_user_id is someone else
      vi.spyOn(workspaceApi, "useProject").mockReturnValue({
        data: mockProjects[2], // role: viewer, owner_user_id: user-789
        isLoading: false,
        error: null,
      } as any);

      vi.spyOn(workspaceApi, "useProjectGames").mockReturnValue({
        data: mockProjectGames,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useSavedAnalyses").mockReturnValue({
        data: mockSavedAnalyses,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useProjectMembers").mockReturnValue({
        data: mockMembers,
        isLoading: false,
      } as any);

      vi.spyOn(workspaceApi, "useSnapshots").mockReturnValue({
        data: mockSnapshots,
        isLoading: false,
      } as any);

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/workspace/projects/proj-3">
            <ProjectDetailPage />
          </RouterProvider>
        </QueryClientProvider>
      );

      // Viewer should NOT see Delete or Settings
      expect(screen.queryByRole("button", { name: /^delete$/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /^settings$/i })).not.toBeInTheDocument();

      // Viewer should NOT see "New Analysis"
      expect(screen.queryByRole("button", { name: /new analysis/i })).not.toBeInTheDocument();

      // Go to Collaborators tab - Viewer should NOT see Add Collaborator
      const membersTab = screen.getByRole("tab", { name: /collaborators/i });
      fireEvent.click(membersTab);

      expect(screen.queryByRole("button", { name: /add collaborator/i })).not.toBeInTheDocument();
    });

    it("displays error alert when project fails to load", () => {
      const queryClient = createTestQueryClient();
      vi.spyOn(authContext, "useAuth").mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isAuthModalOpen: false,
        openAuthModal: vi.fn(),
        closeAuthModal: vi.fn(),
      });

      vi.spyOn(workspaceApi, "useProject").mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error("Project 'proj-missing' was not found or access denied"),
      } as any);

      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider initialPath="/workspace/projects/proj-missing">
            <ProjectDetailPage />
          </RouterProvider>
        </QueryClientProvider>
      );

      expect(screen.getByText("Project Not Accessible")).toBeInTheDocument();
      expect(screen.getByText("Project 'proj-missing' was not found or access denied")).toBeInTheDocument();
    });
  });
});
