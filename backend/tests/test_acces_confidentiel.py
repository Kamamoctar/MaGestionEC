"""
Tests de la couche 2 de sécurité : accès aux courriers calculé sur le POSTE.
Un agent sans poste de niveau confidentiel ne doit pas voir les courriers confidentiels.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.utilisateur import RoleFonctionnel
from app.models.poste import Poste, NiveauAcces
from app.models.courrier import Courrier, TypeCourrier, ConfidentialiteCourrier, EtatCourrier
from app.models.piece_jointe import PieceJointe
from app.services.courrier_service import get_courriers_poste
from tests.conftest import _create_user, _get_token

import uuid


def _ref():
    return f"TEST-{uuid.uuid4().hex[:6].upper()}"


@pytest.mark.asyncio
async def test_poste_normal_ne_voit_pas_confidentiel(db: AsyncSession):
    user = await _create_user(db, "agent_normal@test.com", RoleFonctionnel.agent)

    poste_normal = Poste(intitule="Agent Normal", occupant_user_id=user.id, niveau_acces=NiveauAcces.normal)
    db.add(poste_normal)
    await db.commit()
    await db.refresh(poste_normal)

    courrier_conf = Courrier(
        reference=_ref(), objet="Secret", expediteur="Ext",
        poste_destinataire_id=poste_normal.id,
        type=TypeCourrier.arrivee,
        confidentialite=ConfidentialiteCourrier.confidentiel,
        etat=EtatCourrier.en_attente,
        created_by_id=user.id,
    )
    courrier_normal = Courrier(
        reference=_ref(), objet="Normal", expediteur="Ext",
        poste_destinataire_id=poste_normal.id,
        type=TypeCourrier.arrivee,
        confidentialite=ConfidentialiteCourrier.normal,
        etat=EtatCourrier.en_attente,
        created_by_id=user.id,
    )
    db.add_all([courrier_conf, courrier_normal])
    await db.commit()

    resultats = await get_courriers_poste(db, poste_normal)

    refs = [c.reference for c in resultats]
    assert courrier_normal.reference in refs
    assert courrier_conf.reference not in refs


@pytest.mark.asyncio
async def test_poste_confidentiel_voit_tout(db: AsyncSession):
    user = await _create_user(db, "dir_conf@test.com", RoleFonctionnel.direction)

    poste_conf = Poste(intitule="Direction Confidentielle", occupant_user_id=user.id, niveau_acces=NiveauAcces.confidentiel)
    db.add(poste_conf)
    await db.commit()
    await db.refresh(poste_conf)

    c1 = Courrier(reference=_ref(), objet="Secret DG", expediteur="Ext", poste_destinataire_id=poste_conf.id,
                  type=TypeCourrier.arrivee, confidentialite=ConfidentialiteCourrier.confidentiel,
                  etat=EtatCourrier.en_attente, created_by_id=user.id)
    c2 = Courrier(reference=_ref(), objet="Normal DG", expediteur="Ext", poste_destinataire_id=poste_conf.id,
                  type=TypeCourrier.arrivee, confidentialite=ConfidentialiteCourrier.normal,
                  etat=EtatCourrier.en_attente, created_by_id=user.id)
    db.add_all([c1, c2])
    await db.commit()

    resultats = await get_courriers_poste(db, poste_conf)
    refs = [c.reference for c in resultats]
    assert c1.reference in refs
    assert c2.reference in refs


@pytest.mark.asyncio
async def test_detail_confidentiel_refuse_poste_normal(db: AsyncSession, client: AsyncClient):
    """Un courrier confidentiel reste inaccessible par ID direct si le poste est normal."""
    user = await _create_user(db, "agent_detail_conf@test.com", RoleFonctionnel.agent)
    poste = Poste(intitule="Poste Normal Detail", occupant_user_id=user.id, niveau_acces=NiveauAcces.normal)
    db.add(poste)
    await db.commit()
    await db.refresh(poste)

    courrier_conf = Courrier(
        reference=_ref(), objet="Secret par URL", expediteur="DG",
        poste_destinataire_id=poste.id, type=TypeCourrier.arrivee,
        confidentialite=ConfidentialiteCourrier.confidentiel,
        etat=EtatCourrier.en_attente, created_by_id=user.id,
    )
    db.add(courrier_conf)
    await db.commit()

    token = await _get_token(client, user.email)
    r = await client.get(
        f"/courriers/{courrier_conf.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_pieces_jointes_confidentiel_refuse_poste_normal(db: AsyncSession, client: AsyncClient):
    """Les pièces jointes héritent de la confidentialité du courrier."""
    user = await _create_user(db, "agent_pj_conf@test.com", RoleFonctionnel.agent)
    poste = Poste(intitule="Poste PJ Normal", occupant_user_id=user.id, niveau_acces=NiveauAcces.normal)
    db.add(poste)
    await db.commit()
    await db.refresh(poste)

    courrier_conf = Courrier(
        reference=_ref(), objet="Secret PJ", expediteur="DG",
        poste_destinataire_id=poste.id, type=TypeCourrier.arrivee,
        confidentialite=ConfidentialiteCourrier.confidentiel,
        etat=EtatCourrier.en_attente, created_by_id=user.id,
    )
    db.add(courrier_conf)
    await db.flush()
    db.add(PieceJointe(
        courrier_id=courrier_conf.id,
        nom_fichier="secret.pdf",
        chemin_stockage="uploads/test/secret.pdf",
        taille_octets=12,
        mime_type="application/pdf",
    ))
    await db.commit()

    token = await _get_token(client, user.email)
    r = await client.get(
        f"/courriers/{courrier_conf.id}/pieces-jointes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
