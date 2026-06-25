"""
Tests de la couche 1 de sécurité : rôles fonctionnels protégeant les routes admin.
Un non-admin ne peut pas accéder aux routes d'administration.
"""
import pytest
from httpx import AsyncClient

from app.models.utilisateur import RoleFonctionnel
from tests.conftest import _create_user, _get_token


@pytest.mark.asyncio
async def test_agent_ne_peut_pas_creer_utilisateur(db, client: AsyncClient):
    await _create_user(db, "agent_role@test.com", RoleFonctionnel.agent)
    token = await _get_token(client, "agent_role@test.com")

    r = await client.post(
        "/utilisateurs",
        json={"nom": "X", "prenom": "Y", "email": "new@test.com", "password": "p"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_secretariat_ne_peut_pas_creer_poste(db, client: AsyncClient):
    await _create_user(db, "sec_role@test.com", RoleFonctionnel.secretariat)
    token = await _get_token(client, "sec_role@test.com")

    r = await client.post(
        "/postes",
        json={"intitule": "Poste Interdit"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_peut_creer_poste(db, client: AsyncClient):
    await _create_user(db, "admin_role@test.com", RoleFonctionnel.admin)
    token = await _get_token(client, "admin_role@test.com")

    r = await client.post(
        "/postes",
        json={"intitule": "Poste Admin OK"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_non_authentifie_refuse(client: AsyncClient):
    r = await client.get("/postes")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_mauvais_mdp(db, client: AsyncClient):
    await _create_user(db, "bad_pwd@test.com", RoleFonctionnel.agent)
    r = await client.post("/auth/token", data={"username": "bad_pwd@test.com", "password": "mauvais"})
    assert r.status_code == 401
