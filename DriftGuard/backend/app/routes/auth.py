"""Authentication endpoint for DriftGuard dashboard login."""

import hashlib
import hmac
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(req: LoginRequest):
    user_ok = hmac.compare_digest(req.username.strip(), settings.admin_user)
    pass_ok = hmac.compare_digest(req.password, settings.admin_password)
    if not (user_ok and pass_ok):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = hashlib.sha256(f"{settings.admin_user}:{settings.admin_password}".encode("utf-8")).hexdigest()
    return {
        "token": token,
        "username": settings.admin_user,
        "role": "MLOps Engineer",
    }
