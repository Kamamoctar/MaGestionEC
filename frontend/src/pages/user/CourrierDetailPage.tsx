import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getCourrier, transmettreCourrier, actionParapheur, archiverCourrier, type ActionParapheur } from "../../api/courriers";
import { getPostes } from "../../api/postes";
import { getHistoriqueMouvements, type Mouvement } from "../../api/mouvements";
import {
  getPiecesJointes, uploadPieceJointe, supprimerPieceJointe,
  downloadUrl, formatTaille, iconeType, type PieceJointe,
} from "../../api/piecesJointes";
import { useAuthStore } from "../../store/authStore";
import type { Courrier, Poste } from "../../types";

const PRIORITE_LABELS: Record<string, string> = {
  normal: "Normal", urgent: "Urgent", tres_urgent: "Très urgent",
};
const PRIORITE_COLORS: Record<string, string> = {
  normal: "bg-gray-100 text-gray-600",
  urgent: "bg-orange-100 text-orange-700",
  tres_urgent: "bg-red-100 text-red-700",
};
const ACTION_LABELS: Record<string, string> = {
  creation: "Enregistré", transmission: "Transmis", visa: "Visé",
  signature: "Signé", annotation: "Annoté", retour: "Retourné", archive: "Archivé",
};
const ACTION_COLORS: Record<string, string> = {
  visa: "bg-blue-500", signature: "bg-purple-500", annotation: "bg-yellow-400",
  transmission: "bg-primary", retour: "bg-orange-400", creation: "bg-green-500", archive: "bg-gray-400",
};

// Boutons du parapheur selon le type d'étape courante
const PARAPHEUR_CONFIG: Record<string, { label: string; action: ActionParapheur; color: string }> = {
  visa: { label: "Viser", action: "visa", color: "bg-blue-600 hover:bg-blue-700" },
  signature: { label: "Signer", action: "signature", color: "bg-purple-600 hover:bg-purple-700" },
  information: { label: "Accusé de réception", action: "visa", color: "bg-teal-600 hover:bg-teal-700" },
  distribution: { label: "Valider distribution", action: "visa", color: "bg-green-600 hover:bg-green-700" },
};

type PanelMode = "transmettre" | "action" | "annoter" | null;

