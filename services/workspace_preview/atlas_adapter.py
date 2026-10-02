"""Reuse V2 planning without creating a second editable project record."""
import hashlib
import re

from services.v2.atlas import prepare
from services.v2.projects import canonical, evidence_review
from shared.projects import ProjectDraft


def select_references(topics, question, work_type):
    """Two task references plus one safety/context reference, at most three.

    Selection is keyword discovery, never a determination of applicability.
    Preserve complete citation and contract-scope metadata from preparation.
    """
    hints = {
        "marking_materials": r"material|glass bead|thermoplastic|paint",
        "marking_removal": r"remov|surface prep",
        "marking_visibility": r"retroreflect|visibility",
        "flaggers": r"flagger|flagging",
        "advance_warning": r"advance.*warning|warning sign",
        "striping": r"striping|pavement marking|line marking",
        "excavation": r"excavat|trench",
        "utility": r"utility|utilities",
    }
    explicit = [key for key, pattern in hints.items() if re.search(pattern, question, re.I)]
    defaults = {"line_striping": "striping", "underground_utility": "utility"}
    preferred = explicit or ([defaults[work_type]] if work_type in defaults else [])
    by_id = {topic["id"]: topic["candidates"] for topic in topics}
    selected, seen = [], set()

    def add(ref):
        key = (ref["source_id"], ref["revision"], ref.get("page"), ref.get("section"), ref["text"])
        if key not in seen and len(selected) < 3:
            seen.add(key)
            selected.append(ref)

    # Round-robin explicit topics before their second candidates.
    groups = [by_id.get(key, []) for key in preferred]
    for offset in range(max((len(group) for group in groups), default=0)):
        for group in groups:
            if offset < len(group) and len(selected) < 2:
                add(group[offset])
    if selected:
        for key in ("worker_safety", "traffic_control"):
            before = len(selected)
            for ref in by_id.get(key, []):
                add(ref)
                if len(selected) > before:
                    break
            if len(selected) > before:
                break
    for topic in topics:
        for ref in topic["candidates"]:
            before = len(selected)
            add(ref)
            if len(selected) > before:
                break
    return selected


def prepare_order(order, knowledge):
    draft = ProjectDraft(name=order["title"], intake={
        "work_type": order["work_type"], "work_description": order["notes"] or order["title"],
        "location": {"address": order["address"], "locality": order["locality"],
                     "road_authority": order.get("road_authority")},
        "project_date": order["work_date"], "site": order.get("site", {}),
        "requested_outputs": ["work_zone_setup", "required_forms", "annotated_image"],
    }, job_geometry=order.get("job_geometry"))
    record = {"project_id": order["id"], "version": order["version"],
              "sha256": hashlib.sha256(canonical(draft).encode()).hexdigest(),
              "draft": draft.model_dump(mode="json"), "evidence_review": evidence_review(draft)}
    packet = prepare(record, knowledge)
    packet.update(order_id=order["id"], version=order["version"],
                  attention_items=packet["references"]["assessment"]["attention_items"],
                  note="Reference candidates from the local library. Applicability remains unverified; no model call or field approval.")
    return packet
