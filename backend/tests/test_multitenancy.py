import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.courrier import TypeCourrier
from app.models.poste import Poste, NiveauAcces
from app.models.utilisateur import RoleFonctionnel
from tests.conftest import _add_member, _create_tenant, _create_user, _get_token


def _slug(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.mark.asyncio
async def test_envoi_intertenant_cree_courrier_arrivee_dans_tenant_destinataire(
    db: AsyncSession,
    client: AsyncClient,
):
    tenant_a = await _create_tenant(db, "A Ministere", _slug("tenant-a"))
    tenant_b = await _create_tenant(db, "B Agence", _slug("tenant-b"))
    emetteur = await _create_user(db, f"sec-a-{uuid.uuid4().hex[:6]}@test.com", RoleFonctionnel.secretariat)
    destinataire = await _create_user(db, f"sec-b-{uuid.uuid4().hex[:6]}@test.com", RoleFonctionnel.secretariat)
    await _add_member(db, tenant_a, emetteur, RoleFonctionnel.secretariat)
    await _add_member(db, tenant_b, destinataire, RoleFonctionnel.secretariat)

    poste_a = Poste(
        intitule="Secretariat emetteur",
        tenant_id=tenant_a.id,
        occupant_user_id=emetteur.id,
        niveau_acces=NiveauAcces.normal,
    )
    poste_b = Poste(
        intitule="Secretariat destinataire",
        tenant_id=tenant_b.id,
        occupant_user_id=destinataire.id,
        niveau_acces=NiveauAcces.normal,
    )
    db.add_all([poste_a, poste_b])
    await db.commit()

    token_a = await _get_token(client, emetteur.email)
    response = await client.post(
        "/courriers",
        json={
            "objet": "Transmission inter-tenant",
            "expediteur": "Cabinet A",
            "type": TypeCourrier.depart.value,
            "tenant_destinataire_id": tenant_b.id,
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response.status_code == 201, response.text
    depart = response.json()
    assert depart["type"] == TypeCourrier.depart.value
    assert depart["tenant_id"] == tenant_a.id
    assert depart["tenant_destinataire_id"] == tenant_b.id
    assert depart["courrier_lie_id"] is not None

    token_b = await _get_token(client, destinataire.email)
    corbeille_b = await client.get(
        "/courriers/mes-corbeilles",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert corbeille_b.status_code == 200
    arrivees = [c for c in corbeille_b.json() if c["courrier_lie_id"] == depart["id"]]
    assert len(arrivees) == 1
    arrivee = arrivees[0]
    assert arrivee["type"] == TypeCourrier.arrivee.value
    assert arrivee["tenant_id"] == tenant_b.id
    assert arrivee["tenant_expediteur_id"] == tenant_a.id
    assert arrivee["reference_expediteur"] == depart["reference"]
    assert arrivee["expediteur"] == tenant_a.nom

    detail_arrivee_vu_par_a = await client.get(
        f"/courriers/{depart['courrier_lie_id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert detail_arrivee_vu_par_a.status_code == 403

    detail_depart_vu_par_b = await client.get(
        f"/courriers/{depart['id']}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert detail_depart_vu_par_b.status_code == 403
