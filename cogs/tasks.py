from discord.ext import commands, tasks
import datetime

class Members(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

    @tasks.loop(minutes=1)
    async def unbanloop(self):
        result = self.bot.con.fetchall("SELECT * FROM tempbans WHERE endtime < $1", datetime.datetime.utcnow())
        if result[3] < datetime.datetime.utcnow():
            guild = self.bot.get_guild(346653006759985152)
            user = self.bot.get_member(result[1]) or await self.bot.fetch_user(result[1])
            try:
                await guild.unban(user, reason='Tempban expired')
            except Exception:
                pass

    @unbanloop.before_loop
    async def before_unbanloop(self):
        await self.bot.wait_until_ready()

    unbanloop.start()

def setup(bot):
    bot.add_cog(Members(bot))
