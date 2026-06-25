from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.models.utilisateur import Utilisateur, RoleFonctionnel
from app.models.poste import Poste, NiveauAcces

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
async def get_poste_utilisateur(
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Poste | None:
    """Retourne le poste actuellement occupé par l'utilisateur connecté."""
    result = await db.execute(
        select(Poste).where(Poste.occupant_user_id == current_user.id, Poste.is_active == True)
    )
    return result.scalar_one_or_none()


def peut_voir_courrier_confidentiel(poste: Poste | None) -> bool:
    """Un courrier confidentiel n'est visible que si le poste de l'utilisateur est de niveau confidentiel."""
    if poste is None:
        return False
    return poste.niveau_acces == NiveauAcces.confidentiel
