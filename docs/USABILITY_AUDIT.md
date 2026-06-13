# Usability Audit — PHC Queue Management System

A 5-user audit testing whether the system actually works in the hands of real people. This document is both the **protocol** (how to run the audit) and the **report template** (where to record results).

> **Note for evaluators:** Audit participants are friends of the developer standing in as proxies for the four user roles. Each was briefed on their role context before testing. Real-PHC validation is planned post-hackathon.

---

## Participants (5 minimum)

| # | Role | Stand-in Profile |
|---|---|---|
| P1 | Patient — smartphone literate | Engineering student, WhatsApp daily user |
| P2 | Patient — limited literacy | Family member, uses WhatsApp only for forwards/voice notes |
| P3 | Front-desk staff | Friend with retail/customer-facing experience |
| P4 | Doctor / MO | Med student or family member in healthcare |
| P5 | ANM / helper | Anyone who has not used the system before |

---

## Tasks

Each participant attempts a fixed set of tasks. The facilitator observes silently and times completion. Hints are recorded but not given unless the participant is stuck for >60 seconds.

### P1, P2 — Patient tasks
1. Receive token confirmation message on WhatsApp. Read out what your token number is and your estimated wait.
2. Reply STATUS to check your position.
3. When you receive the "3 ahead" notification, explain in your own words what you should do.

### P3 — Front-desk tasks
1. Open the OPD for the day.
2. Issue 5 tokens — 3 with phone numbers, 2 without.
3. Identify how many patients are currently waiting.
4. Identify whether the doctor is active.

### P4 — Doctor tasks
1. Call the next patient.
2. Determine how many patients are remaining.
3. Identify the average consultation time so far.

### P5 — Cold start
1. Without prior training, figure out how to issue a token.
2. Without prior training, figure out how to advance the queue.

---

## Scoring Rubric

Each task is scored on three dimensions:

| Dimension | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **Ease** | Could not complete | Completed with hints | Completed with hesitation | Completed comfortably | Completed instantly |
| **Speed** | >2 min | 1–2 min | 30–60 sec | 10–30 sec | <10 sec |
| **Confidence** | Confused throughout | Unsure of outcome | Mostly sure | Confident | Certain |

A task is **"positive"** if the average across the three dimensions is ≥ 3.5.

A participant is **"satisfied"** if ≥ 75% of their tasks are positive.

---

## Results Template

> Fill this in after running the audit. Each row is one participant × one task.

| Participant | Task | Ease | Speed | Confidence | Avg | Notes |
|---|---|---|---|---|---|---|
| P1 | Read token confirmation | _ | _ | _ | _ | |
| P1 | Reply STATUS | _ | _ | _ | _ | |
| P1 | Interpret 3-ahead alert | _ | _ | _ | _ | |
| P2 | Read token confirmation | _ | _ | _ | _ | |
| P2 | Reply STATUS | _ | _ | _ | _ | |
| P2 | Interpret 3-ahead alert | _ | _ | _ | _ | |
| P3 | Open OPD | _ | _ | _ | _ | |
| P3 | Issue 5 tokens | _ | _ | _ | _ | |
| P3 | Identify queue count | _ | _ | _ | _ | |
| P3 | Check doctor activity | _ | _ | _ | _ | |
| P4 | Call next patient | _ | _ | _ | _ | |
| P4 | Read remaining count | _ | _ | _ | _ | |
| P4 | Read avg consult time | _ | _ | _ | _ | |
| P5 | Issue a token, no help | _ | _ | _ | _ | |
| P5 | Advance queue, no help | _ | _ | _ | _ | |

---

## Per-Participant Summary

| Participant | Tasks attempted | Tasks positive | Satisfied? | Quote |
|---|---|---|---|---|
| P1 | 3 | _ | _ | |
| P2 | 3 | _ | _ | |
| P3 | 4 | _ | _ | |
| P4 | 3 | _ | _ | |
| P5 | 2 | _ | _ | |

**Overall satisfaction rate:** _ / 5 = _%

**Target:** ≥ 80% (i.e., ≥ 4 of 5 satisfied)

---

## Observed Issues (to fix in v1.1)

Record any usability issues observed during the audit. These should not be invented — leave blank if none were found in a given category.

### Critical (blocks task completion)
- _

### Major (causes hesitation, repeated mistakes)
- _

### Minor (cosmetic, polish)
- _

---

## What We're NOT Auditing in This Round

- WhatsApp Business API approval flow (sandbox is fine for the audit)
- Telugu/Hindi message rendering on actual Indian Android phones in the field
- Multi-day session behaviour (we test one OPD session per participant)
- Concurrent front-desk + doctor usage from the same tablet
- Long-running stability (>4 hour sessions)

These are scoped for the PHC pilot phase, post-hackathon.

---

## Audit Logistics

- **Where:** Quiet room with WiFi, one tablet for front-desk, one tablet/laptop for doctor, one phone per patient stand-in
- **How long per participant:** 10–15 minutes (5 min context briefing + tasks + 2 min debrief)
- **Total time:** ~90 minutes for 5 participants
- **Facilitator:** developer (records observations, does not intervene)
- **Recording:** notes only — no video unless participant consents
