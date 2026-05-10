import { apiClient } from "./client";
import type {
  ReportStatusResponse,
  ReportSubmitRequest,
  ReportSubmitResponse
} from "../types/report";

export async function submitReport(
  payload: ReportSubmitRequest,
): Promise<ReportSubmitResponse> {
  // 提交异步报告任务：后端写入 Kafka 后立即返回 task_id。
  const { data } = await apiClient.post<ReportSubmitResponse>(
    "/reports/submit",
    payload,
  );

  return data;
}

export async function getReportStatus(
  taskId: string,
): Promise<ReportStatusResponse> {
  // 根据 task_id 查询 Redis 中的报告状态和结果。
  const { data } = await apiClient.get<ReportStatusResponse>(`/reports/${taskId}`);
  return data;
}
