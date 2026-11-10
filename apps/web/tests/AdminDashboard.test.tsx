import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "../src/app/router/Router";
import { Header } from "../src/app/layouts/Header";
import { AdminDashboardPage } from "../src/pages/AdminDashboardPage";
import * as authContext from "../src/features/auth/context/AuthContext";
import { adminClient } from "../src/features/admin/api/admin-client";
import {
  AdminAuditLog,
  AdminGame,
  AdminIngestionJob,
  AdminModel,
  AdminOperationalErrors,
  AdminPipelineRun,
} from "../src/types/admin";
import { User } from "../src/features/auth/types/auth";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const mockAdminUser: User = {
  id: "admin-123",
  email: "admin@steamscoop.com",
  display_name: "Super Admin",
  status: "active",
  roles: ["admin", "member"],
};

const mockRegularUser: User = {
  id: "user-456",
  email: "researcher@example.com",
  display_name: "Gordon Freeman",
  status: "active",
  roles: ["member"],
};

const mockGames: AdminGame[] = [
  {
    id: "game-1",
    steam_app_id: 1145360,
    name: "Hades",
    catalog_status: "indexed",
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-02-01T00:00:00Z",
  },
  {
    id: "game-2",
    steam_app_id: 367520,
    name: "Hollow Knight",
    catalog_status: "pending",
    is_active: false,
    created_at: "2026-01-02T00:00:00Z",
    updated_at: "2026-02-02T00:00:00Z",
  },
];

const mockJobs: AdminIngestionJob[] = [
  {
    job_id: "job-run-001",
    game_id: "game-1",
    job_type: "incremental",
    status: "running",
    target_reviews: 1000,
    collected_reviews: 650,
    started_at: "2026-03-01T10:00:00Z",
  },
  {
    job_id: "job-fail-002",
    game_id: "game-2",
    job_type: "historical",
    status: "failed",
    target_reviews: 5000,
    collected_reviews: 2100,
    error_code: "UPSTREAM_RATE_LIMIT",
    error_message: "Steam Store 429 backoff limit exceeded.",
    started_at: "2026-03-02T11:00:00Z",
    finished_at: "2026-03-02T11:15:00Z",
  },
];

const mockPipelines: AdminPipelineRun[] = [
  {
    run_id: "pipe-001",
    pipeline_type: "sentiment_batch",
    status: "succeeded",
    model_version_snapshot: "distilbert-v1.0.0",
    input_count: 5000,
    success_count: 4995,
    failure_count: 5,
    started_at: "2026-03-01T12:00:00Z",
    finished_at: "2026-03-01T12:05:00Z",
  },
  {
    run_id: "pipe-002",
    pipeline_type: "aspect_extraction",
    status: "failed",
    model_version_snapshot: "deberta-absa-v1.2",
    input_count: 1000,
    success_count: 850,
    failure_count: 150,
    error_summary: "CUDA out of memory exception during batch size 64",
    started_at: "2026-03-02T13:00:00Z",
    finished_at: "2026-03-02T13:02:00Z",
  },
];

const mockModels: AdminModel[] = [
  {
    id: "model-1",
    model_key: "distilbert-sentiment",
    version: "v1.0.0",
    task: "sentiment",
    framework: "transformers",
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "model-2",
    model_key: "roberta-sentiment-v2",
    version: "v2.0.0",
    task: "sentiment",
    framework: "transformers",
    is_active: false,
    created_at: "2026-02-15T00:00:00Z",
  },
];

const mockAuditLogs: AdminAuditLog[] = [
  {
    id: 101,
    action: "catalog.game.create",
    resource_type: "game",
    resource_id: "game-1",
    actor_user_id: "admin-123",
    metadata: { steam_app_id: 1145360, name: "Hades" },
    created_at: "2026-03-01T09:00:00Z",
  },
  {
    id: 102,
    action: "model.activate",
    resource_type: "ml_model",
    resource_id: "model-1",
    actor_user_id: "admin-123",
    metadata: { version: "v1.0.0", task: "sentiment" },
    created_at: "2026-03-01T09:30:00Z",
  },
];

