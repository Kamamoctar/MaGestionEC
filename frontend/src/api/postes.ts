import apiClient from "./client";
import type { Poste } from "../types";

export async function getPostes(includeInactive = false): Promise<Poste[]> {
  const { data } = await apiClient.get<Poste[]>("/postes", {
    params: includeInactive ? { include_inactive: true } : undefined,
  });
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

export async function libererOccupant(posteId: string): Promise<Poste> {
  const { data } = await apiClient.delete<Poste>(`/postes/${posteId}/occupant`);
  return data;
}

export async function desactiverPoste(posteId: string): Promise<Poste> {
  const { data } = await apiClient.post<Poste>(`/postes/${posteId}/desactiver`);
  return data;
}

export async function reactiverPoste(posteId: string): Promise<Poste> {
  const { data } = await apiClient.post<Poste>(`/postes/${posteId}/reactiver`);
  return data;
}

export async function supprimerPoste(posteId: string): Promise<void> {
  await apiClient.delete(`/postes/${posteId}`);
}

export async function affecterInterimaire(posteId: string, utilisateur_id: string): Promise<Poste> {
  const { data } = await apiClient.post<Poste>(`/postes/${posteId}/interimaire`, { utilisateur_id });
  return data;
}

export async function affecterDelegation(posteId: string, utilisateur_id: string): Promise<Poste> {
  const { data } = await apiClient.post<Poste>(`/postes/${posteId}/delegation`, { utilisateur_id });
  return data;
}
