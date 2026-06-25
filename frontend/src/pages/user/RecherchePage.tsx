import { useState } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../../api/client";
import type { Courrier } from "../../types";

const ETAT_LABELS: Record<string, string> = {
  en_attente: "En attente", en_cours: "En cours", traite: "Traité", archive: "Archivé",
};
const ETAT_COLORS: Record<string, string> = {
  en_attente: "bg-orange-100 text-orange-700",
  en_cours: "bg-blue-100 text-blue-700",
  traite: "bg-green-100 text-green-700",
  archive: "bg-gray-100 text-gray-500",
};
const PRIORITE_COLORS: Record<string, string> = {
  normal: "bg-gray-100 text-gray-600",
  urgent: "bg-orange-100 text-orange-700",
  tres_urgent: "bg-red-100 text-red-700",
};

export default function RecherchePage() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [type, setType] = useState("");
  const [etat, setEtat] = useState("");
  const [priorite, setPriorite] = useState("");
  const [dateDebut, setDateDebut] = useState("");
  const [dateFin, setDateFin] = useState("");
  const [resultats, setResultats] = useState<Courrier[] | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleRecherche(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (q) params.q = q;
      if (type) params.type = type;
      if (etat) params.etat = etat;
      if (priorite) params.priorite = priorite;
      if (dateDebut) params.date_debut = new Date(dateDebut).toISOString();
      if (dateFin) params.date_fin = new Date(dateFin + "T23:59:59").toISOString();
      const { data } = await apiClient.get<Courrier[]>("/recherche/courriers", { params });
      setResultats(data);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setQ(""); setType(""); setEtat(""); setPriorite(""); setDateDebut(""); setDateFin("");
    setResultats(null);
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-xl font-semibold text-gray-800 mb-6">Recherche de courriers</h1>

      <form onSubmit={handleRecherche} className="bg-white rounded-xl border p-5 mb-6 space-y-4">
        {/* Texte libre */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Texte libre</label>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Objet, expéditeur, référence…"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* Filtres */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
            <select value={type} onChange={(e) => setType(e.target.value)}
              className="w-full border rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
              <option value="">Tous</option>
              <option value="arrivee">Arrivée</option>
              <option value="depart">Départ</option>
              <option value="interne">Interne</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">État</label>
            <select value={etat} onChange={(e) => setEtat(e.target.value)}
              className="w-full border rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
              <option value="">Tous</option>
              <option value="en_attente">En attente</option>
              <option value="en_cours">En cours</option>
              <option value="traite">Traité</option>
              <option value="archive">Archivé</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Priorité</label>
            <select value={priorite} onChange={(e) => setPriorite(e.target.value)}
              className="w-full border rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
              <option value="">Toutes</option>
              <option value="normal">Normal</option>
              <option value="urgent">Urgent</option>
              <option value="tres_urgent">Très urgent</option>
            </select>
          </div>
          <div>
            {/* spacer */}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Reçu depuis</label>
            <input type="date" value={dateDebut} onChange={(e) => setDateDebut(e.target.value)}
              className="w-full border rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Reçu jusqu'au</label>
            <input type="date" value={dateFin} onChange={(e) => setDateFin(e.target.value)}
              className="w-full border rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
          </div>
        </div>

        <div className="flex gap-3">
          <button type="submit" disabled={loading || (!q && !type && !etat && !priorite && !dateDebut && !dateFin)}
            className="px-5 py-2 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50">
            {loading ? "Recherche…" : "Rechercher"}
          </button>
          {resultats !== null && (
            <button type="button" onClick={handleReset}
              className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700">
              Réinitialiser
            </button>
          )}
        </div>
      </form>

      {/* Résultats */}
      {resultats !== null && (
        <div className="bg-white rounded-xl border overflow-hidden">
          <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">
              {resultats.length} résultat{resultats.length !== 1 ? "s" : ""}
            </span>
          </div>

          {resultats.length === 0 ? (
            <div className="px-4 py-10 text-center text-gray-400 text-sm">
              Aucun courrier ne correspond à ces critères.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-2 font-medium text-gray-600 w-32">Référence</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Objet</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Expéditeur</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Date</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">État</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Priorité</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {resultats.map((c) => (
                  <tr
                    key={c.id}
                    onClick={() => navigate(`/app/courriers/${c.id}`)}
                    className="hover:bg-blue-50 cursor-pointer"
                  >
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{c.reference}</td>
                    <td className="px-4 py-3 font-medium text-gray-800 max-w-xs truncate">{c.objet}</td>
                    <td className="px-4 py-3 text-gray-600">{c.expediteur}</td>
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {new Date(c.date_reception).toLocaleDateString("fr-FR")}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ETAT_COLORS[c.etat] ?? ""}`}>
                        {ETAT_LABELS[c.etat] ?? c.etat}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PRIORITE_COLORS[c.priorite] ?? ""}`}>
                        {c.priorite.replace("_", " ")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
