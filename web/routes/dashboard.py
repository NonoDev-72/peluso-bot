import os
import tempfile
import uuid

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from PIL import Image

from bot.welcome_card import DEFAULT_FONT_KEY, FONT_CHOICES, build_welcome_card
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

ALLOWED_BACKGROUND_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


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
            "font_choices": FONT_CHOICES,
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
    welcome_background: UploadFile | None = File(None),
    remove_welcome_background: bool = Form(False),
    welcome_font: str = Form(DEFAULT_FONT_KEY),
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
        config.welcome_font = welcome_font if welcome_font in FONT_CHOICES else DEFAULT_FONT_KEY
        config.goodbye_enabled = goodbye_enabled
        config.goodbye_channel_id = int(goodbye_channel_id) if goodbye_channel_id else None
        config.goodbye_message = goodbye_message
        config.default_role_id = int(default_role_id) if default_role_id else None

        if remove_welcome_background:
            _delete_background_file(config.welcome_background_path)
            config.welcome_background_path = None
        elif welcome_background is not None and welcome_background.filename:
            extension = ALLOWED_BACKGROUND_TYPES.get(welcome_background.content_type)
            if extension is None:
                raise HTTPException(status_code=400, detail="La imagen de fondo debe ser PNG, JPEG o WEBP")
            _delete_background_file(config.welcome_background_path)
            config.welcome_background_path = _save_background_file(guild_id, welcome_background, extension)

        session.commit()

    return RedirectResponse(f"{settings.web_base_path}/dashboard/{guild_id}", status_code=303)


def _save_background_file(guild_id: int, upload: UploadFile, extension: str) -> str:
    os.makedirs(settings.uploads_dir, exist_ok=True)
    filename = f"welcome_bg_{guild_id}_{uuid.uuid4().hex}{extension}"
    path = os.path.join(settings.uploads_dir, filename)
    with open(path, "wb") as out_file:
        out_file.write(upload.file.read())
    return path


def _delete_background_file(path: str | None) -> None:
    if path and os.path.isfile(path):
        os.remove(path)


@router.get("/{guild_id}/welcome-background")
async def get_welcome_background(guild_id: int, user=Depends(get_current_user)):
    guilds = await fetch_manageable_guilds(user.access_token)
    if not any(int(g["id"]) == guild_id for g in guilds):
        raise HTTPException(status_code=403, detail="No tenes permisos sobre ese servidor")

    with SessionLocal() as session:
        config = get_or_create_guild_config(session, guild_id)
        path = config.welcome_background_path

    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="No hay imagen de fondo configurada")

    return FileResponse(path)


@router.get("/{guild_id}/welcome-preview")
async def welcome_preview(
    guild_id: int,
    user=Depends(get_current_user),
    font: str = DEFAULT_FONT_KEY,
    message: str = "",
):
    guilds = await fetch_manageable_guilds(user.access_token)
    if not any(int(g["id"]) == guild_id for g in guilds):
        raise HTTPException(status_code=403, detail="No tenes permisos sobre ese servidor")

    with SessionLocal() as session:
        config = get_or_create_guild_config(session, guild_id)
        background_path = config.welcome_background_path
        guild_name = config.guild_name

    font_key = font if font in FONT_CHOICES else DEFAULT_FONT_KEY
    template_text = message.strip() or "¡Bienvenido/a {member} a **{guild}**! Ya somos {member_count}."
    try:
        preview_text = template_text.format(member=user.username, guild=guild_name or "tu servidor", member_count=100)
    except (KeyError, IndexError, ValueError):
        preview_text = template_text

    avatar_url = (
        f"https://cdn.discordapp.com/avatars/{user.discord_id}/{user.avatar_hash}.png?size=256"
        if user.avatar_hash
        else "https://cdn.discordapp.com/embed/avatars/0.png"
    )
    async with httpx.AsyncClient() as client:
        avatar_response = await client.get(avatar_url)
        avatar_bytes = avatar_response.content

    temp_bg_path = None
    bg_path = background_path if background_path and os.path.isfile(background_path) else None
    if bg_path is None:
        temp_bg_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
        Image.new("RGB", (960, 540), (35, 35, 60)).save(temp_bg_path)
        bg_path = temp_bg_path

    try:
        buffer = build_welcome_card(bg_path, avatar_bytes, preview_text, font_key)
    finally:
        if temp_bg_path:
            os.unlink(temp_bg_path)

    return Response(content=buffer.getvalue(), media_type="image/png")


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
