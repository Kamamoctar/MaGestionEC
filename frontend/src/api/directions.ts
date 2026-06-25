import apiClient from "./client";
import type { Direction } from "../types";

export async function getDirections(): Promise<Direction[]> {
  const { data } = await apiClient.get<Direction[]>("/directions");
  return data;
}

export async function creerDirection(payload: { nom: string; description?: string }): Promise<Direction> {
  const { data } = await apiClient.post<Direction>("/directions", payload);
  return data;
}

export async function modifierDirection(id: string, payload: { nom?: string; description?: string }): Promise<Direction> {
  const { data } = await apiClient.patch<Direction>(`/directions/${id}`, payload);
  return data;
}

export async function supprimerDirection(id: string): Promise<void> {
  await apiClient.delete(`/directions/${id}`);
}
