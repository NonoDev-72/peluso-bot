import logging
import os

import discord
from discord.ext import commands

from bot.welcome_card import build_welcome_card
from shared.database import SessionLocal, get_or_create_guild_config

log = logging.getLogger("peluso")


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        with SessionLocal() as session:
            config = get_or_create_guild_config(session, member.guild.id, member.guild.name)

        if config.default_role_id:
            role = member.guild.get_role(config.default_role_id)
            if role is None:
                log.warning("Rol por defecto %s no existe en %s", config.default_role_id, member.guild.name)
            else:
                try:
                    await member.add_roles(role, reason="Rol automatico de bienvenida")
                except discord.Forbidden:
                    log.warning(
                        "Sin permisos para asignar el rol '%s' en %s (revisá la jerarquía de roles)",
                        role.name,
                        member.guild.name,
                    )

        if not config.welcome_enabled or not config.welcome_channel_id:
            return

        channel = member.guild.get_channel(config.welcome_channel_id)
        if channel is None:
            return

        text = config.welcome_message.format(
            member=member.mention,
            guild=member.guild.name,
            member_count=member.guild.member_count,
        )

        file = await self._build_welcome_card_file(member, config.welcome_background_path)
        await channel.send(text, file=file)

    async def _build_welcome_card_file(
        self, member: discord.Member, background_path: str | None
    ) -> discord.File | None:
        if not background_path or not os.path.isfile(background_path):
            return None

        try:
            avatar_bytes = await member.display_avatar.replace(size=256, static_format="png").read()
            buffer = build_welcome_card(background_path, avatar_bytes)
        except Exception:
            log.exception("No se pudo generar la tarjeta de bienvenida para %s en %s", member, member.guild.name)
            return None

        return discord.File(buffer, filename="bienvenida.png")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        with SessionLocal() as session:
            config = get_or_create_guild_config(session, member.guild.id, member.guild.name)
            if not config.goodbye_enabled or not config.goodbye_channel_id:
                return
            message = config.goodbye_message

        channel = member.guild.get_channel(config.goodbye_channel_id)
        if channel is None:
            return

        text = message.format(
            member=member.mention,
            guild=member.guild.name,
            member_count=member.guild.member_count,
        )
        await channel.send(text)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Welcome(bot))
