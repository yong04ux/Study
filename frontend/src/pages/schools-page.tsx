import { FormEvent, ReactNode, useState } from "react";
import { Link } from "react-router-dom";
import { addFavoriteSchool, removeFavoriteSchool } from "../api/favorites";
import {
  getSchoolDetail,
  getSchoolScoreLines,
  searchSchools,
} from "../api/school";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardBody, CardHeader } from "../components/ui/card";
import { UsageGuide } from "../components/usage-guide";
import { EmptyState } from "../components/ui/empty-state";
import { ErrorMessage } from "../components/ui/error-message";
import { Input } from "../components/ui/input";
import { Loading, LoadingBlock } from "../components/ui/loading";
import { Select } from "../components/ui/select";
import { cx } from "../components/ui/cx";
import { useAuth } from "../contexts/auth-context";
import type {
  ScoreLine,
  SchoolDetail,
  SchoolSearchParams,
  SchoolListItem,
} from "../types/school";

// 院校查询页：左侧负责查询表单和院校列表，右侧展示选中院校详情与历年分数线。
const copy = {
  eyebrow: "Schools",
  title: "\u9662\u6821\u67e5\u8be2",
  intro:
    "\u6309\u9662\u6821\u540d\u79f0\u3001\u7701\u4efd\u3001\u5c42\u6b21\u548c\u9879\u76ee\u6807\u7b7e\u7b5b\u9009\u9662\u6821\uff0c\u5e76\u8fdb\u4e00\u6b65\u67e5\u770b\u57fa\u672c\u4fe1\u606f\u3001\u9662\u6821\u7b80\u4ecb\u4e0e\u5386\u5e74\u5206\u6570\u7ebf\u3002",
  schoolName: "\u9662\u6821\u540d\u79f0",
  province: "\u7701\u4efd",
  schoolLevel: "\u9662\u6821\u5c42\u6b21",
  is985: "\u662f\u5426 985",
  is211: "\u662f\u5426 211",
  all: "\u5168\u90e8",
  yes: "\u662f",
  no: "\u5426",
  search: "\u67e5\u8be2",
  searching: "\u67e5\u8be2\u4e2d...",
  reset: "\u91cd\u7f6e",
  results: "\u9662\u6821\u5217\u8868",
  detail: "\u9662\u6821\u8be6\u60c5",
  scoreLines: "\u5386\u5e74\u5206\u6570\u7ebf",
  introduction: "\u9662\u6821\u7b80\u4ecb",
  noIntroduction: "\u6682\u65e0\u9662\u6821\u7b80\u4ecb\u4fe1\u606f\u3002",
  noData: "\u6682\u65e0\u6570\u636e",
  noTags: "\u666e\u901a\u9662\u6821",
  noResults:
    "\u6682\u672a\u627e\u5230\u5339\u914d\u9662\u6821\uff0c\u53ef\u4ee5\u5c1d\u8bd5\u653e\u5bbd\u67e5\u8be2\u6761\u4ef6\u3002",
  selectSchool:
    "\u9009\u62e9\u5de6\u4fa7\u9662\u6821\u540e\uff0c\u8fd9\u91cc\u4f1a\u5c55\u793a\u57fa\u672c\u4fe1\u606f\u3001\u7b80\u4ecb\u548c\u5386\u5e74\u5206\u6570\u7ebf\u3002",
  searchHint:
    "\u5148\u8f93\u5165\u67e5\u8be2\u6761\u4ef6\uff0c\u518d\u5728\u5217\u8868\u4e2d\u9009\u62e9\u611f\u5174\u8da3\u7684\u9662\u6821\u3002",
  schoolNamePlaceholder: "\u5982\uff1a\u5317\u4eac\u5927\u5b66",
  provincePlaceholder: "\u5982\uff1a\u5e7f\u4e1c",
  levelPlaceholder: "\u5982\uff1a\u672c\u79d1",
  schoolCode: "\u9662\u6821\u4ee3\u7801",
  city: "\u57ce\u5e02",
  type: "\u7c7b\u578b",
  level: "\u5c42\u6b21",
  queryScoreLines: "\u67e5\u8be2\u5206\u6570\u7ebf",
  queryScoreLinesLoading: "\u67e5\u8be2\u4e2d...",
  year: "\u5e74\u4efd",
  subjectType: "\u79d1\u7c7b",
  majorName: "\u4e13\u4e1a\u540d\u79f0",
  majorNamePlaceholder: "\u53ef\u9009\uff0c\u5982\uff1a\u8f6f\u4ef6\u5de5\u7a0b",
  batch: "\u6279\u6b21",
  minScore: "\u6700\u4f4e\u5206",
  minRank: "\u6700\u4f4e\u4f4d\u6b21",
  avgScore: "\u5e73\u5747\u5206",
  maxScore: "\u6700\u9ad8\u5206",
  total: "\u5339\u914d\u7ed3\u679c",
  schoolProfile: "\u57fa\u672c\u4fe1\u606f",
  scoreLineHint:
    "\u53ef\u6839\u636e\u7701\u4efd\u3001\u5e74\u4efd\u3001\u79d1\u7c7b\u548c\u4e13\u4e1a\u8fdb\u4e00\u6b65\u8fc7\u6ee4\u5386\u5e74\u5f55\u53d6\u7ebf\u3002",
  noScoreLines:
    "\u5f53\u524d\u6761\u4ef6\u4e0b\u6682\u65e0\u5206\u6570\u7ebf\u6570\u636e\u3002",
  loadDetailError:
    "\u9662\u6821\u8be6\u60c5\u52a0\u8f7d\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002",
  loadScoreLinesError:
    "\u5206\u6570\u7ebf\u67e5\u8be2\u5931\u8d25\uff0c\u8bf7\u68c0\u67e5\u6761\u4ef6\u540e\u91cd\u8bd5\u3002",
  searchError:
    "\u9662\u6821\u67e5\u8be2\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002",
  scoreLineValidation:
    "\u8bf7\u786e\u4fdd\u5e74\u4efd\u5728 2000 \u5230 2100 \u4e4b\u95f4\uff0c\u6216\u8005\u7559\u7a7a\u4e0d\u6309\u5e74\u4efd\u8fc7\u6ee4\u3002",
  favorite: "\u6536\u85cf\u5b66\u6821",
  unfavorite: "\u53d6\u6d88\u6536\u85cf",
  favoriteHint:
    "\u767b\u5f55\u540e\u53ef\u4ee5\u6536\u85cf\u5b66\u6821\uff0c\u5e76\u5728\u5de5\u4f5c\u53f0\u91cc\u96c6\u4e2d\u67e5\u770b\u3002",
  favoriteError:
    "\u6536\u85cf\u64cd\u4f5c\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002",
};

