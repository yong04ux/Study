import { apiClient } from "./client";
import type { DashboardActivity, DashboardOverview } from "../types/dashboard";

export async function getDashboardOverview(): Promise<DashboardOverview> {
  const { data } = await apiClient.get<DashboardOverview>("/dashboard/overview");
  return data;
}

export async function getDashboardActivities(activityType?: string): Promise<DashboardActivity[]> {
  const { data } = await apiClient.get<DashboardActivity[]>("/dashboard/activities", {
    params: activityType ? { activity_type: activityType } : undefined,
  });
  return data;
}
