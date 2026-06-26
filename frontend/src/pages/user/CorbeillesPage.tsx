import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getMesCorbeilles } from "../../api/courriers";
import { slaStatus } from "../../utils/sla";
import type { Courrier } from "../../types";

type Corbeille = "tout" | "a_traiter" | "pour_information" | "traites";

const CORBEILLES: { value: Corbeille; label: string; desc: string }[] = [
  { value: "tout",             label: "Tout",              desc: "Tous les courriers de mon poste" },
  { value: "a_traiter",       label: "À traiter",         desc: "En attente ou en cours de traitement" },
  { value: "pour_information", label: "Pour information",  desc: "Courriers reçus pour information (aucune action requise)" },
  { value: "traites",         label: "Traités",           desc: "Courriers traités ou archivés" },
];

function corbeilleToParams(c: Corbeille): { etat?: string; type_action?: string } {
  if (c === "a_traiter")        return { etat: "en_attente" };
  if (c === "pour_information") return { type_action: "information" };
  if (c === "traites")          return { etat: "traite" };
  return {};
}

const PRIORITE_COLORS: Record<string, string> = {
  normal:      "bg-gray-100 text-gray-600",
  urgent:      "bg-orange-100 text-orange-700",
  tres_urgent: "bg-red-100 text-red-700",
};

const TYPE_ACTION_LABELS: Record<string, string> = {
  visa:         "Visa",
  signature:    "Signature",
  distribution: "Distribution",
  information:  "Pour info",
};

export default function CorbeillesPage() {
  const navigate = useNavigate();
  const [courriers, setCourriers] = useState<Courrier[]>([]);
  const [corbeille, setCorbeille] = useState<Corbeille>("tout");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const { etat, type_action } = corbeilleToParams(corbeille);
    getMesCorbeilles(etat, type_action).then(setCourriers).finally(() => setLoading(false));
  }, [corbeille]);

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

      {/* Onglets corbeilles */}
      <div className="flex flex-wrap gap-2 mb-6">
        {CORBEILLES.map((c) => (
          <button
            key={c.value}
            onClick={() => setCorbeille(c.value)}
            title={c.desc}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              corbeille === c.value
                ? "bg-primary text-white"
                : "bg-white border text-gray-600 hover:border-primary"
            }`}
          >
            {c.label}
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
                    <div className="flex items-center gap-2 flex-wrap">
                      {sla === "retard" && <span className="text-red-500 text-xs font-bold shrink-0">⚠ RETARD</span>}
                      {sla === "proche" && <span className="text-orange-500 text-xs font-semibold shrink-0">⏱ URGENT</span>}
                      {c.type_action_courante && (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-teal-50 text-teal-700 shrink-0">
                          {TYPE_ACTION_LABELS[c.type_action_courante] ?? c.type_action_courante}
                        </span>
                      )}
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
