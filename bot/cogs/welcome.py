import discord
from discord.ext import commands

from shared.database import SessionLocal, get_or_create_guild_config


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        with SessionLocal() as session:
            config = get_or_create_guild_config(session, member.guild.id, member.guild.name)
            if not config.welcome_enabled or not config.welcome_channel_id:
                return
            message = config.welcome_message

        channel = member.guild.get_channel(config.welcome_channel_id)
        if channel is None:
            return

        text = message.format(
            member=member.mention,
            guild=member.guild.name,
            member_count=member.guild.member_count,
        )
        await channel.send(text)

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
