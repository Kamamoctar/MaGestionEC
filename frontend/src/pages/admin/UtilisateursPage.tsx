import { useEffect, useState } from "react";
import apiClient from "../../api/client";
import type { Utilisateur } from "../../types";

const ROLES: Record<string, string> = {
  admin: "Admin",
  secretariat: "Secrétariat",
  agent: "Agent",
  direction: "Direction",
};

export default function UtilisateursPage() {
  const [utilisateurs, setUtilisateurs] = useState<Utilisateur[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get<Utilisateur[]>("/utilisateurs").then((r) => setUtilisateurs(r.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400">Chargement…</div>;

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-800 mb-6">Utilisateurs</h1>
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Nom</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Rôle</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Statut</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {utilisateurs.map((u) => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{u.prenom} {u.nom}</td>
                <td className="px-4 py-3 text-gray-500">{u.email}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                    {ROLES[u.role_fonctionnel] ?? u.role_fonctionnel}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`w-2 h-2 rounded-full inline-block ${u.is_active ? "bg-green-500" : "bg-gray-300"}`} />
                </td>
              </tr>
            ))}
            {utilisateurs.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">Aucun utilisateur</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
