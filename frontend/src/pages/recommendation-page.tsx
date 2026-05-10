import { FormEvent, ReactNode, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createPlan } from "../api/plans";
import { generateRecommendation } from "../api/recommendation";
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
import type { CreatePlanRequest } from "../types/plan";
import type {
  RecommendationChoiceGroup,
  RecommendationChoiceItem,
  RecommendationRequest,
  RecommendationResponse,
} from "../types/recommendation";
import { splitPreferenceInput } from "../utils/split-preference-input";

// 志愿推荐页：左侧收集考生分数、位次和偏好，右侧展示冲刺/稳妥/保底结果。

const subjectOptions = ["物理类", "历史类", "理科", "文科"];

const copy = {
  title: "志愿推荐",
  intro:
    "输入考生基础信息和偏好后，系统会根据分数、位次与偏好条件生成冲刺、稳妥、保底推荐，并附带成绩分析和学习建议。",
  province: "省份",
  subjectType: "科类",
  score: "分数",
  rank: "位次",
  preferredProvinces: "偏好地区",
  preferredMajors: "偏好专业",
  submit: "生成推荐",
  submitting: "生成中...",
  resultOverview: "推荐概览",
  scoreAnalysis: "成绩分析",
  studyPlan: "学习规划",
  finalAdvice: "综合建议",
  rush: "冲刺院校",
  stable: "稳妥院校",
  safe: "保底院校",
  noTag: "普通院校",
  noData: "暂无数据",
  noResult: "填写左侧表单并点击“生成推荐”后，这里会展示完整推荐结果。",
  noBucketResult: "当前分组暂无推荐结果，可以尝试调整偏好条件后重新生成。",
  noLocation: "暂未提供",
  validationProvince: "请输入省份。",
  validationSubjectType: "请选择科类。",
  validationScore: "分数需在 0 到 750 之间。",
  validationRank: "位次需为大于 0 的整数。",
  requestError: "推荐请求失败，请稍后重试。",
  provincePlaceholder: "如：广东",
  scorePlaceholder: "如：625",
  rankPlaceholder: "如：12000",
  preferredProvincePlaceholder:
    "支持逗号、顿号、分号、空格、换行分隔，如：广东 上海 北京",
  preferredMajorPlaceholder:
    "支持逗号、顿号、分号、空格、换行分隔，如：软件工程 人工智能",
  parsedProvincePrefix: "已识别 ",
  parsedProvinceMiddle: " 个地区：",
  parsedMajorMiddle: " 个专业：",
  emptyParsed: "暂无",
  totalPrefix: "共 ",
  totalSuffix: " 条推荐",
  analysisLevel: "评估等级",
  analysisSummary: "分析摘要",
  analysisSuggestion: "填报建议",
  minScore: "最低分",
  minRank: "最低位次",
  location: "所在省市",
  reason: "推荐理由",
  emptyStudyPlan: "当前结果暂无学习规划。",
  emptyFinalAnswer: "当前结果暂无综合建议。",
};

const initialFormState = {
  // 表单状态先用字符串保存，提交前再统一校验并转换成后端需要的 number/array。
  province: "",
  subjectType: subjectOptions[0],
  score: "",
  rank: "",
  preferredProvinces: "",
  preferredMajors: "",
};

type FormState = typeof initialFormState;
type FormErrors = Partial<Record<keyof FormState, string>>;

const bucketConfig: Record<
  keyof RecommendationChoiceGroup,
  {
    title: string;
    description: string;
    badgeTone: "danger" | "warning" | "success";
    panelTone: string;
  }
> = {
  rush: {
    title: copy.rush,
    description: "适合作为冲高志愿，录取挑战更大，但也带来更高的上升空间。",
    badgeTone: "danger",
    panelTone: "border-rose-200/80 bg-rose-50/70",
  },
  stable: {
    title: copy.stable,
    description: "与当前分数和位次更接近，通常是整套志愿方案的核心承接层。",
    badgeTone: "warning",
    panelTone: "border-amber-200/80 bg-amber-50/70",
  },
  safe: {
    title: copy.safe,
    description: "更强调录取稳定性，用来保证志愿结构具备安全边界。",
    badgeTone: "success",
    panelTone: "border-emerald-200/80 bg-emerald-50/70",
  },
};

