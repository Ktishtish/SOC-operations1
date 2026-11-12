"""Simulated threat-intel enrichment for training IOCs."""

from __future__ import annotations

from typing import Any


def enrich_ioc(session: dict[str, Any], ioc: str) -> dict[str, Any]:
    db = session.get("enrichment_db", {})
    key = ioc.strip()
    # Try exact, then case-insensitive, then partial domain-ish matches
    record = db.get(key)
    if record is None:
        for candidate, value in db.items():
            if candidate.lower() == key.lower():
                record = value
                key = candidate
                break
    if record is None:
        result = {
            "ioc": key,
            "ioc_type": "unknown",
            "reputation": "unknown — no intel hit in lab dataset",
            "related_campaigns": [],
            "whois_summary": None,
            "dns_records": None,
            "risk_score": 20,
            "analyst_guidance": (
                "No lab enrichment hit. In production, pivot across VirusTotal, WHOIS, "
                "passive DNS, and internal sightings before deciding."
            ),
        }
    else:
        result = {
            "ioc": key,
            "ioc_type": record["ioc_type"],
            "reputation": record["reputation"],
            "related_campaigns": record.get("related_campaigns", []),
            "whois_summary": record.get("whois_summary"),
            "dns_records": record.get("dns_records"),
            "risk_score": record.get("risk_score", 50),
            "analyst_guidance": record.get("analyst_guidance", ""),
        }

    if key not in session.setdefault("enrichments_run", []):
        session["enrichments_run"].append(key)
        # Reward thoughtful enrichment
        session["score"] = min(session.get("max_score", 100), session.get("score", 0) + 3)

    return result
