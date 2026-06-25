import { NavLink, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

const navItems = [
  { to: "/app/corbeilles", label: "Mes corbeilles" },
  { to: "/app/enregistrement", label: "Enregistrer un courrier" },
];

export default function UserLayout() {
  const { utilisateur, logout } = useAuthStore();
  const isAdmin = utilisateur?.role_fonctionnel === "admin";

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-gray-900 text-white flex flex-col">
        <div className="p-5 border-b border-gray-700">
          <p className="font-bold text-lg">GEC</p>
          <p className="text-xs text-gray-400 mt-0.5">{utilisateur?.prenom} {utilisateur?.nom}</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? "bg-white text-gray-900" : "text-gray-300 hover:bg-gray-700"
                }`
              }
            >
              {item.label}
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
