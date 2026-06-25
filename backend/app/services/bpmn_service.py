"""
Parser BPMN — extrait les lanes, tâches et leur ordre topologique
à partir d'un fichier .bpmn/.xml (spec BPMN 2.0, lxml).

Étapes :
1. analyser_bpmn()  → détecte lanes + ordre des tâches (lecture seule)
2. generer_flux()   → crée Flux + FluxEtape en base à partir du mapping validé
"""
from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field

from lxml import etree

# Namespaces BPMN connus (OMG standard + variantes outils)
_KNOWN_BPMN_NS = [
    "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "http://www.omg.org/spec/BPMN/20100524/MODEL/",
    "http://www.omg.org/spec/bpmn/20100524/MODEL",
    "http://www.omg.org/spec/bpmn/20100524/model",
    "http://b3mn.org/stencilset/bpmn2.0#",
]
BPMN_NS = _KNOWN_BPMN_NS[0]
B = f"{{{BPMN_NS}}}"

# Éléments considérés comme des tâches exécutables
TASK_TAGS = {
    f"{B}task", f"{B}userTask", f"{B}manualTask",
    f"{B}serviceTask", f"{B}sendTask", f"{B}receiveTask",
    f"{B}scriptTask", f"{B}businessRuleTask",
}

# Mots-clés → type d'action (ordre important : plus spécifique en premier)
_ACTION_KEYWORDS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"sign(ature|er|é)", re.I), "signature"),
    (re.compile(r"visa|viser|approuv", re.I), "visa"),
    (re.compile(r"inform(ation|er)|notif|pour info", re.I), "information"),
    (re.compile(r"distrib|enregistr|transmett|router|dispatch", re.I), "distribution"),
]


def _detect_bpmn_namespace(root: etree._Element) -> str:
    """
    Cherche le namespace BPMN dans tous les namespaces déclarés.
    Retourne une chaîne vide si le fichier n'utilise pas de namespace (rare mais possible).
    """
    all_ns: dict[str, str] = {}
    # Collecter tous les nsmap de l'arbre (pas seulement la racine)
    for el in root.iter():
        all_ns.update(el.nsmap)

    # 1. Chercher un namespace connu exact
    for known in _KNOWN_BPMN_NS:
        if known in all_ns.values():
            return known

    # 2. Chercher par heuristique (contient "bpmn" et "model" ou "omg")
    for v in all_ns.values():
        if v and "bpmn" in v.lower() and ("model" in v.lower() or "omg" in v.lower()):
            return v

    # 3. Chercher par présence d'un élément <process> ou <definitions>
    for el in root.iter():
        local = etree.QName(el.tag).localname if "{" in el.tag else el.tag
        ns = etree.QName(el.tag).namespace if "{" in el.tag else None
        if local in ("process", "definitions", "lane") and ns:
            return ns

    return ""  # fichier sans namespace explicite


def _iter_local(root: etree._Element, local_name: str):
    """Itère tous les éléments dont le nom local correspond, quel que soit le namespace."""
    for el in root.iter():
        tag = el.tag
        lname = etree.QName(tag).localname if "{" in tag else tag
        if lname == local_name:
            yield el


def _detect_action(task_name: str) -> str:
    for pattern, action in _ACTION_KEYWORDS:
        if pattern.search(task_name):
            return action
    return "distribution"


@dataclass
class LaneDetecte:
    lane_id: str
    lane_name: str
    node_refs: list[str]        # IDs des nœuds appartenant à cette lane
    taches: list[str]           # Noms des tâches (filtrés, sans start/end/gateway)
    type_action_propose: str    # Déduit du nom de la première tâche


@dataclass
class BpmnAnalyse:
    nom_processus: str
    lanes: list[LaneDetecte]
    ordre_lanes: list[str]      # lane_ids dans l'ordre topologique d'exécution
    bpmn_source: str            # XML brut (pour stockage en base)
    avertissements: list[str] = field(default_factory=list)


