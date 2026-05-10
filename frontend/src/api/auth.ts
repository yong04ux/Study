import { apiClient } from "./client";
import type {
  CurrentUserResponse,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
} from "../types/auth";

export async function registerUser(payload: RegisterRequest): Promise<CurrentUserResponse> {
  const { data } = await apiClient.post<CurrentUserResponse>("/auth/register", payload);
  return data;
}

export async function loginUser(payload: LoginRequest): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", payload);
  return data;
}

export async function getCurrentUser(): Promise<CurrentUserResponse> {
  const { data } = await apiClient.get<CurrentUserResponse>("/auth/me");
  return data;
}