const mockOperationalErrors: AdminOperationalErrors = {
  failed_ingestion_jobs: [mockJobs[1]],
  failed_pipeline_runs: [mockPipelines[1]],
  total_failures: 2,
};

describe("Administrative Dashboard & Security Guard", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();

    // Default admin mock endpoints
    vi.spyOn(adminClient, "listGames").mockResolvedValue(mockGames);
    vi.spyOn(adminClient, "listIngestionJobs").mockResolvedValue(mockJobs);
    vi.spyOn(adminClient, "listPipelineRuns").mockResolvedValue(mockPipelines);
    vi.spyOn(adminClient, "listModels").mockResolvedValue(mockModels);
    vi.spyOn(adminClient, "listAuditLogs").mockResolvedValue(mockAuditLogs);
    vi.spyOn(adminClient, "getOperationalErrors").mockResolvedValue(mockOperationalErrors);
    vi.spyOn(adminClient, "refreshMetadata").mockResolvedValue({
      game_id: "game-1",
      status: "queued",
      message: "Metadata refresh queued for 'Hades'.",
    });
    vi.spyOn(adminClient, "queueIngestionJob").mockResolvedValue({
      job_id: "new-job-123",
      game_id: "game-1",
      job_type: "incremental",
      status: "queued",
      target_reviews: 0,
      collected_reviews: 0,
    });
    vi.spyOn(adminClient, "createGame").mockResolvedValue({
      id: "game-3",
      steam_app_id: 413150,
      name: "Stardew Valley",
      catalog_status: "indexed",
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
    vi.spyOn(adminClient, "updateGame").mockResolvedValue({
      ...mockGames[0],
      is_active: false,
    });
    vi.spyOn(adminClient, "cancelIngestionJob").mockResolvedValue({
      ...mockJobs[0],
      status: "cancelled",
    });
    vi.spyOn(adminClient, "retryIngestionJob").mockResolvedValue({
      ...mockJobs[1],
      status: "queued",
    });
    vi.spyOn(adminClient, "activateModel").mockResolvedValue({
      model_id: "model-2",
      task: "sentiment",
      is_active: true,
      message: "Model activated successfully.",
    });
  });

  it("denies access to unauthenticated guests and prompts sign-in", () => {
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      openAuthModal: vi.fn(),
      closeAuthModal: vi.fn(),
      isAuthModalOpen: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider initialPath="/admin">
          <AdminDashboardPage />
        </RouterProvider>
      </QueryClientProvider>
    );

    expect(screen.getByText("Administrator Access Required")).toBeInTheDocument();
    expect(screen.getByText("Sign In as Administrator")).toBeInTheDocument();
  });

  it("denies access to non-admin authenticated users", () => {
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      user: mockRegularUser,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      openAuthModal: vi.fn(),
      closeAuthModal: vi.fn(),
      isAuthModalOpen: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider initialPath="/admin">
          <AdminDashboardPage />
        </RouterProvider>
      </QueryClientProvider>
    );

    expect(screen.getByText("Administrator Access Required")).toBeInTheDocument();
    expect(
      screen.getByText(/Your current account \(researcher@example\.com\) is not provisioned/i)
    ).toBeInTheDocument();
  });

  it("allows access to administrator and renders all navigation tabs with catalog games", async () => {
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      user: mockAdminUser,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      openAuthModal: vi.fn(),
      closeAuthModal: vi.fn(),
      isAuthModalOpen: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider initialPath="/admin">
          <AdminDashboardPage />
        </RouterProvider>
      </QueryClientProvider>
    );

    expect(screen.getByText("Administrative Command Center")).toBeInTheDocument();
    expect(screen.getByText(/Admin: Super Admin/i)).toBeInTheDocument();

    // Verify Tab Options
    expect(screen.getByRole("button", { name: /^Game Catalog/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Ingestion Jobs/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Pipeline Runs/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Model Registry/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Operational Errors/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Audit Trail/i })).toBeInTheDocument();

    // Catalog Table Content
    await waitFor(() => {
      expect(screen.getByText("Hades")).toBeInTheDocument();
      expect(screen.getByText("1145360")).toBeInTheDocument();
      expect(screen.getByText("Hollow Knight")).toBeInTheDocument();
      expect(screen.getByText("367520")).toBeInTheDocument();
    });
  });

  it("opens confirmation modal and triggers metadata refresh for a game", async () => {
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      user: mockAdminUser,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      openAuthModal: vi.fn(),
      closeAuthModal: vi.fn(),
      isAuthModalOpen: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider initialPath="/admin">
          <AdminDashboardPage />
        </RouterProvider>
      </QueryClientProvider>
    );

    await waitFor(() => expect(screen.getByText("Hades")).toBeInTheDocument());

    const refreshButtons = screen.getAllByRole("button", { name: /Refresh Metadata/i });
    fireEvent.click(refreshButtons[0]);

    // Modal Confirmation Dialog appears
    expect(screen.getByText("Confirm Metadata Refresh")).toBeInTheDocument();
    expect(
      screen.getByText(/Queue an asynchronous refresh of Steam store metadata and media assets for 'Hades'/i)
    ).toBeInTheDocument();

    const confirmBtn = screen.getByRole("button", { name: "Queue Refresh" });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(adminClient.refreshMetadata).toHaveBeenCalledWith("game-1");
    });
  });

  it("opens new game modal and creates a new game record in catalog", async () => {
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      user: mockAdminUser,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      openAuthModal: vi.fn(),
      closeAuthModal: vi.fn(),
      isAuthModalOpen: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider initialPath="/admin">
          <AdminDashboardPage />
        </RouterProvider>
      </QueryClientProvider>
    );

    await waitFor(() => expect(screen.getByText("Hades")).toBeInTheDocument());

    const addGameBtn = screen.getByRole("button", { name: /^Add Game$/i });
    fireEvent.click(addGameBtn);

    expect(screen.getByText("Add Game to Catalog")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Steam App ID \*/i), { target: { value: "413150" } });
    fireEvent.change(screen.getByLabelText(/Game Title \*/i), { target: { value: "Stardew Valley" } });
    fireEvent.change(screen.getByLabelText(/Short Description/i), {
      target: { value: "Country farming life." },
    });

    const modalDialog = screen.getByRole("dialog");
    const submitBtn = modalDialog.querySelector('button[type="submit"]') as HTMLButtonElement;
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(adminClient.createGame).toHaveBeenCalledWith(
        expect.objectContaining({
          steam_app_id: 413150,
          name: "Stardew Valley",
          short_description: "Country farming life.",
        })
      );
    });
  });

  it("switches to Ingestion Jobs tab, displays progress bar and handles cancellation", async () => {
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      user: mockAdminUser,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      openAuthModal: vi.fn(),
      closeAuthModal: vi.fn(),
      isAuthModalOpen: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider initialPath="/admin">
          <AdminDashboardPage />
        </RouterProvider>
      </QueryClientProvider>
    );

    const ingestionTabBtn = screen.getByRole("button", { name: /^Ingestion Jobs/i });
    fireEvent.click(ingestionTabBtn);

    await waitFor(() => {
      expect(screen.getByText("job-run-...")).toBeInTheDocument();
      expect(screen.getByText("650 collected")).toBeInTheDocument();
      expect(screen.getByText(/65%/i)).toBeInTheDocument();
    });

    // Test Cancel Action with confirmation
    const cancelBtn = screen.getByRole("button", { name: /Cancel/i });
    fireEvent.click(cancelBtn);

    expect(screen.getByRole("heading", { name: "Cancel Ingestion Job" })).toBeInTheDocument();
    const confirmCancelBtn = screen.getByRole("button", { name: "Cancel Ingestion Job" });
    fireEvent.click(confirmCancelBtn);

    await waitFor(() => {
      expect(adminClient.cancelIngestionJob).toHaveBeenCalledWith("job-run-001");
    });
  });

  it("switches to Model Registry tab, displays models and activates candidate model", async () => {
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      user: mockAdminUser,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      openAuthModal: vi.fn(),
      closeAuthModal: vi.fn(),
      isAuthModalOpen: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider initialPath="/admin">
          <AdminDashboardPage />
        </RouterProvider>
      </QueryClientProvider>
    );

    const modelTabBtn = screen.getByRole("button", { name: /^Model Registry/i });
    fireEvent.click(modelTabBtn);

    await waitFor(() => {
      expect(screen.getByText("distilbert-sentiment")).toBeInTheDocument();
      expect(screen.getByText("roberta-sentiment-v2")).toBeInTheDocument();
      expect(screen.getByText("Active (Production)")).toBeInTheDocument();
    });

    // Click Activate on candidate model
    const activateBtn = screen.getByRole("button", { name: /Activate/i });
    fireEvent.click(activateBtn);

    expect(screen.getByText("Confirm Model Activation")).toBeInTheDocument();
    expect(
      screen.getByText(/Activate model 'roberta-sentiment-v2' \(v2\.0\.0\) for task 'sentiment'/i)
    ).toBeInTheDocument();

    const confirmActivateBtn = screen.getByRole("button", { name: "Activate in Production" });
    fireEvent.click(confirmActivateBtn);

    await waitFor(() => {
      expect(adminClient.activateModel).toHaveBeenCalledWith("model-2");
    });
  });

  it("switches to Operational Errors tab and displays diagnostics", async () => {
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      user: mockAdminUser,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      openAuthModal: vi.fn(),
      closeAuthModal: vi.fn(),
      isAuthModalOpen: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider initialPath="/admin">
          <AdminDashboardPage />
        </RouterProvider>
      </QueryClientProvider>
    );

    const errorsTabBtn = screen.getByRole("button", { name: /^Operational Errors/i });
    fireEvent.click(errorsTabBtn);

    await waitFor(() => {
      expect(screen.getByText("System Failures & Operational Diagnostics")).toBeInTheDocument();
      expect(screen.getByText("Error: UPSTREAM_RATE_LIMIT")).toBeInTheDocument();
      expect(screen.getByText("Steam Store 429 backoff limit exceeded.")).toBeInTheDocument();
      expect(
        screen.getByText("CUDA out of memory exception during batch size 64")
      ).toBeInTheDocument();
    });
  });

  it("switches to Audit Trail tab and displays recorded audit logs", async () => {
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      user: mockAdminUser,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      openAuthModal: vi.fn(),
      closeAuthModal: vi.fn(),
      isAuthModalOpen: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider initialPath="/admin">
          <AdminDashboardPage />
        </RouterProvider>
      </QueryClientProvider>
    );

    const auditTabBtn = screen.getByRole("button", { name: /^Audit Trail/i });
    fireEvent.click(auditTabBtn);

    await waitFor(() => {
      expect(screen.getByText("catalog.game.create")).toBeInTheDocument();
      expect(screen.getByText("model.activate")).toBeInTheDocument();
      expect(screen.getByText("#101")).toBeInTheDocument();
      expect(screen.getByText("#102")).toBeInTheDocument();
    });
  });

  it("Header displays Admin navigation link only for authenticated admins", () => {
    // 1. Regular user has NO admin link
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      user: mockRegularUser,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      openAuthModal: vi.fn(),
      closeAuthModal: vi.fn(),
      isAuthModalOpen: false,
    });

    const { unmount } = render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider initialPath="/">
          <Header />
        </RouterProvider>
      </QueryClientProvider>
    );

    expect(screen.queryByRole("link", { name: /Admin/i })).not.toBeInTheDocument();
    unmount();

    // 2. Admin user HAS Admin link
    vi.spyOn(authContext, "useAuth").mockReturnValue({
      user: mockAdminUser,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      openAuthModal: vi.fn(),
      closeAuthModal: vi.fn(),
      isAuthModalOpen: false,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider initialPath="/">
          <Header />
        </RouterProvider>
      </QueryClientProvider>
    );

    const adminLink = screen.getByRole("link", { name: /Admin/i });
    expect(adminLink).toBeInTheDocument();
    expect(adminLink).toHaveAttribute("href", "/admin");
  });
});
