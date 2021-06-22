import discord
from discord import Webhook, AsyncWebhookAdapter
from discord.ext import commands, tasks
import datetime
import asyncpg
import asyncio
import aiohttp
from discord.webhook import WebhookAdapter

from config import *


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things

        self.guild = None
        self.members = 0
        self.messages = 0

        self.tempinfractionloop.start()
        self.redditlog.start()

    @tasks.loop(minutes=1)
    async def tempinfractionloop(self):
        async with self.bot.pool.acquire() as con:
            if not self.guild:
                self.guild = self.bot.get_guild(GUILDID)
            time = await con.fetchrow("SELECT(timedate) FROM tracker")
            banresults = await con.fetch("SELECT(banid, uid, endtime) FROM tempbans WHERE endtime < $1 AND endtime > $2", datetime.datetime.utcnow(), time[0])
            muteresults = await con.fetch("SELECT(muteid, uid, endtime) FROM tempmutes WHERE endtime < $1 AND endtime > $2", datetime.datetime.utcnow(), time[0])

            for result in banresults:
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

            for result in muteresults:
                try:
                    member = self.guild.get_member(result[0][1])
                    muterole = self.guild.get_role(MUTEDROLE)
                    await member.remove_roles(muterole)

                    embed = discord.Embed(color=discord.Color.green())
                    embed.set_footer(
                        text=f'Action performed by bot | Case {result[0][0]}')
                    embed.set_author(name=f'Case {result[0][0]} | Unmute | {member}')
                    embed.add_field(name=f'Reason', value='Temporary mute expired', inline=False)
                    await self.bot.logchannel.send(embed=embed)
                except Exception as e:
                    print(f"Could not unmute {result}", e)
            await con.execute("UPDATE tracker SET timedate = $1", datetime.datetime.utcnow())

    @tempinfractionloop.before_loop
    async def before_tempinfractionloop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(2)

    

    @tasks.loop(minutes=1)
    async def redditlog(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.reddit.com/r/tekxit.json?sort=new") as resp:
                if resp.status == 200:
                    json = await resp.json()
                    posts = json['data']['children']
                    if not posts:
                        print(json)
                        print(posts)
                    posts = list(map(lambda p: p['data'], posts))
                    posts.reverse()

                    async with self.bot.pool.acquire() as con:
                        data = await con.fetch("SELECT * FROM posted")
                        posted = list(map(lambda d: d["id"], data))
                    
                        for post in posts:
                            if post["name"] not in posted:
                                embed = discord.Embed(title=post["title"], url=post["url"], description=post["selftext"] if not post["selftext"] == "" else None, color=0xFF0000)
                                embed.set_author(name="New post on r/tekxit")
                                embed.add_field(name="Post author", value=post["author"])
                                try:
                                    embed.set_image(url=post["url_overridden_by_dest"])
                                except KeyError:
                                    pass
                                webhook = Webhook.from_url(REDDITWEBHOOK, adapter=AsyncWebhookAdapter(session))
                                await webhook.send(embed=embed)
                                async with self.bot.pool.acquire() as con:
                                    await con.execute("INSERT INTO posted(id) VALUES($1)", post["name"])
                        



def setup(bot):
    bot.add_cog(Tasks(bot))
