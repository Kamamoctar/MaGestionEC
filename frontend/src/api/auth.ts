import apiClient from "./client";
import type { Utilisateur } from "../types";

export interface LoginResponse {
  access_token: string;
  token_type: string;
  utilisateur: Utilisateur;
  tenant_id?: string | null;
  tenant_nom?: string | null;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const form = new URLSearchParams({ username: email, password });
  const { data } = await apiClient.post<LoginResponse>("/auth/token", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function getMe(): Promise<Utilisateur> {
  const { data } = await apiClient.get<Utilisateur>("/auth/me");
  return data;
}
