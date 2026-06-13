# PHC Queue Management System

A token + wait-time system for Primary Health Centres. Patients get a token, leave the clinic, and come back when a WhatsApp message tells them their turn is near.

**Challenge 1.3 · Track B — Intelligent Systems for Public Service Access**

**Pilot site:** Latha Children's Clinic, Attapur, Hyderabad
**Target deployment:** PHCs across Telangana / India

---

## What's in this repo

| Path | Purpose |
|---|---|
| `app/` | FastAPI backend, SQLite, Twilio WhatsApp integration |
| `static/` | Front-desk dashboard and doctor console (plain HTML + JS) |
| `docs/PRD.md` | Product requirements |
| `docs/DELIVERABLES.md` | BOM, throughput estimate, success metrics |
| `docs/USABILITY_AUDIT.md` | 5-user usability audit protocol + report template |
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

To enable WhatsApp, copy `.env.example` to `.env` and fill in Twilio credentials.

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
- **₹1,500/month** WhatsApp messaging cost at 200 patients/day

Full breakdown in [docs/DELIVERABLES.md](docs/DELIVERABLES.md).

---

## How it works in one paragraph

The front desk clicks **New Token** — patient gets a number and (if they provided one) a WhatsApp confirmation. The doctor clicks **Next Patient** after each consultation, which advances the queue. The system tracks the rolling average of the last 10 consultation durations and uses it to estimate wait times. When a patient is 3 ahead, they get a WhatsApp message telling them to head to the OPD. They can reply STATUS at any time to check their position. No app install for patients, no internet required for the queue logic (only for WhatsApp).

---

## Tech choices, briefly

- **FastAPI + SQLite** — runs on a Raspberry Pi, survives power loss
- **Plain HTML + JS** — no build step, loads on cheap tablets, anyone can fix it
- **Twilio WhatsApp** — proven, well-documented, ₹0.8–1.2 per message
- **No Redis, no Docker, no React, no ML** — every dependency justified by an actual constraint
