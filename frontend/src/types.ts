export type Severity = 'informational' | 'low' | 'medium' | 'high' | 'critical'
export type AlertStatus =
  | 'new'
  | 'triaging'
  | 'investigating'
  | 'contained'
  | 'resolved'
  | 'false_positive'

export interface ScenarioSummary {
  id: string
  title: string
  difficulty: string
  description: string
  mitre_tactics: string[]
  estimated_minutes: number
  learning_objectives: string[]
}

export interface IOC {
  type: string
  value: string
  context: string
  malicious: boolean
  reputation?: string
}

export interface Alert {
  id: string
  scenario_id: string
  title: string
  description: string
  severity: Severity
  status: AlertStatus
  created_at: string
  source: string
  category: string
  mitre_techniques: string[]
  related_email_id?: string
  related_user?: string
  related_host?: string
  iocs: IOC[]
  raw_evidence: Record<string, unknown>
}

export interface EmailMessage {
  id: string
  from_address: string
  from_display: string
  to_address: string
  subject: string
  received_at: string
  body_text: string
  body_html_preview: string
  headers: Record<string, string>
  urls: string[]
  attachments: { name: string; sha256?: string; type?: string }[]
  spoof_indicators: string[]
}

export interface TimelineEvent {
  id: string
  timestamp: string
  source: string
  actor: string
  action: string
  detail: string
  severity: Severity
}

export interface PlaybookStep {
  id: string
  phase: string
  title: string
  description: string
  guidance: string
  status: 'pending' | 'in_progress' | 'completed' | 'skipped'
  action_type?: string
  action_payload?: Record<string, string>
  completed_at?: string
  notes?: string
}

export interface Incident {
  id: string
  scenario_id: string
  title: string
  status: string
  severity: Severity
  created_at: string
  updated_at: string
  alert_ids: string[]
  playbook_steps: PlaybookStep[]
  containment_actions: ContainmentEntry[]
  analyst_notes: { at: string; text: string }[]
  score?: number
  feedback?: string[]
}

export interface ContainmentEntry {
  id: string
  action: string
  target: string
  reason: string
  at: string
  result: string
  detail: string
}

export interface SessionState {
  session_id: string
  scenario_id: string
  started_at: string
  alerts: Alert[]
  emails: EmailMessage[]
  timeline: TimelineEvent[]
  incident: Incident | null
  score: number
  max_score: number
  completed: boolean
  learning_tips_seen: string[]
  containment_log: ContainmentEntry[]
}

export interface AIAssistResponse {
  answer: string
  suggested_next_steps: string[]
  mitre_hints: string[]
  confidence: string
  teaching_note: string
}

export interface EnrichmentResult {
  ioc: string
  ioc_type: string
  reputation: string
  related_campaigns: string[]
  whois_summary?: string
  dns_records?: Record<string, unknown>
  risk_score: number
  analyst_guidance: string
}

export interface Scorecard {
  total: number
  max_total: number
  categories: Record<string, number>
  strengths: string[]
  improvements: string[]
  grade: string
}

export interface KnowledgeBase {
  title: string
  nist_phases: { phase: string; goals: string[] }[]
  quick_checks: string[]
  ai_soc_use_cases: string[]
}
