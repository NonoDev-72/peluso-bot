import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from shared.config import settings
from shared.database import (
    GuildConfig,
    SessionLocal,
    create_voice_room_trigger,
    delete_voice_room_trigger,
    get_or_create_guild_config,
    get_voice_room_trigger_by_channel,
    list_voice_room_triggers,
)
from web.auth import get_current_user
from web.discord_oauth import fetch_guild_roles, fetch_guild_voice_channels, fetch_manageable_guilds

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

    try:
        roles = await fetch_guild_roles(guild_id)
        roles_error = None
    except httpx.HTTPStatusError:
        roles = []
        roles_error = "No se pudieron cargar los roles: el bot no está en este servidor o le faltan permisos."

    try:
        voice_channels = await fetch_guild_voice_channels(guild_id)
        voice_channels_error = None
    except httpx.HTTPStatusError:
        voice_channels = []
        voice_channels_error = "No se pudieron cargar los canales de voz: el bot no está en este servidor o le faltan permisos."

    with SessionLocal() as session:
        voice_room_triggers = list_voice_room_triggers(session, guild_id)
        session.expunge_all()

    voice_channel_names = {int(c["id"]): c["name"] for c in voice_channels}

    return templates.TemplateResponse(
        request,
        "guild_settings.html",
        {
            "user": user,
            "config": config,
            "roles": roles,
            "roles_error": roles_error,
            "voice_channels": voice_channels,
            "voice_channels_error": voice_channels_error,
            "voice_room_triggers": voice_room_triggers,
            "voice_channel_names": voice_channel_names,
        },
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
    default_role_id: str = Form(""),
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
        config.default_role_id = int(default_role_id) if default_role_id else None
        session.commit()

    return RedirectResponse(f"{settings.web_base_path}/dashboard/{guild_id}", status_code=303)


@router.post("/{guild_id}/voice-rooms")
async def create_voice_room(
    request: Request,
    guild_id: int,
    user=Depends(get_current_user),
    trigger_channel_id: str = Form(...),
    name_template: str = Form("Sala {n}"),
):
    guilds = await fetch_manageable_guilds(user.access_token)
    if not any(int(g["id"]) == guild_id for g in guilds):
        raise HTTPException(status_code=403, detail="No tenes permisos sobre ese servidor")

    channel_id = int(trigger_channel_id)
    template = name_template.strip() or "Sala {n}"

    with SessionLocal() as session:
        existing = get_voice_room_trigger_by_channel(session, guild_id, channel_id)
        if existing is None:
            create_voice_room_trigger(session, guild_id, channel_id, template)

    return RedirectResponse(f"{settings.web_base_path}/dashboard/{guild_id}", status_code=303)


@router.post("/{guild_id}/voice-rooms/{trigger_id}/delete")
async def delete_voice_room(
    request: Request,
    guild_id: int,
    trigger_id: int,
    user=Depends(get_current_user),
):
    guilds = await fetch_manageable_guilds(user.access_token)
    if not any(int(g["id"]) == guild_id for g in guilds):
        raise HTTPException(status_code=403, detail="No tenes permisos sobre ese servidor")

    with SessionLocal() as session:
        delete_voice_room_trigger(session, guild_id, trigger_id)

    return RedirectResponse(f"{settings.web_base_path}/dashboard/{guild_id}", status_code=303)
