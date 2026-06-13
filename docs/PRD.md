# PRD — PHC Queue Management System
**Challenge 1.3 · Track B**
Version 1.0 · June 2026

---

## What We're Actually Building

A token + wait-time system for Primary Health Centres where patients currently show up at 7 AM, get a slip, and have no idea if they'll be seen at 9 AM or 1 PM. We give them a number, an estimated time, and a way to leave and come back — over WhatsApp, because that's what they already use.

This is not an app. It is not a "platform." It is a FastAPI backend, a WhatsApp bot, and a tablet on the front desk.

**Pilot site:** Latha Children's Clinic, Attapur, Hyderabad — a high-footfall single-doctor clinic with the same queue dynamics as a PHC, used as the accessible test site for the usability audit.

**Target deployment:** PHCs across Telangana / Andhra Pradesh, scaling to any single-doctor public health facility in India. The queue problem is identical across both contexts.

---

## The Core Problem (Specific, Not Abstract)

A typical PHC OPD runs one doctor, 80–120 patients a day, 6 AM to 2 PM. The waiting room holds maybe 30 people. The overflow spills into the corridor, the compound, the road. A daily-wage labourer who loses half a workday waiting also loses ₹300–500 in income.

The problem isn't that there are too many patients. It's that patients have no signal about when to actually show up, so everyone shows up at once.

**Three things we fix:**
1. Patients don't know their position in the queue without being physically present
2. Staff have no visibility into how many people are waiting vs. how many have wandered off
3. There is no mechanism to notify patients when their turn is approaching

---

## Users

**Patient (primary)** — Likely owns a basic smartphone or shares one with a family member. May not speak English. May be semi-literate in their regional language. Is not going to install an app. Has WhatsApp.

**Front-desk staff (primary)** — One or two people. Manages the OPD register, hands out tokens, handles a hundred small interruptions simultaneously. Cannot babysit a complex dashboard. Needs something that basically runs itself.

**Doctor / MO (secondary)** — Wants to know how many patients are left. Should be able to mark a consultation done in one tap.

**PHC admin / CMHO (secondary)** — Wants aggregate throughput data. Not in scope for v1.

---

## What the System Does

### Token Issuance (the front desk)

A patient walks in. The front desk opens a browser tab (the tablet dashboard) and clicks **New Token**. The system:
- Assigns a token number (T-001, T-002, etc.)
- Asks for a mobile number (optional — if given, sends a WhatsApp confirmation)
- Displays the token number on screen for printing or manual handoff

That's it. No registration, no form, no login per patient.

### WhatsApp Check-in (for patients who gave a number)

Patient receives: *"Your token is T-014 at Latha Children's Clinic. Approx. wait: 55 min. We'll message you when 3 patients are ahead. Reply STATUS to check anytime."*

At any point, patient texts STATUS and gets: *"T-014 · 2 patients ahead · ~15 min. Please return to the OPD."*

When 3 patients are ahead: auto-notification fires.

### Doctor Console (a second browser tab, or same tablet)

Doctor or assistant clicks **Next Patient** after each consultation. This:
- Advances the queue counter
- Updates all live wait-time estimates
- Triggers the 3-ahead notifications for whoever is now in that position

### Wait Time Estimation

No ML needed. A rolling average of the last 10 consultation durations is enough. If the last 10 consultations averaged 6 minutes each, and there are 8 patients ahead of T-014, estimated wait = 48 min. Displayed with a ± buffer. This is communicated honestly as an estimate.

Edge case: if the doctor goes on a break (no "Next Patient" click for >15 min), the system flags this on the dashboard and stops sending time estimates until activity resumes.

### End-of-Day

Admin clicks **Close OPD**. Any un-served tokens get a message: *"OPD has closed. Please visit tomorrow morning."* Session resets for next day.

---

## What It Does NOT Do

- No appointment booking. Patients still walk in. We are not changing the access model, only the waiting experience.
- No patient health records. No integration with any hospital management system.
- No facial recognition, no cameras, no biometrics.
- No app install required for patients.
- No internet required for the doctor console or front desk (local network is enough). WhatsApp messages go out via cloud but queue logic works offline.

---

## Tech Stack

