import { MetaEnvelope, ResponseEnvelope } from "../types/api";

export interface ApiErrorDetail {
  field?: string | null;
  issue: string;
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: ApiErrorDetail[] | unknown;
  readonly requestId?: string | null;
  readonly retryAfter?: number | null;

  constructor(
    code: string,
    message: string,
    status = 500,
    details?: ApiErrorDetail[] | unknown,
    requestId?: string | null,
    retryAfter?: number | null
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
    this.requestId = requestId;
    this.retryAfter = retryAfter;
  }
}

const DEFAULT_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || "/api/v1";

export interface ApiClientOptions extends RequestInit {
  params?: Record<string, string | number | boolean | null | undefined>;
}

function buildUrl(endpoint: string, params?: ApiClientOptions["params"]): string {
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const base = endpoint.startsWith("http")
    ? endpoint
    : `${DEFAULT_BASE_URL}${normalizedEndpoint}`;

  if (!params) {
    return base;
  }

  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.append(key, String(value));
    }
  }

  const queryString = searchParams.toString();
  if (!queryString) {
    return base;
  }

  return base.includes("?") ? `${base}&${queryString}` : `${base}?${queryString}`;
}

export async function apiClientWithMeta<T>(
  endpoint: string,
  options?: ApiClientOptions
): Promise<{ data: T; meta: MetaEnvelope }> {
  const { params, ...fetchOptions } = options || {};
  const url = buildUrl(endpoint, params);

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(fetchOptions?.headers || {}),
    },
    ...fetchOptions,
  });

  const retryAfterHeader = response.headers?.get?.("Retry-After");
  const retryAfter = retryAfterHeader ? parseInt(retryAfterHeader, 10) : null;

  let envelope: ResponseEnvelope<T> | null = null;
  try {
    envelope = (await response.json()) as ResponseEnvelope<T>;
  } catch {
    // Non-JSON response
    if (!response.ok) {
      throw new ApiError(
        "NETWORK_ERROR",
        `HTTP ${response.status}: ${response.statusText || "Request failed"}`,
        response.status,
        null,
        null,
        retryAfter
      );
    }
  }

  if (!response.ok || envelope?.error) {
    throw new ApiError(
      envelope?.error?.code || `HTTP_${response.status}`,
      envelope?.error?.message || `HTTP ${response.status}: Failed to fetch ${url}`,
      response.status,
      envelope?.error?.details,
      envelope?.error?.request_id || envelope?.meta?.request_id,
      retryAfter
    );
  }

  if (!envelope || envelope.data === null) {
    throw new ApiError(
      "EMPTY_DATA",
      "Received empty payload from server",
      response.status,
      null,
      envelope?.meta?.request_id
    );
  }

  return {
    data: envelope.data,
    meta: envelope.meta,
  };
}

export async function apiClient<T>(
  endpoint: string,
  options?: ApiClientOptions
): Promise<T> {
  const result = await apiClientWithMeta<T>(endpoint, options);
  return result.data;
}
