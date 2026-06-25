import { Link } from "react-router-dom";

export default function NonAutorisePage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4">
      <h1 className="text-3xl font-bold text-gray-700">Accès refusé</h1>
      <p className="text-gray-500">Vous n'avez pas les droits nécessaires pour accéder à cette page.</p>
      <Link to="/" className="text-primary underline">Retour à l'accueil</Link>
    </div>
  );
}
