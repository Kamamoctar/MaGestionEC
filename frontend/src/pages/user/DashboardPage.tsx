import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getDashboardStats, type DashboardStats } from "../../api/dashboard";

function KpiCard({
  label, value, color, sub,
}: { label: string; value: number; color: string; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border p-5 flex flex-col gap-1">
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats().then(setStats).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400">Chargement…</div>;
  if (!stats) return null;

  const maxTotal = Math.max(...stats.top_postes.map((p) => p.total), 1);

  const tauxTraitement = stats.total > 0
    ? Math.round((stats.traites / stats.total) * 100)
    : 0;

  return (
    <div className="max-w-5xl space-y-6">
      <h1 className="text-xl font-semibold text-gray-800">Tableau de bord</h1>

      {/* Alerte retards */}
      {stats.en_retard > 0 && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          <span className="text-xl">⚠️</span>
          <span>
            <strong>{stats.en_retard} courrier{stats.en_retard > 1 ? "s" : ""}</strong> en retard
            (échéance dépassée, non traité{stats.en_retard > 1 ? "s" : ""}).
          </span>
          <button
            onClick={() => navigate("/app/recherche?etat=en_cours")}
            className="ml-auto text-xs underline"
          >
            Voir
          </button>
        </div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard label="Total" value={stats.total} color="text-gray-800" />
        <KpiCard label="En attente" value={stats.en_attente} color="text-orange-500" />
        <KpiCard label="En cours" value={stats.en_cours} color="text-blue-600" />
        <KpiCard
          label="Traités"
          value={stats.traites}
          color="text-green-600"
          sub={`${tauxTraitement} % du total`}
        />
        <KpiCard label="En retard" value={stats.en_retard} color="text-red-600" />
      </div>

      {/* Répartition par état */}
      <div className="bg-white rounded-xl border p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Répartition par état</h2>
        <div className="space-y-3">
          {[
            { label: "En attente", value: stats.en_attente, color: "bg-orange-400" },
            { label: "En cours",   value: stats.en_cours,   color: "bg-blue-500" },
            { label: "Traités",    value: stats.traites,    color: "bg-green-500" },
            { label: "Archivés",   value: stats.archives,   color: "bg-gray-300" },
          ].map(({ label, value, color }) => {
            const pct = stats.total > 0 ? (value / stats.total) * 100 : 0;
            return (
              <div key={label} className="flex items-center gap-3 text-sm">
                <span className="w-24 text-gray-500 shrink-0">{label}</span>
                <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${color}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="w-8 text-right text-gray-600 font-medium">{value}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top postes (affiché seulement si données dispo) */}
      {stats.top_postes.length > 0 && (
        <div className="bg-white rounded-xl border p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Volume par poste</h2>
          <div className="space-y-3">
            {stats.top_postes.map((p) => {
              const pct = (p.total / maxTotal) * 100;
              const traitePct = p.total > 0 ? Math.round((p.traites / p.total) * 100) : 0;
              return (
                <div key={p.intitule} className="text-sm">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-gray-700 truncate max-w-xs">{p.intitule}</span>
                    <div className="flex items-center gap-2 shrink-0 ml-2">
                      {p.en_retard > 0 && (
                        <span className="text-xs text-red-600 font-medium">{p.en_retard} en retard</span>
                      )}
                      <span className="text-gray-500">{p.total} ({traitePct}% traités)</span>
                    </div>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