function validateForm(form: FormState): FormErrors {
  // 前端只做基础输入校验，真正的推荐策略仍由后端 Agent 工作流处理。
  const errors: FormErrors = {};
  const score = Number(form.score);
  const rank = Number(form.rank);

  if (!form.province.trim()) {
    errors.province = copy.validationProvince;
  }
  if (!form.subjectType) {
    errors.subjectType = copy.validationSubjectType;
  }
  if (!form.score.trim() || !Number.isFinite(score) || score < 0 || score > 750) {
    errors.score = copy.validationScore;
  }
  if (!form.rank.trim() || !Number.isInteger(rank) || rank < 1) {
    errors.rank = copy.validationRank;
  }

  return errors;
}

function normalizeChoiceItems(items: RecommendationChoiceItem[] | undefined) {
  // 推荐分组必须兜底为数组，避免页面读取 length/map 时报错。
  return Array.isArray(items) ? items : [];
}

function normalizeChoiceGroup(
  group: Partial<RecommendationChoiceGroup> | RecommendationChoiceGroup | null | undefined,
): RecommendationChoiceGroup {
  // 后端缺少某个分组时，页面仍然显示 empty 状态而不是崩溃。
  return {
    rush: normalizeChoiceItems(group?.rush),
    stable: normalizeChoiceItems(group?.stable),
    safe: normalizeChoiceItems(group?.safe),
  };
}

function flattenPlanItems(group: RecommendationChoiceGroup) {
  const buckets: Array<keyof RecommendationChoiceGroup> = ["rush", "stable", "safe"];
  return buckets.flatMap((bucket) =>
    group[bucket].map((item, index) => ({
      school_id: item.school_id ?? null,
      major_id: item.major_id ?? null,
      school_name: getSchoolName(item),
      major_name: item.major_name ?? null,
      province: item.province,
      city: item.city ?? null,
      group_type: bucket,
      sort_order: index,
      source_type: "recommendation" as const,
      recommend_reason: item.reason,
      risk_level:
        bucket === "rush" ? "high" : bucket === "stable" ? "medium" : "low",
    })),
  );
}

function getSchoolTags(item: RecommendationChoiceItem) {
  // 合并 tags 数组和 985/211/双一流布尔字段，统一展示院校标签。
  const tags = new Set<string>();

  if (Array.isArray(item.tags)) {
    for (const tag of item.tags) {
      if (!tag) {
        continue;
      }

      tags.add(tag === "double_first_class" ? "双一流" : tag);
    }
  }

  if (item.is_985) {
    tags.add("985");
  }
  if (item.is_211) {
    tags.add("211");
  }
  if (item.is_double_first_class) {
    tags.add("双一流");
  }

  return tags.size > 0 ? [...tags] : [copy.noTag];
}

function getSchoolName(item: RecommendationChoiceItem) {
  return item.school_name || item.name || copy.noData;
}

function getMajorName(item: RecommendationChoiceItem) {
  return item.major_name || copy.noData;
}

function getLocationLabel(item: RecommendationChoiceItem) {
  return [item.province, item.city].filter(Boolean).join(" / ") || copy.noLocation;
}

function getMinScore(item: RecommendationChoiceItem) {
  return item.estimated_min_score ?? item.min_score ?? copy.noData;
}

function getMinRank(item: RecommendationChoiceItem) {
  return item.estimated_min_rank ?? item.min_rank ?? copy.noData;
}

function formatAnalysisValue(value: unknown) {
  // 成绩分析字段可能是字符串、数字或对象，这里统一转成可展示文本。
  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }

  if (value && typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return copy.noData;
}

function FieldHint({
  count,
  items,
  middle,
}: {
  count: number;
  items: string[];
  middle: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50 px-4 py-3 text-xs leading-6 text-slate-500">
      {copy.parsedProvincePrefix}
      <span className="font-semibold text-slate-700">{count}</span>
      {middle}
      <span className="text-slate-700">{items.join("、") || copy.emptyParsed}</span>
    </div>
  );
}

function InfoTile({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        {label}
      </p>
      <div className="mt-3 text-sm leading-7 text-slate-700">{value}</div>
    </div>
  );
}