const subjectOptions = [
  "\u7269\u7406\u7c7b",
  "\u5386\u53f2\u7c7b",
  "\u7406\u79d1",
  "\u6587\u79d1",
];

const initialSearchForm = {
  // 院校列表查询表单：这些字段会转换为 /schools/search 的查询参数。
  schoolName: "",
  province: "",
  schoolLevel: "",
  is985: "",
  is211: "",
};

const initialScoreForm = {
  // 分数线过滤表单：选中院校后自动带入省份，也允许用户继续筛选年份/科类/专业。
  province: "",
  year: "2024",
  subjectType: subjectOptions[0],
  majorName: "",
};

type SearchFormState = typeof initialSearchForm;
type ScoreFormState = typeof initialScoreForm;

function booleanFilterValue(value: string) {
  // select 的值是字符串，这里转换成后端需要的 boolean 或 undefined。
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }

  return undefined;
}

function buildSearchParams(form: SearchFormState): SchoolSearchParams {
  // 只把非空条件传给后端，避免空字符串影响 SQL 过滤。
  return {
    school_name: form.schoolName.trim() || undefined,
    province: form.province.trim() || undefined,
    school_level: form.schoolLevel.trim() || undefined,
    is_985: booleanFilterValue(form.is985),
    is_211: booleanFilterValue(form.is211),
    page: 1,
    page_size: 20,
  };
}

function getTags(school: SchoolListItem | SchoolDetail) {
  // 根据院校标签字段生成可展示的徽标数组。
  const tags: string[] = [];

  if (school.is_985) {
    tags.push("985");
  }
  if (school.is_211) {
    tags.push("211");
  }
  if (school.is_double_first_class) {
    tags.push("\u53cc\u4e00\u6d41");
  }

  return tags;
}

