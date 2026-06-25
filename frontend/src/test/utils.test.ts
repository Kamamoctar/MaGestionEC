import { describe, it, expect } from "vitest";
import { formatTaille, iconeType } from "../api/piecesJointes";
import { slaStatus } from "../utils/sla";

// ── formatTaille ─────────────────────────────────────────────────────────────

describe("formatTaille", () => {
  it("affiche en octets sous 1 Ko", () => {
    expect(formatTaille(512)).toBe("512 o");
  });

  it("affiche en Ko entre 1 Ko et 1 Mo", () => {
    expect(formatTaille(2048)).toBe("2 Ko");
  });

  it("affiche en Mo au-dessus de 1 Mo", () => {
    expect(formatTaille(5 * 1024 * 1024)).toBe("5.0 Mo");
  });
});

// ── iconeType ─────────────────────────────────────────────────────────────────

describe("iconeType", () => {
  it("retourne 📄 pour PDF", () => {
    expect(iconeType("application/pdf")).toBe("📄");
  });

  it("retourne 📝 pour Word", () => {
    expect(iconeType("application/msword")).toBe("📝");
    expect(iconeType("application/vnd.openxmlformats-officedocument.wordprocessingml.document")).toBe("📝");
  });

  it("retourne 📊 pour Excel", () => {
    expect(iconeType("application/vnd.ms-excel")).toBe("📊");
  });

  it("retourne 🖼 pour les images", () => {
    expect(iconeType("image/png")).toBe("🖼");
    expect(iconeType("image/jpeg")).toBe("🖼");
  });

  it("retourne 📎 par défaut", () => {
    expect(iconeType("application/octet-stream")).toBe("📎");
  });
});

// ── slaStatus ─────────────────────────────────────────────────────────────────

describe("slaStatus", () => {
  const now = new Date();

  const past = new Date(now.getTime() - 24 * 3600 * 1000).toISOString();
  const in24h = new Date(now.getTime() + 24 * 3600 * 1000).toISOString();
  const in72h = new Date(now.getTime() + 72 * 3600 * 1000).toISOString();

  it("retourne 'retard' quand la date_limite est dépassée", () => {
    expect(slaStatus({ date_limite: past, etat: "en_cours" })).toBe("retard");
  });

  it("retourne 'proche' quand l'échéance est dans moins de 48h", () => {
    expect(slaStatus({ date_limite: in24h, etat: "en_attente" })).toBe("proche");
  });

  it("retourne null quand l'échéance est dans plus de 48h", () => {
    expect(slaStatus({ date_limite: in72h, etat: "en_cours" })).toBeNull();
  });

  it("retourne null si date_limite absent", () => {
    expect(slaStatus({ date_limite: null, etat: "en_cours" })).toBeNull();
  });

  it("retourne null si le courrier est traité, même si en retard", () => {
    expect(slaStatus({ date_limite: past, etat: "traite" })).toBeNull();
  });

  it("retourne null si le courrier est archivé", () => {
    expect(slaStatus({ date_limite: past, etat: "archive" })).toBeNull();
  });
});
