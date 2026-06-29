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
  tenant_id?: string | null;
  intitule: string;
  direction_id: string | null;
  occupant_user_id: string | null;
  niveau_acces: "normal" | "confidentiel";
  is_active: boolean;
}

export interface Courrier {
  id: string;
  tenant_id?: string | null;
  reference: string;
  objet: string;
  expediteur: string;
  reference_expediteur: string | null;
  poste_destinataire_id: string;
  tenant_expediteur_id?: string | null;
  tenant_destinataire_id?: string | null;
  courrier_lie_id?: string | null;
  type: "arrivee" | "depart" | "interne";
  priorite: "normal" | "urgent" | "tres_urgent";
  confidentialite: "normal" | "confidentiel";
  date_reception: string;
  date_limite: string | null;
  etat: "en_attente" | "en_cours" | "traite" | "archive";
  flux_id: string | null;
  etape_courante_id: string | null;
  type_action_courante: "distribution" | "visa" | "signature" | "information" | null;
  courrier_parent_id: string | null;
  dossier_id: string | null;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface CourrierLiaison {
  id: string;
  reference: string;
  objet: string;
  type: "arrivee" | "depart" | "interne";
  etat: "en_attente" | "en_cours" | "traite" | "archive";
  priorite: "normal" | "urgent" | "tres_urgent";
  date_reception: string;
  expediteur: string;
}

export interface Dossier {
  id: string;
  tenant_id?: string | null;
  titre: string;
  description: string | null;
  created_by_id: string;
  created_at: string;
  nb_courriers: number;
}

export interface Direction {
  id: string;
  tenant_id?: string | null;
  nom: string;
  description: string | null;
}

export interface FluxEtape {
  id: string;
  flux_id: string;
  ordre: number;
  poste_id: string;
  intitule_poste: string | null;
  type_action: "distribution" | "visa" | "signature" | "information";
  condition_transition: string | null;
  is_terminal: boolean;
}

export interface Flux {
  id: string;
  tenant_id?: string | null;
  nom: string;
  description: string | null;
  etapes: FluxEtape[];
}

export interface Tenant {
  id: string;
  nom: string;
  slug: string;
  is_active: boolean;
  created_at: string;
}
