import time

import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Muestra la latencia del bot")
    async def ping(self, interaction: discord.Interaction) -> None:
        start = time.perf_counter()
        await interaction.response.send_message("Calculando...", ephemeral=True)
        elapsed_ms = (time.perf_counter() - start) * 1000
        await interaction.edit_original_response(
            content=f"🏓 Pong! Latencia de API: {self.bot.latency * 1000:.0f}ms · Respuesta: {elapsed_ms:.0f}ms"
        )

    @app_commands.command(name="info", description="Informacion sobre el bot")
    async def info(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title="Peluso Bot", color=discord.Color.blurple())
        embed.add_field(name="Servidores", value=str(len(self.bot.guilds)))
        embed.add_field(name="Latencia", value=f"{self.bot.latency * 1000:.0f}ms")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
