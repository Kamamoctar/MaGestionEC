import apiClient from "./client";
import type { Courrier } from "../types";

export async function getMesCorbeilles(etat?: string): Promise<Courrier[]> {
  const { data } = await apiClient.get<Courrier[]>("/courriers/mes-corbeilles", {
    params: etat ? { etat } : {},
  });
  return data;
}

export async function getCourrier(id: string): Promise<Courrier> {
  const { data } = await apiClient.get<Courrier>(`/courriers/${id}`);
  return data;
}

export async function creerCourrier(payload: Partial<Courrier>): Promise<Courrier> {
  const { data } = await apiClient.post<Courrier>("/courriers", payload);
  return data;
}

export async function transmettreCourrier(id: string, poste_destination_id: string, commentaire?: string): Promise<Courrier> {
  const { data } = await apiClient.post<Courrier>(`/courriers/${id}/transmettre`, {
    poste_destination_id,
    commentaire,
  });
  return data;
}
