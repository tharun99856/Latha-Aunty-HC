from datetime import datetime, date
from app.database import get_db


def open_session():
    db = get_db()
    try:
        today = date.today().isoformat()
        db.execute(
            "UPDATE sessions SET is_active = 0, closed_at = ? WHERE is_active = 1 AND date != ?",
            (datetime.now().isoformat(), today),
        )
        existing = db.execute(
            "SELECT * FROM sessions WHERE is_active = 1 AND date = ?", (today,)
        ).fetchone()
        if existing:
            db.commit()
            return dict(existing)

        now = datetime.now().isoformat()
        cur = db.execute(
            "INSERT INTO sessions (date, opened_at) VALUES (?, ?)", (today, now)
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM sessions WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        db.close()


def close_session():
    db = get_db()
    try:
        session = db.execute(
            "SELECT id FROM sessions WHERE is_active = 1"
        ).fetchone()
        if not session:
            return None

        now = datetime.now().isoformat()
        db.execute(
            "UPDATE sessions SET is_active = 0, closed_at = ? WHERE id = ?",
            (now, session["id"]),
        )
        db.execute(
            "UPDATE tokens SET status = 'no-show' WHERE session_id = ? AND status IN ('waiting', 'called')",
            (session["id"],),
        )
        db.commit()

        rows = db.execute(
            "SELECT phone FROM tokens WHERE session_id = ? AND status = 'no-show' AND phone IS NOT NULL",
            (session["id"],),
        ).fetchall()
        return [r["phone"] for r in rows]
    finally:
        db.close()


def issue_token(phone=None):
    db = get_db()
    try:
        session = db.execute(
            "SELECT * FROM sessions WHERE is_active = 1"
        ).fetchone()
        if not session:
            return None

        count = db.execute(
            "SELECT COUNT(*) as c FROM tokens WHERE session_id = ?",
            (session["id"],),
        ).fetchone()["c"]

        token_number = f"T-{count + 1:03d}"
        now = datetime.now().isoformat()

        cur = db.execute(
            "INSERT INTO tokens (session_id, number, phone, issued_at) VALUES (?, ?, ?, ?)",
            (session["id"], token_number, phone, now),
        )
        db.execute(
            "UPDATE sessions SET total_issued = total_issued + 1 WHERE id = ?",
            (session["id"],),
        )
        db.commit()

        token = dict(
            db.execute("SELECT * FROM tokens WHERE id = ?", (cur.lastrowid,)).fetchone()
        )
        token["position"] = _position(db, session["id"], token["id"])
        token["estimated_wait"] = _wait_estimate(db, session["id"], token["position"])
        return token
    finally:
        db.close()


def call_next():
    db = get_db()
    try:
        session = db.execute(
            "SELECT * FROM sessions WHERE is_active = 1"
        ).fetchone()
        if not session:
            return None

        now = datetime.now()
        current = db.execute(
            "SELECT * FROM tokens WHERE session_id = ? AND status = 'called' ORDER BY called_at ASC LIMIT 1",
            (session["id"],),
        ).fetchone()

        if current:
            called_at = datetime.fromisoformat(current["called_at"])
            duration = max(1, int((now - called_at).total_seconds()))
            db.execute(
                "UPDATE tokens SET status = 'served', served_at = ? WHERE id = ?",
                (now.isoformat(), current["id"]),
            )
            db.execute(
                "INSERT INTO consultations (session_id, token_id, duration_seconds, completed_at) VALUES (?, ?, ?, ?)",
                (session["id"], current["id"], duration, now.isoformat()),
            )
            db.execute(
                "UPDATE sessions SET total_served = total_served + 1 WHERE id = ?",
                (session["id"],),
            )

        next_token = db.execute(
            "SELECT * FROM tokens WHERE session_id = ? AND status = 'waiting' ORDER BY id ASC LIMIT 1",
            (session["id"],),
        ).fetchone()

        if not next_token:
            db.commit()
            return {"empty": True}

        db.execute(
            "UPDATE tokens SET status = 'called', called_at = ? WHERE id = ?",
            (now.isoformat(), next_token["id"]),
        )
        db.commit()

        result = dict(
            db.execute("SELECT * FROM tokens WHERE id = ?", (next_token["id"],)).fetchone()
        )
        result["notify"] = _collect_notifications(db, session["id"])
        return result
    finally:
        db.close()


def get_queue_state():
    db = get_db()
    try:
        session = db.execute(
            "SELECT * FROM sessions WHERE is_active = 1"
        ).fetchone()
        if not session:
            return None

        sid = session["id"]

        waiting = db.execute(
            "SELECT COUNT(*) as c FROM tokens WHERE session_id = ? AND status = 'waiting'",
            (sid,),
        ).fetchone()["c"]

        current = db.execute(
            "SELECT * FROM tokens WHERE session_id = ? AND status = 'called' ORDER BY called_at DESC LIMIT 1",
            (sid,),
        ).fetchone()

        recent = db.execute(
            "SELECT * FROM tokens WHERE session_id = ? ORDER BY id DESC LIMIT 10",
            (sid,),
        ).fetchall()

        avg = _avg_duration(db, sid)
        wait_min = round(avg * waiting / 60) if avg and waiting else 0

        last_called = db.execute(
            "SELECT MAX(called_at) as t FROM tokens WHERE session_id = ? AND status IN ('called','served')",
            (sid,),
        ).fetchone()["t"]

        doctor_inactive = False
        if last_called and waiting > 0:
            elapsed = (datetime.now() - datetime.fromisoformat(last_called)).total_seconds()
            doctor_inactive = elapsed > 900

        return {
            "session": dict(session),
            "waiting": waiting,
            "current_token": dict(current) if current else None,
            "recent_tokens": [dict(r) for r in recent],
            "avg_duration_seconds": avg,
            "estimated_wait_minutes": wait_min,
            "doctor_inactive": doctor_inactive,
            "last_activity": last_called,
        }
    finally:
        db.close()


def check_token_status(number):
    db = get_db()
    try:
        session = db.execute(
            "SELECT id FROM sessions WHERE is_active = 1"
        ).fetchone()
        if not session:
            return None

        token = db.execute(
            "SELECT * FROM tokens WHERE session_id = ? AND number = ?",
            (session["id"], number.upper()),
        ).fetchone()
        if not token:
            return None

        result = dict(token)
        if result["status"] == "waiting":
            result["position"] = _position(db, session["id"], result["id"])
            result["estimated_wait"] = _wait_estimate(db, session["id"], result["position"])
        return result
    finally:
        db.close()


def check_token_by_phone(phone):
    db = get_db()
    try:
        session = db.execute(
            "SELECT id FROM sessions WHERE is_active = 1"
        ).fetchone()
        if not session:
            return None

        suffix = phone[-10:] if len(phone) >= 10 else phone
        token = db.execute(
            "SELECT * FROM tokens WHERE session_id = ? AND phone LIKE ? AND status IN ('waiting','called') ORDER BY id DESC LIMIT 1",
            (session["id"], f"%{suffix}"),
        ).fetchone()
        if not token:
            return None

        result = dict(token)
        if result["status"] == "waiting":
            result["position"] = _position(db, session["id"], result["id"])
            result["estimated_wait"] = _wait_estimate(db, session["id"], result["position"])
        return result
    finally:
        db.close()


def _position(db, session_id, token_id):
    return db.execute(
        "SELECT COUNT(*) as c FROM tokens WHERE session_id = ? AND status = 'waiting' AND id < ?",
        (session_id, token_id),
    ).fetchone()["c"]


def _avg_duration(db, session_id):
    row = db.execute(
        "SELECT AVG(duration_seconds) as v FROM (SELECT duration_seconds FROM consultations WHERE session_id = ? ORDER BY id DESC LIMIT 10)",
        (session_id,),
    ).fetchone()
    return round(row["v"]) if row["v"] else None


def _wait_estimate(db, session_id, position):
    avg = _avg_duration(db, session_id)
    if not avg:
        avg = 360
    return round(avg * position / 60)


def _collect_notifications(db, session_id):
    candidates = db.execute(
        "SELECT * FROM tokens WHERE session_id = ? AND status = 'waiting' AND phone IS NOT NULL AND notified_3ahead = 0 ORDER BY id ASC",
        (session_id,),
    ).fetchall()

    targets = []
    for tok in candidates:
        pos = db.execute(
            "SELECT COUNT(*) as c FROM tokens WHERE session_id = ? AND status = 'waiting' AND id < ?",
            (session_id, tok["id"]),
        ).fetchone()["c"]
        if pos <= 3:
            db.execute("UPDATE tokens SET notified_3ahead = 1 WHERE id = ?", (tok["id"],))
            targets.append({"phone": tok["phone"], "number": tok["number"], "position": pos})

    db.commit()
    return targets
