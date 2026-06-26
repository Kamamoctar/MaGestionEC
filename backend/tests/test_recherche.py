"""
Tests de la recherche avancée : full-text, filtres, et respect
de la confidentialité (couche 2 de sécurité dans la recherche).
"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.utilisateur import RoleFonctionnel
from app.models.poste import Poste, NiveauAcces
from app.models.courrier import Courrier, TypeCourrier, ConfidentialiteCourrier, EtatCourrier
from tests.conftest import _create_user, _get_token


def _ref():
    return f"TEST-{uuid.uuid4().hex[:6].upper()}"


async def _setup_recherche(db: AsyncSession):
    """Crée user + poste normal + deux courriers (normal / confidentiel)."""
    user = await _create_user(db, f"agent_rech_{uuid.uuid4().hex[:4]}@test.com", RoleFonctionnel.agent)
    poste = Poste(intitule="Poste Recherche", occupant_user_id=user.id, niveau_acces=NiveauAcces.normal)
    db.add(poste)
    await db.commit()
    await db.refresh(poste)

    c_normal = Courrier(
        reference=_ref(), objet="Rapport annuel 2026", expediteur="DAF",
        poste_destinataire_id=poste.id, type=TypeCourrier.arrivee,
        confidentialite=ConfidentialiteCourrier.normal, etat=EtatCourrier.en_attente,
        created_by_id=user.id,
    )
    c_conf = Courrier(
        reference=_ref(), objet="Note confidentielle DG", expediteur="DG",
        poste_destinataire_id=poste.id, type=TypeCourrier.arrivee,
        confidentialite=ConfidentialiteCourrier.confidentiel, etat=EtatCourrier.en_attente,
        created_by_id=user.id,
    )
    db.add_all([c_normal, c_conf])
    await db.commit()
    return user, poste, c_normal, c_conf


@pytest.mark.asyncio
async def test_recherche_trouve_par_objet(db: AsyncSession, client: AsyncClient):
    """Recherche full-text sur l'objet retourne le bon courrier."""
    user, poste, c_normal, _ = await _setup_recherche(db)
    token = await _get_token(client, user.email)

    r = await client.get("/recherche/courriers",
        params={"q": "Rapport annuel"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    refs = [c["reference"] for c in r.json()]
    assert c_normal.reference in refs


@pytest.mark.asyncio
async def test_recherche_trouve_par_expediteur(db: AsyncSession, client: AsyncClient):
    """Recherche sur le champ expéditeur."""
    user, poste, c_normal, _ = await _setup_recherche(db)
    token = await _get_token(client, user.email)

    r = await client.get("/recherche/courriers",
        params={"q": "DAF"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    refs = [c["reference"] for c in r.json()]
    assert c_normal.reference in refs


@pytest.mark.asyncio
async def test_recherche_masque_confidentiel_poste_normal(db: AsyncSession, client: AsyncClient):
    """Un poste à niveau normal ne doit pas voir les courriers confidentiels via la recherche."""
    user, poste, c_normal, c_conf = await _setup_recherche(db)
    token = await _get_token(client, user.email)

    # Recherche sans filtre — devrait retourner tous les non-confidentiels du poste
    r = await client.get("/recherche/courriers",
        params={"q": "confidentielle"},  # terme présent dans l'objet confidentiel
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    refs = [c["reference"] for c in r.json()]
    assert c_conf.reference not in refs


@pytest.mark.asyncio
async def test_recherche_poste_confidentiel_voit_tout(db: AsyncSession, client: AsyncClient):
    """Un poste à niveau confidentiel voit les courriers confidentiels dans la recherche."""
    user = await _create_user(db, f"dir_conf_rech_{uuid.uuid4().hex[:4]}@test.com", RoleFonctionnel.direction)
    poste_conf = Poste(intitule="DG Conf Recherche", occupant_user_id=user.id, niveau_acces=NiveauAcces.confidentiel)
    db.add(poste_conf)
    await db.commit()
    await db.refresh(poste_conf)

    c_conf = Courrier(
        reference=_ref(), objet="Note ultra-secrète", expediteur="Cabinet",
        poste_destinataire_id=poste_conf.id, type=TypeCourrier.arrivee,
        confidentialite=ConfidentialiteCourrier.confidentiel, etat=EtatCourrier.en_attente,
        created_by_id=user.id,
    )
    db.add(c_conf)
    await db.commit()

    token = await _get_token(client, user.email)
    r = await client.get("/recherche/courriers",
        params={"q": "ultra-secrète"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    refs = [c["reference"] for c in r.json()]
    assert c_conf.reference in refs


@pytest.mark.asyncio
async def test_recherche_filtre_par_etat(db: AsyncSession, client: AsyncClient):
    """Le filtre etat=en_attente ne retourne pas les courriers en_cours."""
    user = await _create_user(db, f"agent_etat_{uuid.uuid4().hex[:4]}@test.com", RoleFonctionnel.agent)
    poste = Poste(intitule="Poste Etat", occupant_user_id=user.id)
    db.add(poste)
    await db.commit()
    await db.refresh(poste)

    c_att = Courrier(reference=_ref(), objet="En attente XYZ123", expediteur="A",
        poste_destinataire_id=poste.id, type=TypeCourrier.arrivee,
        etat=EtatCourrier.en_attente, created_by_id=user.id)
    c_enc = Courrier(reference=_ref(), objet="En cours XYZ123", expediteur="A",
        poste_destinataire_id=poste.id, type=TypeCourrier.arrivee,
        etat=EtatCourrier.en_cours, created_by_id=user.id)
    db.add_all([c_att, c_enc])
    await db.commit()

    token = await _get_token(client, user.email)
    r = await client.get("/recherche/courriers",
        params={"q": "XYZ123", "etat": "en_attente"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    refs = [c["reference"] for c in r.json()]
    assert c_att.reference in refs
    assert c_enc.reference not in refs


@pytest.mark.asyncio
async def test_recherche_sans_poste_retourne_vide(db: AsyncSession, client: AsyncClient):
    """Un utilisateur sans poste affecté obtient une liste vide."""
    user = await _create_user(db, f"sans_poste_{uuid.uuid4().hex[:4]}@test.com", RoleFonctionnel.agent)
    token = await _get_token(client, user.email)

    r = await client.get("/recherche/courriers",
        params={"q": "rapport"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_recherche_non_authentifie_refuse(client: AsyncClient):
    """La recherche requiert une authentification."""
    r = await client.get("/recherche/courriers", params={"q": "test"})
    assert r.status_code == 401
