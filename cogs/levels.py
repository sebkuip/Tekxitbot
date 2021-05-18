from logging import currentframe
import discord
from discord.ext import commands, tasks
import random
import asyncio
import math
from config import *


class Members(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things
        self.chatted = {}
        self.reduce_cooldown.start()
        self.lock = asyncio.Lock()

    @tasks.loop(seconds=1)
    async def reduce_cooldown(self):
        async with self.lock:
            new_chatted = {user:(interval-1) for user,interval in self.chatted.items() if interval>1}
            self.chatted = new_chatted

    def xp_needed_for_level(self, level: int):
        return int(5/6*((2*(level)**3)+(27*(level)**2)+(91*(level))))
    
    @commands.Cog.listener()
    async def on_message(self, m):
        chatted = self.chatted
        if m.author.id in chatted or m.author.bot:
            return
        
        # fetch db data
        async with self.bot.pool.acquire() as con:
            data = await con.fetchrow("SELECT * FROM levels WHERE uid = $1", m.author.id)
            if not data:
                await con.execute("INSERT INTO levels(uid, xp, level, message_count) VALUES($1, $2, $3, $4) ON CONFLICT DO NOTHING", m.author.id, 0, 0, 0)
                return
        
        async with self.lock:
            self.chatted[m.author.id] = INTERVAL

        xp = data["xp"] + random.randint(MINXP, MAXXP)
        xp_needed = self.xp_needed_for_level(data["level"]+1)

        if xp >= xp_needed:
            level = data["level"] + 1
            await m.channel.send(f"GG <@{m.author.id}>, you just advanced to **level {level}**!")
        else:
            level = data["level"]
                
        message_count = data["message_count"] + 1
        
        async with self.bot.pool.acquire() as con:
            await con.execute("UPDATE levels SET xp = $1, level = $2, message_count = $3 WHERE uid = $4", xp, level, message_count, m.author.id)
        
    @commands.command(help="Show xp and level of either yourself or someone else", aliases=["rank"])
    async def level(self, ctx, user: discord.Member = None):
        if not user:
            user = ctx.author    
        
        async with self.bot.pool.acquire() as con:
            data = await con.fetchrow("SELECT * FROM levels WHERE uid = $1", user.id)
            rankdata = await con.fetchrow("SELECT position FROM(SELECT *, row_number() OVER(ORDER BY xp DESC) AS position FROM levels) RESULT WHERE uid = $1", user.id)
            rank = rankdata["position"]
            
            if not data and user == ctx.author:
                await ctx.send("You don't have a rank yet")
                return
            elif not data:
                await ctx.send("This user isn't ranked yet")
                return

        cur_xp = data['xp']-self.xp_needed_for_level(data['level'])
        next_xp = self.xp_needed_for_level(data['level']+1)-self.xp_needed_for_level(data['level'])
        
        embed = discord.Embed(description=f"Rank: {rank}\nLevel: {data['level']}\nTotal XP: {data['xp']} xp", color=discord.Color.blurple())
        embed.set_author(name=str(user), icon_url=user.avatar_url)
        progress = math.floor(cur_xp/(next_xp/10))
        bar = ""
        for i in range(0,10):
            if i <= progress:
                bar += "🟩"
            else:
                bar += "🟥"
        embed.add_field(name=bar, value=f"{cur_xp}/{next_xp} xp to next level", inline=False)
        await ctx.send(embed=embed)
    
    @commands.has_permissions(administrator=True)
    @commands.command(help="Force set someone's xp, level and message_count")
    async def setxp(self, ctx, user: discord.User, xp: int, level: int, message_count: int):
        async with self.bot.pool.acquire() as con:
            data = await con.fetchrow("UPDATE levels SET xp = $1, level = $2, message_count = $3 WHERE uid = $4 RETURNING uid", xp, level, message_count, user.id)
        # else:
            # await con.execute("INSERT INTO levels(uid, xp, level, message_count) VALUES($1, $2, $3, $4)", user.id, xp, level, message_count)
        await ctx.send(f"Sucessfully set data for <@{data['uid']}> to xp = {xp}, level = {level}, message_count = {message_count}")

    @commands.command(help="shows the top 10 for chat xp", aliases=["lb"])
    async def leaderboard(self, ctx, page=1):
        page = 1 if page<1 else page
        offset = (page-1)*10

        async with self.bot.pool.acquire() as con:
            data = await con.fetch("SELECT * FROM levels ORDER BY xp DESC LIMIT 10 OFFSET $1", offset)
        
        embed = discord.Embed(title="Leaderboard", description=f"page {page}", color=discord.Color.blurple())
        for i, entry in enumerate(data):
            user = self.bot.get_user(entry['uid']) or await self.bot.fetch_user(entry['uid'])
            embed.add_field(name=str(user), value=f"Rank: {i+1+(page-1)*10}\nLevel: {entry['level']}\nTotal XP: {entry['xp']}", inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Members(bot))