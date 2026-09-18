import logging

import discord
from discord.ext import commands

from shared.database import (
    SessionLocal,
    create_temp_voice_channel,
    delete_temp_voice_channel,
    get_temp_voice_channel,
    get_voice_room_trigger_by_channel,
    next_room_number,
)

log = logging.getLogger("peluso")


class VoiceRooms(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        if after.channel is not None and after.channel != before.channel:
            await self._handle_join(member, after.channel)

        if before.channel is not None and before.channel != after.channel:
            await self._handle_leave(before.channel)

    async def _handle_join(self, member: discord.Member, channel: discord.VoiceChannel) -> None:
        with SessionLocal() as session:
            trigger = get_voice_room_trigger_by_channel(session, channel.guild.id, channel.id)
            if trigger is None:
                return
            trigger_id = trigger.id
            name_template = trigger.name_template
            number = next_room_number(session, trigger_id)

        try:
            name = name_template.format(n=number)
        except (KeyError, IndexError):
            name = f"Sala {number}"

        overwrites = channel.category.overwrites if channel.category else None
        try:
            new_channel = await channel.guild.create_voice_channel(
                name=name,
                category=channel.category,
                overwrites=overwrites,
                reason=f"Sala temporal solicitada por {member}",
            )
        except discord.Forbidden:
            log.warning("Sin permisos para crear canales de voz en %s", channel.guild.name)
            return

        with SessionLocal() as session:
            create_temp_voice_channel(session, new_channel.id, channel.guild.id, trigger_id, number)

        try:
            await member.move_to(new_channel, reason="Movido a su sala temporal")
        except discord.HTTPException:
            log.warning("No se pudo mover a %s a su sala temporal en %s", member, channel.guild.name)

    async def _handle_leave(self, channel: discord.VoiceChannel) -> None:
        with SessionLocal() as session:
            temp_channel = get_temp_voice_channel(session, channel.id)
            if temp_channel is None:
                return

        if len(channel.members) > 0:
            return

        try:
            await channel.delete(reason="Sala temporal vacía")
        except discord.NotFound:
            pass
        except discord.Forbidden:
            log.warning("Sin permisos para borrar la sala temporal '%s' en %s", channel.name, channel.guild.name)
            return

        with SessionLocal() as session:
            delete_temp_voice_channel(session, channel.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceRooms(bot))