Chosen for: deployability by a non-DevOps team, minimal cost, works on cheap hardware.

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI (Python) | Simple, fast enough, easy to run on a Pi or a cheap VPS |
| Database | SQLite | No setup, no config, survives reboots, more than sufficient for 200 tokens/day |
| Frontend (dashboard) | Plain HTML + vanilla JS | Loads on a 2014 tablet over LAN. No build step, no Node.js |
| WhatsApp | Twilio WhatsApp API (sandbox for dev, paid for deploy) | Proven, documented, ₹0.8–1.2 per message |
| Hosting | Raspberry Pi 4 (local) or ₹500/mo VPS | Pi for full offline capability |
| Notifications | Twilio webhook + FastAPI route | Inbound "STATUS" messages handled server-side |

**Explicitly not using:** Redis, Celery, Docker (for v1), React, any ML model, Firebase.

---

## System Architecture

```
[Tablet — Front Desk]          [Tablet — Doctor]
  Browser → /dashboard    →     Browser → /doctor
         ↓                              ↓
              FastAPI Backend (local or VPS)
                      ↓
                  SQLite DB
                      ↓
              Twilio WhatsApp API
                      ↓
            Patient's WhatsApp
```

The front desk and doctor tabs poll the backend every 5 seconds for queue state. No websockets needed for v1.

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
| POST | `/api/session/close` | Close OPD, notify un-served tokens |
| POST | `/api/token` | Issue a new token (optional phone) |
| GET | `/api/token/{number}` | Get status of a specific token |
| GET | `/api/queue` | Full queue state for dashboards |
| POST | `/api/queue/next` | Doctor advances queue (closes current, calls next) |
| POST | `/api/whatsapp/webhook` | Inbound WhatsApp messages from Twilio |

---

## Screens

### Front Desk Dashboard (`/dashboard`)
- Large current queue count (e.g., **23 waiting**)
- "New Token" button — big, can't miss it
- Estimated wait for next token issued
- List of last 10 tokens with status
- Alert if doctor hasn't advanced queue in >15 min

### Doctor Console (`/doctor`)
- Current token being served (large, e.g., **NOW SERVING: T-008**)
- "Next Patient" button
- Count of remaining patients
- Today's average consultation time
- Today's served count

### Patient-Facing (WhatsApp only — no web app)
- Confirmation on token issue
- Status on demand (reply STATUS)
- 3-ahead notification
- OPD closure notification

---

## Offline / Degraded State Behaviour

| Scenario | What Happens |
|---|---|
| Internet down | Queue still works on local LAN. WhatsApp messages queue and send when connectivity returns. Dashboard shows "Offline — messages paused." |
| Power cut | Pi runs on UPS or mobile battery pack (~₹800 setup). SQLite survives power loss cleanly. |
| Twilio credit runs out | System works without WhatsApp. Patients use the physical token. Dashboard still functional. |
| Staff doesn't click Next Patient | Queue freezes. System shows a warning after 15 min of inactivity. No automated "fix" — a human resolves it. |
| Tablet dies | Any phone browser on the same LAN can open the dashboard. No state is in the browser. |

---

## Out of Scope for v1 (Explicitly)

- Appointment scheduling (pre-booking)
- Integration with Aarogya Setu, ABDM, or any national health stack
- Multi-department queues (separate queues for lab, pharmacy — that's v2)
- Analytics dashboard for CMHO / district
- IVR / voice call fallback for patients without WhatsApp

These are real needs. They are not in scope because they add complexity that breaks the ₹10,000 deployment ceiling and makes the system harder for untrained staff to run.

---

## Risks

**Twilio account suspended** — WhatsApp Business API requires a registered business. For a hackathon, the sandbox works. For real deployment, an NGO or hospital trust needs to register. Mitigation: document the registration path; the system works without WhatsApp.

**Staff don't click "Next Patient"** — This is the biggest operational risk. If the doctor doesn't advance the queue, all estimates go wrong. Mitigation: make the button very visible on the doctor's tablet; consider a gentle audio ping after 10 minutes of inactivity.

**Phone number not given** — Some patients won't give a number (or don't have one). System handles this: they get a paper token and the queue still advances correctly. WhatsApp is enhancement, not requirement.

**Wrong number entered** — Message goes to a stranger. Mitigation: front desk reads the number back before confirming; messages include the token number and PHC name so the wrong recipient knows immediately it's not for them.

---

## Definition of Done

The prototype is considered complete when:

- A front desk person who has never seen the system can issue 5 tokens in a row without help
- WhatsApp STATUS replies correctly from a real phone number
- "Next Patient" advances the queue and triggers notifications correctly
- The system recovers cleanly from a simulated internet outage (queue state preserved, messages resume)
- A 5-person usability session has been conducted and documented
- Wait time estimate is within ±15 minutes of actual wait for a simulated 20-patient queue
