import { useEffect, useState } from "react";
import { fetchHealth } from "../api/health";
import { StatusCard } from "../components/status-card";
import type { HealthResponse } from "../types/health";

/* 健康检查页：用于验证前端 Axios 配置和后端 /api/v1/health 是否连通。 */
export function HealthPage() {
  /* health 保存成功响应；loading/error 分别控制加载骨架和错误提示。 */
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    /* active 防止组件卸载后异步请求回来继续 setState。 */
    let active = true;

    const loadHealth = async () => {
      /* 请求流程：进入 loading -> 调用健康检查接口 -> 写入数据或错误 -> 结束 loading。 */
      try {
        setLoading(true);
        setError(null);
        const data = await fetchHealth();

        if (active) {
          setHealth(data);
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Failed to load health status.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void loadHealth();

    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
      <div className="panel">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-brand-600">
          API Check
        </p>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">
          后端健康检查
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
          这里通过统一的 Axios 实例请求 FastAPI 的
          <code className="mx-1 rounded bg-slate-100 px-2 py-1 text-xs text-slate-700">
            /api/v1/health
          </code>
          接口，用来验证前后端联调链路是否正常。
        </p>

        <button
          type="button"
          onClick={() => window.location.reload()}
          className="mt-6 rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
        >
          重新请求
        </button>
      </div>

      <div className="panel">
        {loading ? (
          <div className="space-y-4">
            <div className="h-24 animate-pulse rounded-2xl bg-slate-100" />
            <div className="h-24 animate-pulse rounded-2xl bg-slate-100" />
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-5 text-rose-700">
            <p className="text-sm font-semibold uppercase tracking-[0.2em]">
              Request Error
            </p>
            <p className="mt-3 text-sm leading-6">{error}</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            <StatusCard
              title="Status"
              value={health?.status ?? "unknown"}
              tone={health?.status === "ok" ? "success" : "neutral"}
            />
            <StatusCard
              title="Service"
              value={health?.service ?? "unknown"}
              tone="neutral"
            />
          </div>
        )}
      </div>
    </section>
  );
}
