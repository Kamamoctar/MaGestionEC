"""Tests du cycle de vie d'un poste : désactivation, réactivation, suppression sûre."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.courrier import Courrier, EtatCourrier, TypeCourrier
from app.models.poste import Poste
from app.models.poste_affectation import PosteAffectation, TypeAffectation
from app.models.utilisateur import RoleFonctionnel
from tests.conftest import _create_user, _get_token


@pytest.mark.asyncio
async def test_desactiver_poste_refuse_courriers_actifs(db: AsyncSession, client: AsyncClient):
    admin = await _create_user(db, "admin_desactiver_refus@test.com", RoleFonctionnel.admin)
    token = await _get_token(client, admin.email)

    poste = Poste(intitule="Poste avec encours")
    db.add(poste)
    await db.flush()
    db.add(Courrier(
        reference="POSTE-ACTIF-001",
        objet="Courrier à traiter",
        expediteur="DG",
        poste_destinataire_id=poste.id,
        type=TypeCourrier.arrivee,
        etat=EtatCourrier.en_attente,
        created_by_id=admin.id,
    ))
    await db.commit()

    r = await client.post(
        f"/postes/{poste.id}/desactiver",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 409
    assert "courriers actifs" in r.json()["detail"]


@pytest.mark.asyncio
async def test_desactiver_poste_cloture_affectations(db: AsyncSession, client: AsyncClient):
    admin = await _create_user(db, "admin_desactiver_ok@test.com", RoleFonctionnel.admin)
    occupant = await _create_user(db, "occupant_desactiver@test.com", RoleFonctionnel.agent)
    token = await _get_token(client, admin.email)

    poste = Poste(intitule="Poste à désactiver", occupant_user_id=occupant.id)
    db.add(poste)
    await db.flush()
    db.add(PosteAffectation(
        poste_id=poste.id,
        utilisateur_id=occupant.id,
        type=TypeAffectation.titulaire,
    ))
    await db.commit()

    r = await client.post(
        f"/postes/{poste.id}/desactiver",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["is_active"] is False
    assert data["occupant_user_id"] is None

    result = await db.execute(select(PosteAffectation).where(PosteAffectation.poste_id == poste.id))
    affectation = result.scalar_one()
    assert affectation.date_fin is not None


@pytest.mark.asyncio
async def test_reactiver_poste(db: AsyncSession, client: AsyncClient):
    admin = await _create_user(db, "admin_reactiver@test.com", RoleFonctionnel.admin)
    token = await _get_token(client, admin.email)

    poste = Poste(intitule="Poste à réactiver", is_active=False)
    db.add(poste)
    await db.commit()

    r = await client.post(
        f"/postes/{poste.id}/reactiver",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["is_active"] is True


@pytest.mark.asyncio
async def test_supprimer_poste_vierge(db: AsyncSession, client: AsyncClient):
    admin = await _create_user(db, "admin_delete_poste@test.com", RoleFonctionnel.admin)
    token = await _get_token(client, admin.email)

    poste = Poste(intitule="Poste erreur de saisie")
    db.add(poste)
    await db.commit()
    poste_id = poste.id

    r = await client.delete(
        f"/postes/{poste_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 204

    result = await db.execute(select(Poste).where(Poste.id == poste_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_supprimer_poste_reference_refuse(db: AsyncSession, client: AsyncClient):
    admin = await _create_user(db, "admin_delete_refus@test.com", RoleFonctionnel.admin)
    token = await _get_token(client, admin.email)

    poste = Poste(intitule="Poste historisé")
    db.add(poste)
    await db.flush()
    db.add(Courrier(
        reference="POSTE-HIST-001",
        objet="Courrier traité",
        expediteur="DG",
        poste_destinataire_id=poste.id,
        type=TypeCourrier.arrivee,
        etat=EtatCourrier.traite,
        created_by_id=admin.id,
    ))
    await db.commit()

    r = await client.delete(
        f"/postes/{poste.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 409
    assert "blocages" in r.json()["detail"]
