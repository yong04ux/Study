import { apiClient } from "./client";
import type {
  RecommendationChoiceGroup,
  RecommendationChoiceItem,
  RecommendationRequest,
  RecommendationResponse,
} from "../types/recommendation";

// 后端曾经有两种返回结构：新结构 recommended_choices，旧结构 rush_schools 等。
interface RecommendationApiResponse {
  score_analysis?: RecommendationResponse["score_analysis"];
  rush_schools?: RecommendationChoiceItem[];
  stable_schools?: RecommendationChoiceItem[];
  safe_schools?: RecommendationChoiceItem[];
  recommended_choices?: Partial<RecommendationChoiceGroup> | null;
  study_plan?: RecommendationResponse["study_plan"];
  final_answer?: string;
}

// 每个推荐分组都必须兜底为数组，避免页面读取 .length 或 map 时报错。
function normalizeChoiceItems(items: RecommendationChoiceItem[] | undefined) {
  return Array.isArray(items) ? items : [];
}

// 统一新旧响应结构，让页面只关心 rush / stable / safe。
function normalizeRecommendedChoices(
  payload: RecommendationApiResponse,
): RecommendationChoiceGroup {
  return {
    rush: normalizeChoiceItems(
      payload.recommended_choices?.rush ?? payload.rush_schools,
    ),
    stable: normalizeChoiceItems(
      payload.recommended_choices?.stable ?? payload.stable_schools,
    ),
    safe: normalizeChoiceItems(
      payload.recommended_choices?.safe ?? payload.safe_schools,
    ),
  };
}

export async function generateRecommendation(
  payload: RecommendationRequest,
): Promise<RecommendationResponse> {
  // 同步推荐请求：提交考生信息和偏好，后端调用 LangGraph 返回完整推荐结果。
  const response = await apiClient.post<RecommendationApiResponse>(
    "/recommendations/generate",
    payload,
  );

  if (import.meta.env.DEV) {
    console.log("[recommendation] response.data", response.data);
  }

  // 页面需要稳定结构，因此这里对缺失字段做默认值兜底。
  return {
    score_analysis: response.data.score_analysis ?? {
      level: "",
      summary: "",
      suggestion: "",
    },
    recommended_choices: normalizeRecommendedChoices(response.data),
    study_plan: response.data.study_plan ?? "",
    final_answer: response.data.final_answer ?? "",
  };
}
