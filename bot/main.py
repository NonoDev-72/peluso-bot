import asyncio
import logging

import discord
from discord.ext import commands

from shared.config import settings
from shared.database import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("peluso")

INITIAL_COGS = (
    "bot.cogs.general",
    "bot.cogs.welcome",
    "bot.cogs.voice_rooms",
)


class PelusoBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        for extension in INITIAL_COGS:
            await self.load_extension(extension)
        await self.tree.sync()

    async def on_ready(self) -> None:
        log.info("Conectado como %s (id=%s)", self.user, self.user.id)


async def main() -> None:
    if not settings.discord_token:
        raise SystemExit("Falta DISCORD_TOKEN en el archivo .env")

    init_db()

    bot = PelusoBot()
    async with bot:
        await bot.start(settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())
