import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import type { RoleFonctionnel } from "../types";

interface Props {
  roles?: RoleFonctionnel[];
}

export default function PrivateRoute({ roles }: Props) {
  const { token, utilisateur } = useAuthStore();

  if (!token || !utilisateur) {
    return <Navigate to="/login" replace />;
  }

  if (roles && !roles.includes(utilisateur.role_fonctionnel)) {
    return <Navigate to="/non-autorise" replace />;
  }

  return <Outlet />;
}
