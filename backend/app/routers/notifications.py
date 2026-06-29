"""
Notifications temps réel via Server-Sent Events.

Le client se connecte à GET /notifications/stream?token=<jwt> et reçoit
un événement 'nouveau_courrier' à chaque nouveau courrier assigné à son poste.
Le token JWT est passé en query param car EventSource ne supporte pas les headers.
"""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import courrier_access_condition, get_postes_accessibles_by_user_id
from app.core.security import decode_token as decode_access_token
from app.database import AsyncSessionLocal
from app.models.courrier import Courrier, EtatCourrier
from app.models.poste import Poste
from app.models.utilisateur import Utilisateur

router = APIRouter(prefix="/notifications", tags=["notifications"])

POLL_INTERVAL = 6  # secondes entre chaque vérification DB
KEEPALIVE_INTERVAL = 20  # secondes entre les pings keepalive


async def _get_user_and_postes(token: str) -> tuple[Utilisateur, list[Poste]] | None:
    """Résout le token JWT en (utilisateur, postes accessibles). Retourne None si invalide."""
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None

    async with AsyncSessionLocal() as db:
        user_res = await db.execute(select(Utilisateur).where(Utilisateur.id == user_id))
        user = user_res.scalar_one_or_none()
        if not user:
            return None

        postes = await get_postes_accessibles_by_user_id(db, user_id)
        return user, postes


@router.get("/stream")
async def stream(token: Annotated[str, Query(description="JWT access token")]):
    """
    Flux SSE — envoie un événement quand un nouveau courrier arrive sur le poste.
    Format : data: {"type": "nouveau_courrier", "reference": "ARR-2026-0001", "objet": "..."}
    """
    result = await _get_user_and_postes(token)
    if result is None:
        raise HTTPException(status_code=401, detail="Token invalide")

    _, postes = result
    if not postes:
        # Pas de poste → flux vide mais valide (keepalive uniquement)
        pass

    async def generate():
        last_check = datetime.now(timezone.utc)
        last_keepalive = datetime.now(timezone.utc)
        known_ids: set[str] = set()

        # Initialiser les IDs déjà présents pour ne pas notifier l'historique
        if postes:
            async with AsyncSessionLocal() as db:
                res = await db.execute(
                    select(Courrier.id)
                    .where(courrier_access_condition(postes))
                )
                known_ids = {row[0] for row in res.all()}

        try:
            while True:
                now = datetime.now(timezone.utc)

                # Keepalive pour maintenir la connexion ouverte (proxy nginx, etc.)
                if (now - last_keepalive).total_seconds() >= KEEPALIVE_INTERVAL:
                    yield ": ping\n\n"
                    last_keepalive = now

                # Vérification des nouveaux courriers
                if postes and (now - last_check).total_seconds() >= POLL_INTERVAL:
                    async with AsyncSessionLocal() as db:
                        res = await db.execute(
                            select(Courrier)
                            .where(
                                courrier_access_condition(postes),
                                Courrier.etat.in_([EtatCourrier.en_attente, EtatCourrier.en_cours]),
                                Courrier.created_at >= last_check - timedelta(seconds=POLL_INTERVAL + 2),
                            )
                        )
                        nouveaux = [c for c in res.scalars().all() if c.id not in known_ids]

                    for c in nouveaux:
                        known_ids.add(c.id)
                        payload = json.dumps({
                            "type": "nouveau_courrier",
                            "id": c.id,
                            "reference": c.reference,
                            "objet": c.objet,
                            "expediteur": c.expediteur,
                            "priorite": c.priorite,
                        }, ensure_ascii=False)
                        yield f"data: {payload}\n\n"

                    last_check = now

                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # désactive le buffering nginx
        },
    )
