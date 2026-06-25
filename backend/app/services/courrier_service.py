import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.courrier import Courrier, EtatCourrier, ConfidentialiteCourrier
from app.models.mouvement import Mouvement, ActionMouvement
from app.models.poste import Poste, NiveauAcces
from app.models.utilisateur import Utilisateur


def _generer_reference(type_courrier: str) -> str:
    annee = datetime.now(timezone.utc).year
    uid = uuid.uuid4().hex[:6].upper()
    prefixes = {"arrivee": "ARR", "depart": "DEP", "interne": "INT"}
    prefix = prefixes.get(type_courrier, "GEC")
    return f"{prefix}-{annee}-{uid}"


async def creer_courrier(db: AsyncSession, data: dict, created_by: Utilisateur) -> Courrier:
    courrier = Courrier(
        **data,
        id=str(uuid.uuid4()),
        reference=_generer_reference(data["type"]),
        created_by_id=created_by.id,
    )
    db.add(courrier)

    mouvement = Mouvement(
        courrier_id=courrier.id,
        utilisateur_id=created_by.id,
        action=ActionMouvement.creation,
        poste_destination_id=data["poste_destinataire_id"],
    )
    db.add(mouvement)
    await db.commit()
    await db.refresh(courrier)
    return courrier


async def transmettre_courrier(
    db: AsyncSession,
    courrier: Courrier,
    poste_destination_id: str,
    acteur: Utilisateur,
    commentaire: str | None = None,
) -> Courrier:
    poste_source_id = courrier.poste_destinataire_id
    courrier.poste_destinataire_id = poste_destination_id
    courrier.etat = EtatCourrier.en_cours
    courrier.updated_at = datetime.now(timezone.utc)

    mouvement = Mouvement(
        courrier_id=courrier.id,
        utilisateur_id=acteur.id,
        action=ActionMouvement.transmission,
        poste_source_id=poste_source_id,
        poste_destination_id=poste_destination_id,
        commentaire=commentaire,
    )
    db.add(mouvement)
    await db.commit()
    await db.refresh(courrier)
    return courrier


async def get_courriers_poste(
    db: AsyncSession,
    poste: Poste,
    etat: str | None = None,
) -> list[Courrier]:
    """
    Couche 2 : retourne uniquement les courriers du POSTE.
    Les courriers confidentiels ne sont visibles que si le poste a niveau_acces=confidentiel.
    """
    conditions = [Courrier.poste_destinataire_id == poste.id]

    if poste.niveau_acces != NiveauAcces.confidentiel:
        conditions.append(Courrier.confidentialite != ConfidentialiteCourrier.confidentiel)

    if etat:
        conditions.append(Courrier.etat == etat)

    result = await db.execute(
        select(Courrier).where(and_(*conditions)).order_by(Courrier.created_at.desc())
    )
    return list(result.scalars().all())