function ResultMetric({
  label,
  value,
  tone,
  labelClassName,
  valueClassName,
}: {
  label: string;
  value: number;
  tone: string;
  labelClassName?: string;
  valueClassName?: string;
}) {
  return (
    <div className={cx("rounded-2xl border p-5", tone)}>
      <p
        className={cx(
          "text-xs font-semibold uppercase tracking-[0.22em]",
          labelClassName ?? "text-slate-500",
        )}
      >
        {label}
      </p>
      <p
        className={cx(
          "mt-4 text-3xl font-semibold tracking-tight",
          valueClassName ?? "text-slate-950",
        )}
      >
        {value}
      </p>
    </div>
  );
}

function RecommendationCard({ item }: { item: RecommendationChoiceItem }) {
  // 单个推荐卡片：展示院校、专业、地区、参考最低分/位次和推荐理由。
  const tags = getSchoolTags(item);

  return (
    <Card className="overflow-hidden border-white/80 bg-white/95">
      <CardBody className="space-y-5 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h3 className="text-xl font-semibold tracking-tight text-slate-950">
              {getSchoolName(item)}
            </h3>
            <p className="mt-2 text-sm font-semibold text-sky-700">
              {getMajorName(item)}
            </p>
            <p className="mt-3 text-sm text-slate-600">
              {copy.location}：{getLocationLabel(item)}
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

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <InfoTile label={copy.minScore} value={getMinScore(item)} />
          <InfoTile label={copy.minRank} value={getMinRank(item)} />
          <InfoTile label={copy.province} value={item.province || copy.noData} />
          <InfoTile label={copy.location} value={item.city || copy.noLocation} />
        </div>

        <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            {copy.reason}
          </p>
          <p className="mt-3 text-sm leading-7 text-slate-700">
            {item.reason || copy.noData}
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
  // 一个推荐梯度区块，对应 rush/stable/safe 中的一类。
  const config = bucketConfig[bucket];

  return (
    <section className={cx("rounded-[1.75rem] border p-5 sm:p-6", config.panelTone)}>
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <Badge tone={config.badgeTone}>{config.title}</Badge>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
            {config.description}
          </p>
        </div>
        <div className="rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm text-slate-600">
          {copy.totalPrefix}
          <span className="font-semibold text-slate-900">{items.length}</span>
          {copy.totalSuffix}
        </div>
      </div>

      <div className="mt-5 space-y-4">
        {items.length > 0 ? (
          items.map((item, index) => (
            <RecommendationCard
              key={`${bucket}-${getSchoolName(item)}-${getMajorName(item)}-${index}`}
              item={item}
            />
          ))
        ) : (
          <EmptyState description={copy.noBucketResult} className="bg-white/70" />
        )}
      </div>
    </section>
  );
}

export function RecommendationPage() {
  // form/errors 管理左侧表单；loading/requestError/result 管理请求生命周期。
  const [form, setForm] = useState<FormState>(initialFormState);
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const { currentUser, isAuthenticated } = useAuth();
  const [planName, setPlanName] = useState("");
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  const parsedProvincePreferences = useMemo(
    () => splitPreferenceInput(form.preferredProvinces),
    [form.preferredProvinces],
  );
  const parsedMajorPreferences = useMemo(
    () => splitPreferenceInput(form.preferredMajors),
    [form.preferredMajors],
  );
  const choiceGroup = useMemo(
    () => normalizeChoiceGroup(result?.recommended_choices),
    [result],
  );
  const defaultPlanName = useMemo(() => {
    const province = form.province.trim() || "志愿";
    const score = form.score.trim() || "未命名";
    return `${province}-${score}分方案`;
  }, [form.province, form.score]);

  const handleChange = (field: keyof FormState, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors = validateForm(form);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    const payload: RecommendationRequest = {
      user_id: currentUser?.username || "frontend-user",
      province: form.province.trim(),
      subject_type: form.subjectType,
      score: Number(form.score),
      rank: Number(form.rank),
      preferred_provinces: parsedProvincePreferences,
      preferred_majors: parsedMajorPreferences,
    };

    if (import.meta.env.DEV) {
      console.log("[recommendation] request payload", payload);
    }

    try {
      setLoading(true);
      setRequestError(null);
      setResult(null);
      setSaveError(null);
      setSaveSuccess(null);
      const data = await generateRecommendation(payload);
      setResult(data);
      setPlanName((current) => current || defaultPlanName);
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : copy.requestError);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePlan = async () => {
    if (!result) {
      return;
    }

    const payload: CreatePlanRequest = {
      name: planName.trim() || defaultPlanName,
      province: form.province.trim(),
      subject_type: form.subjectType,
      score: Number(form.score),
      rank: Number(form.rank),
      status: "draft",
      items: flattenPlanItems(choiceGroup),
    };

    try {
      setSaveLoading(true);
      setSaveError(null);
      setSaveSuccess(null);
      const saved = await createPlan(payload);
      setSaveSuccess("方案保存成功，正在跳转到详情页...");
      window.location.assign(`/plans/${saved.id}`);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "保存方案失败，请稍后重试。");
    } finally {
      setSaveLoading(false);
    }
  };

  return (
    <section className="space-y-6">
      <UsageGuide
        badge="Tutorial"
        title="推荐页使用教程"
        description="这个页面是登录后主流程的起点。生成结果后，你可以继续保存方案，并让工作台自动记录本次推荐。"
        steps={[
          "填写省份、科类、分数和位次，偏好地区与专业可以留空，也可以输入多个值。",
          "点击“生成推荐”后，先看上方的冲稳保数量，再往下阅读成绩分析和推荐理由。",
          "如果已经登录，建议立即把当前结果保存为方案，方便后续在“我的方案”里继续对比。",
          "想验证工作台闭环时，保存方案后再去院校查询收藏学校，最后提交报告任务。",
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
        <div className="space-y-6">
          <Card className="overflow-hidden xl:sticky xl:top-28">
            <CardBody className="space-y-6 p-6">
              <div>
                <p className="eyebrow">Recommendation</p>
                <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                  {copy.title}
                </h2>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
                  {copy.intro}
                </p>
              </div>

              <form className="space-y-5" onSubmit={handleSubmit}>
                <div className="field-grid">
                  <Input
                    label={copy.province}
                    value={form.province}
                    onChange={(event) => handleChange("province", event.target.value)}
                    placeholder={copy.provincePlaceholder}
                    error={errors.province}
                  />
                  <Select
                    label={copy.subjectType}
                    value={form.subjectType}
                    onChange={(event) => handleChange("subjectType", event.target.value)}
                    error={errors.subjectType}
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
                    onChange={(event) => handleChange("score", event.target.value)}
                    inputMode="numeric"
                    placeholder={copy.scorePlaceholder}
                    error={errors.score}
                  />
                  <Input
                    label={copy.rank}
                    value={form.rank}
                    onChange={(event) => handleChange("rank", event.target.value)}
                    inputMode="numeric"
                    placeholder={copy.rankPlaceholder}
                    error={errors.rank}
                  />
                </div>

                <div className="space-y-4">
                  <Textarea
                    label={copy.preferredProvinces}
                    value={form.preferredProvinces}
                    onChange={(event) => handleChange("preferredProvinces", event.target.value)}
                    rows={3}
                    placeholder={copy.preferredProvincePlaceholder}
                  />
                  <FieldHint
                    count={parsedProvincePreferences.length}
                    items={parsedProvincePreferences}
                    middle={copy.parsedProvinceMiddle}
                  />
                </div>

                <div className="space-y-4">
                  <Textarea
                    label={copy.preferredMajors}
                    value={form.preferredMajors}
                    onChange={(event) => handleChange("preferredMajors", event.target.value)}
                    rows={3}
                    placeholder={copy.preferredMajorPlaceholder}
                  />
                  <FieldHint
                    count={parsedMajorPreferences.length}
                    items={parsedMajorPreferences}
                    middle={copy.parsedMajorMiddle}
                  />
                </div>

                <Button type="submit" disabled={loading} fullWidth>
                  {loading ? copy.submitting : copy.submit}
                </Button>

                {requestError ? <ErrorMessage>{requestError}</ErrorMessage> : null}
              </form>
            </CardBody>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardBody className="space-y-5">
              <div>
                <p className="eyebrow">{copy.resultOverview}</p>
                <h3 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
                  {copy.resultOverview}
                </h3>
                <p className="mt-3 text-sm leading-7 text-slate-600">
                  这里会展示成绩分析、冲稳保结构和后续学习建议。
                </p>
              </div>

              {loading ? (
                <div className="space-y-4">
                  <Loading label={copy.submitting} />
                  <div className="grid gap-4 md:grid-cols-3">
                    <LoadingBlock />
                    <LoadingBlock />
                    <LoadingBlock />
                  </div>
                </div>
              ) : result ? (
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-3">
                    <ResultMetric
                      label={copy.rush}
                      value={choiceGroup.rush.length}
                      tone="border-slate-900 bg-slate-950"
                      labelClassName="text-white/70"
                      valueClassName="text-white"
                    />
                    <ResultMetric
                      label={copy.stable}
                      value={choiceGroup.stable.length}
                      tone="border-amber-200 bg-amber-50"
                    />
                    <ResultMetric
                      label={copy.safe}
                      value={choiceGroup.safe.length}
                      tone="border-emerald-200 bg-emerald-50"
                    />
                  </div>

                  {isAuthenticated ? (
                    <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 p-4">
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
                        <Input
                          label="方案名称"
                          value={planName}
                          onChange={(event) => setPlanName(event.target.value)}
                          placeholder={defaultPlanName}
                          className="lg:flex-1"
                        />
                        <Button disabled={saveLoading} onClick={() => void handleSavePlan()}>
                          {saveLoading ? "保存中..." : "保存为方案"}
                        </Button>
                      </div>
                      {saveError ? <ErrorMessage>{saveError}</ErrorMessage> : null}
                      {saveSuccess ? <p className="mt-3 text-sm text-emerald-700">{saveSuccess}</p> : null}
                    </div>
                  ) : (
                    <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 p-4 text-sm leading-7 text-slate-600">
                      登录后可以将当前推荐结果保存为长期管理的志愿方案。
                      {" "}
                      <Link to="/login" className="font-semibold text-sky-700 hover:text-sky-800">
                        立即登录
                      </Link>
                    </div>
                  )}
                </div>
              ) : (
                <EmptyState description={copy.noResult} />
              )}
            </CardBody>
          </Card>

          {result ? (
            <>
              <Card>
                <CardHeader>
                  <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                    {copy.scoreAnalysis}
                  </p>
                </CardHeader>
                <CardBody>
                  <div className="grid gap-4 md:grid-cols-3">
                    <InfoTile
                      label={copy.analysisLevel}
                      value={formatAnalysisValue(result.score_analysis.level)}
                    />
                    <InfoTile
                      label={copy.analysisSummary}
                      value={formatAnalysisValue(result.score_analysis.summary)}
                    />
                    <InfoTile
                      label={copy.analysisSuggestion}
                      value={formatAnalysisValue(result.score_analysis.suggestion)}
                    />
                  </div>
                </CardBody>
              </Card>

              <RecommendationBucket bucket="rush" items={choiceGroup.rush} />
              <RecommendationBucket bucket="stable" items={choiceGroup.stable} />
              <RecommendationBucket bucket="safe" items={choiceGroup.safe} />

              <Card>
                <CardHeader>
                  <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                    {copy.studyPlan}
                  </p>
                </CardHeader>
                <CardBody>
                  {result.study_plan ? (
                    <p className="whitespace-pre-wrap text-sm leading-8 text-slate-700">
                      {typeof result.study_plan === "string"
                        ? result.study_plan
                        : JSON.stringify(result.study_plan, null, 2)}
                    </p>
                  ) : (
                    <EmptyState description={copy.emptyStudyPlan} />
                  )}
                </CardBody>
              </Card>

              <Card>
                <CardHeader>
                  <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                    {copy.finalAdvice}
                  </p>
                </CardHeader>
                <CardBody>
                  {result.final_answer ? (
                    <p className="text-sm leading-8 text-slate-700">{result.final_answer}</p>
                  ) : (
                    <EmptyState description={copy.emptyFinalAnswer} />
                  )}
                </CardBody>
              </Card>
            </>
          ) : null}
        </div>
      </div>
    </section>
  );
}
