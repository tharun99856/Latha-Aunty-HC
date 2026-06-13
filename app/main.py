import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from app.database import init_db
from app import queue, whatsapp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
PHC_NAME = os.getenv("PHC_NAME", "Latha Children's Clinic")


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="PHC Queue", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
@app.get("/dashboard")
async def dashboard():
    return FileResponse(os.path.join(STATIC_DIR, "dashboard.html"))


@app.get("/doctor")
async def doctor():
    return FileResponse(os.path.join(STATIC_DIR, "doctor.html"))


@app.post("/api/session/open")
async def open_session():
    return queue.open_session()


@app.post("/api/session/close")
async def close_session():
    phones = queue.close_session()
    if phones is None:
        return JSONResponse({"error": "No active session"}, status_code=400)
    for phone in phones:
        whatsapp.send_opd_closed(phone)
    return {"closed": True, "notified": len(phones)}


class TokenRequest(BaseModel):
    phone: str | None = None


@app.post("/api/token")
async def create_token(body: TokenRequest):
    token = queue.issue_token(body.phone)
    if not token:
        return JSONResponse({"error": "No active session"}, status_code=400)

    if token.get("phone"):
        whatsapp.send_token_issued(
            token["phone"], token["number"], PHC_NAME,
            token.get("estimated_wait", 0),
        )

    return token


@app.get("/api/token/{number}")
async def token_status(number: str):
    token = queue.check_token_status(number)
    if not token:
        return JSONResponse({"error": "Token not found"}, status_code=404)
    return token


@app.post("/api/queue/next")
async def next_patient():
    result = queue.call_next()
    if not result:
        return JSONResponse({"error": "No active session"}, status_code=400)

    for target in result.get("notify", []):
        whatsapp.send_approaching(target["phone"], target["number"], target["position"])

    return result


@app.get("/api/queue")
async def queue_state():
    state = queue.get_queue_state()
    if not state:
        return {"active": False}
    state["active"] = True
    return state


@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    body_text = form.get("Body", "").strip().upper()
    from_number = form.get("From", "").replace("whatsapp:", "")

    if body_text == "STATUS" and from_number:
        token = queue.check_token_by_phone(from_number)
        if token:
            whatsapp.send_status(
                token["phone"], token["number"], token["status"],
                token.get("position", 0), token.get("estimated_wait", 0),
            )

    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )
