import { useEffect, useState } from "react";
import apiClient from "../../api/client";
import { getPostes, creerPoste, affecterOccupant } from "../../api/postes";
import type { Poste, Utilisateur } from "../../types";

export default function PostesPage() {
  const [postes, setPostes] = useState<Poste[]>([]);
  const [utilisateurs, setUtilisateurs] = useState<Utilisateur[]>([]);
  const [loading, setLoading] = useState(true);

  // Formulaire nouveau poste
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [intitule, setIntitule] = useState("");

  // Affectation occupant
  const [affectPosteId, setAffectPosteId] = useState<string | null>(null);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [affectLoading, setAffectLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      getPostes(),
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

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const poste = await creerPoste({ intitule });
    setPostes((prev) => [...prev, poste]);
    setIntitule("");
    setShowCreateForm(false);
  }

  async function handleAffecter(e: React.FormEvent) {
    e.preventDefault();
    if (!affectPosteId) return;
    setAffectLoading(true);
    try {
      const updated = await affecterOccupant(affectPosteId, selectedUserId);
      setPostes((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      setAffectPosteId(null);
      setSelectedUserId("");
    } finally {
      setAffectLoading(false);
    }
  }

  async function handleLiberer(posteId: string) {
    const updated = await affecterOccupant(posteId, "");
    setPostes((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
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
              <th className="text-left px-4 py-3 font-medium text-gray-600">Occupant</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Niveau</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Statut</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {postes.map((p) => (
              <>
                <tr key={p.id} className="hover:bg-gray-50">
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
                    <span className={`w-2 h-2 rounded-full inline-block ${p.is_active ? "bg-green-500" : "bg-gray-300"}`} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => { setAffectPosteId(p.id); setSelectedUserId(p.occupant_user_id ?? ""); }}
                        className="text-xs px-2 py-1 border rounded-md text-primary hover:bg-blue-50"
                      >
                        {p.occupant_user_id ? "Changer" : "Affecter"}
                      </button>
                      {p.occupant_user_id && (
                        <button
                          onClick={() => handleLiberer(p.id)}
                          className="text-xs px-2 py-1 border rounded-md text-gray-500 hover:bg-gray-50"
                        >
                          Libérer
                        </button>
                      )}
                    </div>
                  </td>
                </tr>

                {/* Inline affectation form */}
                {affectPosteId === p.id && (
                  <tr key={`affect-${p.id}`} className="bg-blue-50">
                    <td colSpan={5} className="px-4 py-3">
                      <form onSubmit={handleAffecter} className="flex gap-3 items-end">
                        <div className="flex-1">
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Affecter à « {p.intitule} »
                          </label>
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
                          disabled={affectLoading || !selectedUserId}
                          className="px-4 py-2 bg-primary text-white rounded-lg text-sm disabled:opacity-50"
                        >
                          {affectLoading ? "…" : "Confirmer"}
                        </button>
                        <button
                          type="button"
                          onClick={() => setAffectPosteId(null)}
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
