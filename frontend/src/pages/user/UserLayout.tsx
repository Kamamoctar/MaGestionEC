import { useCallback, useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import { getDashboardStats } from "../../api/dashboard";
import { useNotifications, type NotifEvent } from "../../hooks/useNotifications";

interface Toast {
  id: number;
  message: string;
  reference: string;
  priorite: string;
}

const PRIORITE_TOAST: Record<string, string> = {
  tres_urgent: "border-red-400 bg-red-50",
  urgent:      "border-orange-400 bg-orange-50",
  normal:      "border-blue-300 bg-blue-50",
};

export default function UserLayout() {
  const { utilisateur, logout } = useAuthStore();
  const isAdmin = utilisateur?.role_fonctionnel === "admin";
  const [enRetard, setEnRetard] = useState(0);
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    getDashboardStats()
      .then((s) => setEnRetard(s.en_retard))
      .catch(() => {});
  }, []);

  const handleNotif = useCallback((e: NotifEvent) => {
    if (e.type !== "nouveau_courrier") return;
    const id = Date.now();
    const toast: Toast = {
      id,
      message: e.objet,
      reference: e.reference,
      priorite: e.priorite,
    };
    setToasts((prev) => [...prev.slice(-3), toast]); // max 4 toasts simultanés
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 6000);
    // Incrémenter le badge si retard (la valeur réelle sera rafraîchie au prochain cycle)
  }, []);

  useNotifications(handleNotif);

  const navItems = [
    { to: "/app/dashboard",     label: "Tableau de bord" },
    { to: "/app/corbeilles",    label: "Mes corbeilles", badge: enRetard },
    { to: "/app/recherche",     label: "Recherche" },
    { to: "/app/enregistrement",label: "Enregistrer" },
  ];

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-gray-900 text-white flex flex-col">
        <div className="p-5 border-b border-gray-700">
          <p className="font-bold text-lg">GEC</p>
          <p className="text-xs text-gray-400 mt-0.5">{utilisateur?.prenom} {utilisateur?.nom}</p>
          {enRetard > 0 && (
            <p className="text-xs text-red-400 mt-1 font-medium">
              ⚠ {enRetard} en retard
            </p>
          )}
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? "bg-white text-gray-900" : "text-gray-300 hover:bg-gray-700"
                }`
              }
            >
              <span>{item.label}</span>
              {item.badge != null && item.badge > 0 && (
                <span className="ml-2 bg-red-500 text-white text-xs font-bold rounded-full px-1.5 py-0.5 min-w-[1.25rem] text-center">
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-gray-700 space-y-1">
          {isAdmin && (
            <NavLink to="/admin" className="block px-3 py-2 text-xs text-gray-400 hover:text-white">
              Espace admin →
            </NavLink>
          )}
          <NavLink
            to="/app/aide"
            className={({ isActive }) =>
              `block px-3 py-2 text-xs transition-colors ${isActive ? "text-white" : "text-gray-400 hover:text-white"}`
            }
          >
            Aide & documentation
          </NavLink>
          <button onClick={logout} className="block w-full text-left px-3 py-2 text-xs text-gray-400 hover:text-white">
            Déconnexion
          </button>
        </div>
      </aside>

      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>

      {/* Toasts notifications temps réel */}
      {toasts.length > 0 && (
        <div className="fixed bottom-5 right-5 flex flex-col gap-2 z-50 max-w-sm">
          {toasts.map((t) => (
            <div
              key={t.id}
              className={`flex items-start gap-3 p-3 rounded-xl border shadow-lg text-sm animate-in slide-in-from-bottom-4 duration-300 ${PRIORITE_TOAST[t.priorite] ?? "border-blue-300 bg-blue-50"}`}
            >
              <span className="text-blue-600 text-lg shrink-0">📬</span>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-800 text-xs">Nouveau courrier — {t.reference}</p>
                <p className="text-gray-600 truncate">{t.message}</p>
              </div>
              <button
                onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
                className="shrink-0 text-gray-400 hover:text-gray-600 text-xs"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
