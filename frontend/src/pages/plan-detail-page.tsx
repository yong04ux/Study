import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { getPlanDetail } from "../api/plans";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardBody, CardHeader } from "../components/ui/card";
import { EmptyState } from "../components/ui/empty-state";
import { ErrorMessage } from "../components/ui/error-message";
import { Loading, LoadingBlock } from "../components/ui/loading";
import { useAuth } from "../contexts/auth-context";
import type { PlanDetail, PlanGroupType, PlanItem } from "../types/plan";

const bucketMeta: Record<
  PlanGroupType,
  { title: string; tone: "danger" | "warning" | "success"; panel: string }
> = {
  rush: { title: "冲刺院校", tone: "danger", panel: "border-rose-200/80 bg-rose-50/60" },
  stable: { title: "稳妥院校", tone: "warning", panel: "border-amber-200/80 bg-amber-50/60" },
  safe: { title: "保底院校", tone: "success", panel: "border-emerald-200/80 bg-emerald-50/60" },
};

function formatDate(value: string) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function ItemCard({ item }: { item: PlanItem }) {
  return (
    <Card className="border-white/80 bg-white/95">
      <CardBody className="space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-950">{item.school_name}</h3>
            <p className="mt-2 text-sm font-semibold text-sky-700">{item.major_name || "未区分专业"}</p>
          </div>
          <Badge tone="neutral">{item.risk_level || "unknown"}</Badge>
        </div>
        <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            推荐理由
          </p>
          <p className="mt-3 text-sm leading-7 text-slate-700">
            {item.recommend_reason || "暂无推荐理由"}
          </p>
        </div>
      </CardBody>
    </Card>
  );
}

function BucketSection({ groupType, items }: { groupType: PlanGroupType; items: PlanItem[] }) {
  const meta = bucketMeta[groupType];

  return (
    <section className={`rounded-[1.75rem] border p-5 sm:p-6 ${meta.panel}`}>
      <div className="flex items-center justify-between gap-4">
        <Badge tone={meta.tone}>{meta.title}</Badge>
        <Badge tone="neutral">{items.length}</Badge>
      </div>
      <div className="mt-5 space-y-4">
        {items.length > 0 ? (
          items.map((item) => <ItemCard key={item.id} item={item} />)
        ) : (
          <EmptyState description="当前分组暂无条目。" className="bg-white/70" />
        )}
      </div>
    </section>
  );
}

export function PlanDetailPage() {
  const { planId } = useParams();
  const { isAuthenticated, loadingUser } = useAuth();
  const [plan, setPlan] = useState<PlanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated || !planId) {
      return;
    }

    const loadPlan = async () => {
      try {
        setLoading(true);
        setError(null);
        setPlan(await getPlanDetail(Number(planId)));
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "方案详情加载失败，请稍后重试。");
      } finally {
        setLoading(false);
      }
    };

    void loadPlan();
  }, [isAuthenticated, planId]);

  const groupedItems = useMemo(
    () =>
      plan?.grouped_items ?? {
        rush: [],
        stable: [],
        safe: [],
      },
    [plan],
  );

  if (!loadingUser && !isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: `/plans/${planId}` }} />;
  }

  return (
    <section className="space-y-6">
      <Card>
        <CardBody className="space-y-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="eyebrow">Plan Detail</p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
                {plan?.name || "志愿方案详情"}
              </h1>
              <p className="mt-4 text-sm leading-7 text-slate-600">
                查看方案基本信息，以及冲刺、稳妥、保底三类院校专业条目。
              </p>
            </div>
            <Link to="/plans">
              <Button variant="secondary">返回方案列表</Button>
            </Link>
          </div>
        </CardBody>
      </Card>

      {error ? <ErrorMessage>{error}</ErrorMessage> : null}

      {loading ? (
        <Card>
          <CardBody className="space-y-4">
            <Loading label="正在加载方案详情..." />
            <LoadingBlock />
            <LoadingBlock />
          </CardBody>
        </Card>
      ) : plan ? (
        <>
          <Card>
            <CardHeader>
              <p className="eyebrow">Plan Detail</p>
              <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
                方案基本信息
              </h2>
            </CardHeader>
            <CardBody>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm leading-7 text-slate-700">
                  省份：{plan.province}
                </div>
                <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm leading-7 text-slate-700">
                  科类：{plan.subject_type}
                </div>
                <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm leading-7 text-slate-700">
                  分数：{plan.score}
                </div>
                <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm leading-7 text-slate-700">
                  位次：{plan.rank}
                </div>
                <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm leading-7 text-slate-700">
                  状态：{plan.status}
                </div>
                <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm leading-7 text-slate-700">
                  创建时间：{formatDate(plan.created_at)}
                </div>
              </div>
            </CardBody>
          </Card>

          <BucketSection groupType="rush" items={groupedItems.rush} />
          <BucketSection groupType="stable" items={groupedItems.stable} />
          <BucketSection groupType="safe" items={groupedItems.safe} />
        </>
      ) : (
        <EmptyState description="未找到该方案。" />
      )}
    </section>
  );
}
