import type {
  AIAssistResponse,
  Alert,
  AlertStatus,
  EnrichmentResult,
  KnowledgeBase,
  ScenarioSummary,
  Scorecard,
  SessionState,
} from './types'

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || res.statusText)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string }>('/health'),
  scenarios: () => request<ScenarioSummary[]>('/scenarios'),
  startSession: (scenario_id: string) =>
    request<SessionState>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ scenario_id }),
    }),
  getSession: (sessionId: string) => request<SessionState>(`/sessions/${sessionId}`),
  updateAlert: (sessionId: string, alertId: string, status: AlertStatus, note?: string) =>
    request<Alert>(`/sessions/${sessionId}/alerts/${alertId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, note }),
    }),
  createIncident: (sessionId: string, alert_ids: string[], title?: string) =>
    request(`/sessions/${sessionId}/incidents`, {
      method: 'POST',
      body: JSON.stringify({ alert_ids, title }),
    }),
  contain: (sessionId: string, action: string, target: string, reason: string) =>
    request(`/sessions/${sessionId}/containment`, {
      method: 'POST',
      body: JSON.stringify({ action, target, reason }),
    }),
  playbook: (
    sessionId: string,
    step_id: string,
    action: string,
    notes?: string,
    action_payload?: Record<string, string>,
  ) =>
    request(`/sessions/${sessionId}/playbook`, {
      method: 'POST',
      body: JSON.stringify({ step_id, action, notes, action_payload }),
    }),
  enrich: (sessionId: string, ioc: string) =>
    request<EnrichmentResult>(`/sessions/${sessionId}/enrich?ioc=${encodeURIComponent(ioc)}`),
  assist: (sessionId: string, question: string, context_alert_id?: string) =>
    request<AIAssistResponse>(`/sessions/${sessionId}/ai/assist`, {
      method: 'POST',
      body: JSON.stringify({ question, context_alert_id }),
    }),
  complete: (sessionId: string) =>
    request<{ session: SessionState; scorecard: Scorecard }>(`/sessions/${sessionId}/complete`, {
      method: 'POST',
    }),
  knowledge: () => request<KnowledgeBase>('/knowledge/playbooks'),
}
