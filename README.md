# PHC Queue Management System

A token + wait-time system for Primary Health Centres. Patients get a printed token with an honest wait estimate and leave the clinic. Front desk keeps their phone number so staff can call them back if they're missing when called.

**Challenge 1.3 · Track B — Intelligent Systems for Public Service Access**

**Pilot site:** Latha Children's Clinic, Attapur, Hyderabad
**Target deployment:** PHCs across Telangana / India

---

## What's in this repo

| Path | Purpose |
|---|---|
| `app/` | FastAPI backend + SQLite |
| `static/` | Front-desk dashboard and doctor console (plain HTML + JS) |
| `docs/PRD.md` | Product requirements |
| `docs/DELIVERABLES.md` | BOM, throughput estimate, success metrics |
| `docs/USABILITY_AUDIT.md` | 4-persona developer self-test audit |
| `docs/USABILITY_AUDIT.pdf` | Same audit, print-ready |
| `simulation.py` | Throughput model — baseline vs. new system |
| `test_flow.py` | End-to-end backend test |

---

## Run it

```bash
python -m pip install -r requirements.txt
python run.py
```

Open:
- **Front desk:** http://localhost:8000/dashboard
- **Doctor console:** http://localhost:8000/doctor

Copy `.env.example` to `.env` to set the clinic name. No external API keys required for V1.

---

## Verify it works

```bash
python test_flow.py     # backend smoke test
python simulation.py    # throughput simulation (10 runs × 100 patients)
```

---

## Headline numbers

- **67% reduction in physical wait time** (simulation, 10 runs × 100 patients)
- **69% reduction in peak in-clinic occupancy**
- **₹9,300** one-time hardware cost per PHC (under the ₹10,000 ceiling)
- **₹0 / month** running cost in V1 — no third-party API dependency

Full breakdown in [docs/DELIVERABLES.md](docs/DELIVERABLES.md).

---

## How it works in one paragraph

The front desk clicks **New Token** — patient gets a printed token with their position and a wait estimate based on the rolling 10-consultation average. Phone number is captured (optional). The doctor clicks **Next Patient** after each consultation, which advances the queue and updates everyone's estimates. The front-desk dashboard shows phone numbers for the recent tokens, so staff can call a patient if they don't show up when called. No app install for patients, no internet required for the queue logic.

---

## V1 vs V2 scope

| Capability | V1 (this submission) | V2 (future) |
|---|---|---|
| Token issue + queue advance | ✓ | ✓ |
| Wait time estimation | ✓ | ✓ |
| Phone number capture | ✓ | ✓ |
| Doctor inactivity alert | ✓ | ✓ |
| Manual staff callback to patient | ✓ | — |
| Automated WhatsApp / SMS notifications | — | ✓ |
| Multi-language UI (Telugu / Hindi) | — | ✓ |
| Multi-department queues | — | ✓ |
| Admin / CMHO analytics | — | ✓ |

V1 deliberately ships without third-party messaging integration to keep the prototype simple, free to run, and demonstrable without external accounts.

---

## Tech choices, briefly

- **FastAPI + SQLite** — runs on a Raspberry Pi, survives power loss
- **Plain HTML + JS** — no build step, loads on cheap tablets, anyone can fix it
- **No Redis, no Docker, no React, no ML, no third-party APIs in V1** — every dependency justified by an actual constraint
