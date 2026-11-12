"""Rule-based AI SOC analyst coach for phishing IR training.

This is a deterministic teaching assistant — not a live attack tool.
It coaches learners through triage, enrichment, and IR decisions.
"""

from __future__ import annotations

import re
from typing import Any


def _find_alert(session: dict[str, Any], alert_id: str | None) -> dict[str, Any] | None:
    if not alert_id:
        return None
    for alert in session["alerts"]:
        if alert["id"] == alert_id:
            return alert
    return None


def _scenario_hints(scenario_id: str) -> dict[str, Any]:
    catalog = {
        "spearphish_payroll": {
            "focus": "credential harvest → account takeover chain",
            "priority": "Contain the compromised user and phishing domain before hunting mailbox rules.",
            "mitre": ["T1566.002 Spearphishing Link", "T1078 Valid Accounts"],
        },
        "business_email_compromise": {
            "focus": "BEC / payment fraud without malware",
            "priority": "Stop the pending wire first; SPF pass does not mean safe.",
            "mitre": ["T1566.002 Spearphishing Link", "T1534 Internal Spearphishing"],
        },
        "ransomware_phish": {
            "focus": "macro phish → C2 → ransomware precursor",
            "priority": "Isolate WS-WH-007 immediately — encryption is imminent.",
            "mitre": ["T1566.001 Spearphishing Attachment", "T1059.001 PowerShell", "T1490 Inhibit System Recovery"],
        },
    }
    return catalog.get(
        scenario_id,
        {
            "focus": "phishing incident response",
            "priority": "Triage critical alerts, enrich IOCs, contain, then eradicate.",
            "mitre": ["T1566 Phishing"],
        },
    )


