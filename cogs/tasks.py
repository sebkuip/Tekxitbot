import discord
from discord.ext import commands, tasks
import datetime
import asyncpg
import asyncio

from config import *


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

        self.guild = None
        self.members = 0
        self.messages = 0

        self.unbanloop.start()
        self.get_members.start()
        self.update_stats.start()

    @tasks.loop(minutes=1)
    async def unbanloop(self):
        async with self.bot.pool.acquire() as con:
            if not self.guild:
                self.guild = self.bot.get_guild(GUILDID)
            time = await con.fetchrow("SELECT(timedate) FROM tracker")
            results = await con.fetch("SELECT(banid, uid, endtime) FROM tempbans WHERE endtime < $1 AND endtime > $2", datetime.datetime.utcnow(), time[0])

            for result in results:
                try:
                    entry = await self.guild.fetch_ban(discord.Object(id=result[0][1]))
                    user = entry[1]
                    await self.guild.unban(user, reason="Temporary ban expired")

                    embed = discord.Embed(color=discord.Color.green())
                    embed.set_footer(
                        text=f'Action performed by bot | Case {result[0][0]}')
                    embed.set_author(name=f'Case {result[0][0]} | Unban | {user}')
                    embed.add_field(name=f'Reason', value='Temporary ban expired', inline=False)
                    await self.bot.logchannel.send(embed=embed)
                except Exception as e:
                    print(f"Could not unban {result}", e)
            await con.execute("UPDATE tracker SET timedate = $1", datetime.datetime.utcnow())

    @unbanloop.before_loop
    async def before_unbanloop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(2)
    
    @tasks.loop(minutes=1)
    async def get_members(self):
        if not self.guild:
            self.guild = self.bot.get_guild(GUILDID)
        
        self.members = self.guild.member_count
    
    @get_members.before_loop
    async def before_get_members(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(1)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        self.messages += 1


    @tasks.loop(minutes=15)
    async def update_stats(self):
        async with self.bot.pool.acquire() as con:
            await con.execute("INSERT INTO stats VALUES($1, $2, $3)", datetime.datetime.utcnow(), self.members, self.messages)
    
    @update_stats.before_loop
    async def before_update_stats(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(2)


def setup(bot):
    bot.add_cog(Tasks(bot))
