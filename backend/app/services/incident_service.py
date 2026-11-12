"""Incident creation, playbook progression, containment, and scoring."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


PHASE_ORDER = [
    "open",
    "investigating",
    "containment",
    "eradication",
    "recovery",
    "lessons_learned",
    "closed",
]


def create_incident(session: dict[str, Any], alert_ids: list[str], title: str | None = None) -> dict[str, Any]:
    alerts = [a for a in session["alerts"] if a["id"] in alert_ids]
    if not alerts:
        raise ValueError("No valid alerts provided")

    severity_rank = {"informational": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    top = max(alerts, key=lambda a: severity_rank.get(a["severity"], 0))

    steps = []
    for raw in session.get("playbook_template", []):
        steps.append(
            {
                **raw,
                "status": "pending",
                "completed_at": None,
                "notes": None,
            }
        )

    incident = {
        "id": f"INC-{str(uuid.uuid4())[:8].upper()}",
        "scenario_id": session["scenario_id"],
        "title": title or f"Phishing IR — {top['title']}",
        "status": "investigating",
        "severity": top["severity"],
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
        "alert_ids": [a["id"] for a in alerts],
        "playbook_steps": steps,
        "containment_actions": [],
        "analyst_notes": [],
        "score": None,
        "feedback": None,
    }

    for alert in session["alerts"]:
        if alert["id"] in alert_ids and alert["status"] == "new":
            alert["status"] = "investigating"

    session["incident"] = incident
    session["score"] = min(session.get("max_score", 100), session.get("score", 0) + 5)
    return incident


def update_alert(session: dict[str, Any], alert_id: str, status: str, note: str | None = None) -> dict[str, Any]:
    alert = next((a for a in session["alerts"] if a["id"] == alert_id), None)
    if not alert:
        raise KeyError("Alert not found")
    alert["status"] = status
    if note:
        session.setdefault("notes", []).append(
            {"alert_id": alert_id, "note": note, "at": _utcnow()}
        )
        if session.get("incident"):
            session["incident"]["analyst_notes"].append(
                {"at": _utcnow(), "text": f"[{alert_id}] {note}"}
            )
            session["incident"]["updated_at"] = _utcnow()
    if status in ("contained", "resolved") and alert["severity"] in ("high", "critical"):
        session["score"] = min(session.get("max_score", 100), session.get("score", 0) + 4)
    return alert


def execute_containment(session: dict[str, Any], action: str, target: str, reason: str) -> dict[str, Any]:
    allowed = {"block_domain", "reset_password", "isolate_host", "revoke_session", "block_url"}
    if action not in allowed:
        raise ValueError(f"Unsupported action. Allowed: {sorted(allowed)}")

    entry = {
        "id": str(uuid.uuid4())[:8],
        "action": action,
        "target": target,
        "reason": reason,
        "at": _utcnow(),
        "result": "success",
        "detail": _action_detail(action, target),
    }
    session.setdefault("containment_log", []).append(entry)
    if session.get("incident"):
        session["incident"]["containment_actions"].append(entry)
        session["incident"]["updated_at"] = _utcnow()
        if session["incident"]["status"] in ("open", "investigating"):
            session["incident"]["status"] = "containment"

    meta = session.get("scoring_meta", {})
    correct_targets = {t.lower() for t in meta.get("correct_containment_targets", [])}
    required_actions = set(meta.get("required_actions", []))
    gain = 2
    if target.lower() in correct_targets:
        gain += 6
    if action in required_actions:
        gain += 4
    session["score"] = min(session.get("max_score", 100), session.get("score", 0) + gain)
    return entry


def _action_detail(action: str, target: str) -> str:
    messages = {
        "block_domain": f"Domain {target} added to DNS/proxy blocklist (simulated).",
        "block_url": f"URL {target} blocked at secure web gateway (simulated).",
        "reset_password": f"Password reset forced for {target}; user must enroll MFA on next login (simulated).",
        "revoke_session": f"All SSO/OAuth sessions revoked for {target} (simulated).",
        "isolate_host": f"Host {target} network-isolated via EDR (simulated).",
    }
    return messages.get(action, f"Executed {action} on {target}")


def advance_playbook(
    session: dict[str, Any],
    step_id: str,
    action: str,
    notes: str | None = None,
    action_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    incident = session.get("incident")
    if not incident:
        raise ValueError("Create an incident before using the playbook")

    step = next((s for s in incident["playbook_steps"] if s["id"] == step_id), None)
    if not step:
        raise KeyError("Playbook step not found")

    if action == "skip":
        step["status"] = "skipped"
        step["notes"] = notes
        step["completed_at"] = _utcnow()
    elif action in ("complete", "execute"):
        # Optional: auto-run linked containment
        if action == "execute" and step.get("action_type") == "containment":
            payload = action_payload or step.get("action_payload") or {}
            if payload.get("action") and payload.get("target"):
                execute_containment(
                    session,
                    payload["action"],
                    payload["target"],
                    notes or f"Playbook step {step_id}",
                )
        step["status"] = "completed"
        step["notes"] = notes
        step["completed_at"] = _utcnow()
        session["score"] = min(session.get("max_score", 100), session.get("score", 0) + 5)
        _sync_incident_phase(incident, step.get("phase", ""))
    else:
        raise ValueError("action must be complete, skip, or execute")

    incident["updated_at"] = _utcnow()
    return step


def _sync_incident_phase(incident: dict[str, Any], phase: str) -> None:
    mapping = {
        "detection": "investigating",
        "containment": "containment",
        "eradication": "eradication",
        "recovery": "recovery",
        "lessons_learned": "lessons_learned",
    }
    if phase in mapping:
        incident["status"] = mapping[phase]


def finalize_score(session: dict[str, Any]) -> dict[str, Any]:
    meta = session.get("scoring_meta", {})
    required_actions = set(meta.get("required_actions", []))
    correct_targets = {t.lower() for t in meta.get("correct_containment_targets", [])}
    critical_alerts = set(meta.get("critical_alerts", []))

    done_actions = {e["action"] for e in session.get("containment_log", [])}
    done_targets = {e["target"].lower() for e in session.get("containment_log", [])}

    categories = {
        "enrichment": min(20, len(session.get("enrichments_run", [])) * 3),
        "containment_actions": 0,
        "containment_targets": 0,
        "alert_handling": 0,
        "playbook": 0,
        "documentation": 0,
    }

    if required_actions:
        categories["containment_actions"] = int(20 * len(required_actions & done_actions) / len(required_actions))
    if correct_targets:
        categories["containment_targets"] = int(20 * len(correct_targets & done_targets) / len(correct_targets))

    handled = [
        a
        for a in session["alerts"]
        if a["id"] in critical_alerts and a["status"] in ("contained", "resolved", "investigating", "triaging")
    ]
    if critical_alerts:
        categories["alert_handling"] = int(15 * len(handled) / len(critical_alerts))

    incident = session.get("incident")
    if incident:
        steps = incident.get("playbook_steps", [])
        completed = [s for s in steps if s["status"] == "completed"]
        if steps:
            categories["playbook"] = int(15 * len(completed) / len(steps))
        categories["documentation"] = min(10, len(incident.get("analyst_notes", [])) * 2)
    else:
        categories["playbook"] = 0
        categories["documentation"] = 0

    total = sum(categories.values())
    # Blend with live score but cap by computed rubric
    blended = min(100, max(total, int(session.get("score", 0) * 0.85)))
    session["score"] = blended

    strengths = []
    improvements = []
    if categories["containment_actions"] >= 15:
        strengths.append("Executed the required containment action types for this scenario.")
    else:
        improvements.append("Revisit required containment actions (block/reset/isolate as applicable).")
    if categories["containment_targets"] >= 15:
        strengths.append("Contained the correct high-value targets.")
    else:
        improvements.append("Double-check IOC targets — domain, user, host, or URL may still be open.")
    if categories["enrichment"] >= 12:
        strengths.append("Used threat enrichment to support decisions.")
    else:
        improvements.append("Enrich IOCs before or during containment to justify actions.")
    if categories["playbook"] >= 10:
        strengths.append("Worked the IR playbook systematically.")
    else:
        improvements.append("Create an incident early and complete playbook phases.")
    if categories["documentation"] >= 6:
        strengths.append("Left useful analyst notes for handoff.")
    else:
        improvements.append("Add concise notes when changing alert/incident state.")

    grade = (
        "A"
        if blended >= 90
        else "B"
        if blended >= 80
        else "C"
        if blended >= 70
        else "D"
        if blended >= 60
        else "F"
    )

    if incident:
        incident["score"] = blended
        incident["feedback"] = strengths + improvements
        incident["status"] = "closed"
        incident["updated_at"] = _utcnow()
    session["completed"] = True

    return {
        "total": blended,
        "max_total": 100,
        "categories": categories,
        "strengths": strengths,
        "improvements": improvements,
        "grade": grade,
    }
