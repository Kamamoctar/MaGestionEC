import { NavLink, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

const navItems = [
  { to: "/admin/postes", label: "Postes" },
  { to: "/admin/utilisateurs", label: "Utilisateurs" },
  { to: "/admin/directions", label: "Directions" },
  { to: "/admin/import-bpmn", label: "Import BPMN" },
];

export default function AdminLayout() {
  const { utilisateur, logout } = useAuthStore();

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-56 bg-primary text-white flex flex-col">
        <div className="p-5 border-b border-blue-800">
          <p className="font-bold text-lg">GEC Admin</p>
          <p className="text-xs text-blue-300 mt-0.5">{utilisateur?.prenom} {utilisateur?.nom}</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? "bg-white text-primary" : "text-blue-100 hover:bg-blue-800"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-blue-800">
          <NavLink to="/app" className="block px-3 py-2 text-xs text-blue-300 hover:text-white">
            Espace utilisateur →
          </NavLink>
          <NavLink
            to="/admin/aide"
            className={({ isActive }) =>
              `block px-3 py-2 text-xs transition-colors ${isActive ? "text-white" : "text-blue-300 hover:text-white"}`
            }
          >
            Aide & documentation
          </NavLink>
          <button onClick={logout} className="block w-full text-left px-3 py-2 text-xs text-blue-300 hover:text-white">
            Déconnexion
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
