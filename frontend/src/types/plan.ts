export type PlanGroupType = "rush" | "stable" | "safe";
export type PlanSourceType = "manual" | "recommendation";

export interface PlanItemCreateRequest {
  school_id?: number | null;
  major_id?: number | null;
  school_name: string;
  major_name?: string | null;
  province?: string | null;
  city?: string | null;
  group_type: PlanGroupType;
  sort_order: number;
  source_type: PlanSourceType;
  recommend_reason?: string | null;
  risk_level?: string | null;
}

export interface CreatePlanRequest {
  name: string;
  province: string;
  subject_type: string;
  score: number;
  rank: number;
  status: string;
  items: PlanItemCreateRequest[];
}

export interface PlanSummary {
  id: number;
  user_id: number;
  name: string;
  province: string;
  subject_type: string;
  score: number;
  rank: number;
  status: string;
  created_at: string;
  updated_at: string;
  items_count: number;
}

export interface PlanItem {
  id: number;
  plan_id: number;
  school_id?: number | null;
  major_id?: number | null;
  school_name: string;
  major_name?: string | null;
  group_type: PlanGroupType;
  sort_order: number;
  source_type: PlanSourceType;
  recommend_reason?: string | null;
  risk_level?: string | null;
  created_at: string;
  updated_at: string;
}

export interface GroupedPlanItems {
  rush: PlanItem[];
  stable: PlanItem[];
  safe: PlanItem[];
}

export interface PlanDetail extends PlanSummary {
  items: PlanItem[];
  grouped_items: GroupedPlanItems;
}
