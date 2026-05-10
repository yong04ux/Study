import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { deletePlan, duplicatePlan, listPlans } from "../api/plans";
import { UsageGuide } from "../components/usage-guide";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardBody, CardHeader } from "../components/ui/card";
import { EmptyState } from "../components/ui/empty-state";
import { ErrorMessage } from "../components/ui/error-message";
import { Loading, LoadingBlock } from "../components/ui/loading";
import { useAuth } from "../contexts/auth-context";
import type { PlanSummary } from "../types/plan";

function formatDate(value: string) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

export function PlansPage() {
  const navigate = useNavigate();
  const { isAuthenticated, loadingUser } = useAuth();
  const [plans, setPlans] = useState<PlanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingActionId, setPendingActionId] = useState<number | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    const loadPlans = async () => {
      try {
        setLoading(true);
        setError(null);
        setPlans(await listPlans());
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "方案列表加载失败，请稍后重试。");
      } finally {
        setLoading(false);
      }
    };

    void loadPlans();
  }, [isAuthenticated]);

  if (!loadingUser && !isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: "/plans" }} />;
  }

  const handleDelete = async (planId: number) => {
    try {
      setPendingActionId(planId);
      setError(null);
      await deletePlan(planId);
      setPlans((current) => current.filter((plan) => plan.id !== planId));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "删除方案失败，请稍后重试。");
    } finally {
      setPendingActionId(null);
    }
  };

  const handleDuplicate = async (planId: number) => {
    try {
      setPendingActionId(planId);
      setError(null);
      const duplicated = await duplicatePlan(planId);
      navigate(`/plans/${duplicated.id}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "复制方案失败，请稍后重试。");
    } finally {
      setPendingActionId(null);
    }
  };

  return (
    <section className="space-y-6">
      <UsageGuide
        badge="Tutorial"
        title="方案页使用教程"
        description="方案页用于承接你在推荐页保存下来的结果。建议把不同分数段、不同偏好下的推荐结果分别保存成方案，便于横向比较。"
        steps={[
          "先在“志愿推荐”生成结果，并至少保存一份方案。",
          "进入当前页面后查看方案数量、创建时间和每份方案的条目数。",
          "需要做备选时可以直接复制方案，再分别调整不同填报思路。",
          "不再使用的草稿方案可以删除，保持工作台和方案列表更清爽。",
        ]}
      />

      <Card>
        <CardBody className="space-y-4">
          <div>
            <p className="eyebrow">Plans</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
              志愿方案管理
            </h1>
            <p className="mt-4 text-sm leading-7 text-slate-600">
              查看、复制和删除你保存下来的志愿方案，后续可以继续扩展排序、对比与导出能力。
            </p>
          </div>
        </CardBody>
      </Card>

      {error ? <ErrorMessage>{error}</ErrorMessage> : null}

      <Card>
        <CardHeader className="flex items-center justify-between">
          <div>
            <p className="eyebrow">Plans</p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
              我的方案
            </h2>
          </div>
          <Badge tone="neutral">{plans.length}</Badge>
        </CardHeader>
        <CardBody className="space-y-4">
          {loading ? (
            <div className="space-y-4">
              <Loading label="正在加载方案..." />
              <LoadingBlock className="h-28" />
              <LoadingBlock className="h-28" />
            </div>
          ) : plans.length === 0 ? (
            <EmptyState description="你还没有保存任何志愿方案。先去推荐页生成结果并保存为方案。" />
          ) : (
            <div className="space-y-4">
              {plans.map((plan) => {
                const pending = pendingActionId === plan.id;
                return (
                  <Card key={plan.id} className="border-slate-200/80 shadow-none">
                    <CardBody className="space-y-5">
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                        <div>
                          <h3 className="text-xl font-semibold text-slate-950">{plan.name}</h3>
                          <p className="mt-3 text-sm leading-7 text-slate-600">
                            省份：{plan.province} / 科类：{plan.subject_type}
                          </p>
                          <p className="text-sm leading-7 text-slate-600">
                            分数：{plan.score} / 位次：{plan.rank}
                          </p>
                          <p className="text-sm leading-7 text-slate-600">
                            创建时间：{formatDate(plan.created_at)}
                          </p>
                        </div>

                        <div className="flex flex-wrap gap-2">
                          <Badge tone="brand">方案条目：{plan.items_count}</Badge>
                          <Badge tone="neutral">{plan.status}</Badge>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-3">
                        <Link to={`/plans/${plan.id}`}>
                          <Button variant="secondary">查看详情</Button>
                        </Link>
                        <Button
                          variant="secondary"
                          disabled={pending}
                          onClick={() => void handleDuplicate(plan.id)}
                        >
                          {pending ? "复制中..." : "复制"}
                        </Button>
                        <Button disabled={pending} onClick={() => void handleDelete(plan.id)}>
                          {pending ? "删除中..." : "删除"}
                        </Button>
                      </div>
                    </CardBody>
                  </Card>
                );
              })}
            </div>
          )}
        </CardBody>
      </Card>
    </section>
  );
}
