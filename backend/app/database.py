
import asyncio
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USERS = [
    {"id": 1, "username": "admin", "password_hash": pwd_context.hash("core1234")},
    {"id": 2, "username": "debugger_neo", "password_hash": pwd_context.hash("redpill")},
]

MODULES = [
    {"id": i, "name": f"Core-Module-{i}", "status": "unstable" if i % 3 == 0 else "stable", "owner_id": 1}
    for i in range(1, 26)
]

# Simulates network/db latency
async def fake_io_delay(seconds: float = 0.05):
    await asyncio.sleep(seconds)


def get_user_by_username(username: str):
    for u in USERS:
        if u["username"] == username:
            return u
    return None


def get_modules_for_owner(owner_id: int):
    """Used to demonstrate an N+1 query pattern in main.py on purpose."""
    return [m for m in MODULES if m["owner_id"] == owner_id]


async def fetch_module_report(module_id: int):
    await fake_io_delay(0.05)
    module = next((m for m in MODULES if m["id"] == module_id), None)
    if module is None:
        return {"error": "not found"}
    return {"name": module["name"], "status": module["status"], "generated": True}
