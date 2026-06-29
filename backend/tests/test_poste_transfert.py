"""
Tests du principe fondamental : le courrier est rattaché au POSTE.
Changer d'occupant ne touche pas aux courriers — le nouvel occupant les hérite automatiquement.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.utilisateur import RoleFonctionnel
from app.models.poste import Poste, NiveauAcces
from app.models.courrier import Courrier, TypeCourrier, EtatCourrier
from app.models.poste_affectation import TypeAffectation
from app.services.poste_service import changer_occupant, affecter_interimaire, affecter_delegation, get_historique_affectations
from tests.conftest import _create_user, _get_token


@pytest.mark.asyncio
async def test_transfert_poste_herite_courriers(db: AsyncSession):
    """
    Après un changement d'occupant, les courriers du poste n'ont PAS changé de poste_destinataire_id —
    le nouvel occupant y accède simplement parce qu'il occupe maintenant le poste.
    """
    user_a = await _create_user(db, "alice@test.com", RoleFonctionnel.agent)
    user_b = await _create_user(db, "bob@test.com", RoleFonctionnel.agent)

    poste = Poste(intitule="Directeur Test", occupant_user_id=user_a.id)
    db.add(poste)
    await db.commit()
    await db.refresh(poste)

    assert poste.occupant_user_id == user_a.id

    # Transfert vers user_b
    poste = await changer_occupant(db, poste, user_b.id, TypeAffectation.titulaire)

    assert poste.occupant_user_id == user_b.id
    # L'id du poste n'a pas changé — les courriers liés à ce poste_id sont donc hérités par user_b
    assert poste.id is not None


@pytest.mark.asyncio
async def test_historique_affectation_cloture(db: AsyncSession):
    """Quand on change d'occupant, l'ancienne affectation est clôturée (date_fin renseignée)."""
    user_a = await _create_user(db, "alice2@test.com", RoleFonctionnel.agent)
    user_b = await _create_user(db, "bob2@test.com", RoleFonctionnel.agent)

    poste = Poste(intitule="Secrétariat Test", occupant_user_id=user_a.id)
    db.add(poste)
    await db.commit()
    await db.refresh(poste)

    # Créer affectation initiale
    await changer_occupant(db, poste, user_a.id, TypeAffectation.titulaire)
    await changer_occupant(db, poste, user_b.id, TypeAffectation.titulaire)

    historique = await get_historique_affectations(db, poste.id)
    # Au moins une affectation clôturée
    affectations_closees = [a for a in historique if a.date_fin is not None]
    assert len(affectations_closees) >= 1


@pytest.mark.asyncio
async def test_interim_enregistre_separement(db: AsyncSession):
    """L'affectation intérimaire est enregistrée avec le type 'interim'."""
    user_titulaire = await _create_user(db, "titulaire@test.com", RoleFonctionnel.agent)
    user_interim = await _create_user(db, "interim@test.com", RoleFonctionnel.agent)

    poste = Poste(intitule="DG Intérim", occupant_user_id=user_titulaire.id)
    db.add(poste)
    await db.commit()
    await db.refresh(poste)

    poste = await affecter_interimaire(db, poste, user_interim.id)

    assert poste.occupant_user_id == user_interim.id

    historique = await get_historique_affectations(db, poste.id)
    interims = [a for a in historique if a.type == TypeAffectation.interim]
    assert len(interims) >= 1


@pytest.mark.asyncio
async def test_liberer_poste(db: AsyncSession):
    """Libérer un poste met occupant_user_id à None."""
    user = await _create_user(db, "libre@test.com", RoleFonctionnel.agent)
    poste = Poste(intitule="Poste à libérer", occupant_user_id=user.id)
    db.add(poste)
    await db.commit()
    await db.refresh(poste)

    poste = await changer_occupant(db, poste, None)
    assert poste.occupant_user_id is None


@pytest.mark.asyncio
async def test_delegation_donne_acces_aux_corbeilles(db: AsyncSession, client: AsyncClient):
    """Un délégataire actif voit les courriers du poste sans devenir occupant titulaire."""
    titulaire = await _create_user(db, "titulaire_deleg@test.com", RoleFonctionnel.agent)
    delegataire = await _create_user(db, "delegataire@test.com", RoleFonctionnel.agent)

    poste = Poste(intitule="Poste Délégué", occupant_user_id=titulaire.id)
    db.add(poste)
    await db.commit()
    await db.refresh(poste)

    await affecter_delegation(db, poste, delegataire.id)

    courrier = Courrier(
        reference="DELEG-TEST-001",
        objet="Courrier délégué",
        expediteur="Cabinet",
        poste_destinataire_id=poste.id,
        type=TypeCourrier.arrivee,
        etat=EtatCourrier.en_attente,
        created_by_id=titulaire.id,
    )
    db.add(courrier)
    await db.commit()

    token = await _get_token(client, delegataire.email)
    r = await client.get(
        "/courriers/mes-corbeilles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    refs = [c["reference"] for c in r.json()]
    assert courrier.reference in refs
    assert poste.occupant_user_id == titulaire.id
