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

function slaStatus(c: Courrier): "retard" | "proche" | null {
  if (!c.date_limite || c.etat === "traite" || c.etat === "archive") return null;
  const now = Date.now();
  const limite = new Date(c.date_limite).getTime();
  if (limite < now) return "retard";
  if (limite - now < 48 * 3600 * 1000) return "proche";
  return null;
}

export default function CorbeillesPage() {
  const navigate = useNavigate();
  const [courriers, setCourriers] = useState<Courrier[]>([]);
  const [etat, setEtat] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getMesCorbeilles(etat).then(setCourriers).finally(() => setLoading(false));
  }, [etat]);

  const nbRetard = courriers.filter((c) => slaStatus(c) === "retard").length;
  const nbProche = courriers.filter((c) => slaStatus(c) === "proche").length;

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-800 mb-4">Mes corbeilles</h1>

      {/* Alertes SLA */}
      {(nbRetard > 0 || nbProche > 0) && (
        <div className="space-y-2 mb-4">
          {nbRetard > 0 && (
            <div className="flex items-center gap-2 px-4 py-2.5 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
              <span>🔴</span>
              <strong>{nbRetard} courrier{nbRetard > 1 ? "s" : ""} en retard</strong>
              <span className="text-red-500">— échéance dépassée</span>
            </div>
          )}
          {nbProche > 0 && (
            <div className="flex items-center gap-2 px-4 py-2.5 bg-orange-50 border border-orange-200 rounded-xl text-orange-700 text-sm">
              <span>🟡</span>
              <strong>{nbProche} courrier{nbProche > 1 ? "s" : ""}</strong>
              <span className="text-orange-500">— échéance dans moins de 48h</span>
            </div>
          )}
        </div>
      )}

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
          {courriers.map((c) => {
            const sla = slaStatus(c);
            return (
              <div
                key={c.id}
                onClick={() => navigate(`/app/courriers/${c.id}`)}
                className={`bg-white rounded-xl border p-4 hover:shadow-sm transition-shadow cursor-pointer ${
                  sla === "retard" ? "border-red-300 bg-red-50/30" :
                  sla === "proche" ? "border-orange-200 bg-orange-50/20" : ""
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {sla === "retard" && <span className="text-red-500 text-xs font-bold shrink-0">⚠ RETARD</span>}
                      {sla === "proche" && <span className="text-orange-500 text-xs font-semibold shrink-0">⏱ URGENT</span>}
                      <p className="font-medium text-gray-800 truncate">{c.objet}</p>
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">De : {c.expediteur} — Réf. {c.reference}</p>
                  </div>
                  <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${PRIORITE_COLORS[c.priorite]}`}>
                    {c.priorite.replace("_", " ")}
                  </span>
                </div>
                {c.date_limite && (
                  <p className={`mt-2 text-xs font-medium ${
                    sla === "retard" ? "text-red-600" :
                    sla === "proche" ? "text-orange-600" : "text-gray-400"
                  }`}>
                    Échéance : {new Date(c.date_limite).toLocaleDateString("fr-FR")}
                  </p>
                )}
              </div>
            );
          })}
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
