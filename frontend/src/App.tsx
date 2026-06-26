import { Routes, Route, Navigate } from "react-router-dom";
import PrivateRoute from "./router/PrivateRoute";
import LoginPage from "./pages/LoginPage";
import NonAutorisePage from "./pages/NonAutorisePage";
import AidePage from "./pages/AidePage";

// Espace Admin
import AdminLayout from "./pages/admin/AdminLayout";
import PostesPage from "./pages/admin/PostesPage";
import UtilisateursPage from "./pages/admin/UtilisateursPage";
import ImportBpmnPage from "./pages/admin/ImportBpmnPage";
import DirectionsPage from "./pages/admin/DirectionsPage";
import SupervisionPage from "./pages/admin/SupervisionPage";
import CircuitsPage from "./pages/admin/CircuitsPage";

// Espace Utilisateur
import UserLayout from "./pages/user/UserLayout";
import DashboardPage from "./pages/user/DashboardPage";
import CorbeillesPage from "./pages/user/CorbeillesPage";
import RecherchePage from "./pages/user/RecherchePage";
import CourrierDetailPage from "./pages/user/CourrierDetailPage";
import EnregistrementPage from "./pages/user/EnregistrementPage";

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/non-autorise" element={<NonAutorisePage />} />

      {/* Espace Admin — rôle admin requis */}
      <Route element={<PrivateRoute roles={["admin"]} />}>
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="/admin/postes" replace />} />
          <Route path="postes" element={<PostesPage />} />
          <Route path="utilisateurs" element={<UtilisateursPage />} />
          <Route path="directions" element={<DirectionsPage />} />
          <Route path="import-bpmn" element={<ImportBpmnPage />} />
          <Route path="supervision" element={<SupervisionPage />} />
          <Route path="circuits" element={<CircuitsPage />} />
          <Route path="aide" element={<AidePage />} />
        </Route>
      </Route>

      {/* Espace Utilisateur — tout rôle authentifié */}
      <Route element={<PrivateRoute />}>
        <Route path="/app" element={<UserLayout />}>
          <Route index element={<Navigate to="/app/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="corbeilles" element={<CorbeillesPage />} />
          <Route path="recherche" element={<RecherchePage />} />
          <Route path="courriers/:id" element={<CourrierDetailPage />} />
          <Route path="enregistrement" element={<EnregistrementPage />} />
          <Route path="aide" element={<AidePage />} />
        </Route>
      </Route>

      {/* Racine → redirection */}
      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
