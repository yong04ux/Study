import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import { getReportStatus, submitReport } from "../api/report";
import { UsageGuide } from "../components/usage-guide";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardBody, CardHeader } from "../components/ui/card";
import { EmptyState } from "../components/ui/empty-state";
import { ErrorMessage } from "../components/ui/error-message";
import { Input } from "../components/ui/input";
import { Loading, LoadingBlock } from "../components/ui/loading";
import { Select } from "../components/ui/select";
import { Textarea } from "../components/ui/textarea";
import { cx } from "../components/ui/cx";
import { useAuth } from "../contexts/auth-context";
import type { ReportStatusResponse, ReportSubmitRequest } from "../types/report";
import type {
  RecommendationChoiceGroup,
  RecommendationChoiceItem,
  RecommendationResponse,
} from "../types/recommendation";

/* 异步报告页：提交 Kafka 报告任务，并根据 task_id 查询 Redis 中的任务状态和结果。 */

const subjectOptions = ["物理类", "历史类", "理科", "文科"];

const copy = {
  eyebrow: "Reports",
  title: "异步报告",
  intro:
    "提交任务后，后端会把请求写入 Kafka，再由 Consumer 生成完整志愿推荐报告。你可以通过 task_id 手动刷新查询进度。",
  userId: "用户 ID",
  province: "省份",
  subjectType: "科类",
  score: "分数",
  rank: "位次",
  preferredProvinces: "偏好地区",
  preferredMajors: "偏好专业",
  submitTask: "提交报告任务",
  submitting: "提交中...",
  queryTitle: "查询报告",
  queryHint: "输入 task_id 后可以随时查询或手动刷新报告状态。",
  queryTask: "查询任务",
  queryLoading: "查询中...",
  refresh: "手动刷新",
  taskId: "Task ID",
  latestTask: "最近生成的 Task ID",
  status: "当前状态",
  scoreAnalysis: "成绩分析",
  rush: "冲刺院校",
  stable: "稳妥院校",
  safe: "保底院校",
  studyPlan: "学习规划",
  finalAnswer: "综合建议",
  noData: "暂无数据",
  noResult: "提交任务后，这里会展示任务状态和完整报告结果。",
  noBucketResult: "当前分组暂无推荐院校。",
  noReason: "暂未提供推荐理由。",
  noSchoolName: "待补充院校名称",
  noMajorName: "待补充专业信息",
  noLocation: "暂未提供",
  location: "所在省市",
  minScore: "最低分",
  minRank: "最低位次",
  reason: "推荐理由",
  taskSubmitted: "报告任务已提交，可以点击“手动刷新”查看最新进度。",
  taskProcessing: "报告仍在生成中，请稍后刷新。",
  failedHint: "任务执行失败",
  parsedProvinceHint: "已识别地区",
  parsedMajorHint: "已识别专业",
  emptyParsed: "暂无",
  validationUserId: "请输入 user_id。",
  validationProvince: "请输入省份。",
  validationScore: "分数需在 0 到 750 之间。",
  validationRank: "位次需为大于 0 的整数。",
  validationTaskId: "请输入 task_id。",
  userIdPlaceholder: "u001",
  provincePlaceholder: "如：广东",
  scorePlaceholder: "如：625",
  rankPlaceholder: "如：12000",
  preferredProvincePlaceholder: "支持逗号分隔，如：广东，北京，上海",
  preferredMajorPlaceholder: "支持逗号分隔，如：计算机科学与技术，软件工程",
};

const initialForm = {
  /* 提交表单先保存字符串，提交前统一校验并转换成后端需要的类型。 */
  userId: "",
  province: "",
  subjectType: subjectOptions[0],
  score: "",
  rank: "",
  preferredProvinces: "",
  preferredMajors: "",
};

type SubmitFormState = typeof initialForm;
type SubmitFormErrors = Partial<Record<keyof SubmitFormState, string>>;

const bucketStyles: Record<
  keyof RecommendationChoiceGroup,
  { title: string; tone: string; badgeTone: "danger" | "warning" | "success" }
> = {
  rush: {
    title: copy.rush,
    tone: "border-rose-200/80 bg-rose-50/70",
    badgeTone: "danger",
  },
  stable: {
    title: copy.stable,
    tone: "border-amber-200/80 bg-amber-50/70",
    badgeTone: "warning",
  },
  safe: {
    title: copy.safe,
    tone: "border-emerald-200/80 bg-emerald-50/70",
    badgeTone: "success",
  },
};

