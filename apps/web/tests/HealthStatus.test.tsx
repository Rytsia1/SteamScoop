import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { HealthStatus } from "../src/components/HealthStatus";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe("HealthStatus component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders loading state initially", () => {
    const queryClient = createTestQueryClient();
    // Simulate pending fetch
    vi.spyOn(global, "fetch").mockImplementation(() => new Promise(() => {}));

    render(
      <QueryClientProvider client={queryClient}>
        <HealthStatus />
      </QueryClientProvider>
    );

    expect(screen.getByRole("status")).toHaveTextContent("Checking system health...");
  });

  it("renders healthy status when API returns successful envelope", async () => {
    const queryClient = createTestQueryClient();

    const mockResponse = {
      data: {
        status: "healthy",
        version: "0.1.0",
        app_env: "testing",
        timestamp: "2026-11-09T13:00:00Z",
      },
      error: null,
      meta: {
        request_id: "req_test_123",
        timestamp: "2026-11-09T13:00:00Z",
      },
    };

    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    render(
      <QueryClientProvider client={queryClient}>
        <HealthStatus />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByRole("region")).toBeInTheDocument();
      expect(screen.getByText(/Backend Connected: HEALTHY/i)).toBeInTheDocument();
      expect(screen.getByText("v0.1.0")).toBeInTheDocument();
    });
  });

  it("renders dependency status when provided in envelope", async () => {
    const queryClient = createTestQueryClient();

    const mockResponse = {
      data: {
        status: "healthy",
        version: "0.1.0",
        app_env: "development",
        timestamp: "2026-11-09T13:00:00Z",
        dependencies: {
          database: "connected",
          redis: "connected",
        },
      },
      error: null,
      meta: {
        request_id: "req_test_dep",
        timestamp: "2026-11-09T13:00:00Z",
      },
    };

    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    render(
      <QueryClientProvider client={queryClient}>
        <HealthStatus />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/DB: connected/i)).toBeInTheDocument();
      expect(screen.getByText(/Redis: connected/i)).toBeInTheDocument();
    });
  });

  it("renders error alert when API fetch fails", async () => {
    const queryClient = createTestQueryClient();

    vi.spyOn(global, "fetch").mockRejectedValue(new Error("Network connection refused"));

    render(
      <QueryClientProvider client={queryClient}>
        <HealthStatus />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText(/System Status: Disconnected/i)).toBeInTheDocument();
      expect(screen.getByText(/Network connection refused/i)).toBeInTheDocument();
    });
  });
});

