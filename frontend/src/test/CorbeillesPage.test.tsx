import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import CorbeillesPage from "../pages/user/CorbeillesPage";
import type { Courrier } from "../types";

vi.mock("../api/courriers", () => ({
  getMesCorbeilles: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return { ...actual, useNavigate: () => vi.fn() };
});

import { getMesCorbeilles } from "../api/courriers";

const now = new Date();
const past = new Date(now.getTime() - 24 * 3600 * 1000).toISOString();
const in24h = new Date(now.getTime() + 24 * 3600 * 1000).toISOString();
const in72h = new Date(now.getTime() + 72 * 3600 * 1000).toISOString();

const makeCourrier = (overrides: Partial<Courrier>): Courrier => ({
  id: "c1",
  reference: "ARR-2026-001",
  objet: "Courrier de test",
  expediteur: "Expéditeur Test",
  type: "arrivee",
  priorite: "normal",
  etat: "en_attente",
  date_reception: new Date().toISOString(),
  date_limite: null,
  poste_destinataire_id: "p1",
  confidentialite: "normal",
  type_action_courante: null,
  flux_id: null,
  etape_courante_id: null,
  created_by_id: "u1",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

function renderCorbeilles() {
  return render(
    <MemoryRouter>
      <CorbeillesPage />
    </MemoryRouter>
  );
}

describe("CorbeillesPage", () => {
  beforeEach(() => {
    vi.mocked(getMesCorbeilles).mockResolvedValue([]);
  });

  it("affiche un état vide quand aucun courrier", async () => {
    renderCorbeilles();
    await waitFor(() => expect(screen.getByText(/aucun courrier/i)).toBeInTheDocument());
  });

  it("affiche les courriers avec objet et référence", async () => {
    vi.mocked(getMesCorbeilles).mockResolvedValue([
      makeCourrier({ objet: "Note de service", reference: "ARR-2026-042" }),
    ]);
    renderCorbeilles();
    await waitFor(() => expect(screen.getByText("Note de service")).toBeInTheDocument());
    expect(screen.getByText(/ARR-2026-042/)).toBeInTheDocument();
  });

  it("affiche le badge RETARD sur les courriers en retard", async () => {
    vi.mocked(getMesCorbeilles).mockResolvedValue([
      makeCourrier({ date_limite: past, etat: "en_cours" }),
    ]);
    renderCorbeilles();
    // Le badge sur la carte contient exactement "⚠ RETARD"
    await waitFor(() =>
      expect(screen.getByText(/⚠ RETARD/)).toBeInTheDocument()
    );
  });

  it("affiche le badge URGENT pour les échéances dans moins de 48h", async () => {
    vi.mocked(getMesCorbeilles).mockResolvedValue([
      makeCourrier({ date_limite: in24h, etat: "en_attente" }),
    ]);
    renderCorbeilles();
    await waitFor(() => expect(screen.getByText(/⏱ URGENT/)).toBeInTheDocument());
  });

  it("n'affiche pas de badge SLA si l'échéance est dans plus de 48h", async () => {
    vi.mocked(getMesCorbeilles).mockResolvedValue([
      makeCourrier({ date_limite: in72h, etat: "en_attente" }),
    ]);
    renderCorbeilles();
    await waitFor(() => expect(screen.getByText("Courrier de test")).toBeInTheDocument());
    expect(screen.queryByText(/⚠ RETARD/)).not.toBeInTheDocument();
    expect(screen.queryByText(/⏱ URGENT/)).not.toBeInTheDocument();
  });

  it("affiche la bannière d'alerte si des courriers sont en retard", async () => {
    vi.mocked(getMesCorbeilles).mockResolvedValue([
      makeCourrier({ date_limite: past, etat: "en_cours" }),
    ]);
    renderCorbeilles();
    // La bannière rouge contient "1 courrier en retard"
    await waitFor(() => {
      const banners = document.querySelectorAll(".bg-red-50");
      const found = Array.from(banners).some((b) =>
        b.textContent?.includes("1 courrier") && b.textContent?.includes("en retard")
      );
      expect(found).toBe(true);
    });
  });

  it("filtre les onglets et rappelle l'API avec le bon état", async () => {
    renderCorbeilles();
    await waitFor(() => screen.getByText("À traiter"));

    await userEvent.click(screen.getByText("À traiter"));
    expect(getMesCorbeilles).toHaveBeenCalledWith("en_attente", undefined);
  });

  it("filtre l'onglet Pour information avec type_action=information", async () => {
    renderCorbeilles();
    await waitFor(() => screen.getByText("Pour information"));

    await userEvent.click(screen.getByText("Pour information"));
    expect(getMesCorbeilles).toHaveBeenCalledWith(undefined, "information");
  });
});
