import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import type {
  AIAssistResponse,
  Alert,
  AlertStatus,
  EnrichmentResult,
  Scorecard,
  SessionState,
} from '../types'

type Tab = 'evidence' | 'timeline' | 'containment' | 'playbook'

export function Console() {
  const { sessionId = '' } = useParams()
  const [session, setSession] = useState<SessionState | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('evidence')
  const [error, setError] = useState('')
  const [note, setNote] = useState('')
  const [containAction, setContainAction] = useState('block_domain')
  const [containTarget, setContainTarget] = useState('')
  const [containReason, setContainReason] = useState('Training containment action')
  const [enrichIoc, setEnrichIoc] = useState('')
  const [enrichment, setEnrichment] = useState<EnrichmentResult | null>(null)
  const [aiQuestion, setAiQuestion] = useState('What should I do first?')
  const [aiReply, setAiReply] = useState<AIAssistResponse | null>(null)
  const [scorecard, setScorecard] = useState<Scorecard | null>(null)
  const [busy, setBusy] = useState(false)

  const refresh = useCallback(async () => {
    const data = await api.getSession(sessionId)
    setSession(data)
    return data
  }, [sessionId])

  useEffect(() => {
    let cancelled = false
    refresh()
      .then((data) => {
        if (!cancelled && data.alerts[0]) {
          setSelectedId((current) => current ?? data.alerts[0].id)
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [refresh])

  const selected: Alert | undefined = useMemo(
    () => session?.alerts.find((a) => a.id === selectedId),
    [session, selectedId],
  )

  const relatedEmail = useMemo(() => {
    if (!session || !selected?.related_email_id) return null
    return session.emails.find((e) => e.id === selected.related_email_id) || null
  }, [session, selected])

  async function run(task: () => Promise<void>) {
    setBusy(true)
    setError('')
    try {
      await task()
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setBusy(false)
    }
  }

  if (!session) {
    return (
      <main className="page">
        {error ? <div className="error-banner">{error}</div> : <p className="muted">Loading console…</p>}
      </main>
    )
  }

  if (scorecard) {
    return (
      <main className="page">
        <div className="section-head">
          <h1>IR scorecard</h1>
          <p>Session complete. Review how your triage and containment choices scored.</p>
        </div>
        <div className="panel">
          <div className="panel-b scorecard">
            <div>
              <div className="grade">{scorecard.grade}</div>
              <p className="score-pill">
                {scorecard.total}/{scorecard.max_total}
              </p>
            </div>
            <div>
              {Object.entries(scorecard.categories).map(([key, value]) => (
                <div key={key} style={{ marginBottom: '0.85rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span>{key.replaceAll('_', ' ')}</span>
                    <span className="muted">{value}</span>
                  </div>
                  <div className="bar">
                    <span style={{ width: `${Math.min(100, value * 5)}%` }} />
                  </div>
                </div>
              ))}
              <h3>Strengths</h3>
              <ul className="check-list">
                {scorecard.strengths.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
              <h3>Improve next run</h3>
              <ul className="check-list">
                {scorecard.improvements.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
              <div className="cta-row" style={{ marginTop: '1.25rem' }}>
                <Link className="btn btn-primary" to="/scenarios">
                  Run another scenario
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <div className="console">
      {error && <div className="error-banner">{error}</div>}
      <div className="console-bar">
        <div>
          <strong>SOC Console</strong>
          <span className="muted"> · {session.scenario_id.replaceAll('_', ' ')}</span>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <span className="score-pill">
            score {session.score}/{session.max_score}
          </span>
          {session.incident && (
            <span className="chip">{session.incident.id} · {session.incident.status}</span>
          )}
          <button
            className="btn btn-secondary btn-small"
            disabled={busy || !!session.incident}
            onClick={() =>
              run(async () => {
                const ids = session.alerts.map((a) => a.id)
                await api.createIncident(session.session_id, ids)
              })
            }
          >
            Open incident
          </button>
          <button
            className="btn btn-primary btn-small"
            disabled={busy}
            onClick={() =>
              run(async () => {
                const result = await api.complete(session.session_id)
                setSession(result.session)
                setScorecard(result.scorecard)
              })
            }
          >
            Complete & score
          </button>
        </div>
      </div>

      <div className="console-grid">
        <section className="panel">
          <div className="panel-h">
            <h2>Alert queue</h2>
            <span className="chip">{session.alerts.length}</span>
          </div>
          <div className="panel-b alert-list">
            {session.alerts.map((alert) => (
              <button
                key={alert.id}
                className={`alert-item ${selectedId === alert.id ? 'active' : ''}`}
                onClick={() => {
                  setSelectedId(alert.id)
                  setContainTarget(alert.iocs[0]?.value || alert.related_host || alert.related_user || '')
                  setEnrichIoc(alert.iocs[0]?.value || '')
                }}
              >
                <div className={`sev ${alert.severity}`}>{alert.severity}</div>
                <div className="title">{alert.title}</div>
                <div className="status">
                  {alert.status} · {alert.source}
                </div>
              </button>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-h">
            <h2>Investigation</h2>
            <div className="tabs">
              {(['evidence', 'timeline', 'containment', 'playbook'] as Tab[]).map((t) => (
                <button
                  key={t}
                  className={`tab ${tab === t ? 'active' : ''}`}
                  onClick={() => setTab(t)}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
          <div className="panel-b detail-stack">
            {!selected && <div className="empty">Select an alert to investigate.</div>}

            {selected && tab === 'evidence' && (
              <>
                <div className="detail-block">
                  <h3>{selected.title}</h3>
                  <p>{selected.description}</p>
                  <dl className="kv">
                    <dt>severity</dt>
                    <dd className={`sev ${selected.severity}`}>{selected.severity}</dd>
                    <dt>category</dt>
                    <dd>{selected.category}</dd>
                    <dt>user</dt>
                    <dd>{selected.related_user || '—'}</dd>
                    <dt>host</dt>
                    <dd>{selected.related_host || '—'}</dd>
                    <dt>mitre</dt>
                    <dd>{selected.mitre_techniques.join(', ') || '—'}</dd>
                  </dl>
                  <div className="form-row">
                    <select
                      value={selected.status}
                      onChange={(e) =>
                        run(async () => {
                          await api.updateAlert(
                            session.session_id,
                            selected.id,
                            e.target.value as AlertStatus,
                            note || undefined,
                          )
                          setNote('')
                        })
                      }
                    >
                      {[
                        'new',
                        'triaging',
                        'investigating',
                        'contained',
                        'resolved',
                        'false_positive',
                      ].map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                    <input
                      placeholder="Analyst note"
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                    />
                  </div>
                </div>

                {relatedEmail && (
                  <div className="detail-block">
                    <h3>Email evidence</h3>
                    <dl className="kv">
                      <dt>from</dt>
                      <dd>
                        {relatedEmail.from_display} &lt;{relatedEmail.from_address}&gt;
                      </dd>
                      <dt>to</dt>
                      <dd>{relatedEmail.to_address}</dd>
                      <dt>subject</dt>
                      <dd>{relatedEmail.subject}</dd>
                    </dl>
                    <div className="email-box">{relatedEmail.body_text}</div>
                    <h4 style={{ marginBottom: 0 }}>Spoof indicators</h4>
                    <ul className="spoof-list">
                      {relatedEmail.spoof_indicators.map((s) => (
                        <li key={s}>{s}</li>
                      ))}
                    </ul>
                    <h4>Headers</h4>
                    <div className="email-box">
                      {Object.entries(relatedEmail.headers)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join('\n')}
                    </div>
                  </div>
                )}

                <div className="detail-block">
                  <h3>IOCs</h3>
                  <div className="ioc-list">
                    {selected.iocs.map((ioc) => (
                      <div className="ioc-row" key={`${ioc.type}-${ioc.value}`}>
                        <div>
                          <div className="chip">{ioc.type}</div>
                          <div>
                            <code>{ioc.value}</code>
                          </div>
                          <div className="muted">{ioc.context}</div>
                        </div>
                        <button
                          className="btn btn-secondary btn-small"
                          disabled={busy}
                          onClick={() =>
                            run(async () => {
                              const result = await api.enrich(session.session_id, ioc.value)
                              setEnrichment(result)
                              setEnrichIoc(ioc.value)
                            })
                          }
                        >
                          Enrich
                        </button>
                      </div>
                    ))}
                  </div>
                  <div className="form-row">
                    <input
                      value={enrichIoc}
                      onChange={(e) => setEnrichIoc(e.target.value)}
                      placeholder="IOC to enrich"
                    />
                    <button
                      className="btn btn-secondary btn-small"
                      disabled={busy || !enrichIoc}
                      onClick={() =>
                        run(async () => {
                          setEnrichment(await api.enrich(session.session_id, enrichIoc))
                        })
                      }
                    >
                      Lookup
                    </button>
                  </div>
                  {enrichment && (
                    <div className="enrich-card">
                      <strong>{enrichment.ioc}</strong>
                      <div className={`sev ${enrichment.risk_score > 80 ? 'critical' : 'high'}`}>
                        risk {enrichment.risk_score} · {enrichment.reputation}
                      </div>
                      <p className="muted">{enrichment.analyst_guidance}</p>
                      {enrichment.whois_summary && <p>{enrichment.whois_summary}</p>}
                      {enrichment.related_campaigns.length > 0 && (
                        <div className="meta-row">
                          {enrichment.related_campaigns.map((c) => (
                            <span className="chip" key={c}>
                              {c}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </>
            )}

            {tab === 'timeline' && (
              <div className="timeline">
                {session.timeline.map((ev) => (
                  <div className="timeline-item" key={ev.id}>
                    <div className={`sev ${ev.severity}`}>{ev.timestamp}</div>
                    <strong>
                      {ev.action} · {ev.actor}
                    </strong>
                    <div className="muted">
                      {ev.source}: {ev.detail}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {tab === 'containment' && (
              <div className="detail-block">
                <h3>Simulated containment</h3>
                <p className="muted">
                  Training actions only — block domains/URLs, reset passwords, revoke sessions, or
                  isolate hosts in this lab environment.
                </p>
                <div className="form-row">
                  <select value={containAction} onChange={(e) => setContainAction(e.target.value)}>
                    <option value="block_domain">block_domain</option>
                    <option value="block_url">block_url</option>
                    <option value="reset_password">reset_password</option>
                    <option value="revoke_session">revoke_session</option>
                    <option value="isolate_host">isolate_host</option>
                  </select>
                  <input
                    value={containTarget}
                    onChange={(e) => setContainTarget(e.target.value)}
                    placeholder="target"
                  />
                </div>
                <div className="form-row">
                  <input
                    value={containReason}
                    onChange={(e) => setContainReason(e.target.value)}
                    placeholder="reason"
                  />
                  <button
                    className="btn btn-danger btn-small"
                    disabled={busy || !containTarget}
                    onClick={() =>
                      run(async () => {
                        await api.contain(
                          session.session_id,
                          containAction,
                          containTarget,
                          containReason,
                        )
                      })
                    }
                  >
                    Execute
                  </button>
                </div>
                <div className="ioc-list" style={{ marginTop: '1rem' }}>
                  {session.containment_log.length === 0 && (
                    <div className="empty">No containment actions yet.</div>
                  )}
                  {session.containment_log.map((c) => (
                    <div className="note-item" key={c.id}>
                      <code>
                        {c.action} → {c.target}
                      </code>
                      <div className="muted">
                        {c.at} · {c.detail}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {tab === 'playbook' && (
              <div className="playbook">
                {!session.incident && (
                  <div className="empty">Open an incident to unlock the IR playbook.</div>
                )}
                {session.incident?.playbook_steps.map((step) => (
                  <div className={`play-step ${step.status}`} key={step.id}>
                    <div className="phase">
                      {step.phase} · {step.status}
                    </div>
                    <strong>{step.title}</strong>
                    <p className="muted">{step.description}</p>
                    <p className="teaching">{step.guidance}</p>
                    {step.status === 'pending' && (
                      <div className="form-row">
                        <button
                          className="btn btn-primary btn-small"
                          disabled={busy}
                          onClick={() =>
                            run(async () => {
                              await api.playbook(
                                session.session_id,
                                step.id,
                                step.action_type === 'containment' ? 'execute' : 'complete',
                                'Completed during training run',
                                step.action_payload,
                              )
                            })
                          }
                        >
                          {step.action_type === 'containment' ? 'Execute step' : 'Mark complete'}
                        </button>
                        <button
                          className="btn btn-secondary btn-small"
                          disabled={busy}
                          onClick={() =>
                            run(async () => {
                              await api.playbook(session.session_id, step.id, 'skip', 'Skipped')
                            })
                          }
                        >
                          Skip
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="panel ai-panel">
          <div className="panel-h">
            <h2>AI SOC coach</h2>
            <span className="chip">assist</span>
          </div>
          <div className="panel-b">
            <p className="muted">
              Ask for triage order, header analysis, containment choices, MITRE mapping, or playbook
              guidance.
            </p>
            <div className="form-row">
              <textarea value={aiQuestion} onChange={(e) => setAiQuestion(e.target.value)} />
            </div>
            <div className="form-row">
              <button
                className="btn btn-primary btn-small"
                disabled={busy || !aiQuestion.trim()}
                onClick={() =>
                  run(async () => {
                    setAiReply(
                      await api.assist(session.session_id, aiQuestion, selected?.id),
                    )
                  })
                }
              >
                Ask coach
              </button>
            </div>
            {aiReply && (
              <div className="ai-bubble" style={{ marginTop: '0.75rem' }}>
                <div>{aiReply.answer}</div>
                <div className="teaching">{aiReply.teaching_note}</div>
                <h4>Suggested next steps</h4>
                <ul className="check-list">
                  {aiReply.suggested_next_steps.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
                <div className="meta-row" style={{ marginTop: '0.5rem' }}>
                  {aiReply.mitre_hints.map((m) => (
                    <span className="chip" key={m}>
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div style={{ marginTop: '1rem' }}>
              <h4>Quick prompts</h4>
              <div className="meta-row">
                {[
                  'What should I do first?',
                  'How do I read SPF/DKIM/DMARC?',
                  'Which containment actions fit?',
                  'Map this to MITRE',
                ].map((q) => (
                  <button
                    key={q}
                    className="chip"
                    style={{ cursor: 'pointer', background: 'transparent' }}
                    onClick={() => setAiQuestion(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
