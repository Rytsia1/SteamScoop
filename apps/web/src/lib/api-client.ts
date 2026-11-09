import { ResponseEnvelope } from "../types/api";

export class ApiError extends Error {
  code: string;
  details?: unknown;
  requestId?: string | null;

  constructor(code: string, message: string, details?: unknown, requestId?: string | null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.details = details;
    this.requestId = requestId;
  }
}

const DEFAULT_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || "/api/v1";

export async function apiClient<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = endpoint.startsWith("http")
    ? endpoint
    : `${DEFAULT_BASE_URL}${normalizedEndpoint}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  const envelope: ResponseEnvelope<T> = await response.json();

  if (!response.ok || envelope.error) {
    throw new ApiError(
      envelope.error?.code || "HTTP_ERROR",
      envelope.error?.message || `HTTP ${response.status}: Failed to fetch ${url}`,
      envelope.error?.details,
      envelope.error?.request_id || envelope.meta?.request_id
    );
  }

  if (envelope.data === null) {
    throw new ApiError(
      "EMPTY_DATA",
      "Received empty payload from server",
      null,
      envelope.meta?.request_id
    );
  }

  return envelope.data;
}
