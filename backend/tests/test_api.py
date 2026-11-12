"""API tests for Aegis SOC Lab."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_scenarios_listed():
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    ids = {s["id"] for s in res.json()}
    assert "spearphish_payroll" in ids
    assert "business_email_compromise" in ids
    assert "ransomware_phish" in ids


def test_full_payroll_flow():
    start = client.post("/api/sessions", json={"scenario_id": "spearphish_payroll"})
    assert start.status_code == 200
    session = start.json()
    sid = session["session_id"]
    assert len(session["alerts"]) >= 3

    alert_id = session["alerts"][0]["id"]
    patched = client.patch(
        f"/api/sessions/{sid}/alerts/{alert_id}",
        json={"status": "investigating", "note": "Validating headers"},
    )
    assert patched.status_code == 200

    enrich = client.get(f"/api/sessions/{sid}/enrich", params={"ioc": "acme-hr-portal.com"})
    assert enrich.status_code == 200
    assert enrich.json()["risk_score"] >= 80

    assist = client.post(
        f"/api/sessions/{sid}/ai/assist",
        json={"question": "What should I do first?", "context_alert_id": alert_id},
    )
    assert assist.status_code == 200
    body = assist.json()
    assert body["answer"]
    assert body["suggested_next_steps"]

    incident = client.post(
        f"/api/sessions/{sid}/incidents",
        json={"alert_ids": [a["id"] for a in session["alerts"]]},
    )
    assert incident.status_code == 200
    assert incident.json()["playbook_steps"]

    contain = client.post(
        f"/api/sessions/{sid}/containment",
        json={
            "action": "block_domain",
            "target": "acme-hr-portal.com",
            "reason": "Phishing domain",
        },
    )
    assert contain.status_code == 200

    contain2 = client.post(
        f"/api/sessions/{sid}/containment",
        json={
            "action": "reset_password",
            "target": "jordan.lee@acme.corp",
            "reason": "Credential harvest",
        },
    )
    assert contain2.status_code == 200

    client.post(
        f"/api/sessions/{sid}/containment",
        json={
            "action": "revoke_session",
            "target": "jordan.lee@acme.corp",
            "reason": "ATO containment",
        },
    )

    steps = incident.json()["playbook_steps"]
    for step in steps:
        action = "execute" if step.get("action_type") == "containment" else "complete"
        res = client.post(
            f"/api/sessions/{sid}/playbook",
            json={"step_id": step["id"], "action": action, "notes": "done"},
        )
        assert res.status_code == 200

    done = client.post(f"/api/sessions/{sid}/complete")
    assert done.status_code == 200
    scorecard = done.json()["scorecard"]
    assert scorecard["total"] >= 60
    assert scorecard["grade"] in list("ABCDF")


def test_knowledge_base():
    res = client.get("/api/knowledge/playbooks")
    assert res.status_code == 200
    assert len(res.json()["nist_phases"]) >= 5
