from collections.abc import Iterable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import and_, false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.models.courrier import Courrier, ConfidentialiteCourrier
from app.models.utilisateur import Utilisateur, RoleFonctionnel
from app.models.poste import Poste, NiveauAcces
from app.models.poste_affectation import PosteAffectation, TypeAffectation

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Utilisateur:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    result = await db.execute(select(Utilisateur).where(Utilisateur.id == user_id, Utilisateur.is_active == True))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_error
    return user


# Couche 1 : garde par rôle fonctionnel (contrôle les écrans/routes)
def require_role(*roles: RoleFonctionnel):
    async def _check(current_user: Annotated[Utilisateur, Depends(get_current_user)]) -> Utilisateur:
        if current_user.role_fonctionnel not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
        return current_user
    return _check


require_admin = require_role(RoleFonctionnel.admin)
require_secretariat = require_role(RoleFonctionnel.admin, RoleFonctionnel.secretariat)
require_direction = require_role(RoleFonctionnel.admin, RoleFonctionnel.direction)


# Couche 2 : accès aux courriers calculé sur le POSTE du connecté + confidentialité
async def get_postes_accessibles_by_user_id(db: AsyncSession, user_id: str) -> list[Poste]:
    """
    Retourne les postes dont l'utilisateur exerce actuellement les droits.

    Source principale : occupant_user_id du poste.
    Source temporaire : affectation active d'intérim ou de délégation.
    Les affectations titulaires historiques ne suffisent pas : le titulaire courant reste
    déterminé par Poste.occupant_user_id.
    """
    direct_result = await db.execute(
        select(Poste)
        .where(Poste.occupant_user_id == user_id, Poste.is_active == True)
        .order_by(Poste.intitule)
    )

    delegated_result = await db.execute(
        select(Poste)
        .join(PosteAffectation, PosteAffectation.poste_id == Poste.id)
        .where(
            Poste.is_active == True,
            PosteAffectation.utilisateur_id == user_id,
            PosteAffectation.date_fin == None,
            PosteAffectation.type.in_([TypeAffectation.interim, TypeAffectation.delegation]),
        )
        .order_by(Poste.intitule)
    )

    postes_by_id: dict[str, Poste] = {}
    for poste in list(direct_result.scalars().all()) + list(delegated_result.scalars().all()):
        postes_by_id[poste.id] = poste
    return list(postes_by_id.values())


async def get_postes_utilisateur(
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[Poste]:
    """Retourne tous les postes accessibles par l'utilisateur connecté."""
    return await get_postes_accessibles_by_user_id(db, current_user.id)


async def get_poste_utilisateur(
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Poste | None:
    """Compatibilité : retourne le premier poste accessible par l'utilisateur connecté."""
    postes = await get_postes_accessibles_by_user_id(db, current_user.id)
    return postes[0] if postes else None


def peut_voir_courrier_confidentiel(poste: Poste | None) -> bool:
    """Un courrier confidentiel n'est visible que si le poste de l'utilisateur est de niveau confidentiel."""
    if poste is None:
        return False
    return poste.niveau_acces == NiveauAcces.confidentiel


def poste_peut_acceder_courrier(poste: Poste, courrier: Courrier) -> bool:
    """Vérifie l'accès d'un poste à un courrier donné."""
    if courrier.poste_destinataire_id != poste.id:
        return False
    if courrier.confidentialite == ConfidentialiteCourrier.confidentiel:
        return poste.niveau_acces == NiveauAcces.confidentiel
    return True


def postes_peuvent_acceder_courrier(postes: Iterable[Poste], courrier: Courrier) -> bool:
    """Vérifie si au moins un des postes accessibles peut voir le courrier."""
    return any(poste_peut_acceder_courrier(poste, courrier) for poste in postes)


def courrier_access_condition(postes: Iterable[Poste]):
    """Condition SQL appliquant poste + confidentialité pour une liste de postes."""
    postes = list(postes)
    if not postes:
        return false()

    poste_ids = [poste.id for poste in postes]
    postes_confidentiels = [
        poste.id for poste in postes
        if poste.niveau_acces == NiveauAcces.confidentiel
    ]

    confidentiality_condition = Courrier.confidentialite != ConfidentialiteCourrier.confidentiel
    if postes_confidentiels:
        confidentiality_condition = or_(
            confidentiality_condition,
            Courrier.poste_destinataire_id.in_(postes_confidentiels),
        )

    return and_(
        Courrier.poste_destinataire_id.in_(poste_ids),
        confidentiality_condition,
    )
