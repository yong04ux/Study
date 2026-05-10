import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { getDashboardOverview } from "../api/dashboard";
import { UsageGuide } from "../components/usage-guide";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardBody, CardHeader } from "../components/ui/card";
import { EmptyState } from "../components/ui/empty-state";
import { ErrorMessage } from "../components/ui/error-message";
import { Loading, LoadingBlock } from "../components/ui/loading";
import { useAuth } from "../contexts/auth-context";
import type { DashboardActivity, DashboardOverview } from "../types/dashboard";
import type { FavoriteSchool } from "../types/favorite";

function formatDate(value: string) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function ActivitySection({
  title,
  eyebrow,
  items,
  emptyText,
  footer,
}: {
  title: string;
  eyebrow: string;
  items: DashboardActivity[];
  emptyText: string;
  footer?: ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="flex items-center justify-between gap-4">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">{title}</h2>
        </div>
        <Badge tone="neutral">{items.length}</Badge>
      </CardHeader>
      <CardBody className="space-y-4">
        {items.length === 0 ? (
          <EmptyState description={emptyText} />
        ) : (
          items.map((item) => (
            <div
              key={`${item.activity_type}-${item.id}`}
              className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4"
            >
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm font-semibold text-slate-900">{item.summary}</p>
                <p className="text-xs text-slate-500">{formatDate(item.created_at)}</p>
              </div>
              {item.payload.question ? (
                <p className="mt-2 line-clamp-2 text-sm leading-7 text-slate-600">
                  {String(item.payload.question)}
                </p>
              ) : null}
            </div>
          ))
        )}
        {footer ? <div>{footer}</div> : null}
      </CardBody>
    </Card>
  );
}

function FavoriteSection({ favorites }: { favorites: FavoriteSchool[] }) {
  return (
    <Card>
      <CardHeader className="flex items-center justify-between gap-4">
        <div>
          <p className="eyebrow">Favorites</p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
            {"\u6536\u85cf\u5b66\u6821"}
          </h2>
        </div>
        <Badge tone="neutral">{favorites.length}</Badge>
      </CardHeader>
      <CardBody className="space-y-4">
        {favorites.length === 0 ? (
          <EmptyState
            description={
              "\u4f60\u8fd8\u6ca1\u6709\u6536\u85cf\u4efb\u4f55\u5b66\u6821\u3002\u53ef\u4ee5\u5728\u9662\u6821\u8be6\u60c5\u9875\u70b9\u51fb\u201c\u6536\u85cf\u5b66\u6821\u201d\u3002"
            }
          />
        ) : (
          favorites.map((favorite) => (
            <div
              key={favorite.id}
              className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4"
            >
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-base font-semibold text-slate-950">{favorite.school_name}</p>
                  <p className="mt-2 text-sm leading-7 text-slate-600">
                    {[favorite.province, favorite.city].filter(Boolean).join(" / ") ||
                      "\u6682\u65e0\u5730\u533a\u4fe1\u606f"}
                  </p>
                </div>
                <Link to="/schools">
                  <Button variant="secondary">{"\u53bb\u9662\u6821\u9875\u67e5\u770b"}</Button>
                </Link>
              </div>
            </div>
          ))
        )}
      </CardBody>
    </Card>
  );
}

function PlanSection({ plans }: { plans: DashboardOverview["recent_plans"] }) {
  return (
    <Card>
      <CardHeader className="flex items-center justify-between gap-4">
        <div>
          <p className="eyebrow">Plans</p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
            {"\u5fd7\u613f\u65b9\u6848\u5165\u53e3"}
          </h2>
        </div>
        <Link to="/plans">
          <Button variant="secondary">{"\u8fdb\u5165\u65b9\u6848\u9875"}</Button>
        </Link>
      </CardHeader>
      <CardBody className="space-y-4">
        {plans.length === 0 ? (
          <EmptyState
            description={
              "\u4f60\u8fd8\u6ca1\u6709\u4fdd\u5b58\u4efb\u4f55\u5fd7\u613f\u65b9\u6848\u3002\u5148\u53bb\u63a8\u8350\u9875\u751f\u6210\u7ed3\u679c\uff0c\u518d\u4fdd\u5b58\u4e3a\u65b9\u6848\u3002"
            }
          />
        ) : (
          plans.map((plan) => (
            <div
              key={plan.id}
              className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4"
            >
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-base font-semibold text-slate-950">{plan.name}</p>
                  <p className="mt-2 text-sm leading-7 text-slate-600">
                    {plan.province} / {plan.subject_type} / {plan.score}
                    {"\u5206 / \u4f4d\u6b21 "}
                    {plan.rank}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge tone="brand">
                    {plan.items_count}
                    {" \u9879"}
                  </Badge>
                  <Link to={`/plans/${plan.id}`}>
                    <Button variant="secondary">{"\u67e5\u770b\u8be6\u60c5"}</Button>
                  </Link>
                </div>
              </div>
            </div>
          ))
        )}
      </CardBody>
    </Card>
  );
}

