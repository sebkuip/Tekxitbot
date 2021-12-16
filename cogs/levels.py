import asyncio
import math
import random
import typing
from logging import currentframe

import discord
from discord.errors import HTTPException
from discord.ext import commands, tasks

from config import *


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things
        self.chatted = {}
        self.reduce_cooldown.start()
        self.lock = asyncio.Lock()

    @tasks.loop(seconds=1)
    async def reduce_cooldown(self):
        async with self.lock:
            new_chatted = {
                user: (interval - 1)
                for user, interval in self.chatted.items()
                if interval > 1
            }
            self.chatted = new_chatted

    def xp_needed_for_level(self, level: int):
        return int(5 / 6 * ((2 * (level) ** 3) + (27 * (level) ** 2) + (91 * (level))))

    @commands.Cog.listener()
    async def on_message(self, m):
        chatted = self.chatted
        if m.author.id in chatted or m.author.bot:
            return

        # fetch db data
        async with self.bot.pool.acquire() as con:
            data = await con.fetchrow(
                "SELECT * FROM levels WHERE uid = $1", m.author.id
            )
            if not data:
                await con.execute(
                    "INSERT INTO levels(uid, xp, level, message_count) VALUES($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                    m.author.id,
                    0,
                    0,
                    0,
                )
                return

        async with self.lock:
            self.chatted[m.author.id] = INTERVAL

        xp = data["xp"] + random.randint(MINXP, MAXXP)
        xp_needed = self.xp_needed_for_level(data["level"] + 1)

        if xp >= xp_needed:
            level = data["level"] + 1
            await m.channel.send(
                f"GG <@{m.author.id}>, you just advanced to **level {level}**!"
            )

            async with self.bot.pool.acquire() as con:
                guild = self.bot.get_guild(GUILDID) or await self.bot.fetch_guild(
                    GUILDID
                )
                removeroles_id = await con.fetch("SELECT roleid FROM levelroles")
                removeroles_id = [role_id[0] for role_id in removeroles_id]
                removeroles = [guild.get_role(role_id) for role_id in removeroles_id]
                for rrole in removeroles:
                    if rrole in m.author.roles:
                        try:
                            await m.author.remove_roles(
                                rrole, reason="removed old rank role"
                            )
                        except HTTPException:
                            continue

                addroles_id = await con.fetch(
                    "SELECT roleid FROM levelroles WHERE level = $1", level
                )
                addroles_id = [role_id[0] for role_id in addroles_id]
                addroles = [guild.get_role(role_id) for role_id in addroles_id]
                for arole in addroles:
                    try:
                        await m.author.add_roles(arole, reason="Add new rank role")
                    except HTTPException:
                        continue
        else:
            level = data["level"]

        message_count = data["message_count"] + 1

        async with self.bot.pool.acquire() as con:
            await con.execute(
                "UPDATE levels SET xp = $1, level = $2, message_count = $3 WHERE uid = $4",
                xp,
                level,
                message_count,
                m.author.id,
            )

    @commands.command(
        help="Show xp and level of either yourself or someone else", aliases=["rank"]
    )
    async def level(self, ctx, user: discord.Member = None):
        if not user:
            user = ctx.author

        async with self.bot.pool.acquire() as con:
            data = await con.fetchrow("SELECT * FROM levels WHERE uid = $1", user.id)
            rankdata = await con.fetchrow(
                "SELECT position FROM(SELECT *, row_number() OVER(ORDER BY xp DESC) AS position FROM levels) RESULT WHERE uid = $1",
                user.id,
            )
            rank = rankdata["position"]

            if not data and user == ctx.author:
                await ctx.send("You don't have a rank yet")
                return
            elif not data:
                await ctx.send("This user isn't ranked yet")
                return

        cur_xp = data["xp"] - self.xp_needed_for_level(data["level"])
        next_xp = self.xp_needed_for_level(
            data["level"] + 1
        ) - self.xp_needed_for_level(data["level"])

        embed = discord.Embed(
            description=f"Rank: {rank}\nLevel: {data['level']}\nTotal XP: {data['xp']} xp",
            color=discord.Color.blurple(),
        )
        embed.set_author(name=str(user), icon_url=user.avatar.url)
        progress = math.floor(cur_xp / (next_xp / 10))
        bar = ""
        for i in range(0, 10):
            if i <= progress:
                bar += "🟩"
            else:
                bar += "🟥"
        embed.add_field(
            name=bar, value=f"{cur_xp}/{next_xp} xp to next level", inline=False
        )
        await ctx.send(embed=embed)

    @commands.has_permissions(administrator=True)
    @commands.command(help="Force set someone's xp, level and message_count")
    async def setxp(
        self, ctx, user: discord.User, xp: int, level: int, message_count: int
    ):
        async with self.bot.pool.acquire() as con:
            data = await con.fetchrow(
                "UPDATE levels SET xp = $1, level = $2, message_count = $3 WHERE uid = $4 RETURNING uid",
                xp,
                level,
                message_count,
                user.id,
            )
        # else:
        # await con.execute("INSERT INTO levels(uid, xp, level, message_count) VALUES($1, $2, $3, $4)", user.id, xp, level, message_count)
        await ctx.send(
            f"Sucessfully set data for <@{data['uid']}> to xp = {xp}, level = {level}, message_count = {message_count}"
        )

    class LeaderBoard(discord.ui.View):
        def __init__(self, bot, ctx, page, data):
            super().__init__()
            self.bot = bot
            self.ctx = ctx
            self.page = page

            self.timeout = 20
            self.message = None

            if page == 1:
                button = discord.utils.get(self.children, custom_id="pg_bck")
                button.disabled = True

            if len(data) < 10:
                button = discord.utils.get(self.children, custom_id="pg_fwd")
                button.disabled = True

        async def on_timeout(self):
            for child in self.children:
                child.disabled = True
            await self.message.edit(
                content="timed out", embed=self.message.embeds[0], view=self
            )

        @discord.ui.button(
            label="<<", style=discord.ButtonStyle.blurple, custom_id="pg_bck"
        )
        async def page_back(
            self, button: discord.ui.Button, interaction: discord.Interaction
        ):
            if not self.ctx.author == interaction.user:
                await interaction.response.send_message(
                    "You cannot respond to this", ephemeral=True
                )
                return

            if self.page == 2:
                button.disabled = True

            self.page -= 1

            offset = (self.page - 1) * 10

            async with self.bot.pool.acquire() as con:
                data = await con.fetch(
                    "SELECT * FROM levels ORDER BY xp DESC LIMIT 10 OFFSET $1", offset
                )

            embed = discord.Embed(
                title="Leaderboard",
                description=f"page {self.page}",
                color=discord.Color.blurple(),
            )
            for i, entry in enumerate(data):
                user = self.bot.get_user(entry["uid"]) or await self.bot.fetch_user(
                    entry["uid"]
                )
                embed.add_field(
                    name=str(user),
                    value=f"Rank: {i+1+(self.page-1)*10}\nLevel: {entry['level']}\nTotal XP: {entry['xp']}",
                    inline=False,
                )
            if len(data) == 10:
                forward = discord.utils.get(self.children, custom_id="pg_fwd")
                forward.disabled = False
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(
            label=">>", style=discord.ButtonStyle.blurple, custom_id="pg_fwd"
        )
        async def page_forward(
            self, button: discord.ui.Button, interaction: discord.Interaction
        ):
            if not self.ctx.author == interaction.user:
                await interaction.response.send_message(
                    "You cannot respond to this", ephemeral=True
                )
                return

            if self.page == 1:
                back = discord.utils.get(self.children, custom_id="pg_bck")
                back.disabled = False

            self.page += 1

            offset = (self.page - 1) * 10

            async with self.bot.pool.acquire() as con:
                data = await con.fetch(
                    "SELECT * FROM levels ORDER BY xp DESC LIMIT 10 OFFSET $1", offset
                )

            embed = discord.Embed(
                title="Leaderboard",
                description=f"page {self.page}",
                color=discord.Color.blurple(),
            )
            for i, entry in enumerate(data):
                user = self.bot.get_user(entry["uid"]) or await self.bot.fetch_user(
                    entry["uid"]
                )
                embed.add_field(
                    name=str(user),
                    value=f"Rank: {i+1+(self.page-1)*10}\nLevel: {entry['level']}\nTotal XP: {entry['xp']}",
                    inline=False,
                )
            if len(data) < 10:
                button.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.danger)
        async def cancel(
            self, button: discord.ui.Button, interaction: discord.Interaction
        ):
            if not self.ctx.author == interaction.user:
                await interaction.response.send_message(
                    "You cannot respond to this", ephemeral=True
                )
                return

            self.stop()
            await interaction.message.delete()
            await self.ctx.message.delete()

    @commands.command(help="shows the top 10 for chat xp", aliases=["lb"])
    async def leaderboard(self, ctx, page=1):
        page = 1 if page < 1 else page
        offset = (page - 1) * 10

        async with self.bot.pool.acquire() as con:
            data = await con.fetch(
                "SELECT * FROM levels ORDER BY xp DESC LIMIT 10 OFFSET $1", offset
            )

        embed = discord.Embed(
            title="Leaderboard",
            description=f"page {page}",
            color=discord.Color.blurple(),
        )
        for i, entry in enumerate(data):
            user = self.bot.get_user(entry["uid"]) or await self.bot.fetch_user(
                entry["uid"]
            )
            embed.add_field(
                name=str(user),
                value=f"Rank: {i+1+(page-1)*10}\nLevel: {entry['level']}\nTotal XP: {entry['xp']}",
                inline=False,
            )

        lbview = self.LeaderBoard(self.bot, ctx, page, data)
        lbview.message = await ctx.send(embed=embed, view=lbview)

    @commands.has_permissions(administrator=True)
    @commands.command(help="Add a role to the rewards list")
    async def addrolereward(self, ctx, role: discord.Role, level: int):
        if level <= 0:
            await ctx.send("That is not a valid level")
            return
        async with ctx.typing():
            async with self.bot.pool.acquire() as con:
                try:
                    await con.execute(
                        "INSERT INTO levelroles(roleid, level) VALUES($1, $2)",
                        role.id,
                        level,
                    )
                except:
                    await ctx.send("Failed to add role, check if data is valid")
                    return
                await ctx.send(
                    f"Sucesfully added {role.name} ({role.id}) as a reward to level {level}"
                )

    @commands.has_permissions(administrator=True)
    @commands.command(help="Remove a role from the rewards list")
    async def removerolereward(self, ctx, role: discord.Role, level: int):
        if level <= 0:
            await ctx.send("That is not a valid level")
            return
        async with ctx.typing():
            async with self.bot.pool.acquire() as con:
                try:
                    await con.execute(
                        "DELETE FROM levelroles WHERE roleid = $1 AND level = $2",
                        role.id,
                        level,
                    )
                except:
                    await ctx.send("Failed to remove role, check if data is valid")
                    return
                await ctx.send(
                    f"Sucesfully removed {role.name} ({role.id}) as a reward to level {level}"
                )


def setup(bot):
    bot.add_cog(Levels(bot))
