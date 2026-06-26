import { useEffect, useState } from "react";
import { getFlux } from "../../api/flux";
import apiClient from "../../api/client";
import type { Flux } from "../../types";

const ACTION_COLORS: Record<string, string> = {
  visa: "bg-blue-100 text-blue-700",
  signature: "bg-purple-100 text-purple-700",
  distribution: "bg-green-100 text-green-700",
  information: "bg-teal-100 text-teal-700",
};

const ACTION_LABELS: Record<string, string> = {
  visa: "Visa",
  signature: "Signature",
  distribution: "Distribution",
  information: "Information",
};

export default function CircuitsPage() {
  const [circuits, setCircuits] = useState<Flux[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    getFlux().then(setCircuits).finally(() => setLoading(false));
  }, []);

  async function handleSupprimer(id: string, nom: string) {
    if (!confirm(`Supprimer le circuit « ${nom} » ? Les courriers en cours perdront leur circuit.`)) return;
    setDeleting(id);
    try {
      await apiClient.delete(`/flux/${id}`);
      setCircuits((prev) => prev.filter((f) => f.id !== id));
      if (expanded === id) setExpanded(null);
    } finally {
      setDeleting(null);
    }
  }

  if (loading) return <div className="text-gray-400">Chargement…</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-800">Circuits de traitement</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Circuits générés depuis des fichiers BPMN. Pour en créer un, utilisez{" "}
            <a href="/admin/import-bpmn" className="text-primary underline">Import BPMN</a>.
          </p>
        </div>
        <span className="text-sm text-gray-400">{circuits.length} circuit{circuits.length !== 1 ? "s" : ""}</span>
      </div>

      {circuits.length === 0 ? (
        <div className="bg-white rounded-xl border p-12 text-center text-gray-400">
          <p className="text-3xl mb-3">⚙️</p>
          <p className="font-medium">Aucun circuit configuré</p>
          <p className="text-sm mt-1">Importez un fichier BPMN pour générer le premier circuit.</p>
          <a href="/admin/import-bpmn"
            className="inline-block mt-4 px-4 py-2 bg-primary text-white rounded-lg text-sm">
            Importer un BPMN
          </a>
        </div>
      ) : (
        <div className="space-y-3">
          {circuits.map((f) => {
            const etapesSorted = [...f.etapes].sort((a, b) => a.ordre - b.ordre);
            const isOpen = expanded === f.id;

            return (
              <div key={f.id} className="bg-white rounded-xl border overflow-hidden">
                {/* En-tête cliquable */}
                <button
                  onClick={() => setExpanded(isOpen ? null : f.id)}
                  className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 text-left"
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <span className="text-gray-400 text-lg">{isOpen ? "▾" : "▸"}</span>
                    <div className="min-w-0">
                      <p className="font-medium text-gray-800">{f.nom}</p>
                      {f.description && (
                        <p className="text-xs text-gray-400 truncate mt-0.5">{f.description}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0 ml-4">
                    {/* Pipeline miniature des étapes */}
                    <div className="hidden sm:flex items-center gap-1">
                      {etapesSorted.map((e, i) => (
                        <div key={e.id} className="flex items-center gap-1">
                          {i > 0 && <span className="text-gray-300 text-xs">→</span>}
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ACTION_COLORS[e.type_action] ?? "bg-gray-100 text-gray-600"}`}>
                            {ACTION_LABELS[e.type_action] ?? e.type_action}
                          </span>
                        </div>
                      ))}
                    </div>
                    <span className="text-xs text-gray-400">{etapesSorted.length} étape{etapesSorted.length > 1 ? "s" : ""}</span>
                  </div>
                </button>

                {/* Détail des étapes */}
                {isOpen && (
                  <div className="border-t">
                    <div className="px-5 py-4">
                      <div className="space-y-2 mb-5">
                        {etapesSorted.map((e) => (
                          <div key={e.id} className="flex items-center gap-3 text-sm">
                            <div className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-600 text-xs font-bold shrink-0">
                              {e.ordre}
                            </div>
                            <div className="flex-1">
                              <span className="font-medium text-gray-800">
                                {e.intitule_poste ?? e.poste_id}
                              </span>
                            </div>
                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${ACTION_COLORS[e.type_action] ?? "bg-gray-100 text-gray-600"}`}>
                              {ACTION_LABELS[e.type_action] ?? e.type_action}
                            </span>
                            {e.is_terminal && (
                              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                                Terminal
                              </span>
                            )}
                          </div>
                        ))}
                      </div>

                      <div className="pt-4 border-t flex justify-end">
                        <button
                          onClick={() => handleSupprimer(f.id, f.nom)}
                          disabled={deleting === f.id}
                          className="px-4 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50"
                        >
                          {deleting === f.id ? "Suppression…" : "Supprimer ce circuit"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