function displayValue(value: string | number | null | undefined) {
  return value ?? copy.noData;
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

function SchoolTags({ school }: { school: SchoolListItem | SchoolDetail }) {
  const tags = getTags(school);

  return tags.length > 0 ? (
    <>
      {tags.map((tag) => (
        <Badge key={tag} tone="brand">
          {tag}
        </Badge>
      ))}
    </>
  ) : (
    <Badge tone="neutral">{copy.noTags}</Badge>
  );
}

function DetailField({
  label,
  value,
}: {
  label: string;
  value: string | number | null | undefined;
}) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-4">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        {label}
      </p>
      <p className="mt-3 text-sm font-medium text-slate-900">{displayValue(value)}</p>
    </div>
  );
}

function SchoolCard({
  school,
  selected,
  onSelect,
}: {
  school: SchoolListItem;
  selected: boolean;
  onSelect: () => void;
}) {
  // 左下院校列表卡片：点击后触发详情和分数线加载。
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cx(
        "w-full text-left transition",
        selected && "translate-y-[-1px]",
      )}
    >
      <Card
        className={cx(
          "overflow-hidden border-slate-200/90 hover:border-sky-200 hover:shadow-[0_24px_55px_rgba(14,165,233,0.14)]",
          selected && "border-sky-400 ring-4 ring-sky-100",
        )}
      >
        <CardBody className="space-y-4 p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-950">{school.school_name}</h3>
              <p className="mt-2 text-sm text-slate-600">
                {displayValue(school.province)} / {displayValue(school.city)}
              </p>
              <p className="mt-2 text-sm text-slate-600">
                {displayValue(school.school_type)} / {displayValue(school.school_level)}
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <SchoolTags school={school} />
            </div>
          </div>
        </CardBody>
      </Card>
    </button>
  );
}

