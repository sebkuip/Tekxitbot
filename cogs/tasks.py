import discord
from discord.ext import commands, tasks
import datetime
import asyncpg


# banned user converter. From R.Danny by Danny (Raptzz). https://github.com/Rapptz/RoboDanny
class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.isdigit():
            member_id = int(argument, base=10)
            try:
                return await ctx.guild.fetch_ban(discord.Object(id=member_id))
            except discord.NotFound:
                raise commands.BadArgument(
                    'This member has not been banned before.') from None

        ban_list = await ctx.guild.bans()
        entity = discord.utils.find(
            lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            raise commands.BadArgument(
                'This member has not been banned before.')
        return entity


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    @tasks.loop(minutes=1)
    async def unbanloop(self):
        result = await self.bot.con.fetchrow("SELECT(timedate) FROM tracker")
        results = await self.bot.con.fetchall("SELECT(uid) FROM tempbans WHERE endtime < now() AND endtime > $1", result)
        for result in results:
            pass

    @unbanloop.before_loop
    async def before_unbanloop(self):
        await self.bot.wait_until_ready()

    unbanloop.start()


def setup(bot):
    bot.add_cog(Tasks(bot))
