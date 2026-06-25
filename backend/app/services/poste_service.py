"""
Logique métier autour du Poste.

Règle fondamentale : les courriers, droits et historique restent liés au POSTE.
Changer l'occupant ne touche à rien d'autre — le nouvel occupant hérite
automatiquement de tout ce qui est rattaché au poste.
"""
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.poste import Poste
from app.models.poste_affectation import PosteAffectation, TypeAffectation
from app.models.utilisateur import Utilisateur


async def changer_occupant(
    db: AsyncSession,
    poste: Poste,
    nouvel_utilisateur_id: str | None,
    type_affectation: TypeAffectation = TypeAffectation.titulaire,
) -> Poste:
    """
    Transfère le poste à un nouvel occupant.
    1. Clôture l'affectation active en cours (date_fin = maintenant).
    2. Crée une nouvelle affectation pour le nouvel occupant.
    3. Met à jour occupant_user_id sur le poste.
    Les courriers et droits ne bougent pas — ils restent liés au poste.
    """
    now = datetime.now(timezone.utc)

    # Clôturer toutes les affectations actives (date_fin null)
    await db.execute(
        update(PosteAffectation)
        .where(PosteAffectation.poste_id == poste.id, PosteAffectation.date_fin == None)
        .values(date_fin=now)
    )

    if nouvel_utilisateur_id is not None:
        nouvelle_affectation = PosteAffectation(
            poste_id=poste.id,
            utilisateur_id=nouvel_utilisateur_id,
            date_debut=now,
            type=type_affectation,
        )
        db.add(nouvelle_affectation)

    poste.occupant_user_id = nouvel_utilisateur_id
    await db.commit()
    await db.refresh(poste)
    return poste


async def liberer_poste(db: AsyncSession, poste: Poste) -> Poste:
    """Retire l'occupant courant sans en affecter un nouveau."""
    return await changer_occupant(db, poste, None)


async def affecter_interimaire(
    db: AsyncSession,
    poste: Poste,
    interimaire_id: str,
) -> Poste:
    """Affecte un intérimaire sans clôturer l'affectation titulaire."""
    now = datetime.now(timezone.utc)
    affectation = PosteAffectation(
        poste_id=poste.id,
        utilisateur_id=interimaire_id,
        date_debut=now,
        type=TypeAffectation.interim,
    )
    db.add(affectation)
    # L'occupant courant (interface utilisateur) devient l'intérimaire
    poste.occupant_user_id = interimaire_id
    await db.commit()
    await db.refresh(poste)
    return poste


async def get_historique_affectations(db: AsyncSession, poste_id: str) -> list[PosteAffectation]:
    result = await db.execute(
        select(PosteAffectation)
        .where(PosteAffectation.poste_id == poste_id)
        .order_by(PosteAffectation.date_debut.desc())
    )
    return list(result.scalars().all())
