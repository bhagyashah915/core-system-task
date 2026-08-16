import asyncio
import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext

from . import database
from . import auth

app = FastAPI(title="CodeVerse Core System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

CORE_API_KEY = os.environ.get("CORE_SYSTEM_APIKEY")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.get("/health")
def health():
    return {"status": "Core System responding", "api_key_loaded": bool(CORE_API_KEY)}


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user = database.get_user_by_username(payload.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token({"sub": user["username"], "uid": user["id"]})
    return LoginResponse(access_token=token)


def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ")[1]
    payload = auth.decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def log_request(event: str, log: list | None = None):
    if log is None:
        log = []
    log.append(event)
    return log


@app.get("/modules")
def list_modules(owner_id: int = 1, page: int = 1, page_size: int = 10):
    log_request(f"list_modules called for owner={owner_id}")

    all_modules = database.get_modules_for_owner(owner_id)

    start = (page - 1) * page_size
    end = start + page_size
    paged = all_modules[start:end]

    return {"page": page, "total": len(all_modules), "modules": paged}


@app.get("/modules/detailed")
async def list_modules_detailed(owner_id: int = 1):
    modules = database.get_modules_for_owner(owner_id)

    async def enrich(m):
        await database.fake_io_delay(0.05)
        return {**m, "status_detail": f"{m['status']}-verified"}

    detailed = await asyncio.gather(*[enrich(m) for m in modules])
    return {"modules": detailed}


core_stability_score = 100
_stability_lock = asyncio.Lock()


@app.post("/core/stabilize")
async def stabilize_core():
    global core_stability_score
    async with _stability_lock:
        current = core_stability_score
        await database.fake_io_delay(0.02)
        core_stability_score = current - 1
        await database.fake_io_delay(0.02)
        core_stability_score += 2
    return {"core_stability_score": core_stability_score}


@app.get("/core/status")
def core_status():
    return {"core_stability_score": core_stability_score}


@app.get("/modules/{module_id}/report")
async def module_report(module_id: int):

    report = database.fetch_module_report(module_id)
    return {"module_id": module_id, "report": report}


@app.get("/modules/search")
def search_modules(query: str):

    matches = [m for m in database.MODULES if query.lower() in m["name"].lower()]
    return {"matches": matches}
