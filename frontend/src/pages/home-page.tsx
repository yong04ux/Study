import { Link } from "react-router-dom";
import { UsageGuide } from "../components/usage-guide";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardBody } from "../components/ui/card";

/* 首页功能卡片配置：用于集中维护模块入口，不把文案散落在 JSX 中。 */
const featureCards = [
  {
    title: "\u6210\u7ee9\u5206\u6790",
    description:
      "\u57fa\u4e8e\u5206\u6570\u3001\u4f4d\u6b21\u548c\u79d1\u7c7b\u5feb\u901f\u5f62\u6210\u7b56\u7565\u5224\u65ad\uff0c\u9002\u5408\u5c55\u793a\u6570\u636e\u5efa\u6a21\u4e0e\u7528\u6237\u51b3\u7b56\u8f85\u52a9\u3002",
    to: "/recommendation",
    tag: "Analysis",
  },
  {
    title: "\u9662\u6821\u67e5\u8be2",
    description:
      "\u6309\u5730\u533a\u3001\u5c42\u6b21\u3001 985/211 \u6807\u7b7e\u68c0\u7d22\u9662\u6821\uff0c\u67e5\u770b\u57fa\u672c\u4fe1\u606f\u4e0e\u5386\u5e74\u5206\u6570\u7ebf\u3002",
    to: "/schools",
    tag: "Search",
  },
  {
    title: "\u5fd7\u613f\u63a8\u8350",
    description:
      "\u751f\u6210\u51b2\u3001\u7a33\u3001\u4fdd\u63a8\u8350\u7ed3\u679c\uff0c\u7528\u66f4\u6e05\u6670\u7684\u5361\u7247\u5c55\u793a\u53ef\u89c6\u5316\u8f93\u51fa\u4e0e\u7efc\u5408\u5efa\u8bae\u3002",
    to: "/recommendation",
    tag: "Recommend",
  },
  {
    title: "\u667a\u80fd\u95ee\u7b54",
    description:
      "\u57fa\u4e8e Agent + RAG \u7684\u8f7b\u91cf\u804a\u5929\u4ea4\u4e92\uff0c\u9002\u5408\u5c55\u793a\u77e5\u8bc6\u68c0\u7d22\u3001\u95ee\u7b54\u4e0e\u5f15\u7528\u6765\u6e90\u900f\u660e\u5ea6\u3002",
    to: "/qa",
    tag: "RAG",
  },
];

const highlightItems = [
  { value: "FastAPI", label: "Backend API" },
  { value: "LangGraph", label: "Agent Workflow" },
  { value: "RAG", label: "Knowledge QA" },
  { value: "Redis + Kafka", label: "Async Pipeline" },
];

export function HomePage() {
  /* 首页只负责展示项目能力和入口，不发起 API 请求。 */
  return (
    <section className="space-y-6">
      <section className="overflow-hidden rounded-2xl border border-slate-200/80 bg-[linear-gradient(135deg,rgba(255,255,255,0.96)_0%,rgba(240,249,255,0.96)_52%,rgba(236,253,245,0.96)_100%)] shadow-[0_24px_90px_rgba(15,23,42,0.10)]">
        <div className="grid gap-8 px-6 py-8 sm:px-8 sm:py-10 lg:grid-cols-[1.25fr_0.75fr] lg:items-end lg:px-10">
          <div>
            <Badge tone="brand">GaokaoPilot Demo</Badge>
            <h1 className="mt-5 max-w-4xl text-4xl font-semibold text-slate-950 sm:text-5xl lg:text-6xl">
              GaokaoPilot
            </h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-slate-600">
              {"\u9ad8\u8003\u5b66\u4e60\u4e0e\u5fd7\u613f\u586b\u62a5\u8f85\u52a9\u7cfb\u7edf\uff0c\u57fa\u4e8e Agent + RAG\uff0c\u805a\u7126\u6210\u7ee9\u5206\u6790\u3001\u9662\u6821\u67e5\u8be2\u3001\u5fd7\u613f\u63a8\u8350\u548c\u667a\u80fd\u95ee\u7b54\u3002"}
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/recommendation">
                <Button className="min-w-40">{"\u4f53\u9a8c\u5fd7\u613f\u63a8\u8350"}</Button>
              </Link>
              <Link to="/schools">
                <Button variant="secondary" className="min-w-40">
                  {"\u8fdb\u5165\u9662\u6821\u67e5\u8be2"}
                </Button>
              </Link>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
            {highlightItems.map((item) => (
              <Card key={item.label} className="border-white/80 bg-[rgba(255,255,255,0.82)]">
                <CardBody className="flex items-end justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                      {item.label}
                    </p>
                    <p className="mt-2 text-xl font-semibold text-slate-900">{item.value}</p>
                  </div>
                  <span className="h-10 w-10 rounded-lg bg-[linear-gradient(135deg,rgba(14,165,233,0.12),rgba(16,185,129,0.12))]" />
                </CardBody>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {featureCards.map((card) => (
          <Link key={card.title} to={card.to} className="block">
            <Card className="h-full transition duration-200 hover:-translate-y-1 hover:shadow-[0_26px_70px_rgba(14,165,233,0.12)]">
              <CardBody className="flex h-full flex-col">
                <Badge tone="neutral" className="w-fit">
                  {card.tag}
                </Badge>
                <h2 className="mt-4 text-xl font-semibold text-slate-900">{card.title}</h2>
                <p className="mt-3 flex-1 text-sm leading-7 text-slate-600">
                  {card.description}
                </p>
                <span className="mt-5 text-sm font-semibold text-sky-700">
                  {"\u8fdb\u5165\u6a21\u5757"}
                </span>
              </CardBody>
            </Card>
          </Link>
        ))}
      </section>

      <UsageGuide
        badge="Quick Start"
        title="首次体验建议顺序"
        description="如果你想最快跑通完整流程，可以按这个顺序操作。登录后，推荐结果、收藏学校、方案和报告任务都会逐步汇总到工作台。"
        steps={[
          "先注册或直接登录测试账号，进入“我的工作台”确认登录态已经生效。",
          "去“志愿推荐”输入分数、位次和偏好，生成一组冲稳保结果。",
          "在“院校查询”里查看目标学校详情，并收藏你想持续跟进的院校。",
          "回到“志愿推荐”把结果保存为方案，随后在“我的方案”里继续查看和复制。",
          "最后在“报告查询”提交异步报告任务，再回工作台检查最近活动是否已经串起来。",
        ]}
      />
    </section>
  );
}
