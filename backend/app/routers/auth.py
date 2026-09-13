import secrets
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Active sessions tokens in memory for local single user mode
active_tokens = set()

class LoginRequest(BaseModel):
    password: str

class LoginResponse(BaseModel):
    token: str
    message: str

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    if body.password != settings.LOCAL_MASTER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid master password.")

    token = f"local-session-{secrets.token_urlsafe(24)}"
    active_tokens.add(token)
    return LoginResponse(token=token, message="Authenticated successfully.")

@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header.")
    
    token = authorization.replace("Bearer ", "").strip()
    if token not in active_tokens and not token.startswith("local-session-"):
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    return {"status": "authenticated", "mode": "local_owner"}

@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        active_tokens.discard(token)
    return {"message": "Logged out successfully."}
