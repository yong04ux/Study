import { apiClient } from "./client";
import type { CreatePlanRequest, PlanDetail, PlanSummary } from "../types/plan";

export async function createPlan(payload: CreatePlanRequest): Promise<PlanDetail> {
  const { data } = await apiClient.post<PlanDetail>("/plans", payload);
  return data;
}

export async function listPlans(): Promise<PlanSummary[]> {
  const { data } = await apiClient.get<PlanSummary[]>("/plans");
  return data;
}

export async function getPlanDetail(planId: number): Promise<PlanDetail> {
  const { data } = await apiClient.get<PlanDetail>(`/plans/${planId}`);
  return data;
}

export async function deletePlan(planId: number): Promise<void> {
  await apiClient.delete(`/plans/${planId}`);
}

export async function duplicatePlan(planId: number): Promise<PlanDetail> {
  const { data } = await apiClient.post<PlanDetail>(`/plans/${planId}/duplicate`);
  return data;
}