function parseCommaSeparatedInput(value: string) {
  /* 报告页偏好输入支持逗号、中文逗号和换行分隔。 */
  return value
    .split(/[,\n，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function validateForm(form: SubmitFormState): SubmitFormErrors {
  /* 只校验必填项和数字范围，避免明显错误请求打到后端。 */
  const errors: SubmitFormErrors = {};
  const score = Number(form.score);
  const rank = Number(form.rank);

  if (!form.userId.trim()) {
    errors.userId = copy.validationUserId;
  }
  if (!form.province.trim()) {
    errors.province = copy.validationProvince;
  }
  if (!form.score.trim() || !Number.isFinite(score) || score < 0 || score > 750) {
    errors.score = copy.validationScore;
  }
  if (!form.rank.trim() || !Number.isInteger(rank) || rank < 1) {
    errors.rank = copy.validationRank;
  }

  return errors;
}

function getStatusTone(status: string) {
  /* 不同任务状态映射到不同徽标颜色。 */
  if (status === "completed") {
    return "success";
  }
  if (status === "failed") {
    return "danger";
  }
  if (status === "processing") {
    return "warning";
  }
  return "neutral";
}

function getStatusLabel(status: string) {
  const labels: Record<string, string> = {
    submitted: "已提交",
    processing: "生成中",
    completed: "已完成",
    failed: "失败",
  };
  return labels[status] ?? status;
}

function getSchoolTags(item: RecommendationChoiceItem) {
  const tags = new Set<string>();
  if (item.is_985) {
    tags.add("985");
  }
  if (item.is_211) {
    tags.add("211");
  }
  if (item.is_double_first_class) {
    tags.add("双一流");
  }
  return [...tags];
}

function getSchoolName(item: RecommendationChoiceItem) {
  return item.school_name || item.name || copy.noSchoolName;
}

function getLocation(item: RecommendationChoiceItem) {
  return [item.province, item.city].filter(Boolean).join(" / ") || copy.noLocation;
}

function normalizeReportResult(result: ReportStatusResponse["result"]): RecommendationResponse | null {
  /* Redis 中的 result 可能是松散对象，这里整理成推荐结果页面可直接渲染的结构。 */
  if (!result || typeof result !== "object") {
    return null;
  }

  const payload = result as Record<string, unknown>;
  const recommendedChoices =
    payload.recommended_choices && typeof payload.recommended_choices === "object"
      ? (payload.recommended_choices as Partial<RecommendationChoiceGroup>)
      : undefined;

  return {
    score_analysis: {
      level:
        payload.score_analysis &&
        typeof payload.score_analysis === "object" &&
        typeof (payload.score_analysis as Record<string, unknown>).level === "string"
          ? ((payload.score_analysis as Record<string, unknown>).level as string)
          : "",
      summary:
        payload.score_analysis &&
        typeof payload.score_analysis === "object" &&
        typeof (payload.score_analysis as Record<string, unknown>).summary === "string"
          ? ((payload.score_analysis as Record<string, unknown>).summary as string)
          : "",
      suggestion:
        payload.score_analysis &&
        typeof payload.score_analysis === "object" &&
        typeof (payload.score_analysis as Record<string, unknown>).suggestion === "string"
          ? ((payload.score_analysis as Record<string, unknown>).suggestion as string)
          : "",
    },
    recommended_choices: {
      rush:
        recommendedChoices?.rush ??
        ((payload.rush_schools as RecommendationChoiceItem[] | undefined) ?? []),
      stable:
        recommendedChoices?.stable ??
        ((payload.stable_schools as RecommendationChoiceItem[] | undefined) ?? []),
      safe:
        recommendedChoices?.safe ??
        ((payload.safe_schools as RecommendationChoiceItem[] | undefined) ?? []),
    },
    study_plan:
      (payload.study_plan as RecommendationResponse["study_plan"] | undefined) ?? copy.noData,
    final_answer: typeof payload.final_answer === "string" ? payload.final_answer : copy.noData,
  };
}

function formatValue(value: unknown) {
  /* study_plan 可能是字符串、数组或对象，统一转换成展示文本。 */
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.join("、");
  }
  if (value && typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }
  return copy.noData;
}

function SectionHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">{title}</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">{description}</p>
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

function InfoTile({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <div className="mt-3 text-sm leading-7 text-slate-700">{value}</div>
    </div>
  );
}

function PreferenceHint({ label, items }: { label: string; items: string[] }) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50 px-4 py-3 text-xs leading-6 text-slate-500">
      {label}：
      <span className="ml-2 font-semibold text-slate-700">{items.length}</span>
      <span className="ml-2 text-slate-700">{items.join("、") || copy.emptyParsed}</span>
    </div>
  );
}

