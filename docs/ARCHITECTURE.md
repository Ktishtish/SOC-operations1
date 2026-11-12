# Architecture

```
Browser (React SOC Console)
        │  /api/*
        ▼
FastAPI (SOCWatch backend)
  ├─ Scenario loader (JSON packs)
  ├─ Session store (in-memory lab state)
  ├─ Enrichment service (simulated intel)
  ├─ Incident / playbook / containment
  ├─ AI analyst coach (deterministic teaching assistant)
  └─ Scoring rubric
```

## Design choices

- **In-memory sessions** keep the lab zero-dependency for classroom use.  
- **Deterministic AI coach** teaches consistently without requiring API keys.  
- **Scenario packs** separate content from engine so instructors can add campaigns.  
- **Simulated containment** records actions for scoring without touching real systems.

## Extending

1. Add a new JSON file under `backend/app/data/scenarios/`.  
2. Include emails, alerts, timeline, playbook, enrichment_db, and scoring keys.  
3. Restart the API — scenarios are loaded from disk on startup (cached).
