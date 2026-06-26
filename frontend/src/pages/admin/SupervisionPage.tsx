import { useEffect, useState } from "react";
import { getSupervision, type SupervisionData } from "../../api/supervision";
import { getDashboardStats, type DashboardStats } from "../../api/dashboard";

const ACTION_COLORS: Record<string, string> = {
  visa: "bg-blue-100 text-blue-700",
  signature: "bg-purple-100 text-purple-700",
  distribution: "bg-green-100 text-green-700",
  information: "bg-teal-100 text-teal-700",
};

function KpiCard({ label, value, color, sub }: { label: string; value: number; color: string; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border p-5 flex flex-col gap-1">
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400">{sub}</p>}
    </div>
  );
}

export default function SupervisionPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [supervision, setSupervision] = useState<SupervisionData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getDashboardStats(), getSupervision()])
      .then(([s, sv]) => { setStats(s); setSupervision(sv); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-400">Chargement…</div>;
  if (!stats || !supervision) return null;

  const maxDir = Math.max(...supervision.par_direction.map((d) => d.total), 1);
  const tauxTraitement = stats.total > 0 ? Math.round((stats.traites / stats.total) * 100) : 0;

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-gray-800">Supervision</h1>

      {/* KPIs globaux */}
      {stats.en_retard > 0 && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          <span className="text-xl">⚠️</span>
          <strong>{stats.en_retard} courrier{stats.en_retard > 1 ? "s" : ""} en retard</strong>
          <span>sur l'ensemble des postes</span>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard label="Total" value={stats.total} color="text-gray-800" />
        <KpiCard label="En attente" value={stats.en_attente} color="text-orange-500" />
        <KpiCard label="En cours" value={stats.en_cours} color="text-blue-600" />
        <KpiCard label="Traités" value={stats.traites} color="text-green-600"
          sub={`${tauxTraitement} % du total`} />
        <KpiCard label="En retard" value={stats.en_retard} color="text-red-600" />
      </div>

      {/* Répartition par direction */}
      {supervision.par_direction.length > 0 && (
        <div className="bg-white rounded-xl border p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-5">Volume par direction</h2>
          <div className="space-y-4">
            {supervision.par_direction.map((d) => {
              const taux = d.total > 0 ? Math.round((d.traites / d.total) * 100) : 0;
              return (
                <div key={d.direction_id}>
                  <div className="flex items-center justify-between text-sm mb-1.5">
                    <span className="font-medium text-gray-700">{d.nom}</span>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      {d.en_retard > 0 && (
                        <span className="text-red-600 font-medium">⚠ {d.en_retard} en retard</span>
                      )}
                      <span>{d.en_attente} att. / {d.en_cours} en cours / {d.traites} traités</span>
                      <span className="font-semibold">{d.total} total ({taux}%)</span>
                    </div>
                  </div>
                  <div className="h-3 bg-gray-100 rounded-full overflow-hidden flex">
                    {/* Barre empilée : en_attente / en_cours / traites */}
                    {d.en_attente > 0 && (
                      <div
                        className="h-full bg-orange-400"
                        style={{ width: `${(d.en_attente / maxDir) * 100}%` }}
                        title={`En attente : ${d.en_attente}`}
                      />
                    )}
                    {d.en_cours > 0 && (
                      <div
                        className="h-full bg-blue-500"
                        style={{ width: `${(d.en_cours / maxDir) * 100}%` }}
                        title={`En cours : ${d.en_cours}`}
                      />
                    )}
                    {d.traites > 0 && (
                      <div
                        className="h-full bg-green-500"
                        style={{ width: `${(d.traites / maxDir) * 100}%` }}
                        title={`Traités : ${d.traites}`}
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex items-center gap-4 mt-4 text-xs text-gray-400">
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-orange-400 inline-block" /> En attente</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-blue-500 inline-block" /> En cours</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-green-500 inline-block" /> Traités</span>
          </div>
        </div>
      )}

      {supervision.par_direction.length === 0 && (
        <div className="bg-white rounded-xl border p-6 text-center text-gray-400 text-sm">
          Aucune direction configurée ou aucun poste rattaché à une direction.
        </div>
      )}

      {/* Circuits actifs */}
      <div className="bg-white rounded-xl border p-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-5">
          Circuits actifs
          {supervision.circuits_actifs.length > 0 && (
            <span className="ml-2 text-xs text-gray-400 font-normal">
              — courriers actuellement en circulation
            </span>
          )}
        </h2>

        {supervision.circuits_actifs.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-4">
            Aucun courrier en circulation dans un circuit pour l'instant.
          </p>
        ) : (
          <div className="space-y-5">
            {supervision.circuits_actifs.map((c) => (
              <div key={c.flux_id} className="border rounded-xl overflow-hidden">
                {/* En-tête circuit */}
                <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b">
                  <div>
                    <p className="font-medium text-gray-800 text-sm">{c.flux_nom}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {c.total_en_cours} courrier{c.total_en_cours > 1 ? "s" : ""} en circulation
                    </p>
                  </div>
                  <span className="px-2.5 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full">
                    {c.total_en_cours} en cours
                  </span>
                </div>

                {/* Étapes avec courriers bloqués */}
                <div className="divide-y">
                  {c.etapes.map((e) => (
                    <div key={`${c.flux_id}-${e.ordre}`} className="flex items-center gap-4 px-4 py-3">
                      <span className="w-6 h-6 rounded-full bg-gray-200 text-gray-600 text-xs flex items-center justify-center font-bold shrink-0">
                        {e.ordre}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-700 truncate">{e.intitule_poste}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ACTION_COLORS[e.type_action] ?? "bg-gray-100 text-gray-600"}`}>
                        {e.type_action}
                      </span>
                      <span className="shrink-0 px-2.5 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-700">
                        {e.nb_courriers} bloqué{e.nb_courriers > 1 ? "s" : ""}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