export function SchoolsPage() {
  const { isAuthenticated } = useAuth();
  // searchForm：左上查询条件；scoreForm：右侧分数线过滤条件。
  const [searchForm, setSearchForm] = useState<SearchFormState>(initialSearchForm);
  const [scoreForm, setScoreForm] = useState<ScoreFormState>(initialScoreForm);
  // schools/total：左下院校列表和总数；selectedSchool/scoreLines：右侧详情数据。
  const [schools, setSchools] = useState<SchoolListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedSchool, setSelectedSchool] = useState<SchoolDetail | null>(null);
  const [scoreLines, setScoreLines] = useState<ScoreLine[]>([]);
  // loading 分开管理，避免“查询列表”和“加载详情/分数线”互相影响。
  const [searchLoading, setSearchLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [scoreLinesLoading, setScoreLinesLoading] = useState(false);
  // error 分开管理，页面可分别展示搜索失败、详情失败、分数线失败。
  const [searchError, setSearchError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [scoreLinesError, setScoreLinesError] = useState<string | null>(null);
  const [favoriteLoading, setFavoriteLoading] = useState(false);
  const [favoriteError, setFavoriteError] = useState<string | null>(null);
  // hasSearched 用于区分初始空状态和搜索后无结果状态。
  const [hasSearched, setHasSearched] = useState(false);

  const updateSearchForm = (field: keyof SearchFormState, value: string) => {
    setSearchForm((current) => ({ ...current, [field]: value }));
  };

  const updateScoreForm = (field: keyof ScoreFormState, value: string) => {
    setScoreForm((current) => ({ ...current, [field]: value }));
  };

  const handleSearch = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();

    try {
      // 点击“查询”后进入 loading，清空旧错误，调用 /schools/search。
      setSearchLoading(true);
      setSearchError(null);
      setHasSearched(true);
      const data = await searchSchools(buildSearchParams(searchForm));
      // API 层已 normalize，这里再保守兜底，避免 undefined.length 问题。
      const items = Array.isArray(data.items) ? data.items : [];
      setSchools(items);
      setTotal(Number.isFinite(data.total) ? data.total : items.length);
      // 新搜索开始时清空右侧已选院校，避免展示旧详情。
      setSelectedSchool(null);
      setScoreLines([]);
      setDetailError(null);
      setScoreLinesError(null);
      setFavoriteError(null);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : copy.searchError);
      setSchools([]);
      setTotal(0);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleReset = () => {
    // 重置会恢复到初始状态：无搜索、无选中、无错误。
    setSearchForm(initialSearchForm);
    setSchools([]);
    setTotal(0);
    setSelectedSchool(null);
    setScoreLines([]);
    setSearchError(null);
    setDetailError(null);
    setScoreLinesError(null);
    setFavoriteError(null);
    setHasSearched(false);
  };

  const loadScoreLines = async (schoolId: number, form: ScoreFormState) => {
    const province = form.province.trim();
    const year = form.year.trim() ? Number(form.year) : undefined;

    if (year !== undefined && (!Number.isInteger(year) || year < 2000 || year > 2100)) {
      // 只校验用户填写的年份；年份留空时表示不按年份过滤。
      setScoreLinesError(copy.scoreLineValidation);
      setScoreLines([]);
      return;
    }

    try {
      // 分数线查询单独 loading，避免右侧详情整体闪烁。
      setScoreLinesLoading(true);
      setScoreLinesError(null);
      const data = await getSchoolScoreLines(schoolId, {
        province: province || undefined,
        year,
        subject_type: form.subjectType || undefined,
        major_name: form.majorName.trim() || undefined,
      });
      setScoreLines(Array.isArray(data) ? data : []);
    } catch (error) {
      setScoreLinesError(error instanceof Error ? error.message : copy.loadScoreLinesError);
      setScoreLines([]);
    } finally {
      setScoreLinesLoading(false);
    }
  };

  const handleSelectSchool = async (school: SchoolListItem) => {
    try {
      // 点击院校卡片后，先查详情，再用详情中的省份补充分数线查询条件。
      setDetailLoading(true);
      setDetailError(null);
      setScoreLinesError(null);
      setFavoriteError(null);
      const detail = await getSchoolDetail(school.id);
      setSelectedSchool(detail);

      const nextScoreForm = {
        ...scoreForm,
        province: searchForm.province.trim() || detail.province || "",
      };
      setScoreForm(nextScoreForm);
      // 详情加载成功后，自动加载一次该院校分数线，形成页面闭环。
      await loadScoreLines(detail.id, nextScoreForm);
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : copy.loadDetailError);
      setSelectedSchool(null);
      setScoreLines([]);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleScoreLineSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (selectedSchool) {
      await loadScoreLines(selectedSchool.id, scoreForm);
    }
  };

  const handleToggleFavorite = async () => {
    if (!selectedSchool) {
      return;
    }

    try {
      setFavoriteLoading(true);
      setFavoriteError(null);
      if (selectedSchool.is_favorited) {
        await removeFavoriteSchool(selectedSchool.id);
        setSelectedSchool((current) =>
          current ? { ...current, is_favorited: false } : current,
        );
      } else {
        await addFavoriteSchool(selectedSchool.id);
        setSelectedSchool((current) =>
          current ? { ...current, is_favorited: true } : current,
        );
      }
    } catch (error) {
      setFavoriteError(error instanceof Error ? error.message : copy.favoriteError);
    } finally {
      setFavoriteLoading(false);
    }
  };

  return (
    <section className="space-y-6">
      <UsageGuide
        badge="Tutorial"
        title="院校查询页使用教程"
        description="这个页面适合在推荐结果出来后继续做学校筛选。登录后，打开学校详情和收藏学校都会帮助你补齐工作台数据。"
        steps={[
          "先按学校名、省份或 985/211 条件搜索，缩小候选范围。",
          "点击左侧学校卡片后，右侧会自动加载详情和历年分数线。",
          "如果你已经登录，建议把准备重点比较的学校加入收藏，工作台会同步显示。",
          "需要继续判断录取风险时，可以结合右侧分数线与推荐页结果一起看。",
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div className="space-y-6">
          <Card>
            <CardBody className="space-y-6 p-6">
              <SectionHeading
                eyebrow={copy.eyebrow}
                title={copy.title}
                description={copy.intro}
                action={<Badge tone="brand">Search + Detail Drilldown</Badge>}
              />

              <form className="space-y-5" onSubmit={handleSearch}>
                <div className="field-grid">
                  <Input
                    label={copy.schoolName}
                    value={searchForm.schoolName}
                    onChange={(event) => updateSearchForm("schoolName", event.target.value)}
                    placeholder={copy.schoolNamePlaceholder}
                  />
                  <Input
                    label={copy.province}
                    value={searchForm.province}
                    onChange={(event) => updateSearchForm("province", event.target.value)}
                    placeholder={copy.provincePlaceholder}
                  />
                  <Input
                    label={copy.schoolLevel}
                    value={searchForm.schoolLevel}
                    onChange={(event) => updateSearchForm("schoolLevel", event.target.value)}
                    placeholder={copy.levelPlaceholder}
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <Select
                      label={copy.is985}
                      value={searchForm.is985}
                      onChange={(event) => updateSearchForm("is985", event.target.value)}
                    >
                      <option value="">{copy.all}</option>
                      <option value="true">{copy.yes}</option>
                      <option value="false">{copy.no}</option>
                    </Select>
                    <Select
                      label={copy.is211}
                      value={searchForm.is211}
                      onChange={(event) => updateSearchForm("is211", event.target.value)}
                    >
                      <option value="">{copy.all}</option>
                      <option value="true">{copy.yes}</option>
                      <option value="false">{copy.no}</option>
                    </Select>
                  </div>
                </div>

                <div className="flex flex-col gap-3 sm:flex-row">
                  <Button type="submit" disabled={searchLoading} className="sm:flex-1">
                    {searchLoading ? copy.searching : copy.search}
                  </Button>
                  <Button type="button" variant="secondary" onClick={handleReset}>
                    {copy.reset}
                  </Button>
                </div>

                {searchError ? <ErrorMessage>{searchError}</ErrorMessage> : null}
              </form>
            </CardBody>
          </Card>

          <Card>
            <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="eyebrow">{copy.results}</p>
                <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
                  {copy.results}
                </h2>
              </div>
              <Badge tone="neutral">
                {copy.total} {total}
              </Badge>
            </CardHeader>
            <CardBody className="space-y-4">
              {searchLoading ? (
                <div className="space-y-3">
                  <Loading label={copy.searching} />
                  <LoadingBlock className="h-32" />
                  <LoadingBlock className="h-32" />
                  <LoadingBlock className="h-32" />
                </div>
              ) : schools.length > 0 ? (
                <div className="space-y-3">
                  {schools.map((school) => (
                    <SchoolCard
                      key={school.id}
                      school={school}
                      selected={selectedSchool?.id === school.id}
                      onSelect={() => void handleSelectSchool(school)}
                    />
                  ))}
                </div>
              ) : (
                <EmptyState description={hasSearched ? copy.noResults : copy.searchHint} />
              )}
            </CardBody>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="xl:sticky xl:top-28">
            <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                  <p className="eyebrow">{copy.detail}</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                  {selectedSchool?.school_name ?? copy.detail}
                </h2>
              </div>
              {selectedSchool ? (
                <div className="flex flex-wrap items-center gap-2">
                  <SchoolTags school={selectedSchool} />
                  {isAuthenticated ? (
                    <Button
                      type="button"
                      variant={selectedSchool.is_favorited ? "secondary" : "primary"}
                      disabled={favoriteLoading}
                      onClick={() => void handleToggleFavorite()}
                    >
                      {favoriteLoading
                        ? "..."
                        : selectedSchool.is_favorited
                          ? copy.unfavorite
                          : copy.favorite}
                    </Button>
                  ) : (
                    <Link
                      to="/login"
                      className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
                    >
                      {copy.favorite}
                    </Link>
                  )}
                </div>
              ) : null}
            </CardHeader>

            <CardBody className="space-y-6">
              {detailLoading ? (
                <div className="space-y-4">
                  <Loading label={copy.detail} />
                  <LoadingBlock />
                  <LoadingBlock />
                </div>
              ) : detailError ? (
                <ErrorMessage>{detailError}</ErrorMessage>
              ) : selectedSchool ? (
                <>
                  {favoriteError ? <ErrorMessage>{favoriteError}</ErrorMessage> : null}
                  {!isAuthenticated ? (
                    <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-5 py-4 text-sm leading-7 text-slate-600">
                      {copy.favoriteHint}{" "}
                      <Link to="/login" className="font-semibold text-sky-700 hover:text-sky-800">
                        {"\u7acb\u5373\u767b\u5f55"}
                      </Link>
                    </div>
                  ) : null}
                  <div className="space-y-4">
                    <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                      {copy.schoolProfile}
                    </p>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <DetailField label={copy.schoolCode} value={selectedSchool.school_code} />
                      <DetailField label={copy.province} value={selectedSchool.province} />
                      <DetailField label={copy.city} value={selectedSchool.city} />
                      <DetailField label={copy.type} value={selectedSchool.school_type} />
                      <DetailField label={copy.level} value={selectedSchool.school_level} />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-5 py-5">
                    <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                      {copy.introduction}
                    </p>
                    <p className="mt-4 text-sm leading-8 text-slate-700">
                      {selectedSchool.description || copy.noIntroduction}
                    </p>
                  </div>

                  <Card className="border-slate-200/80 shadow-none">
                    <CardHeader>
                      <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                        {copy.scoreLines}
                      </p>
                      <p className="mt-3 text-sm leading-7 text-slate-600">
                        {copy.scoreLineHint}
                      </p>
                    </CardHeader>
                    <CardBody className="space-y-5">
                      <form className="space-y-5" onSubmit={handleScoreLineSubmit}>
                        <div className="field-grid">
                          <Input
                            label={copy.province}
                            value={scoreForm.province}
                            onChange={(event) => updateScoreForm("province", event.target.value)}
                            placeholder={copy.provincePlaceholder}
                          />
                          <Input
                            label={copy.year}
                            value={scoreForm.year}
                            onChange={(event) => updateScoreForm("year", event.target.value)}
                            inputMode="numeric"
                          />
                          <Select
                            label={copy.subjectType}
                            value={scoreForm.subjectType}
                            onChange={(event) =>
                              updateScoreForm("subjectType", event.target.value)
                            }
                          >
                            {subjectOptions.map((option) => (
                              <option key={option} value={option}>
                                {option}
                              </option>
                            ))}
                          </Select>
                          <Input
                            label={copy.majorName}
                            value={scoreForm.majorName}
                            onChange={(event) => updateScoreForm("majorName", event.target.value)}
                            placeholder={copy.majorNamePlaceholder}
                          />
                        </div>

                        <Button type="submit" disabled={scoreLinesLoading} fullWidth>
                          {scoreLinesLoading
                            ? copy.queryScoreLinesLoading
                            : copy.queryScoreLines}
                        </Button>
                      </form>

                      {scoreLinesError ? <ErrorMessage>{scoreLinesError}</ErrorMessage> : null}

                      {scoreLinesLoading ? (
                        <div className="space-y-3">
                          <Loading label={copy.queryScoreLinesLoading} />
                          <LoadingBlock />
                          <LoadingBlock />
                        </div>
                      ) : scoreLines.length > 0 ? (
                        <div className="overflow-hidden rounded-2xl border border-slate-200/80">
                          <div className="overflow-x-auto">
                            <table className="min-w-[760px] w-full border-collapse">
                              <thead className="bg-slate-50">
                                <tr className="text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                                  <th className="px-4 py-3">{copy.year}</th>
                                  <th className="px-4 py-3">{copy.majorName}</th>
                                  <th className="px-4 py-3">{copy.batch}</th>
                                  <th className="px-4 py-3">{copy.minScore}</th>
                                  <th className="px-4 py-3">{copy.minRank}</th>
                                  <th className="px-4 py-3">{copy.avgScore}</th>
                                  <th className="px-4 py-3">{copy.maxScore}</th>
                                </tr>
                              </thead>
                              <tbody>
                                {scoreLines.map((line) => (
                                  <tr
                                    key={`${line.year}-${line.province}-${line.subject_type}-${line.major_name ?? "school"}-${line.min_score}`}
                                    className="border-t border-slate-200/80 text-sm text-slate-700"
                                  >
                                    <td className="px-4 py-3">{line.year}</td>
                                    <td className="px-4 py-3">{displayValue(line.major_name)}</td>
                                    <td className="px-4 py-3">{line.batch}</td>
                                    <td className="px-4 py-3">{line.min_score}</td>
                                    <td className="px-4 py-3">{displayValue(line.min_rank)}</td>
                                    <td className="px-4 py-3">{displayValue(line.avg_score)}</td>
                                    <td className="px-4 py-3">{displayValue(line.max_score)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      ) : (
                        <EmptyState description={copy.noScoreLines} className="py-8" />
                      )}
                    </CardBody>
                  </Card>
                </>
              ) : (
                <EmptyState description={copy.selectSchool} />
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </section>
  );
}
