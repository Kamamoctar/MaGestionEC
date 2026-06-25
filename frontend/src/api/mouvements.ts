import apiClient from "./client";

export interface Mouvement {
  id: string;
  action: string;
  poste_source_id: string | null;
  poste_destination_id: string | null;
  utilisateur_id: string;
  commentaire: string | null;
  created_at: string;
}

export async function getHistoriqueMouvements(courrierId: string): Promise<Mouvement[]> {
  const { data } = await apiClient.get<Mouvement[]>(`/courriers/${courrierId}/historique`);
  return data;
}
