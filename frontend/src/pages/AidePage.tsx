import { useState } from "react";

type Section = { title: string; content: React.ReactNode };

const ADMIN_SECTIONS: Section[] = [
  {
    title: "Gestion des Postes",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>Un <strong>poste</strong> représente une fonction (ex : Directeur Général, Secrétariat). C'est l'entité centrale de GEC : les courriers, droits et historiques sont rattachés au poste, jamais à la personne.</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li><strong>Créer un poste</strong> : cliquez « + Nouveau poste », saisissez l'intitulé.</li>
          <li><strong>Affecter un titulaire</strong> : bouton « Affecter / Changer » → sélectionnez un utilisateur actif. Tous les courriers en cours du poste lui sont instantanément accessibles.</li>
          <li><strong>Intérim</strong> : bouton « Intérim » (violet) → l'intérimaire hérite temporairement des courriers et droits du poste sans modifier l'affectation titulaire.</li>
          <li><strong>Libérer un poste</strong> : bouton « Libérer » → le poste devient vacant. Les courriers restent attachés au poste.</li>
        </ul>
      </div>
    ),
  },
  {
    title: "Gestion des Utilisateurs",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>Un <strong>utilisateur</strong> est une personne physique. Son rôle fonctionnel détermine les écrans accessibles.</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li><strong>admin</strong> : accès complet à l'espace admin et à l'espace utilisateur.</li>
          <li><strong>secrétariat</strong> : peut enregistrer des courriers et les transmettre.</li>
          <li><strong>agent</strong> : consulte et traite les courriers de son poste.</li>
          <li><strong>direction</strong> : vise et signe dans le parapheur.</li>
        </ul>
        <p className="mt-2">Pour créer un compte : renseignez prénom, nom, e-mail, mot de passe et rôle. Activez / désactivez un compte via le bouton correspondant (un compte désactivé ne peut plus se connecter).</p>
      </div>
    ),
  },
  {
    title: "Gestion des Directions",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>Une <strong>direction</strong> est une entité organisationnelle (DG, DRH, DAF…). Les postes peuvent être rattachés à une direction pour faciliter le filtrage.</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>Créez une direction avec un nom et une description optionnelle.</li>
          <li>Modifiez-la via le crayon, supprimez-la via la corbeille (uniquement si aucun poste ne l'utilise).</li>
        </ul>
      </div>
    ),
  },
  {
    title: "Import de circuits BPMN",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>Un <strong>circuit</strong> définit l'itinéraire d'un courrier (étapes, responsables, types d'action). Il est créé en important un fichier BPMN (Camunda Modeler, draw.io, Signavio…).</p>
        <ol className="list-decimal pl-5 space-y-1 mt-2">
          <li><strong>Étape 1 — Upload</strong> : glissez-déposez votre fichier <code>.bpmn</code> ou <code>.xml</code>.</li>
          <li><strong>Étape 2 — Mapping</strong> : chaque lane détectée est associée à un poste et à un type d'action (visa / signature / distribution / information). L'ordre topologique des lanes est préservé.</li>
          <li><strong>Étape 3 — Génération</strong> : donnez un nom au circuit et cliquez « Générer ». Le circuit est prêt à être utilisé à l'enregistrement des courriers.</li>
        </ol>
        <p className="mt-2 text-orange-600">La dernière étape du circuit est automatiquement marquée comme terminale : un visa/signature sur cette étape clôture le courrier (état = traité).</p>
      </div>
    ),
  },
  {
    title: "Niveaux de confidentialité",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>GEC applique deux niveaux de confidentialité :</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li><strong>Normal</strong> : visible par tous les postes qui reçoivent le courrier.</li>
          <li><strong>Confidentiel</strong> : visible uniquement par les postes dont le <em>niveau d'accès</em> est défini à « confidentiel ». Configurez ce niveau sur le poste lui-même.</li>
        </ul>
        <p className="mt-2">Ce filtre s'applique dans les corbeilles <em>et</em> dans la recherche.</p>
      </div>
    ),
  },
];

