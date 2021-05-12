from logging import currentframe
import discord
from discord.ext import commands, tasks
import random
import asyncio
import math
import typing
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
            chatted[m.author.id] = INTERVAL

        xp = data["xp"] + random.randint(MINXP, MAXXP)
        xp_needed = self.xp_needed_for_level(data["level"]+1)

        async with self.bot.pool.acquire() as con:
            if xp >= xp_needed:
                level = data["level"] + 1
                await m.channel.send(f"Good job <@{m.author.id}>, you just reached level {level}!")
            else:
                level = data["level"]
                
            message_count = data["message_count"] + 1

            await con.execute("UPDATE levels SET xp = $1, level = $2, message_count = $3 WHERE uid = $4", xp, level, message_count, m.author.id)
        
    @commands.command(help="Show xp and level of either yourself or someone else", aliases=["rank"])
    async def level(self, ctx, user: discord.Member = None):
        if not user:
            user = ctx.author    
        
        async with self.bot.pool.acquire() as con:
            data = await con.fetchrow("SELECT * FROM levels WHERE uid = $1", user.id)
            
            if not data and user == ctx.author:
                await ctx.send("You don't have a rank yet")
                return
            elif not data:
                await ctx.send("This user isn't ranked yet")
                return

        cur_xp = data['xp']-self.xp_needed_for_level(data['level'])
        next_xp = self.xp_needed_for_level(data['level']+1)-self.xp_needed_for_level(data['level'])
        
        embed = discord.Embed(title="Level", description=f"Your current level is {data['level']}\nYour current XP is {cur_xp}/{next_xp}", color=discord.Color.blurple())
        progress = math.floor(cur_xp/(next_xp/10))
        bar = ""
        for i in range(0,10):
            if i <= progress:
                bar += "🟩"
            else:
                bar += "🟥"
        embed.add_field(name="\u200b", value=bar, inline=False)
        await ctx.send(embed=embed)
    
    @commands.has_permissions(administrator=True)
    @commands.command(help="Force set someone's xp, level and message_count")
    async def setxp(self, ctx, user: discord.User, xp: int, level: int, message_count: int):
        async with self.bot.pool.acquire() as con:
            data = await con.fetchrow("UPDATE levels SET xp = $1, level = $2, message_count = $3 WHERE uid = $4 RETURNING uid", xp, level, message_count, user.id)
        # else:
            # await con.execute("INSERT INTO levels(uid, xp, level, message_count) VALUES($1, $2, $3, $4)", user.id, xp, level, message_count)
        await ctx.send(f"Sucessfully set data for <@{data['uid']}> to xp = {xp}, level = {level}, message_count = {message_count}")


def setup(bot):
    bot.add_cog(Members(bot))