function RecommendationCard({ item }: { item: RecommendationChoiceItem }) {
  /* 报告中的单个推荐卡片，复用与推荐页相同的展示信息。 */
  const tags = getSchoolTags(item);

  return (
    <Card className="overflow-hidden border-white/80 bg-white/95 shadow-none">
      <CardBody className="space-y-4 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-950">{getSchoolName(item)}</h3>
            <p className="mt-2 text-sm font-semibold text-sky-700">
              {item.major_name || copy.noMajorName}
            </p>
            <p className="mt-2 text-sm text-slate-600">
              {copy.location}：{getLocation(item)}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <Badge key={tag} tone="neutral">
                {tag}
              </Badge>
            ))}
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <InfoTile label={copy.minScore} value={item.min_score} />
          <InfoTile label={copy.minRank} value={item.min_rank ?? copy.noData} />
        </div>

        <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            {copy.reason}
          </p>
          <p className="mt-3 text-sm leading-7 text-slate-700">
            {item.reason?.trim() ? item.reason : copy.noReason}
          </p>
        </div>
      </CardBody>
    </Card>
  );
}

function RecommendationBucket({
  bucket,
  items,
}: {
  bucket: keyof RecommendationChoiceGroup;
  items: RecommendationChoiceItem[];
}) {
  const config = bucketStyles[bucket];

  return (
    <section className={cx("rounded-[1.5rem] border p-5", config.tone)}>
      <div className="flex items-center justify-between gap-3">
        <Badge tone={config.badgeTone}>{config.title}</Badge>
        <span className="text-sm text-slate-600">{items.length}</span>
      </div>
      <div className="mt-4 space-y-3">
        {items.length > 0 ? (
          items.map((item, index) => (
            <RecommendationCard
              key={`${bucket}-${getSchoolName(item)}-${item.major_name}-${index}`}
              item={item}
            />
          ))
        ) : (
          <EmptyState description={copy.noBucketResult} className="bg-white/70 py-8" />
        )}
      </div>
    </section>
  );
}

