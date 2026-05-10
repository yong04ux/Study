export interface HealthResponse {
  // 后端健康状态，例如 ok。
  status: string;
  // 服务名，用于确认当前连接的是 gaokao-pilot 后端。
  service: string;
}
