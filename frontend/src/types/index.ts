export type RoleFonctionnel = "admin" | "secretariat" | "agent" | "direction";

export interface Utilisateur {
  id: string;
  nom: string;
  prenom: string;
  email: string;
  role_fonctionnel: RoleFonctionnel;
  is_active: boolean;
  created_at: string;
}

export interface Poste {
  id: string;
  intitule: string;
  direction_id: string | null;
  occupant_user_id: string | null;
  niveau_acces: "normal" | "confidentiel";
  is_active: boolean;
}

export interface Courrier {
  id: string;
  reference: string;
  objet: string;
  expediteur: string;
  poste_destinataire_id: string;
  type: "arrivee" | "depart" | "interne";
  priorite: "normal" | "urgent" | "tres_urgent";
  confidentialite: "normal" | "confidentiel";
  date_reception: string;
  date_limite: string | null;
  etat: "en_attente" | "en_cours" | "traite" | "archive";
  flux_id: string | null;
  etape_courante_id: string | null;
  type_action_courante: "distribution" | "visa" | "signature" | "information" | null;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface Direction {
  id: string;
  nom: string;
  description: string | null;
}

export interface FluxEtape {
  id: string;
  flux_id: string;
  ordre: number;
  poste_id: string;
  type_action: "distribution" | "visa" | "signature" | "information";
  condition_transition: string | null;
  is_terminal: boolean;
}

export interface Flux {
  id: string;
  nom: string;
  description: string | null;
  etapes: FluxEtape[];
}
