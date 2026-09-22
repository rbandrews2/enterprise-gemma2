"""Reuse V2 planning without creating a second editable project record."""
import hashlib

from services.v2.atlas import prepare
from services.v2.projects import canonical, evidence_review
from shared.projects import ProjectDraft


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
