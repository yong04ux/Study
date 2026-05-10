export interface ApiErrorPayload {
  // FastAPI 常见错误响应字段，Axios 拦截器会优先展示它。
  detail?: string;
}

// 通用 JSON 对象类型，用于暂时无法确定具体结构的响应数据。
export type JsonObject = Record<string, unknown>;
