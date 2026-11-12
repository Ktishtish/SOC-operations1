import { useEffect, useState } from 'react'
import { api } from '../api'
import type { KnowledgeBase } from '../types'

export function Knowledge() {
  const [data, setData] = useState<KnowledgeBase | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .knowledge()
      .then(setData)
      .catch((err: Error) => setError(err.message))
  }, [])

  return (
    <main className="page">
      <div className="section-head">
        <h1>Phishing IR knowledge base</h1>
        <p>
          Core SOC reference for simulated phishing response — NIST phases, rapid email checks, and
          where AI assists analysts without replacing judgment.
        </p>
      </div>
      {error && <div className="error-banner">{error}</div>}
      {!data && !error && <p className="muted">Loading…</p>}
      {data && (
        <div className="knowledge-grid">
          <section className="panel">
            <div className="panel-h">
              <h2>NIST-aligned phases</h2>
            </div>
            <div className="panel-b">
              {data.nist_phases.map((phase) => (
                <div className="phase-block" key={phase.phase}>
                  <h3>{phase.phase}</h3>
                  <ul>
                    {phase.goals.map((g) => (
                      <li key={g}>{g}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>
          <div style={{ display: 'grid', gap: '1rem' }}>
            <section className="panel">
              <div className="panel-h">
                <h2>Quick phishing checks</h2>
              </div>
              <div className="panel-b">
                <ul className="check-list">
                  {data.quick_checks.map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              </div>
            </section>
            <section className="panel">
              <div className="panel-h">
                <h2>AI in the SOC</h2>
              </div>
              <div className="panel-b">
                <ul className="check-list">
                  {data.ai_soc_use_cases.map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              </div>
            </section>
          </div>
        </div>
      )}
    </main>
  )
}