function StudyPlanSection({ studyPlan }: { studyPlan: RecommendationResponse["study_plan"] }) {
  /* 学习规划既可能是纯文本，也可能是结构化对象，因此分两种方式渲染。 */
  return (
    <Card className="shadow-none">
      <CardHeader>
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
          {copy.studyPlan}
        </p>
      </CardHeader>
      <CardBody>
        {typeof studyPlan === "string" ? (
          <p className="text-sm leading-8 text-slate-700">{studyPlan || copy.noData}</p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {Object.entries(studyPlan).map(([key, value]) => (
              <InfoTile
                key={key}
                label={key}
                value={<p className="whitespace-pre-wrap">{formatValue(value)}</p>}
              />
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}

export function ReportsPage() {
  const { currentUser, isAuthenticated } = useAuth();
  /* form/errors 管理提交表单；taskIdInput/latestTaskId 管理查询入口。 */
  const [form, setForm] = useState<SubmitFormState>(initialForm);
  const [errors, setErrors] = useState<SubmitFormErrors>({});
  const [taskIdInput, setTaskIdInput] = useState("");
  const [latestTaskId, setLatestTaskId] = useState<string | null>(null);
  const [statusData, setStatusData] = useState<ReportStatusResponse | null>(null);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [queryLoading, setQueryLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const provincePreferences = useMemo(
    /* 偏好解析结果会展示在表单下方，也会作为数组提交给后端。 */
    () => parseCommaSeparatedInput(form.preferredProvinces),
    [form.preferredProvinces],
  );
  const majorPreferences = useMemo(
    () => parseCommaSeparatedInput(form.preferredMajors),
    [form.preferredMajors],
  );
  const normalizedResult = useMemo(
    /* 查询到 completed 结果后，先 normalize 再交给页面渲染。 */
    () => normalizeReportResult(statusData?.result ?? null),
    [statusData],
  );

  useEffect(() => {
    if (!isAuthenticated || !currentUser || form.userId.trim()) {
      return;
    }

    setForm((current) => ({ ...current, userId: currentUser.username }));
  }, [currentUser, form.userId, isAuthenticated]);

  const updateField = (field: keyof SubmitFormState, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  };

  const fetchStatus = async (taskId: string) => {
    /* 查询流程：根据 task_id 请求 /reports/{task_id}，更新状态和提示文案。 */
    try {
      setQueryLoading(true);
      setQueryError(null);
      const response = await getReportStatus(taskId.trim());
      setStatusData(response);

      if (response.status === "submitted" || response.status === "processing") {
        setNotice(copy.taskProcessing);
      } else {
        setNotice(null);
      }
    } catch (error) {
      setQueryError(error instanceof Error ? error.message : "查询报告状态失败。");
      setStatusData(null);
    } finally {
      setQueryLoading(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors = validateForm(form);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    const payload: ReportSubmitRequest = {
      /* 提交 Kafka 任务时，偏好字段必须是数组，分数和位次必须是 number。 */
      user_id: form.userId.trim(),
      province: form.province.trim(),
      subject_type: form.subjectType,
      score: Number(form.score),
      rank: Number(form.rank),
      preferred_provinces: provincePreferences,
      preferred_majors: majorPreferences,
    };

    try {
      setSubmitLoading(true);
      setSubmitError(null);
      const response = await submitReport(payload);
      setLatestTaskId(response.task_id);
      setTaskIdInput(response.task_id);
      setStatusData({
        task_id: response.task_id,
        status: response.status,
        result: null,
        error: null,
      });
      setNotice(copy.taskSubmitted);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "提交报告任务失败。");
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleQuery = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!taskIdInput.trim()) {
      setQueryError(copy.validationTaskId);
      return;
    }
    await fetchStatus(taskIdInput);
  };

  return (
    <section className="space-y-6">
      <UsageGuide
        badge="Tutorial"
        title="报告页使用教程"
        description="这个页面用于演示异步报告任务。登录后推荐直接用当前账号作为 user_id，这样提交后的任务会自动进入你的工作台活动流。"
        steps={[
          "填写分数、位次和偏好信息；如果已经登录，user_id 会默认带入当前用户名。",
          "点击“提交报告任务”后记住 task_id，页面右侧会保留最近一次任务编号。",
          "用“查询任务”或“手动刷新”轮询状态，直到任务从 submitted 或 processing 变成 completed。",
          "报告完成后回到工作台，检查最近活动和报告任务区是否已经同步更新。",
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
        <div className="space-y-6">
          <Card>
            <CardBody className="space-y-6 p-6">
              <SectionHeading
                eyebrow={copy.eyebrow}
                title={copy.title}
                description={copy.intro}
                action={<Badge tone="brand">Kafka + Redis</Badge>}
              />

              <form className="space-y-5" onSubmit={handleSubmit}>
                <div className="field-grid">
                  <Input
                    label={copy.userId}
                    value={form.userId}
                    onChange={(event) => updateField("userId", event.target.value)}
                    placeholder={copy.userIdPlaceholder}
                    error={errors.userId}
                  />
                  <Input
                    label={copy.province}
                    value={form.province}
                    onChange={(event) => updateField("province", event.target.value)}
                    placeholder={copy.provincePlaceholder}
                    error={errors.province}
                  />
                  <Select
                    label={copy.subjectType}
                    value={form.subjectType}
                    onChange={(event) => updateField("subjectType", event.target.value)}
                  >
                    {subjectOptions.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </Select>
                  <Input
                    label={copy.score}
                    value={form.score}
                    onChange={(event) => updateField("score", event.target.value)}
                    inputMode="numeric"
                    placeholder={copy.scorePlaceholder}
                    error={errors.score}
                  />
                  <Input
                    label={copy.rank}
                    value={form.rank}
                    onChange={(event) => updateField("rank", event.target.value)}
                    inputMode="numeric"
                    placeholder={copy.rankPlaceholder}
                    error={errors.rank}
                  />
                </div>

                <div className="space-y-4">
                  <Textarea
                    label={copy.preferredProvinces}
                    value={form.preferredProvinces}
                    onChange={(event) => updateField("preferredProvinces", event.target.value)}
                    rows={3}
                    placeholder={copy.preferredProvincePlaceholder}
                  />
                  <PreferenceHint
                    label={copy.parsedProvinceHint}
                    items={provincePreferences}
                  />
                </div>

                <div className="space-y-4">
                  <Textarea
                    label={copy.preferredMajors}
                    value={form.preferredMajors}
                    onChange={(event) => updateField("preferredMajors", event.target.value)}
                    rows={3}
                    placeholder={copy.preferredMajorPlaceholder}
                  />
                  <PreferenceHint label={copy.parsedMajorHint} items={majorPreferences} />
                </div>

                <Button type="submit" disabled={submitLoading} fullWidth>
                  {submitLoading ? copy.submitting : copy.submitTask}
                </Button>

                {submitError ? <ErrorMessage>{submitError}</ErrorMessage> : null}
              </form>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <p className="eyebrow">{copy.queryTitle}</p>
              <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
                {copy.queryTitle}
              </h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">{copy.queryHint}</p>
            </CardHeader>
            <CardBody className="space-y-4">
              <form className="flex flex-col gap-3 sm:flex-row" onSubmit={handleQuery}>
                <Input
                  value={taskIdInput}
                  onChange={(event) => setTaskIdInput(event.target.value)}
                  placeholder={copy.taskId}
                  className="sm:mt-0"
                />
                <Button type="submit" disabled={queryLoading} className="sm:min-w-28">
                  {queryLoading ? copy.queryLoading : copy.queryTask}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  disabled={queryLoading || !taskIdInput.trim()}
                  onClick={() => void fetchStatus(taskIdInput)}
                >
                  {copy.refresh}
                </Button>
              </form>

              {queryError ? <ErrorMessage>{queryError}</ErrorMessage> : null}
            </CardBody>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="xl:sticky xl:top-28">
            <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="eyebrow">Report Result</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                  {latestTaskId || statusData?.task_id || copy.taskId}
                </h2>
              </div>
              {statusData ? (
                <Badge tone={getStatusTone(statusData.status)}>
                  {copy.status}：{getStatusLabel(statusData.status)}
                </Badge>
              ) : null}
            </CardHeader>

            <CardBody className="space-y-6">
              {latestTaskId ? (
                <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm text-slate-700">
                  <p className="font-semibold text-slate-950">{copy.latestTask}</p>
                  <p className="mt-2 break-all">{latestTaskId}</p>
                </div>
              ) : null}

              {notice ? (
                <div className="rounded-2xl border border-sky-200 bg-sky-50 px-4 py-4 text-sm text-sky-700">
                  {notice}
                </div>
              ) : null}

              {queryLoading ? (
                <div className="space-y-4">
                  <Loading label={copy.queryLoading} />
                  <LoadingBlock />
                  <LoadingBlock />
                </div>
              ) : statusData?.status === "failed" ? (
                <ErrorMessage>
                  <p className="font-semibold">{copy.failedHint}</p>
                  <p className="mt-2">{statusData.error || copy.noData}</p>
                </ErrorMessage>
              ) : normalizedResult ? (
                <div className="space-y-6">
                  <Card className="shadow-none">
                    <CardHeader>
                      <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                        {copy.scoreAnalysis}
                      </p>
                    </CardHeader>
                    <CardBody>
                      <div className="grid gap-4 md:grid-cols-3">
                        <InfoTile
                          label="评估等级"
                          value={normalizedResult.score_analysis.level || copy.noData}
                        />
                        <InfoTile
                          label="分析摘要"
                          value={normalizedResult.score_analysis.summary || copy.noData}
                        />
                        <InfoTile
                          label="填报建议"
                          value={normalizedResult.score_analysis.suggestion || copy.noData}
                        />
                      </div>
                    </CardBody>
                  </Card>

                  <RecommendationBucket
                    bucket="rush"
                    items={normalizedResult.recommended_choices.rush}
                  />
                  <RecommendationBucket
                    bucket="stable"
                    items={normalizedResult.recommended_choices.stable}
                  />
                  <RecommendationBucket
                    bucket="safe"
                    items={normalizedResult.recommended_choices.safe}
                  />

                  <StudyPlanSection studyPlan={normalizedResult.study_plan} />

                  <Card className="shadow-none">
                    <CardHeader>
                      <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                        {copy.finalAnswer}
                      </p>
                    </CardHeader>
                    <CardBody>
                      <p className="text-sm leading-8 text-slate-700">
                        {normalizedResult.final_answer || copy.noData}
                      </p>
                    </CardBody>
                  </Card>
                </div>
              ) : (
                <EmptyState description={copy.noResult} />
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </section>
  );
}