def analyser_bpmn(xml_content: str | bytes) -> BpmnAnalyse:
    """
    Parse le BPMN et retourne une analyse sans toucher à la base.
    Lève ValueError si le XML est invalide ou ne contient aucune lane.
    """
    if isinstance(xml_content, str):
        xml_content = xml_content.encode("utf-8")

    try:
        root = etree.fromstring(xml_content)
    except etree.XMLSyntaxError as exc:
        raise ValueError(f"XML invalide : {exc}") from exc

    # Détecter le namespace BPMN utilisé par ce fichier (compatible tous outils)
    bpmn_ns = _detect_bpmn_namespace(root)
    b = f"{{{bpmn_ns}}}" if bpmn_ns else ""

    task_tags_local = {
        f"{b}task", f"{b}userTask", f"{b}manualTask",
        f"{b}serviceTask", f"{b}sendTask", f"{b}receiveTask",
        f"{b}scriptTask", f"{b}businessRuleTask",
        # sans namespace (certains fichiers draw.io n'en ont pas)
        "task", "userTask", "manualTask", "serviceTask",
        "sendTask", "receiveTask", "scriptTask", "businessRuleTask",
    }

    # ── 1. Nom du processus ──────────────────────────────────────────────
    process_el = next(_iter_local(root, "process"), None)
    nom_processus = (process_el.get("name") or "Circuit") if process_el is not None else "Circuit"

    # ── 2. Catalogue id→élément pour tous les nœuds ─────────────────────
    id_to_el: dict[str, etree._Element] = {}
    for el in root.iter():
        eid = el.get("id")
        if eid:
            id_to_el[eid] = el

    # ── 3. Lanes ─────────────────────────────────────────────────────────
    lane_els = list(_iter_local(root, "lane"))
    if not lane_els:
        raise ValueError(
            "Aucune lane (swimlane) trouvée dans ce fichier BPMN. "
            "Assurez-vous que votre processus utilise des Swimlanes/Pools. "
            "Les outils supportés : bpmn.io, Camunda Modeler, Signavio."
        )

    lanes: list[LaneDetecte] = []
    for lane_el in lane_els:
        lane_id = lane_el.get("id", "")
        lane_name = lane_el.get("name", "Sans nom")
        node_refs = [
            ref.text.strip()
            for ref in _iter_local(lane_el, "flowNodeRef")
            if ref.text
        ]

        # Garder uniquement les tâches réelles
        task_names = []
        for ref_id in node_refs:
            el = id_to_el.get(ref_id)
            if el is not None and el.tag in task_tags_local:
                name = el.get("name") or ref_id
                task_names.append(name)

        action = _detect_action(" ".join(task_names)) if task_names else "distribution"
        lanes.append(LaneDetecte(
            lane_id=lane_id,
            lane_name=lane_name,
            node_refs=node_refs,
            taches=task_names,
            type_action_propose=action,
        ))

    # ── 4. Ordre topologique via sequenceFlow ────────────────────────────
    adj: dict[str, list[str]] = {eid: [] for eid in id_to_el}
    for sf in _iter_local(root, "sequenceFlow"):
        src, tgt = sf.get("sourceRef"), sf.get("targetRef")
        if src and tgt:
            adj.setdefault(src, []).append(tgt)

    # BFS depuis le startEvent
    start_ids = [el.get("id") for el in _iter_local(root, "startEvent") if el.get("id")]
    visited_tasks: list[str] = []  # IDs de tâches dans l'ordre de visite
    visited: set[str] = set()
    queue: deque[str] = deque(start_ids)
    while queue:
        node_id = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)
        el = id_to_el.get(node_id)
        if el is not None and el.tag in task_tags_local:
            visited_tasks.append(node_id)
        for nxt in adj.get(node_id, []):
            if nxt not in visited:
                queue.append(nxt)

    # Associer chaque tâche visitée à sa lane
    node_to_lane: dict[str, str] = {}
    for lane in lanes:
        for ref in lane.node_refs:
            node_to_lane[ref] = lane.lane_id

    ordre_lanes: list[str] = []
    seen_lanes: set[str] = set()
    for task_id in visited_tasks:
        lane_id = node_to_lane.get(task_id)
        if lane_id and lane_id not in seen_lanes:
            seen_lanes.add(lane_id)
            ordre_lanes.append(lane_id)

    # Lanes sans tâches → avertissement
    avertissements: list[str] = []
    for lane in lanes:
        if not lane.taches:
            avertissements.append(f"Lane « {lane.lane_name} » : aucune tâche détectée.")
    if not ordre_lanes:
        # Fallback : ordre de déclaration dans le fichier
        ordre_lanes = [l.lane_id for l in lanes if l.taches]
        avertissements.append("Ordre topologique indéterminé — ordre de déclaration utilisé.")

    return BpmnAnalyse(
        nom_processus=nom_processus,
        lanes=lanes,
        ordre_lanes=ordre_lanes,
        bpmn_source=xml_content.decode("utf-8"),
        avertissements=avertissements,
    )
