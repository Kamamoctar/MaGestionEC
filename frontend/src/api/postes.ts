import apiClient from "./client";
import type { Poste } from "../types";

export async function getPostes(): Promise<Poste[]> {
  const { data } = await apiClient.get<Poste[]>("/postes");
  return data;
}

export async function getPoste(id: string): Promise<Poste> {
  const { data } = await apiClient.get<Poste>(`/postes/${id}`);
  return data;
}

export async function creerPoste(payload: Partial<Poste>): Promise<Poste> {
  const { data } = await apiClient.post<Poste>("/postes", payload);
  return data;
}

export async function affecterOccupant(posteId: string, utilisateur_id: string, type = "titulaire"): Promise<Poste> {
  const { data } = await apiClient.put<Poste>(`/postes/${posteId}/occupant`, { utilisateur_id, type });
  return data;
}

export async function affecterInterimaire(posteId: string, utilisateur_id: string): Promise<Poste> {
  const { data } = await apiClient.post<Poste>(`/postes/${posteId}/interimaire`, { utilisateur_id });
  return data;
}
