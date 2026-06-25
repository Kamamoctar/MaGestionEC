import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getMesCorbeilles } from "../../api/courriers";
import type { Courrier } from "../../types";

const ETATS = [
  { value: undefined, label: "Tout" },
  { value: "en_attente", label: "À traiter" },
  { value: "en_cours", label: "En cours" },
  { value: "traite", label: "Traités" },
];

const PRIORITE_COLORS: Record<string, string> = {
  normal: "bg-gray-100 text-gray-600",
  urgent: "bg-orange-100 text-orange-700",
  tres_urgent: "bg-red-100 text-red-700",
};

export default function CorbeillesPage() {
  const navigate = useNavigate();
  const [courriers, setCourriers] = useState<Courrier[]>([]);
  const [etat, setEtat] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getMesCorbeilles(etat).then(setCourriers).finally(() => setLoading(false));
  }, [etat]);

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-800 mb-4">Mes corbeilles</h1>

      {/* Onglets état */}
      <div className="flex gap-2 mb-6">
        {ETATS.map((e) => (
          <button
            key={String(e.value)}
            onClick={() => setEtat(e.value)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              etat === e.value ? "bg-primary text-white" : "bg-white border text-gray-600 hover:border-primary"
            }`}
          >
            {e.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-gray-400">Chargement…</div>
      ) : (
        <div className="space-y-3">
          {courriers.map((c) => (
            <div key={c.id} onClick={() => navigate(`/app/courriers/${c.id}`)} className="bg-white rounded-xl border p-4 hover:shadow-sm transition-shadow cursor-pointer">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-gray-800">{c.objet}</p>
                  <p className="text-xs text-gray-400 mt-0.5">De : {c.expediteur} — Réf. {c.reference}</p>
                </div>
                <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${PRIORITE_COLORS[c.priorite]}`}>
                  {c.priorite.replace("_", " ")}
                </span>
              </div>
              {c.date_limite && (
                <p className="mt-2 text-xs text-orange-600">
                  Échéance : {new Date(c.date_limite).toLocaleDateString("fr-FR")}
                </p>
              )}
            </div>
          ))}
          {courriers.length === 0 && (
            <div className="text-center py-16 text-gray-400">
              <p className="text-4xl mb-3">📭</p>
              <p>Aucun courrier dans cette corbeille</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
