"""In-memory training session store."""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any

from app.services.scenario_loader import get_scenario


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def create(self, scenario_id: str) -> dict[str, Any]:
        scenario = get_scenario(scenario_id)
        session_id = str(uuid.uuid4())
        alerts = []
        for raw in scenario["alerts"]:
            alert = copy.deepcopy(raw)
            alert["scenario_id"] = scenario_id
            alert["status"] = "new"
            alerts.append(alert)

        session = {
            "session_id": session_id,
            "scenario_id": scenario_id,
            "started_at": _utcnow(),
            "alerts": alerts,
            "emails": copy.deepcopy(scenario["emails"]),
            "timeline": copy.deepcopy(scenario["timeline"]),
            "incident": None,
            "score": 0,
            "max_score": 100,
            "completed": False,
            "learning_tips_seen": [],
            "containment_log": [],
            "enrichments_run": [],
            "ai_queries": [],
            "notes": [],
            "scoring_meta": copy.deepcopy(scenario.get("scoring", {})),
            "enrichment_db": copy.deepcopy(scenario.get("enrichment_db", {})),
            "playbook_template": copy.deepcopy(scenario.get("playbook", [])),
        }
        self._sessions[session_id] = session
        return self.public_view(session)

    def get(self, session_id: str) -> dict[str, Any]:
        if session_id not in self._sessions:
            raise KeyError("Session not found")
        return self._sessions[session_id]

    def public_view(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "session_id": session["session_id"],
            "scenario_id": session["scenario_id"],
            "started_at": session["started_at"],
            "alerts": session["alerts"],
            "emails": session["emails"],
            "timeline": session["timeline"],
            "incident": session["incident"],
            "score": session["score"],
            "max_score": session["max_score"],
            "completed": session["completed"],
            "learning_tips_seen": session["learning_tips_seen"],
            "containment_log": session.get("containment_log", []),
        }

    def list_ids(self) -> list[str]:
        return list(self._sessions.keys())


store = SessionStore()
