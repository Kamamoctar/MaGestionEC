"""
Tests du parser BPMN et de la génération de flux.
"""
import os
import pytest
from httpx import AsyncClient

from app.models.utilisateur import RoleFonctionnel
from app.models.poste import Poste
from app.services.bpmn_service import analyser_bpmn
from tests.conftest import _create_user, _get_token

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _bpmn(filename: str) -> bytes:
    with open(os.path.join(FIXTURE_DIR, filename), "rb") as f:
        return f.read()


# ── Tests unitaires du parser ────────────────────────────────────────────────

def test_analyser_detecte_trois_lanes():
    analyse = analyser_bpmn(_bpmn("circuit_standard.bpmn"))
    assert len(analyse.lanes) == 3


def test_analyser_nom_processus():
    analyse = analyser_bpmn(_bpmn("circuit_standard.bpmn"))
    assert "Circuit" in analyse.nom_processus


def test_analyser_ordre_topologique():
    analyse = analyser_bpmn(_bpmn("circuit_standard.bpmn"))
    # Le secrétariat est premier (startEvent dans sa lane)
    premier = next(l for l in analyse.lanes if l.lane_id == analyse.ordre_lanes[0])
    assert "Secr" in premier.lane_name


def test_analyser_detection_type_action():
    analyse = analyser_bpmn(_bpmn("circuit_standard.bpmn"))
    # Lane avec tâche "Visa" → type visa
    visa_lane = next(l for l in analyse.lanes if any("Visa" in t for t in l.taches))
    assert visa_lane.type_action_propose == "visa"
    # Lane avec tâche "Signature" → type signature
    sig_lane = next(l for l in analyse.lanes if any("Signature" in t for t in l.taches))
    assert sig_lane.type_action_propose == "signature"


def test_analyser_bpmn_invalide():
    with pytest.raises(ValueError, match="XML invalide"):
        analyser_bpmn(b"pas du xml valide <<<")


def test_analyser_bpmn_sans_lane():
    bpmn_sans_lane = """<?xml version="1.0" encoding="UTF-8"?>
    <definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">
      <process id="p1" name="Sans Lane">
        <startEvent id="s1"/>
        <userTask id="t1" name="Tache simple"/>
        <endEvent id="e1"/>
        <sequenceFlow id="f1" sourceRef="s1" targetRef="t1"/>
        <sequenceFlow id="f2" sourceRef="t1" targetRef="e1"/>
      </process>
    </definitions>"""
    with pytest.raises(ValueError, match="lane"):
        analyser_bpmn(bpmn_sans_lane)


# ── Tests d'intégration (endpoints) ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_bpmn_analyse(db, client: AsyncClient):
    await _create_user(db, "admin_bpmn@test.com", RoleFonctionnel.admin)
    token = await _get_token(client, "admin_bpmn@test.com")

    bpmn_bytes = _bpmn("circuit_standard.bpmn")
    r = await client.post(
        "/bpmn/analyser",
        files={"file": ("circuit_standard.bpmn", bpmn_bytes, "application/xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["lanes"]) == 3
    assert len(data["ordre_lanes"]) > 0


@pytest.mark.asyncio
async def test_generer_flux_depuis_bpmn(db, client: AsyncClient):
    await _create_user(db, "admin_gen@test.com", RoleFonctionnel.admin)
    token = await _get_token(client, "admin_gen@test.com")

    # Créer 3 postes pour le mapping
    postes = []
    for nom in ["Secrétariat Test", "DAG Test", "DG Test"]:
        r = await client.post(
            "/postes", json={"intitule": nom},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201
        postes.append(r.json()["id"])

    # Analyser le BPMN
    bpmn_bytes = _bpmn("circuit_standard.bpmn")
    r_analyse = await client.post(
        "/bpmn/analyser",
        files={"file": ("circuit_standard.bpmn", bpmn_bytes, "application/xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_analyse.status_code == 200
    analyse = r_analyse.json()

    # Construire le mapping lane → poste
    mapping = [
        {"lane_id": analyse["ordre_lanes"][i], "poste_id": postes[i], "type_action": lane["type_action_propose"]}
        for i, lane in enumerate(
            sorted(analyse["lanes"], key=lambda l: analyse["ordre_lanes"].index(l["lane_id"]))
        )
    ]

    r_flux = await client.post(
        "/bpmn/generer",
        json={
            "nom": "Circuit Standard Test",
            "bpmn_source": analyse["bpmn_source"],
            "mapping": mapping,
            "ordre_lanes": analyse["ordre_lanes"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_flux.status_code == 201, r_flux.text
    flux = r_flux.json()
    assert flux["nom"] == "Circuit Standard Test"
    assert len(flux["etapes"]) == 3
    # Dernière étape est terminale
    assert flux["etapes"][-1]["is_terminal"] is True


@pytest.mark.asyncio
async def test_non_admin_ne_peut_pas_uploader(db, client: AsyncClient):
    await _create_user(db, "agent_bpmn@test.com", RoleFonctionnel.agent)
    token = await _get_token(client, "agent_bpmn@test.com")
    bpmn_bytes = _bpmn("circuit_standard.bpmn")
    r = await client.post(
        "/bpmn/analyser",
        files={"file": ("test.bpmn", bpmn_bytes, "application/xml")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
