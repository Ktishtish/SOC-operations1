# Aegis — AI-Powered SOC Lab

**Topic:** AI-Powered SOC · **Focus:** Simulated Phishing Attack & Incident Response

Aegis is a defensive training platform that builds Security Operations Center (SOC) skills through realistic, **simulated** phishing campaigns. Analysts practice alert triage, email/header analysis, IOC enrichment, containment, and NIST-aligned incident response — coached by an embedded AI SOC assistant.

> This project is for **education and blue-team skill building only**. It does not send real phishing mail, exploit systems, or provide offensive attack tooling.

## What you practice

| Skill | Lab capability |
| --- | --- |
| Phishing triage | Alert queue with severity, MITRE tags, and mailbox evidence |
| Email forensics | Headers, SPF/DKIM/DMARC, spoof indicators, lookalike domains |
| Threat enrichment | Simulated intel lookups (WHOIS, reputation, campaigns) |
| Containment | Block domain/URL, reset password, revoke session, isolate host |
| Incident response | Playbooks mapped to detection → lessons learned |
| AI-assisted SOC | Coach for triage order, containment choices, MITRE, playbooks |
| After-action review | Scorecard with strengths and improvement guidance |

## Scenarios

1. **Spear-Phishing: Fake Payroll Portal** (beginner) — credential harvest → account takeover  
2. **BEC: Vendor Invoice Redirect** (intermediate) — lookalike vendor / payment fraud  
3. **Malicious Macro Phish → Ransomware Precursor** (advanced) — macro → C2 → staging  

## Stack

- **Backend:** Python FastAPI (scenario engine, IR workflow, AI coach, scoring)
- **Frontend:** React + Vite + TypeScript (SOC console UI)
- **Data:** Versioned JSON scenario packs (emails, alerts, timelines, playbooks)

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 20+

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 — the Vite dev server proxies `/api` to the backend.

### One-shot demo script

```bash
./scripts/run-demo.sh
```

### Tests

```bash
cd backend
PYTHONPATH=. python -m pytest tests -q
```

## Learning path

1. Read **IR Playbook** in the UI for NIST phases and phishing quick checks  
2. Run the beginner payroll spear-phish scenario  
3. Ask the AI coach “What should I do first?”  
4. Enrich IOCs → open an incident → execute containment → complete playbook steps  
5. Finish for a scorecard, then attempt BEC and ransomware precursor scenarios  

## Project layout

```
backend/
  app/
    main.py              # FastAPI app
    routers/api.py       # REST endpoints
    services/            # scenarios, AI coach, enrichment, IR, scoring
    data/scenarios/      # Simulated phishing IR packs
  tests/
frontend/
  src/pages/             # Home, Scenarios, Console, Knowledge
docs/
  LEARNING_GUIDE.md
  ARCHITECTURE.md
scripts/
  run-demo.sh
```

## Safety & ethics

- All phishing content is **fictional and simulated** inside the lab.  
- Containment actions are **mocked** — nothing is blocked on real infrastructure.  
- Do not reuse scenario lures against real users or production systems.  

## License

Educational use. Adapt for internal SOC onboarding and tabletop exercises.
