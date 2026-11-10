import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient, apiClientWithMeta, ApiError } from "../src/lib/api-client";

describe("API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("unwraps data envelope successfully on 200 OK", async () => {
    const mockEnvelope = {
      data: { id: "123", title: "Portal 2" },
      error: null,
      meta: { request_id: "req_abc_1", timestamp: "2026-11-10T00:00:00Z" },
    };

    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers(),
      json: async () => mockEnvelope,
    } as Response);

    const result = await apiClient<{ id: string; title: string }>("/games/123");

    expect(result.id).toBe("123");
    expect(result.title).toBe("Portal 2");
  });

  it("returns both data and meta in apiClientWithMeta", async () => {
    const mockEnvelope = {
      data: [{ id: "g1" }],
      error: null,
      meta: {
        request_id: "req_abc_2",
        timestamp: "2026-11-10T00:00:00Z",
        pagination: { next_cursor: "cursor_next_token", has_more: true, total_count: 50 },
      },
    };

    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers(),
      json: async () => mockEnvelope,
    } as Response);

    const result = await apiClientWithMeta<Array<{ id: string }>>("/games");

    expect(result.data).toHaveLength(1);
    expect(result.meta.pagination?.next_cursor).toBe("cursor_next_token");
    expect(result.meta.pagination?.has_more).toBe(true);
  });

  it("throws structured ApiError on non-200 or error envelope", async () => {
    const errorEnvelope = {
      data: null,
      error: {
        code: "RESOURCE_NOT_FOUND",
        message: "Game 'unknown' was not found",
        details: null,
        request_id: "req_err_404",
      },
      meta: { request_id: "req_err_404", timestamp: "2026-11-10T00:00:00Z" },
    };

    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 404,
      headers: new Headers(),
      json: async () => errorEnvelope,
    } as Response);

    await expect(apiClient("/games/unknown")).rejects.toThrowError(ApiError);

    try {
      await apiClient("/games/unknown");
    } catch (err) {
      const apiErr = err as ApiError;
      expect(apiErr.code).toBe("RESOURCE_NOT_FOUND");
      expect(apiErr.status).toBe(404);
      expect(apiErr.requestId).toBe("req_err_404");
    }
  });

  it("captures retry-after header when rate limited with 429", async () => {
    const rateLimitEnvelope = {
      data: null,
      error: {
        code: "RATE_LIMITED",
        message: "Quota exceeded",
        details: null,
      },
      meta: { request_id: "req_rate", timestamp: "2026-11-10T00:00:00Z" },
    };

    const headers = new Headers();
    headers.set("Retry-After", "45");

    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 429,
      headers,
      json: async () => rateLimitEnvelope,
    } as Response);

    try {
      await apiClient("/comparisons");
    } catch (err) {
      const apiErr = err as ApiError;
      expect(apiErr.code).toBe("RATE_LIMITED");
      expect(apiErr.status).toBe(429);
      expect(apiErr.retryAfter).toBe(45);
    }
  });

  it("serializes query parameters properly", async () => {
    let capturedUrl = "";
    vi.spyOn(global, "fetch").mockImplementation(async (url) => {
      capturedUrl = String(url);
      return {
        ok: true,
        status: 200,
        headers: new Headers(),
        json: async () => ({ data: [], error: null, meta: { request_id: "1", timestamp: "now" } }),
      } as Response;
    });

    await apiClient("/games", {
      params: { q: "Witcher", status: "indexed", limit: 10 },
    });

    expect(capturedUrl).toContain("q=Witcher");
    expect(capturedUrl).toContain("status=indexed");
    expect(capturedUrl).toContain("limit=10");
  });
});

