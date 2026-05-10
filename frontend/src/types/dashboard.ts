import type { FavoriteSchool } from "./favorite";
import type { PlanSummary } from "./plan";

export type DashboardActivityType =
  | "recommendation"
  | "school_view"
  | "qa"
  | "report";

export interface DashboardActivity {
  id: number;
  activity_type: DashboardActivityType;
  target_id?: string | null;
  summary: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface DashboardOverview {
  recent_recommendations: DashboardActivity[];
  recent_school_views: DashboardActivity[];
  recent_questions: DashboardActivity[];
  favorite_schools: FavoriteSchool[];
  report_tasks: DashboardActivity[];
  recent_plans: PlanSummary[];
}
