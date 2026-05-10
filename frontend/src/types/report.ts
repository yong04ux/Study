import type {
  RecommendationRequest,
  RecommendationResponse
} from "./recommendation";

export type ReportSubmitRequest = RecommendationRequest;
// 异步报告任务状态，对应 Redis 中保存的 status。
export type ReportTaskStatus = "submitted" | "processing" | "completed" | "failed";

export interface ReportSubmitResponse {
  // 提交任务后立即返回的任务 ID，后续查询都依赖它。
  task_id: string;
  status: ReportTaskStatus;
}

export interface ReportStatusResponse {
  // 当前任务状态和结果；任务失败时 error 会携带失败原因。
  task_id: string;
  status: ReportTaskStatus;
  result: RecommendationResponse | Record<string, unknown> | null;
  error?: string | null;
}
