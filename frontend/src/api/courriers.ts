import apiClient from "./client";
import type { Courrier, CourrierLiaison } from "../types";

export async function getMesCorbeilles(etat?: string, type_action?: string): Promise<Courrier[]> {
  const params: Record<string, string> = {};
  if (etat) params.etat = etat;
  if (type_action) params.type_action = type_action;
  const { data } = await apiClient.get<Courrier[]>("/courriers/mes-corbeilles", { params });
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

export async function archiverCourrier(id: string): Promise<Courrier> {
  const { data } = await apiClient.post<Courrier>(`/courriers/${id}/archiver`);
  return data;
}

export type ActionParapheur = "visa" | "signature" | "annotation" | "retour";

export async function actionParapheur(id: string, action: ActionParapheur, commentaire?: string): Promise<Courrier> {
  const { data } = await apiClient.post<Courrier>(`/courriers/${id}/action`, { action, commentaire });
  return data;
}

export interface LiaisonsResponse {
  parent: CourrierLiaison | null;
  reponses: CourrierLiaison[];
}

export async function getLiaisons(id: string): Promise<LiaisonsResponse> {
  const { data } = await apiClient.get<LiaisonsResponse>(`/courriers/${id}/liaisons`);
  return data;
}
