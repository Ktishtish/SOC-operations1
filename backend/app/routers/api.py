"""SOCWatch HTTP API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    AIAssistRequest,
    AIAssistResponse,
    ContainmentRequest,
    CreateIncidentRequest,
    PlaybookActionRequest,
    StartSessionRequest,
    UpdateAlertRequest,
)
from app.services import ai_analyst, enrichment, incident_service
from app.services.scenario_loader import get_scenario, list_scenario_summaries
from app.services.session_store import store

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "socwatch-lab"}


@router.get("/scenarios")
def scenarios() -> list[dict]:
    return list_scenario_summaries()


@router.get("/scenarios/{scenario_id}")
def scenario_detail(scenario_id: str) -> dict:
    try:
        scenario = get_scenario(scenario_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "id": scenario["id"],
        "title": scenario["title"],
        "difficulty": scenario["difficulty"],
        "description": scenario["description"],
        "mitre_tactics": scenario["mitre_tactics"],
        "estimated_minutes": scenario["estimated_minutes"],
        "learning_objectives": scenario["learning_objectives"],
        "alert_count": len(scenario["alerts"]),
        "playbook_steps": len(scenario["playbook"]),
    }


@router.post("/sessions")
def start_session(body: StartSessionRequest) -> dict:
    try:
        return store.create(body.scenario_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    try:
        session = store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return store.public_view(session)


@router.get("/sessions/{session_id}/emails/{email_id}")
def get_email(session_id: str, email_id: str) -> dict:
    try:
        session = store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    email = next((e for e in session["emails"] if e["id"] == email_id), None)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.get("/sessions/{session_id}/alerts/{alert_id}")
def get_alert(session_id: str, alert_id: str) -> dict:
    try:
        session = store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    alert = next((a for a in session["alerts"] if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/sessions/{session_id}/alerts/{alert_id}")
def patch_alert(session_id: str, alert_id: str, body: UpdateAlertRequest) -> dict:
    try:
        session = store.get(session_id)
        alert = incident_service.update_alert(session, alert_id, body.status.value, body.note)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return alert


@router.post("/sessions/{session_id}/incidents")
def open_incident(session_id: str, body: CreateIncidentRequest) -> dict:
    try:
        session = store.get(session_id)
        return incident_service.create_incident(session, body.alert_ids, body.title)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/containment")
def contain(session_id: str, body: ContainmentRequest) -> dict:
    try:
        session = store.get(session_id)
        return incident_service.execute_containment(session, body.action, body.target, body.reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/playbook")
def playbook_action(session_id: str, body: PlaybookActionRequest) -> dict:
    try:
        session = store.get(session_id)
        return incident_service.advance_playbook(
            session,
            body.step_id,
            body.action,
            body.notes,
            body.action_payload,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/enrich")
def enrich(session_id: str, ioc: str) -> dict:
    try:
        session = store.get(session_id)
        return enrichment.enrich_ioc(session, ioc)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/ai/assist", response_model=AIAssistResponse)
def ai_assist(session_id: str, body: AIAssistRequest) -> dict:
    try:
        session = store.get(session_id)
        return ai_analyst.assist(session, body.question, body.context_alert_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/complete")
def complete(session_id: str) -> dict:
    try:
        session = store.get(session_id)
        breakdown = incident_service.finalize_score(session)
        return {"session": store.public_view(session), "scorecard": breakdown}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/knowledge/playbooks")
def knowledge_playbooks() -> dict:
    """Static learning content for SOC phishing IR."""
    return {
        "title": "Phishing & BEC Incident Response Knowledge Base",
        "nist_phases": [
            {
                "phase": "Detection & Analysis",
                "goals": [
                    "Validate phishing/BEC indicators",
                    "Scope affected users/hosts",
                    "Preserve email and log evidence",
                ],
            },
            {
                "phase": "Containment",
                "goals": [
                    "Block domains/URLs/IPs",
                    "Reset credentials / revoke sessions",
                    "Isolate endpoints when malware is present",
                    "Stop fraudulent payments for BEC",
                ],
            },
            {
                "phase": "Eradication",
                "goals": [
                    "Remove inbox rules and persistence",
                    "Clean or reimage compromised hosts",
                    "Invalidate attacker infrastructure access",
                ],
            },
            {
                "phase": "Recovery",
                "goals": [
                    "Restore users/hosts to service",
                    "Heighten monitoring",
                    "Communicate with stakeholders",
                ],
            },
            {
                "phase": "Lessons Learned",
                "goals": [
                    "Identify control failures",
                    "Tune detections",
                    "Update playbooks and awareness training",
                ],
            },
        ],
        "quick_checks": [
            "SPF / DKIM / DMARC authentication results",
            "Display-name vs SMTP domain mismatch",
            "Lookalike / newly registered domains",
            "Reply-To anomalies",
            "Credential POST or macro execution telemetry",
            "Impossible travel / anomalous SSO",
            "Mailbox forwarding rules",
            "Pending high-value payment changes",
        ],
        "ai_soc_use_cases": [
            "Alert summarization and severity rationale",
            "IOC enrichment prioritization",
            "Playbook step recommendations",
            "Natural-language investigation coaching",
            "Post-incident report drafting assistance",
        ],
    }
