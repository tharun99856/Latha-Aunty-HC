# PRD — PHC Queue Management System
**Challenge 1.3 · Track B**
Version 1.1 · June 2026

---

## What We're Actually Building

A token + wait-time system for Primary Health Centres where patients currently show up at 7 AM, get a slip, and have no idea if they'll be seen at 9 AM or 1 PM. We give them a number, an honest time estimate, and a printed token they can trust. They leave the clinic, run their errands, and come back near their slot. Front desk keeps their phone number so staff can call them back if they're not present when called.

This is not an app. It is not a "platform." It is a FastAPI backend, a SQLite database, and a tablet on the front desk.

**Pilot site:** Latha Children's Clinic, Attapur, Hyderabad — a high-footfall single-doctor clinic with the same queue dynamics as a PHC, used as the accessible test site for the usability audit.

**Target deployment:** PHCs across Telangana / Andhra Pradesh, scaling to any single-doctor public health facility in India. The queue problem is identical across both contexts.

---

## The Core Problem (Specific, Not Abstract)

A typical PHC OPD runs one doctor, 80–120 patients a day, 6 AM to 2 PM. The waiting room holds maybe 30 people. The overflow spills into the corridor, the compound, the road. A daily-wage labourer who loses half a workday waiting also loses ₹300–500 in income.

The problem isn't that there are too many patients. It's that patients have no signal about when to actually show up, so everyone shows up at once.

**Three things we fix:**
1. Patients don't know their position in the queue without being physically present
2. Staff have no visibility into how many people are waiting vs. how many have wandered off
3. There is no mechanism to estimate when a patient's turn is approaching

---

## Users

**Patient (primary)** — Likely owns a basic phone. May not speak English. May be semi-literate in their regional language. Is not going to install an app. Walks in.

**Front-desk staff (primary)** — One or two people. Manages the OPD register, hands out tokens, handles a hundred small interruptions simultaneously. Cannot babysit a complex dashboard. Needs something that basically runs itself.

**Doctor / MO (secondary)** — Wants to know how many patients are left. Should be able to mark a consultation done in one tap.

**PHC admin / CMHO (secondary)** — Wants aggregate throughput data. Not in scope for v1.

---

## What the V1 System Does

### Token Issuance (the front desk)

A patient walks in. The front desk opens a browser tab (the tablet dashboard) and clicks **New Token**. The system:
- Assigns a token number (T-001, T-002, etc.)
- Asks for a mobile number (optional)
- Displays the token number on screen with an estimated wait time
- Stores the phone number alongside the token so staff can call the patient back if they're missing when called

No registration, no form, no login per patient.

### Doctor Console

Doctor or assistant clicks **Next Patient** after each consultation. This:
- Advances the queue counter
- Records the consultation duration into the rolling average
- Updates all live wait-time estimates

### Wait Time Estimation

No ML needed. A rolling average of the last 10 consultation durations is enough. If the last 10 consultations averaged 6 minutes each, and there are 8 patients ahead of T-014, estimated wait = 48 min. Displayed with a ± buffer. This is communicated honestly as an estimate.

Edge case: if the doctor goes on a break (no "Next Patient" click for >15 min), the system flags this on the dashboard and stops updating estimates until activity resumes.

### Front Desk Call-Back Workflow

The "Recent Tokens" table on the dashboard shows token, status, and phone number for every recent issuance. When the doctor calls the next patient and they're not physically present:
- Staff looks at the dashboard, finds the phone number
- Staff calls the patient manually
- Patient is told their turn is now

This is intentionally manual in V1. Automation (WhatsApp / SMS) is V2.

### End-of-Day

Admin clicks **Close OPD**. Any un-served tokens are marked no-show. Session closes; next day starts fresh.

---

## Future Scope (V2)

These are real needs explicitly scoped out of V1 to keep the prototype simple and free to run:

**Automated WhatsApp / SMS notifications** — Twilio (or Bhashini SMS gateway) integration to send:
- Token confirmation on issue
- 3-ahead notification when turn is near
- STATUS reply on inbound query
- OPD closure notification

Expected impact: lifts patient-trust adoption from ~50% to ~85%, increasing wait-time reduction from ~45% to ~75%.

**Multi-language UI** — Telugu and Hindi labels on the dashboard for non-English-speaking PHC staff. Identified as a critical pre-deployment finding in the usability audit.

**Multi-department queues** — separate parallel queues for lab and pharmacy (currently a single OPD queue only).

