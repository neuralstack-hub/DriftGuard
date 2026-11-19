"""Username/password authentication and bearer-session management."""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Auth"])
auth_service = AuthService()


def require_user(authorization: str | None = Header(default=None)):
    if not settings.authentication_enabled:
        return {"username": "local-developer", "role": "Developer"}
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    session = auth_service.get_session(authorization[7:].strip())
    if not session:
        raise HTTPException(status_code=401, detail="Your session expired. Please sign in again.")
    return session


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(req: LoginRequest):
    try:
        return auth_service.authenticate(req.username, req.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    if authorization and authorization.startswith("Bearer "):
        auth_service.revoke_session(authorization[7:].strip())
    return {"status": "signed_out"}