export function DashboardPage() {
  const { isAuthenticated, loadingUser } = useAuth();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    const loadOverview = async () => {
      try {
        setLoading(true);
        setError(null);
        setOverview(await getDashboardOverview());
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Failed to load dashboard. Please try again later.",
        );
      } finally {
        setLoading(false);
      }
    };

    void loadOverview();
  }, [isAuthenticated]);

  if (!loadingUser && !isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: "/dashboard" }} />;
  }

  return (
    <section className="space-y-6">
      <Card>
        <CardBody className="space-y-4">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
              {"\u6211\u7684\u5de5\u4f5c\u53f0"}
            </h1>
            <p className="mt-4 text-sm leading-7 text-slate-600">
              {
                "\u767b\u5f55\u540e\u53ef\u4ee5\u96c6\u4e2d\u56de\u770b\u6700\u8fd1\u63a8\u8350\u3001\u9662\u6821\u6d4f\u89c8\u3001\u667a\u80fd\u95ee\u7b54\u3001\u6536\u85cf\u5b66\u6821\u3001\u62a5\u544a\u4efb\u52a1\u548c\u5fd7\u613f\u65b9\u6848\u3002"
              }
            </p>
          </div>
        </CardBody>
      </Card>

      <UsageGuide
        badge="Workflow"
        title="登录后怎么使用"
        description="工作台负责汇总你登录后的关键动作。下面这几步完成后，推荐、院校浏览、收藏、方案和报告任务都会在这里出现。"
        steps={[
          "先去“志愿推荐”生成一组新的推荐结果。",
          "去“院校查询”打开目标学校详情，并收藏想重点跟进的学校。",
          "把推荐结果保存成方案，后续在“我的方案”里统一管理。",
          "去“报告查询”提交异步报告任务，等待状态从 submitted 或 processing 变成 completed。",
          "完成以上动作后刷新当前页面，检查最近推荐、收藏学校、报告任务和方案入口是否都已更新。",
        ]}
      />

      {error ? <ErrorMessage>{error}</ErrorMessage> : null}

      {loading ? (
        <div className="space-y-4">
          <Loading label={"\u6b63\u5728\u52a0\u8f7d\u5de5\u4f5c\u53f0..."} />
          <div className="grid gap-4 xl:grid-cols-2">
            <LoadingBlock className="h-64" />
            <LoadingBlock className="h-64" />
            <LoadingBlock className="h-64" />
            <LoadingBlock className="h-64" />
          </div>
        </div>
      ) : overview ? (
        <div className="grid gap-6 xl:grid-cols-2">
          <ActivitySection
            eyebrow="Recommendations"
            title={"\u6700\u8fd1\u63a8\u8350"}
            items={overview.recent_recommendations}
            emptyText={"\u4f60\u6700\u8fd1\u8fd8\u6ca1\u6709\u751f\u6210\u63a8\u8350\u7ed3\u679c\u3002"}
          />
          <ActivitySection
            eyebrow="Schools"
            title={"\u6700\u8fd1\u67e5\u770b\u9662\u6821"}
            items={overview.recent_school_views}
            emptyText={"\u4f60\u6700\u8fd1\u8fd8\u6ca1\u6709\u67e5\u770b\u9662\u6821\u8be6\u60c5\u3002"}
          />
          <ActivitySection
            eyebrow="Q&A"
            title={"\u6700\u8fd1\u95ee\u7b54"}
            items={overview.recent_questions}
            emptyText={"\u4f60\u6700\u8fd1\u8fd8\u6ca1\u6709\u8fdb\u884c\u667a\u80fd\u95ee\u7b54\u3002"}
          />
          <ActivitySection
            eyebrow="Reports"
            title={"\u62a5\u544a\u4efb\u52a1"}
            items={overview.report_tasks}
            emptyText={"\u4f60\u6700\u8fd1\u8fd8\u6ca1\u6709\u63d0\u4ea4\u62a5\u544a\u4efb\u52a1\u3002"}
          />
          <FavoriteSection favorites={overview.favorite_schools} />
          <PlanSection plans={overview.recent_plans} />
        </div>
      ) : (
        <EmptyState
          description={
            "\u6682\u65f6\u65e0\u6cd5\u83b7\u53d6\u5de5\u4f5c\u53f0\u6570\u636e\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5\u3002"
          }
        />
      )}
    </section>
  );
}
