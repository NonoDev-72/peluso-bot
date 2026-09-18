from urllib.parse import urlencode

import httpx

from shared.config import settings

API_BASE = "https://discord.com/api/v10"
AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = f"{API_BASE}/oauth2/token"

SCOPES = "identify guilds"

# Permiso "Manage Server" requerido para administrar la config de un guild desde el panel
MANAGE_GUILD_PERMISSION = 0x20


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
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/users/@me/guilds", headers=headers)
        response.raise_for_status()
        guilds = response.json()

    return [
        guild
        for guild in guilds
        if guild.get("owner") or (int(guild.get("permissions", 0)) & MANAGE_GUILD_PERMISSION)
    ]
