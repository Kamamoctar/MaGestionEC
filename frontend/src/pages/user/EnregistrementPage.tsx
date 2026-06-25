import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { creerCourrier } from "../../api/courriers";
import { getPostes } from "../../api/postes";
import { getFlux } from "../../api/flux";
import type { Poste, Flux } from "../../types";

export default function EnregistrementPage() {
  const navigate = useNavigate();
  const [postes, setPostes] = useState<Poste[]>([]);
  const [circuits, setCircuits] = useState<Flux[]>([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    objet: "",
    expediteur: "",
    poste_destinataire_id: "",
    type: "arrivee" as "arrivee" | "depart" | "interne",
    priorite: "normal" as "normal" | "urgent" | "tres_urgent",
    confidentialite: "normal" as "normal" | "confidentiel",
    date_limite: "",
    flux_id: "" as string,
  });

  useEffect(() => {
    Promise.all([getPostes(), getFlux()]).then(([ps, fx]) => {
      setPostes(ps);
      setCircuits(fx);
    });
  }, []);

  function set(field: string, value: string) {
    setForm((prev) => {
      const next = { ...prev, [field]: value };
      // Quand un circuit est sélectionné, le poste destinataire est géré automatiquement
      if (field === "flux_id") next.poste_destinataire_id = "";
      return next;
    });
  }

  const selectedFlux = circuits.find((f) => f.id === form.flux_id);
  const premiereEtape = selectedFlux?.etapes.slice().sort((a, b) => a.ordre - b.ordre)[0];

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const payload: Record<string, unknown> = {
        objet: form.objet,
        expediteur: form.expediteur,
        type: form.type,
        priorite: form.priorite,
        confidentialite: form.confidentialite,
        date_limite: form.date_limite ? new Date(form.date_limite).toISOString() : null,
      };
      if (form.flux_id) {
        payload.flux_id = form.flux_id;
        // poste_destinataire_id sera déduit de la première étape côté backend
        payload.poste_destinataire_id = form.poste_destinataire_id || "placeholder";
      } else {
        payload.poste_destinataire_id = form.poste_destinataire_id;
      }
      await creerCourrier(payload as Parameters<typeof creerCourrier>[0]);
      navigate("/app/corbeilles");
    } finally {
      setLoading(false);
    }
  }

  const needsPoste = !form.flux_id;
  const canSubmit = form.objet && form.expediteur && (form.flux_id || form.poste_destinataire_id);

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-semibold text-gray-800 mb-6">Enregistrement express</h1>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border p-6 space-y-5">
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Objet *</label>
            <input
              value={form.objet}
              onChange={(e) => set("objet", e.target.value)}
              required
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Expéditeur *</label>
            <input
              value={form.expediteur}
              onChange={(e) => set("expediteur", e.target.value)}
              required
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {/* Circuit de traitement (optionnel) */}
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Circuit de traitement
              <span className="ml-1 text-xs text-gray-400 font-normal">(optionnel — définit le routage automatique)</span>
            </label>
            <select
              value={form.flux_id}
              onChange={(e) => set("flux_id", e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Aucun circuit — transmission manuelle</option>
              {circuits.map((f) => (
                <option key={f.id} value={f.id}>{f.nom}</option>
              ))}
            </select>
            {premiereEtape && (
              <p className="mt-1.5 text-xs text-blue-600">
                → Première étape : <strong>{premiereEtape.type_action}</strong> —
                le courrier sera dirigé automatiquement vers le poste associé
              </p>
            )}
          </div>

          {/* Poste destinataire — affiché uniquement si pas de circuit */}
          {needsPoste && (
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Poste destinataire *</label>
              <select
                value={form.poste_destinataire_id}
                onChange={(e) => set("poste_destinataire_id", e.target.value)}
                required
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">Choisir un poste…</option>
                {postes.map((p) => (
                  <option key={p.id} value={p.id}>{p.intitule}</option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select value={form.type} onChange={(e) => set("type", e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
              <option value="arrivee">Arrivée</option>
              <option value="depart">Départ</option>
              <option value="interne">Interne</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priorité</label>
            <select value={form.priorite} onChange={(e) => set("priorite", e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
              <option value="normal">Normal</option>
              <option value="urgent">Urgent</option>
              <option value="tres_urgent">Très urgent</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confidentialité</label>
            <select value={form.confidentialite} onChange={(e) => set("confidentialite", e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
              <option value="normal">Normal</option>
              <option value="confidentiel">Confidentiel</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Date limite (optionnel)</label>
            <input
              type="date"
              value={form.date_limite}
              onChange={(e) => set("date_limite", e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={loading || !canSubmit}
            className="px-5 py-2 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary-dark"
          >
            {loading ? "Enregistrement…" : "Enregistrer le courrier"}
          </button>
          <button type="button" onClick={() => navigate(-1)} className="px-4 py-2 text-sm text-gray-500">
            Annuler
          </button>
        </div>
      </form>
    </div>
  );
}
