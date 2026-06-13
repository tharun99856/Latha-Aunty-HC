# Deliverables — PHC Queue Management System
**Challenge 1.3 · Track B**

---

## 1. Working Prototype

A FastAPI backend + SQLite + two browser screens, fully implemented and runnable on a Raspberry Pi or any cheap VPS.

**How to run:**
```
python -m pip install -r requirements.txt
python run.py
```

Then open:
- `http://<host>:8000/dashboard` — front desk
- `http://<host>:8000/doctor` — doctor console

**What works end-to-end:**
- Open / close OPD session
- Issue tokens (with or without phone)
- Track patient state (waiting → called → served / no-show)
- Doctor advances queue one patient at a time
- WhatsApp confirmation on token issue
- 3-ahead WhatsApp notification when a patient's turn nears
- Inbound STATUS query handled via Twilio webhook
- Rolling 10-consultation average for wait estimation
- Doctor-inactivity warning after 15 min

**Tested:**
- Backend integration test (`test_flow.py`) — covers open → issue 5 tokens → advance queue → status check
- Throughput simulation (`simulation.py`) — 10 runs × 100 patients

---

## 2. Bill of Materials (Per PHC Deployment)

| Item | Cost (INR) |
|---|---|
| Raspberry Pi 4 (2GB) + case + 32GB SD card | 4,500 |
| Power supply + 10,000 mAh power bank (UPS) | 800 |
| Cheap Android tablet, 8" (reuse if PHC has one) | 4,000 |
| **One-time hardware total** | **9,300** |
| Twilio WhatsApp messages (200 patients × 3 msg × 25 days) | ~1,500 / month |
| **Recurring monthly cost** | **~1,500** |

**Cost ceiling check:** ₹9,300 hardware is under the ₹10,000 per-deployment target.

**10-PHC deployment estimate:**
- Hardware: ₹9,300 × 10 = **₹93,000 one-time**
- Operating: ₹1,500 × 10 × 12 = **₹1,80,000 / year**
- Total year-1: **₹2,73,000** for ~30,000 patients/day across 10 PHCs

**Cost-per-patient-visit:** approximately **₹0.36** in year 1, dropping to **₹0.24** in subsequent years (no hardware repurchase).

If the PHC already has any Android device, the Pi is optional and a ₹500/month VPS replaces it — bringing hardware cost per PHC to under ₹4,500.

---

## 3. Throughput Improvement Estimate

Modelled via `simulation.py`. Source code is in the repo and reproducible.

### Model

- One doctor, OPD 9 AM – 2 PM
- Consultation duration: 5.5 min mean, σ = 1.8 min (Normal)
- 100 patients per day, arriving Gaussian-distributed between 6:30 – 8:30 AM (peak ~7 AM)
- 75% WhatsApp adoption (matches Indian rural smartphone penetration estimates)
- WhatsApp users return ~15 min before their slot (after the 3-ahead notification)

### Results (10 runs averaged)

| Metric | Baseline | With System | Reduction |
|---|---|---|---|
| Average physical wait time | **6h 06m** | **1h 59m** | **67.4%** |
| Peak in-clinic occupancy | ~100 patients | ~30 patients | **69.4%** |

### Sensitivity to WhatsApp adoption

| Adoption rate | Wait reduction |
|---|---|
| 30% | 24.2% |
| 50% | 43.3% |
| 70% | 61.0% |
| 90% | 80.2% |

**Target (≥30% reduction) is met at any adoption rate above ~38%.** At realistic Indian smartphone penetration (60–80%), the system exceeds the target by 2× or more.

### Why the model is conservative

- We don't count time saved by patients who can run errands or work while waiting
- We don't count reduced no-shows (people leave when they can't see when they'll be seen)
- Doctor consultation time is held constant; in practice, reduced crowd noise improves consultation quality

---

## 4. Success Metrics — Status

| Metric | Target | Status |
|---|---|---|
| Wait time reduction | ≥ 30% | **67%** (simulation, 10-run avg) |
| Per-deployment cost | ≤ ₹10,000 | **₹9,300** ✓ |
| Usability rating | ≥ 80% positive | See [USABILITY_AUDIT.md](USABILITY_AUDIT.md) |
| Setup time (new session) | < 2 min | **1 click**, ~5 sec ✓ |
| System downtime | < 10 min / day | depends on power / network; SQLite + local LAN keeps queue running through internet outage ✓ |

---

## 5. Files in This Submission

```
my cllg project/
├── app/                         backend
│   ├── main.py                  FastAPI routes
│   ├── queue.py                 queue logic + wait estimation
│   ├── whatsapp.py              Twilio integration
│   └── database.py              SQLite schema + connection
├── static/                      frontend
│   ├── dashboard.html           front desk screen
│   ├── doctor.html              doctor console
│   └── style.css                shared styles
├── docs/
│   ├── PRD.md                   product requirements
│   ├── DELIVERABLES.md          this file
│   └── USABILITY_AUDIT.md       audit protocol + results
├── simulation.py                throughput model
├── test_flow.py                 backend integration test
├── run.py                       server entry point
├── requirements.txt
├── .env.example                 Twilio config template
└── README.md
```
