import apiClient from "./client";
import type { Flux } from "../types";

export interface LaneDetecte {
  lane_id: string;
  lane_name: string;
  taches: string[];
  type_action_propose: "distribution" | "visa" | "signature" | "information";
}

export interface BpmnAnalyse {
  nom_processus: string;
  lanes: LaneDetecte[];
  ordre_lanes: string[];
  bpmn_source: string;
  avertissements: string[];
}

export interface MappingLane {
  lane_id: string;
  poste_id: string;
  type_action: string;
}

export async function analyserBpmn(file: File): Promise<BpmnAnalyse> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<BpmnAnalyse>("/bpmn/analyser", form);
  return data;
}

export async function genererFlux(payload: {
  nom: string;
  description?: string;
  bpmn_source: string;
  mapping: MappingLane[];
  ordre_lanes: string[];
}): Promise<Flux> {
  const { data } = await apiClient.post<Flux>("/bpmn/generer", payload);
  return data;
}