const USER_SECTIONS: Section[] = [
  {
    title: "Tableau de bord",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>Le tableau de bord s'affiche à la connexion. Il présente :</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li><strong>5 cartes KPI</strong> : Total / En attente / En cours / Traités / En retard.</li>
          <li><strong>Alerte rouge</strong> si des courriers ont dépassé leur date limite.</li>
          <li><strong>Barres de répartition</strong> par état.</li>
          <li><strong>Top postes</strong> (admin uniquement) : volume et taux de traitement par poste.</li>
        </ul>
      </div>
    ),
  },
  {
    title: "Mes corbeilles",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>Affiche les courriers en attente dans votre poste courant. Filtrez par onglet :</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li><strong>Tout</strong> : tous les courriers du poste.</li>
          <li><strong>À traiter</strong> : état en_attente (pas encore ouvert dans un circuit).</li>
          <li><strong>En cours</strong> : courriers en circulation dans un circuit.</li>
          <li><strong>Traités</strong> : courriers dont le circuit est terminé.</li>
        </ul>
        <p className="mt-2">Les badges <span className="text-red-600 font-medium">⚠ RETARD</span> et <span className="text-orange-600 font-medium">⏱ URGENT</span> signalent respectivement les courriers dont l'échéance est dépassée ou dans moins de 48h.</p>
      </div>
    ),
  },
  {
    title: "Enregistrer un courrier",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>Rôle requis : <strong>secrétariat</strong> (ou admin).</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>Renseignez l'objet, l'expéditeur, le type (arrivée / départ / interne) et la priorité.</li>
          <li><strong>Circuit de traitement</strong> (optionnel) : sélectionnez un circuit BPMN. Le courrier est automatiquement dirigé vers la première étape du circuit — le champ « Poste destinataire » disparaît car le circuit définit le routage.</li>
          <li>Sans circuit : choisissez manuellement le poste destinataire. Le courrier peut ensuite être transmis de poste en poste via le bouton « Transmettre ».</li>
          <li>La référence (ARR-2026-XXXXXX / DEP / INT) est générée automatiquement.</li>
        </ul>
      </div>
    ),
  },
  {
    title: "Parapheur — visa, signature, annotation",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>Ouvrez un courrier depuis les corbeilles. Dans la zone d'actions :</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li><strong>Viser / Signer</strong> : action principale selon l'étape courante. Si le circuit est à l'étape terminale, le courrier passe à l'état « Traité ».</li>
          <li><strong>Annoter</strong> : ajoute un commentaire sans faire avancer le circuit.</li>
          <li><strong>Transmettre →</strong> : envoie le courrier à un autre poste (hors circuit ou pour les courriers sans circuit).</li>
          <li><strong>↩ Retourner</strong> : renvoie le courrier au poste émetteur précédent.</li>
          <li><strong>Archiver</strong> : disponible uniquement sur les courriers traités. Retire le courrier des corbeilles actives de façon définitive.</li>
        </ul>
      </div>
    ),
  },
  {
    title: "Pièces jointes",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>Dans le détail d'un courrier, section « Pièces jointes » :</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li><strong>Ajouter</strong> : cliquez « + Ajouter » (formats PDF, Word, Excel, images, ZIP — max 20 Mo).</li>
          <li><strong>Télécharger</strong> : le téléchargement est authentifié (pas de lien public direct).</li>
          <li><strong>Supprimer</strong> : bouton ✕ à droite du fichier.</li>
        </ul>
        <p className="mt-2">Les fichiers sont stockés sur le serveur, seule la référence est en base de données.</p>
      </div>
    ),
  },
  {
    title: "Historique des mouvements",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>En bas du détail de chaque courrier, une frise chronologique affiche tous les mouvements : enregistrement, transmissions, visas, signatures, annotations, retours et archivages.</p>
        <p className="mt-2">L'historique est <strong>immuable</strong> : aucun mouvement ne peut être supprimé, ce qui garantit la traçabilité complète du courrier.</p>
      </div>
    ),
  },
  {
    title: "Recherche avancée",
    content: (
      <div className="space-y-2 text-sm text-gray-600">
        <p>Accessible via le lien « Recherche » dans la barre latérale.</p>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li><strong>Texte libre</strong> : cherche dans l'objet, l'expéditeur et la référence.</li>
          <li><strong>Filtres</strong> : type, état, priorité, plage de dates de réception.</li>
          <li>Les résultats sont cliquables pour accéder au détail du courrier.</li>
          <li>Les courriers confidentiels hors de votre niveau d'accès n'apparaissent jamais dans les résultats.</li>
        </ul>
      </div>
    ),
  },
];

function AccordionSection({ title, content }: Section) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-3.5 bg-white hover:bg-gray-50 text-left"
      >
        <span className="font-medium text-gray-800 text-sm">{title}</span>
        <span className="text-gray-400 text-lg leading-none">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="px-5 py-4 bg-gray-50 border-t">
          {content}
        </div>
      )}
    </div>
  );
}

export default function AidePage() {
  const [tab, setTab] = useState<"user" | "admin">("user");

  const sections = tab === "admin" ? ADMIN_SECTIONS : USER_SECTIONS;

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-semibold text-gray-800 mb-2">Aide & documentation</h1>
      <p className="text-sm text-gray-500 mb-6">
        GEC — Gestion Électronique des Courriers. Consultez la section correspondant à votre profil.
      </p>

      {/* Onglets */}
      <div className="flex gap-2 mb-6">
        {(["user", "admin"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              tab === t ? "bg-primary text-white" : "bg-white border text-gray-600 hover:border-primary"
            }`}
          >
            {t === "user" ? "Espace utilisateur" : "Espace administrateur"}
          </button>
        ))}
      </div>

      {/* Sections accordéon */}
      <div className="space-y-2">
        {sections.map((s) => (
          <AccordionSection key={s.title} title={s.title} content={s.content} />
        ))}
      </div>

      <p className="mt-8 text-xs text-gray-400 text-center">
        GEC v0.1.0 — Pour signaler un problème, contactez votre administrateur système.
      </p>
    </div>
  );
}
