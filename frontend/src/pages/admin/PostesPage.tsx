import { useEffect, useState } from "react";
import apiClient from "../../api/client";
import {
  getPostes,
  creerPoste,
  affecterOccupant,
  libererOccupant,
  desactiverPoste,
  reactiverPoste,
  supprimerPoste,
  affecterInterimaire,
  affecterDelegation,
} from "../../api/postes";
import type { Poste, Utilisateur } from "../../types";

type PanelMode = "affecter" | "interimaire" | "delegation" | null;

export default function PostesPage() {
  const [postes, setPostes] = useState<Poste[]>([]);
  const [utilisateurs, setUtilisateurs] = useState<Utilisateur[]>([]);
  const [loading, setLoading] = useState(true);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [intitule, setIntitule] = useState("");

  // Panel inline : quel poste + quel mode
  const [panelPosteId, setPanelPosteId] = useState<string | null>(null);
  const [panelMode, setPanelMode] = useState<PanelMode>(null);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [panelLoading, setPanelLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      getPostes(true),
      apiClient.get<Utilisateur[]>("/utilisateurs").then((r) => r.data),
    ]).then(([ps, us]) => {
      setPostes(ps);
      setUtilisateurs(us);
    }).finally(() => setLoading(false));
  }, []);

  function nomUtilisateur(id: string | null): string {
    if (!id) return "—";
    const u = utilisateurs.find((u) => u.id === id);
    return u ? `${u.prenom} ${u.nom}` : id.slice(0, 8) + "…";
  }

  function openPanel(posteId: string, mode: PanelMode, currentUserId?: string | null) {
    setPanelPosteId(posteId);
    setPanelMode(mode);
    setSelectedUserId(mode === "affecter" ? (currentUserId ?? "") : "");
  }

  function closePanel() {
    setPanelPosteId(null);
    setPanelMode(null);
    setSelectedUserId("");
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const poste = await creerPoste({ intitule });
    setPostes((prev) => [...prev, poste]);
    setIntitule("");
    setShowCreateForm(false);
  }

  async function handlePanelSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!panelPosteId || !selectedUserId) return;
    setPanelLoading(true);
    try {
      let updated: Poste;
      if (panelMode === "affecter") {
        updated = await affecterOccupant(panelPosteId, selectedUserId);
      } else if (panelMode === "interimaire") {
        updated = await affecterInterimaire(panelPosteId, selectedUserId);
      } else {
        updated = await affecterDelegation(panelPosteId, selectedUserId);
      }
      setPostes((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      closePanel();
    } finally {
      setPanelLoading(false);
    }
  }

  async function handleLiberer(posteId: string) {
    if (!confirm("Libérer ce poste (retirer l'occupant titulaire) ?")) return;
    const updated = await libererOccupant(posteId);
    setPostes((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
  }

  async function handleDesactiver(poste: Poste) {
    if (!confirm(`Désactiver le poste « ${poste.intitule} » ?`)) return;
    try {
      const updated = await desactiverPoste(poste.id);
      setPostes((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      closePanel();
    } catch (e: any) {
      alert(e?.response?.data?.detail ?? "Impossible de désactiver ce poste.");
    }
  }

  async function handleReactiver(poste: Poste) {
    const updated = await reactiverPoste(poste.id);
    setPostes((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
  }

  async function handleSupprimer(poste: Poste) {
    if (!confirm(`Supprimer définitivement le poste « ${poste.intitule} » ?`)) return;
    try {
      await supprimerPoste(poste.id);
      setPostes((prev) => prev.filter((p) => p.id !== poste.id));
      closePanel();
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (detail?.blocages) {
        alert(`${detail.message}\n\nRéférences trouvées :\n- ${detail.blocages.join("\n- ")}`);
      } else {
        alert(detail ?? "Suppression impossible.");
      }
    }
  }

  if (loading) return <div className="text-gray-400">Chargement…</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-800">Postes</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-dark"
        >
          + Nouveau poste
        </button>
      </div>

      {showCreateForm && (
        <form onSubmit={handleCreate} className="mb-6 flex gap-3 bg-white p-4 rounded-xl border">
          <input
            value={intitule}
            onChange={(e) => setIntitule(e.target.value)}
            placeholder="Intitulé du poste (ex : Directeur Général)"
            required
            className="border rounded-lg px-3 py-2 flex-1 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button type="submit" className="bg-primary text-white px-4 py-2 rounded-lg text-sm">Créer</button>
          <button type="button" onClick={() => setShowCreateForm(false)} className="px-4 py-2 text-sm text-gray-500">Annuler</button>
        </form>
      )}

      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Intitulé</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Occupant titulaire</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Niveau</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Statut</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {postes.map((p) => (
              <>
                <tr key={p.id} className={`hover:bg-gray-50 ${!p.is_active ? "bg-gray-50 text-gray-500" : ""}`}>
                  <td className="px-4 py-3 font-medium">{p.intitule}</td>
                  <td className="px-4 py-3">
                    {p.occupant_user_id ? (
                      <span className="inline-flex items-center gap-1.5">
                        <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs flex items-center justify-center font-bold">
                          {nomUtilisateur(p.occupant_user_id).charAt(0)}
                        </span>
                        <span className="text-gray-700">{nomUtilisateur(p.occupant_user_id)}</span>
                      </span>
                    ) : (
                      <span className="text-gray-400 italic">Vacant</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      p.niveau_acces === "confidentiel" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"
                    }`}>
                      {p.niveau_acces}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${p.is_active ? "text-green-600" : "text-gray-400"}`}>
                      <span className={`w-2 h-2 rounded-full inline-block ${p.is_active ? "bg-green-500" : "bg-gray-300"}`} />
                      {p.is_active ? "Actif" : "Désactivé"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2 flex-wrap">
                      <button
                        onClick={() => openPanel(p.id, "affecter", p.occupant_user_id)}
                        disabled={!p.is_active}
                        className="text-xs px-2 py-1 border rounded-md text-primary hover:bg-blue-50 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {p.occupant_user_id ? "Changer" : "Affecter"}
                      </button>
                      <button
                        onClick={() => openPanel(p.id, "interimaire")}
                        disabled={!p.is_active}
                        className="text-xs px-2 py-1 border rounded-md text-purple-600 hover:bg-purple-50 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Intérim
                      </button>
                      <button
                        onClick={() => openPanel(p.id, "delegation")}
                        disabled={!p.is_active}
                        className="text-xs px-2 py-1 border rounded-md text-amber-600 hover:bg-amber-50 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Déléguer
                      </button>
                      {p.occupant_user_id && (
                        <button
                          onClick={() => handleLiberer(p.id)}
                          className="text-xs px-2 py-1 border rounded-md text-gray-500 hover:bg-gray-50"
                        >
                          Libérer
                        </button>
                      )}
                      {p.is_active ? (
                        <button
                          onClick={() => handleDesactiver(p)}
                          className="text-xs px-2 py-1 border rounded-md text-gray-600 hover:bg-gray-50"
                        >
                          Désactiver
                        </button>
                      ) : (
                        <button
                          onClick={() => handleReactiver(p)}
                          className="text-xs px-2 py-1 border rounded-md text-green-600 hover:bg-green-50"
                        >
                          Réactiver
                        </button>
                      )}
                      <button
                        onClick={() => handleSupprimer(p)}
                        className="text-xs px-2 py-1 border rounded-md text-red-500 hover:bg-red-50"
                      >
                        Supprimer
                      </button>
                    </div>
                  </td>
                </tr>

                {/* Panel inline */}
                {panelPosteId === p.id && panelMode !== null && (
                  <tr key={`panel-${p.id}`} className={
                    panelMode === "interimaire" ? "bg-purple-50" :
                    panelMode === "delegation" ? "bg-amber-50" : "bg-blue-50"
                  }>
                    <td colSpan={5} className="px-4 py-3">
                      <form onSubmit={handlePanelSubmit} className="flex gap-3 items-end">
                        <div className="flex-1">
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            {panelMode === "interimaire"
                              ? `Désigner un intérimaire pour « ${p.intitule} »`
                              : panelMode === "delegation"
                              ? `Déléguer les droits de « ${p.intitule} »`
                              : `Affecter un titulaire à « ${p.intitule} »`}
                          </label>
                          {panelMode === "interimaire" && (
                            <p className="text-xs text-purple-600 mb-2">
                              L'intérimaire hérite temporairement des courriers et droits de ce poste.
                            </p>
                          )}
                          {panelMode === "delegation" && (
                            <p className="text-xs text-amber-600 mb-2">
                              Le titulaire reste en place. La délégation donne accès temporairement aux courriers du poste à la personne désignée.
                            </p>
                          )}
                          <select
                            value={selectedUserId}
                            onChange={(e) => setSelectedUserId(e.target.value)}
                            required
                            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white"
                          >
                            <option value="">Choisir un utilisateur…</option>
                            {utilisateurs.filter((u) => u.is_active).map((u) => (
                              <option key={u.id} value={u.id}>{u.prenom} {u.nom} — {u.email}</option>
                            ))}
                          </select>
                        </div>
                        <button
                          type="submit"
                          disabled={panelLoading || !selectedUserId}
                          className={`px-4 py-2 text-white rounded-lg text-sm disabled:opacity-50 ${
                            panelMode === "interimaire" ? "bg-purple-600" :
                            panelMode === "delegation" ? "bg-amber-600" : "bg-primary"
                          }`}
                        >
                          {panelLoading ? "…" : "Confirmer"}
                        </button>
                        <button
                          type="button"
                          onClick={closePanel}
                          className="px-3 py-2 text-sm text-gray-500"
                        >
                          Annuler
                        </button>
                      </form>
                    </td>
                  </tr>
                )}
              </>
            ))}
            {postes.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Aucun poste créé</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
