import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import DashboardPage from "../pages/user/DashboardPage";

const mockStats = {
  total: 42,
  en_attente: 10,
  en_cours: 8,
  traites: 20,
  archives: 4,
  en_retard: 3,
  top_postes: [
    { intitule: "Secrétariat Général", total: 15, traites: 10, en_retard: 2 },
    { intitule: "Direction des RH", total: 8, traites: 5, en_retard: 0 },
  ],
};

vi.mock("../api/dashboard", () => ({
  getDashboardStats: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return { ...actual, useNavigate: () => vi.fn() };
});

import { getDashboardStats } from "../api/dashboard";

beforeEach(() => {
  vi.mocked(getDashboardStats).mockResolvedValue(mockStats);
});

function renderDashboard() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>
  );
}

describe("DashboardPage", () => {
  it("affiche la valeur totale", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("42")).toBeInTheDocument());
  });

  it("affiche le titre Tableau de bord", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("Tableau de bord")).toBeInTheDocument());
  });

  it("affiche le taux de traitement en pourcentage", async () => {
    renderDashboard();
    // 20/42 ≈ 48 %
    await waitFor(() => expect(screen.getByText(/48 % du total/i)).toBeInTheDocument());
  });

  it("affiche l'alerte retard dans le DOM quand en_retard > 0", async () => {
    renderDashboard();
    // L'alerte contient "3" et "en retard" mais dans des éléments séparés —
    // on teste le conteneur via textContent
    await waitFor(() => {
      const alerte = document.querySelector(".bg-red-50");
      expect(alerte?.textContent).toMatch(/3/);
      expect(alerte?.textContent).toMatch(/en retard/i);
    });
  });

  it("n'affiche pas de bannière rouge quand en_retard = 0", async () => {
    vi.mocked(getDashboardStats).mockResolvedValueOnce({ ...mockStats, en_retard: 0 });
    renderDashboard();
    await waitFor(() => expect(screen.getByText("42")).toBeInTheDocument());
    expect(document.querySelector(".bg-red-50")).not.toBeInTheDocument();
  });

  it("affiche les noms des postes dans le top postes", async () => {
    renderDashboard();
    await waitFor(() => expect(screen.getByText("Secrétariat Général")).toBeInTheDocument());
    expect(screen.getByText("Direction des RH")).toBeInTheDocument();
  });
});