**Admin / CMHO analytics dashboard** — aggregate throughput data across multiple PHCs, exportable to district-level reports.

**IVR / voice call fallback** — for patients without smartphones, an automated call with token position via Exotel / Knowlarity.

V2 features are designed to layer on top of V1 without rewriting the queue core. V1 ships first.

---

## What It Does NOT Do (Either Version)

- No appointment booking. Patients still walk in. We are not changing the access model, only the waiting experience.
- No patient health records. No integration with any hospital management system.
- No facial recognition, no cameras, no biometrics.
- No app install required for patients.
- No internet required for the doctor console or front desk (local network is enough).

---

## Tech Stack

Chosen for: deployability by a non-DevOps team, minimal cost, works on cheap hardware.

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI (Python) | Simple, fast enough, easy to run on a Pi or a cheap VPS |
| Database | SQLite | No setup, no config, survives reboots, more than sufficient for 200 tokens/day |
| Frontend (dashboard) | Plain HTML + vanilla JS | Loads on a 2014 tablet over LAN. No build step, no Node.js |
| Hosting | Raspberry Pi 4 (local) or ₹500/mo VPS | Pi for full offline capability |

**Explicitly not using:** Redis, Celery, Docker (for v1), React, any ML model, Firebase, any third-party API.

---

## System Architecture

```
[Tablet — Front Desk]          [Tablet — Doctor]
  Browser → /dashboard    →     Browser → /doctor
         ↓                              ↓
              FastAPI Backend (local or VPS)
                      ↓
                  SQLite DB
```

The front desk and doctor tabs poll the backend every 5 seconds for queue state.

---

## Data Model

**Session** — date, open/close time, total tokens issued, total served

**Token** — token_id, number, phone (nullable), status (waiting/called/served/no-show), issued_at, called_at, served_at

**Consultation** — token_id, duration_seconds (for rolling average calculation)

Three tables. That's the entire database.

---

## API Surface

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/session/open` | Open today's OPD session |
| POST | `/api/session/close` | Close OPD, mark un-served tokens no-show |
| POST | `/api/token` | Issue a new token (optional phone) |
| GET | `/api/token/{number}` | Get status of a specific token |
| GET | `/api/queue` | Full queue state for dashboards |
| POST | `/api/queue/next` | Doctor advances queue (closes current, calls next) |

---

## Screens

### Front Desk Dashboard (`/dashboard`)
- Large current queue count (e.g., **23 waiting**)
- "New Token" button — big, can't miss it
- Optional phone number input ("for staff callback if needed")
- Estimated wait for next token issued
- Recent-tokens table showing **token, issued time, status, and phone number** (so staff can call back missing patients)
- Alert if doctor hasn't advanced queue in >15 min

### Doctor Console (`/doctor`)
- Current token being served (large, e.g., **NOW SERVING: T-008**)
- "Next Patient" button
- Count of remaining patients
- Today's served count

---

## Offline / Degraded State Behaviour

| Scenario | What Happens |
|---|---|
| Internet down | V1 doesn't care — no external API. LAN-only operation. |
| Power cut | Pi runs on UPS or mobile battery pack (~₹800 setup). SQLite survives power loss cleanly. |
| Staff doesn't click Next Patient | Queue freezes. System shows a warning after 15 min of inactivity. No automated "fix" — a human resolves it. |
| Tablet dies | Any phone browser on the same LAN can open the dashboard. No state is in the browser. |

---

## Risks

**Staff don't click "Next Patient"** — This is the biggest operational risk. If the doctor doesn't advance the queue, all estimates go wrong. Mitigation: make the button very visible on the doctor's tablet; gentle audio ping after 10 minutes of inactivity (V2).

**Phone number not given** — Some patients won't give a number (or don't have one). System handles this: they get a paper token with an estimate, and the queue still advances correctly. Phone is enhancement, not requirement.

**Patient doesn't trust the estimate** — If a patient doesn't believe the printed wait time, they stay physically present, and the throughput benefit doesn't materialize for them. Mitigation: estimate uses a rolling average that gets more accurate as the day progresses, and the front desk staff vouches verbally.

---

## Definition of Done

The V1 prototype is considered complete when:

- A front desk person who has never seen the system can issue 5 tokens in a row without help
- "Next Patient" advances the queue correctly
- The system recovers cleanly from a simulated power cut (queue state preserved)
- A 4-persona developer self-test audit has been conducted and documented
- Wait time estimate is within ±15 minutes of actual wait for a simulated 20-patient queue
- Phone numbers are stored and visible to staff in the recent-tokens table