export default function CourrierDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token } = useAuthStore();
  const fileRef = useRef<HTMLInputElement>(null);
  const [courrier, setCourrier] = useState<Courrier | null>(null);
  const [mouvements, setMouvements] = useState<Mouvement[]>([]);
  const [postes, setPostes] = useState<Poste[]>([]);
  const [piecesJointes, setPiecesJointes] = useState<PieceJointe[]>([]);
  const [loading, setLoading] = useState(true);
  const [panel, setPanel] = useState<PanelMode>(null);
  const [posteDestId, setPosteDestId] = useState("");
  const [commentaire, setCommentaire] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([getCourrier(id), getHistoriqueMouvements(id), getPostes(), getPiecesJointes(id)])
      .then(([c, mvts, ps, pjs]) => { setCourrier(c); setMouvements(mvts); setPostes(ps); setPiecesJointes(pjs); })
      .finally(() => setLoading(false));
  }, [id]);

  async function refreshCourrier() {
    if (!id) return;
    const [c, mvts] = await Promise.all([getCourrier(id), getHistoriqueMouvements(id)]);
    setCourrier(c);
    setMouvements(mvts);
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !id) return;
    setUploading(true);
    setUploadError(null);
    try {
      const pj = await uploadPieceJointe(id, file);
      setPiecesJointes((prev) => [...prev, pj]);
    } catch (err: any) {
      setUploadError(err?.response?.data?.detail ?? "Erreur lors de l'envoi du fichier");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function handleSupprimerPj(pjId: string) {
    await supprimerPieceJointe(pjId);
    setPiecesJointes((prev) => prev.filter((p) => p.id !== pjId));
  }

  async function handleTransmettre(e: React.FormEvent) {
    e.preventDefault();
    if (!id || !posteDestId) return;
    setSubmitting(true);
    try {
      await transmettreCourrier(id, posteDestId, commentaire || undefined);
      await refreshCourrier();
      setPanel(null); setCommentaire(""); setPosteDestId("");
    } finally { setSubmitting(false); }
  }

  async function handleAction(action: ActionParapheur) {
    if (!id) return;
    setSubmitting(true);
    try {
      await actionParapheur(id, action, commentaire || undefined);
      await refreshCourrier();
      setPanel(null); setCommentaire("");
    } finally { setSubmitting(false); }
  }

  async function handleAnnoter(e: React.FormEvent) {
    e.preventDefault();
    await handleAction("annotation");
  }

  if (loading) return <div className="text-gray-400 p-8">Chargement…</div>;
  if (!courrier) return <div className="text-red-500 p-8">Courrier introuvable</div>;

  const enCours = courrier.etat !== "archive" && courrier.etat !== "traite";
  const estTraite = courrier.etat === "traite";
  const actionConfig = courrier.type_action_courante
    ? PARAPHEUR_CONFIG[courrier.type_action_courante]
    : null;

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
          <div><dt className="text-gray-400">Expéditeur</dt><dd className="font-medium">{courrier.expediteur}</dd></div>
          <div><dt className="text-gray-400">Type</dt><dd className="font-medium capitalize">{courrier.type.replace("_", " ")}</dd></div>
          <div><dt className="text-gray-400">Reçu le</dt><dd className="font-medium">{new Date(courrier.date_reception).toLocaleDateString("fr-FR")}</dd></div>
          {courrier.date_limite && (
            <div>
              <dt className="text-gray-400">Échéance</dt>
              <dd className={`font-medium ${new Date(courrier.date_limite) < new Date() ? "text-red-600" : "text-orange-600"}`}>
                {new Date(courrier.date_limite).toLocaleDateString("fr-FR")}
              </dd>
            </div>
          )}
          <div>
            <dt className="text-gray-400">État</dt>
            <dd>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                courrier.etat === "traite" ? "bg-green-100 text-green-700" :
                courrier.etat === "en_cours" ? "bg-blue-100 text-blue-700" :
                courrier.etat === "archive" ? "bg-gray-100 text-gray-500" :
                "bg-orange-100 text-orange-700"
              }`}>
                {courrier.etat.replace("_", " ")}
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-gray-400">Confidentialité</dt>
            <dd className={`font-medium ${courrier.confidentialite === "confidentiel" ? "text-red-600" : ""}`}>
              {courrier.confidentialite}
            </dd>
          </div>
        </dl>

        {/* Zone d'actions */}
        {enCours && (
          <div className="mt-5 pt-4 border-t">
            {panel === null && (
              <div className="flex flex-wrap gap-2">
                {/* Bouton parapheur principal (visa/signature selon l'étape) */}
                {actionConfig && (
                  <button
                    onClick={() => { setPanel("action"); setCommentaire(""); }}
                    className={`px-4 py-2 text-white rounded-lg text-sm font-medium ${actionConfig.color}`}
                  >
                    {actionConfig.label} ✓
                  </button>
                )}
                <button
                  onClick={() => { setPanel("annoter"); setCommentaire(""); }}
                  className="px-4 py-2 border border-yellow-300 text-yellow-700 bg-yellow-50 rounded-lg text-sm hover:bg-yellow-100"
                >
                  Annoter
                </button>
                <button
                  onClick={() => { setPanel("transmettre"); setCommentaire(""); }}
                  className="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-dark"
                >
                  Transmettre →
                </button>
                {mouvements.some((m) => m.poste_source_id) && (
                  <button
                    onClick={() => handleAction("retour")}
                    className="px-4 py-2 border border-orange-300 text-orange-700 bg-orange-50 rounded-lg text-sm hover:bg-orange-100"
                    disabled={submitting}
                  >
                    ↩ Retourner
                  </button>
                )}
              </div>
            )}

            {/* Panel Parapheur (visa/signature) */}
            {panel === "action" && actionConfig && (
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-700">{actionConfig.label} — ajouter un commentaire (optionnel)</p>
                <textarea value={commentaire} onChange={(e) => setCommentaire(e.target.value)}
                  rows={2} placeholder="Commentaire…"
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                <div className="flex gap-2">
                  <button onClick={() => handleAction(actionConfig.action)} disabled={submitting}
                    className={`px-4 py-2 text-white rounded-lg text-sm font-medium disabled:opacity-50 ${actionConfig.color}`}>
                    {submitting ? "Enregistrement…" : `Confirmer ${actionConfig.label}`}
                  </button>
                  <button onClick={() => setPanel(null)} className="px-4 py-2 text-sm text-gray-500">Annuler</button>
                </div>
              </div>
            )}

            {/* Panel Annotation */}
            {panel === "annoter" && (
              <form onSubmit={handleAnnoter} className="space-y-3">
                <p className="text-sm font-medium text-gray-700">Ajouter une annotation</p>
                <textarea value={commentaire} onChange={(e) => setCommentaire(e.target.value)}
                  rows={3} placeholder="Votre annotation…" required
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                <div className="flex gap-2">
                  <button type="submit" disabled={submitting || !commentaire.trim()}
                    className="px-4 py-2 bg-yellow-500 text-white rounded-lg text-sm disabled:opacity-50">
                    {submitting ? "…" : "Annoter"}
                  </button>
                  <button type="button" onClick={() => setPanel(null)} className="px-4 py-2 text-sm text-gray-500">Annuler</button>
                </div>
              </form>
            )}

            {/* Panel Transmettre */}
            {panel === "transmettre" && (
              <form onSubmit={handleTransmettre} className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Transmettre à</label>
                  <select value={posteDestId} onChange={(e) => setPosteDestId(e.target.value)} required
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
                    <option value="">Choisir un poste…</option>
                    {postes.map((p) => <option key={p.id} value={p.id}>{p.intitule}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Commentaire (optionnel)</label>
                  <textarea value={commentaire} onChange={(e) => setCommentaire(e.target.value)}
                    rows={2}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                </div>
                <div className="flex gap-2">
                  <button type="submit" disabled={submitting}
                    className="px-4 py-2 bg-primary text-white rounded-lg text-sm disabled:opacity-50">
                    {submitting ? "Envoi…" : "Transmettre"}
                  </button>
                  <button type="button" onClick={() => setPanel(null)} className="px-4 py-2 text-sm text-gray-500">Annuler</button>
                </div>
              </form>
            )}
          </div>
        )}
      </div>

      {/* Archivage */}
      {estTraite && (
        <div className="bg-white rounded-xl border p-4 mb-4 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-700">Courrier traité</p>
            <p className="text-xs text-gray-400">Archiver pour le retirer des corbeilles actives</p>
          </div>
          <button
            disabled={submitting}
            onClick={async () => {
              if (!id || !confirm("Archiver ce courrier ? Cette action est définitive.")) return;
              setSubmitting(true);
              try { const c = await archiverCourrier(id); setCourrier(c); } finally { setSubmitting(false); }
            }}
            className="px-4 py-2 bg-gray-700 text-white rounded-lg text-sm hover:bg-gray-800 disabled:opacity-50"
          >
            Archiver
          </button>
        </div>
      )}

      {/* Pièces jointes */}
      <div className="bg-white rounded-xl border p-6 mb-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-medium text-gray-700">Pièces jointes</h2>
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="text-sm px-3 py-1.5 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50"
          >
            {uploading ? "Envoi…" : "+ Ajouter"}
          </button>
          <input ref={fileRef} type="file" className="hidden" onChange={handleUpload}
            accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.webp,.txt,.zip" />
        </div>

        {uploadError && (
          <p className="text-sm text-red-600 mb-3">{uploadError}</p>
        )}

        {piecesJointes.length === 0 ? (
          <p className="text-gray-400 text-sm">Aucune pièce jointe</p>
        ) : (
          <ul className="space-y-2">
            {piecesJointes.map((pj) => (
              <li key={pj.id} className="flex items-center gap-3 p-2.5 rounded-lg bg-gray-50 hover:bg-gray-100">
                <span className="text-xl">{iconeType(pj.mime_type)}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{pj.nom_fichier}</p>
                  <p className="text-xs text-gray-400">{formatTaille(pj.taille_octets)}</p>
                </div>
                <a
                  href={`${downloadUrl(pj.id)}?token=${token}`}
                  download={pj.nom_fichier}
                  onClick={(e) => {
                    // Téléchargement authentifié via fetch blob
                    e.preventDefault();
                    fetch(downloadUrl(pj.id), { headers: { Authorization: `Bearer ${token}` } })
                      .then((r) => r.blob())
                      .then((blob) => {
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url; a.download = pj.nom_fichier; a.click();
                        URL.revokeObjectURL(url);
                      });
                  }}
                  className="text-xs px-2 py-1 border rounded-md text-primary hover:bg-blue-50"
                >
                  Télécharger
                </a>
                <button
                  onClick={() => handleSupprimerPj(pj.id)}
                  className="text-xs px-2 py-1 border rounded-md text-red-500 hover:bg-red-50"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Historique */}
      <div className="bg-white rounded-xl border p-6">
        <h2 className="font-medium text-gray-700 mb-4">Historique</h2>
        {mouvements.length === 0 ? (
          <p className="text-gray-400 text-sm">Aucun mouvement enregistré</p>
        ) : (
          <ol className="relative border-l border-gray-200 space-y-4 pl-5">
            {mouvements.map((m) => (
              <li key={m.id} className="relative">
                <span className={`absolute -left-[1.35rem] top-0.5 w-3 h-3 rounded-full border-2 border-white ${ACTION_COLORS[m.action] ?? "bg-gray-400"}`} />
                <p className="text-sm font-medium text-gray-700">{ACTION_LABELS[m.action] ?? m.action}</p>
                {m.commentaire && <p className="text-xs text-gray-500 mt-0.5 italic">"{m.commentaire}"</p>}
                <p className="text-xs text-gray-400 mt-0.5">{new Date(m.created_at).toLocaleString("fr-FR")}</p>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
