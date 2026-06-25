import apiClient from "./client";

export interface PieceJointe {
  id: string;
  courrier_id: string;
  nom_fichier: string;
  taille_octets: number;
  mime_type: string;
  uploaded_at: string;
}

export async function getPiecesJointes(courrierId: string): Promise<PieceJointe[]> {
  const { data } = await apiClient.get<PieceJointe[]>(`/courriers/${courrierId}/pieces-jointes`);
  return data;
}

export async function uploadPieceJointe(courrierId: string, file: File): Promise<PieceJointe> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<PieceJointe>(
    `/courriers/${courrierId}/pieces-jointes`,
    form,
  );
  return data;
}

export function downloadUrl(pjId: string): string {
  return `${apiClient.defaults.baseURL}/pieces-jointes/${pjId}/download`;
}

export async function supprimerPieceJointe(pjId: string): Promise<void> {
  await apiClient.delete(`/pieces-jointes/${pjId}`);
}

export function formatTaille(octets: number): string {
  if (octets < 1024) return `${octets} o`;
  if (octets < 1024 * 1024) return `${(octets / 1024).toFixed(0)} Ko`;
  return `${(octets / (1024 * 1024)).toFixed(1)} Mo`;
}

export function iconeType(mime: string): string {
  if (mime.includes("pdf")) return "📄";
  if (mime.includes("word") || mime.includes("document")) return "📝";
  if (mime.includes("excel") || mime.includes("sheet")) return "📊";
  if (mime.startsWith("image/")) return "🖼";
  if (mime.includes("zip")) return "🗜";
  return "📎";
}
