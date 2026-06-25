import type { Courrier } from "../types";

export type SlaStatus = "retard" | "proche" | null;

export function slaStatus(c: Pick<Courrier, "date_limite" | "etat">): SlaStatus {
  if (!c.date_limite || c.etat === "traite" || c.etat === "archive") return null;
  const now = Date.now();
  const limite = new Date(c.date_limite).getTime();
  if (limite < now) return "retard";
  if (limite - now < 48 * 3600 * 1000) return "proche";
  return null;
}
