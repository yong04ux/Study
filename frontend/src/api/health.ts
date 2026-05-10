import { apiClient } from "./client";
import type { HealthResponse } from "../types/health";

export async function fetchHealth() {
  // 最小联调接口，用于确认前端能访问 FastAPI 后端。
  const { data } = await apiClient.get<HealthResponse>("/api/v1/health");
  return data;
}
