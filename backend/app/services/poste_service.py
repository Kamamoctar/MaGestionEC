"""
Logique métier autour du Poste.

Règle fondamentale : les courriers, droits et historique restent liés au POSTE.
Changer l'occupant ne touche à rien d'autre — le nouvel occupant hérite
automatiquement de tout ce qui est rattaché au poste.
"""
from datetime import datetime, timezone

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.courrier import Courrier, EtatCourrier
from app.models.flux import FluxEtape
from app.models.mouvement import Mouvement
from app.models.poste import Poste
from app.models.poste_affectation import PosteAffectation, TypeAffectation


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


async def affecter_delegation(
    db: AsyncSession,
    poste: Poste,
    delegataire_id: str,
) -> Poste:
    """
    Enregistre une délégation sans changer l'occupant titulaire :
    le titulaire reste en poste mais délègue ses droits à quelqu'un d'autre.
    """
    now = datetime.now(timezone.utc)
    # Clôturer les délégations actives précédentes sur ce poste
    from sqlalchemy import update
    await db.execute(
        update(PosteAffectation)
        .where(
            PosteAffectation.poste_id == poste.id,
            PosteAffectation.type == TypeAffectation.delegation,
            PosteAffectation.date_fin == None,
        )
        .values(date_fin=now)
    )
    affectation = PosteAffectation(
        poste_id=poste.id,
        utilisateur_id=delegataire_id,
        date_debut=now,
        type=TypeAffectation.delegation,
    )
    db.add(affectation)
    await db.commit()
    await db.refresh(poste)
    return poste


async def count_courriers_actifs_poste(db: AsyncSession, poste_id: str) -> int:
    """Compte les courriers encore à traiter sur un poste."""
    result = await db.execute(
        select(func.count())
        .select_from(Courrier)
        .where(
            Courrier.poste_destinataire_id == poste_id,
            Courrier.etat.in_([EtatCourrier.en_attente, EtatCourrier.en_cours]),
        )
    )
    return result.scalar_one() or 0


async def desactiver_poste(db: AsyncSession, poste: Poste) -> Poste:
    """
    Archive fonctionnellement un poste.
    Les traces restent en base, mais le poste ne reçoit plus de nouveaux droits/courriers.
    """
    courriers_actifs = await count_courriers_actifs_poste(db, poste.id)
    if courriers_actifs > 0:
        raise ValueError("Impossible de désactiver un poste avec des courriers actifs")

    now = datetime.now(timezone.utc)
    await db.execute(
        update(PosteAffectation)
        .where(PosteAffectation.poste_id == poste.id, PosteAffectation.date_fin == None)
        .values(date_fin=now)
    )
    poste.occupant_user_id = None
    poste.is_active = False
    await db.commit()
    await db.refresh(poste)
    return poste


async def reactiver_poste(db: AsyncSession, poste: Poste) -> Poste:
    """Rend à nouveau le poste sélectionnable et affectable."""
    poste.is_active = True
    await db.commit()
    await db.refresh(poste)
    return poste


async def get_blocages_suppression_poste(db: AsyncSession, poste: Poste) -> list[str]:
    """Retourne les traces qui empêchent une suppression physique du poste."""
    blocages: list[str] = []
    if poste.occupant_user_id:
        blocages.append("occupant actif")

    checks = [
        ("courriers", select(func.count()).select_from(Courrier).where(Courrier.poste_destinataire_id == poste.id)),
        ("affectations", select(func.count()).select_from(PosteAffectation).where(PosteAffectation.poste_id == poste.id)),
        ("étapes de circuit", select(func.count()).select_from(FluxEtape).where(FluxEtape.poste_id == poste.id)),
        (
            "mouvements",
            select(func.count())
            .select_from(Mouvement)
            .where(or_(Mouvement.poste_source_id == poste.id, Mouvement.poste_destination_id == poste.id)),
        ),
    ]

    for label, stmt in checks:
        count = (await db.execute(stmt)).scalar_one() or 0
        if count > 0:
            blocages.append(f"{label}: {count}")
    return blocages


async def get_historique_affectations(db: AsyncSession, poste_id: str) -> list[PosteAffectation]:
    result = await db.execute(
        select(PosteAffectation)
        .where(PosteAffectation.poste_id == poste_id)
        .order_by(PosteAffectation.date_debut.desc())
    )
    return list(result.scalars().all())
