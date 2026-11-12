import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import type { ScenarioSummary } from '../types'

export function Scenarios() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([])
  const [error, setError] = useState('')
  const [loadingId, setLoadingId] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    api
      .scenarios()
      .then(setScenarios)
      .catch((err: Error) => setError(err.message || 'Failed to load scenarios'))
  }, [])

  async function start(scenarioId: string) {
    setLoadingId(scenarioId)
    setError('')
    try {
      const session = await api.startSession(scenarioId)
      navigate(`/console/${session.session_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start session')
      setLoadingId(null)
    }
  }

  return (
    <main className="page">
      <div className="section-head">
        <h1>Phishing IR scenarios</h1>
        <p>
          Choose a simulated campaign. Each run seeds alerts, mailbox evidence, timeline events, and
          an AI coach that teaches SOC decision-making.
        </p>
      </div>
      {error && <div className="error-banner">{error}</div>}
      <div className="scenario-grid">
        {scenarios.map((s) => (
          <button
            key={s.id}
            className="scenario-item"
            onClick={() => start(s.id)}
            disabled={loadingId === s.id}
          >
            <div className="difficulty">{s.difficulty}</div>
            <h3>{s.title}</h3>
            <p>{s.description}</p>
            <div className="meta-row">
              <span className="chip">{s.estimated_minutes} min</span>
              {s.mitre_tactics.slice(0, 2).map((t) => (
                <span className="chip" key={t}>
                  {t}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>
    </main>
  )
}
