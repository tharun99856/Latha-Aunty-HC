import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from app.database import init_db
from app import queue

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
    result = queue.close_session()
    if result is None:
        return JSONResponse({"error": "No active session"}, status_code=400)
    return {"closed": True, "no_show_count": len(result)}


class TokenRequest(BaseModel):
    phone: str | None = None


@app.post("/api/token")
async def create_token(body: TokenRequest):
    token = queue.issue_token(body.phone)
    if not token:
        return JSONResponse({"error": "No active session"}, status_code=400)
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
    return result


@app.get("/api/queue")
async def queue_state():
    state = queue.get_queue_state()
    if not state:
        return {"active": False}
    state["active"] = True
    return state
