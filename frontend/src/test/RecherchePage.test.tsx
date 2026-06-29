import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import RecherchePage from "../pages/user/RecherchePage";
import type { Courrier } from "../types";

// Mock apiClient utilisé directement dans RecherchePage
vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
  },
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return { ...actual, useNavigate: () => vi.fn() };
});

import apiClient from "../api/client";

const fakeCourrier: Courrier = {
  id: "c99",
  reference: "DEP-2026-007",
  objet: "Rapport annuel",
  expediteur: "Direction RH",
  reference_expediteur: null,
  type: "depart",
  priorite: "urgent",
  etat: "en_cours",
  date_reception: "2026-05-01T08:00:00Z",
  date_limite: null,
  poste_destinataire_id: "p1",
  confidentialite: "normal",
  type_action_courante: null,
  flux_id: null,
  etape_courante_id: null,
  courrier_parent_id: null,
  dossier_id: null,
  created_by_id: "u1",
  created_at: "2026-05-01T08:00:00Z",
  updated_at: "2026-05-01T08:00:00Z",
};

function renderRecherche() {
  return render(
    <MemoryRouter>
      <RecherchePage />
    </MemoryRouter>
  );
}

describe("RecherchePage", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: [] });
  });

  it("le bouton Rechercher est désactivé sans critère", () => {
    renderRecherche();
    expect(screen.getByRole("button", { name: /rechercher/i })).toBeDisabled();
  });

  it("active le bouton quand un texte est saisi", async () => {
    renderRecherche();
    await userEvent.type(screen.getByPlaceholderText(/objet/i), "rapport");
    expect(screen.getByRole("button", { name: /rechercher/i })).not.toBeDisabled();
  });

  it("appelle l'API avec le paramètre q", async () => {
    renderRecherche();
    await userEvent.type(screen.getByPlaceholderText(/objet/i), "rapport");
    await userEvent.click(screen.getByRole("button", { name: /rechercher/i }));
    await waitFor(() =>
      expect(apiClient.get).toHaveBeenCalledWith(
        "/recherche/courriers",
        expect.objectContaining({ params: expect.objectContaining({ q: "rapport" }) })
      )
    );
  });

  it("affiche l'état vide si l'API retourne zéro résultat", async () => {
    renderRecherche();
    await userEvent.type(screen.getByPlaceholderText(/objet/i), "xyz");
    await userEvent.click(screen.getByRole("button", { name: /rechercher/i }));
    await waitFor(() => expect(screen.getByText(/aucun courrier/i)).toBeInTheDocument());
  });

  it("affiche le tableau des résultats quand l'API retourne des données", async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [fakeCourrier] });
    renderRecherche();
    await userEvent.type(screen.getByPlaceholderText(/objet/i), "rapport");
    await userEvent.click(screen.getByRole("button", { name: /rechercher/i }));
    await waitFor(() => expect(screen.getByText("Rapport annuel")).toBeInTheDocument());
    expect(screen.getByText("DEP-2026-007")).toBeInTheDocument();
    expect(screen.getByText("Direction RH")).toBeInTheDocument();
  });

  it("affiche le nombre de résultats", async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [fakeCourrier] });
    renderRecherche();
    await userEvent.type(screen.getByPlaceholderText(/objet/i), "rapport");
    await userEvent.click(screen.getByRole("button", { name: /rechercher/i }));
    await waitFor(() => expect(screen.getByText(/1 résultat/i)).toBeInTheDocument());
  });

  it("affiche le bouton Réinitialiser après une recherche", async () => {
    renderRecherche();
    await userEvent.type(screen.getByPlaceholderText(/objet/i), "rapport");
    await userEvent.click(screen.getByRole("button", { name: /rechercher/i }));
    await waitFor(() => expect(screen.getByText(/réinitialiser/i)).toBeInTheDocument());
  });
});
