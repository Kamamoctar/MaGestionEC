import apiClient from "./client";
import type { Tenant } from "../types";

export async function getTenants(): Promise<Tenant[]> {
  const { data } = await apiClient.get<Tenant[]>("/tenants");
  return data;
}

export async function getTenantCourant(): Promise<Tenant> {
  const { data } = await apiClient.get<Tenant>("/tenants/me");
  return data;
}
