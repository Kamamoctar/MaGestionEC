import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getCourrier, transmettreCourrier } from "../../api/courriers";
import { getPostes } from "../../api/postes";
import { getHistoriqueMouvements, type Mouvement } from "../../api/mouvements";
import type { Courrier, Poste } from "../../types";

const PRIORITE_LABELS: Record<string, string> = {
  normal: "Normal",
  urgent: "Urgent",
  tres_urgent: "Très urgent",
};

const PRIORITE_COLORS: Record<string, string> = {
  normal: "bg-gray-100 text-gray-600",
  urgent: "bg-orange-100 text-orange-700",
  tres_urgent: "bg-red-100 text-red-700",
};

const ACTION_LABELS: Record<string, string> = {
  creation: "Enregistré",
  transmission: "Transmis",
  visa: "Visé",
  signature: "Signé",
  annotation: "Annoté",
  retour: "Retourné",
  archive: "Archivé",
};

export default function CourrierDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [courrier, setCourrier] = useState<Courrier | null>(null);
  const [mouvements, setMouvements] = useState<Mouvement[]>([]);
  const [postes, setPostes] = useState<Poste[]>([]);
  const [loading, setLoading] = useState(true);
  const [showTransmettre, setShowTransmettre] = useState(false);
  const [posteDestId, setPosteDestId] = useState("");
  const [commentaire, setCommentaire] = useState("");
  const [transmitting, setTransmitting] = useState(false);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      getCourrier(id),
      getHistoriqueMouvements(id),
      getPostes(),
    ]).then(([c, mvts, ps]) => {
      setCourrier(c);
      setMouvements(mvts);
      setPostes(ps);
    }).finally(() => setLoading(false));
  }, [id]);

  async function handleTransmettre(e: React.FormEvent) {
    e.preventDefault();
    if (!id || !posteDestId) return;
    setTransmitting(true);
    try {
      const updated = await transmettreCourrier(id, posteDestId, commentaire || undefined);
      setCourrier(updated);
      // Recharger l'historique
      const mvts = await getHistoriqueMouvements(id);
      setMouvements(mvts);
      setShowTransmettre(false);
      setCommentaire("");
      setPosteDestId("");
    } finally {
      setTransmitting(false);
    }
  }

  if (loading) return <div className="text-gray-400 p-8">Chargement…</div>;
  if (!courrier) return <div className="text-red-500 p-8">Courrier introuvable</div>;

  return (
    <div className="max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-500 hover:text-gray-700 mb-4">
        ← Retour
      </button>

      {/* En-tête */}
      <div className="bg-white rounded-xl border p-6 mb-4">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <p className="text-xs text-gray-400 font-mono mb-1">{courrier.reference}</p>
            <h1 className="text-lg font-semibold text-gray-800">{courrier.objet}</h1>
          </div>
          <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${PRIORITE_COLORS[courrier.priorite]}`}>
            {PRIORITE_LABELS[courrier.priorite]}
          </span>
        </div>

        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
          <div>
            <dt className="text-gray-400">Expéditeur</dt>
            <dd className="font-medium">{courrier.expediteur}</dd>
          </div>
          <div>
            <dt className="text-gray-400">Type</dt>
            <dd className="font-medium capitalize">{courrier.type.replace("_", " ")}</dd>
          </div>
          <div>
            <dt className="text-gray-400">Reçu le</dt>
            <dd className="font-medium">{new Date(courrier.date_reception).toLocaleDateString("fr-FR")}</dd>
          </div>
          {courrier.date_limite && (
            <div>
              <dt className="text-gray-400">Échéance</dt>
              <dd className="font-medium text-orange-600">{new Date(courrier.date_limite).toLocaleDateString("fr-FR")}</dd>
            </div>
          )}
          <div>
            <dt className="text-gray-400">État</dt>
            <dd className="font-medium capitalize">{courrier.etat.replace("_", " ")}</dd>
          </div>
          <div>
            <dt className="text-gray-400">Confidentialité</dt>
            <dd className={`font-medium ${courrier.confidentialite === "confidentiel" ? "text-red-600" : ""}`}>
              {courrier.confidentialite}
            </dd>
          </div>
        </dl>

        {/* Action transmettre */}
        {courrier.etat !== "archive" && courrier.etat !== "traite" && (
          <div className="mt-5 pt-4 border-t">
            {showTransmettre ? (
              <form onSubmit={handleTransmettre} className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Transmettre à</label>
                  <select
                    value={posteDestId}
                    onChange={(e) => setPosteDestId(e.target.value)}
                    required
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="">Choisir un poste…</option>
                    {postes.map((p) => (
                      <option key={p.id} value={p.id}>{p.intitule}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Commentaire (optionnel)</label>
                  <textarea
                    value={commentaire}
                    onChange={(e) => setCommentaire(e.target.value)}
                    rows={2}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                <div className="flex gap-2">
                  <button type="submit" disabled={transmitting} className="px-4 py-2 bg-primary text-white rounded-lg text-sm disabled:opacity-50">
                    {transmitting ? "Envoi…" : "Transmettre"}
                  </button>
                  <button type="button" onClick={() => setShowTransmettre(false)} className="px-4 py-2 text-sm text-gray-500">
                    Annuler
                  </button>
                </div>
              </form>
            ) : (
              <button
                onClick={() => setShowTransmettre(true)}
                className="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-dark"
              >
                Transmettre →
              </button>
            )}
          </div>
        )}
      </div>

      {/* Historique des mouvements */}
      <div className="bg-white rounded-xl border p-6">
        <h2 className="font-medium text-gray-700 mb-4">Historique</h2>
        {mouvements.length === 0 ? (
          <p className="text-gray-400 text-sm">Aucun mouvement enregistré</p>
        ) : (
          <ol className="relative border-l border-gray-200 space-y-4 pl-5">
            {mouvements.map((m) => (
              <li key={m.id} className="relative">
                <span className="absolute -left-[1.35rem] top-0.5 w-3 h-3 rounded-full bg-primary border-2 border-white" />
                <p className="text-sm font-medium text-gray-700">{ACTION_LABELS[m.action] ?? m.action}</p>
                {m.commentaire && <p className="text-xs text-gray-500 mt-0.5 italic">"{m.commentaire}"</p>}
                <p className="text-xs text-gray-400 mt-0.5">
                  {new Date(m.created_at).toLocaleString("fr-FR")}
                </p>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
