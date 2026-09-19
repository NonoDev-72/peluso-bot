import time
from urllib.parse import urlencode

import httpx

from shared.config import settings

API_BASE = "https://discord.com/api/v10"
AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = f"{API_BASE}/oauth2/token"

SCOPES = "identify guilds"

# Permiso "Manage Server" requerido para administrar la config de un guild desde el panel
MANAGE_GUILD_PERMISSION = 0x20

# Permisos que necesita el bot para sus features (ver bot/cogs/*.py): ver canales, enviar mensajes,
# adjuntar/incrustar la tarjeta de bienvenida, gestionar roles (rol automatico), gestionar canales y
# mover miembros (salas de voz temporales).
BOT_INVITE_PERMISSIONS = (
    0x400  # View Channels
    | 0x800  # Send Messages
    | 0x8000  # Attach Files
    | 0x4000  # Embed Links
    | 0x10  # Manage Channels
    | 0x1000000  # Move Members
    | 0x10000000  # Manage Roles
)


def build_bot_invite_url(guild_id: int) -> str:
    params = {
        "client_id": settings.discord_client_id,
        "permissions": BOT_INVITE_PERMISSIONS,
        "scope": "bot",
        "guild_id": guild_id,
        "disable_guild_select": "true",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"

# /users/@me/guilds tiene un rate limit mas agresivo que el resto de la API de Discord.
# El preview de la tarjeta de bienvenida la consulta en cada cambio de fuente/texto, así que
# el cache dura más que en el resto del panel para no comerse el rate limit con ese uso repetido.
GUILDS_CACHE_TTL_SECONDS = 120
_guilds_cache: dict[str, tuple[float, list[dict]]] = {}


def build_authorize_url(state: str) -> str:
    params = {
        "client_id": settings.discord_client_id,
        "redirect_uri": settings.discord_redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
        "prompt": "consent",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    data = {
        "client_id": settings.discord_client_id,
        "client_secret": settings.discord_client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.discord_redirect_uri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, data=data, headers=headers)
        response.raise_for_status()
        return response.json()


async def fetch_user(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/users/@me", headers=headers)
        response.raise_for_status()
        return response.json()


async def fetch_manageable_guilds(access_token: str) -> list[dict]:
    """Guilds donde el usuario tiene permiso de administrar el servidor."""
    cached = _guilds_cache.get(access_token)
    if cached and time.monotonic() - cached[0] < GUILDS_CACHE_TTL_SECONDS:
        return cached[1]

    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/users/@me/guilds", headers=headers)
        response.raise_for_status()
        guilds = response.json()

    manageable = [
        guild
        for guild in guilds
        if guild.get("owner") or (int(guild.get("permissions", 0)) & MANAGE_GUILD_PERMISSION)
    ]
    _guilds_cache[access_token] = (time.monotonic(), manageable)
    return manageable


async def is_bot_in_guild(guild_id: int) -> bool:
    """Chequea con el token del bot si esta en el guild (403/404 = no es miembro)."""
    headers = {"Authorization": f"Bot {settings.discord_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/guilds/{guild_id}", headers=headers)
    if response.status_code in (403, 404):
        return False
    response.raise_for_status()
    return True


async def fetch_guild_roles(guild_id: int) -> list[dict]:
    """Roles asignables del servidor, consultados con el token del bot (no del usuario)."""
    headers = {"Authorization": f"Bot {settings.discord_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/guilds/{guild_id}/roles", headers=headers)
        response.raise_for_status()
        roles = response.json()

    assignable = [role for role in roles if role["id"] != str(guild_id) and not role.get("managed")]
    return sorted(assignable, key=lambda r: r["position"], reverse=True)


# Tipo de canal 2 = GUILD_VOICE (https://discord.com/developers/docs/resources/channel#channel-object-channel-types)
GUILD_VOICE_CHANNEL_TYPE = 2


async def fetch_guild_voice_channels(guild_id: int) -> list[dict]:
    """Canales de voz del servidor, consultados con el token del bot."""
    headers = {"Authorization": f"Bot {settings.discord_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/guilds/{guild_id}/channels", headers=headers)
        response.raise_for_status()
        channels = response.json()

    voice_channels = [channel for channel in channels if channel.get("type") == GUILD_VOICE_CHANNEL_TYPE]
    return sorted(voice_channels, key=lambda c: c["position"])
