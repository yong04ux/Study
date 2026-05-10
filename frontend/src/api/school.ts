import { apiClient } from "./client";
import type {
  ScoreLine,
  SchoolDetail,
  SchoolListItem,
  SchoolScoreLineParams,
  SchoolSearchParams,
  SchoolSearchResponse
} from "../types/school";

// 兼容后端历史字段：旧接口可能返回 name / introduction / official_website。
type SchoolLike = Partial<SchoolListItem> & {
  name?: string;
  school_code?: string;
  description?: string | null;
  introduction?: string | null;
  official_website?: string | null;
};

type ScoreLineLike = Partial<ScoreLine>;

// 后端布尔值可能是 boolean、数字或字符串，统一转换成真正的 boolean。
function toBoolean(value: unknown): boolean {
  return value === true || value === 1 || value === "1" || value === "true";
}

// 将院校列表 item 归一化，避免页面因为字段缺失或旧字段名而崩溃。
function normalizeSchoolItem(raw: SchoolLike): SchoolListItem {
  return {
    id: Number(raw.id ?? 0),
    school_name: String(raw.school_name ?? raw.name ?? ""),
    province: String(raw.province ?? ""),
    city: raw.city ?? null,
    school_type: raw.school_type ?? null,
    school_level: raw.school_level ?? null,
    is_985: toBoolean(raw.is_985),
    is_211: toBoolean(raw.is_211),
    is_double_first_class: toBoolean(raw.is_double_first_class),
    is_favorited: toBoolean((raw as SchoolLike & { is_favorited?: unknown }).is_favorited),
  };
}

// 院校详情在列表字段基础上补充 school_code 和 description。
function normalizeSchoolDetail(raw: SchoolLike): SchoolDetail {
  return {
    ...normalizeSchoolItem(raw),
    school_code: String(raw.school_code ?? ""),
    description: raw.description ?? raw.introduction ?? raw.official_website ?? null,
  };
}

// 分数线接口返回值也做一次兜底，保证页面始终拿到稳定字段类型。
function normalizeScoreLine(raw: ScoreLineLike): ScoreLine {
  return {
    year: Number(raw.year ?? 0),
    province: String(raw.province ?? ""),
    subject_type: String(raw.subject_type ?? ""),
    batch: String(raw.batch ?? ""),
    major_name: raw.major_name ?? null,
    min_score: Number(raw.min_score ?? 0),
    min_rank: raw.min_rank == null ? null : Number(raw.min_rank),
    avg_score: raw.avg_score == null ? null : Number(raw.avg_score),
    max_score: raw.max_score == null ? null : Number(raw.max_score),
  };
}

export async function searchSchools(
  params: SchoolSearchParams = {},
): Promise<SchoolSearchResponse> {
  // 查询流程：页面传入筛选条件 -> 调用后端 /schools/search -> normalize 后返回页面。
  const { data } = await apiClient.get<SchoolSearchResponse>("/schools/search", {
    params
  });

  // items 必须兜底成数组，否则页面读取 schools.length 时会报错。
  const items = Array.isArray(data?.items) ? data.items.map(normalizeSchoolItem) : [];
  const fallbackPageSize = params.page_size ?? (items.length > 0 ? items.length : 10);

  return {
    items,
    total: Number(data?.total ?? items.length),
    page: Number(data?.page ?? params.page ?? 1),
    page_size: Number(data?.page_size ?? fallbackPageSize),
  };
}

export async function getSchoolDetail(schoolId: number): Promise<SchoolDetail> {
  // 点击院校卡片后调用详情接口，右侧详情面板依赖这个结果渲染。
  const { data } = await apiClient.get<SchoolLike>(`/schools/${schoolId}`);
  return normalizeSchoolDetail(data ?? {});
}

export async function getSchoolScoreLines(
  schoolId: number,
  params: SchoolScoreLineParams = {},
): Promise<ScoreLine[]> {
  // 分数线参数都是可选的，页面可按省份、年份、科类、专业逐步过滤。
  const { data } = await apiClient.get<ScoreLineLike[]>(
    `/schools/${schoolId}/score-lines`,
    {
      params
    },
  );

  return Array.isArray(data) ? data.map(normalizeScoreLine) : [];
}
