import { apiClient } from "./client";
import type { QaAskRequest, QaAskResponse } from "../types/qa";

export async function askQuestion(payload: QaAskRequest): Promise<QaAskResponse> {
  // 智能问答可能需要检索向量库和调用大模型，因此单独把超时时间放宽到 60 秒。
  const { data } = await apiClient.post<QaAskResponse>("/qa/ask", payload, {
    timeout: 60000,
  });
  return data;
}
