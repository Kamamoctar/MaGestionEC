import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth import get_current_user, get_poste_utilisateur
from app.database import get_db
from app.models.courrier import Courrier
from app.models.piece_jointe import PieceJointe
from app.models.poste import Poste
from app.models.utilisateur import Utilisateur
from app.schemas.piece_jointe import PieceJointeOut

router = APIRouter(tags=["pieces_jointes"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 Mo

MIME_AUTORISES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "text/plain", "application/zip",
    # Fallback pour navigateurs qui envoient octet-stream
    "application/octet-stream",
}


async def _get_courrier_avec_acces(
    courrier_id: str,
    db: AsyncSession,
    poste: Poste | None,
) -> Courrier:
    result = await db.execute(select(Courrier).where(Courrier.id == courrier_id))
    courrier = result.scalar_one_or_none()
    if not courrier:
        raise HTTPException(status_code=404, detail="Courrier introuvable")
    if poste is None or courrier.poste_destinataire_id != poste.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    return courrier


@router.get("/courriers/{courrier_id}/pieces-jointes", response_model=list[PieceJointeOut])
async def lister(
    courrier_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    poste: Annotated[Poste | None, Depends(get_poste_utilisateur)],
):
    await _get_courrier_avec_acces(courrier_id, db, poste)
    result = await db.execute(
        select(PieceJointe)
        .where(PieceJointe.courrier_id == courrier_id)
        .order_by(PieceJointe.uploaded_at)
    )
    return list(result.scalars().all())


@router.post(
    "/courriers/{courrier_id}/pieces-jointes",
    response_model=PieceJointeOut,
    status_code=status.HTTP_201_CREATED,
)
async def uploader(
    courrier_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
    poste: Poste | None = Depends(get_poste_utilisateur),
):
    await _get_courrier_avec_acces(courrier_id, db, poste)

    contenu = await file.read()
    if len(contenu) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 20 Mo)")

    mime = file.content_type or "application/octet-stream"
    if mime not in MIME_AUTORISES:
        raise HTTPException(status_code=415, detail=f"Type de fichier non autorisé : {mime}")

    # Chemin : uploads/<courrier_id>/<uuid>_<nom_original>
    dossier = Path(settings.UPLOADS_DIR) / courrier_id
    dossier.mkdir(parents=True, exist_ok=True)
    nom_original = file.filename or "fichier"
    nom_stockage = f"{uuid.uuid4().hex}_{nom_original}"
    chemin = dossier / nom_stockage

    chemin.write_bytes(contenu)

    pj = PieceJointe(
        courrier_id=courrier_id,
        nom_fichier=nom_original,
        chemin_stockage=str(chemin),
        taille_octets=len(contenu),
        mime_type=mime,
    )
    db.add(pj)
    await db.commit()
    await db.refresh(pj)
    return pj


@router.get("/pieces-jointes/{pj_id}/download")
async def telecharger(
    pj_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    poste: Annotated[Poste | None, Depends(get_poste_utilisateur)],
):
    result = await db.execute(select(PieceJointe).where(PieceJointe.id == pj_id))
    pj = result.scalar_one_or_none()
    if not pj:
        raise HTTPException(status_code=404, detail="Pièce jointe introuvable")

    # Vérifier l'accès via le courrier
    await _get_courrier_avec_acces(pj.courrier_id, db, poste)

    if not os.path.exists(pj.chemin_stockage):
        raise HTTPException(status_code=410, detail="Fichier manquant sur le serveur")

    return FileResponse(
        path=pj.chemin_stockage,
        filename=pj.nom_fichier,
        media_type=pj.mime_type,
    )


@router.delete("/pieces-jointes/{pj_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer(
    pj_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    poste: Annotated[Poste | None, Depends(get_poste_utilisateur)],
):
    result = await db.execute(select(PieceJointe).where(PieceJointe.id == pj_id))
    pj = result.scalar_one_or_none()
    if not pj:
        raise HTTPException(status_code=404, detail="Pièce jointe introuvable")

    await _get_courrier_avec_acces(pj.courrier_id, db, poste)

    # Supprimer le fichier physique
    try:
        os.remove(pj.chemin_stockage)
    except FileNotFoundError:
        pass

    await db.delete(pj)
    await db.commit()
