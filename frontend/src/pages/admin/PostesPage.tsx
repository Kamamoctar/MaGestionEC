import { useEffect, useState } from "react";
import { getPostes, creerPoste, affecterOccupant } from "../../api/postes";
import type { Poste } from "../../types";

export default function PostesPage() {
  const [postes, setPostes] = useState<Poste[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [intitule, setIntitule] = useState("");

  useEffect(() => {
    getPostes().then(setPostes).finally(() => setLoading(false));
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const poste = await creerPoste({ intitule });
    setPostes((prev) => [...prev, poste]);
    setIntitule("");
    setShowForm(false);
  }

  if (loading) return <div className="text-gray-400">Chargement…</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-800">Postes</h1>
        <button
          onClick={() => setShowForm(true)}
          className="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-dark"
        >
          + Nouveau poste
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="mb-6 flex gap-3">
          <input
            value={intitule}
            onChange={(e) => setIntitule(e.target.value)}
            placeholder="Intitulé du poste"
            required
            className="border rounded-lg px-3 py-2 flex-1 focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button type="submit" className="bg-primary text-white px-4 py-2 rounded-lg text-sm">Créer</button>
          <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-sm text-gray-500">Annuler</button>
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
            </tr>
          </thead>
          <tbody className="divide-y">
            {postes.map((p) => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{p.intitule}</td>
                <td className="px-4 py-3 text-gray-500">{p.occupant_user_id ?? "—"}</td>
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
              </tr>
            ))}
            {postes.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">Aucun poste créé</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
