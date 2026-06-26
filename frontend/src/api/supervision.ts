import apiClient from "./client";

export interface StatDirection {
  direction_id: string;
  nom: string;
  total: number;
  en_attente: number;
  en_cours: number;
  traites: number;
  en_retard: number;
}

export interface EtapeActive {
  ordre: number;
  type_action: string;
  intitule_poste: string;
  nb_courriers: number;
}

export interface CircuitActif {
  flux_id: string;
  flux_nom: string;
  total_en_cours: number;
  etapes: EtapeActive[];
}

export interface SupervisionData {
  par_direction: StatDirection[];
  circuits_actifs: CircuitActif[];
}

export async function getSupervision(): Promise<SupervisionData> {
  const { data } = await apiClient.get<SupervisionData>("/admin/supervision");
  return data;
}
