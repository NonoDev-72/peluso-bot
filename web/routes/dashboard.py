from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from shared.config import settings
from shared.database import GuildConfig, SessionLocal, get_or_create_guild_config
from web.auth import get_current_user
from web.discord_oauth import fetch_manageable_guilds

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="web/templates")


@router.get("")
async def list_guilds(request: Request, user=Depends(get_current_user)):
    guilds = await fetch_manageable_guilds(user.access_token)
    return templates.TemplateResponse(
        request, "dashboard.html", {"user": user, "guilds": guilds}
    )


@router.get("/{guild_id}")
async def edit_guild(request: Request, guild_id: int, user=Depends(get_current_user)):
    guilds = await fetch_manageable_guilds(user.access_token)
    if not any(int(g["id"]) == guild_id for g in guilds):
        raise HTTPException(status_code=403, detail="No tenes permisos sobre ese servidor")

    with SessionLocal() as session:
        config = get_or_create_guild_config(session, guild_id)
        session.expunge(config)

    return templates.TemplateResponse(
        request, "guild_settings.html", {"user": user, "config": config}
    )


@router.post("/{guild_id}")
async def update_guild(
    request: Request,
    guild_id: int,
    user=Depends(get_current_user),
    welcome_enabled: bool = Form(False),
    welcome_channel_id: str = Form(""),
    welcome_message: str = Form(...),
    goodbye_enabled: bool = Form(False),
    goodbye_channel_id: str = Form(""),
    goodbye_message: str = Form(...),
):
    guilds = await fetch_manageable_guilds(user.access_token)
    if not any(int(g["id"]) == guild_id for g in guilds):
        raise HTTPException(status_code=403, detail="No tenes permisos sobre ese servidor")

    with SessionLocal() as session:
        config: GuildConfig = get_or_create_guild_config(session, guild_id)
        config.welcome_enabled = welcome_enabled
        config.welcome_channel_id = int(welcome_channel_id) if welcome_channel_id else None
        config.welcome_message = welcome_message
        config.goodbye_enabled = goodbye_enabled
        config.goodbye_channel_id = int(goodbye_channel_id) if goodbye_channel_id else None
        config.goodbye_message = goodbye_message
        session.commit()

    return RedirectResponse(f"{settings.web_base_path}/dashboard/{guild_id}", status_code=303)
