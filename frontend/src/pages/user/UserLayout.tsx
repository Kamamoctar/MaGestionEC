import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import { getDashboardStats } from "../../api/dashboard";

export default function UserLayout() {
  const { utilisateur, logout } = useAuthStore();
  const isAdmin = utilisateur?.role_fonctionnel === "admin";
  const [enRetard, setEnRetard] = useState(0);

  useEffect(() => {
    getDashboardStats()
      .then((s) => setEnRetard(s.en_retard))
      .catch(() => {});
  }, []);

  const navItems = [
    { to: "/app/dashboard", label: "Tableau de bord" },
    { to: "/app/corbeilles", label: "Mes corbeilles", badge: enRetard },
    { to: "/app/recherche", label: "Recherche" },
    { to: "/app/enregistrement", label: "Enregistrer" },
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
          <button onClick={logout} className="block w-full text-left px-3 py-2 text-xs text-gray-400 hover:text-white">
            Déconnexion
          </button>
        </div>
      </aside>

      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
