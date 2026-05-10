import { apiClient } from "./client";
import type { FavoriteSchool, FavoriteSchoolStatus } from "../types/favorite";

export async function listFavoriteSchools(): Promise<FavoriteSchool[]> {
  const { data } = await apiClient.get<FavoriteSchool[]>("/favorites/schools");
  return Array.isArray(data) ? data : [];
}

export async function addFavoriteSchool(schoolId: number): Promise<FavoriteSchool> {
  const { data } = await apiClient.post<FavoriteSchool>(`/favorites/schools/${schoolId}`);
  return data;
}

export async function removeFavoriteSchool(schoolId: number): Promise<void> {
  await apiClient.delete(`/favorites/schools/${schoolId}`);
}

export async function getFavoriteSchoolStatus(schoolId: number): Promise<FavoriteSchoolStatus> {
  const { data } = await apiClient.get<FavoriteSchoolStatus>(`/favorites/schools/${schoolId}/status`);
  return data;
}
