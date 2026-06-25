import { useEffect, useState } from "react";
import apiClient from "../../api/client";
import type { Utilisateur, RoleFonctionnel } from "../../types";

const ROLES: Record<string, string> = {
  admin: "Admin",
  secretariat: "Secrétariat",
  agent: "Agent",
  direction: "Direction",
};

const ROLE_COLORS: Record<string, string> = {
  admin: "bg-purple-100 text-purple-700",
  secretariat: "bg-blue-100 text-blue-700",
  agent: "bg-gray-100 text-gray-700",
  direction: "bg-orange-100 text-orange-700",
};

interface FormData {
  prenom: string;
  nom: string;
  email: string;
  password: string;
  role_fonctionnel: RoleFonctionnel;
}

const DEFAULT_FORM: FormData = { prenom: "", nom: "", email: "", password: "", role_fonctionnel: "agent" };

export default function UtilisateursPage() {
  const [utilisateurs, setUtilisateurs] = useState<Utilisateur[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FormData>(DEFAULT_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient.get<Utilisateur[]>("/utilisateurs")
      .then((r) => setUtilisateurs(r.data))
      .finally(() => setLoading(false));
  }, []);

  function setField(field: keyof FormData, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const { data } = await apiClient.post<Utilisateur>("/utilisateurs", form);
      setUtilisateurs((prev) => [...prev, data]);
      setForm(DEFAULT_FORM);
      setShowForm(false);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Erreur lors de la création");
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleActif(user: Utilisateur) {
    const { data } = await apiClient.patch<Utilisateur>(`/utilisateurs/${user.id}`, {
      is_active: !user.is_active,
    });
    setUtilisateurs((prev) => prev.map((u) => (u.id === data.id ? data : u)));
  }

  if (loading) return <div className="text-gray-400">Chargement…</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-800">Utilisateurs</h1>
        <button
          onClick={() => { setShowForm(true); setError(null); }}
          className="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-dark"
        >
          + Nouvel utilisateur
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="mb-6 bg-white rounded-xl border p-6 space-y-4">
          <h2 className="font-medium text-gray-700">Créer un utilisateur</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Prénom *</label>
              <input value={form.prenom} onChange={(e) => setField("prenom", e.target.value)} required
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Nom *</label>
              <input value={form.nom} onChange={(e) => setField("nom", e.target.value)} required
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Email *</label>
              <input type="email" value={form.email} onChange={(e) => setField("email", e.target.value)} required
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Mot de passe *</label>
              <input type="password" value={form.password} onChange={(e) => setField("password", e.target.value)} required
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Rôle *</label>
              <select value={form.role_fonctionnel} onChange={(e) => setField("role_fonctionnel", e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
                {Object.entries(ROLES).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex gap-3">
            <button type="submit" disabled={submitting}
              className="px-5 py-2 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50">
              {submitting ? "Création…" : "Créer l'utilisateur"}
            </button>
            <button type="button" onClick={() => { setShowForm(false); setError(null); }}
              className="px-4 py-2 text-sm text-gray-500">Annuler</button>
          </div>
        </form>
      )}

      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Nom</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Rôle</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Statut</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {utilisateurs.map((u) => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{u.prenom} {u.nom}</td>
                <td className="px-4 py-3 text-gray-500">{u.email}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ROLE_COLORS[u.role_fonctionnel] ?? "bg-gray-100 text-gray-600"}`}>
                    {ROLES[u.role_fonctionnel] ?? u.role_fonctionnel}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-medium ${u.is_active ? "text-green-600" : "text-gray-400"}`}>
                    {u.is_active ? "Actif" : "Inactif"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => toggleActif(u)}
                    className="text-xs px-2 py-1 border rounded-md text-gray-500 hover:bg-gray-50"
                  >
                    {u.is_active ? "Désactiver" : "Réactiver"}
                  </button>
                </td>
              </tr>
            ))}
            {utilisateurs.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Aucun utilisateur</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
