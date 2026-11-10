import { apiClient, setAuthToken } from "../../../lib/api-client";
import {
  LoginCredentials,
  LoginResponseData,
  RegisterCredentials,
  User,
} from "../types/auth";

export async function registerUser(credentials: RegisterCredentials): Promise<User> {
  return apiClient<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export async function loginUser(credentials: LoginCredentials): Promise<LoginResponseData> {
  const result = await apiClient<LoginResponseData>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
  if (result.token) {
    setAuthToken(result.token);
  }
  return result;
}

export async function logoutUser(): Promise<void> {
  try {
    await apiClient<void>("/auth/logout", {
      method: "POST",
    });
  } finally {
    setAuthToken(null);
  }
}

export async function fetchCurrentUser(): Promise<User> {
  return apiClient<User>("/auth/me");
}

