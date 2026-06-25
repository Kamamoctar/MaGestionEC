import apiClient from "./client";

export interface DashboardStats {
  total: number;
  en_attente: number;
  en_cours: number;
  traites: number;
  archives: number;
  en_retard: number;
  top_postes: { intitule: string; total: number; traites: number; en_retard: number }[];
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>("/dashboard/stats");
  return data;
}
