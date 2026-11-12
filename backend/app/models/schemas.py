"""Pydantic models for the SOCWatch API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    informational = "informational"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertStatus(str, Enum):
    new = "new"
    triaging = "triaging"
    investigating = "investigating"
    contained = "contained"
    resolved = "resolved"
    false_positive = "false_positive"


class IncidentStatus(str, Enum):
    open = "open"
    investigating = "investigating"
    containment = "containment"
    eradication = "eradication"
    recovery = "recovery"
    lessons_learned = "lessons_learned"
    closed = "closed"


class PlaybookStepStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class IOCType(str, Enum):
    domain = "domain"
    url = "url"
    ip = "ip"
    email = "email"
    hash = "hash"
    filename = "filename"
    user = "user"
    host = "host"


class ScenarioSummary(BaseModel):
    id: str
    title: str
    difficulty: str
    description: str
    mitre_tactics: list[str]
    estimated_minutes: int
    learning_objectives: list[str]


class EmailMessage(BaseModel):
    id: str
    from_address: str
    from_display: str
    to_address: str
    subject: str
    received_at: str
    body_text: str
    body_html_preview: str
    headers: dict[str, str]
    urls: list[str]
    attachments: list[dict[str, str]]
    spoof_indicators: list[str]


class IOC(BaseModel):
    type: IOCType
    value: str
    context: str
    malicious: bool = False
    reputation: Optional[str] = None


class TimelineEvent(BaseModel):
    id: str
    timestamp: str
    source: str
    actor: str
    action: str
    detail: str
    severity: Severity = Severity.informational


class Alert(BaseModel):
    id: str
    scenario_id: str
    title: str
    description: str
    severity: Severity
    status: AlertStatus = AlertStatus.new
    created_at: str
    source: str
    category: str
    mitre_techniques: list[str] = Field(default_factory=list)
    related_email_id: Optional[str] = None
    related_user: Optional[str] = None
    related_host: Optional[str] = None
    iocs: list[IOC] = Field(default_factory=list)
    raw_evidence: dict[str, Any] = Field(default_factory=dict)


class PlaybookStep(BaseModel):
    id: str
    phase: str
    title: str
    description: str
    guidance: str
    status: PlaybookStepStatus = PlaybookStepStatus.pending
    action_type: Optional[str] = None
    action_payload: Optional[dict[str, Any]] = None
    completed_at: Optional[str] = None
    notes: Optional[str] = None


class Incident(BaseModel):
    id: str
    scenario_id: str
    title: str
    status: IncidentStatus = IncidentStatus.open
    severity: Severity
    created_at: str
    updated_at: str
    alert_ids: list[str] = Field(default_factory=list)
    playbook_steps: list[PlaybookStep] = Field(default_factory=list)
    containment_actions: list[dict[str, Any]] = Field(default_factory=list)
    analyst_notes: list[dict[str, str]] = Field(default_factory=list)
    score: Optional[int] = None
    feedback: Optional[list[str]] = None


class SessionState(BaseModel):
    session_id: str
    scenario_id: str
    started_at: str
    alerts: list[Alert]
    emails: list[EmailMessage]
    timeline: list[TimelineEvent]
    incident: Optional[Incident] = None
    score: int = 0
    max_score: int = 100
    completed: bool = False
    learning_tips_seen: list[str] = Field(default_factory=list)


class StartSessionRequest(BaseModel):
    scenario_id: str


class UpdateAlertRequest(BaseModel):
    status: AlertStatus
    note: Optional[str] = None


class CreateIncidentRequest(BaseModel):
    alert_ids: list[str]
    title: Optional[str] = None


class PlaybookActionRequest(BaseModel):
    step_id: str
    action: str  # complete | skip | execute
    notes: Optional[str] = None
    action_payload: Optional[dict[str, Any]] = None


class ContainmentRequest(BaseModel):
    action: str  # block_domain | reset_password | isolate_host | revoke_session | block_url
    target: str
    reason: str


class AIAssistRequest(BaseModel):
    question: str
    context_alert_id: Optional[str] = None


class AIAssistResponse(BaseModel):
    answer: str
    suggested_next_steps: list[str]
    mitre_hints: list[str]
    confidence: str
    teaching_note: str


class EnrichmentResult(BaseModel):
    ioc: str
    ioc_type: str
    reputation: str
    related_campaigns: list[str]
    whois_summary: Optional[str] = None
    dns_records: Optional[dict[str, Any]] = None
    risk_score: int
    analyst_guidance: str


class ScoreBreakdown(BaseModel):
    total: int
    max_total: int
    categories: dict[str, int]
    strengths: list[str]
    improvements: list[str]
    grade: str
