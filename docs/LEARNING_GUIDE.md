# Aegis Learning Guide — Simulated Phishing & IR

## Goal

Advance SOC operations knowledge by practicing an end-to-end phishing incident: detection, analysis, containment, eradication, recovery, and lessons learned — with AI coaching.

## Analyst workflow (recommended)

1. **Triage the queue** — open critical/high alerts first.  
2. **Inspect email evidence** — Authentication-Results, From vs Reply-To, lookalike domains, urgency language.  
3. **Enrich IOCs** — domains, URLs, IPs, hashes before broad action when time allows.  
4. **Open an incident** — unlock the scenario playbook.  
5. **Contain** — match actions to the kill chain stage (credentials vs BEC vs ransomware).  
6. **Work the playbook** — complete phases; document notes.  
7. **Score the run** — review strengths and gaps; repeat on harder scenarios.

## Scenario tips

### Fake Payroll Portal

- SPF/DMARC failures + lookalike domain are strong phishing signals.  
- After credential POST and anomalous SSO, prioritize `reset_password` + `revoke_session` and `block_domain`.  
- Hunt mailbox forwarding rules during eradication.

### BEC Vendor Redirect

- Auth can **pass** on attacker-owned lookalike domains.  
- Business priority: stop the pending wire, then block infrastructure.  
- Always verify vendors out-of-band (not via Reply-To).

### Macro → Ransomware Precursor

- Imminent impact: `isolate_host` before perfect documentation.  
- Block C2 IP/domain; hunt for the loader hash on other hosts.  
- Prefer reimage for ransomware staging endpoints.

## How AI helps (and what it shouldn’t do)

**Use AI for:** summarization, triage suggestions, MITRE hints, playbook reminders, enrichment prioritization.  

**You still own:** evidence validation, containment authorization, business communication, and final disposition.
