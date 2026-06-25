import apiClient from "./client";
import type { Flux } from "../types";

export async function getFlux(): Promise<Flux[]> {
  const { data } = await apiClient.get<Flux[]>("/flux");
  return data;
}
