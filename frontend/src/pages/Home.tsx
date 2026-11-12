import { Link } from 'react-router-dom'

export function Home() {
  return (
    <section className="hero">
      <div className="hero-visual" aria-hidden="true" />
      <div className="hero-content">
        <h1 className="hero-brand">Aegis</h1>
        <p className="hero-headline">AI-powered SOC drills for phishing & incident response.</p>
        <p className="hero-sub">
          Practice triage, enrichment, containment, and NIST-aligned response against simulated
          spear-phishing, BEC, and ransomware precursor campaigns — without touching live attackers.
        </p>
        <div className="cta-row">
          <Link className="btn btn-primary" to="/scenarios">
            Enter the lab
          </Link>
          <Link className="btn btn-secondary" to="/knowledge">
            Study IR playbooks
          </Link>
        </div>
      </div>
    </section>
  )
}
