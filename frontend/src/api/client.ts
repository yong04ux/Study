import axios, { AxiosError } from "axios";
import { getStoredAccessToken } from "../contexts/auth-storage";
import type { ApiErrorPayload } from "../types/common";

const apiBaseURL = import.meta.env.VITE_API_BASE_URL?.trim() || "/";

export const apiClient = axios.create({
  baseURL: apiBaseURL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

export function getApiBaseUrl() {
  return apiBaseURL;
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function extractErrorMessage(error: AxiosError<ApiErrorPayload>) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  return error.message || "Request failed. Please try again.";
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorPayload>) => Promise.reject(new Error(extractErrorMessage(error))),
);
