import { useEffect, useState } from "react";
import { getDirections, creerDirection, modifierDirection, supprimerDirection } from "../../api/directions";
import type { Direction } from "../../types";

export default function DirectionsPage() {
  const [directions, setDirections] = useState<Direction[]>([]);
  const [loading, setLoading] = useState(true);

  // Création
  const [showCreate, setShowCreate] = useState(false);
  const [nom, setNom] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Édition inline
  const [editId, setEditId] = useState<string | null>(null);
  const [editNom, setEditNom] = useState("");
  const [editDesc, setEditDesc] = useState("");

  useEffect(() => {
    getDirections().then(setDirections).finally(() => setLoading(false));
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const d = await creerDirection({ nom, description: description || undefined });
      setDirections((prev) => [...prev, d]);
      setNom(""); setDescription(""); setShowCreate(false);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!editId) return;
    const d = await modifierDirection(editId, { nom: editNom, description: editDesc || undefined });
    setDirections((prev) => prev.map((x) => (x.id === d.id ? d : x)));
    setEditId(null);
  }

  async function handleDelete(id: string, nom: string) {
    if (!confirm(`Supprimer la direction « ${nom} » ?`)) return;
    await supprimerDirection(id);
    setDirections((prev) => prev.filter((d) => d.id !== id));
  }

  function startEdit(d: Direction) {
    setEditId(d.id);
    setEditNom(d.nom);
    setEditDesc(d.description ?? "");
  }

  if (loading) return <div className="text-gray-400">Chargement…</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-800">Directions</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-dark"
        >
          + Nouvelle direction
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="mb-6 bg-white rounded-xl border p-5 space-y-3">
          <h2 className="font-medium text-gray-700">Nouvelle direction</h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Nom *</label>
              <input value={nom} onChange={(e) => setNom(e.target.value)} required placeholder="ex : Direction Générale"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
              <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optionnel"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={submitting}
              className="px-5 py-2 bg-primary text-white rounded-lg text-sm disabled:opacity-50">
              {submitting ? "Création…" : "Créer"}
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-gray-500">Annuler</button>
          </div>
        </form>
      )}

      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Nom</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Description</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {directions.map((d) => (
              <>
                <tr key={d.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{d.nom}</td>
                  <td className="px-4 py-3 text-gray-500">{d.description ?? <span className="italic">—</span>}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button onClick={() => startEdit(d)}
                        className="text-xs px-2 py-1 border rounded-md text-primary hover:bg-blue-50">
                        Modifier
                      </button>
                      <button onClick={() => handleDelete(d.id, d.nom)}
                        className="text-xs px-2 py-1 border rounded-md text-red-500 hover:bg-red-50">
                        Supprimer
                      </button>
                    </div>
                  </td>
                </tr>
                {editId === d.id && (
                  <tr key={`edit-${d.id}`} className="bg-blue-50">
                    <td colSpan={3} className="px-4 py-3">
                      <form onSubmit={handleEdit} className="flex gap-3 items-end">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Nom *</label>
                          <input value={editNom} onChange={(e) => setEditNom(e.target.value)} required
                            className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white w-48" />
                        </div>
                        <div className="flex-1">
                          <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
                          <input value={editDesc} onChange={(e) => setEditDesc(e.target.value)}
                            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-white" />
                        </div>
                        <button type="submit" className="px-4 py-2 bg-primary text-white rounded-lg text-sm">Enregistrer</button>
                        <button type="button" onClick={() => setEditId(null)} className="px-3 py-2 text-sm text-gray-500">Annuler</button>
                      </form>
                    </td>
                  </tr>
                )}
              </>
            ))}
            {directions.length === 0 && (
              <tr><td colSpan={3} className="px-4 py-8 text-center text-gray-400">Aucune direction créée</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
