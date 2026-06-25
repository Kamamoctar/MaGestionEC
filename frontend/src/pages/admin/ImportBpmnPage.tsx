import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyserBpmn, genererFlux, type BpmnAnalyse, type MappingLane } from "../../api/bpmn";
import { getPostes } from "../../api/postes";
import type { Poste } from "../../types";

type Etape = "upload" | "mapping" | "succes";

const ACTION_OPTIONS = [
  { value: "distribution", label: "Distribution" },
  { value: "visa", label: "Visa" },
  { value: "signature", label: "Signature" },
  { value: "information", label: "Pour information" },
];

export default function ImportBpmnPage() {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [etape, setEtape] = useState<Etape>("upload");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analyse, setAnalyse] = useState<BpmnAnalyse | null>(null);
  const [postes, setPostes] = useState<Poste[]>([]);
  const [nomFlux, setNomFlux] = useState("");
  const [mapping, setMapping] = useState<MappingLane[]>([]);
  const [fluxCree, setFluxCree] = useState<{ id: string; nom: string } | null>(null);

  useEffect(() => {
    getPostes().then(setPostes);
  }, []);

  async function handleFile(file: File) {
    if (!file.name.match(/\.(bpmn|xml)$/i)) {
      setError("Fichier non supporté — utilisez un fichier .bpmn ou .xml");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await analyserBpmn(file);
      setAnalyse(result);
      setNomFlux(result.nom_processus);
      // Initialiser le mapping dans l'ordre topologique
      setMapping(
        result.ordre_lanes.map((laneId) => {
          const lane = result.lanes.find((l) => l.lane_id === laneId)!;
          return {
            lane_id: laneId,
            poste_id: "",
            type_action: lane.type_action_propose,
          };
        })
      );
      setEtape("mapping");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Erreur lors de l'analyse du fichier");
    } finally {
      setLoading(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function updateMapping(laneId: string, field: keyof MappingLane, value: string) {
    setMapping((prev) =>
      prev.map((m) => (m.lane_id === laneId ? { ...m, [field]: value } : m))
    );
  }

  async function handleGenerer() {
    if (!analyse) return;
    const incomplet = mapping.find((m) => !m.poste_id);
    if (incomplet) {
      const lane = analyse.lanes.find((l) => l.lane_id === incomplet.lane_id);
      setError(`Choisissez un poste pour la lane « ${lane?.lane_name} »`);
      return;
    }
    if (!nomFlux.trim()) {
      setError("Le nom du circuit est requis");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const flux = await genererFlux({
        nom: nomFlux,
        bpmn_source: analyse.bpmn_source,
        mapping,
        ordre_lanes: analyse.ordre_lanes,
      });
      setFluxCree({ id: flux.id, nom: flux.nom });
      setEtape("succes");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Erreur lors de la génération du circuit");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setEtape("upload");
    setAnalyse(null);
    setMapping([]);
    setError(null);
    setFluxCree(null);
    if (fileRef.current) fileRef.current.value = "";
  }

  // ── Étape 1 : Upload ────────────────────────────────────────────────────
  if (etape === "upload") {
    return (
      <div>
        <h1 className="text-xl font-semibold text-gray-800 mb-1">Import BPMN</h1>
        <p className="text-sm text-gray-500 mb-6">
          Chargez un fichier <code>.bpmn</code> ou <code>.xml</code> pour générer automatiquement un circuit de traitement.
        </p>

        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={`rounded-2xl border-2 border-dashed p-16 flex flex-col items-center gap-4 text-center transition-colors ${
            dragging ? "border-primary bg-blue-50" : "border-gray-200 bg-white"
          }`}
        >
          <div className="w-14 h-14 rounded-full bg-blue-50 flex items-center justify-center">
            <svg className="w-7 h-7 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <div>
            <p className="font-medium text-gray-700">Glissez-déposez votre fichier BPMN ici</p>
            <p className="text-xs text-gray-400 mt-1">ou cliquez pour parcourir (.bpmn, .xml — max 5 Mo)</p>
          </div>
          <button
            onClick={() => fileRef.current?.click()}
            disabled={loading}
            className="px-5 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-dark disabled:opacity-50"
          >
            {loading ? "Analyse en cours…" : "Choisir un fichier"}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".bpmn,.xml"
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
          />
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
        )}
      </div>
    );
  }

  // ── Étape 2 : Mapping ────────────────────────────────────────────────────
  if (etape === "mapping" && analyse) {
    const lanesOrdonnees = analyse.ordre_lanes
      .map((id) => analyse.lanes.find((l) => l.lane_id === id)!)
      .filter(Boolean);

    return (
      <div className="max-w-3xl">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={reset} className="text-sm text-gray-400 hover:text-gray-600">← Recommencer</button>
          <h1 className="text-xl font-semibold text-gray-800">Mapping des lanes</h1>
        </div>

        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-6 text-sm text-blue-700">
          <strong>{lanesOrdonnees.length} lanes détectées</strong> dans « {analyse.nom_processus} ».
          Associez chaque lane à un poste existant, vérifiez le type d'action, puis générez le circuit.
        </div>

        {analyse.avertissements.length > 0 && (
          <div className="bg-orange-50 border border-orange-100 rounded-xl p-3 mb-4 text-sm text-orange-700 space-y-1">
            {analyse.avertissements.map((w, i) => <p key={i}>⚠ {w}</p>)}
          </div>
        )}

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Nom du circuit *</label>
          <input
            value={nomFlux}
            onChange={(e) => setNomFlux(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div className="bg-white rounded-xl border overflow-hidden mb-6">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600 w-6">#</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Lane BPMN</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Tâches détectées</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Poste *</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {lanesOrdonnees.map((lane, idx) => {
                const m = mapping.find((x) => x.lane_id === lane.lane_id)!;
                return (
                  <tr key={lane.lane_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-400 text-xs">{idx + 1}</td>
                    <td className="px-4 py-3 font-medium">{lane.lane_name}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {lane.taches.length > 0 ? lane.taches.join(", ") : <span className="italic">aucune</span>}
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={m?.poste_id ?? ""}
                        onChange={(e) => updateMapping(lane.lane_id, "poste_id", e.target.value)}
                        className="w-full border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      >
                        <option value="">Choisir…</option>
                        {postes.map((p) => (
                          <option key={p.id} value={p.id}>{p.intitule}</option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={m?.type_action ?? "distribution"}
                        onChange={(e) => updateMapping(lane.lane_id, "type_action", e.target.value)}
                        className="border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      >
                        {ACTION_OPTIONS.map((o) => (
                          <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
        )}

        <div className="flex gap-3">
          <button
            onClick={handleGenerer}
            disabled={loading}
            className="px-6 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-dark disabled:opacity-50"
          >
            {loading ? "Génération…" : "Générer le circuit →"}
          </button>
          <button onClick={reset} className="px-4 py-2 text-sm text-gray-500">Annuler</button>
        </div>
      </div>
    );
  }

  // ── Étape 3 : Succès ─────────────────────────────────────────────────────
  return (
    <div className="max-w-lg text-center py-12">
      <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
        <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h2 className="text-xl font-semibold text-gray-800 mb-2">Circuit généré !</h2>
      <p className="text-gray-500 text-sm mb-6">
        Le circuit <strong>« {fluxCree?.nom} »</strong> est prêt.
        Il peut maintenant être appliqué aux courriers.
      </p>
      <div className="flex gap-3 justify-center">
        <button onClick={reset} className="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-dark">
          Importer un autre fichier
        </button>
        <button onClick={() => navigate("/admin/postes")} className="px-4 py-2 border rounded-lg text-sm text-gray-600">
          Retour aux postes
        </button>
      </div>
    </div>
  );
}
