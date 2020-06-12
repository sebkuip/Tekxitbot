import discord
import psycopg2
from discord.ext import commands

from config import *


class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # This is the bot instance, it lets us interact with most things
        try:
            self.conn = psycopg2.connect(host=HOST, port=PORT, database=DATABASE, user=USER,
                                         password=PASSWORD)
            self.cur = self.conn.cursor()
        except (Exception, psycopg2.DatabaseError) as error:
            pass

    @commands.command(help='Kicks the specified member for the specified reason')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.add_field(name=f'**YOU GOT KICKED FROM**', value=f'```{ctx.guild.name}```', inline=False)
        embed.add_field(name=f'**BY**', value=ctx.author.mention, inline=False)
        if reason:
            embed.add_field(name=f'**FOR THE REASON**', value=f'`{reason}`', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')
        await member.kick(reason=reason)
        try:
            self.cur.execute("INSERT INTO kicks(uid, executor, timedate, reason) VALUES(%s, %s, "
                             "CURRENT_TIMESTAMP(1), %s)", (member.id, ctx.author.id, reason))
            self.conn.commit()
        except Exception as error:
            print(error)
        embed.remove_field(0)
        embed.remove_field(0)
        embed.insert_field_at(0, name=f'**GOT KICKED BY**', value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
        await ctx.message.delete()
        channel = await self.bot.fetch_channel(425632491622105088)
        await channel.send(embed=embed)

    @commands.command(help='Bans the specified member for the specified reason')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.add_field(name=f'**YOU GOT BANNED FROM**', value=f'```{ctx.guild.name}```', inline=False)
        embed.add_field(name=f'**BY**', value=ctx.author.mention, inline=False)
        if reason:
            embed.add_field(name=f'**FOR THE REASON**', value=f'`{reason}`', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')
        await member.ban(reason=reason)
        embed.remove_field(0)
        embed.remove_field(0)
        embed.insert_field_at(0, name=f'**GOT BANNED BY**', value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
        await ctx.message.delete()
        channel = await self.bot.fetch_channel(425632491622105088)
        await channel.send(embed=embed)

    @commands.command(help='Warns the user for the specified reason')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.add_field(name=f'**YOU GOT WARNED IN**', value=f'```{ctx.guild.name}```', inline=False)
        embed.add_field(name=f'**BY**', value=ctx.author.mention, inline=False)
        if reason:
            embed.add_field(name=f'**FOR THE REASON**', value=f'`{reason}`', inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await ctx.send('Could not send DM to user')
        embed.remove_field(0)
        embed.remove_field(0)
        embed.insert_field_at(0, name=f'**GOT WARNED BY**', value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
        await ctx.message.delete()
        channel = await self.bot.fetch_channel(425632491622105088)
        await channel.send(embed=embed)
        try:
            self.cur.execute("INSERT INTO warnings(uid, executor, timedate, reason) VALUES(%s, "
                             "%s, CURRENT_TIMESTAMP(1), %s)", (member.id, ctx.author.id, reason))
            self.conn.commit()
        except Exception as error:
            print(error)

    @commands.command(help='View all infractions for a user')
    @commands.has_permissions(manage_messages=True)
    async def infractions(self, ctx, member: discord.Member):
        try:
            embed = discord.Embed(description='Infractions:')
            self.cur.execute("SELECT * FROM warnings WHERE uid LIKE %s", (member.id,))
            warns = self.cur.fetchall()
            self.cur.execute("SELECT * FROM kicks WHERE uid LIKE %s", (member.id,))
            kicks = self.cur.fetchall()
            self.cur.execute("SELECT * FROM bans WHERE uid LIKE %s", (member.id,))
            bans = self.cur.fetchall()
            embed.set_author(name=str(member), icon_url=member.avatar_url)
            embed.add_field(name='warnings', value=','.join(warns), inline=False)
            embed.add_field(name='kicks', value=','.join(kicks), inline=False)
            embed.add_field(name='bans', value=','.join(bans), inline=False)
            ctx.send(embed=embed)
        except Exception as error:
            print(error)


def setup(bot):
    bot.add_cog(moderation(bot))
