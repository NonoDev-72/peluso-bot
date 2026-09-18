import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from shared.config import settings
from shared.database import SessionLocal, User
from web.discord_oauth import build_authorize_url, exchange_code, fetch_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    request.session["oauth_state"] = state
    return RedirectResponse(build_authorize_url(state))


@router.get("/callback")
async def callback(request: Request, code: str, state: str) -> RedirectResponse:
    expected_state = request.session.pop("oauth_state", None)
    if not expected_state or state != expected_state:
        raise HTTPException(status_code=400, detail="Estado OAuth invalido")

    token_data = await exchange_code(code)
    discord_user = await fetch_user(token_data["access_token"])

    with SessionLocal() as session:
        user = session.get(User, int(discord_user["id"]))
        if user is None:
            user = User(discord_id=int(discord_user["id"]))
            session.add(user)

        user.username = f"{discord_user['username']}#{discord_user.get('discriminator', '0')}"
        user.avatar_hash = discord_user.get("avatar")
        user.access_token = token_data["access_token"]
        user.refresh_token = token_data["refresh_token"]
        user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        session.commit()

    request.session["discord_id"] = int(discord_user["id"])
    return RedirectResponse(f"{settings.web_base_path}/dashboard")


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(f"{settings.web_base_path}/")
