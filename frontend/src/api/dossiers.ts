import apiClient from "./client";
import type { Dossier } from "../types";

export async function getDossiers(): Promise<Dossier[]> {
  const { data } = await apiClient.get<Dossier[]>("/dossiers");
  return data;
}

export async function creerDossier(titre: string, description?: string): Promise<Dossier> {
  const { data } = await apiClient.post<Dossier>("/dossiers", { titre, description });
  return data;
}

export async function modifierDossier(id: string, updates: { titre?: string; description?: string }): Promise<Dossier> {
  const { data } = await apiClient.patch<Dossier>(`/dossiers/${id}`, updates);
  return data;
}

export async function supprimerDossier(id: string): Promise<void> {
  await apiClient.delete(`/dossiers/${id}`);
}