def assist(session: dict[str, Any], question: str, context_alert_id: str | None = None) -> dict[str, Any]:
    q = question.lower().strip()
    alert = _find_alert(session, context_alert_id)
    hints = _scenario_hints(session["scenario_id"])
    incident = session.get("incident")

    suggested: list[str] = []
    mitre = list(hints["mitre"])
    confidence = "high"
    teaching_note = ""

    if any(k in q for k in ("what should i do", "next step", "priorit", "where start", "triage")):
        open_critical = [
            a for a in session["alerts"] if a["severity"] in ("critical", "high") and a["status"] == "new"
        ]
        if open_critical:
            top = sorted(open_critical, key=lambda a: 0 if a["severity"] == "critical" else 1)[0]
            answer = (
                f"Start with the highest-severity open alert: **{top['title']}** "
                f"({top['severity']}). Scenario focus: {hints['focus']}. "
                f"Priority guidance: {hints['priority']}"
            )
            suggested = [
                f"Open alert {top['id']} and review related email evidence",
                "Enrich key IOCs before broad containment",
                "Open an incident and work the playbook phases in order",
            ]
            teaching_note = (
                "In a SOC, severity + business impact drive triage order. "
                "Critical ATO or ransomware precursors outrank medium phishing detections."
            )
        else:
            answer = (
                "High-severity alerts are already in progress. Move into containment and "
                "playbook execution — confirm domains/users/hosts are blocked or reset."
            )
            suggested = [
                "Review containment log for gaps",
                "Complete remaining playbook steps",
                "Add analyst notes for handoff quality",
            ]
            teaching_note = "After triage, speed of containment reduces dwell time and blast radius."

    elif any(k in q for k in ("spf", "dkim", "dmarc", "header", "email authentic")):
        answer = (
            "Check Authentication-Results in the email headers. "
            "SPF/DKIM/DMARC failures strongly support phishing. "
            "Important exception: BEC lookalike domains can pass auth because attackers own that domain — "
            "then rely on brand impersonation, Reply-To mismatch, and payment-change language."
        )
        suggested = [
            "Compare display name / domain to the real brand",
            "Inspect Reply-To vs From",
            "Note urgency and financial language",
        ]
        mitre = ["T1566 Phishing", "T1036 Masquerading"]
        teaching_note = "Authentication results are necessary but not sufficient. BEC often authenticates cleanly."

    elif any(k in q for k in ("ioc", "enrich", "reputation", "whois", "domain", "indicator")):
        answer = (
            "Enrich domains, URLs, IPs, and hashes before and during containment. "
            "Prioritize newly registered domains, lookalikes, C2 IPs, and file hashes tied to execution."
        )
        iocs = []
        if alert:
            iocs = [i["value"] for i in alert.get("iocs", [])[:3]]
        suggested = [f"Enrich `{v}`" for v in iocs] or [
            "Enrich the sender domain",
            "Enrich any clicked URL",
            "Enrich suspicious login IPs",
        ]
        teaching_note = "Enrichment turns raw observables into decision-quality intel for blocklists and hunting."

    elif any(k in q for k in ("contain", "block", "isolate", "reset", "revoke")):
        if session["scenario_id"] == "ransomware_phish":
            answer = (
                "For ransomware precursors: isolate the host first (WS-WH-007), then block C2/domain. "
                "Do not delay isolation to finish perfect documentation."
            )
            suggested = [
                "isolate_host → WS-WH-007",
                "block_domain → fedex-shipment-updates.net",
                "Hunt for update_svc.exe elsewhere",
            ]
        elif session["scenario_id"] == "business_email_compromise":
            answer = (
                "For BEC: stop the payment path immediately, then block the lookalike domain. "
                "Malware containment actions (host isolate) are usually secondary unless malware is present."
            )
            suggested = [
                "Document payment hold with finance",
                "block_domain → northwind-suppl1es.com",
                "Out-of-band vendor callback",
            ]
        else:
            answer = (
                "For credential-harvest phishing: block the harvest domain/URL, reset the user password, "
                "and revoke SSO sessions. Then hunt mailbox forwarding rules."
            )
            suggested = [
                "block_domain on the phishing domain",
                "reset_password + revoke_session for the victim",
                "Check mailbox rules / MFA status",
            ]
        teaching_note = "Containment should match the kill-chain stage you are actually in."

    elif any(k in q for k in ("mitre", "technique", "tactic", "attack")):
        answer = (
            f"This scenario maps primarily to: {', '.join(hints['mitre'])}. "
            "Use MITRE to structure detection coverage and post-incident control recommendations."
        )
        suggested = [
            "Tag alerts with techniques during triage",
            "Map playbook steps to tactics",
            "Identify detection gaps per technique",
        ]
        teaching_note = "MITRE is a shared language for detections, IR, and purple-team follow-ups."

    elif any(k in q for k in ("false positive", "fp", "benign", "not phishing")):
        answer = (
            "Before closing as false positive, verify auth results, domain age/lookalike distance, "
            "user click/credential events, and whether finance or identity impact exists. "
            "In these labs, the seeded alerts are true positives by design — practice proving why."
        )
        suggested = [
            "List evidence that supports true positive",
            "Compare against known-good vendor/brand domains",
            "Keep FP decisions documented with evidence",
        ]
        confidence = "medium"
        teaching_note = "FP discipline matters: missed phishing becomes incident debt."

    elif any(k in q for k in ("playbook", "nist", "phase", "incident response")):
        phase = "detection"
        if incident:
            phase = incident.get("status", "detection")
        answer = (
            f"Follow NIST-aligned phases: detection → containment → eradication → recovery → lessons learned. "
            f"Your incident is currently in **{phase}**. {hints['priority']}"
        )
        suggested = [
            "Complete the current playbook step fully before skipping",
            "Log containment actions with reason codes",
            "Write lessons learned that name a control fix",
        ]
        teaching_note = "Playbooks reduce panic and create repeatable IR quality across analysts."

    elif any(k in q for k in ("score", "grade", "how am i", "feedback")):
        answer = (
            f"Current training score: {session.get('score', 0)}/{session.get('max_score', 100)}. "
            "Score rises when you enrich IOCs, contain the right targets, progress playbook steps, "
            "and close critical alerts with notes."
        )
        suggested = [
            "Ensure required containment actions are done",
            "Mark critical alerts contained/resolved with notes",
            "Finish lessons-learned playbook step",
        ]
        teaching_note = "The score is a coaching signal, not a blue-team KPI substitute."

    else:
        # Generic coaching grounded in alert context
        if alert:
            answer = (
                f"Regarding **{alert['title']}**: {alert['description']} "
                f"Category `{alert['category']}`, severity `{alert['severity']}`. "
                f"Scenario coaching: {hints['priority']}"
            )
            suggested = [
                "Review related email and timeline around this alert",
                "Enrich the alert's IOCs",
                "Decide: escalate to incident, contain, or gather more evidence",
            ]
            mitre = alert.get("mitre_techniques") or mitre
        else:
            answer = (
                f"I am your AI SOC coach for this phishing IR lab. "
                f"Scenario focus: {hints['focus']}. Ask about triage, headers, IOCs, containment, MITRE, or playbooks."
            )
            suggested = [
                "What should I do first?",
                "How do I read SPF/DKIM/DMARC?",
                "Which containment actions fit this scenario?",
            ]
            confidence = "medium"
        teaching_note = "Good analysts ask precise questions against evidence — keep pivoting on artifacts."

    # Light keyword expansion for user/host mentions
    host_match = re.search(r"\b(WS-[A-Z0-9-]+)\b", question)
    if host_match:
        suggested.insert(0, f"Consider isolate_host for {host_match.group(1)} if compromised")

    session.setdefault("ai_queries", []).append(
        {"question": question, "alert_id": context_alert_id, "answer_preview": answer[:180]}
    )

    return {
        "answer": answer,
        "suggested_next_steps": suggested[:5],
        "mitre_hints": mitre,
        "confidence": confidence,
        "teaching_note": teaching_note,
    }
