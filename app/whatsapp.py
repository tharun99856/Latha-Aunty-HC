import os
from twilio.rest import Client


def _client():
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        return None
    return Client(sid, token)


def _send(phone, text):
    client = _client()
    if not client:
        return False

    from_num = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    to_num = f"whatsapp:+91{phone[-10:]}" if not phone.startswith("+") else f"whatsapp:{phone}"

    try:
        client.messages.create(body=text, from_=from_num, to=to_num)
        return True
    except Exception:
        return False


def send_token_issued(phone, token_number, phc_name, wait_minutes):
    return _send(phone, (
        f"Your token is {token_number} at {phc_name}. "
        f"Approx. wait: {wait_minutes} min. "
        f"We'll message you when 3 patients are ahead. "
        f"Reply STATUS to check anytime."
    ))


def send_approaching(phone, token_number, position):
    return _send(phone, (
        f"{token_number} · {position} patient{'s' if position != 1 else ''} ahead of you. "
        f"Please head to the OPD now."
    ))


def send_status(phone, token_number, status, position=0, wait_minutes=0):
    if status == "called":
        return _send(phone, f"{token_number} · It's your turn! Please come to the OPD now.")

    if status == "waiting":
        return _send(phone, (
            f"{token_number} · {position} patient{'s' if position != 1 else ''} ahead · ~{wait_minutes} min. "
            f"Please return to the OPD."
        ))

    if status == "served":
        return _send(phone, f"{token_number} · Your consultation is complete.")

    return False


def send_opd_closed(phone):
    return _send(phone, "OPD has closed for today. Please visit tomorrow morning.")
